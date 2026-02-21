# DDD Integration with CodeIgniter 4

Strategies for applying Domain-Driven Design within a CI4 application.

## Domain Extraction from CI4 app/

### Recommended Directory Structure

```
app/
├── Domain/                              # Pure PHP, no CI4 dependencies
│   ├── Order/
│   │   ├── Entity/Order.php
│   │   ├── ValueObject/
│   │   │   ├── OrderId.php
│   │   │   ├── OrderStatus.php
│   │   │   └── Money.php
│   │   ├── Repository/OrderRepositoryInterface.php
│   │   ├── Service/OrderPricingService.php
│   │   └── Event/OrderConfirmedEvent.php
│   └── Customer/
│       ├── Entity/Customer.php
│       └── ValueObject/CustomerId.php
├── Application/                         # Use Cases, no infrastructure
│   └── Order/
│       ├── ConfirmOrderUseCase.php
│       ├── CreateOrderUseCase.php
│       └── DTO/OrderDTO.php
├── Infrastructure/                      # CI4 Model wrappers, adapters
│   └── Persistence/
│       ├── CIOrderRepository.php
│       └── CICustomerRepository.php
├── Controllers/                         # Thin controllers
└── Config/
    └── Services.php                     # Wiring layer
```

### Domain Entity (Pure PHP)

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

use App\Domain\Order\Event\OrderConfirmedEvent;
use App\Domain\Order\ValueObject\Money;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Order\ValueObject\OrderStatus;

final class Order
{
    /** @var array<object> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly string $customerId,
        private Money $total,
        private OrderStatus $status = OrderStatus::Draft,
    ) {}

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new \DomainException('Only draft orders can be confirmed');
        }

        if ($this->total->isZeroOrNegative()) {
            throw new \DomainException('Cannot confirm order with zero total');
        }

        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id);
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function status(): OrderStatus
    {
        return $this->status;
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

## CI4 Model to Repository Pattern

### Repository Interface (Domain Layer)

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

    public function delete(OrderId $id): void;
}
```

### Repository Implementation (Infrastructure Layer)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Order\ValueObject\Money;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Order\ValueObject\OrderStatus;
use App\Models\OrderModel;

final readonly class CIOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private OrderModel $model,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $row = $this->model->find($id->value());

        if ($row === null) {
            return null;
        }

        return new Order(
            id: new OrderId($row->id),
            customerId: $row->customer_id,
            total: new Money((int) $row->total),
            status: OrderStatus::from($row->status),
        );
    }

    public function save(Order $order): void
    {
        $data = [
            'id'          => $order->id()->value(),
            'customer_id' => $order->customerId(),
            'total'       => $order->total()->cents(),
            'status'      => $order->status()->value,
        ];

        $this->model->save($data);
    }

    public function delete(OrderId $id): void
    {
        $this->model->delete($id->value());
    }
}
```

## Domain Events in CI4

### Using CI4 Events System

```php
<?php

declare(strict_types=1);

// app/Config/Events.php
namespace Config;

use CodeIgniter\Events\Events;

Events::on('order.confirmed', static function (object $event): void {
    $notifier = service('orderNotificationService');
    $notifier->sendConfirmation($event->orderId);
});
```

### Event Dispatcher Adapter

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Event;

use App\Domain\Shared\EventDispatcherInterface;
use CodeIgniter\Events\Events;

final readonly class CIEventDispatcher implements EventDispatcherInterface
{
    public function dispatch(object $event): void
    {
        $eventName = $this->resolveEventName($event);
        Events::trigger($eventName, $event);
    }

    private function resolveEventName(object $event): string
    {
        $class = (new \ReflectionClass($event))->getShortName();

        return strtolower((string) preg_replace('/(?<!^)[A-Z]/', '.$0', $class));
    }
}
```

## Value Objects Integration

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\ValueObject;

final readonly class OrderId
{
    public function __construct(
        private string $value,
    ) {
        if (trim($value) === '') {
            throw new \InvalidArgumentException('OrderId cannot be empty');
        }
    }

    public function value(): string
    {
        return $this->value;
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\ValueObject;

enum OrderStatus: string
{
    case Draft     = 'draft';
    case Confirmed = 'confirmed';
    case Shipped   = 'shipped';
    case Cancelled = 'cancelled';
}
```

## Keeping Domain Pure in CodeIgniter

### Detection Patterns

```bash
# CRITICAL: Domain layer must not import CI4 framework
Grep: "use CodeIgniter\\\\" --glob "app/Domain/**/*.php"
Grep: "use Config\\\\" --glob "app/Domain/**/*.php"
Grep: "use App\\\\Models\\\\" --glob "app/Domain/**/*.php"

# Domain should not use CI4 helpers
Grep: "service\(|helper\(|config\(|cache\(" --glob "app/Domain/**/*.php"

# Good: Domain uses only its own namespace
Grep: "use App\\\\Domain\\\\" --glob "app/Domain/**/*.php"
```

### Wiring in Services

```php
<?php

declare(strict_types=1);

// app/Config/Services.php
namespace Config;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Infrastructure\Persistence\CIOrderRepository;
use App\Models\OrderModel;
use CodeIgniter\Config\BaseService;

final class Services extends BaseService
{
    public static function orderRepository(bool $getShared = true): OrderRepositoryInterface
    {
        if ($getShared) {
            return static::getSharedInstance('orderRepository');
        }

        return new CIOrderRepository(new OrderModel());
    }
}
```

### Common DDD Mistakes in CI4

| Mistake | Why It Happens | Fix |
|---------|---------------|-----|
| Extending `CodeIgniter\Entity` in Domain | CI4 docs encourage Entity usage | Use pure PHP domain entities |
| Using `model()` helper in Domain | CI4 convention | Inject repository interface |
| Validation rules in Domain Entity | CI4 Entity supports `$casts` | Keep domain validation in constructor |
| `$db` in Domain Service | Quick database access | Inject repository interface |
| Events via `Events::trigger()` in Domain | CI4 Events are global | Use domain event collection + dispatcher adapter |
| Shield `->can()` in Domain | Quick auth checks | Use domain Specifications |
| `service('queue')` in Domain | Async from entity | Infrastructure listener pushes jobs |
| `service('cache')` in Domain | Quick caching | Domain cache port + Infrastructure adapter |

## Security in DDD Context

Shield authentication belongs in Infrastructure/Presentation layers. Domain defines a pure `User` aggregate with domain roles (enum).

**Key patterns:**
- Domain `User` entity stays pure PHP — no `UserIdentity` or `Authenticatable`
- Infrastructure `ShieldUserProvider` wraps domain entity for Shield integration
- Shield Groups/Permissions used at route/Filter level; Domain uses Specifications for business rules
- Password hashing uses a domain `PasswordHasherInterface` port

See `security.md` for full implementation with Shield groups, permissions, Filters, and CSRF.

## Queue Integration

Queue jobs and handlers are Infrastructure concerns. Domain events are pure PHP — dispatched by Application layer, then Infrastructure listeners push to the `codeigniter4/queue`.

**Key patterns:**
- Jobs extend `BaseJob` and delegate to Application UseCases
- `$retryAfter` and `$tries` configure retry strategy per job
- Chained jobs for sequential execution via `service('queue')->chain()`
- `QueueEventManager` events for monitoring (JOB_FAILED, WORKER_STOPPED)

See `queue.md` for job creation, worker management, and resilience patterns.

## Event System Integration

CI4 `Events` class provides framework-wide publish/subscribe. Domain events are pure PHP.

**Bridge pattern:**
1. Domain aggregate collects events via `releaseEvents()`
2. Application layer dispatches via domain `EventDispatcherInterface` port
3. Infrastructure `CIEventDispatcher` adapter bridges to `Events::trigger()`
4. Listeners in `app/Config/Events.php` handle side effects (notifications, projections, queue push)

See `event-system.md` for priority system, lifecycle events, and testing patterns.

## Keeping Domain Pure — Extended Summary

| DDD Aspect | CI4 Component | Integration Pattern |
|------------|--------------|---------------------|
| Persistence | CI4 Model / Query Builder | Infrastructure repository + mapper |
| Domain Events | CI4 Events | Domain port + CIEventDispatcher adapter |
| Auth Identity | Shield UserIdentity | Infrastructure ShieldUserProvider |
| Authorization | Shield Groups/Permissions | Filter delegates to domain Specifications |
| Queue/Jobs | codeigniter4/queue | Infrastructure listeners push; handlers call UseCases |
| Caching | Cache service (Redis/File) | Domain port + CIOrderCache adapter |
| HTTP Client | CURLRequest | Domain port + Infrastructure adapter |
| Rate Limiting | Throttler | Presentation Filter only |

## Migration Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Create Domain entity (pure PHP) | No `use CodeIgniter\` |
| 2 | Extract repository interface to Domain | Interface in Domain namespace |
| 3 | Create CI4 Model in Infrastructure | Extends `CodeIgniter\Model` |
| 4 | Implement repository with CI4 Model | Maps Model data to Domain entity |
| 5 | Wire via Config\Services | `Services::orderRepository()` binding |
| 6 | Dispatch domain events | Via domain EventDispatcherInterface port |
| 7 | Replace direct Model usage in controllers | Use UseCase instead |
| 8 | Separate auth identity | Infrastructure ShieldUserProvider |
| 9 | Implement infrastructure ports | Cache, HTTP Client, Email adapters |
