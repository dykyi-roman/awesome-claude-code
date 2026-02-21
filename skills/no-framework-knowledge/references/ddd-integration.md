# DDD Integration in No-Framework PHP

Maximum domain freedom: building a pure Domain layer without any framework constraints.

## Why No-Framework Excels for DDD

In a no-framework project, the Domain layer is pure by default. There is no framework ORM leaking annotations into entities, no base classes to extend, and no service container magic obscuring dependencies. Every domain object is plain PHP.

## Detection Patterns

```bash
# Domain layer must have zero external use statements
Grep: "use Doctrine\\\\|use Illuminate\\\\|use Symfony\\\\" --glob "**/Domain/**/*.php"

# Domain must not import Infrastructure or Presentation
Grep: "use Infrastructure\\\\|use Presentation\\\\" --glob "**/Domain/**/*.php"

# Entities should have behavior (not just getters/setters)
Grep: "public function set[A-Z]" --glob "**/Domain/**/Entity/**/*.php"

# Value Objects should be readonly
Grep: "^final readonly class" --glob "**/Domain/**/ValueObject/**/*.php"

# Repository interfaces must be in Domain
Grep: "interface.*RepositoryInterface" --glob "**/Domain/**/*.php"

# Repository implementations must be in Infrastructure
Grep: "implements.*RepositoryInterface" --glob "**/Infrastructure/**/*.php"

# Domain Events should exist
Grep: "class.*Event" --glob "**/Domain/**/Event/**/*.php"
```

## Value Objects (Pure PHP)

**Good — immutable, self-validating:**

```php
declare(strict_types=1);

namespace Domain\Order\ValueObject;

use Domain\Order\Exception\InvalidMoneyException;

final readonly class Money
{
    public function __construct(
        public int $cents,
        public Currency $currency,
    ) {
        if ($cents < 0) {
            throw new InvalidMoneyException('Amount cannot be negative');
        }
    }

    public function add(self $other): self
    {
        if (!$this->currency->equals($other->currency)) {
            throw new InvalidMoneyException('Cannot add different currencies');
        }

        return new self($this->cents + $other->cents, $this->currency);
    }

    public function isGreaterThan(self $other): bool
    {
        return $this->cents > $other->cents;
    }

    public function equals(self $other): bool
    {
        return $this->cents === $other->cents
            && $this->currency->equals($other->currency);
    }
}
```

**Bad — mutable, no validation:**

```php
class Money
{
    public int $amount;     // Public mutable property
    public string $currency; // String instead of VO

    public function setAmount(int $amount): void  // Setter = mutable
    {
        $this->amount = $amount;
    }
}
```

## Entities with Behavior

**Good — rich domain model with state transitions:**

```php
declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\Event\OrderConfirmedEvent;
use Domain\Order\Event\OrderLineAddedEvent;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderLine;
use Domain\Order\ValueObject\Money;
use Domain\Order\Exception\InvalidStateTransitionException;

final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    /** @var array<object> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function addLine(ProductId $productId, int $quantity, Money $price): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException('Cannot modify confirmed order');
        }

        $line = new OrderLine($productId, $quantity, $price);
        $this->lines[] = $line;
        $this->events[] = new OrderLineAddedEvent($this->id, $line);
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException('Only draft orders can be confirmed');
        }

        if ($this->lines === []) {
            throw new InvalidStateTransitionException('Cannot confirm empty order');
        }

        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id, $this->total());
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            static fn(Money $carry, OrderLine $line): Money => $carry->add($line->subtotal()),
            Money::zero($this->lines[0]->price->currency),
        );
    }

    /** @return array<object> */
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

## Domain Events (Custom Dispatcher)

**Event interface and implementation:**

```php
declare(strict_types=1);

namespace Domain\Shared\Event;

interface DomainEventInterface
{
    public function occurredAt(): \DateTimeImmutable;
}
```

```php
declare(strict_types=1);

namespace Domain\Order\Event;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\Money;
use Domain\Shared\Event\DomainEventInterface;

final readonly class OrderConfirmedEvent implements DomainEventInterface
{
    private \DateTimeImmutable $occurredAt;

    public function __construct(
        public OrderId $orderId,
        public Money $total,
    ) {
        $this->occurredAt = new \DateTimeImmutable();
    }

    public function occurredAt(): \DateTimeImmutable
    {
        return $this->occurredAt;
    }
}
```

**Custom event dispatcher (Infrastructure):**

```php
declare(strict_types=1);

namespace Infrastructure\EventDispatcher;

use Domain\Shared\Event\DomainEventInterface;
use Domain\Shared\Event\EventDispatcherInterface;

final class InMemoryEventDispatcher implements EventDispatcherInterface
{
    /** @var array<class-string, array<callable>> */
    private array $listeners = [];

    public function subscribe(string $eventClass, callable $listener): void
    {
        $this->listeners[$eventClass][] = $listener;
    }

    public function dispatch(DomainEventInterface $event): void
    {
        $eventClass = $event::class;

        foreach ($this->listeners[$eventClass] ?? [] as $listener) {
            $listener($event);
        }
    }
}
```

## Repository Interfaces (Domain)

```php
declare(strict_types=1);

namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    public function save(Order $order): void;

    public function delete(OrderId $id): void;

    /** @return array<Order> */
    public function findByCustomer(CustomerId $customerId): array;
}
```

## Aggregate Root Pattern

```php
declare(strict_types=1);

namespace Domain\Shared\Entity;

use Domain\Shared\Event\DomainEventInterface;

abstract class AggregateRoot
{
    /** @var array<DomainEventInterface> */
    private array $domainEvents = [];

    protected function recordEvent(DomainEventInterface $event): void
    {
        $this->domainEvents[] = $event;
    }

    /** @return array<DomainEventInterface> */
    public function releaseEvents(): array
    {
        $events = $this->domainEvents;
        $this->domainEvents = [];

        return $events;
    }
}
```

## Security in DDD Context

Authentication and authorization are Infrastructure/Presentation concerns. Domain defines pure `User` aggregate with domain roles (enum).

**Key patterns:**
- Domain `User` entity stays pure PHP — no JWT library, no `UserInterface`
- Infrastructure `JwtTokenGenerator` implements domain `TokenGeneratorInterface` port
- RBAC middleware at Presentation layer; Domain uses Specifications for business rules
- Password hashing uses a domain `PasswordHasherInterface` port with `NativePasswordHasher` adapter

See `security.md` for full implementation with JWT, RBAC middleware, CSRF, and security headers.

## Queue Integration

Queue producers and consumers are Infrastructure concerns. Domain events are pure PHP — dispatched by Application layer, then Infrastructure listeners push to the queue.

**Key patterns:**
- Job handlers delegate to Application UseCases
- Worker includes `pcntl_signal` for graceful shutdown (SIGTERM/SIGINT)
- Retry logic via reject + requeue with max attempts
- Supervisor manages worker processes in production
- Domain never imports `enqueue/*` or `php-amqplib/*`

See `queue.md` for producer/consumer setup, job dispatcher, and supervisor configuration.

## Event System Integration

No-framework projects can use PSR-14 (`league/event`) or custom `InMemoryEventDispatcher`.

**Bridge pattern:**
1. Domain aggregate collects events via `AggregateRoot::recordEvent()`
2. Application layer dispatches via domain `EventDispatcherInterface` port
3. Infrastructure `PsrEventDispatcherAdapter` bridges to `league/event` (or InMemory)
4. Listeners in config handle side effects (notifications, projections, queue push)
5. Async events via `AsyncEventDispatcher` decorator routing to queue

See `event-system.md` for PSR-14 setup, custom dispatcher, async processing, and testing.

## Keeping Domain Pure — Extended Summary

| DDD Aspect | Standalone Package | Integration Pattern |
|------------|--------------------|---------------------|
| Persistence | Doctrine ORM / Cycle ORM / PDO | Infrastructure repository + mapper |
| Domain Events | Pure PHP / PSR-14 | Domain port + InMemory or PSR-14 adapter |
| Auth Identity | `lcobucci/jwt` | Infrastructure JwtTokenGenerator adapter |
| Authorization | Custom RBAC middleware | PSR-15 middleware delegates to domain Specifications |
| Queue/Jobs | `enqueue/enqueue` / `php-amqplib` | Infrastructure producer + worker; handlers call UseCases |
| Caching | `symfony/cache` (standalone PSR-6/16) | Domain port + PSR-16 adapter |
| HTTP Client | `guzzlehttp/guzzle` (PSR-18) | Domain port + Infrastructure adapter |
| Mailer | `symfony/mailer` (standalone) | Domain NotificationSenderInterface port + adapter |
| Rate Limiting | Custom token bucket + PSR-16 cache | PSR-15 middleware only |

## Migration Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Create Domain entity (pure PHP) | No external `use` statements |
| 2 | Extract repository interface to Domain | Interface in Domain namespace |
| 3 | Implement repository with Doctrine/PDO | In Infrastructure namespace |
| 4 | Wire via DI container (PHP-DI/League) | PSR-11 container config |
| 5 | Dispatch domain events via port | Via domain EventDispatcherInterface |
| 6 | Replace direct dependencies in Use Cases | All via constructor injection |
| 7 | Separate auth identity | Infrastructure JwtTokenGenerator |
| 8 | Implement infrastructure ports | Cache, HTTP Client, Mailer adapters |
| 9 | Add queue integration | Infrastructure producer + worker |

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| External dependency in Domain layer | Critical | Architecture purity |
| Anemic entity (only getters/setters) | Critical | Domain model quality |
| Missing Value Objects for concepts | Warning | Encapsulation |
| No Domain Events | Warning | Decoupling |
| Repository interface in Infrastructure | Warning | Dependency direction |
| Mutable Value Objects | Warning | Data integrity |
