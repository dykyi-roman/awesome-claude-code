# Laravel Event System

Event discovery, queued listeners, subscribers, domain event integration, and testing patterns.

## Event Discovery

Laravel auto-discovers listeners by scanning the `Listeners` directory. Methods named `handle` or `__invoke` with type-hinted event parameter are registered automatically.

**Detection:**
```bash
# Event classes
Grep: "class.*Event" --glob "**/Events/**/*.php"
Grep: "use Dispatchable" --glob "**/Events/**/*.php"

# Listener classes
Grep: "function handle\\(|function __invoke\\(" --glob "**/Listeners/**/*.php"

# Domain events (pure PHP, no Laravel traits)
Grep: "readonly class.*Event" --glob "**/Domain/**/Event/**/*.php"
```

## Event Structure

**Laravel event (Infrastructure/Presentation):**
```php
<?php

declare(strict_types=1);

namespace App\Events;

use Illuminate\Foundation\Events\Dispatchable;
use Illuminate\Queue\SerializesModels;

final class OrderShippedEvent
{
    use Dispatchable, SerializesModels;

    public function __construct(
        public readonly string $orderId,
        public readonly string $trackingNumber,
    ) {}
}
```

**Domain event (pure PHP):**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Event;

// No Laravel dependency — pure domain event
final readonly class OrderConfirmedEvent
{
    public function __construct(
        public string $orderId,
        public \DateTimeImmutable $confirmedAt,
    ) {}
}
```

## Queued Listeners

Implement `ShouldQueue` to process listeners asynchronously.

```php
<?php

declare(strict_types=1);

namespace App\Listeners\Order;

use App\Domain\Order\Event\OrderConfirmedEvent;
use Illuminate\Contracts\Queue\ShouldQueue;

final class SendOrderConfirmationEmail implements ShouldQueue
{
    public string $queue = 'notifications';
    public int $delay = 10;
    public int $tries = 3;

    /** @return array<int> */
    public function backoff(): array
    {
        return [1, 5, 10];
    }

    public function handle(OrderConfirmedEvent $event): void
    {
        // Send email notification
    }

    public function shouldQueue(OrderConfirmedEvent $event): bool
    {
        // Only queue for non-test orders
        return !str_starts_with($event->orderId, 'test-');
    }

    public function failed(OrderConfirmedEvent $event, \Throwable $exception): void
    {
        // Handle permanent failure
    }
}
```

## Event Subscribers

Group related listeners into a subscriber class.

**Bad — unrelated listeners mixed in one subscriber:**
```php
<?php

declare(strict_types=1);

namespace App\Listeners;

// VIOLATION: Mixing unrelated concerns
class EventSubscriber
{
    public function handleLogin($event): void { /* ... */ }
    public function handleOrderCreated($event): void { /* ... */ }
    public function handlePaymentFailed($event): void { /* ... */ }
}
```

**Good — focused subscriber per bounded context:**
```php
<?php

declare(strict_types=1);

namespace App\Listeners\Auth;

use Illuminate\Auth\Events\Login;
use Illuminate\Auth\Events\Logout;
use Illuminate\Events\Dispatcher;

final readonly class AuthEventSubscriber
{
    public function subscribe(Dispatcher $events): array
    {
        return [
            Login::class => 'handleLogin',
            Logout::class => 'handleLogout',
        ];
    }

    public function handleLogin(Login $event): void
    {
        // Log authentication event
    }

    public function handleLogout(Logout $event): void
    {
        // Cleanup session data
    }
}
```

**Register in provider:**
```php
// In AppServiceProvider::boot()
use Illuminate\Support\Facades\Event;

Event::subscribe(AuthEventSubscriber::class);
```

## Domain Event Dispatching

Domain defines its own `EventDispatcherInterface`; Laravel implements it.

**Bad — Laravel Event facade in Domain:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

use Illuminate\Support\Facades\Event;

// VIOLATION: Laravel dependency in Domain
final class Order
{
    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        Event::dispatch(new OrderConfirmedEvent($this->id));
    }
}
```

**Good — Aggregate collects events, Application layer dispatches:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

// Domain entity records events without dispatching
final class Order
{
    /** @var array<object> */
    private array $events = [];

    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent(
            orderId: $this->id->value(),
            confirmedAt: new \DateTimeImmutable(),
        );
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

namespace App\Domain\Shared;

// Domain port
interface EventDispatcherInterface
{
    /** @param array<object> $events */
    public function dispatch(array $events): void;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use App\Domain\Shared\EventDispatcherInterface;
use Illuminate\Contracts\Events\Dispatcher;

// Infrastructure adapter
final readonly class LaravelEventDispatcher implements EventDispatcherInterface
{
    public function __construct(
        private Dispatcher $dispatcher,
    ) {}

    /** @param array<object> $events */
    public function dispatch(array $events): void
    {
        foreach ($events as $event) {
            $this->dispatcher->dispatch($event);
        }
    }
}
```

## Events After Database Transactions

Ensure events dispatch only after the transaction commits.

```php
<?php

declare(strict_types=1);

namespace App\Events;

use Illuminate\Contracts\Events\ShouldDispatchAfterCommit;
use Illuminate\Foundation\Events\Dispatchable;

// Only dispatched after DB transaction commits
final class OrderCreatedEvent implements ShouldDispatchAfterCommit
{
    use Dispatchable;

    public function __construct(
        public readonly string $orderId,
    ) {}
}
```

## Unique Listeners

Prevent duplicate listener execution.

```php
<?php

declare(strict_types=1);

namespace App\Listeners;

use Illuminate\Contracts\Queue\ShouldBeUnique;
use Illuminate\Contracts\Queue\ShouldQueue;

final class UpdateSearchIndex implements ShouldQueue, ShouldBeUnique
{
    public int $uniqueFor = 3600;

    public function uniqueId(ProductUpdatedEvent $event): string
    {
        return 'search-index:' . $event->productId;
    }

    public function handle(ProductUpdatedEvent $event): void
    {
        // Update search index
    }
}
```

## Laravel Events vs Domain Events

| Feature | Laravel Events | Domain Events |
|---------|---------------|---------------|
| Location | `app/Events/` | `src/Domain/*/Event/` |
| Dependencies | `Dispatchable`, `SerializesModels` | None (pure PHP) |
| Dispatching | `Event::dispatch()` or `event()` | Collected in aggregate, dispatched by Application |
| Use For | Infrastructure: notifications, cache, logging | Business state changes |
| Async Support | `ShouldQueue` on listeners | Via queue adapter |
| Testing | `Event::fake()` | Direct assertion on `releaseEvents()` |

## Testing Events

```php
use Illuminate\Support\Facades\Event;

// Fake all events
Event::fake();

$this->postJson('/api/orders', $payload);

Event::assertDispatched(OrderCreatedEvent::class);
Event::assertDispatched(fn (OrderCreatedEvent $e) => $e->orderId !== null);
Event::assertNotDispatched(OrderCancelledEvent::class);

// Fake specific events only
Event::fake([OrderCreatedEvent::class]);

// Scoped fake
$order = Event::fakeFor(function () {
    return Order::factory()->create();
});
```

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Discovery | Auto-discovery via type-hinted `handle()` methods |
| Listener Style | One listener per class, `ShouldQueue` for async |
| Subscribers | Group by bounded context (Auth, Payment), register in provider |
| Domain Events | Pure PHP in Domain; `LaravelEventDispatcher` adapter in Infrastructure |
| Transaction Safety | `ShouldDispatchAfterCommit` for events with DB side effects |
| Idempotency | `ShouldBeUnique` on queued listeners |
| Business Logic | Never in listeners — delegate to Use Cases |
| Testing | `Event::fake()` for Laravel events; direct assertions for domain events |
