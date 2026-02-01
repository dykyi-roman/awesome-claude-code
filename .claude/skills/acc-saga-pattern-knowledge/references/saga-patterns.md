# Saga Implementation Patterns

## Overview

Sagas manage distributed transactions by breaking them into a sequence of local transactions, each with a compensating action to undo its effects if the overall saga fails.

## Choreography Pattern

Services communicate via events. Each service listens for events and publishes new ones.

### Event Flow Example

```
OrderService                 InventoryService              PaymentService
     │                             │                            │
     │ OrderCreated ──────────────▶│                            │
     │                             │ InventoryReserved ────────▶│
     │                             │                            │ PaymentCharged
     │◀──────────────────────────────────────────────────────────│
     │                             │                            │
     │ OrderConfirmed              │                            │
```

### PHP Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

use Domain\Inventory\Event\InventoryReserved;
use Domain\Inventory\Event\InventoryReservationFailed;
use Domain\Order\OrderRepositoryInterface;
use Domain\Order\OrderStatus;

final readonly class HandleInventoryReservationResult
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private PaymentServiceInterface $payments
    ) {}

    public function onReserved(InventoryReserved $event): void
    {
        $order = $this->orders->findById($event->orderId);

        // Proceed to next step
        $this->payments->charge(
            orderId: $event->orderId,
            amount: $order->total(),
            correlationId: $event->correlationId
        );
    }

    public function onFailed(InventoryReservationFailed $event): void
    {
        $order = $this->orders->findById($event->orderId);
        $order->markAsFailed($event->reason);
        $this->orders->save($order);
    }
}
```

### Choreography Pros/Cons

**Pros:**
- Loose coupling between services
- Simple services (each handles its own logic)
- No single point of failure

**Cons:**
- Hard to understand the overall flow
- Difficult to test end-to-end
- Cyclic dependencies possible
- Harder to add new steps

## Orchestration Pattern

A central orchestrator manages the saga execution.

### PHP Orchestrator Example

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga;

use Application\Shared\Saga\SagaOrchestrator;
use Domain\Shared\Saga\SagaContext;

final readonly class OrderSagaFactory
{
    public function __construct(
        private ReserveInventoryStep $reserveStep,
        private ChargePaymentStep $chargeStep,
        private CreateShipmentStep $shipStep,
        private SagaPersistenceInterface $persistence
    ) {}

    public function create(string $orderId, string $customerId): SagaOrchestrator
    {
        $context = new SagaContext(
            sagaId: "order-saga-{$orderId}",
            correlationId: $orderId,
            startedAt: new \DateTimeImmutable()
        );

        $context->set('order_id', $orderId);
        $context->set('customer_id', $customerId);

        return (new SagaOrchestrator($context, $this->persistence))
            ->addStep($this->reserveStep)
            ->addStep($this->chargeStep)
            ->addStep($this->shipStep);
    }
}
```

### Step Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaStepInterface;
use Domain\Shared\Saga\StepResult;

final readonly class ReserveInventoryStep implements SagaStepInterface
{
    public function __construct(
        private InventoryServiceInterface $inventory
    ) {}

    public function name(): string
    {
        return 'reserve_inventory';
    }

    public function execute(SagaContext $context): StepResult
    {
        try {
            $reservationId = $this->inventory->reserve(
                orderId: $context->get('order_id'),
                items: $context->get('items')
            );

            $context->set('reservation_id', $reservationId);

            return StepResult::success();
        } catch (InsufficientStockException $e) {
            return StepResult::failure($e->getMessage());
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        try {
            $this->inventory->release(
                reservationId: $context->get('reservation_id')
            );

            return StepResult::success();
        } catch (\Throwable $e) {
            return StepResult::failure($e->getMessage());
        }
    }

    public function isIdempotent(): bool
    {
        return true;
    }
}
```

### Orchestration Pros/Cons

**Pros:**
- Clear transaction flow
- Easy to understand and maintain
- Simpler testing
- Easy to add/modify steps

**Cons:**
- Single point of failure (orchestrator)
- Orchestrator can become complex
- Tighter coupling to orchestrator

## State Machine Approach

Use explicit state machine for saga lifecycle.

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

enum SagaState: string
{
    case Created = 'created';
    case InventoryReserving = 'inventory_reserving';
    case InventoryReserved = 'inventory_reserved';
    case PaymentCharging = 'payment_charging';
    case PaymentCharged = 'payment_charged';
    case ShipmentCreating = 'shipment_creating';
    case Completed = 'completed';
    case Compensating = 'compensating';
    case Failed = 'failed';

    public function nextStep(): ?self
    {
        return match ($this) {
            self::Created => self::InventoryReserving,
            self::InventoryReserved => self::PaymentCharging,
            self::PaymentCharged => self::ShipmentCreating,
            self::ShipmentCreating => self::Completed,
            default => null,
        };
    }

    public function previousStep(): ?self
    {
        return match ($this) {
            self::PaymentCharged => self::InventoryReserved,
            self::InventoryReserved => self::Created,
            default => null,
        };
    }
}
```

## Parallel Steps

Execute independent steps concurrently.

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

final class ParallelSagaStep implements SagaStepInterface
{
    /** @param array<SagaStepInterface> $steps */
    public function __construct(
        private array $steps
    ) {}

    public function name(): string
    {
        return 'parallel_' . implode('_', array_map(
            fn($s) => $s->name(),
            $this->steps
        ));
    }

    public function execute(SagaContext $context): StepResult
    {
        $results = [];

        // In production, use async/parallel execution
        foreach ($this->steps as $step) {
            $result = $step->execute($context);

            if ($result->isFailure()) {
                // Compensate already executed steps
                $this->compensateCompleted($context, $results);
                return $result;
            }

            $results[] = ['step' => $step, 'result' => $result];
        }

        return StepResult::success();
    }

    public function compensate(SagaContext $context): StepResult
    {
        foreach (array_reverse($this->steps) as $step) {
            $result = $step->compensate($context);
            if ($result->isFailure()) {
                return $result;
            }
        }
        return StepResult::success();
    }

    private function compensateCompleted(SagaContext $context, array $completed): void
    {
        foreach (array_reverse($completed) as $item) {
            $item['step']->compensate($context);
        }
    }

    public function isIdempotent(): bool
    {
        return array_reduce(
            $this->steps,
            fn($carry, $step) => $carry && $step->isIdempotent(),
            true
        );
    }
}
```

## Saga Persistence

### Database Schema

```sql
CREATE TABLE sagas (
    id VARCHAR(255) PRIMARY KEY,
    type VARCHAR(255) NOT NULL,
    state VARCHAR(50) NOT NULL,
    context JSONB NOT NULL,
    completed_steps JSONB NOT NULL DEFAULT '[]',
    current_step VARCHAR(255),
    error TEXT,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    INDEX idx_state (state),
    INDEX idx_type_state (type, state)
);

CREATE TABLE saga_steps_log (
    id UUID PRIMARY KEY,
    saga_id VARCHAR(255) NOT NULL REFERENCES sagas(id),
    step_name VARCHAR(255) NOT NULL,
    action VARCHAR(20) NOT NULL, -- 'execute' or 'compensate'
    status VARCHAR(20) NOT NULL, -- 'success' or 'failure'
    error TEXT,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    INDEX idx_saga (saga_id)
);
```

### Repository Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Saga;

use Domain\Shared\Saga\SagaState;

final readonly class DoctrineSagaPersistence implements SagaPersistenceInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function save(
        string $sagaId,
        SagaState $state,
        array $completedSteps,
        ?string $error = null
    ): void {
        $this->connection->executeStatement(
            'INSERT INTO sagas (id, state, completed_steps, error, updated_at)
             VALUES (:id, :state, :steps, :error, :now)
             ON CONFLICT (id) DO UPDATE SET
                state = :state,
                completed_steps = :steps,
                error = :error,
                updated_at = :now',
            [
                'id' => $sagaId,
                'state' => $state->value,
                'steps' => json_encode($completedSteps),
                'error' => $error,
                'now' => (new \DateTimeImmutable())->format('Y-m-d H:i:s'),
            ]
        );
    }

    public function findIncomplete(): array
    {
        return $this->connection->fetchAllAssociative(
            'SELECT * FROM sagas WHERE state NOT IN (:completed, :failed)',
            [
                'completed' => SagaState::Completed->value,
                'failed' => SagaState::Failed->value,
            ]
        );
    }
}
```

## Saga Recovery

Handle saga recovery after system restart.

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

final readonly class SagaRecoveryService
{
    public function __construct(
        private SagaPersistenceInterface $persistence,
        private SagaFactoryInterface $factory,
        private LoggerInterface $logger
    ) {}

    public function recoverIncompleteSagas(): void
    {
        $incomplete = $this->persistence->findIncomplete();

        foreach ($incomplete as $sagaData) {
            try {
                $saga = $this->factory->reconstruct($sagaData);

                if ($sagaData['state'] === SagaState::Compensating->value) {
                    $saga->continueCompensation();
                } else {
                    $saga->resume();
                }
            } catch (\Throwable $e) {
                $this->logger->error('Saga recovery failed', [
                    'saga_id' => $sagaData['id'],
                    'error' => $e->getMessage(),
                ]);
            }
        }
    }
}
```
