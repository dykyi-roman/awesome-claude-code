---
name: yii-knowledge
description: Yii framework knowledge base. Provides Yii3 modular architecture, DDD integration, PSR-7/PSR-15 compliance, persistence, DI, security (RBAC, auth), event system (PSR-14), queue/jobs, infrastructure components (cache, rate limiter, HTTP client), testing, and antipatterns for Yii PHP projects.
---

# Yii Knowledge Base

Quick reference for Yii3 framework patterns and PHP implementation guidelines. Yii3 is a complete rewrite — modular, PSR-compliant, and designed for modern PHP 8.4+ applications.

## Core Principles

### PSR Compliance

Yii3 implements PSR-3 (log), PSR-4 (autoload), PSR-7/PSR-17 (HTTP messages/factories via `yiisoft/http-message`), PSR-11 (DI via `yiisoft/di`), PSR-12 (coding style), PSR-15 (middleware via `yiisoft/middleware-dispatcher`).

### Middleware Pipeline

```
Request → [Router] → [Auth] → [CORS] → [Action] → Response
              ↓                            ↓
         yiisoft/router            Application Logic
```

**Rule:** All HTTP handling flows through the PSR-15 middleware pipeline. No global state.

### Modular Package Architecture

Yii3 is split into independent packages (`yiisoft/*`). Install only what you need. No monolithic framework dependency.

## Quick Checklists

### DDD-Compatible Yii3 Project

- [ ] Domain layer has zero `use Yiisoft\` imports
- [ ] ActiveRecord used only in Infrastructure layer
- [ ] Repository pattern used for persistence access (folder placement varies by architectural style)
- [ ] Value Objects used instead of primitives in Domain
- [ ] Actions/Controllers only map input and delegate to UseCases
- [ ] DI container configured via providers, not service locator
- [ ] Domain events dispatched through domain `EventDispatcherInterface` port (not PSR-14 directly)
- [ ] RBAC Rules delegate business logic to domain Specifications
- [ ] Queue handlers delegate to Application UseCases
- [ ] Infrastructure components (Cache, HTTP Client) accessed via domain ports

### Layer Boundary Checks

- [ ] No `Yiisoft\ActiveRecord` in Domain or Application layers
- [ ] No HTTP concerns (`ServerRequestInterface`) in Application layer
- [ ] Middleware handles cross-cutting concerns (auth, CORS, logging)
- [ ] Config files separate from business logic
- [ ] Service providers wire interfaces to implementations
- [ ] Tests do not depend on Yii container for unit tests

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| ActiveRecord in Domain | `use Yiisoft\ActiveRecord` in Domain layer | Critical |
| Service Locator usage | `$container->get()` outside composition root | Critical |
| Business logic in Action | if/switch on domain state in Controller/Action | Critical |
| Framework in Domain (Clean/Onion projects) | `use Yiisoft\` in Domain namespace | Critical in Clean/Onion; acceptable in Layered |
| Fat middleware | Middleware doing business logic | Warning |
| Missing input validation | Action without request validation | Warning |
| IdentityInterface in Domain | `use Yiisoft\Auth` in Domain layer | Critical |
| RBAC logic in Domain | `use Yiisoft\Rbac` in Domain layer | Critical |
| Queue in Domain | `QueueInterface` in Domain layer | Critical |
| Cache/HTTP Client in Domain | `CacheInterface` or PSR-18 in Domain layer | Critical |
| Yii2 patterns in Yii3 | `Yii::$app->`, global helpers | Critical |

## PHP 8.4 Yii Patterns

### Action (Single Action Controller)

```php
declare(strict_types=1);

namespace Order;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
        private OrderRequestMapper $mapper,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $dto = $this->mapper->fromRequest($request);
        $result = $this->createOrder->execute($dto);

        return $this->responseFactory->createJson($result->toArray(), 201);
    }
}
```

### PSR-15 Middleware

```php
declare(strict_types=1);

namespace Middleware;

final readonly class CorrelationIdMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $correlationId = $request->getHeaderLine('X-Correlation-ID') ?: Uuid::v4();
        $request = $request->withAttribute('correlationId', $correlationId);

        return $handler->handle($request)
            ->withHeader('X-Correlation-ID', $correlationId);
    }
}
```

### UseCase with DI

```php
declare(strict_types=1);

namespace UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(CreateOrderDTO $dto): OrderResultDTO
    {
        $order = Order::create(
            id: $this->orders->nextIdentity(),
            customerId: $dto->customerId,
            lines: $dto->lines,
        );
        $this->orders->save($order);
        $this->events->dispatch(...$order->releaseEvents());

        return OrderResultDTO::fromEntity($order);
    }
}
```

## References

For detailed information, load these reference files:

- `references/architecture.md` — Yii3 modular architecture, middleware pipeline, config system
- `references/ddd-integration.md` — Extracting Domain from Yii, Repository pattern, Domain Events
- `references/routing-http.md` — Routing, Actions, PSR-7/PSR-15 middleware
- `references/persistence.md` — ActiveRecord, Cycle ORM, migrations, Repository pattern
- `references/dependency-injection.md` — yiisoft/di container, service providers, PSR-11
- `references/testing.md` — PHPUnit, fixtures, functional testing, middleware testing
- `references/security.md` — RBAC, authentication, IdentityInterface adapter, password hashing, CSRF
- `references/event-system.md` — PSR-14 dispatcher, listeners, domain event bridge, stoppable events
- `references/queue.md` — yii-queue, messages, handlers, middleware pipelines, retry, channels
- `references/infrastructure-components.md` — Cache (PSR-16), Rate Limiter, HTTP Client (PSR-18), Mailer with DDD ports
- `references/antipatterns.md` — Yii2-in-Yii3 detection, framework coupling, fat controllers, RBAC in Domain, missing queue resilience
