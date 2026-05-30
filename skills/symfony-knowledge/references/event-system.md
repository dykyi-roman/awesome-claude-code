# Symfony Event System

EventDispatcher patterns, domain event integration, kernel events, and PSR-14 alignment.

## EventDispatcherInterface

Symfony's event system is PSR-14 compatible since Symfony 5.

**Detection:**
```bash
# Event dispatcher usage
Grep: "EventDispatcherInterface" --glob "src/**/*.php"
Grep: "#\\[AsEventListener" --glob "src/**/*.php"
Grep: "EventSubscriberInterface" --glob "src/**/*.php"

# Domain events pattern
Grep: "DomainEvent|releaseEvents|recordedEvents" --glob "**/Domain/**/*.php"
```

| Interface | Source | Use |
|-----------|--------|-----|
| `Psr\EventDispatcher\EventDispatcherInterface` | PSR-14 | Domain port definition |
| `Symfony\Contracts\EventDispatcher\EventDispatcherInterface` | Symfony | Infrastructure implementation |
| `Symfony\Component\EventDispatcher\EventDispatcherInterface` | Symfony | Full-featured (add/remove listeners) |

## #[AsEventListener] vs EventSubscriberInterface

| Feature | `#[AsEventListener]` | `EventSubscriberInterface` |
|---------|---------------------|---------------------------|
| Registration | Auto-discovered via attribute | Must implement interface |
| Configuration | Attribute parameters | `getSubscribedEvents()` method |
| Single Responsibility | One method per listener | Multiple methods per class |
| Testability | Easy to test in isolation | Couples multiple concerns |
| Priority | `priority` attribute parameter | Array config in method |

**Bad — subscriber mixing concerns:**
```php
<?php

declare(strict_types=1);

namespace Order\Infrastructure\EventListener;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\Event\ResponseEvent;
use Symfony\Component\HttpKernel\KernelEvents;

// VIOLATION: Multiple unrelated concerns in one class
class AppEventSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::REQUEST => 'onRequest',
            KernelEvents::RESPONSE => 'onResponse',
            OrderPlacedEvent::class => 'onOrderPlaced',
        ];
    }

    public function onRequest(RequestEvent $event): void { /* logging */ }
    public function onResponse(ResponseEvent $event): void { /* headers */ }
    public function onOrderPlaced(OrderPlacedEvent $event): void { /* notification */ }
}
```

**Good — focused listeners with attributes:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventListener;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\KernelEvents;

#[AsEventListener(event: KernelEvents::REQUEST, priority: 10)]
final readonly class RequestLoggingListener
{
    public function __construct(
        private \Psr\Log\LoggerInterface $logger,
    ) {}

    public function __invoke(RequestEvent $event): void
    {
        $this->logger->info('Incoming request', [
            'method' => $event->getRequest()->getMethod(),
            'uri' => $event->getRequest()->getRequestUri(),
        ]);
    }
}
```

## Priority Management

Listeners execute in priority order (highest first). Document priorities explicitly.

| Priority Range | Convention | Example |
|----------------|-----------|---------|
| 200+ | Security / Auth | Authentication check |
| 100-199 | Validation / Normalization | Input sanitization |
| 0 (default) | Business logic | Standard handlers |
| -100 to -1 | Post-processing | Response modification |
| -200 and below | Logging / Audit | Request logging |

```php
#[AsEventListener(event: KernelEvents::REQUEST, priority: 200)]
final readonly class AuthenticationListener { /* ... */ }

#[AsEventListener(event: KernelEvents::REQUEST, priority: 100)]
final readonly class InputSanitizationListener { /* ... */ }

#[AsEventListener(event: KernelEvents::RESPONSE, priority: -100)]
final readonly class SecurityHeadersListener { /* ... */ }
```

## Kernel Events Lifecycle

```
REQUEST → CONTROLLER → CONTROLLER_ARGUMENTS → VIEW → RESPONSE → FINISH_REQUEST → TERMINATE
                                                  ↗
                                        EXCEPTION
```

| Event | When | Appropriate Use |
|-------|------|-----------------|
| `kernel.request` | Before controller resolved | Authentication, locale, CORS |
| `kernel.controller` | Controller resolved | Authorization check |
| `kernel.controller_arguments` | Arguments resolved | Argument validation |
| `kernel.view` | Controller returns non-Response | Convert DTO to Response |
| `kernel.response` | Response ready | Security headers, caching |
| `kernel.finish_request` | Sub-request completed | Cleanup |
| `kernel.terminate` | Response sent | Heavy operations (email, logs) |
| `kernel.exception` | Exception thrown | Error handling, logging |

**Bad — business logic in kernel listener:**
```php
<?php

declare(strict_types=1);

namespace Order\Infrastructure\EventListener;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\ControllerEvent;
use Symfony\Component\HttpKernel\KernelEvents;

// VIOLATION: Business logic in kernel listener
#[AsEventListener(event: KernelEvents::CONTROLLER)]
final readonly class OrderLimitListener
{
    public function __invoke(ControllerEvent $event): void
    {
        $user = $this->security->getUser();
        $orderCount = $this->orderRepo->countByUser($user->getId());

        // Business rule in infrastructure listener
        if ($orderCount >= 100) {
            throw new TooManyOrdersException();
        }
    }
}
```

**Good — keep business rules in domain, infrastructure handles cross-cutting:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventListener;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\ResponseEvent;
use Symfony\Component\HttpKernel\KernelEvents;

// Infrastructure concern: security headers
#[AsEventListener(event: KernelEvents::RESPONSE)]
final readonly class SecurityHeadersListener
{
    public function __invoke(ResponseEvent $event): void
    {
        $response = $event->getResponse();
        $response->headers->set('X-Content-Type-Options', 'nosniff');
        $response->headers->set('X-Frame-Options', 'DENY');
        $response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
    }
}
```

## Domain Event Dispatching

Domain defines its own `EventDispatcherInterface`; Symfony implements it.

**Bad — Symfony EventDispatcher in Domain layer:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Symfony\Contracts\EventDispatcher\EventDispatcherInterface;

// VIOLATION: Symfony interface in Domain
final class Order
{
    public function __construct(
        private EventDispatcherInterface $dispatcher,
    ) {}
}
```

**Good — Domain defines pure interface, Infrastructure adapts:**
```php
<?php

declare(strict_types=1);

namespace Domain;

// Pure PHP interface — no framework dependency
interface EventDispatcherInterface
{
    public function dispatch(DomainEvent $event): void;
}
```

```php
<?php

declare(strict_types=1);

namespace Event;

use Domain\DomainEvent;
use App\Shared\Domain\EventDispatcherInterface as DomainEventDispatcher;
use Symfony\Component\Messenger\MessageBusInterface;

// Infrastructure adapter — dispatches domain events via Messenger
final readonly class MessengerDomainEventDispatcher implements DomainEventDispatcher
{
    public function __construct(
        private MessageBusInterface $eventBus,
    ) {}

    public function dispatch(DomainEvent $event): void
    {
        $this->eventBus->dispatch($event);
    }
}
```

## Stopping Propagation

PSR-14 `StoppableEventInterface` allows listeners to stop event propagation.

```php
<?php

declare(strict_types=1);

namespace Event;

use Psr\EventDispatcher\StoppableEventInterface;

final class ValidationEvent implements StoppableEventInterface
{
    private bool $propagationStopped = false;

    /** @var array<string> */
    private array $errors = [];

    public function addError(string $error): void
    {
        $this->errors[] = $error;
        $this->propagationStopped = true;
    }

    public function isPropagationStopped(): bool
    {
        return $this->propagationStopped;
    }

    /** @return array<string> */
    public function errors(): array
    {
        return $this->errors;
    }
}
```

## EventDispatcher vs Messenger

| Feature | EventDispatcher | Messenger |
|---------|----------------|-----------|
| Execution | Synchronous (in-process) | Sync or async (via transports) |
| Return Value | Event object (with modifications) | Envelope with stamps |
| Multiple Handlers | All execute in order | All execute (parallel possible) |
| Retry | No | Yes (retry strategy) |
| Dead Letter Queue | No | Yes (failure transport) |
| Middleware | No | Yes (middleware pipeline) |
| Use For | Kernel events, sync hooks | Commands, queries, domain events |
| DDD Role | Infrastructure cross-cutting | CQRS bus, domain event delivery |

**Guideline:**
- Use EventDispatcher for synchronous, infrastructure-level hooks (kernel events, security events)
- Use Messenger for domain events, commands, queries (supports async, retry, DLQ)

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Listener Style | `#[AsEventListener]` over `EventSubscriberInterface` |
| Priorities | Document explicitly; follow convention ranges |
| Kernel Events | Infrastructure concerns only (headers, auth, logging) |
| Domain Events | Pure PHP interface in Domain, Messenger adapter in Infrastructure |
| Propagation | Use `StoppableEventInterface` (PSR-14) when needed |
| Sync vs Async | EventDispatcher for sync hooks; Messenger for domain/CQRS events |
| Business Logic | Never in kernel listeners; keep in domain or application layer |
