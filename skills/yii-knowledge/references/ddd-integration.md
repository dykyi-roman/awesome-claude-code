# DDD Integration with Yii3

Extracting Domain from Yii application, ActiveRecord to Repository migration, Domain Events, Value Objects, and keeping Domain pure.

## Extracting Domain from Yii Application

### Target Structure

```
src/
├── Domain/                          # Zero Yii dependencies
│   ├── Order/
│   │   ├── Entity/
│   │   │   └── Order.php
│   │   ├── ValueObject/
│   │   │   ├── OrderId.php
│   │   │   └── OrderStatus.php
│   │   ├── Repository/
│   │   │   └── OrderRepositoryInterface.php
│   │   ├── Event/
│   │   │   └── OrderCreated.php
│   │   └── Exception/
│   │       └── OrderNotFoundException.php
│   └── Shared/
│       └── ValueObject/
│           └── Money.php
├── Application/                     # UseCase orchestration
│   └── Order/
│       ├── UseCase/
│       │   └── CreateOrderUseCase.php
│       └── DTO/
│           ├── CreateOrderDTO.php
│           └── OrderResultDTO.php
└── Infrastructure/                  # Yii implementations
    └── Persistence/
        └── ActiveRecord/
            ├── OrderActiveRecord.php
            └── ActiveRecordOrderRepository.php
```

### Detection: Domain Purity

```bash
# Domain must have ZERO Yii imports
Grep: "use Yiisoft\\\\" --glob "**/Domain/**/*.php"

# Domain must have ZERO infrastructure imports
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"

# Application must not import Yii ActiveRecord
Grep: "use Yiisoft\\\\ActiveRecord" --glob "**/Application/**/*.php"
```

## ActiveRecord to Repository Pattern Migration

### Bad: ActiveRecord in Domain

```php
<?php

declare(strict_types=1);

namespace Entity;

use Yiisoft\ActiveRecord\ActiveRecord; // VIOLATION: Yii in Domain

final class Order extends ActiveRecord
{
    public function tableName(): string
    {
        return 'orders';
    }

    public function confirm(): void
    {
        $this->status = 'confirmed';
        $this->save(); // VIOLATION: Persistence in Domain
    }
}
```

### Good: Pure Domain Entity + Infrastructure ActiveRecord

```php
<?php

declare(strict_types=1);

namespace Entity;

use ValueObject\OrderId;
use ValueObject\OrderStatus;
use Event\OrderConfirmed;
use ValueObject\Money;

final class Order
{
    /** @var array<DomainEvent> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private OrderStatus $status,
        private Money $total,
    ) {}

    public static function create(OrderId $id, CustomerId $customerId, Money $total): self
    {
        $order = new self($id, $customerId, OrderStatus::Draft, $total);
        $order->events[] = new OrderCreated($id);

        return $order;
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotConfirmOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmed($this->id);
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];

        return $events;
    }

    public function id(): OrderId { return $this->id; }
    public function status(): OrderStatus { return $this->status; }
}
```

### Infrastructure: ActiveRecord + Repository

```php
<?php

declare(strict_types=1);

namespace Persistence\ActiveRecord;

use Yiisoft\ActiveRecord\ActiveRecord;

final class OrderActiveRecord extends ActiveRecord
{
    public function tableName(): string
    {
        return '{{%orders}}';
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Persistence\ActiveRecord;

use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;
use Yiisoft\ActiveRecord\ActiveQuery;

final readonly class ActiveRecordOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private ActiveQuery $orderQuery,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $record = $this->orderQuery
            ->where(['id' => $id->value])
            ->one();

        return $record !== null ? $this->toDomain($record) : null;
    }

    public function save(Order $order): void
    {
        $record = $this->orderQuery
            ->where(['id' => $order->id()->value])
            ->one() ?? new OrderActiveRecord();

        $record->setAttribute('id', $order->id()->value);
        $record->setAttribute('customer_id', $order->customerId()->value);
        $record->setAttribute('status', $order->status()->value);
        $record->setAttribute('total_cents', $order->total()->cents());
        $record->save();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }

    private function toDomain(OrderActiveRecord $record): Order
    {
        return new Order(
            id: new OrderId($record->getAttribute('id')),
            customerId: new CustomerId($record->getAttribute('customer_id')),
            status: OrderStatus::from($record->getAttribute('status')),
            total: Money::fromCents($record->getAttribute('total_cents')),
        );
    }
}
```

## Domain Events in Yii3

### Event Definition (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace Event;

use ValueObject\OrderId;

final readonly class OrderConfirmed
{
    public function __construct(
        public OrderId $orderId,
        public \DateTimeImmutable $occurredAt = new \DateTimeImmutable(),
    ) {}
}
```

### Event Dispatching via yiisoft/event-dispatcher

```php
<?php

declare(strict_types=1);

// config/common/di/events.php
use Yiisoft\EventDispatcher\Provider\ListenerCollection;

return [
    ListenerCollection::class => static function () {
        return (new ListenerCollection())
            ->add(static fn (OrderConfirmed $event) => /* handle */, OrderConfirmed::class)
            ->add(static fn (OrderCreated $event) => /* handle */, OrderCreated::class);
    },
];
```

## Value Objects Integration

```php
<?php

declare(strict_types=1);

namespace ValueObject;

final readonly class OrderId
{
    public function __construct(
        public string $value,
    ) {
        if (trim($value) === '') {
            throw new \InvalidArgumentException('OrderId cannot be empty');
        }
    }

    public static function generate(): self
    {
        return new self(Uuid::v4());
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

## Detection Patterns

```bash
# ActiveRecord leaking into Domain
Grep: "extends ActiveRecord" --glob "**/Domain/**/*.php"
Grep: "->save\(\)" --glob "**/Domain/**/*.php"

# Missing repository interface
Grep: "OrderRepositoryInterface" --glob "**/Domain/**/*.php" --output_mode count
# Should have at least one result

# Domain events not being dispatched
Grep: "releaseEvents" --glob "**/Application/**/*.php"
Grep: "dispatch.*Event" --glob "**/Application/**/*.php"

# Value Objects used correctly
Grep: "string \$id" --glob "**/Domain/**/*.php"
# Should be minimal — prefer OrderId over string
```

## Security in DDD Context

The Yii auth system (`IdentityInterface`) belongs in Infrastructure. Domain defines a pure `User` aggregate.

**Key patterns:**
- Domain `User` entity stays pure PHP — no `IdentityInterface`
- Infrastructure `SecurityIdentityAdapter` wraps Domain entity, implements `IdentityInterface`
- RBAC Rules delegate business logic to domain Specifications
- Password hashing uses a domain `PasswordHasherInterface` port

See `security.md` for full implementation details with RBAC, Rules, and authentication middleware.

## Advanced Queue Patterns

Queue messages and handlers are Infrastructure concerns. Domain events are pure PHP — dispatched by Application layer, then Infrastructure listeners push to queues.

**Key patterns:**
- **Failure middleware** (`FailureMiddlewareInterface`) for retry with exponential backoff
- **Push middleware** (`PushMiddlewareInterface`) for correlation IDs, metadata
- **Consume middleware** (`ConsumeMiddlewareInterface`) for logging, transaction wrapping
- **Channels** — one queue channel per bounded context

See `queue.md` for middleware pipelines, retry strategies, and DLQ patterns.

## Event System Integration

Yii3 `yiisoft/event-dispatcher` (PSR-14) serves infrastructure concerns. Domain events are pure PHP.

**Bridge pattern:**
1. Domain aggregate collects events via `releaseEvents()`
2. Application layer dispatches via domain `EventDispatcherInterface` port
3. Infrastructure `YiiEventDispatcherAdapter` bridges to PSR-14
4. Listeners in Infrastructure handle side effects (notifications, projections, queue push)

See `event-system.md` for PSR-14 details, CompositeProvider, and stoppable events.

## Keeping Domain Pure — Extended Summary

| DDD Aspect | Yii Component | Integration Pattern |
|------------|---------------|---------------------|
| Persistence | ActiveRecord / Cycle ORM | Infrastructure repository + mapper |
| Domain Events | yiisoft/event-dispatcher | Domain port + YiiEventDispatcherAdapter |
| Auth Identity | yiisoft/auth | Infrastructure SecurityIdentityAdapter |
| Authorization | yiisoft/rbac | Rules delegate to domain Specifications |
| Queue/Jobs | yiisoft/yii-queue | Infrastructure listeners push; handlers call UseCases |
| Caching | yiisoft/cache (PSR-16) | Domain port + PsrOrderCache adapter |
| HTTP Client | PSR-18 (Guzzle, etc.) | Domain port + Infrastructure adapter |
| Rate Limiting | yiisoft/rate-limiter | Presentation middleware only |

## Migration Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Create Domain entity (pure PHP) | No `use Yiisoft\` |
| 2 | Define Repository pattern in Domain | Repository lives with the domain (folder placement varies by architecture) |
| 3 | Create ActiveRecord model in Infrastructure | Extends `ActiveRecord` |
| 4 | Implement repository with ActiveRecord | Maps AR to Domain entity |
| 5 | Wire via DI config | `config/common/di/` binding |
| 6 | Dispatch domain events | Via domain EventDispatcherInterface port |
| 7 | Replace direct AR usage in controllers | Use UseCase instead |
| 8 | Separate auth identity | Infrastructure SecurityIdentityAdapter |
| 9 | Implement infrastructure ports | Cache, HTTP Client, Mailer adapters |
