# Single Responsibility Principle (SRP) Patterns

## Definition

A class should have only one reason to change. Each class should encapsulate one responsibility and do it well.

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| God class (>500 LOC) | Line count analysis | CRITICAL |
| >7 dependencies | Constructor analysis | WARNING |
| Name contains "And/Or" | Name pattern | WARNING |
| Multiple public method groups | Method grouping | WARNING |
| Changes for multiple reasons | Git history analysis | INFO |

### Compliance Signs

- Class fits on one screen (~200 lines)
- Single constructor with ≤5 dependencies
- Clear, focused name (noun + responsibility)
- All methods relate to same abstraction

## Refactoring Patterns

### Extract Class

```php
<?php

declare(strict_types=1);

// BEFORE: Multiple responsibilities
final class User
{
    public function save(): void { /* DB logic */ }
    public function validate(): bool { /* Validation logic */ }
    public function sendWelcomeEmail(): void { /* Email logic */ }
    public function calculateDiscount(): Money { /* Business logic */ }
}

// AFTER: Separated responsibilities
final readonly class User
{
    public function __construct(
        public UserId $id,
        public Email $email,
        public UserStatus $status,
    ) {}

    public function activate(): self
    {
        return new self($this->id, $this->email, UserStatus::Active);
    }
}

final readonly class UserRepository
{
    public function save(User $user): void { /* DB logic */ }
}

final readonly class UserValidator
{
    public function validate(User $user): ValidationResult { /* ... */ }
}

final readonly class WelcomeEmailSender
{
    public function send(User $user): void { /* ... */ }
}

final readonly class DiscountCalculator
{
    public function calculate(User $user): Money { /* ... */ }
}
```

### Use Command/Query Handlers

```php
<?php

declare(strict_types=1);

// BEFORE: Service with many methods
final class OrderService
{
    public function create(array $data): Order { /* ... */ }
    public function cancel(int $id): void { /* ... */ }
    public function ship(int $id): void { /* ... */ }
    public function refund(int $id): void { /* ... */ }
    public function getById(int $id): Order { /* ... */ }
    public function getByUser(int $userId): array { /* ... */ }
}

// AFTER: Single-responsibility handlers
final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderRepository $orders,
        private EventDispatcher $events,
    ) {}

    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create($command->items, $command->customerId);
        $this->orders->save($order);
        $this->events->dispatch($order->releaseEvents());

        return $order->id;
    }
}

final readonly class CancelOrderHandler
{
    public function __invoke(CancelOrderCommand $command): void { /* ... */ }
}

final readonly class GetOrderByIdQuery
{
    public function __invoke(OrderId $id): OrderDTO { /* ... */ }
}
```

### Facade for Coordination

```php
<?php

declare(strict_types=1);

// When coordination is needed, use a thin facade
final readonly class OrderFacade
{
    public function __construct(
        private CreateOrderHandler $createHandler,
        private CancelOrderHandler $cancelHandler,
        private GetOrderByIdQuery $getQuery,
    ) {}

    public function create(CreateOrderCommand $command): OrderId
    {
        return ($this->createHandler)($command);
    }

    public function cancel(CancelOrderCommand $command): void
    {
        ($this->cancelHandler)($command);
    }

    public function get(OrderId $id): OrderDTO
    {
        return ($this->getQuery)($id);
    }
}
```

## DDD Application

### Aggregate Root

Each aggregate has single consistency boundary:

```php
<?php

declare(strict_types=1);

// One aggregate = one transactional boundary
final class Order
{
    private OrderId $id;
    private CustomerId $customerId;
    /** @var OrderLine[] */
    private array $lines = [];
    private OrderStatus $status;
    /** @var DomainEvent[] */
    private array $events = [];

    // All methods maintain THIS aggregate's consistency
    public function addLine(Product $product, Quantity $quantity): void
    {
        $this->ensureNotShipped();
        $this->lines[] = new OrderLine($product, $quantity);
        $this->events[] = new OrderLineAdded($this->id, $product->id);
    }

    public function ship(): void
    {
        $this->ensureCanShip();
        $this->status = OrderStatus::Shipped;
        $this->events[] = new OrderShipped($this->id);
    }

    private function ensureNotShipped(): void { /* ... */ }
    private function ensureCanShip(): void { /* ... */ }
}
```

### Domain Service

When logic spans multiple aggregates:

```php
<?php

declare(strict_types=1);

// Single responsibility: transfer money between accounts
final readonly class MoneyTransferService
{
    public function transfer(
        Account $source,
        Account $destination,
        Money $amount,
    ): void {
        $source->debit($amount);
        $destination->credit($amount);
    }
}
```

## Testing Benefits

SRP makes testing easier:

```php
<?php

declare(strict_types=1);

#[CoversClass(CreateOrderHandler::class)]
final class CreateOrderHandlerTest extends TestCase
{
    // Test only order creation logic
    // No email, no reports, no validation
    public function testCreatesOrderFromCommand(): void
    {
        $handler = new CreateOrderHandler(
            $this->createMock(OrderRepository::class),
            $this->createMock(EventDispatcher::class),
        );

        $result = ($handler)(new CreateOrderCommand(/* ... */));

        $this->assertInstanceOf(OrderId::class, $result);
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Lines of code | <200 | 200-500 | >500 |
| Dependencies | ≤5 | 6-7 | >7 |
| Public methods | ≤7 | 8-10 | >10 |
| Cyclomatic complexity | ≤10 | 11-20 | >20 |
