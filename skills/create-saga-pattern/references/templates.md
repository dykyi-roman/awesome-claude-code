# Saga Pattern Templates

## Domain Layer Components

### SagaState Enum

**File:** `src/Domain/Shared/Saga/SagaState.php`

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

    public function isSuccess(): bool
    {
        return $this === self::Completed;
    }
}
```

---

### StepResult Value Object

**File:** `src/Domain/Shared/Saga/StepResult.php`

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

---

### SagaStepInterface

**File:** `src/Domain/Shared/Saga/SagaStepInterface.php`

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

---

### SagaContext

**File:** `src/Domain/Shared/Saga/SagaContext.php`

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

---

### SagaResult

**File:** `src/Domain/Shared/Saga/SagaResult.php`

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

    public function isCompensationFailed(): bool
    {
        return $this->state === SagaState::CompensationFailed;
    }
}
```

---

### Exception Classes

**File:** `src/Domain/Shared/Saga/InvalidSagaStateTransition.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

final class InvalidSagaStateTransition extends \DomainException
{
    public function __construct(SagaState $from, SagaState $to)
    {
        parent::__construct(
            sprintf('Invalid saga state transition from %s to %s', $from->value, $to->value)
        );
    }
}
```

**File:** `src/Domain/Shared/Saga/SagaStepNotFound.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Saga;

final class SagaStepNotFound extends \RuntimeException
{
    public function __construct(string $stepName)
    {
        parent::__construct(sprintf('Saga step not found: %s', $stepName));
    }
}
```

---

## Application Layer Components

### SagaPersistenceInterface

**File:** `src/Application/Shared/Saga/SagaPersistenceInterface.php`

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
        SagaContext $context,
        ?string $error = null
    ): void;

    public function findById(string $sagaId): ?SagaRecord;

    /** @return array<SagaRecord> */
    public function findIncomplete(): array;

    /** @return array<SagaRecord> */
    public function findByCorrelationId(string $correlationId): array;

    public function markAsDeadLettered(string $sagaId): void;
}
```

---

### SagaRecord

**File:** `src/Application/Shared/Saga/SagaRecord.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Saga;

use Domain\Shared\Saga\SagaContext;
use Domain\Shared\Saga\SagaState;

final readonly class SagaRecord
{
    public function __construct(
        public string $id,
        public string $type,
        public SagaState $state,
        public array $completedSteps,
        public SagaContext $context,
        public ?string $error,
        public \DateTimeImmutable $createdAt,
        public \DateTimeImmutable $updatedAt,
        public ?\DateTimeImmutable $completedAt = null
    ) {}
}
```

---

### SagaOrchestrator

**File:** `src/Application/Shared/Saga/SagaOrchestrator.php`

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
            'correlation_id' => $this->context->correlationId,
        ]);

        foreach ($this->steps as $step) {
            $result = $this->executeStep($step);

            if ($result->isFailure()) {
                return $this->compensate($step->name(), $result->error());
            }

            $this->context->merge($result->data());
            $this->completedSteps[] = $step->name();
            $this->saveState();
        }

        $this->transitionTo(SagaState::Completed);
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

        foreach (array_reverse($this->completedSteps) as $stepName) {
            $step = $this->findStep($stepName);
            $result = $this->compensateStep($step);

            if ($result->isFailure()) {
                $this->transitionTo(SagaState::CompensationFailed);
                return SagaResult::compensationFailed($this->context, $error, $result->error());
            }
        }

        $this->transitionTo(SagaState::Failed);
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

    private function saveState(?string $error = null): void
    {
        $this->persistence->save(
            $this->context->sagaId,
            $this->context->sagaType,
            $this->state,
            $this->completedSteps,
            $this->context,
            $error
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

    public function getState(): SagaState
    {
        return $this->state;
    }

    public function getCompletedSteps(): array
    {
        return $this->completedSteps;
    }
}
```

---

### AbstractSagaStep

**File:** `src/Application/Shared/Saga/AbstractSagaStep.php`

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
        return sprintf('%s_%s', $context->sagaId, $this->name());
    }
}
```

---

## Infrastructure Layer

### DoctrineSagaPersistence

**File:** `src/Infrastructure/Persistence/Doctrine/Repository/DoctrineSagaPersistence.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine\Repository;

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
        SagaContext $context,
        ?string $error = null
    ): void {
        $now = (new \DateTimeImmutable())->format('Y-m-d H:i:s.u');
        $isTerminal = $state->isTerminal();

        $this->connection->executeStatement(
            'INSERT INTO sagas (id, type, state, completed_steps, context, error, created_at, updated_at, completed_at)
             VALUES (:id, :type, :state, :steps, :context, :error, :now, :now, :completed)
             ON CONFLICT (id) DO UPDATE SET
                state = :state,
                completed_steps = :steps,
                context = :context,
                error = :error,
                updated_at = :now,
                completed_at = :completed',
            [
                'id' => $sagaId,
                'type' => $sagaType,
                'state' => $state->value,
                'steps' => json_encode($completedSteps),
                'context' => json_encode($context),
                'error' => $error,
                'now' => $now,
                'completed' => $isTerminal ? $now : null,
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
             WHERE state NOT IN (:completed, :failed, :compFailed, :dead)
             ORDER BY created_at ASC',
            [
                'completed' => SagaState::Completed->value,
                'failed' => SagaState::Failed->value,
                'compFailed' => SagaState::CompensationFailed->value,
                'dead' => 'dead_lettered',
            ]
        );

        return array_map($this->hydrate(...), $rows);
    }

    public function findByCorrelationId(string $correlationId): array
    {
        $rows = $this->connection->fetchAllAssociative(
            "SELECT * FROM sagas WHERE context->>'correlation_id' = :correlationId",
            ['correlationId' => $correlationId]
        );

        return array_map($this->hydrate(...), $rows);
    }

    public function markAsDeadLettered(string $sagaId): void
    {
        $this->connection->update(
            'sagas',
            [
                'state' => 'dead_lettered',
                'updated_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s.u'),
            ],
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
            error: $row['error'],
            createdAt: new \DateTimeImmutable($row['created_at']),
            updatedAt: new \DateTimeImmutable($row['updated_at']),
            completedAt: $row['completed_at']
                ? new \DateTimeImmutable($row['completed_at'])
                : null
        );
    }
}
```

---

### Database Migration

**File:** `migrations/Version*_CreateSagasTable.php`

```php
<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20240101000001_CreateSagasTable extends AbstractMigration
{
    public function up(Schema $schema): void
    {
        $this->addSql('
            CREATE TABLE sagas (
                id VARCHAR(255) PRIMARY KEY,
                type VARCHAR(255) NOT NULL,
                state VARCHAR(50) NOT NULL,
                completed_steps JSONB NOT NULL DEFAULT \'[]\',
                context JSONB NOT NULL,
                error TEXT,
                created_at TIMESTAMP(6) NOT NULL,
                updated_at TIMESTAMP(6) NOT NULL,
                completed_at TIMESTAMP(6)
            )
        ');

        $this->addSql('CREATE INDEX idx_sagas_state ON sagas (state)');
        $this->addSql('CREATE INDEX idx_sagas_type_state ON sagas (type, state)');
        $this->addSql('CREATE INDEX idx_sagas_correlation ON sagas ((context->>\'correlation_id\'))');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE sagas');
    }
}
```
