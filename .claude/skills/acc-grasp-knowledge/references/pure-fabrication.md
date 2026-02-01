# Pure Fabrication Pattern

## Definition

Assign a highly cohesive set of responsibilities to an artificial or convenience class that does not represent a domain concept — a fabrication of the imagination.

## When to Apply

- Information Expert would result in poor cohesion or coupling
- Need infrastructure services (persistence, logging)
- Cross-cutting concerns don't fit domain objects
- Reusability requires non-domain abstraction

## Key Indicators

### When to Use

| Situation | Example |
|-----------|---------|
| Persistence | Repository, Data Mapper |
| Infrastructure | Event Dispatcher, Logger |
| Calculations | Specification, Calculator |
| Creation | Factory, Builder |
| Cross-cutting | Policy, Validator |

### Common Pure Fabrications in DDD

| Pattern | Purpose |
|---------|---------|
| Repository | Aggregate persistence abstraction |
| Factory | Complex object creation |
| Domain Service | Cross-entity business logic |
| Specification | Reusable business rules |
| Event Dispatcher | Domain event distribution |
| Query Handler | Read model construction |

## Patterns

### Repository

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Not a domain concept
interface OrderRepository
{
    public function nextIdentity(): OrderId;
    public function find(OrderId $id): ?Order;
    public function get(OrderId $id): Order;
    public function save(Order $order): void;
    public function remove(Order $order): void;
}

final readonly class DoctrineOrderRepository implements OrderRepository
{
    public function __construct(
        private EntityManagerInterface $em,
        private IdGenerator $idGenerator,
    ) {}

    public function nextIdentity(): OrderId
    {
        return new OrderId($this->idGenerator->generate());
    }

    public function find(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function get(OrderId $id): Order
    {
        return $this->find($id)
            ?? throw new OrderNotFoundException($id);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function remove(Order $order): void
    {
        $this->em->remove($order);
        $this->em->flush();
    }
}
```

### Factory

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Encapsulates complex creation
interface OrderFactory
{
    public function createFromCart(CustomerId $customerId, Cart $cart): Order;
    public function createFromCommand(CreateOrderCommand $command): Order;
}

final readonly class DefaultOrderFactory implements OrderFactory
{
    public function __construct(
        private OrderRepository $repository,
        private ProductReader $products,
        private Clock $clock,
    ) {}

    public function createFromCart(CustomerId $customerId, Cart $cart): Order
    {
        $order = new Order(
            $this->repository->nextIdentity(),
            $customerId,
            $this->clock->now(),
        );

        foreach ($cart->items() as $item) {
            $product = $this->products->get($item->productId);
            $order->addLine($product, $item->quantity);
        }

        return $order;
    }

    public function createFromCommand(CreateOrderCommand $command): Order
    {
        $order = new Order(
            $this->repository->nextIdentity(),
            $command->customerId,
            $this->clock->now(),
        );

        foreach ($command->items as $item) {
            $product = $this->products->get($item->productId);
            $order->addLine($product, $item->quantity);
        }

        return $order;
    }
}
```

### Specification

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Reusable business rule
interface Specification
{
    public function isSatisfiedBy(mixed $candidate): bool;
}

abstract readonly class CompositeSpecification implements Specification
{
    public function and(Specification $other): Specification
    {
        return new AndSpecification($this, $other);
    }

    public function or(Specification $other): Specification
    {
        return new OrSpecification($this, $other);
    }

    public function not(): Specification
    {
        return new NotSpecification($this);
    }
}

final readonly class EligibleForFreeShippingSpecification extends CompositeSpecification
{
    public function __construct(
        private Money $minimumOrderValue,
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Order) {
            return false;
        }

        return $candidate->total()->isGreaterThanOrEqual($this->minimumOrderValue);
    }
}

final readonly class PremiumCustomerSpecification extends CompositeSpecification
{
    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Customer) {
            return false;
        }

        return $candidate->tier === CustomerTier::Premium
            || $candidate->tier === CustomerTier::Vip;
    }
}

// Usage
$freeShipping = new EligibleForFreeShippingSpecification(Money::fromCents(5000));
$premiumCustomer = new PremiumCustomerSpecification();

$eligibleForDiscount = $freeShipping->and($premiumCustomer);
```

### Domain Service

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Logic that doesn't belong to a single entity
interface MoneyTransferService
{
    public function transfer(Account $from, Account $to, Money $amount): void;
}

final readonly class DefaultMoneyTransferService implements MoneyTransferService
{
    public function __construct(
        private TransactionRepository $transactions,
        private Clock $clock,
    ) {}

    public function transfer(Account $from, Account $to, Money $amount): void
    {
        if (!$from->canWithdraw($amount)) {
            throw new InsufficientFundsException($from->id, $amount);
        }

        $from->debit($amount);
        $to->credit($amount);

        $this->transactions->save(
            new Transaction(
                $this->transactions->nextIdentity(),
                $from->id,
                $to->id,
                $amount,
                $this->clock->now(),
            ),
        );
    }
}
```

### Event Dispatcher

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Infrastructure service
interface EventDispatcher
{
    public function dispatch(DomainEvent ...$events): void;
}

final class SyncEventDispatcher implements EventDispatcher
{
    /** @var array<string, array<callable>> */
    private array $listeners = [];

    public function subscribe(string $eventClass, callable $listener): void
    {
        $this->listeners[$eventClass][] = $listener;
    }

    public function dispatch(DomainEvent ...$events): void
    {
        foreach ($events as $event) {
            $eventClass = get_class($event);
            foreach ($this->listeners[$eventClass] ?? [] as $listener) {
                $listener($event);
            }
        }
    }
}
```

### Query Handler (Read Model)

```php
<?php

declare(strict_types=1);

// Pure Fabrication: CQRS read side
interface OrderSummaryQuery
{
    public function execute(GetOrderSummaryQuery $query): OrderSummaryDTO;
}

final readonly class OrderSummaryQueryHandler implements OrderSummaryQuery
{
    public function __construct(
        private Connection $connection,
    ) {}

    public function execute(GetOrderSummaryQuery $query): OrderSummaryDTO
    {
        $row = $this->connection->fetchAssociative(
            'SELECT o.id, o.customer_name, o.total, o.status,
                    COUNT(ol.id) as line_count
             FROM orders o
             LEFT JOIN order_lines ol ON ol.order_id = o.id
             WHERE o.id = :id
             GROUP BY o.id',
            ['id' => $query->orderId->value],
        );

        if ($row === false) {
            throw new OrderNotFoundException($query->orderId);
        }

        return new OrderSummaryDTO(
            id: $row['id'],
            customerName: $row['customer_name'],
            total: $row['total'],
            status: $row['status'],
            lineCount: (int) $row['line_count'],
        );
    }
}
```

### Policy

```php
<?php

declare(strict_types=1);

// Pure Fabrication: Authorization/business rules
interface OrderCancellationPolicy
{
    public function canCancel(Order $order, User $user): bool;
}

final readonly class DefaultOrderCancellationPolicy implements OrderCancellationPolicy
{
    public function __construct(
        private Clock $clock,
    ) {}

    public function canCancel(Order $order, User $user): bool
    {
        // Admin can always cancel
        if ($user->isAdmin()) {
            return true;
        }

        // Only owner can cancel
        if (!$order->belongsTo($user->customerId)) {
            return false;
        }

        // Can't cancel shipped orders
        if ($order->isShipped()) {
            return false;
        }

        // Can only cancel within 24 hours
        $placedAt = $order->placedAt;
        $now = $this->clock->now();
        $hoursSincePlaced = ($now->getTimestamp() - $placedAt->getTimestamp()) / 3600;

        return $hoursSincePlaced <= 24;
    }
}
```

## DDD Layer Placement

| Fabrication | Layer | Purpose |
|-------------|-------|---------|
| Repository Interface | Domain | Aggregate persistence contract |
| Repository Implementation | Infrastructure | Actual persistence |
| Factory | Domain or Application | Object creation |
| Specification | Domain | Business rules |
| Domain Service | Domain | Cross-entity logic |
| Event Dispatcher | Application/Infrastructure | Event distribution |
| Query Handler | Application | Read model |
| Policy | Domain | Authorization rules |

## Anti-patterns

### Overusing Pure Fabrication

```php
<?php

// ANTIPATTERN: Creating fabrication when Information Expert works
final readonly class OrderTotalCalculator
{
    public function calculate(Order $order): Money
    {
        // Order has all the data - should be Order::total()
        $total = Money::zero();
        foreach ($order->getLines() as $line) {
            $total = $total->add($line->getPrice()->multiply($line->getQuantity()));
        }
        return $total;
    }
}

// FIX: Use Information Expert
final class Order
{
    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn(Money $sum, OrderLine $line) => $sum->add($line->total()),
            Money::zero(),
        );
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Fabrication per aggregate | 1-3 | 4-5 | >5 |
| Fabrication complexity | <100 LOC | 100-200 | >200 |
| Domain logic in fabrication | 0% | <10% | >10% |
