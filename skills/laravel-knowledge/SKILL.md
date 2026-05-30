---
name: laravel-knowledge
description: Laravel framework knowledge base. Provides architecture, DDD integration, Eloquent persistence, service container, security, queues, events, infrastructure components, testing, and antipatterns for Laravel PHP projects.
---

# Laravel Knowledge Base

Quick reference for Laravel framework patterns, DDD integration strategies, and PHP 8.4 best practices for building scalable Laravel applications.

## Core Principles

### Service Providers

Service Providers are the central place to configure and bootstrap the application. All bindings, event listeners, middleware, and routes are registered through providers.

### Facades

Facades provide a static-like interface to classes in the service container. Prefer dependency injection over Facades in Domain and Application layers; Facades are acceptable in Presentation and Infrastructure layers.

### Directory Structure

```
Default Laravel:                DDD-Aligned Laravel:
app/                            app/
├── Http/Controllers/           src/
├── Models/                     ├── Domain/
├── Providers/                  │   ├── Order/
├── Services/                   │   │   ├── Entity/
├── Events/                     │   │   ├── ValueObject/
├── Listeners/                  │   │   ├── Repository/
├── Jobs/                       │   │   └── Event/
├── Mail/                       │   └── Customer/
└── Exceptions/                 ├── Application/
                                │   ├── Order/UseCase/
                                │   └── Customer/UseCase/
                                └── Infrastructure/
                                    ├── Persistence/
                                    ├── Http/
                                    └── Provider/
```

## Quick Checklists

### DDD-Compatible Laravel Project

- [ ] Domain layer has zero Laravel imports
- [ ] Eloquent Models live in Infrastructure, not Domain
- [ ] Repository pattern used for persistence access (folder placement varies by architectural style)
- [ ] Service Providers wire interfaces to implementations
- [ ] Domain Events decoupled from Laravel Event system
- [ ] Value Objects used instead of primitive types
- [ ] Controllers are thin, delegate to Use Cases
- [ ] Authorization uses Policies delegating to domain Specifications
- [ ] Queued jobs have retry strategy, `failed()` method, and concurrency protection
- [ ] Domain defines its own `EventDispatcherInterface` (not Laravel `Event` facade)
- [ ] Infrastructure components (Cache, HTTP Client) accessed via domain ports

### Layer Boundary Checks

- [ ] No `use Illuminate\...` in Domain layer
- [ ] No business logic in Controllers or Middleware
- [ ] FormRequest used for input validation
- [ ] API Resources used for response transformation
- [ ] Single-action controllers for complex endpoints
- [ ] No direct DB queries in Controllers

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Eloquent in Domain layer | `use Illuminate\Database` in Domain/ | Critical |
| Business logic in Controller | if/switch on domain state in Controllers | Critical |
| Fat Eloquent Model | Model with 500+ lines, business methods | Critical |
| Facade in Domain | `use Illuminate\Support\Facades` in Domain/ | Critical |
| Missing FormRequest | Raw `$request->input()` with inline validation | Warning |
| N+1 query | Relationship access in loops without eager loading | Warning |
| Missing API Resource | Array building in Controller for responses | Warning |
| Direct DB in Controller | `DB::table()` or `Model::where()` in Controller | Warning |
| Business logic in Policy | DB queries or complex logic in Policy class | Warning |
| Missing job retry strategy | `ShouldQueue` without `$tries` or `backoff()` | Warning |
| Event facade in Domain | `Event::dispatch()` or `event()` in Domain layer | Critical |
| Cache/HTTP in Domain | `Cache::` or `Http::` in Domain layer | Critical |

## PHP 8.4 Laravel Patterns

### Single-Action Controller

```php
<?php

declare(strict_types=1);

namespace Order;

use UseCase\CreateOrderUseCase;
use Order\CreateOrderRequest;
use Order\OrderResource;
use Illuminate\Http\JsonResponse;
use Symfony\Component\HttpFoundation\Response;

final readonly class CreateOrderController
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
    ) {}

    public function __invoke(CreateOrderRequest $request): JsonResponse
    {
        $orderId = $this->createOrder->execute($request->toCommand());

        return OrderResource::make($orderId)
            ->response()
            ->setStatusCode(Response::HTTP_CREATED);
    }
}
```

### FormRequest

```php
<?php

declare(strict_types=1);

namespace Order;

use Command\CreateOrderCommand;
use ValueObject\CustomerId;
use Illuminate\Foundation\Http\FormRequest;

final class CreateOrderRequest extends FormRequest
{
    /** @return array<string, mixed> */
    public function rules(): array
    {
        return [
            'customer_id' => ['required', 'uuid'],
            'lines' => ['required', 'array', 'min:1'],
            'lines.*.product_id' => ['required', 'uuid'],
            'lines.*.quantity' => ['required', 'integer', 'min:1'],
        ];
    }

    public function toCommand(): CreateOrderCommand
    {
        return new CreateOrderCommand(
            customerId: new CustomerId($this->validated('customer_id')),
            lines: $this->validated('lines'),
        );
    }
}
```

### Application Service (Use Case)

```php
<?php

declare(strict_types=1);

namespace UseCase;

use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: $command->customerId,
            lines: $command->lines,
        );

        $this->orders->save($order);

        return $order->id();
    }
}
```

## References

For detailed information, load these reference files:

- `references/architecture.md` -- Service Providers, Facades, directory structure, module patterns
- `references/ddd-integration.md` -- Extracting Domain from app/, Eloquent separation, Domain Events
- `references/routing-http.md` -- Controllers, middleware, FormRequest, API Resources, policies
- `references/persistence.md` -- Eloquent ORM, migrations, transactions, read/write splitting
- `references/dependency-injection.md` -- Service Container, contextual binding, interface binding
- `references/testing.md` -- Feature/Unit tests, Pest, factories, mocking, database testing
- `references/security.md` -- Gates, Policies with Specifications, password hashing, Sanctum, User model separation
- `references/queues-advanced.md` -- Job middleware, batching, chaining, retry/DLQ, Horizon, unique jobs, CQRS
- `references/event-system.md` -- Event discovery, queued listeners, subscribers, domain event bridge, testing
- `references/infrastructure-components.md` -- Cache, HTTP Client, Rate Limiting, Task Scheduling, Locks with DDD ports
- `references/antipatterns.md` -- God Model, fat controller, Facade abuse, N+1 detection
