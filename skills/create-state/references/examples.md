# State Pattern Examples

## Order State Machine

### OrderStateInterface

**File:** `src/{architecture-path}/State/OrderStateInterface.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;

interface OrderStateInterface
{
    public function getName(): string;

    public function confirm(Order $order): self;

    public function pay(Order $order): self;

    public function ship(Order $order): self;

    public function deliver(Order $order): self;

    public function cancel(Order $order): self;

    public function refund(Order $order): self;

    /** @return array<string> */
    public function allowedTransitions(): array;

    public function canTransitionTo(self $state): bool;
}
```

### AbstractOrderState

**File:** `src/{architecture-path}/State/AbstractOrderState.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;
use Exception\InvalidStateTransitionException;

abstract readonly class AbstractOrderState implements OrderStateInterface
{
    public function confirm(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('confirm', $this->getName());
    }

    public function pay(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('pay', $this->getName());
    }

    public function ship(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('ship', $this->getName());
    }

    public function deliver(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('deliver', $this->getName());
    }

    public function cancel(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('cancel', $this->getName());
    }

    public function refund(Order $order): OrderStateInterface
    {
        throw InvalidStateTransitionException::actionNotAllowed('refund', $this->getName());
    }

    public function canTransitionTo(OrderStateInterface $state): bool
    {
        return in_array($state->getName(), $this->allowedTransitions(), true);
    }
}
```

### Concrete States

**File:** `src/{architecture-path}/State/PendingState.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;

final readonly class PendingState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'pending';
    }

    public function confirm(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderConfirmed($order->id()));

        return new ConfirmedState();
    }

    public function cancel(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderCancelled($order->id(), 'Cancelled by customer'));

        return new CancelledState();
    }

    public function allowedTransitions(): array
    {
        return ['confirmed', 'cancelled'];
    }
}
```

**File:** `src/{architecture-path}/State/ConfirmedState.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;

final readonly class ConfirmedState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'confirmed';
    }

    public function pay(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderPaid($order->id()));

        return new PaidState();
    }

    public function cancel(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderCancelled($order->id(), 'Cancelled before payment'));

        return new CancelledState();
    }

    public function allowedTransitions(): array
    {
        return ['paid', 'cancelled'];
    }
}
```

**File:** `src/{architecture-path}/State/PaidState.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;

final readonly class PaidState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'paid';
    }

    public function ship(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderShipped($order->id()));

        return new ShippedState();
    }

    public function refund(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderRefunded($order->id()));

        return new RefundedState();
    }

    public function allowedTransitions(): array
    {
        return ['shipped', 'refunded'];
    }
}
```

**File:** `src/{architecture-path}/State/ShippedState.php`

```php
<?php

declare(strict_types=1);

namespace State;

use Entity\Order;

final readonly class ShippedState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'shipped';
    }

    public function deliver(Order $order): OrderStateInterface
    {
        $order->recordEvent(new OrderDelivered($order->id()));

        return new DeliveredState();
    }

    public function allowedTransitions(): array
    {
        return ['delivered'];
    }
}
```

**File:** `src/{architecture-path}/State/DeliveredState.php`

```php
<?php

declare(strict_types=1);

namespace State;

final readonly class DeliveredState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'delivered';
    }

    public function allowedTransitions(): array
    {
        return [];
    }
}
```

**File:** `src/{architecture-path}/State/CancelledState.php`

```php
<?php

declare(strict_types=1);

namespace State;

final readonly class CancelledState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'cancelled';
    }

    public function allowedTransitions(): array
    {
        return [];
    }
}
```

**File:** `src/{architecture-path}/State/RefundedState.php`

```php
<?php

declare(strict_types=1);

namespace State;

final readonly class RefundedState extends AbstractOrderState
{
    public function getName(): string
    {
        return 'refunded';
    }

    public function allowedTransitions(): array
    {
        return [];
    }
}
```

---

## Order Entity with State

**File:** `src/{architecture-path}/Entity/Order.php`

```php
<?php

declare(strict_types=1);

namespace Entity;

use State\OrderStateInterface;
use State\PendingState;
use ValueObject\OrderId;
use Event\DomainEventInterface;

final class Order
{
    private OrderStateInterface $state;

    /** @var array<DomainEventInterface> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private readonly array $items,
        ?OrderStateInterface $state = null
    ) {
        $this->state = $state ?? new PendingState();
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function confirm(): void
    {
        $this->state = $this->state->confirm($this);
    }

    public function pay(): void
    {
        $this->state = $this->state->pay($this);
    }

    public function ship(): void
    {
        $this->state = $this->state->ship($this);
    }

    public function deliver(): void
    {
        $this->state = $this->state->deliver($this);
    }

    public function cancel(): void
    {
        $this->state = $this->state->cancel($this);
    }

    public function refund(): void
    {
        $this->state = $this->state->refund($this);
    }

    public function getState(): OrderStateInterface
    {
        return $this->state;
    }

    public function getStateName(): string
    {
        return $this->state->getName();
    }

    public function isInState(string $stateName): bool
    {
        return $this->state->getName() === $stateName;
    }

    public function isPending(): bool
    {
        return $this->isInState('pending');
    }

    public function isCompleted(): bool
    {
        return $this->isInState('delivered');
    }

    public function isCancelled(): bool
    {
        return $this->isInState('cancelled');
    }

    public function recordEvent(DomainEventInterface $event): void
    {
        $this->events[] = $event;
    }

    /** @return array<DomainEventInterface> */
    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

---

## State Factory

**File:** `src/{architecture-path}/State/OrderStateFactory.php`

```php
<?php

declare(strict_types=1);

namespace State;

final class OrderStateFactory
{
    public static function fromName(string $name): OrderStateInterface
    {
        return match ($name) {
            'pending' => new PendingState(),
            'confirmed' => new ConfirmedState(),
            'paid' => new PaidState(),
            'shipped' => new ShippedState(),
            'delivered' => new DeliveredState(),
            'cancelled' => new CancelledState(),
            'refunded' => new RefundedState(),
            default => throw new \InvalidArgumentException(
                sprintf('Unknown order state: %s', $name)
            ),
        };
    }
}
```

---

## Unit Tests

### PendingStateTest

**File:** `tests/Unit/State/PendingStateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\State;

use Entity\Order;
use State\CancelledState;
use State\ConfirmedState;
use State\PendingState;
use Exception\InvalidStateTransitionException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(PendingState::class)]
final class PendingStateTest extends TestCase
{
    private PendingState $state;
    private Order $order;

    protected function setUp(): void
    {
        $this->state = new PendingState();
        $this->order = $this->createOrder();
    }

    public function testNameIsPending(): void
    {
        self::assertSame('pending', $this->state->getName());
    }

    public function testCanConfirm(): void
    {
        $newState = $this->state->confirm($this->order);

        self::assertInstanceOf(ConfirmedState::class, $newState);
    }

    public function testCanCancel(): void
    {
        $newState = $this->state->cancel($this->order);

        self::assertInstanceOf(CancelledState::class, $newState);
    }

    public function testCannotPay(): void
    {
        $this->expectException(InvalidStateTransitionException::class);

        $this->state->pay($this->order);
    }

    public function testCannotShip(): void
    {
        $this->expectException(InvalidStateTransitionException::class);

        $this->state->ship($this->order);
    }

    public function testAllowedTransitions(): void
    {
        self::assertSame(['confirmed', 'cancelled'], $this->state->allowedTransitions());
    }

    public function testCanTransitionToConfirmed(): void
    {
        self::assertTrue($this->state->canTransitionTo(new ConfirmedState()));
    }

    public function testCannotTransitionToDelivered(): void
    {
        self::assertFalse($this->state->canTransitionTo(new DeliveredState()));
    }

    private function createOrder(): Order
    {
        return new Order(
            id: OrderId::generate(),
            customerId: CustomerId::generate(),
            items: []
        );
    }
}
```

### OrderStateTransitionTest

**File:** `tests/Unit/Entity/OrderStateTransitionTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Entity;

use Entity\Order;
use Exception\InvalidStateTransitionException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderStateTransitionTest extends TestCase
{
    public function testFullOrderLifecycle(): void
    {
        $order = $this->createOrder();

        self::assertTrue($order->isPending());

        $order->confirm();
        self::assertSame('confirmed', $order->getStateName());

        $order->pay();
        self::assertSame('paid', $order->getStateName());

        $order->ship();
        self::assertSame('shipped', $order->getStateName());

        $order->deliver();
        self::assertSame('delivered', $order->getStateName());
        self::assertTrue($order->isCompleted());
    }

    public function testCancelFromPending(): void
    {
        $order = $this->createOrder();

        $order->cancel();

        self::assertTrue($order->isCancelled());
    }

    public function testCannotShipPendingOrder(): void
    {
        $order = $this->createOrder();

        $this->expectException(InvalidStateTransitionException::class);

        $order->ship();
    }

    public function testRefundPaidOrder(): void
    {
        $order = $this->createOrder();
        $order->confirm();
        $order->pay();

        $order->refund();

        self::assertSame('refunded', $order->getStateName());
    }

    public function testRecordsEvents(): void
    {
        $order = $this->createOrder();

        $order->confirm();

        $events = $order->releaseEvents();

        self::assertCount(1, $events);
        self::assertInstanceOf(OrderConfirmed::class, $events[0]);
    }

    private function createOrder(): Order
    {
        return new Order(
            id: OrderId::generate(),
            customerId: CustomerId::generate(),
            items: []
        );
    }
}
```

---

## State Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     ORDER STATE MACHINE                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌──────────┐  confirm   ┌───────────┐  pay   ┌──────────┐ │
│   │ Pending  │───────────▶│ Confirmed │───────▶│   Paid   │ │
│   └────┬─────┘            └─────┬─────┘        └────┬─────┘ │
│        │                        │                   │        │
│        │ cancel                 │ cancel            │ refund │
│        │                        │                   │        │
│        ▼                        ▼                   ▼        │
│   ┌──────────┐            ┌───────────┐       ┌──────────┐  │
│   │Cancelled │            │ Cancelled │       │ Refunded │  │
│   └──────────┘            └───────────┘       └──────────┘  │
│                                                              │
│                 ┌──────────┐                                 │
│                 │   Paid   │                                 │
│                 └────┬─────┘                                 │
│                      │ ship                                  │
│                      ▼                                       │
│                 ┌──────────┐  deliver  ┌───────────┐        │
│                 │ Shipped  │──────────▶│ Delivered │        │
│                 └──────────┘           └───────────┘        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```
