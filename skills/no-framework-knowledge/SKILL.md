---
name: no-framework-knowledge
description: Framework-less PHP knowledge base. Provides pure PHP project architecture, DDD integration, PSR-7/PSR-15 HTTP, standalone persistence, DI containers, security (JWT lcobucci/jwt, RBAC middleware, password hashing, CSRF), event system (PSR-14, league/event, domain events, async processing), queue (enqueue/enqueue, php-amqplib, workers, supervisor), infrastructure components (PSR-6/16 cache, PSR-18 HTTP client, mailer, rate limiting), testing, and antipatterns for projects without a full framework.
---

# No-Framework PHP Knowledge Base

Quick reference for building framework-free PHP applications using PSR standards and standalone Composer packages. Covers everything needed to run a production-grade project without Symfony, Laravel, or any full-stack framework. Applicable across architectural styles (Clean, Hexagonal, Layered, MVC).

## Core Principles

### PSR Compliance

| PSR | Purpose | Recommended Package |
|-----|---------|---------------------|
| PSR-4 | Autoloading | Composer autoloader |
| PSR-7 | HTTP Messages | `nyholm/psr7` or `guzzlehttp/psr7` |
| PSR-11 | Container Interface | `php-di/php-di` or `league/container` |
| PSR-15 | HTTP Handlers & Middleware | `relay/relay` or custom pipeline |
| PSR-17 | HTTP Factories | `nyholm/psr7` (includes factories) |
| PSR-3 | Logging | `monolog/monolog` |
| PSR-6/PSR-16 | Caching | `symfony/cache` (standalone) |

### Key Advantages

- **Maximum domain freedom** — Domain layer is pure PHP by default
- **Composable packages** — pick exactly the libraries you need
- **Full control** — bootstrap, middleware, error handling are explicit
- **Lightweight** — no hidden magic, no auto-wiring unless configured

### Architecture Stack

```
public/index.php (Front Controller) → Middleware Pipeline (PSR-15)
  → Presentation (Actions) → Application (Use Cases) → Domain (Entities/VOs)
  → Infrastructure (Repos/Adapters) ← Composer + PSR-4 Autoloading
```

## Quick Checklists

### DDD-Compatible Pure PHP Project

- [ ] `declare(strict_types=1)` in every file
- [ ] PSR-4 autoloading via Composer
- [ ] Domain layer has zero external `use` statements (no Doctrine, no framework)
- [ ] Repository pattern used for persistence access (folder placement varies by architectural style)
- [ ] DI container configured explicitly (PHP-DI or League)
- [ ] PSR-7 request/response, PSR-15 middleware pipeline
- [ ] Front controller in `public/index.php`
- [ ] Environment config via `.env` + `vlucas/phpdotenv`
- [ ] Error handling middleware with custom exception hierarchy
- [ ] Security via JWT middleware (lcobucci/jwt) + RBAC; Domain uses Specifications for authorization
- [ ] Queue job handlers delegate to Application UseCases; Domain dispatches events, not jobs
- [ ] Infrastructure components (Cache, HTTP Client, Mailer) accessed via domain port interfaces
- [ ] Domain EventDispatcherInterface port; Infrastructure provides PSR-14 or InMemory adapter

### Layer Boundary Checks

- [ ] No `use Illuminate\\` or `use Symfony\\` in Domain or Application layers
- [ ] No HTTP concepts in Application layer
- [ ] All external services accessed through port interfaces
- [ ] Compiled DI container in production
- [ ] Database migrations managed by standalone tool

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Missing `declare(strict_types=1)` | Any PHP file | Critical |
| `require` / `include` instead of autoloading | Entry points, legacy files | Critical |
| Global state (`$_GET`, `$_POST`, `$_SESSION`) | Presentation layer | Critical |
| Framework dependency in Domain | `src/Domain/**/*.php` | Critical |
| Custom ORM instead of using Doctrine/Cycle | `src/Infrastructure/**/*.php` | Warning |
| No PSR-7 — raw `echo` / `header()` calls | `public/index.php`, controllers | Warning |
| Service Locator in Application layer | `src/Application/**/*.php` | Warning |
| Missing DI container — manual `new` chains | Bootstrap files | Warning |
| No middleware pipeline — logic in `index.php` | `public/index.php` | Info |
| JWT/session logic in Domain | `src/Domain/**/*.php` | Critical |
| Queue library in Domain | `use Enqueue\\` or `use PhpAmqpLib\\` in Domain | Critical |
| Cache/HTTP Client in Domain | `CacheInterface` or `HttpClientInterface` in Domain | Critical |
| Missing queue resilience | Workers without retry/error handling | Warning |

## PHP 8.4 No-Framework Patterns

### PSR-15 Middleware

```php
declare(strict_types=1);

namespace Middleware;

use Psr\Http\Message\{ResponseInterface, ServerRequestInterface};
use Psr\Http\Server\{MiddlewareInterface, RequestHandlerInterface};

final readonly class CorsMiddleware implements MiddlewareInterface
{
    public function __construct(private string $allowedOrigin = '*') {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        return $handler->handle($request)
            ->withHeader('Access-Control-Allow-Origin', $this->allowedOrigin)
            ->withHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE');
    }
}
```

### Application Service (Use Case)

```php
declare(strict_types=1);

namespace UseCase;

final readonly class PlaceOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(PlaceOrderCommand $command): OrderId
    {
        $order = Order::create($command->customerId, $command->lines);
        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }

        return $order->id();
    }
}
```

### Front Controller

```php
declare(strict_types=1);

require dirname(__DIR__) . '/vendor/autoload.php';
Dotenv\Dotenv::createImmutable(dirname(__DIR__))->load();
$container = require dirname(__DIR__) . '/config/container.php';
$container->get(App::class)->run();
```

## References

For detailed information, load these reference files:

- `references/architecture.md` — Project structure, PSR-4 autoloading, bootstrap patterns
- `references/ddd-integration.md` — Pure Domain layer, Value Objects, Entities, Domain Events
- `references/routing-http.md` — PSR-7/PSR-15 HTTP, routing, middleware pipeline
- `references/persistence.md` — Doctrine/Cycle standalone, PDO repositories, migrations
- `references/dependency-injection.md` — PHP-DI, League Container, PSR-11, compiled containers
- `references/testing.md` — PHPUnit standalone, mocking, HTTP testing, database testing
- `references/antipatterns.md` — Common no-framework mistakes with detection patterns
- `references/security.md` — JWT authentication (lcobucci/jwt), RBAC middleware, password hashing, CSRF, security headers
- `references/event-system.md` — PSR-14, league/event, custom dispatcher, domain events, async event processing
- `references/queue.md` — enqueue/enqueue, php-amqplib, workers, job dispatcher, supervisor
- `references/infrastructure-components.md` — Cache PSR-6/16, HTTP Client PSR-18, Mailer, Rate Limiting
