---
name: codeigniter-knowledge
description: CodeIgniter 4 framework knowledge base. Provides CI4 MVC architecture, DDD integration, persistence, services, security (Shield auth, Filters authorization, CSRF), event system, queue (codeigniter4/queue jobs, workers, retry), infrastructure components (cache, HTTP client, email, throttler), testing, and antipatterns for CodeIgniter PHP projects.
---

# CodeIgniter Knowledge Base

Quick reference for CodeIgniter 4 framework patterns and PHP implementation guidelines. CodeIgniter 4 is a complete rewrite of the framework, built for PHP 8.1+ with namespaces, autoloading, and a modern MVC architecture. It remains lightweight and fast while providing the tools needed for professional application development.

## Core Principles

### MVC Architecture

```
Request → index.php → Bootstrap → Routing
  → Filters (before) → Controller → Service/Model → View
  → Filters (after) → Response
```

**Key principles:**
- Lightweight core with minimal overhead
- HMVC-capable via modules (app/Modules/)
- Services container for dependency management
- Filters as middleware equivalent
- Entity classes for data hydration

## Quick Checklists

### DDD-Compatible CI4 Project

- [ ] Domain logic extracted from Models into Domain layer
- [ ] Repository pattern used for persistence access (folder placement varies by architectural style)
- [ ] Value Objects used instead of primitive types for domain concepts
- [ ] CI4 Models used only as persistence adapters
- [ ] Services registered in Config\Services for dependency injection
- [ ] Business rules not in Controllers or Filters
- [ ] Domain Events dispatched through domain `EventDispatcherInterface` port (not CI4 Events directly)
- [ ] Input validation at Controller level (not in Domain)
- [ ] Shield Groups/Permissions used only at Filter/Route level; Domain uses Specifications
- [ ] Queue job handlers delegate to Application UseCases
- [ ] Infrastructure components (Cache, HTTP Client, Email) accessed via domain ports

### Layer Boundary Checks

- [ ] No `use CodeIgniter\...` in Domain layer (in projects that enforce this)
- [ ] No direct database access outside Repository
- [ ] Controllers delegate to Application Services / Use Cases
- [ ] DTOs used for cross-layer data transfer
- [ ] Config\Services wires interfaces to implementations
- [ ] Entities are framework-free domain objects in projects that enforce isolation (not required if your style permits CI4 Entity in domain)

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Business logic in Controller | `app/Controllers/*.php` | Critical |
| Domain depends on CI4 framework | `use CodeIgniter\` in Domain classes | Critical |
| Direct DB queries in Controller | `$this->db->` in Controllers | Critical |
| Model contains business rules | Complex `if/switch` in Model methods | Warning |
| Missing input validation | Controllers without `$this->validate()` | Warning |
| God Controller | Controllers > 300 lines | Warning |
| Shield UserIdentity in Domain | `use CodeIgniter\Shield` in Domain layer | Critical |
| Queue in Domain | `service('queue')` in Domain layer | Critical |
| Cache/HTTP Client in Domain | `CacheInterface` or `CURLRequest` in Domain | Critical |
| Missing queue resilience | Jobs without `$retryAfter`/`$tries` | Warning |
| Hardcoded config values | Magic strings instead of `config()` | Info |

## PHP 8.4 CodeIgniter Patterns

### Controller (Thin, Delegates to Service)

```php
<?php
declare(strict_types=1);
namespace Api;

use App\Controllers\BaseController;
use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function __construct(
        private readonly OrderService $orderService,
    ) {}

    public function show(string $id): ResponseInterface
    {
        $order = $this->orderService->findById($id);
        return $this->response->setJSON(['id' => $order->id, 'status' => $order->status->value]);
    }
}
```

### Service (Application Layer)

```php
<?php
declare(strict_types=1);
namespace App\Services;

final readonly class OrderService
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function confirm(string $orderId): void
    {
        $order = $this->orders->findById($orderId)
            ?? throw new OrderNotFoundException($orderId);
        $order->confirm();
        $this->orders->save($order);
        $this->events->dispatch(new OrderConfirmedEvent($order->id()));
    }
}
```

### Model as Repository Adapter

```php
<?php
declare(strict_types=1);
namespace App\Models;

use CodeIgniter\Model;

final class OrderModel extends Model
{
    protected $table         = 'orders';
    protected $primaryKey    = 'id';
    protected $returnType    = OrderEntity::class;
    protected $allowedFields = ['customer_id', 'status', 'total', 'notes'];
    protected $useTimestamps = true;
}
```

## References

For detailed information, load these reference files:

- `references/architecture.md` -- CI4 MVC structure, modules, directory layout
- `references/ddd-integration.md` -- Domain extraction, Repository pattern, Value Objects in CI4
- `references/routing-http.md` -- Controllers, Filters, RESTful routing, validation
- `references/persistence.md` -- CI4 Model, Query Builder, Entity classes, migrations
- `references/dependency-injection.md` -- Services class, custom registration, DI patterns
- `references/testing.md` -- CIUnitTestCase, DatabaseTestTrait, feature testing, mocking
- `references/security.md` -- Shield authentication/authorization, Filters, CSRF, password hashing with DDD
- `references/event-system.md` -- CI4 Events, domain event dispatching, lifecycle events, testing
- `references/queue.md` -- codeigniter4/queue jobs, workers, retry, chained jobs, queue events with DDD
- `references/infrastructure-components.md` -- Cache, CURLRequest HTTP client, Email, Throttler with DDD ports
- `references/antipatterns.md` -- Common violations with detection patterns and fixes
