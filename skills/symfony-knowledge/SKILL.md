---
name: symfony-knowledge
description: Symfony framework knowledge base. Provides architecture, DDD integration, persistence, DI, security, messenger, workflow, events, infrastructure components, testing, and antipatterns for Symfony PHP projects.
---

# Symfony Knowledge Base

Quick reference for Symfony framework patterns, DDD integration, and PHP implementation guidelines for auditing and generating Symfony-based applications.

## Core Principles

- **Bundle System** — Symfony's plugin mechanism. Third-party code is installed as bundles; application code lives outside bundles in `src/`.
- **Symfony Flex** — Automates bundle installation via recipes. Standard dirs: `config/`, `src/`, `public/`, `var/`, `migrations/`, `tests/`, `templates/`.
- **Kernel** — Entry point that boots the container, registers bundles, loads configuration. Must remain thin — no business logic.

## Quick Checklists

### DDD-Compatible Symfony Project

- [ ] Domain layer has zero Symfony imports
- [ ] Doctrine mapping uses XML or PHP config (not entity attributes)
- [ ] Controllers are invokable (single action per class)
- [ ] Messenger handles commands and queries via separate buses
- [ ] Value Objects use custom Doctrine types
- [ ] Repository interfaces in Domain, implementations in Infrastructure
- [ ] `services.yaml` binds interfaces to implementations
- [ ] Domain events are dispatched, not Doctrine lifecycle events
- [ ] Authorization uses Voters delegating to domain Specifications
- [ ] Workflow guards delegate to domain Specifications (no inline business logic)
- [ ] Domain defines its own `EventDispatcherInterface` (not Symfony's)
- [ ] Infrastructure components (Cache, HTTP Client) accessed via domain ports

### Clean Architecture in Symfony

- [ ] No `use Symfony\` in Domain or Application layers
- [ ] No `use Doctrine\` in Domain layer
- [ ] Use Cases accept Command/Query DTOs, not Request objects
- [ ] Controllers only map HTTP to Use Case calls
- [ ] EventSubscribers do not contain business logic
- [ ] Compiler passes do not encode domain rules

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Doctrine attributes in Domain entities | `Domain/**/*.php` with `#[ORM\` | Critical |
| Symfony Request/Response in Application layer | `Application/**/*.php` | Critical |
| Business logic in Controller | Controllers with `if`/`switch` on domain state | Warning |
| Fat Controller (multiple actions) | Controllers with 2+ public methods | Warning |
| Entity used as DTO across layers | Entity passed to templates/serializers directly | Warning |
| Service Locator via ContainerInterface | `$container->get()` in services | Critical |
| Doctrine EventListener with domain logic | `EventListener` classes with business rules | Warning |
| Hard-coded service IDs | `$container->get('service.id')` | Warning |
| UserInterface in Domain | `Domain/**/*.php` with `implements UserInterface` | Critical |
| Missing Messenger retry strategy | `messenger.yaml` without `retry_strategy` | Warning |
| Business logic in Workflow listener | Guard/transition listeners with domain rules | Warning |
| Symfony EventDispatcher in Domain | `Domain/**/*.php` with `use Symfony\Contracts\EventDispatcher` | Critical |
| Direct infrastructure in Application | `Application/**/*.php` with `CacheInterface`, `LockFactory` | Warning |

## PHP 8.4 Symfony Patterns

### Invokable Controller (Single Action)

```php
<?php
declare(strict_types=1);
namespace App\Order\Presentation\Api;

use App\Order\Application\Command\CreateOrderCommand;
use App\Order\Application\UseCase\CreateOrderUseCase;
use Symfony\Component\HttpFoundation\{JsonResponse, Request, Response};
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/orders', methods: ['POST'])]
final readonly class CreateOrderAction
{
    public function __construct(private CreateOrderUseCase $createOrder) {}

    public function __invoke(Request $request): JsonResponse
    {
        $data = $request->toArray();
        $orderId = $this->createOrder->execute(new CreateOrderCommand(
            customerId: $data['customer_id'],
            items: $data['items'],
        ));

        return new JsonResponse(['id' => $orderId->value], Response::HTTP_CREATED);
    }
}
```

### Use Case (Application Service)

```php
<?php
declare(strict_types=1);
namespace App\Order\Application\UseCase;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use App\Shared\Domain\EventDispatcherInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        $order = Order::create($command->customerId, $command->items);
        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }

        return $order->id();
    }
}
```

### Messenger Command Handler

```php
<?php
declare(strict_types=1);
namespace App\Order\Application\Handler;

use App\Order\Application\Command\ConfirmOrderCommand;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler(bus: 'command.bus')]
final readonly class ConfirmOrderHandler
{
    public function __construct(private OrderRepositoryInterface $orders) {}

    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);
        $order->confirm();
        $this->orders->save($order);
    }
}
```

## References

For detailed information, load these reference files:

- `references/architecture.md` — Bundle system, Flex recipes, standard vs DDD-aligned directory layout
- `references/ddd-integration.md` — Domain purity, Messenger CQRS, Domain Events, Value Objects with Doctrine
- `references/routing-http.md` — Invokable controllers, EventSubscribers, attribute routing, validation
- `references/persistence.md` — Doctrine ORM mapping, repositories, migrations, keeping Doctrine out of Domain
- `references/dependency-injection.md` — services.yaml, auto-wiring, tagged services, compiler passes, interface binding
- `references/testing.md` — WebTestCase, KernelTestCase, functional tests, fixtures, Messenger handler testing
- `references/security.md` — UserInterface adapter, Voters with Specifications, firewalls, password hashing, auth events
- `references/messenger-advanced.md` — Multiple buses, transports, retry strategy, DLQ, middleware, workers, serialization
- `references/workflow.md` — StateMachine for aggregates, enum places, guards with Specifications, audit trail
- `references/event-system.md` — EventDispatcher patterns, kernel events, domain event dispatching, PSR-14
- `references/infrastructure-components.md` — Cache, Lock, RateLimiter, HTTP Client, Serializer, Scheduler with DDD ports
- `references/antipatterns.md` — Fat controllers, entity as DTO, Doctrine in Domain, Service Locator, detection patterns
