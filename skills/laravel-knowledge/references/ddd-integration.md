# DDD Integration with Laravel

Strategies for implementing Domain-Driven Design within a Laravel application while keeping the Domain layer pure.

## Extracting Domain from app/ Directory

### Migration Strategy

| Step | Action | Risk |
|------|--------|------|
| 1 | Create `src/Domain/` directory | None |
| 2 | Move pure business logic classes | Low |
| 3 | Extract interfaces from Eloquent repos | Medium |
| 4 | Replace Eloquent models in Domain with Entities | High |
| 5 | Wire via Service Providers | Low |

### Detection Patterns

```bash
# Check if Domain layer exists
Glob: src/Domain/*/
Glob: app/Domain/*/

# Check for Laravel imports in Domain (CRITICAL)
Grep: "use Illuminate\\" --glob "**/Domain/**/*.php"
Grep: "use App\\Models\\" --glob "**/Domain/**/*.php"

# Find business logic still in app/Models
Grep: "public function (calculate|validate|process|verify|approve)" --glob "**/Models/**/*.php"
```

## Eloquent Model vs Domain Entity

### Separation Strategy

**Bad -- Eloquent as Domain Entity:**
```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

// BAD: Mixing persistence with business logic
class Order extends Model
{
    protected $fillable = ['customer_id', 'status', 'total'];

    public function confirm(): void
    {
        if ($this->status !== 'draft') {
            throw new \DomainException('Only draft orders can be confirmed');
        }
        $this->status = 'confirmed';
        $this->save(); // Persistence coupled with domain logic
    }
}
```

**Good -- Separated Entity and Model:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

// Domain Entity: no Eloquent, no framework
final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines;

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        OrderStatus $status = OrderStatus::Draft,
    ) {
        $this->status = $status;
        $this->lines = [];
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidOrderStateException('Only draft orders can be confirmed');
        }
        if (empty($this->lines)) {
            throw new EmptyOrderException('Order must have at least one line');
        }
        $this->status = OrderStatus::Confirmed;
    }

    public function id(): OrderId { return $this->id; }
    public function status(): OrderStatus { return $this->status; }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence\Eloquent\Model;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Concerns\HasUuids;

// Infrastructure Model: persistence only, no business logic
final class OrderModel extends Model
{
    use HasUuids;

    protected $table = 'orders';
    protected $fillable = ['id', 'customer_id', 'status', 'total_cents'];

    public function lines(): HasMany
    {
        return $this->hasMany(OrderLineModel::class, 'order_id');
    }
}
```

## Repository Pattern with Eloquent

### Interface in Domain

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Repository;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\ValueObject\OrderId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
    public function nextIdentity(): OrderId;
}
```

### Eloquent Implementation in Infrastructure

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence\Eloquent;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Order\ValueObject\OrderId;
use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;
use App\Infrastructure\Persistence\Eloquent\Mapper\OrderMapper;

final readonly class EloquentOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private OrderMapper $mapper,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $model = OrderModel::with('lines')->find($id->value());

        return $model !== null
            ? $this->mapper->toDomain($model)
            : null;
    }

    public function save(Order $order): void
    {
        $data = $this->mapper->toPersistence($order);

        OrderModel::updateOrCreate(
            ['id' => $data['id']],
            $data,
        );
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

### Mapper Between Domain and Persistence

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence\Eloquent\Mapper;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\ValueObject\CustomerId;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Order\ValueObject\OrderStatus;
use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;

final readonly class OrderMapper
{
    public function toDomain(OrderModel $model): Order
    {
        return new Order(
            id: new OrderId($model->id),
            customerId: new CustomerId($model->customer_id),
            status: OrderStatus::from($model->status),
        );
    }

    /** @return array<string, mixed> */
    public function toPersistence(Order $order): array
    {
        return [
            'id' => $order->id()->value(),
            'customer_id' => $order->customerId()->value(),
            'status' => $order->status()->value,
        ];
    }
}
```

## Domain Events with Laravel Events

### Pure Domain Event

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Event;

// Pure domain event: no Laravel dependency
final readonly class OrderConfirmedEvent
{
    public function __construct(
        public string $orderId,
        public \DateTimeImmutable $confirmedAt,
    ) {}
}
```

### Laravel Event Bridge in Infrastructure

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use App\Domain\Shared\EventDispatcherInterface;
use Illuminate\Contracts\Events\Dispatcher;

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

## Application Services vs Laravel Services

| Aspect | Application Service (UseCase) | Laravel Service |
|--------|-------------------------------|-----------------|
| Location | `src/Application/` | `app/Services/` |
| Dependencies | Domain interfaces only | May use Laravel classes |
| Purpose | Orchestrate domain operations | Infrastructure glue |
| Framework coupling | None | Laravel-specific |
| Testability | Pure unit tests | Requires Laravel container |

## Keeping Domain Pure

### Detection Patterns

```bash
# Laravel imports in Domain (MUST be zero)
Grep: "use Illuminate\\" --glob "**/Domain/**/*.php"
Grep: "use App\\Models\\" --glob "**/Domain/**/*.php"

# Eloquent usage in Domain
Grep: "extends Model" --glob "**/Domain/**/*.php"
Grep: "->save\(\)|->delete\(\)|->update\(" --glob "**/Domain/**/*.php"

# Framework helpers in Domain
Grep: "\\bapp\(|\\bconfig\(|\\benv\(|\\bcache\(|\\blog\(" --glob "**/Domain/**/*.php"
```

### Rule: Domain Layer Allowed Imports

```
ALLOWED in Domain:
  - PHP built-in classes (DateTimeImmutable, Exception, etc.)
  - Other Domain layer classes
  - Shared kernel / common Value Objects

FORBIDDEN in Domain:
  - Illuminate\* (any Laravel namespace)
  - App\Models\* (Eloquent models)
  - Any third-party library
```

## Security in DDD Context

The Laravel auth system (`UserModel extends Authenticatable`) belongs in Infrastructure. Domain defines a pure `User` aggregate.

**Key patterns:**
- Domain `User` entity stays pure PHP — no `Authenticatable` trait
- Infrastructure `UserModel` wraps auth concerns (Sanctum, Notifications)
- Authorization uses Policies that delegate business rules to domain Specifications
- Password hashing uses a domain `PasswordHasherInterface` port

See `security.md` for full implementation details with Policies, Gates, and Sanctum patterns.

## Advanced Queue Patterns

The basic queue setup in Laravel uses `ShouldQueue` jobs. For production DDD systems:
- **Job middleware** (`WithoutOverlapping`) for aggregate concurrency protection
- **Retry strategy** with exponential backoff for transient failures
- **Job batching** (`Bus::batch()`) for bulk aggregate operations
- **Job chaining** (`Bus::chain()`) for saga-like sequential workflows
- **Unique jobs** (`ShouldBeUnique`) for idempotent processing

See `queues-advanced.md` for middleware, batching, chaining, DLQ, and Horizon configuration.

## Event System Integration

Laravel Events serve infrastructure concerns (notifications, caching). Domain events are pure PHP.

**Bridge pattern:**
1. Domain aggregate collects events via `releaseEvents()`
2. Application layer dispatches via domain `EventDispatcherInterface`
3. Infrastructure `LaravelEventDispatcher` adapter forwards to Laravel event system
4. Queued listeners process async (notifications, projections)

See `event-system.md` for queued listeners, subscribers, `ShouldDispatchAfterCommit`, and testing patterns.

## Keeping Domain Pure — Extended Summary

| DDD Aspect | Laravel Component | Integration Pattern |
|------------|-------------------|---------------------|
| User Aggregate | Auth (`Authenticatable`) | Infrastructure `UserModel` wrapping Domain entity |
| Authorization | Policies + Gates | Policy delegates to domain Specification |
| Aggregate Concurrency | Queue (`WithoutOverlapping`) | Job middleware keyed by aggregate ID |
| Domain Events | Events + Queues | Domain `EventDispatcherInterface` + Laravel adapter |
| Caching | Cache facade/manager | Domain port + `LaravelPriceCache` adapter |
| External APIs | HTTP Client | Domain port + scoped `Http::macro()` adapter |
