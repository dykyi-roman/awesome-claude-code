# Command Patterns

Detailed patterns for CQRS Command implementation in PHP.

## Command Definition

### What is a Command?

A Command is an immutable object representing a request to change system state.

### Characteristics

- **Imperative naming**: verb + noun (CreateOrder, UpdateProfile, DeleteComment)
- **Immutable**: readonly class, no setters
- **Self-validating**: validates invariants in constructor
- **Intent-revealing**: name describes what should happen
- **Returns void or ID**: never returns data

## PHP 8.5 Implementation

### Basic Command

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;

final readonly class CreateOrderCommand
{
    public function __construct(
        public CustomerId $customerId,
        public Money $total,
        public ?string $notes = null
    ) {}
}
```

### Command with Validation

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

final readonly class AddOrderLineCommand
{
    public function __construct(
        public OrderId $orderId,
        public ProductId $productId,
        public int $quantity,
        public Money $unitPrice
    ) {
        if ($quantity <= 0) {
            throw new InvalidArgumentException('Quantity must be positive');
        }
    }
}
```

### Command with Factory

```php
<?php

declare(strict_types=1);

namespace Application\Order\Command;

final readonly class ConfirmOrderCommand
{
    public function __construct(
        public OrderId $orderId,
        public \DateTimeImmutable $confirmedAt
    ) {}

    public static function now(OrderId $orderId): self
    {
        return new self($orderId, new \DateTimeImmutable());
    }

    public static function fromArray(array $data): self
    {
        return new self(
            orderId: new OrderId($data['order_id']),
            confirmedAt: new \DateTimeImmutable($data['confirmed_at'] ?? 'now')
        );
    }
}
```

## Command Naming Conventions

### Good Names (Imperative Verbs)

| Domain | Command Name |
|--------|--------------|
| Order | `CreateOrder`, `ConfirmOrder`, `CancelOrder`, `AddOrderLine` |
| Payment | `ProcessPayment`, `RefundPayment`, `CapturePayment` |
| User | `RegisterUser`, `UpdateProfile`, `DeactivateAccount` |
| Inventory | `ReserveStock`, `ReleaseStock`, `AdjustInventory` |

### Bad Names (Avoid)

| Bad Name | Why | Better Name |
|----------|-----|-------------|
| `OrderCommand` | Vague, not imperative | `CreateOrderCommand` |
| `DoOrder` | Meaningless verb | `PlaceOrderCommand` |
| `OrderCreation` | Noun, not verb | `CreateOrderCommand` |
| `GetOrderCommand` | Query, not command | `GetOrderQuery` |

## Command Validation Strategy

### Where to Validate

| Layer | What to Validate | Example |
|-------|------------------|---------|
| Presentation | Format, required fields | UUID format, non-empty |
| Command | Command invariants | Quantity > 0 |
| Handler | Authorization | User can modify order |
| Domain | Business rules | Order can be confirmed |

### Validation in Command

```php
final readonly class TransferMoneyCommand
{
    public function __construct(
        public AccountId $fromAccount,
        public AccountId $toAccount,
        public Money $amount
    ) {
        // Command invariants
        if ($fromAccount->equals($toAccount)) {
            throw new InvalidArgumentException('Cannot transfer to same account');
        }
        if ($amount->isNegativeOrZero()) {
            throw new InvalidArgumentException('Amount must be positive');
        }
    }
}
```

## Command Return Values

### Option 1: Void (Pure Command)

```php
final readonly class DeactivateAccountHandler
{
    public function __invoke(DeactivateAccountCommand $command): void
    {
        $account = $this->accounts->findById($command->accountId);
        $account->deactivate();
        $this->accounts->save($account);
    }
}
```

### Option 2: Created ID (Create Commands)

```php
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: $command->customerId
        );

        $this->orders->save($order);

        return $order->id();
    }
}
```

### Anti-Pattern: Returning Entity

```php
// BAD - Command returning rich data
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): Order  // BAD!
    {
        $order = Order::create(...);
        $this->orders->save($order);
        return $order;  // Violates CQRS
    }
}

// GOOD - Return only ID, use Query for details
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(...);
        $this->orders->save($order);
        return $order->id();  // Caller uses Query for details
    }
}
```

## Detection Patterns

```bash
# Good - Command classes exist
Glob: **/Command/**/*Command.php
Grep: "final readonly class.*Command" --glob "**/*.php"

# Good - Proper naming
Grep: "class (Create|Update|Delete|Add|Remove|Confirm|Cancel|Process)" --glob "**/*Command.php"

# Warning - Command returning entity
Grep: "function __invoke.*Command.*\): [A-Z][a-z]+" --glob "**/*Handler.php" | grep -v "Id\|void"

# Warning - Mutable command
Grep: "class.*Command[^{]*\{" --glob "**/*Command.php" | grep -v "readonly"

# Bad - Query-like command names
Grep: "class (Get|Find|List|Fetch|Load).*Command" --glob "**/*.php"
```

## Command Composition

### Single Aggregate Rule

One command should affect only one aggregate:

```php
// BAD - Affects multiple aggregates
final readonly class CreateOrderAndNotifyCommand
{
    public function __construct(
        public CustomerId $customerId,
        public array $lines,
        public string $notificationChannel  // Different aggregate
    ) {}
}

// GOOD - Single aggregate, use events for side effects
final readonly class CreateOrderCommand
{
    public function __construct(
        public CustomerId $customerId,
        public array $lines
    ) {}
}

// Handler dispatches event
public function __invoke(CreateOrderCommand $command): OrderId
{
    $order = Order::create(...);
    $this->orders->save($order);

    // Event triggers notification in separate handler
    $this->events->dispatch(new OrderCreatedEvent($order->id()));

    return $order->id();
}
```

## Idempotency

### Idempotent Command Design

```php
final readonly class CreateOrderCommand
{
    public function __construct(
        public OrderId $orderId,  // Client-generated ID
        public CustomerId $customerId,
        public array $lines
    ) {}
}

final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): OrderId
    {
        // Check if already processed
        if ($this->orders->exists($command->orderId)) {
            return $command->orderId;  // Idempotent
        }

        $order = Order::create(
            id: $command->orderId,  // Use provided ID
            customerId: $command->customerId,
            lines: $command->lines
        );

        $this->orders->save($order);

        return $order->id();
    }
}
```
