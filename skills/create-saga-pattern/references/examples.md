# Saga Pattern Examples

## Order Saga Implementation

### ReserveInventoryStep

**File:** `src/Application/Order/Saga/Step/ReserveInventoryStep.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

use Application\Shared\Saga\AbstractSagaStep;
use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\StepResult;

final readonly class ReserveInventoryStep extends AbstractSagaStep
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
        $idempotencyKey = $this->idempotencyKey($context);

        $existing = $this->inventory->findReservationByKey($idempotencyKey);
        if ($existing !== null) {
            return StepResult::success(['reservation_id' => $existing->id]);
        }

        try {
            $reservation = $this->inventory->reserve(
                orderId: $context->get('order_id'),
                items: $context->get('items'),
                idempotencyKey: $idempotencyKey
            );

            return StepResult::success(['reservation_id' => $reservation->id]);
        } catch (InsufficientStockException $e) {
            return StepResult::failure("Insufficient stock: {$e->getMessage()}");
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        $reservationId = $context->get('reservation_id');

        if ($reservationId === null) {
            return StepResult::success();
        }

        try {
            $this->inventory->release($reservationId);
            return StepResult::success();
        } catch (ReservationNotFoundException) {
            return StepResult::success();
        }
    }
}
```

---

### ChargePaymentStep

**File:** `src/Application/Order/Saga/Step/ChargePaymentStep.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga\Step;

use Application\Shared\Saga\AbstractSagaStep;
use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\StepResult;

final readonly class ChargePaymentStep extends AbstractSagaStep
{
    public function __construct(
        private PaymentServiceInterface $payments
    ) {}

    public function name(): string
    {
        return 'charge_payment';
    }

    public function execute(SagaContext $context): StepResult
    {
        $idempotencyKey = $this->idempotencyKey($context);

        $existing = $this->payments->findByIdempotencyKey($idempotencyKey);
        if ($existing !== null) {
            return StepResult::success([
                'payment_id' => $existing->id,
                'charged_amount' => $existing->amount,
            ]);
        }

        try {
            $result = $this->payments->charge(
                customerId: $context->get('customer_id'),
                amount: $context->get('total_amount'),
                currency: $context->get('currency'),
                idempotencyKey: $idempotencyKey
            );

            return StepResult::success([
                'payment_id' => $result->paymentId,
                'charged_amount' => $result->amount,
            ]);
        } catch (PaymentDeclinedException $e) {
            return StepResult::failure("Payment declined: {$e->getMessage()}");
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        $paymentId = $context->get('payment_id');

        if ($paymentId === null) {
            return StepResult::success();
        }

        try {
            $this->payments->refund(
                paymentId: $paymentId,
                amount: $context->get('charged_amount'),
                reason: 'Saga compensation'
            );
            return StepResult::success();
        } catch (PaymentNotFoundException | AlreadyRefundedException) {
            return StepResult::success();
        }
    }
}
```

---

### OrderSagaFactory

**File:** `src/Application/Order/Saga/OrderSagaFactory.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Saga;

use Application\Order\Saga\Step\ChargePaymentStep;
use Application\Order\Saga\Step\CreateShipmentStep;
use Application\Order\Saga\Step\ReserveInventoryStep;
use Application\Shared\Saga\SagaOrchestrator;
use Application\Shared\Saga\SagaPersistenceInterface;
use Domain\Shared\Saga\SagaContext;
use Psr\Log\LoggerInterface;
use Ramsey\Uuid\Uuid;

final readonly class OrderSagaFactory
{
    public function __construct(
        private ReserveInventoryStep $reserveStep,
        private ChargePaymentStep $chargeStep,
        private CreateShipmentStep $shipStep,
        private SagaPersistenceInterface $persistence,
        private LoggerInterface $logger
    ) {}

    public function create(CreateOrderCommand $command): SagaOrchestrator
    {
        $sagaId = Uuid::uuid4()->toString();

        $context = new SagaContext(
            sagaId: $sagaId,
            sagaType: 'order',
            correlationId: $command->orderId,
            startedAt: new \DateTimeImmutable(),
            initialData: [
                'order_id' => $command->orderId,
                'customer_id' => $command->customerId,
                'items' => $command->items,
                'total_amount' => $command->totalAmount,
                'currency' => $command->currency,
            ]
        );

        return (new SagaOrchestrator($context, $this->persistence, $this->logger))
            ->addStep($this->reserveStep)
            ->addStep($this->chargeStep)
            ->addStep($this->shipStep);
    }
}
```

---

## Unit Tests

### SagaStateTest

**File:** `tests/Unit/Domain/Shared/Saga/SagaStateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Saga;

use Domain\Shared\Saga\SagaState;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(SagaState::class)]
final class SagaStateTest extends TestCase
{
    public function testPendingCanTransitionToRunning(): void
    {
        $this->assertTrue(SagaState::Pending->canTransitionTo(SagaState::Running));
        $this->assertFalse(SagaState::Pending->canTransitionTo(SagaState::Completed));
    }

    public function testRunningCanTransitionToCompletedOrCompensating(): void
    {
        $this->assertTrue(SagaState::Running->canTransitionTo(SagaState::Completed));
        $this->assertTrue(SagaState::Running->canTransitionTo(SagaState::Compensating));
        $this->assertFalse(SagaState::Running->canTransitionTo(SagaState::Pending));
    }

    public function testTerminalStatesCannotTransition(): void
    {
        $this->assertTrue(SagaState::Completed->isTerminal());
        $this->assertTrue(SagaState::Failed->isTerminal());
        $this->assertTrue(SagaState::CompensationFailed->isTerminal());

        $this->assertFalse(SagaState::Completed->canTransitionTo(SagaState::Running));
    }
}
```

---

### SagaOrchestratorTest

**File:** `tests/Unit/Application/Shared/Saga/SagaOrchestratorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\Saga;

use Application\Shared\Saga\SagaOrchestrator;
use Application\Shared\Saga\SagaPersistenceInterface;
use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaState;
use Domain\Shared\Saga\SagaStepInterface;
use Domain\Shared\Saga\StepResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(SagaOrchestrator::class)]
final class SagaOrchestratorTest extends TestCase
{
    public function testExecutesAllStepsSuccessfully(): void
    {
        $context = new SagaContext('saga-1', 'test', 'corr-1', new \DateTimeImmutable());

        $step1 = $this->createMock(SagaStepInterface::class);
        $step1->method('name')->willReturn('step1');
        $step1->method('execute')->willReturn(StepResult::success());

        $step2 = $this->createMock(SagaStepInterface::class);
        $step2->method('name')->willReturn('step2');
        $step2->method('execute')->willReturn(StepResult::success());

        $persistence = $this->createMock(SagaPersistenceInterface::class);

        $orchestrator = (new SagaOrchestrator($context, $persistence, new NullLogger()))
            ->addStep($step1)
            ->addStep($step2);

        $result = $orchestrator->execute();

        $this->assertTrue($result->isCompleted());
        $this->assertSame(['step1', 'step2'], $orchestrator->getCompletedSteps());
    }

    public function testCompensatesOnFailure(): void
    {
        $context = new SagaContext('saga-1', 'test', 'corr-1', new \DateTimeImmutable());

        $step1 = $this->createMock(SagaStepInterface::class);
        $step1->method('name')->willReturn('step1');
        $step1->method('execute')->willReturn(StepResult::success());
        $step1->expects($this->once())->method('compensate')->willReturn(StepResult::success());

        $step2 = $this->createMock(SagaStepInterface::class);
        $step2->method('name')->willReturn('step2');
        $step2->method('execute')->willReturn(StepResult::failure('Error'));

        $persistence = $this->createMock(SagaPersistenceInterface::class);

        $orchestrator = (new SagaOrchestrator($context, $persistence, new NullLogger()))
            ->addStep($step1)
            ->addStep($step2);

        $result = $orchestrator->execute();

        $this->assertTrue($result->isFailed());
        $this->assertSame('Error', $result->error);
    }

    public function testReportsCompensationFailure(): void
    {
        $context = new SagaContext('saga-1', 'test', 'corr-1', new \DateTimeImmutable());

        $step1 = $this->createMock(SagaStepInterface::class);
        $step1->method('name')->willReturn('step1');
        $step1->method('execute')->willReturn(StepResult::success());
        $step1->method('compensate')->willReturn(StepResult::failure('Comp error'));

        $step2 = $this->createMock(SagaStepInterface::class);
        $step2->method('name')->willReturn('step2');
        $step2->method('execute')->willReturn(StepResult::failure('Step error'));

        $persistence = $this->createMock(SagaPersistenceInterface::class);

        $orchestrator = (new SagaOrchestrator($context, $persistence, new NullLogger()))
            ->addStep($step1)
            ->addStep($step2);

        $result = $orchestrator->execute();

        $this->assertTrue($result->isCompensationFailed());
        $this->assertSame('Step error', $result->error);
        $this->assertSame('Comp error', $result->compensationError);
    }
}
```
