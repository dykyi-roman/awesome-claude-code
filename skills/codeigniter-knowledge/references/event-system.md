# Event System in CodeIgniter 4

CI4 Events (publish/subscribe), domain event dispatching, framework lifecycle events, and priority management.

## CI4 Events Overview

CodeIgniter 4 provides a lightweight publish/subscribe Events system via `CodeIgniter\Events\Events`. Events are configured in `app/Config/Events.php` and are always globally enabled.

### Core Methods

| Method | Purpose |
|--------|---------|
| `Events::on($event, $callable, $priority)` | Subscribe listener to event |
| `Events::trigger($event, ...$args)` | Fire event, execute all listeners |
| `Events::simulate(bool)` | Skip event execution (testing) |
| `Events::removeListener($event, $callable)` | Unsubscribe specific listener |
| `Events::removeAllListeners($event)` | Remove all listeners for event |

### Subscribing to Events

```php
<?php

declare(strict_types=1);

use CodeIgniter\Events\Events;

// Closure
Events::on('order.confirmed', static function (object $event): void {
    service('logger')->info('Order confirmed', ['id' => $event->orderId]);
});

// Static method
Events::on('order.confirmed', [OrderNotifier::class, 'onConfirmed']);

// Instance method
$handler = new OrderNotificationHandler();
Events::on('order.confirmed', [$handler, 'handle']);
```

### Triggering Events

```php
<?php

declare(strict_types=1);

use CodeIgniter\Events\Events;

// Simple trigger
Events::trigger('order.confirmed', $orderConfirmedEvent);

// With multiple arguments
Events::trigger('payment.processed', $orderId, $amount, $method);
```

### Priority System

Lower values execute first. Predefined constants:

| Constant | Value | Use Case |
|----------|-------|----------|
| `Events::PRIORITY_HIGH` | 10 | Critical listeners (logging, audit) |
| `Events::PRIORITY_NORMAL` | 100 | Standard listeners (notifications) |
| `Events::PRIORITY_LOW` | 200 | Non-critical (analytics, cleanup) |

```php
<?php

declare(strict_types=1);

use CodeIgniter\Events\Events;

Events::on('order.confirmed', [AuditLogger::class, 'log'], Events::PRIORITY_HIGH);
Events::on('order.confirmed', [EmailNotifier::class, 'notify'], Events::PRIORITY_NORMAL);
Events::on('order.confirmed', [AnalyticsTracker::class, 'track'], Events::PRIORITY_LOW);
```

### Stopping Propagation

If any subscriber returns `false`, execution of remaining listeners stops:

```php
<?php

declare(strict_types=1);

Events::on('order.cancellation_requested', static function (object $event): bool {
    if ($event->order->isShipped()) {
        // Stop propagation — shipped orders cannot be cancelled
        return false;
    }

    return true; // Continue to next listener
});
```

## Framework Lifecycle Events

### Web Application Events

| Event | When | Use Case |
|-------|------|----------|
| `pre_system` | Before routing/filters | Request logging, early CORS |
| `post_controller_constructor` | After controller instantiation | Dependency setup |
| `post_system` | Before final output | Response modification |

### CLI Events

| Event | When | Use Case |
|-------|------|----------|
| `pre_command` | Before command execution | CLI logging |
| `post_command` | After command execution | Cleanup |

### Library Events

| Event | When | Use Case |
|-------|------|----------|
| `email` | After email sent | Email audit log |
| `DBQuery` | After database query | Query logging, slow query detection |
| `migrate` | After migration | Schema change notification |

## Domain Event Dispatching

### Domain EventDispatcherInterface (Pure PHP)

```php
<?php

declare(strict_types=1);

namespace App\Domain\Shared;

interface EventDispatcherInterface
{
    public function dispatch(object ...$events): void;
}
```

### Domain Event Definition

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Event;

use App\Domain\Order\ValueObject\OrderId;

final readonly class OrderConfirmed
{
    public function __construct(
        public OrderId $orderId,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}
}
```

### CI4 Events Adapter (Infrastructure)

**Bad: CI4 Events::trigger() in Domain**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

use CodeIgniter\Events\Events; // VIOLATION: CI4 in Domain

final class Order
{
    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        Events::trigger('order.confirmed', $this); // VIOLATION
    }
}
```

**Good: Domain event collection + Infrastructure dispatcher**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

final class Order
{
    /** @var array<object> */
    private array $events = [];

    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmed($this->id);
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

namespace App\Infrastructure\Event;

use App\Domain\Shared\EventDispatcherInterface;
use CodeIgniter\Events\Events;

final readonly class CIEventDispatcher implements EventDispatcherInterface
{
    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            $eventName = $this->resolveEventName($event);
            Events::trigger($eventName, $event);
        }
    }

    private function resolveEventName(object $event): string
    {
        $class = (new \ReflectionClass($event))->getShortName();
        // OrderConfirmed → order.confirmed
        return strtolower((string) preg_replace('/(?<!^)[A-Z]/', '.$0', $class));
    }
}
```

### Application Layer Event Dispatching

```php
<?php

declare(strict_types=1);

namespace App\Application\Order;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Shared\EventDispatcherInterface;

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

### Listener Registration

```php
<?php

declare(strict_types=1);

// app/Config/Events.php
namespace Config;

use CodeIgniter\Events\Events;

// Domain event listeners (Infrastructure layer handles side effects)
Events::on('order.confirmed', static function (object $event): void {
    service('orderNotificationService')->sendConfirmation($event->orderId);
});

Events::on('order.confirmed', static function (object $event): void {
    service('orderProjectionService')->updateReadModel($event->orderId);
});

Events::on('order.confirmed', static function (object $event): void {
    service('logger')->info('Order confirmed', [
        'orderId' => $event->orderId->value(),
        'at' => $event->occurredAt->format('c'),
    ]);
}, Events::PRIORITY_HIGH);
```

## Testing Events

### Simulating Events

```php
<?php

declare(strict_types=1);

use CodeIgniter\Events\Events;
use PHPUnit\Framework\TestCase;

final class OrderConfirmationTest extends TestCase
{
    protected function setUp(): void
    {
        Events::simulate(true); // Disable real event handlers
    }

    protected function tearDown(): void
    {
        Events::simulate(false);
    }

    public function testConfirmOrderDispatchesEvent(): void
    {
        // Test domain event collection without CI4 Events
        $order = Order::create(OrderId::generate(), $customerId, $total);
        $order->confirm();

        $events = $order->releaseEvents();
        $this->assertCount(2, $events); // OrderCreated + OrderConfirmed
        $this->assertInstanceOf(OrderConfirmed::class, $events[1]);
    }
}
```

### Testing with Mock Dispatcher

```php
<?php

declare(strict_types=1);

use App\Domain\Shared\EventDispatcherInterface;

final class InMemoryEventDispatcher implements EventDispatcherInterface
{
    /** @var array<object> */
    public array $dispatched = [];

    public function dispatch(object ...$events): void
    {
        foreach ($events as $event) {
            $this->dispatched[] = $event;
        }
    }
}
```

## Detection Patterns

```bash
# CI4 Events in Domain layer (VIOLATION)
Grep: "use CodeIgniter\\Events\\Events" --glob "**/Domain/**/*.php"
Grep: "Events::trigger\(" --glob "**/Domain/**/*.php"

# CI4 Events in Application layer (VIOLATION)
Grep: "use CodeIgniter\\Events\\Events" --glob "**/Application/**/*.php"

# Good: Domain EventDispatcherInterface exists
Grep: "EventDispatcherInterface" --glob "**/Domain/**/*.php" --output_mode count

# Good: Infrastructure adapter exists
Grep: "CIEventDispatcher|implements EventDispatcherInterface" --glob "**/Infrastructure/**/*.php"

# Event listeners registered
Grep: "Events::on\(" --glob "app/Config/Events.php" --output_mode count
```

## CI4 Events vs Domain Events

| Aspect | CI4 Events | Domain Events |
|--------|-----------|---------------|
| Location | `app/Config/Events.php` | Domain entity `releaseEvents()` |
| Trigger | `Events::trigger()` | Application layer via dispatcher port |
| Scope | Framework-wide, global | Bounded context |
| Priority | `PRIORITY_HIGH/NORMAL/LOW` | N/A (all dispatched) |
| Propagation | Can stop with `return false` | Always dispatched |
| Testing | `Events::simulate()` | Pure PHP assertions |
| Async | No (synchronous only) | Via Queue adapter |

## Summary Table

| Aspect | DDD Layer | CI4 Component | Integration Pattern |
|--------|-----------|--------------|---------------------|
| Domain Events | Domain: event classes | N/A (pure PHP) | Entity collects, UseCase dispatches |
| Event Dispatching | Domain: EventDispatcherInterface | CI4: Events class | Infrastructure CIEventDispatcher adapter |
| Event Listeners | Infrastructure: side-effect handlers | CI4: Events::on() | Registered in Config/Events.php |
| Framework Events | N/A (Infrastructure) | CI4: pre_system, post_system | Only in Infrastructure/Presentation |
| Event Testing | Domain: pure assertions | CI4: Events::simulate() | Mock dispatcher in unit tests |
