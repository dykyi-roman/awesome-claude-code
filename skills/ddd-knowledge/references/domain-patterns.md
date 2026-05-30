# Domain Patterns

Detailed patterns for the DDD domain model in PHP — entities, value objects, aggregates, repositories, domain services, events. These are conceptual patterns; their physical placement varies by architecture (see [`layer-architecture.md`](layer-architecture.md) for the per-architecture placement table).

## Entity

### Definition
Object with unique identity that persists through time and state changes.

### Characteristics
- Has a unique identifier
- Mutable state
- Equality based on identity, not attributes
- Contains behavior (not just data)

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Entity;

use ValueObject\OrderId;
use ValueObject\OrderStatus;
use ValueObject\OrderLine;
use Event\OrderConfirmedEvent;
use ValueObject\Money;

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

Suffix-based globs work across architectures (Clean / Hexagonal / Layered 3-tier / N-Tier / PBF / MVC):

```bash
# Entities by file or class-name suffix
Glob: **/*Entity.php
Glob: **/Entity/**/*.php

# Anti-pattern: anemic entity (only getters/setters, no behavior)
Grep: "public function (get|set|is|has)[A-Z]" --glob "**/*Entity.php"

# Entity has an ID field
Grep: "private readonly.*Id \\\$id" --glob "**/*Entity.php"
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

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace ValueObject;

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

namespace ValueObject;

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
# Value Objects by file or folder suffix
Glob: **/ValueObject/**/*.php
Glob: **/*ValueObject.php
Glob: **/*Id.php
Glob: **/*Email.php

# Immutable VO (final readonly)
Grep: "final readonly class" --glob "**/ValueObject/**/*.php"
Grep: "final readonly class" --glob "**/*ValueObject.php"

# Anti-pattern: mutable Value Object
Grep: "public function set" --glob "**/ValueObject/**/*.php"
Grep: "public function set" --glob "**/*ValueObject.php"
```

## Aggregate

### Definition
Cluster of entities and value objects with a root entity that ensures consistency.

### Characteristics
- Single entry point (Aggregate Root)
- Transactional boundary
- References by ID only (between aggregates)
- Invariants maintained internally

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Aggregate;

use Entity\Order;
use Entity\OrderLine;
use ValueObject\OrderId;

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
# Aggregates by file or folder suffix
Glob: **/Aggregate/**/*.php
Glob: **/*Aggregate.php
Glob: **/*AggregateRoot.php

# Anti-pattern: Aggregate holding an entity reference instead of an ID
Grep: "private readonly [A-Z][a-z]+[^I][^d] \\\$" --glob "**/Aggregate/**/*.php"

# Good: references by ID Value Object
Grep: "private readonly.*Id \\\$" --glob "**/Aggregate/**/*.php"
```

## Repository

### Definition
Collection-like abstraction for accessing aggregates. The Repository is a single domain pattern — DDD does not divide it into separate "interface" and "implementation" concepts. The abstraction and a concrete realization both exist; how they are split into PHP classes and where those classes live varies by architecture.

### Characteristics
- Abstraction (typically a PHP interface or abstract class)
- Operates on aggregate roots, not on internal entities
- Returns domain objects, not arrays or row data
- Uses Value Objects for query parameters, not primitives
- Query-side methods CAN encode business intent (`findShippableOrdersForToday()`)
- Save-side methods do not contain business logic (no validation, calculation, or state change in `save()`)

### Placement varies by architecture

| Architecture | Abstraction lives | Concrete class lives |
|---|---|---|
| Clean | `Application/{Context}/Port/` or `Domain/{Context}/Repository/` (project choice) | `Infrastructure/{Persistence}/` |
| Hexagonal | `Domain/{Context}/Port/Output/` (Driven Port) | `Infrastructure/Persistence/{Doctrine}/` (Driven Adapter) |
| Layered (3-tier Domain-centric) | `Domain/{Context}/Repository/` | `Domain/{Context}/Repository/Doctrine/` — alongside the abstraction |
| N-Tier (4-tier Classical) | `Domain/{Context}/Repository/` | `Infrastructure/Persistence/` |
| Package-by-Feature | per inner architecture, scoped to `{Feature}/` | per inner architecture, scoped to `{Feature}/` |
| MVC | folded into the Model or a sub-folder of Model | folded into the Model |

See [`layer-architecture.md`](layer-architecture.md) for the full context.

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Repository;

use Entity\Order;
use ValueObject\OrderId;
use ValueObject\OrderStatus;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    public function save(Order $order): void;

    public function delete(Order $order): void;

    /**
     * @return list<Order>
     */
    public function findByCustomer(CustomerId $customerId): array;

    /**
     * Query-side business intent — finding what the domain calls
     * "active orders for a status" — is correct Repository content.
     *
     * @return list<Order>
     */
    public function findByStatus(OrderStatus $status, int $limit = 100): array;
}
```

### Rules

1. **Repository is an abstraction over a collection of aggregates** — code calling the Repository works against the contract, not a concrete implementation.
2. **Operate on aggregate roots only** — don't expose child entities directly.
3. **Use Value Objects for queries** — `findByStatus(OrderStatus $status)`, not `findByStatus(string $status)`.
4. **No query builder or SQL types in the abstraction** — Doctrine `Criteria`, `QueryBuilder`, etc. belong in the concrete class.
5. **No business logic in `save()`** — save persists; calculation/validation/state-change belongs on the aggregate.
6. **Folder placement is architectural choice** — see the table above. Don't assert one placement as universally correct.

### Detection patterns

Use suffix-based matching so the checks work regardless of architecture:

```bash
# Repository abstractions (any architecture)
Glob: **/*RepositoryInterface.php
Grep: "interface.*Repository" --glob "**/*.php"

# Repository concrete classes (any architecture; common suffix patterns)
Glob: **/Doctrine/*Repository.php
Glob: **/Persistence/**/*Repository.php
Grep: "implements.*Repository" --glob "**/*.php"

# Anti-pattern: business logic inside a Repository class
Grep: "private function calculate|private function validate" --glob "**/*Repository.php"

# Anti-pattern: primitive query parameter where a Value Object exists
Grep: "find.*\(string \\\$|find.*\(int \\\$" --glob "**/*Repository*.php"
```

Architecture-specific Repository-placement checks (only run the one matching the project's architecture):

```bash
# CLEAN / N-TIER projects: concrete Repository class found inside Domain
# (in Layered 3-tier this is CORRECT — do NOT flag)
Grep: "class.*Repository" --glob "**/Domain/**/*.php" | grep -v Interface

# LAYERED 3-TIER projects: concrete Repository class found in Infrastructure
# (in Clean/Hexagonal/N-Tier this is CORRECT — do NOT flag)
Glob: **/Infrastructure/**/*Repository.php
```

## Domain Service

### Definition
Stateless operation that doesn't naturally belong to an entity.

### Characteristics
- Stateless
- Named after domain action
- Uses domain language
- Coordinates multiple aggregates

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Service;

use Entity\Order;
use Entity\Customer;
use ValueObject\Discount;

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

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Event;

use ValueObject\OrderId;
use ValueObject\Money;

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
# Domain Events by file or folder suffix
Glob: **/Event/**/*.php
Glob: **/*Event.php

# Immutable events (final readonly)
Grep: "final readonly class.*Event" --glob "**/*Event.php"
Grep: "final readonly class.*Event" --glob "**/Event/**/*.php"
```