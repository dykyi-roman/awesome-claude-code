# Symfony Workflow and State Machine

Aggregate lifecycle management using Symfony Workflow component with DDD-aligned guards and transitions.

## Workflow vs StateMachine

| Feature | Workflow | StateMachine |
|---------|----------|--------------|
| Places | Can be in multiple places simultaneously | Exactly one place at a time |
| Transitions | Can move between any connected places | Single-source to single-target |
| Use Case | Parallel processes (review + approval) | Sequential lifecycle (order status) |
| DDD Mapping | Complex multi-track processes | Aggregate status lifecycle |

**Detection:**
```bash
# Workflow usage in project
Grep: "WorkflowInterface|StateMachineInterface" --glob "src/**/*.php"
Grep: "framework:\\s*workflows:" --glob "**/config/**/*.yaml" --multiline true

# Hard-coded status transitions (should use Workflow)
Grep: "if.*->getStatus\\(\\).*===|switch.*->status" --glob "**/Domain/**/*.php"
Grep: "->setStatus\\(" --glob "src/**/*.php"
```

**Bad — hard-coded status management:**
```php
<?php

declare(strict_types=1);

namespace Entity;

// VIOLATION: Manual state machine with string statuses
class Order
{
    private string $status = 'draft';

    public function confirm(): void
    {
        if ($this->status !== 'draft') {
            throw new \RuntimeException('Can only confirm draft orders');
        }
        $this->status = 'confirmed';
    }

    public function ship(): void
    {
        if ($this->status !== 'confirmed' && $this->status !== 'paid') {
            throw new \RuntimeException('Invalid status for shipping');
        }
        $this->status = 'shipped';
    }
}
```

## YAML Configuration

```yaml
# config/packages/workflow.yaml
framework:
    workflows:
        order:
            type: state_machine
            audit_trail:
                enabled: true
            marking_store:
                type: method
                property: status
            supports:
                - App\Order\Domain\Entity\Order
            initial_marking: draft
            places:
                - draft
                - confirmed
                - paid
                - shipped
                - delivered
                - cancelled
            transitions:
                confirm:
                    from: draft
                    to: confirmed
                pay:
                    from: confirmed
                    to: paid
                ship:
                    from: [confirmed, paid]
                    to: shipped
                deliver:
                    from: shipped
                    to: delivered
                cancel:
                    from: [draft, confirmed]
                    to: cancelled
```

## Enum-Based Type-Safe Places

Use PHP 8.4 enums instead of strings for compile-time safety.

**Good — enum-backed places:**
```php
<?php

declare(strict_types=1);

namespace ValueObject;

enum OrderStatus: string
{
    case Draft = 'draft';
    case Confirmed = 'confirmed';
    case Paid = 'paid';
    case Shipped = 'shipped';
    case Delivered = 'delivered';
    case Cancelled = 'cancelled';

    public function canTransitionTo(self $target): bool
    {
        return match ($this) {
            self::Draft => in_array($target, [self::Confirmed, self::Cancelled], true),
            self::Confirmed => in_array($target, [self::Paid, self::Shipped, self::Cancelled], true),
            self::Paid => $target === self::Shipped,
            self::Shipped => $target === self::Delivered,
            self::Delivered, self::Cancelled => false,
        };
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Entity;

use ValueObject\OrderStatus;

final class Order
{
    private OrderStatus $status;

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function status(): OrderStatus
    {
        return $this->status;
    }

    // Workflow component calls this via marking_store
    public function getStatus(): string
    {
        return $this->status->value;
    }

    public function setStatus(string $status): void
    {
        $this->status = OrderStatus::from($status);
    }
}
```

## GuardEvent for Business Rules

Guards validate whether a transition is allowed. DDD approach: delegate to domain Specifications.

**Bad — business logic in guard listener:**
```php
<?php

declare(strict_types=1);

namespace Workflow;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Workflow\Event\GuardEvent;

#[AsEventListener(event: 'workflow.order.guard.ship')]
final class ShipGuardListener
{
    // VIOLATION: Business logic in infrastructure listener
    public function __invoke(GuardEvent $event): void
    {
        $order = $event->getSubject();

        if ($order->getTotal() <= 0) {
            $event->setBlocked(true, 'Order total must be positive');
        }

        if (count($order->getItems()) === 0) {
            $event->setBlocked(true, 'Order must have items');
        }
    }
}
```

**Good — guard delegates to domain Specification:**
```php
<?php

declare(strict_types=1);

namespace Workflow;

use Specification\CanShipOrderSpecification;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Workflow\Event\GuardEvent;

#[AsEventListener(event: 'workflow.order.guard.ship')]
final readonly class ShipGuardListener
{
    public function __construct(
        private CanShipOrderSpecification $specification,
    ) {}

    public function __invoke(GuardEvent $event): void
    {
        /** @var \App\Order\Domain\Entity\Order $order */
        $order = $event->getSubject();

        if (!$this->specification->isSatisfiedBy($order)) {
            $event->setBlocked(true, $this->specification->failureReason($order));
        }
    }
}
```

## Transition Events Lifecycle

Events fire in this order for each transition:

```
guard          → Can this transition happen?
leave          → Leaving current place(s)
transition     → The transition is happening
enter          → Entering new place(s)
entered        → Fully entered new place(s)
completed      → Transition fully completed
announce       → Announce available transitions from new place
```

**Dispatching domain events on transition completion:**
```php
<?php

declare(strict_types=1);

namespace Workflow;

use Event\OrderShippedEvent;
use Domain\EventDispatcherInterface;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Workflow\Event\CompletedEvent;

#[AsEventListener(event: 'workflow.order.completed.ship')]
final readonly class OrderShippedListener
{
    public function __construct(
        private EventDispatcherInterface $domainEvents,
    ) {}

    public function __invoke(CompletedEvent $event): void
    {
        /** @var \App\Order\Domain\Entity\Order $order */
        $order = $event->getSubject();

        $this->domainEvents->dispatch(
            new OrderShippedEvent($order->id()),
        );
    }
}
```

## MarkingStore for Aggregate State

The marking store maps Workflow places to aggregate properties.

| Store Type | Method | DDD Alignment |
|------------|--------|---------------|
| `method` | Calls getter/setter on entity | Use enum-backed `getStatus()/setStatus()` |
| `property` (deprecated) | Direct property access | Avoid — breaks encapsulation |

```yaml
# Recommended: method-based marking store
marking_store:
    type: method
    property: status   # calls getStatus() / setStatus()
```

## Aggregate Lifecycle as Workflow

Complete Order lifecycle example with DDD integration:

```
    ┌─────────┐
    │  draft  │
    └────┬────┘
         │ confirm
    ┌────▼────┐
    │confirmed│──────────┐
    └────┬────┘          │
         │ pay           │ cancel
    ┌────▼────┐    ┌─────▼────┐
    │  paid   │    │cancelled │
    └────┬────┘    └──────────┘
         │ ship
    ┌────▼────┐
    │ shipped │
    └────┬────┘
         │ deliver
    ┌────▼────┐
    │delivered│
    └─────────┘
```

**Using Workflow in Application layer:**
```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use Symfony\Component\Workflow\WorkflowInterface;

final readonly class ShipOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private WorkflowInterface $orderStateMachine,
    ) {}

    public function execute(ShipOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        // Workflow validates guards and applies transition
        $this->orderStateMachine->apply($order, 'ship');

        $this->orders->save($order);
    }
}
```

## Audit Trail

Enable audit trail for tracing all transitions in event store or logs.

```yaml
framework:
    workflows:
        order:
            audit_trail:
                enabled: true   # Logs all transitions via LoggerInterface
```

**Custom audit trail for event store persistence:**
```php
<?php

declare(strict_types=1);

namespace Workflow;

use EventStore\EventStoreInterface;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Workflow\Event\CompletedEvent;

#[AsEventListener(event: 'workflow.order.completed')]
final readonly class WorkflowAuditTrailListener
{
    public function __construct(
        private EventStoreInterface $eventStore,
    ) {}

    public function __invoke(CompletedEvent $event): void
    {
        $this->eventStore->append(
            streamName: 'order-' . $event->getSubject()->id()->value,
            event: new WorkflowTransitionRecordedEvent(
                aggregateId: $event->getSubject()->id()->value,
                transition: $event->getTransition()->getName(),
                from: $event->getTransition()->getFroms(),
                to: $event->getTransition()->getTos(),
                occurredAt: new \DateTimeImmutable(),
            ),
        );
    }
}
```

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Type | StateMachine for aggregate lifecycle, Workflow for parallel tracks |
| Places | Enum-backed values (not raw strings) |
| Guards | Delegate to domain Specifications via listener |
| Transitions | YAML config in Infrastructure; domain remains pure |
| Events | `completed` listeners dispatch domain events |
| MarkingStore | `method` type with `getStatus()/setStatus()` |
| Audit Trail | Enable + persist to event store for traceability |
| Status Checks | Use `$workflow->can($entity, 'transition')` instead of manual checks |
