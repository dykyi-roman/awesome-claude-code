# PHP 8.4 Saga Pattern Implementation

## Complete Implementation Guide

### Domain Layer

#### SagaState Enum

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

enum SagaState: string
{
    case Pending = 'pending';
    case Running = 'running';
    case Compensating = 'compensating';
    case Completed = 'completed';
    case Failed = 'failed';
    case CompensationFailed = 'compensation_failed';

    public function canTransitionTo(self $next): bool
    {
        return match ($this) {
            self::Pending => $next === self::Running,
            self::Running => in_array($next, [self::Completed, self::Compensating], true),
            self::Compensating => in_array($next, [self::Failed, self::CompensationFailed], true),
            self::Completed, self::Failed, self::CompensationFailed => false,
        };
    }

    public function isTerminal(): bool
    {
        return in_array($this, [self::Completed, self::Failed, self::CompensationFailed], true);
    }

    public function requiresCompensation(): bool
    {
        return $this === self::Compensating;
    }
}
```

#### StepResult Value Object

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

final readonly class StepResult
{
    private function __construct(
        private bool $success,
        private ?string $error = null,
        private array $data = []
    ) {}

    public static function success(array $data = []): self
    {
        return new self(true, null, $data);
    }

    public static function failure(string $error): self
    {
        return new self(false, $error);
    }

    public function isSuccess(): bool
    {
        return $this->success;
    }

    public function isFailure(): bool
    {
        return !$this->success;
    }

    public function error(): ?string
    {
        return $this->error;
    }

    public function data(): array
    {
        return $this->data;
    }

    public function get(string $key, mixed $default = null): mixed
    {
        return $this->data[$key] ?? $default;
    }
}
```

#### SagaStep Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

interface SagaStepInterface
{
    public function name(): string;

    public function execute(SagaContext $context): StepResult;

    public function compensate(SagaContext $context): StepResult;

    public function isIdempotent(): bool;

    public function timeout(): int;
}
```

#### SagaContext

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

final class SagaContext implements \JsonSerializable
{
    /** @var array<string, mixed> */
    private array $data = [];

    public function __construct(
        public readonly string $sagaId,
        public readonly string $sagaType,
        public readonly string $correlationId,
        public readonly \DateTimeImmutable $startedAt,
        array $initialData = []
    ) {
        $this->data = $initialData;
    }

    public function set(string $key, mixed $value): self
    {
        $this->data[$key] = $value;
        return $this;
    }

    public function get(string $key, mixed $default = null): mixed
    {
        return $this->data[$key] ?? $default;
    }

    public function has(string $key): bool
    {
        return array_key_exists($key, $this->data);
    }

    public function all(): array
    {
        return $this->data;
    }

    public function merge(array $data): self
    {
        $this->data = array_merge($this->data, $data);
        return $this;
    }

    public function jsonSerialize(): array
    {
        return [
            'saga_id' => $this->sagaId,
            'saga_type' => $this->sagaType,
            'correlation_id' => $this->correlationId,
            'started_at' => $this->startedAt->format('c'),
            'data' => $this->data,
        ];
    }

    public static function fromArray(array $data): self
    {
        $context = new self(
            sagaId: $data['saga_id'],
            sagaType: $data['saga_type'],
            correlationId: $data['correlation_id'],
            startedAt: new \DateTimeImmutable($data['started_at'])
        );
        $context->data = $data['data'] ?? [];
        return $context;
    }
}
```

#### SagaResult

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

final readonly class SagaResult
{
    private function __construct(
        public SagaState $state,
        public SagaContext $context,
        public ?string $error = null,
        public ?string $compensationError = null
    ) {}

    public static function completed(SagaContext $context): self
    {
        return new self(SagaState::Completed, $context);
    }

    public static function failed(SagaContext $context, string $error): self
    {
        return new self(SagaState::Failed, $context, $error);
    }

    public static function compensationFailed(
        SagaContext $context,
        string $error,
        string $compensationError
    ): self {
        return new self(SagaState::CompensationFailed, $context, $error, $compensationError);
    }

    public function isCompleted(): bool
    {
        return $this->state === SagaState::Completed;
    }

    public function isFailed(): bool
    {
        return in_array($this->state, [SagaState::Failed, SagaState::CompensationFailed], true);
    }
}
```

### Application Layer

#### SagaOrchestrator

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaResult;
use Domain\Shared\Saga\SagaState;
use Domain\Shared\Saga\SagaStepInterface;
use Domain\Shared\Saga\StepResult;
use Psr\Log\LoggerInterface;

final class SagaOrchestrator
{
    /** @var array<SagaStepInterface> */
    private array $steps = [];

    /** @var array<string> */
    private array $completedSteps = [];

    private SagaState $state = SagaState::Pending;

    public function __construct(
        private readonly SagaContext $context,
        private readonly SagaPersistenceInterface $persistence,
        private readonly LoggerInterface $logger
    ) {}

    public function addStep(SagaStepInterface $step): self
    {
        $this->steps[] = $step;
        return $this;
    }

    public function execute(): SagaResult
    {
        $this->transitionTo(SagaState::Running);
        $this->logger->info('Saga started', [
            'saga_id' => $this->context->sagaId,
            'saga_type' => $this->context->sagaType,
        ]);

        foreach ($this->steps as $step) {
            $this->logger->debug('Executing saga step', [
                'saga_id' => $this->context->sagaId,
                'step' => $step->name(),
            ]);

            $result = $this->executeStep($step);

            if ($result->isFailure()) {
                $this->logger->warning('Saga step failed, starting compensation', [
                    'saga_id' => $this->context->sagaId,
                    'step' => $step->name(),
                    'error' => $result->error(),
                ]);

                return $this->compensate($step->name(), $result->error());
            }

            $this->completedSteps[] = $step->name();
            $this->saveState();
        }

        $this->transitionTo(SagaState::Completed);

        $this->logger->info('Saga completed successfully', [
            'saga_id' => $this->context->sagaId,
        ]);

        return SagaResult::completed($this->context);
    }

    private function executeStep(SagaStepInterface $step): StepResult
    {
        try {
            return $step->execute($this->context);
        } catch (\Throwable $e) {
            return StepResult::failure($e->getMessage());
        }
    }

    private function compensate(string $failedStep, string $error): SagaResult
    {
        $this->transitionTo(SagaState::Compensating);

        $stepsToCompensate = array_reverse($this->completedSteps);

        foreach ($stepsToCompensate as $stepName) {
            $step = $this->findStep($stepName);

            $this->logger->debug('Compensating saga step', [
                'saga_id' => $this->context->sagaId,
                'step' => $stepName,
            ]);

            $result = $this->compensateStep($step);

            if ($result->isFailure()) {
                $this->transitionTo(SagaState::CompensationFailed);

                $this->logger->error('Saga compensation failed', [
                    'saga_id' => $this->context->sagaId,
                    'step' => $stepName,
                    'error' => $result->error(),
                ]);

                return SagaResult::compensationFailed(
                    $this->context,
                    $error,
                    $result->error()
                );
            }
        }

        $this->transitionTo(SagaState::Failed);

        $this->logger->info('Saga compensation completed', [
            'saga_id' => $this->context->sagaId,
        ]);

        return SagaResult::failed($this->context, $error);
    }

    private function compensateStep(SagaStepInterface $step): StepResult
    {
        try {
            return $step->compensate($this->context);
        } catch (\Throwable $e) {
            return StepResult::failure($e->getMessage());
        }
    }

    private function transitionTo(SagaState $newState): void
    {
        if (!$this->state->canTransitionTo($newState)) {
            throw new InvalidSagaStateTransition($this->state, $newState);
        }

        $this->state = $newState;
        $this->saveState();
    }

    private function saveState(): void
    {
        $this->persistence->save(
            $this->context->sagaId,
            $this->context->sagaType,
            $this->state,
            $this->completedSteps,
            $this->context
        );
    }

    private function findStep(string $name): SagaStepInterface
    {
        foreach ($this->steps as $step) {
            if ($step->name() === $name) {
                return $step;
            }
        }

        throw new SagaStepNotFound($name);
    }
}
```

#### SagaPersistence Interface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaState;

interface SagaPersistenceInterface
{
    public function save(
        string $sagaId,
        string $sagaType,
        SagaState $state,
        array $completedSteps,
        SagaContext $context
    ): void;

    public function findById(string $sagaId): ?SagaRecord;

    /** @return array<SagaRecord> */
    public function findIncomplete(): array;

    public function markAsDeadLettered(string $sagaId): void;
}
```

#### Abstract Step Base Class

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaStepInterface;
use Domain\Shared\Saga\StepResult;

abstract readonly class AbstractSagaStep implements SagaStepInterface
{
    protected const DEFAULT_TIMEOUT = 30;

    public function isIdempotent(): bool
    {
        return true;
    }

    public function timeout(): int
    {
        return static::DEFAULT_TIMEOUT;
    }

    protected function idempotencyKey(SagaContext $context): string
    {
        return "{$context->sagaId}_{$this->name()}";
    }
}
```

### Example: Order Saga

#### OrderSaga Steps

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
        if ($existing) {
            $context->set('reservation_id', $existing->id);
            return StepResult::success();
        }

        try {
            $reservation = $this->inventory->reserve(
                orderId: $context->get('order_id'),
                items: $context->get('items'),
                idempotencyKey: $idempotencyKey
            );

            $context->set('reservation_id', $reservation->id);

            return StepResult::success();
        } catch (InsufficientStockException $e) {
            return StepResult::failure("Insufficient stock: {$e->getMessage()}");
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        $reservationId = $context->get('reservation_id');

        if (!$reservationId) {
            return StepResult::success();
        }

        try {
            $this->inventory->release($reservationId);
            return StepResult::success();
        } catch (ReservationNotFoundException $e) {
            return StepResult::success();
        }
    }
}
```

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
        if ($existing) {
            $context->set('payment_id', $existing->id);
            $context->set('charged_amount', $existing->amount);
            return StepResult::success();
        }

        try {
            $result = $this->payments->charge(
                customerId: $context->get('customer_id'),
                amount: $context->get('total_amount'),
                currency: $context->get('currency'),
                idempotencyKey: $idempotencyKey
            );

            $context->set('payment_id', $result->paymentId);
            $context->set('charged_amount', $result->amount);

            return StepResult::success();
        } catch (PaymentDeclinedException $e) {
            return StepResult::failure("Payment declined: {$e->getMessage()}");
        }
    }

    public function compensate(SagaContext $context): StepResult
    {
        $paymentId = $context->get('payment_id');

        if (!$paymentId) {
            return StepResult::success();
        }

        try {
            $this->payments->refund(
                paymentId: $paymentId,
                amount: $context->get('charged_amount'),
                reason: 'Saga compensation'
            );
            return StepResult::success();
        } catch (PaymentNotFoundException | AlreadyRefundedException $e) {
            return StepResult::success();
        }
    }
}
```

#### OrderSaga Factory

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

### Infrastructure Layer

#### Doctrine SagaPersistence

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Saga;

use Application\Shared\Saga\SagaPersistenceInterface;
use Application\Shared\Saga\SagaRecord;
use Doctrine\DBAL\Connection;
use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaState;

final readonly class DoctrineSagaPersistence implements SagaPersistenceInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function save(
        string $sagaId,
        string $sagaType,
        SagaState $state,
        array $completedSteps,
        SagaContext $context
    ): void {
        $now = (new \DateTimeImmutable())->format('Y-m-d H:i:s.u');

        $this->connection->executeStatement(
            'INSERT INTO sagas (id, type, state, completed_steps, context, created_at, updated_at)
             VALUES (:id, :type, :state, :steps, :context, :now, :now)
             ON CONFLICT (id) DO UPDATE SET
                state = :state,
                completed_steps = :steps,
                context = :context,
                updated_at = :now,
                completed_at = CASE WHEN :state IN (:completed, :failed) THEN :now ELSE NULL END',
            [
                'id' => $sagaId,
                'type' => $sagaType,
                'state' => $state->value,
                'steps' => json_encode($completedSteps),
                'context' => json_encode($context),
                'now' => $now,
                'completed' => SagaState::Completed->value,
                'failed' => SagaState::Failed->value,
            ]
        );
    }

    public function findById(string $sagaId): ?SagaRecord
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM sagas WHERE id = :id',
            ['id' => $sagaId]
        );

        return $row ? $this->hydrate($row) : null;
    }

    public function findIncomplete(): array
    {
        $rows = $this->connection->fetchAllAssociative(
            'SELECT * FROM sagas
             WHERE state NOT IN (:completed, :failed, :dead)
             ORDER BY created_at ASC',
            [
                'completed' => SagaState::Completed->value,
                'failed' => SagaState::Failed->value,
                'dead' => 'dead_lettered',
            ]
        );

        return array_map($this->hydrate(...), $rows);
    }

    public function markAsDeadLettered(string $sagaId): void
    {
        $this->connection->update(
            'sagas',
            ['state' => 'dead_lettered'],
            ['id' => $sagaId]
        );
    }

    private function hydrate(array $row): SagaRecord
    {
        return new SagaRecord(
            id: $row['id'],
            type: $row['type'],
            state: SagaState::from($row['state']),
            completedSteps: json_decode($row['completed_steps'], true),
            context: SagaContext::fromArray(json_decode($row['context'], true)),
            createdAt: new \DateTimeImmutable($row['created_at']),
            updatedAt: new \DateTimeImmutable($row['updated_at'])
        );
    }
}
```

## Testing

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Saga;

use Application\Order\Saga\Step\ReserveInventoryStep;
use Domain\Shared\Saga\SagaContext;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ReserveInventoryStep::class)]
final class ReserveInventoryStepTest extends TestCase
{
    public function testExecuteReservesInventory(): void
    {
        $context = new SagaContext(
            'saga-1',
            'order',
            'order-123',
            new \DateTimeImmutable()
        );
        $context->set('order_id', 'order-123');
        $context->set('items', [['sku' => 'SKU-1', 'qty' => 2]]);

        $inventory = $this->createMock(InventoryServiceInterface::class);
        $inventory->method('findReservationByKey')->willReturn(null);
        $inventory->expects($this->once())
            ->method('reserve')
            ->willReturn(new Reservation('res-456'));

        $step = new ReserveInventoryStep($inventory);
        $result = $step->execute($context);

        $this->assertTrue($result->isSuccess());
        $this->assertSame('res-456', $context->get('reservation_id'));
    }

    public function testCompensateReleasesReservation(): void
    {
        $context = new SagaContext(
            'saga-1',
            'order',
            'order-123',
            new \DateTimeImmutable()
        );
        $context->set('reservation_id', 'res-456');

        $inventory = $this->createMock(InventoryServiceInterface::class);
        $inventory->expects($this->once())
            ->method('release')
            ->with('res-456');

        $step = new ReserveInventoryStep($inventory);
        $result = $step->compensate($context);

        $this->assertTrue($result->isSuccess());
    }

    public function testCompensateIsIdempotent(): void
    {
        $context = new SagaContext(
            'saga-1',
            'order',
            'order-123',
            new \DateTimeImmutable()
        );
        $context->set('reservation_id', 'res-456');

        $inventory = $this->createMock(InventoryServiceInterface::class);
        $inventory->method('release')
            ->willThrowException(new ReservationNotFoundException());

        $step = new ReserveInventoryStep($inventory);
        $result = $step->compensate($context);

        $this->assertTrue($result->isSuccess());
    }
}
```
