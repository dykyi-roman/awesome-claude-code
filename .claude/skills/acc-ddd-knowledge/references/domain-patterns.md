# Domain Patterns

Detailed patterns for Domain layer implementation in PHP.

## Entity

### Definition
Object with unique identity that persists through time and state changes.

### Characteristics
- Has a unique identifier
- Mutable state
- Equality based on identity, not attributes
- Contains behavior (not just data)

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderStatus;
use Domain\Order\ValueObject\OrderLine;
use Domain\Order\Event\OrderConfirmedEvent;
use Domain\Shared\ValueObject\Money;

final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    private array $domainEvents = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private readonly \DateTimeImmutable $createdAt
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function addLine(ProductId $productId, int $quantity, Money $price): void
    {
        if (!$this->status->allowsModification()) {
            throw new OrderCannotBeModifiedException($this->id);
        }

        $this->lines[] = new OrderLine($productId, $quantity, $price);
    }

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidOrderStateTransitionException(
                $this->status,
                OrderStatus::Confirmed
            );
        }

        if (empty($this->lines)) {
            throw new EmptyOrderCannotBeConfirmedException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
        $this->recordEvent(new OrderConfirmedEvent($this->id, $this->total()));
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn(Money $carry, OrderLine $line) => $carry->add($line->subtotal()),
            Money::zero('USD')
        );
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

### Detection Patterns

```bash
# Good - Entity with behavior
Grep: "public function [a-z]+\(" --glob "**/Domain/**/Entity/**/*.php" -A 3

# Bad - Anemic entity (only getters/setters)
Grep: "public function (get|set|is|has)[A-Z]" --glob "**/Domain/**/Entity/**/*.php"

# Check entity has ID
Grep: "private readonly.*Id \$id" --glob "**/Domain/**/Entity/**/*.php"
```

## Value Object

### Definition
Immutable object defined by its attributes, not identity.

### Characteristics
- No identity
- Immutable
- Equality by attributes
- Self-validating
- Side-effect free methods

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\ValueObject;

final readonly class Email
{
    public function __construct(
        public string $value
    ) {
        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidEmailException($value);
        }
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function domain(): string
    {
        return substr($this->value, strpos($this->value, '@') + 1);
    }

    public function __toString(): string
    {
        return $this->value;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\ValueObject;

final readonly class Money
{
    public function __construct(
        public int $amount,
        public string $currency
    ) {
        if ($amount < 0) {
            throw new NegativeMoneyException($amount);
        }
    }

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->amount + $other->amount, $this->currency);
    }

    public function multiply(int $factor): self
    {
        return new self($this->amount * $factor, $this->currency);
    }

    public function equals(self $other): bool
    {
        return $this->amount === $other->amount
            && $this->currency === $other->currency;
    }

    public static function zero(string $currency): self
    {
        return new self(0, $currency);
    }

    private function ensureSameCurrency(self $other): void
    {
        if ($this->currency !== $other->currency) {
            throw new CurrencyMismatchException($this->currency, $other->currency);
        }
    }
}
```

### Common Value Objects

| Concept | Value Object | Validation |
|---------|--------------|------------|
| Identity | `UserId`, `OrderId` | UUID format |
| Contact | `Email`, `Phone` | Format validation |
| Money | `Money`, `Price` | Non-negative, currency |
| Address | `Address` | Required fields |
| Period | `DateRange` | Start < End |
| Quantity | `Quantity` | Non-negative |

### Detection Patterns

```bash
# Good - Value Objects exist
Glob: **/Domain/**/ValueObject/**/*.php
Glob: **/Domain/**/*Id.php
Glob: **/Domain/**/*Email.php

# Good - Readonly class
Grep: "final readonly class" --glob "**/Domain/**/ValueObject/**/*.php"

# Bad - Mutable Value Object
Grep: "public function set" --glob "**/Domain/**/ValueObject/**/*.php"
```

## Aggregate

### Definition
Cluster of entities and value objects with a root entity that ensures consistency.

### Characteristics
- Single entry point (Aggregate Root)
- Transactional boundary
- References by ID only (between aggregates)
- Invariants maintained internally

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Aggregate;

use Domain\Order\Entity\Order;
use Domain\Order\Entity\OrderLine;
use Domain\Order\ValueObject\OrderId;

// Order is the Aggregate Root
// OrderLine is part of the aggregate, accessed only through Order

final class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId  // Reference by ID, not entity
    ) {}

    // All modifications go through the root
    public function addLine(ProductId $productId, Quantity $quantity, Money $price): void
    {
        // Invariant: max 100 lines per order
        if (count($this->lines) >= 100) {
            throw new TooManyOrderLinesException($this->id);
        }

        $this->lines[] = new OrderLine(
            OrderLineId::generate(),
            $productId,
            $quantity,
            $price
        );
    }

    public function removeLine(OrderLineId $lineId): void
    {
        $this->lines = array_filter(
            $this->lines,
            fn(OrderLine $line) => !$line->id()->equals($lineId)
        );
    }

    // Invariant check
    public function canBeConfirmed(): bool
    {
        return !empty($this->lines) && $this->total()->amount > 0;
    }
}
```

### Rules

1. **Reference other aggregates by ID only**
   ```php
   // Good
   private readonly CustomerId $customerId;

   // Bad
   private readonly Customer $customer;
   ```

2. **Modify only through root**
   ```php
   // Good
   $order->addLine($productId, $quantity, $price);

   // Bad
   $order->getLines()[0]->setQuantity(5);
   ```

3. **One aggregate per transaction**

### Detection Patterns

```bash
# Warning - Aggregate holding entity reference
Grep: "private readonly [A-Z][a-z]+[^I][^d] \$" --glob "**/Domain/**/Aggregate/**/*.php"

# Good - Reference by ID
Grep: "private readonly.*Id \$" --glob "**/Domain/**/Aggregate/**/*.php"
```

## Repository Interface

### Definition
Contract for aggregate persistence, defined in Domain.

### Characteristics
- Interface in Domain
- Implementation in Infrastructure
- Works with aggregates, not entities
- Returns domain objects, not arrays

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderStatus;

interface OrderRepositoryInterface
{
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
}
```

### Rules

1. **Interface in Domain, implementation in Infrastructure**
2. **Work with aggregate roots only**
3. **Use Value Objects for queries, not primitives**
4. **No query builder or SQL in interface**

### Detection Patterns

```bash
# Good - Interface in Domain
Grep: "interface.*Repository" --glob "**/Domain/**/*.php"

# Good - Implementation in Infrastructure
Grep: "implements.*Repository" --glob "**/Infrastructure/**/*.php"

# Bad - Implementation in Domain
Grep: "class.*Repository" --glob "**/Domain/**/*.php" | grep -v Interface
```

## Domain Service

### Definition
Stateless operation that doesn't naturally belong to an entity.

### Characteristics
- Stateless
- Named after domain action
- Uses domain language
- Coordinates multiple aggregates

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Service;

use Domain\Order\Entity\Order;
use Domain\Customer\Entity\Customer;
use Domain\Pricing\ValueObject\Discount;

final readonly class PricingService
{
    public function __construct(
        private DiscountPolicyInterface $discountPolicy
    ) {}

    public function calculateDiscount(Order $order, Customer $customer): Discount
    {
        $baseDiscount = $this->discountPolicy->calculate($order->total());

        if ($customer->isVip()) {
            return $baseDiscount->increase(Percentage::fromInt(10));
        }

        return $baseDiscount;
    }
}
```

### When to Use

| Use Domain Service | Use Entity Method |
|--------------------|-------------------|
| Involves multiple aggregates | Single aggregate operation |
| Complex calculation | Simple state change |
| External policy needed | Self-contained logic |

## Domain Event

### Definition
Record of something that happened in the domain.

### Characteristics
- Immutable
- Named in past tense
- Contains all relevant data
- Timestamped

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

use Domain\Order\ValueObject\OrderId;
use Domain\Shared\ValueObject\Money;

final readonly class OrderConfirmedEvent
{
    public function __construct(
        public OrderId $orderId,
        public Money $total,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable()
    ) {}
}
```

### Detection Patterns

```bash
# Good - Events in Domain
Glob: **/Domain/**/Event/**/*.php
Glob: **/Domain/**/*Event.php

# Good - Immutable events
Grep: "final readonly class.*Event" --glob "**/Domain/**/*.php"
```