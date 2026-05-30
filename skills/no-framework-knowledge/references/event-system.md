# Event System in No-Framework PHP

PSR-14 event dispatching, custom dispatchers, domain event patterns, listener management, and async event processing using standalone packages.

## PSR-14 Overview

PSR-14 defines three interfaces for event dispatching:

| Interface | Purpose | Package |
|-----------|---------|---------|
| `EventDispatcherInterface` | Dispatches events | `psr/event-dispatcher` |
| `ListenerProviderInterface` | Provides listeners for events | `psr/event-dispatcher` |
| `StoppableEventInterface` | Events that can halt propagation | `psr/event-dispatcher` |

### Recommended Packages

| Package | Description |
|---------|-------------|
| `league/event` | Full-featured PSR-14 implementation |
| `symfony/event-dispatcher` | Standalone (no framework needed) |
| Custom | InMemory dispatcher (minimal projects) |

```bash
composer require psr/event-dispatcher league/event
```

## Detection Patterns

```bash
# PSR-14 or event library in Domain (VIOLATION)
Grep: "use League\\Event|use Symfony\\.*EventDispatcher" --glob "**/Domain/**/*.php"

# Dispatcher in Domain entity (VIOLATION)
Grep: "EventDispatcher|dispatch\(" --glob "**/Domain/**/Entity/**/*.php"

# Good: Domain EventDispatcherInterface exists
Grep: "interface EventDispatcherInterface" --glob "**/Domain/**/*.php"

# Good: Domain events exist
Grep: "class.*Event implements|class.*Event$" --glob "**/Domain/**/Event/**/*.php"

# Good: Infrastructure adapter exists
Grep: "implements EventDispatcherInterface" --glob "**/Infrastructure/**/*.php"

# Listeners registered
Grep: "subscribeTo\|subscribe\(" --glob "**/config/events*.php"
```

## Custom Event Dispatcher (Pure PHP)

### EventDispatcherInterface (Domain Port)

```php
<?php

declare(strict_types=1);

namespace Event;

interface EventDispatcherInterface
{
    public function dispatch(object ...$events): void;
}
```

### InMemory Implementation (Infrastructure)

```php
<?php

declare(strict_types=1);

namespace EventDispatcher;

use Event\EventDispatcherInterface;

final class InMemoryEventDispatcher implements EventDispatcherInterface
{
    /** @var array<class-string, array<callable>> */
    private array $listeners = [];

    public function subscribe(string $eventClass, callable $listener): void
    {
        $this->listeners[$eventClass][] = $listener;
    }

    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            $eventClass = $event::class;

            foreach ($this->listeners[$eventClass] ?? [] as $listener) {
                $listener($event);
            }
        }
    }
}
```

## PSR-14 with league/event

### Dispatcher Setup

```php
<?php

declare(strict_types=1);

// config/events.php
use League\Event\EventDispatcher;
use League\Event\PrioritizedListenerRegistry;

$listenerProvider = new PrioritizedListenerRegistry();

// Register listeners with priority (lower = earlier)
$listenerProvider->subscribeTo(
    Domain\Order\Event\OrderConfirmed::class,
    new Infrastructure\Listener\SendOrderConfirmationEmail(),
    10,
);

$listenerProvider->subscribeTo(
    Domain\Order\Event\OrderConfirmed::class,
    new Infrastructure\Listener\UpdateOrderReadModel(),
    20,
);

$listenerProvider->subscribeTo(
    Domain\Order\Event\OrderConfirmed::class,
    new Infrastructure\Listener\NotifyAnalytics(),
    100, // Low priority
);

return new EventDispatcher($listenerProvider);
```

### PSR-14 Adapter (bridges league/event to domain port)

```php
<?php

declare(strict_types=1);

namespace EventDispatcher;

use Event\EventDispatcherInterface;
use Psr\EventDispatcher\EventDispatcherInterface as PsrEventDispatcher;

final readonly class PsrEventDispatcherAdapter implements EventDispatcherInterface
{
    public function __construct(
        private PsrEventDispatcher $dispatcher,
    ) {}

    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            $this->dispatcher->dispatch($event);
        }
    }
}
```

## Domain Events

### Domain Event Definition

```php
<?php

declare(strict_types=1);

namespace Event;

use ValueObject\OrderId;
use ValueObject\Money;
use Event\DomainEventInterface;

final readonly class OrderConfirmed implements DomainEventInterface
{
    public function __construct(
        public OrderId $orderId,
        public Money $total,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}

    public function occurredAt(): \DateTimeImmutable
    {
        return $this->occurredAt;
    }
}
```

### Entity Event Collection

**Bad -- Dispatching in Domain:**

```php
<?php

declare(strict_types=1);

namespace Entity;

use Infrastructure\EventDispatcher\InMemoryEventDispatcher; // VIOLATION

final class Order
{
    public function confirm(InMemoryEventDispatcher $dispatcher): void // VIOLATION
    {
        $this->status = OrderStatus::Confirmed;
        $dispatcher->dispatch(new OrderConfirmed($this->id, $this->total())); // VIOLATION
    }
}
```

**Good -- Collect events, dispatch in Application:**

```php
<?php

declare(strict_types=1);

namespace Entity;

use Event\OrderConfirmed;
use Entity\AggregateRoot;

final class Order extends AggregateRoot
{
    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException('Only draft orders can be confirmed');
        }

        $this->status = OrderStatus::Confirmed;
        $this->recordEvent(new OrderConfirmed($this->id, $this->total()));
    }
}
```

### AggregateRoot Base Class

```php
<?php

declare(strict_types=1);

namespace Entity;

abstract class AggregateRoot
{
    /** @var array<object> */
    private array $domainEvents = [];

    protected function recordEvent(object $event): void
    {
        $this->domainEvents[] = $event;
    }

    /** @return array<object> */
    public function releaseEvents(): array
    {
        $events = $this->domainEvents;
        $this->domainEvents = [];

        return $events;
    }
}
```

### Application Layer Dispatching

```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;
use Event\EventDispatcherInterface;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(string $orderId): void
    {
        $order = $this->orders->findById(new OrderId($orderId))
            ?? throw new OrderNotFoundException($orderId);

        $order->confirm();
        $this->orders->save($order);
        $this->events->dispatch(...$order->releaseEvents());
    }
}
```

## Event Listeners (Infrastructure)

```php
<?php

declare(strict_types=1);

namespace Listener;

use Event\OrderConfirmed;
use Psr\Log\LoggerInterface;

final readonly class SendOrderConfirmationEmail
{
    public function __construct(
        private MailerInterface $mailer,
        private LoggerInterface $logger,
    ) {}

    public function __invoke(OrderConfirmed $event): void
    {
        $this->mailer->sendOrderConfirmation($event->orderId);
        $this->logger->info('Order confirmation email sent', [
            'orderId' => $event->orderId->value,
        ]);
    }
}
```

## Stoppable Events (PSR-14)

```php
<?php

declare(strict_types=1);

namespace Event;

use ValueObject\OrderId;
use Psr\EventDispatcher\StoppableEventInterface;

final class OrderCancellationRequested implements StoppableEventInterface
{
    private bool $stopped = false;

    public function __construct(
        public readonly OrderId $orderId,
    ) {}

    public function stop(): void
    {
        $this->stopped = true;
    }

    public function isPropagationStopped(): bool
    {
        return $this->stopped;
    }
}
```

## Async Event Processing

### Dispatching to Queue

```php
<?php

declare(strict_types=1);

namespace EventDispatcher;

use Event\EventDispatcherInterface;

final readonly class AsyncEventDispatcher implements EventDispatcherInterface
{
    public function __construct(
        private EventDispatcherInterface $syncDispatcher,
        private QueueInterface $queue,
        /** @var array<class-string> */
        private array $asyncEvents = [],
    ) {}

    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            if (in_array($event::class, $this->asyncEvents, true)) {
                $this->queue->push('events', $event);
            } else {
                $this->syncDispatcher->dispatch($event);
            }
        }
    }
}
```

### Queue Worker for Events

```php
<?php

declare(strict_types=1);

namespace EventDispatcher;

use Event\EventDispatcherInterface;

final readonly class EventQueueWorker
{
    public function __construct(
        private QueueInterface $queue,
        private EventDispatcherInterface $syncDispatcher,
    ) {}

    public function processNext(): void
    {
        $event = $this->queue->pop('events');

        if ($event === null) {
            return;
        }

        $this->syncDispatcher->dispatch($event);
    }
}
```

## Testing

### InMemory Dispatcher for Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Shared;

use Event\EventDispatcherInterface;

final class InMemoryTestEventDispatcher implements EventDispatcherInterface
{
    /** @var array<object> */
    public array $dispatched = [];

    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            $this->dispatched[] = $event;
        }
    }

    public function assertDispatched(string $eventClass): void
    {
        foreach ($this->dispatched as $event) {
            if ($event instanceof $eventClass) {
                return;
            }
        }

        throw new \RuntimeException("Event {$eventClass} was not dispatched");
    }

    public function assertNotDispatched(string $eventClass): void
    {
        foreach ($this->dispatched as $event) {
            if ($event instanceof $eventClass) {
                throw new \RuntimeException("Event {$eventClass} was unexpectedly dispatched");
            }
        }
    }

    public function reset(): void
    {
        $this->dispatched = [];
    }
}
```

### UseCase Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Application\Order;

use UseCase\ConfirmOrderUseCase;
use Event\OrderConfirmed;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Tests\Shared\InMemoryTestEventDispatcher;

#[Group('unit')]
#[CoversClass(ConfirmOrderUseCase::class)]
final class ConfirmOrderUseCaseTest extends TestCase
{
    public function testDispatchesOrderConfirmedEvent(): void
    {
        $events = new InMemoryTestEventDispatcher();
        $orders = new InMemoryOrderRepository();
        $orders->save(OrderMother::draft('order-1'));

        $useCase = new ConfirmOrderUseCase($orders, $events);
        $useCase->execute('order-1');

        $events->assertDispatched(OrderConfirmed::class);
    }
}
```

## Custom vs PSR-14 Comparison

| Aspect | Custom InMemory | PSR-14 (league/event) |
|--------|----------------|----------------------|
| Dependencies | None | `league/event` |
| Priority | Manual ordering | Built-in priority |
| Stoppable | Must implement | `StoppableEventInterface` |
| Interoperability | Low | High (PSR standard) |
| Testing | Simple | Simple |
| Async | Custom bridge | Custom bridge |
| Best For | Small projects | Medium/Large projects |

## DDD Integration Notes

- Domain events are plain PHP objects defined in `Domain/{Context}/Event/`
- `EventDispatcherInterface` is a **domain port** (interface in Domain layer)
- Infrastructure provides adapters: `InMemoryEventDispatcher`, `PsrEventDispatcherAdapter`, `AsyncEventDispatcher`
- Entities **never dispatch** events directly; they **record** them via `AggregateRoot::recordEvent()`
- Application layer (UseCase) calls `releaseEvents()` after persistence and dispatches them
- Listeners live in Infrastructure and perform side effects (email, logging, read-model updates)
- For testing, use `InMemoryTestEventDispatcher` to assert dispatched events without infrastructure

## Summary Table

| Aspect | DDD Layer | Package | Integration Pattern |
|--------|-----------|---------|---------------------|
| Domain Events | Domain: event classes | Pure PHP | AggregateRoot `recordEvent()` |
| Event Dispatcher | Domain: EventDispatcherInterface port | N/A | Infrastructure adapter |
| PSR-14 Dispatcher | Infrastructure | `league/event` | PsrEventDispatcherAdapter |
| Custom Dispatcher | Infrastructure | None | InMemoryEventDispatcher |
| Event Listeners | Infrastructure | Custom callables | Registered in config/events.php |
| Async Events | Infrastructure | Queue bridge | AsyncEventDispatcher decorator |
| Event Testing | Tests | Pure PHP | InMemoryTestEventDispatcher |
