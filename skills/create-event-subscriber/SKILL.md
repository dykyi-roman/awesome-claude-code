---
name: create-event-subscriber
description: Generates Event Subscriber classes that react to framework or domain events. Subscribers declare a static list of events they handle and react via callback methods. Works with Symfony EventDispatcher, PSR-14, or Laravel events. Includes templates for exception handlers, request lifecycle hooks, and domain-event reactions.
---

# Event Subscriber Generator

Generate Event Subscriber classes — long-lived listeners that declare a static list of events they handle. Subscribers are auto-registered by the event dispatcher and routed by event name.

## Subscriber characteristics

- **Static event list**: `getSubscribedEvents()` returns the events handled; the dispatcher reads this once to route events.
- **One subscriber, many events**: a single class can react to multiple related events.
- **Side effects**: subscribers usually perform side effects (HTTP response shaping, logging, dispatching follow-up actions). They aren't pure transformers.
- **Stateless**: dependencies injected via constructor; no per-event state on instance.
- **Boundary marker**: subscribers usually sit at boundaries (HTTP kernel, domain-event dispatcher, console kernel). Don't put core business logic here.

## When to use

| Scenario | Use a subscriber |
|----------|------------------|
| Translate domain exceptions into HTTP responses | Yes — Symfony `KernelEvents::EXCEPTION` |
| Send notification when an aggregate publishes a domain event | Yes — domain event listener |
| Add a request-id header to every response | Yes — `KernelEvents::RESPONSE` |
| Log every command bus dispatch | Yes — Messenger middleware OR a subscriber on bus events |
| One-shot business operation triggered by user input | No — use a UseCase / Handler |
| Cross-context call | No — use an Anti-Corruption Layer + event |

## Placement

Folder placement varies by your project's architecture; whatever folder hosts event handlers in your project is where Subscribers belong.

## Templates

### Symfony kernel exception subscriber

```php
<?php

declare(strict_types=1);

namespace Subscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;
use Symfony\Component\HttpKernel\KernelEvents;

final readonly class ExceptionSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::EXCEPTION => 'onKernelException',
        ];
    }

    public function onKernelException(ExceptionEvent $event): void
    {
        $exception = $event->getThrowable();

        $response = match (true) {
            $exception instanceof DomainException => new JsonResponse(
                ['error' => $exception->getMessage()],
                Response::HTTP_BAD_REQUEST,
            ),
            $exception instanceof EntityNotFoundException => new JsonResponse(
                ['error' => $exception->getMessage()],
                Response::HTTP_NOT_FOUND,
            ),
            default => null,
        };

        if ($response !== null) {
            $event->setResponse($response);
        }
    }
}
```

### Domain event subscriber

```php
<?php

declare(strict_types=1);

namespace Subscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;

final readonly class SendOrderConfirmationEmailSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private EmailServiceInterface $emailService,
        private CustomerQueryInterface $customerQuery,
    ) {}

    public static function getSubscribedEvents(): array
    {
        return [
            OrderConfirmed::class => 'onOrderConfirmed',
        ];
    }

    public function onOrderConfirmed(OrderConfirmed $event): void
    {
        $customer = $this->customerQuery->findByOrderId($event->orderId());

        $this->emailService->send(
            to: $customer->email(),
            template: 'order_confirmed',
            data: [
                'order_id' => $event->orderId()->value(),
                'total' => $event->total()->amount(),
            ],
        );
    }
}
```

### Multi-event subscriber

```php
<?php

declare(strict_types=1);

namespace Subscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\Event\ResponseEvent;
use Symfony\Component\HttpKernel\KernelEvents;

final readonly class RequestIdSubscriber implements EventSubscriberInterface
{
    public function __construct(
        private CorrelationContextInterface $correlation,
    ) {}

    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::REQUEST => ['onRequest', 100],   // priority: earlier
            KernelEvents::RESPONSE => ['onResponse', -100], // priority: later
        ];
    }

    public function onRequest(RequestEvent $event): void
    {
        $requestId = $event->getRequest()->headers->get('X-Request-Id')
            ?? bin2hex(random_bytes(8));

        $this->correlation->set($requestId);
    }

    public function onResponse(ResponseEvent $event): void
    {
        $event->getResponse()->headers->set(
            'X-Request-Id',
            $this->correlation->current(),
        );
    }
}
```

### Unit test pattern

```php
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class ExceptionSubscriberTest extends TestCase
{
    public function testTranslatesDomainExceptionToBadRequest(): void
    {
        $subscriber = new ExceptionSubscriber();
        $event = $this->makeExceptionEvent(new DomainException('Invalid state'));

        $subscriber->onKernelException($event);

        $response = $event->getResponse();
        self::assertNotNull($response);
        self::assertSame(400, $response->getStatusCode());
    }

    public function testLeavesUnknownExceptionsAlone(): void
    {
        $subscriber = new ExceptionSubscriber();
        $event = $this->makeExceptionEvent(new \RuntimeException('Unexpected'));

        $subscriber->onKernelException($event);

        self::assertNull($event->getResponse());
    }
}
```

## Generation steps

1. **Identify the event(s)** the subscriber will handle. Group related events into one subscriber when they share dependencies and behavior.
2. **Decide placement** — kernel / framework subscriber goes in Application; domain-event subscriber typically goes in the owning context's `Subscriber/` folder.
3. **List dependencies** the handler needs (only services/ports — no entities).
4. **Pick priority** if multiple subscribers handle the same event and order matters (Symfony format: `[method, priority]`).
5. **Generate unit tests** that verify each event handler in isolation.

## Detection patterns

```bash
# Find subscribers
Glob: **/*Subscriber.php
Grep: "implements EventSubscriberInterface|implements ListenerInterface" --glob "**/*.php"

# Find what events are subscribed
Grep: "getSubscribedEvents" --glob "**/*Subscriber.php" -A 10

# Subscribers doing too much (likely business logic)
Grep: "->save\(|->persist\(|->execute\(" --glob "**/*Subscriber.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Business logic in subscriber | Mixes orchestration with side-effect coordination | Dispatch to a UseCase / Handler from the subscriber |
| One subscriber per event class | Class explosion | Group related events when they share dependencies |
| Subscriber that calls `save()` on aggregates | Crosses transaction boundary inappropriately | Raise a follow-up event and let the originating UseCase commit |
| Heavy work in subscriber (HTTP calls, slow queries) | Blocks the dispatch cycle | Push work to a queue / async worker |
| Catching exceptions silently | Hides failures | Re-throw or log explicitly; never swallow |
