---
name: acc-create-aggregate
description: Generates DDD Aggregates for PHP 8.4. Creates consistency boundaries with root entity, domain events, and invariant protection. Includes unit tests.
---

# Aggregate Generator

Generate DDD-compliant Aggregates with root, domain events, and tests.

## Aggregate Characteristics

- **Consistency boundary**: All changes atomic
- **Root entity**: Single entry point
- **Transactional consistency**: Invariants always valid
- **Domain events**: Records what happened
- **Encapsulation**: Children accessed through root
- **Identity**: Referenced by root ID

## Template

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\ValueObject\{Name}Id;
use Domain\{BoundedContext}\Enum\{Name}Status;
use Domain\{BoundedContext}\Event\{Events};
use Domain\Shared\Aggregate\AggregateRoot;

final class {Name} extends AggregateRoot
{
    private {Name}Status $status;
    {privateProperties}
    private DateTimeImmutable $createdAt;

    private function __construct(
        private readonly {Name}Id $id,
        {constructorProperties}
    ) {
        $this->status = {Name}Status::default();
        $this->createdAt = new DateTimeImmutable();
    }

    public static function create(
        {Name}Id $id,
        {factoryProperties}
    ): self {
        $aggregate = new self($id, {constructorArgs});

        $aggregate->recordEvent(new {Name}CreatedEvent(
            {eventProperties}
        ));

        return $aggregate;
    }

    public function id(): {Name}Id
    {
        return $this->id;
    }

    {behaviorMethods}
}
```

## Base Aggregate Root

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Aggregate;

use Domain\Shared\Event\DomainEvent;

abstract class AggregateRoot
{
    /** @var array<DomainEvent> */
    private array $events = [];

    protected function recordEvent(DomainEvent $event): void
    {
        $this->events[] = $event;
    }

    /**
     * @return array<DomainEvent>
     */
    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }

    public function hasUncommittedEvents(): bool
    {
        return !empty($this->events);
    }
}
```

## Complete Aggregate Example

### Order Aggregate

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Event\OrderCreatedEvent;
use Domain\Order\Event\OrderLineAddedEvent;
use Domain\Order\Event\OrderConfirmedEvent;
use Domain\Order\Event\OrderCancelledEvent;
use Domain\Order\Exception\CannotModifyConfirmedOrderException;
use Domain\Order\Exception\CannotConfirmEmptyOrderException;
use Domain\Order\Exception\InvalidStateTransitionException;
use Domain\Shared\Aggregate\AggregateRoot;

final class Order extends AggregateRoot
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    private DateTimeImmutable $createdAt;
    private ?DateTimeImmutable $confirmedAt = null;

    private function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId
    ) {
        $this->status = OrderStatus::Draft;
        $this->createdAt = new DateTimeImmutable();
    }

    public static function create(OrderId $id, CustomerId $customerId): self
    {
        $order = new self($id, $customerId);

        $order->recordEvent(new OrderCreatedEvent(
            orderId: $id->value,
            customerId: $customerId->value,
            createdAt: $order->createdAt
        ));

        return $order;
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function customerId(): CustomerId
    {
        return $this->customerId;
    }

    public function status(): OrderStatus
    {
        return $this->status;
    }

    public function addLine(
        ProductId $productId,
        string $productName,
        int $quantity,
        Money $unitPrice
    ): void {
        $this->ensureDraft();

        if ($quantity <= 0) {
            throw new InvalidQuantityException($quantity);
        }

        $line = new OrderLine(
            productId: $productId,
            productName: $productName,
            quantity: $quantity,
            unitPrice: $unitPrice
        );

        $this->lines[] = $line;

        $this->recordEvent(new OrderLineAddedEvent(
            orderId: $this->id->value,
            productId: $productId->value,
            productName: $productName,
            quantity: $quantity,
            unitPriceCents: $unitPrice->cents(),
            currency: $unitPrice->currency()
        ));
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException(
                from: $this->status,
                to: OrderStatus::Confirmed
            );
        }

        if (empty($this->lines)) {
            throw new CannotConfirmEmptyOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
        $this->confirmedAt = new DateTimeImmutable();

        $this->recordEvent(new OrderConfirmedEvent(
            orderId: $this->id->value,
            totalCents: $this->total()->cents(),
            currency: $this->total()->currency(),
            confirmedAt: $this->confirmedAt
        ));
    }

    public function cancel(string $reason): void
    {
        if (!$this->status->canBeCancelled()) {
            throw new InvalidStateTransitionException(
                from: $this->status,
                to: OrderStatus::Cancelled
            );
        }

        $this->status = OrderStatus::Cancelled;

        $this->recordEvent(new OrderCancelledEvent(
            orderId: $this->id->value,
            reason: $reason,
            cancelledAt: new DateTimeImmutable()
        ));
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn (Money $carry, OrderLine $line) => $carry->add($line->total()),
            Money::zero('USD')
        );
    }

    /**
     * @return array<OrderLine>
     */
    public function lines(): array
    {
        return $this->lines;
    }

    public function lineCount(): int
    {
        return count($this->lines);
    }

    public function isEmpty(): bool
    {
        return empty($this->lines);
    }

    private function ensureDraft(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotModifyConfirmedOrderException($this->id);
        }
    }
}
```

### OrderLine (Child Entity)

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\ProductId;
use Domain\Order\ValueObject\Money;

final readonly class OrderLine
{
    public function __construct(
        public ProductId $productId,
        public string $productName,
        public int $quantity,
        public Money $unitPrice
    ) {}

    public function total(): Money
    {
        return $this->unitPrice->multiply($this->quantity);
    }
}
```

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Entity;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\ValueObject\Money;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Event\OrderCreatedEvent;
use Domain\Order\Event\OrderLineAddedEvent;
use Domain\Order\Event\OrderConfirmedEvent;
use Domain\Order\Exception\CannotConfirmEmptyOrderException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    public function testCreatesOrderWithEvent(): void
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: new CustomerId('customer-123')
        );

        self::assertSame(OrderStatus::Draft, $order->status());
        self::assertTrue($order->isEmpty());

        $events = $order->releaseEvents();
        self::assertCount(1, $events);
        self::assertInstanceOf(OrderCreatedEvent::class, $events[0]);
    }

    public function testAddLineRecordsEvent(): void
    {
        $order = $this->createOrder();

        $order->addLine(
            productId: new ProductId('product-1'),
            productName: 'Test Product',
            quantity: 2,
            unitPrice: new Money(1000, 'USD')
        );

        self::assertSame(1, $order->lineCount());

        $events = $order->releaseEvents();
        self::assertInstanceOf(OrderLineAddedEvent::class, $events[1]);
    }

    public function testConfirmOrderWithLines(): void
    {
        $order = $this->createOrderWithLine();

        $order->confirm();

        self::assertSame(OrderStatus::Confirmed, $order->status());

        $events = $order->releaseEvents();
        $lastEvent = end($events);
        self::assertInstanceOf(OrderConfirmedEvent::class, $lastEvent);
    }

    public function testCannotConfirmEmptyOrder(): void
    {
        $order = $this->createOrder();

        $this->expectException(CannotConfirmEmptyOrderException::class);

        $order->confirm();
    }

    public function testCalculatesTotal(): void
    {
        $order = $this->createOrder();

        $order->addLine(
            productId: new ProductId('product-1'),
            productName: 'Product 1',
            quantity: 2,
            unitPrice: new Money(1000, 'USD')
        );

        $order->addLine(
            productId: new ProductId('product-2'),
            productName: 'Product 2',
            quantity: 1,
            unitPrice: new Money(500, 'USD')
        );

        $total = $order->total();

        self::assertSame(2500, $total->cents());
        self::assertSame('USD', $total->currency());
    }

    private function createOrder(): Order
    {
        return Order::create(
            id: OrderId::generate(),
            customerId: new CustomerId('customer-123')
        );
    }

    private function createOrderWithLine(): Order
    {
        $order = $this->createOrder();

        $order->addLine(
            productId: new ProductId('product-1'),
            productName: 'Test Product',
            quantity: 1,
            unitPrice: new Money(1000, 'USD')
        );

        return $order;
    }
}
```

## Aggregate Design Rules

### 1. Single Transaction Boundary

```php
// GOOD: One aggregate per transaction
$order = $this->orderRepository->findById($orderId);
$order->confirm();
$this->orderRepository->save($order);

// BAD: Multiple aggregates in one transaction
$order = $this->orderRepository->findById($orderId);
$inventory = $this->inventoryRepository->findByProductId($productId);
$order->confirm();
$inventory->reserve($quantity);  // Different aggregate!
$this->orderRepository->save($order);
$this->inventoryRepository->save($inventory);
```

### 2. Reference by ID

```php
// GOOD: Reference by ID
final class Order
{
    private readonly CustomerId $customerId;  // Just the ID
}

// BAD: Direct reference
final class Order
{
    private Customer $customer;  // Full entity reference
}
```

### 3. Small Aggregates

```php
// GOOD: Small, focused aggregate
final class Order
{
    private readonly OrderId $id;
    private array $lines = [];  // Limited collection
}

// BAD: Large aggregate
final class Customer
{
    private array $orders = [];      // All orders ever!
    private array $addresses = [];   // All addresses!
    private array $payments = [];    // All payments!
}
```

## Generation Instructions

When asked to create an Aggregate:

1. **Identify the root entity** (entry point)
2. **Define the boundary** (what's inside)
3. **List domain events** to record
4. **Design behavior methods**
5. **Protect invariants**
6. **Generate tests** for events and behavior

## Usage

To generate an Aggregate, provide:
- Name (e.g., "Order", "ShoppingCart")
- Bounded Context (e.g., "Order", "Cart")
- Root entity identity
- Child entities/VOs
- Domain events to emit
- Key behaviors and invariants
