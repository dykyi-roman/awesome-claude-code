# PHP 8.5 DDD Specifics

PHP 8.5 features and patterns for DDD implementation.

## Language Features for DDD

### Readonly Classes

Perfect for Value Objects and DTOs.

```php
final readonly class Email
{
    public function __construct(
        public string $value
    ) {
        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidEmailException($value);
        }
    }
}
```

### Constructor Property Promotion

Clean entity and value object constructors.

```php
final class Order
{
    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private OrderStatus $status = OrderStatus::Draft,
        private readonly \DateTimeImmutable $createdAt = new \DateTimeImmutable()
    ) {}
}
```

### Enums for Domain States

Replace magic strings with type-safe enums.

```php
enum OrderStatus: string
{
    case Draft = 'draft';
    case Pending = 'pending';
    case Confirmed = 'confirmed';
    case Shipped = 'shipped';
    case Delivered = 'delivered';
    case Cancelled = 'cancelled';

    public function canTransitionTo(self $target): bool
    {
        return match($this) {
            self::Draft => in_array($target, [self::Pending, self::Cancelled]),
            self::Pending => in_array($target, [self::Confirmed, self::Cancelled]),
            self::Confirmed => in_array($target, [self::Shipped, self::Cancelled]),
            self::Shipped => $target === self::Delivered,
            default => false,
        };
    }

    public function isFinal(): bool
    {
        return in_array($this, [self::Delivered, self::Cancelled]);
    }

    public function allowsModification(): bool
    {
        return $this === self::Draft;
    }
}
```

### Union Types and Named Arguments

Expressive domain methods.

```php
final class Money
{
    public function __construct(
        public readonly int $amount,
        public readonly Currency $currency
    ) {}

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self(
            amount: $this->amount + $other->amount,
            currency: $this->currency
        );
    }

    public static function zero(Currency|string $currency): self
    {
        $currency = $currency instanceof Currency
            ? $currency
            : Currency::from($currency);

        return new self(amount: 0, currency: $currency);
    }
}
```

### Attributes for Metadata

Instead of annotations (but keep out of Domain).

```php
// Infrastructure layer - mapping configuration
#[Entity]
#[Table(name: 'orders')]
class OrderMapping
{
    #[Id]
    #[Column(type: 'uuid')]
    public string $id;

    #[Column(type: 'string', enumType: OrderStatus::class)]
    public string $status;
}
```

## DDD Building Blocks in PHP 8.5

### Entity Pattern

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

final class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];
    private array $domainEvents = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private OrderStatus $status = OrderStatus::Draft,
        private readonly \DateTimeImmutable $createdAt = new \DateTimeImmutable()
    ) {}

    public function id(): OrderId
    {
        return $this->id;
    }

    public function addLine(
        ProductId $productId,
        Quantity $quantity,
        Money $unitPrice
    ): void {
        if (!$this->status->allowsModification()) {
            throw new OrderCannotBeModifiedException($this->id);
        }

        $this->lines[] = new OrderLine(
            id: OrderLineId::generate(),
            productId: $productId,
            quantity: $quantity,
            unitPrice: $unitPrice
        );
    }

    public function confirm(): void
    {
        $this->guardCanConfirm();

        $this->status = OrderStatus::Confirmed;
        $this->recordEvent(new OrderConfirmedEvent(
            orderId: $this->id,
            total: $this->total(),
            occurredAt: new \DateTimeImmutable()
        ));
    }

    public function total(): Money
    {
        if (empty($this->lines)) {
            return Money::zero(Currency::USD);
        }

        return array_reduce(
            $this->lines,
            fn(Money $carry, OrderLine $line) => $carry->add($line->subtotal()),
            Money::zero(Currency::USD)
        );
    }

    private function guardCanConfirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidOrderStateTransitionException(
                from: $this->status,
                to: OrderStatus::Confirmed
            );
        }

        if (empty($this->lines)) {
            throw new EmptyOrderCannotBeConfirmedException($this->id);
        }
    }

    private function recordEvent(object $event): void
    {
        $this->domainEvents[] = $event;
    }

    public function releaseEvents(): array
    {
        $events = $this->domainEvents;
        $this->domainEvents = [];
        return $events;
    }
}
```

### Value Object Pattern

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\ValueObject;

final readonly class Money
{
    private function __construct(
        public int $cents,
        public Currency $currency
    ) {
        if ($cents < 0) {
            throw new NegativeMoneyException($cents);
        }
    }

    public static function fromCents(int $cents, Currency $currency): self
    {
        return new self($cents, $currency);
    }

    public static function fromDecimal(float $amount, Currency $currency): self
    {
        return new self((int) round($amount * 100), $currency);
    }

    public static function zero(Currency $currency): self
    {
        return new self(0, $currency);
    }

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->cents + $other->cents, $this->currency);
    }

    public function subtract(self $other): self
    {
        $this->ensureSameCurrency($other);
        $result = $this->cents - $other->cents;

        if ($result < 0) {
            throw new InsufficientFundsException($this, $other);
        }

        return new self($result, $this->currency);
    }

    public function multiply(int $factor): self
    {
        return new self($this->cents * $factor, $this->currency);
    }

    public function isGreaterThan(self $other): bool
    {
        $this->ensureSameCurrency($other);
        return $this->cents > $other->cents;
    }

    public function equals(self $other): bool
    {
        return $this->cents === $other->cents
            && $this->currency === $other->currency;
    }

    public function toDecimal(): float
    {
        return $this->cents / 100;
    }

    private function ensureSameCurrency(self $other): void
    {
        if ($this->currency !== $other->currency) {
            throw new CurrencyMismatchException($this->currency, $other->currency);
        }
    }
}
```

### Identifier Value Object

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

use Ramsey\Uuid\Uuid;
use Ramsey\Uuid\UuidInterface;

final readonly class OrderId
{
    private function __construct(
        public string $value
    ) {
        if (!Uuid::isValid($value)) {
            throw new InvalidOrderIdException($value);
        }
    }

    public static function generate(): self
    {
        return new self(Uuid::uuid7()->toString());
    }

    public static function fromString(string $value): self
    {
        return new self($value);
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function __toString(): string
    {
        return $this->value;
    }
}
```

### Domain Event Pattern

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

final readonly class OrderConfirmedEvent
{
    public function __construct(
        public OrderId $orderId,
        public Money $total,
        public \DateTimeImmutable $occurredAt
    ) {}
}
```

### Repository Interface Pattern

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderStatus;
use Domain\Customer\ValueObject\CustomerId;

interface OrderRepositoryInterface
{
    /**
     * @throws OrderNotFoundException
     */
    public function get(OrderId $id): Order;

    public function findById(OrderId $id): ?Order;

    public function save(Order $order): void;

    public function delete(Order $order): void;

    /**
     * @return array<Order>
     */
    public function findByCustomer(CustomerId $customerId): array;

    /**
     * @return array<Order>
     */
    public function findByStatus(OrderStatus $status, int $limit = 100): array;

    public function nextIdentity(): OrderId;
}
```

### Domain Exception Pattern

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Exception;

final class OrderCannotBeModifiedException extends DomainException
{
    public function __construct(OrderId $orderId)
    {
        parent::__construct(
            sprintf('Order %s cannot be modified in current state', $orderId)
        );
    }
}

final class InvalidOrderStateTransitionException extends DomainException
{
    public function __construct(
        public readonly OrderStatus $from,
        public readonly OrderStatus $to
    ) {
        parent::__construct(
            sprintf('Cannot transition order from %s to %s', $from->value, $to->value)
        );
    }
}
```

## Framework Integration

### Doctrine ORM (Infrastructure)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function get(OrderId $id): Order
    {
        $order = $this->findById($id);

        if ($order === null) {
            throw new OrderNotFoundException($id);
        }

        return $order;
    }

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function delete(Order $order): void
    {
        $this->em->remove($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

### Doctrine Mapping (XML - keeps Domain clean)

```xml
<!-- Infrastructure/Persistence/Doctrine/Mapping/Order.orm.xml -->
<doctrine-mapping>
    <entity name="Domain\Order\Entity\Order" table="orders">
        <id name="id" type="order_id" column="id"/>
        <field name="customerId" type="customer_id" column="customer_id"/>
        <field name="status" type="string" column="status" enumType="Domain\Order\ValueObject\OrderStatus"/>
        <field name="createdAt" type="datetime_immutable" column="created_at"/>

        <one-to-many field="lines" target-entity="Domain\Order\Entity\OrderLine" mapped-by="order">
            <cascade>
                <cascade-all/>
            </cascade>
        </one-to-many>
    </entity>
</doctrine-mapping>
```

## Detection Patterns for PHP 8.5

```bash
# Good - Using readonly classes
Grep: "final readonly class" --glob "**/Domain/**/*.php"

# Good - Using enums
Grep: "^enum " --glob "**/Domain/**/*.php"

# Good - Using constructor promotion
Grep: "public function __construct\(" --glob "**/Domain/**/*.php" -A 5 | grep "private readonly\|public readonly"

# Good - declare(strict_types=1)
Grep: "declare\(strict_types=1\)" --glob "**/*.php"

# Bad - Missing strict_types
Bash: find . -name "*.php" -exec grep -L "declare(strict_types=1)" {} \;

# Bad - Not using final
Grep: "^class " --glob "**/Domain/**/*.php" | grep -v "final\|abstract"
```

## Best Practices Checklist

### PHP 8.5 Features
- [ ] `declare(strict_types=1)` in ALL files
- [ ] `final` on all classes (except when inheritance needed)
- [ ] `readonly` on value objects and DTOs
- [ ] Enums for all fixed value sets
- [ ] Constructor property promotion
- [ ] Named arguments for clarity
- [ ] Union types where appropriate
- [ ] `match` expressions instead of `switch`

### DDD Compliance
- [ ] Domain has no framework imports
- [ ] Entities have behavior methods
- [ ] Value Objects are immutable
- [ ] Repository interfaces in Domain
- [ ] Repository implementations in Infrastructure
- [ ] Exceptions are specific and informative
- [ ] Events are immutable
- [ ] Factories for complex creation