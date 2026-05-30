# Event System in Yii3

PSR-14 Event Dispatcher (`yiisoft/event-dispatcher`), listener registration, stoppable events, composite providers, domain event patterns, and authentication events.

## PSR-14 Event Dispatcher (yiisoft/event-dispatcher)

### Core Components

| Component | Description |
|-----------|-------------|
| Events | Plain PHP objects — no base class required |
| `ListenerCollection` | Registers callable listeners matched by type hint |
| `Provider` | Implements `ListenerProviderInterface`, resolves listeners for event |
| `Dispatcher` | Implements `EventDispatcherInterface`, dispatches events to listeners |
| `CompositeProvider` | Combines multiple providers into one |

### Event Definition (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace Event;

// Pure domain event — no Yii dependency
final readonly class OrderConfirmed
{
    public function __construct(
        public string $orderId,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}
}
```

### Listener Registration via Config

```php
<?php

declare(strict_types=1);

// config/common/di/events.php

use Event\OrderConfirmed;
use Event\OrderCreated;
use Yiisoft\EventDispatcher\Provider\ListenerCollection;

return [
    ListenerCollection::class => static function () {
        return (new ListenerCollection())
            ->add(static fn (OrderConfirmed $event) => /* inline handler */)
            ->add(static fn (OrderCreated $event) => /* inline handler */);
    },
];
```

### Class-Based Listeners

```php
<?php

declare(strict_types=1);

namespace Listener;

use Event\OrderConfirmed;
use Domain\Shared\Mail\MailerInterface;

final readonly class SendOrderConfirmationEmail
{
    public function __construct(
        private MailerInterface $mailer,
    ) {}

    public function __invoke(OrderConfirmed $event): void
    {
        $this->mailer->send(
            to: $event->orderId,
            template: 'order-confirmed',
            context: ['orderId' => $event->orderId, 'occurredAt' => $event->occurredAt],
        );
    }
}
```

### Registering Class-Based Listeners in Config

```php
<?php

declare(strict_types=1);

// config/common/di/events.php

use Event\OrderConfirmed;
use Event\OrderCreated;
use Listener\SendOrderConfirmationEmail;
use Listener\UpdateInventoryOnOrderCreated;
use Yiisoft\EventDispatcher\Provider\ListenerCollection;

return [
    ListenerCollection::class => static function (
        SendOrderConfirmationEmail $confirmationListener,
        UpdateInventoryOnOrderCreated $inventoryListener,
    ) {
        return (new ListenerCollection())
            ->add($confirmationListener, OrderConfirmed::class)
            ->add($inventoryListener, OrderCreated::class);
    },
];
```

## Event Hierarchy with Interfaces

### Interface-Based Grouping

```php
<?php

declare(strict_types=1);

namespace Event;

// Marker interface — group related events by bounded context
interface OrderEvent {}

final readonly class OrderCreated implements OrderEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}
}

final readonly class OrderConfirmed implements OrderEvent
{
    public function __construct(
        public string $orderId,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}
}
```

```php
<?php

declare(strict_types=1);

// Listen to ALL order events via interface type hint
$listeners->add(static fn (OrderEvent $event) => /* log all order events */);
```

## Stoppable Events (PSR-14)

### StoppableEventInterface

```php
<?php

declare(strict_types=1);

namespace Event;

use Psr\EventDispatcher\StoppableEventInterface;

final class BeforeOrderConfirmed implements StoppableEventInterface
{
    private bool $stopped = false;

    public function __construct(
        public readonly string $orderId,
    ) {}

    public function veto(): void
    {
        $this->stopped = true;
    }

    public function isPropagationStopped(): bool
    {
        return $this->stopped;
    }
}
```

Use case: validation events where a listener can veto the action by calling `$event->veto()`. Subsequent listeners are skipped once `isPropagationStopped()` returns `true`.

## CompositeProvider

### One Provider per Bounded Context

```php
<?php

declare(strict_types=1);

// config/common/di/event-providers.php

use Yiisoft\EventDispatcher\Provider\CompositeProvider;
use Yiisoft\EventDispatcher\Provider\Provider;

return [
    CompositeProvider::class => static function (
        Provider $orderProvider,
        Provider $paymentProvider,
        Provider $notificationProvider,
    ) {
        $composite = new CompositeProvider();
        $composite->attach($orderProvider);
        $composite->attach($paymentProvider);
        $composite->attach($notificationProvider);

        return $composite;
    },
];
```

## Domain Event Dispatching Pattern

### Bad: PSR-14 in Domain

```php
<?php

declare(strict_types=1);

namespace Entity;

use Psr\EventDispatcher\EventDispatcherInterface; // VIOLATION: PSR package in Domain

final class Order
{
    public function __construct(
        private EventDispatcherInterface $dispatcher, // Domain depends on external package
    ) {}
}
```

### Good: Domain Defines Own Port

```php
<?php

declare(strict_types=1);

namespace Shared;

interface EventDispatcherInterface
{
    /** @param array<object> $events */
    public function dispatch(array $events): void;
}
```

### Infrastructure Adapter: Bridge to PSR-14

```php
<?php

declare(strict_types=1);

namespace Event;

use Domain\Shared\EventDispatcherInterface as DomainDispatcher;
use Psr\EventDispatcher\EventDispatcherInterface;

final readonly class YiiEventDispatcherAdapter implements DomainDispatcher
{
    public function __construct(
        private EventDispatcherInterface $dispatcher,
    ) {}

    public function dispatch(array $events): void
    {
        foreach ($events as $event) {
            $this->dispatcher->dispatch($event);
        }
    }
}
```

### Aggregate Event Collection + UseCase Dispatching

Entity collects events internally; UseCase calls `releaseEvents()` and dispatches via domain port.

```php
<?php

declare(strict_types=1);

namespace Entity;

use Event\OrderConfirmed;
use ValueObject\OrderId;
use ValueObject\OrderStatus;

final class Order
{
    /** @var array<object> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private OrderStatus $status,
    ) {}

    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmed($this->id->value);
    }

    /** @return array<object> */
    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];

        return $events;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;
use Shared\EventDispatcherInterface;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(string $orderId): void
    {
        $order = $this->orders->findById(new OrderId($orderId));
        $order->confirm();
        $this->orders->save($order);
        $this->events->dispatch($order->releaseEvents());
    }
}
```

## Authentication Events (yiisoft/user)

### Available Events

| Event | Trigger | Cancellable |
|-------|---------|-------------|
| `BeforeLogin` | Before user login | Yes (`invalidate()`) |
| `AfterLogin` | After successful login | No |
| `BeforeLogout` | Before user logout | Yes (`invalidate()`) |
| `AfterLogout` | After successful logout | No |

### Audit Logging Listener

```php
<?php

declare(strict_types=1);

namespace Listener;

use Psr\Log\LoggerInterface;
use Yiisoft\User\Event\AfterLogin;

final readonly class AuthAuditListener
{
    public function __construct(private LoggerInterface $logger) {}

    public function __invoke(AfterLogin $event): void
    {
        $this->logger->info('User logged in', [
            'identity' => $event->getIdentity()->getId(),
        ]);
    }
}
```

## Detection Patterns

```bash
# PSR-14 in Domain (should use domain port instead)
Grep: "use Psr\\EventDispatcher\\" --glob "**/Domain/**/*.php"

# Yii event dispatcher in Domain (MUST be zero)
Grep: "use Yiisoft\\EventDispatcher\\" --glob "**/Domain/**/*.php"

# Event listeners configuration
Grep: "ListenerCollection" --glob "config/**/*.php"

# Domain events defined
Grep: "readonly class.*Event" --glob "**/Domain/**/Event/*.php"

# Events dispatched in Application layer
Grep: "dispatch\(|releaseEvents\(\)" --glob "**/Application/**/*.php"

# Stoppable events
Grep: "StoppableEventInterface" --glob "**/*.php"

# CompositeProvider usage
Grep: "CompositeProvider" --glob "config/**/*.php"

# Auth event listeners
Grep: "AfterLogin\|BeforeLogin\|AfterLogout\|BeforeLogout" --glob "**/*.php"

# Missing domain event port (adapter pattern)
Grep: "YiiEventDispatcherAdapter\|DomainDispatcher" --glob "**/Infrastructure/**/*.php"
```

## EventDispatcher vs Queue Comparison

| Aspect | EventDispatcher | Queue (yii-queue) |
|--------|----------------|-------------------|
| Execution | Synchronous | Asynchronous |
| Retry | No | Yes (failure middleware) |
| Return value | Event object | None |
| Ordering | Guaranteed (listener order) | Not guaranteed |
| Use case | Domain events, hooks | Background jobs, notifications |
| PSR | PSR-14 | None |
| Best for | In-process side effects | Heavy/slow operations |

## Summary Table

| Aspect | DDD Layer | Component | Pattern |
|--------|-----------|-----------|---------|
| Domain Events | Domain | Plain PHP classes (`final readonly`) | No framework dependency |
| Event Dispatching | Application | Domain port `EventDispatcherInterface` | UseCase dispatches after save |
| Listener Registration | Infrastructure | `ListenerCollection` + config | One provider per bounded context |
| Event Bridge | Infrastructure | `YiiEventDispatcherAdapter` | Domain port to PSR-14 adapter |
| Stoppable Events | Domain | `StoppableEventInterface` | Vetoable actions |
| Event Hierarchy | Domain | PHP interfaces | Group related events |
| Auth Events | Infrastructure | `yiisoft/user` events | Audit logging |
