# Compensating Transaction Strategies

## Overview

Compensating transactions are the "undo" operations for saga steps. They restore the system to a consistent state when a saga fails.

## Key Principles

### 1. Semantic Compensation (Not Rollback)

Compensations perform a **semantic undo**, not a database rollback.

```php
// ❌ WRONG: Trying to rollback
public function compensate(SagaContext $context): StepResult
{
    $this->database->rollback(); // Can't rollback committed transaction!
}

// ✅ CORRECT: Semantic undo
public function compensate(SagaContext $context): StepResult
{
    // Create a refund (new transaction that reverses the effect)
    $this->payments->refund(
        originalPaymentId: $context->get('payment_id'),
        amount: $context->get('charged_amount'),
        reason: 'Saga compensation'
    );

    return StepResult::success();
}
```

### 2. Idempotent Compensations

Compensations must be safely re-runnable.

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

final readonly class ReleaseInventoryCompensation
{
    public function execute(SagaContext $context): StepResult
    {
        $reservationId = $context->get('reservation_id');

        // Check if already released (idempotent)
        if ($this->inventory->isReleased($reservationId)) {
            return StepResult::success();
        }

        try {
            $this->inventory->release($reservationId);
            return StepResult::success();
        } catch (ReservationNotFoundException $e) {
            // Already released or never existed - that's OK
            return StepResult::success();
        }
    }
}
```

### 3. Store Compensation Data

Store all data needed for compensation during forward execution.

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

final readonly class ChargePaymentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        $result = $this->payments->charge(
            customerId: $context->get('customer_id'),
            amount: $context->get('total_amount'),
            currency: $context->get('currency')
        );

        // Store everything needed for refund
        $context->set('payment_id', $result->paymentId);
        $context->set('charged_amount', $result->chargedAmount);
        $context->set('payment_method', $result->paymentMethod);
        $context->set('transaction_reference', $result->transactionReference);

        return StepResult::success();
    }

    public function compensate(SagaContext $context): StepResult
    {
        // All data available from context
        $this->payments->refund(
            paymentId: $context->get('payment_id'),
            amount: $context->get('charged_amount'),
            transactionReference: $context->get('transaction_reference')
        );

        return StepResult::success();
    }
}
```

## Compensation Strategies

### Strategy 1: Simple Reversal

Direct opposite operation.

| Forward Action | Compensation |
|----------------|--------------|
| Create order | Cancel order |
| Reserve inventory | Release inventory |
| Charge payment | Refund payment |
| Create shipment | Cancel shipment |

```php
// Forward
$this->inventory->reserve($items);

// Compensation
$this->inventory->release($reservationId);
```

### Strategy 2: Counter-Transaction

Create a new transaction that negates the effect.

```php
<?php

// Forward: Debit account
$this->accounting->debit($accountId, $amount);
$context->set('debit_transaction_id', $transactionId);

// Compensation: Credit account (new transaction)
$this->accounting->credit(
    $accountId,
    $amount,
    reference: "Compensation for {$context->get('debit_transaction_id')}"
);
```

### Strategy 3: State Transition

Move entity to compensated state.

```php
<?php

declare(strict_types=1);

namespace Domain\Order;

enum OrderStatus: string
{
    case Created = 'created';
    case Confirmed = 'confirmed';
    case Cancelled = 'cancelled';
    case CompensationCancelled = 'compensation_cancelled'; // Special status

    public function canCompensate(): bool
    {
        return in_array($this, [self::Created, self::Confirmed], true);
    }
}

final class Order
{
    public function compensateCancel(string $reason): void
    {
        if (!$this->status->canCompensate()) {
            throw new CannotCompensateException($this->id, $this->status);
        }

        $this->status = OrderStatus::CompensationCancelled;
        $this->compensationReason = $reason;
        $this->compensatedAt = new \DateTimeImmutable();
    }
}
```

### Strategy 4: Soft Delete with Reason

Mark as deleted with compensation context.

```php
<?php

final readonly class CancelReservationCompensation
{
    public function execute(SagaContext $context): StepResult
    {
        $reservation = $this->reservations->findById(
            $context->get('reservation_id')
        );

        // Soft delete with compensation metadata
        $reservation->cancel(
            reason: CompensationReason::SagaFailed,
            sagaId: $context->sagaId,
            compensatedAt: new \DateTimeImmutable()
        );

        $this->reservations->save($reservation);

        return StepResult::success();
    }
}
```

## Partial Completion Handling

When a step partially succeeds, compensation must handle partial state.

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

final readonly class CreateShipmentStep implements SagaStepInterface
{
    public function execute(SagaContext $context): StepResult
    {
        $createdShipments = [];

        try {
            foreach ($context->get('items') as $item) {
                $shipment = $this->shipping->createShipment($item);
                $createdShipments[] = $shipment->id;
            }

            $context->set('shipment_ids', $createdShipments);
            return StepResult::success();

        } catch (\Throwable $e) {
            // Store partial progress for compensation
            $context->set('partial_shipment_ids', $createdShipments);
            return StepResult::failure($e->getMessage());
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        // Handle both complete and partial execution
        $shipmentIds = $context->get('shipment_ids')
            ?? $context->get('partial_shipment_ids')
            ?? [];

        foreach ($shipmentIds as $id) {
            try {
                $this->shipping->cancel($id);
            } catch (ShipmentNotFoundException $e) {
                // Already cancelled or never created - OK
                continue;
            }
        }

        return StepResult::success();
    }
}
```

## Compensation Failure Handling

What to do when compensation itself fails.

### Strategy 1: Retry with Backoff

```php
<?php

final readonly class RetryingCompensation
{
    private const MAX_RETRIES = 5;

    public function compensate(SagaContext $context): StepResult
    {
        $retries = 0;
        $lastError = null;

        while ($retries < self::MAX_RETRIES) {
            try {
                $this->doCompensate($context);
                return StepResult::success();
            } catch (\Throwable $e) {
                $lastError = $e;
                $retries++;
                usleep($this->backoff($retries));
            }
        }

        return StepResult::failure("Compensation failed after {$retries} retries: {$lastError->getMessage()}");
    }

    private function backoff(int $attempt): int
    {
        return (int) (100000 * pow(2, $attempt)); // Exponential backoff in microseconds
    }
}
```

### Strategy 2: Manual Intervention Queue

```php
<?php

final readonly class ManualInterventionHandler
{
    public function handleCompensationFailure(
        string $sagaId,
        string $stepName,
        SagaContext $context,
        \Throwable $error
    ): void {
        $this->interventionQueue->add(
            new ManualIntervention(
                sagaId: $sagaId,
                stepName: $stepName,
                context: $context->all(),
                error: $error->getMessage(),
                requiredAction: 'manual_compensation',
                priority: Priority::Critical,
                createdAt: new \DateTimeImmutable()
            )
        );

        $this->alerting->sendAlert(
            'Saga compensation requires manual intervention',
            [
                'saga_id' => $sagaId,
                'step' => $stepName,
                'error' => $error->getMessage(),
            ]
        );
    }
}
```

### Strategy 3: Dead Letter Saga

```php
<?php

final readonly class DeadLetterSagaHandler
{
    public function move(string $sagaId, SagaContext $context, string $error): void
    {
        $this->deadLetterRepository->store(
            new DeadLetterSaga(
                originalSagaId: $sagaId,
                context: json_encode($context->all()),
                error: $error,
                compensationState: 'failed',
                createdAt: new \DateTimeImmutable()
            )
        );

        // Mark original saga
        $this->sagaPersistence->markAsDeadLettered($sagaId);
    }
}
```

## Testing Compensations

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Saga;

use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ReleaseInventoryStep::class)]
final class ReleaseInventoryStepTest extends TestCase
{
    public function testCompensateReleasesReservation(): void
    {
        $context = new SagaContext('saga-1', 'order-123', new \DateTimeImmutable());
        $context->set('reservation_id', 'res-456');

        $inventory = $this->createMock(InventoryServiceInterface::class);
        $inventory->expects($this->once())
            ->method('release')
            ->with('res-456');

        $step = new ReleaseInventoryStep($inventory);
        $result = $step->compensate($context);

        $this->assertTrue($result->isSuccess());
    }

    public function testCompensateIsIdempotent(): void
    {
        $context = new SagaContext('saga-1', 'order-123', new \DateTimeImmutable());
        $context->set('reservation_id', 'res-456');

        $inventory = $this->createMock(InventoryServiceInterface::class);
        $inventory->method('isReleased')->willReturn(true);
        $inventory->expects($this->never())->method('release');

        $step = new ReleaseInventoryStep($inventory);
        $result = $step->compensate($context);

        $this->assertTrue($result->isSuccess());
    }
}
```
