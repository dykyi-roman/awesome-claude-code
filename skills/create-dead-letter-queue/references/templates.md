# Dead Letter Queue Templates

## Domain Layer Components

### FailureType Enum

**File:** `src/Domain/Shared/DeadLetter/FailureType.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\DeadLetter;

enum FailureType: string
{
    case Transient = 'transient';
    case Permanent = 'permanent';
    case Unknown = 'unknown';

    public function isRetryable(): bool
    {
        return match ($this) {
            self::Transient => true,
            self::Permanent => false,
            self::Unknown => true,
        };
    }

    public function shouldAlert(): bool
    {
        return $this === self::Permanent;
    }
}
```

---

### DeadLetterMessage Entity

**File:** `src/Domain/Shared/DeadLetter/DeadLetterMessage.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\DeadLetter;

use Ramsey\Uuid\Uuid;

final class DeadLetterMessage
{
    public function __construct(
        public readonly string $id,
        public readonly string $originalBody,
        public readonly string $originalRoutingKey,
        public readonly array $originalHeaders,
        public readonly string $errorMessage,
        public readonly string $errorTrace,
        public readonly FailureType $failureType,
        public readonly int $attemptCount,
        public readonly \DateTimeImmutable $failedAt,
        public readonly ?\DateTimeImmutable $nextRetryAt = null,
        public readonly ?\DateTimeImmutable $resolvedAt = null,
    ) {}

    public static function create(
        string $originalBody,
        string $originalRoutingKey,
        array $originalHeaders,
        string $errorMessage,
        string $errorTrace,
        FailureType $failureType
    ): self {
        return new self(
            id: Uuid::uuid4()->toString(),
            originalBody: $originalBody,
            originalRoutingKey: $originalRoutingKey,
            originalHeaders: $originalHeaders,
            errorMessage: $errorMessage,
            errorTrace: $errorTrace,
            failureType: $failureType,
            attemptCount: 1,
            failedAt: new \DateTimeImmutable(),
            nextRetryAt: null,
            resolvedAt: null
        );
    }

    public function isRetryable(int $maxAttempts): bool
    {
        if ($this->resolvedAt !== null) {
            return false;
        }

        if (!$this->failureType->isRetryable()) {
            return false;
        }

        return $this->attemptCount < $maxAttempts;
    }

    public function isResolved(): bool
    {
        return $this->resolvedAt !== null;
    }

    public function isPermanentlyFailed(): bool
    {
        return $this->failureType === FailureType::Permanent;
    }

    public function withIncrementedAttempt(\DateTimeImmutable $nextRetryAt): self
    {
        return new self(
            id: $this->id,
            originalBody: $this->originalBody,
            originalRoutingKey: $this->originalRoutingKey,
            originalHeaders: $this->originalHeaders,
            errorMessage: $this->errorMessage,
            errorTrace: $this->errorTrace,
            failureType: $this->failureType,
            attemptCount: $this->attemptCount + 1,
            failedAt: $this->failedAt,
            nextRetryAt: $nextRetryAt,
            resolvedAt: $this->resolvedAt
        );
    }

    public function withResolved(): self
    {
        return new self(
            id: $this->id,
            originalBody: $this->originalBody,
            originalRoutingKey: $this->originalRoutingKey,
            originalHeaders: $this->originalHeaders,
            errorMessage: $this->errorMessage,
            errorTrace: $this->errorTrace,
            failureType: $this->failureType,
            attemptCount: $this->attemptCount,
            failedAt: $this->failedAt,
            nextRetryAt: $this->nextRetryAt,
            resolvedAt: new \DateTimeImmutable()
        );
    }

    public function payloadAsArray(): array
    {
        return json_decode($this->originalBody, true, 512, JSON_THROW_ON_ERROR);
    }
}
```

---

## Application Layer Components

### DeadLetterStoreInterface

**File:** `src/Application/Shared/DeadLetter/DeadLetterStoreInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

use Domain\Shared\DeadLetter\DeadLetterMessage;
use Domain\Shared\DeadLetter\FailureType;

interface DeadLetterStoreInterface
{
    public function store(DeadLetterMessage $message): void;

    /** @return array<DeadLetterMessage> */
    public function findRetryable(int $limit = 100): array;

    public function markRetried(string $id, \DateTimeImmutable $nextRetryAt): void;

    public function markResolved(string $id): void;

    public function purge(\DateTimeImmutable $before): int;

    public function countByType(FailureType $type): int;

    public function findById(string $id): ?DeadLetterMessage;
}
```

---

### DeadLetterHandler

**File:** `src/Application/Shared/DeadLetter/DeadLetterHandler.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

use Domain\Shared\DeadLetter\DeadLetterMessage;
use Psr\Log\LoggerInterface;

final readonly class DeadLetterHandler
{
    public function __construct(
        private DeadLetterStoreInterface $store,
        private FailureClassifier $classifier,
        private LoggerInterface $logger
    ) {}

    public function handle(
        string $body,
        string $routingKey,
        array $headers,
        \Throwable $exception
    ): void {
        $failureType = $this->classifier->classify($exception);

        $message = DeadLetterMessage::create(
            originalBody: $body,
            originalRoutingKey: $routingKey,
            originalHeaders: $headers,
            errorMessage: $exception->getMessage(),
            errorTrace: $exception->getTraceAsString(),
            failureType: $failureType
        );

        $this->store->store($message);

        $this->logger->error('Message sent to DLQ', [
            'dlq_id' => $message->id,
            'routing_key' => $routingKey,
            'failure_type' => $failureType->value,
            'error' => $exception->getMessage(),
            'exception' => get_class($exception),
        ]);
    }
}
```

---

### RetryStrategy

**File:** `src/Application/Shared/DeadLetter/RetryStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

use Domain\Shared\DeadLetter\DeadLetterMessage;

final readonly class RetryStrategy
{
    public function __construct(
        private int $maxAttempts = 5,
        private int $baseDelaySeconds = 60,
        private float $multiplier = 2.0
    ) {}

    public function shouldRetry(DeadLetterMessage $message): bool
    {
        return $message->isRetryable($this->maxAttempts);
    }

    public function calculateNextRetryAt(DeadLetterMessage $message): \DateTimeImmutable
    {
        $attempt = $message->attemptCount;
        $delay = $this->baseDelaySeconds * ($this->multiplier ** ($attempt - 1));
        $jitter = $this->addJitter($delay);

        return (new \DateTimeImmutable())->modify(sprintf('+%d seconds', (int) $jitter));
    }

    private function addJitter(float $delay): float
    {
        $jitterRange = $delay * 0.25;
        $jitter = mt_rand((int) -$jitterRange, (int) $jitterRange);

        return max(1, $delay + $jitter);
    }

    public function maxAttempts(): int
    {
        return $this->maxAttempts;
    }
}
```

---

### FailureClassifier

**File:** `src/Application/Shared/DeadLetter/FailureClassifier.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

use Domain\Shared\DeadLetter\FailureType;

final readonly class FailureClassifier
{
    /** @var array<string, FailureType> */
    private array $mapping;

    /**
     * @param array<string, FailureType> $customMapping
     */
    public function __construct(array $customMapping = [])
    {
        $this->mapping = array_merge($this->defaultMapping(), $customMapping);
    }

    public function classify(\Throwable $exception): FailureType
    {
        $class = get_class($exception);

        if (isset($this->mapping[$class])) {
            return $this->mapping[$class];
        }

        foreach ($this->mapping as $exceptionClass => $type) {
            if (is_a($exception, $exceptionClass)) {
                return $type;
            }
        }

        return FailureType::Unknown;
    }

    private function defaultMapping(): array
    {
        return [
            \PDOException::class => FailureType::Transient,
            \Doctrine\DBAL\Exception\ConnectionException::class => FailureType::Transient,
            \Doctrine\DBAL\Exception\DeadlockException::class => FailureType::Transient,
            \InvalidArgumentException::class => FailureType::Permanent,
            \DomainException::class => FailureType::Permanent,
            \RuntimeException::class => FailureType::Unknown,
        ];
    }
}
```

---

### ProcessingResult

**File:** `src/Application/Shared/DeadLetter/ProcessingResult.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

final readonly class ProcessingResult
{
    public function __construct(
        public int $processed,
        public int $succeeded,
        public int $failed,
        public int $skipped
    ) {}

    public function hasProcessedAny(): bool
    {
        return $this->processed > 0;
    }
}
```

---

### DlqProcessor

**File:** `src/Application/Shared/DeadLetter/DlqProcessor.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\DeadLetter;

use Psr\Log\LoggerInterface;

final readonly class DlqProcessor
{
    public function __construct(
        private DeadLetterStoreInterface $store,
        private RetryStrategy $strategy,
        private LoggerInterface $logger
    ) {}

    /**
     * @param callable(string, string, array): void $handler
     */
    public function process(callable $handler, int $batchSize = 100): ProcessingResult
    {
        $messages = $this->store->findRetryable($batchSize);
        $succeeded = 0;
        $failed = 0;
        $skipped = 0;

        foreach ($messages as $message) {
            if (!$this->strategy->shouldRetry($message)) {
                $skipped++;
                $this->logger->info('Message skipped (max retries)', ['dlq_id' => $message->id]);
                continue;
            }

            if ($message->nextRetryAt !== null && $message->nextRetryAt > new \DateTimeImmutable()) {
                $skipped++;
                continue;
            }

            try {
                $handler(
                    $message->originalBody,
                    $message->originalRoutingKey,
                    $message->originalHeaders
                );

                $this->store->markResolved($message->id);
                $succeeded++;

                $this->logger->info('DLQ message reprocessed successfully', ['dlq_id' => $message->id]);
            } catch (\Throwable $e) {
                $nextRetryAt = $this->strategy->calculateNextRetryAt($message);
                $this->store->markRetried($message->id, $nextRetryAt);
                $failed++;

                $this->logger->warning('DLQ message retry failed', [
                    'dlq_id' => $message->id,
                    'attempt' => $message->attemptCount + 1,
                    'next_retry_at' => $nextRetryAt->format('c'),
                    'error' => $e->getMessage(),
                ]);
            }
        }

        return new ProcessingResult(
            processed: count($messages),
            succeeded: $succeeded,
            failed: $failed,
            skipped: $skipped
        );
    }
}
```

---

## Infrastructure Layer

### DatabaseDeadLetterStore

**File:** `src/Infrastructure/DeadLetter/DatabaseDeadLetterStore.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\DeadLetter;

use Application\Shared\DeadLetter\DeadLetterStoreInterface;
use Domain\Shared\DeadLetter\DeadLetterMessage;
use Domain\Shared\DeadLetter\FailureType;

final readonly class DatabaseDeadLetterStore implements DeadLetterStoreInterface
{
    public function __construct(
        private \PDO $pdo
    ) {}

    public function store(DeadLetterMessage $message): void
    {
        $stmt = $this->pdo->prepare('
            INSERT INTO dead_letter_messages (
                id, original_body, original_routing_key, original_headers,
                error_message, error_trace, failure_type, attempt_count,
                failed_at, next_retry_at, resolved_at
            ) VALUES (
                :id, :body, :routing_key, :headers,
                :error_message, :error_trace, :failure_type, :attempt_count,
                :failed_at, :next_retry_at, :resolved_at
            )
            ON CONFLICT (id) DO UPDATE SET
                attempt_count = :attempt_count,
                next_retry_at = :next_retry_at,
                resolved_at = :resolved_at
        ');

        $stmt->execute([
            'id' => $message->id,
            'body' => $message->originalBody,
            'routing_key' => $message->originalRoutingKey,
            'headers' => json_encode($message->originalHeaders),
            'error_message' => $message->errorMessage,
            'error_trace' => $message->errorTrace,
            'failure_type' => $message->failureType->value,
            'attempt_count' => $message->attemptCount,
            'failed_at' => $message->failedAt->format('Y-m-d H:i:s.u'),
            'next_retry_at' => $message->nextRetryAt?->format('Y-m-d H:i:s.u'),
            'resolved_at' => $message->resolvedAt?->format('Y-m-d H:i:s.u'),
        ]);
    }

    public function findRetryable(int $limit = 100): array
    {
        $stmt = $this->pdo->prepare('
            SELECT * FROM dead_letter_messages
            WHERE resolved_at IS NULL
              AND failure_type != :permanent
              AND (next_retry_at IS NULL OR next_retry_at <= :now)
            ORDER BY failed_at ASC
            LIMIT :limit
        ');

        $stmt->execute([
            'permanent' => FailureType::Permanent->value,
            'now' => (new \DateTimeImmutable())->format('Y-m-d H:i:s.u'),
            'limit' => $limit,
        ]);

        return array_map($this->hydrate(...), $stmt->fetchAll(\PDO::FETCH_ASSOC));
    }

    public function markRetried(string $id, \DateTimeImmutable $nextRetryAt): void
    {
        $stmt = $this->pdo->prepare('
            UPDATE dead_letter_messages
            SET attempt_count = attempt_count + 1,
                next_retry_at = :next_retry_at
            WHERE id = :id
        ');

        $stmt->execute([
            'id' => $id,
            'next_retry_at' => $nextRetryAt->format('Y-m-d H:i:s.u'),
        ]);
    }

    public function markResolved(string $id): void
    {
        $stmt = $this->pdo->prepare('
            UPDATE dead_letter_messages
            SET resolved_at = :resolved_at
            WHERE id = :id
        ');

        $stmt->execute([
            'id' => $id,
            'resolved_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s.u'),
        ]);
    }

    public function purge(\DateTimeImmutable $before): int
    {
        $stmt = $this->pdo->prepare('
            DELETE FROM dead_letter_messages
            WHERE resolved_at < :before
        ');

        $stmt->execute(['before' => $before->format('Y-m-d H:i:s.u')]);

        return $stmt->rowCount();
    }

    public function countByType(FailureType $type): int
    {
        $stmt = $this->pdo->prepare('
            SELECT COUNT(*) FROM dead_letter_messages
            WHERE failure_type = :type
              AND resolved_at IS NULL
        ');

        $stmt->execute(['type' => $type->value]);

        return (int) $stmt->fetchColumn();
    }

    public function findById(string $id): ?DeadLetterMessage
    {
        $stmt = $this->pdo->prepare('SELECT * FROM dead_letter_messages WHERE id = :id');
        $stmt->execute(['id' => $id]);

        $row = $stmt->fetch(\PDO::FETCH_ASSOC);

        return $row ? $this->hydrate($row) : null;
    }

    private function hydrate(array $row): DeadLetterMessage
    {
        return new DeadLetterMessage(
            id: $row['id'],
            originalBody: $row['original_body'],
            originalRoutingKey: $row['original_routing_key'],
            originalHeaders: json_decode($row['original_headers'], true),
            errorMessage: $row['error_message'],
            errorTrace: $row['error_trace'],
            failureType: FailureType::from($row['failure_type']),
            attemptCount: (int) $row['attempt_count'],
            failedAt: new \DateTimeImmutable($row['failed_at']),
            nextRetryAt: $row['next_retry_at'] ? new \DateTimeImmutable($row['next_retry_at']) : null,
            resolvedAt: $row['resolved_at'] ? new \DateTimeImmutable($row['resolved_at']) : null
        );
    }
}
```

---

### Database Migration

**File:** `migrations/Version*_CreateDeadLetterMessagesTable.php`

```php
<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20240101000001_CreateDeadLetterMessagesTable extends AbstractMigration
{
    public function up(Schema $schema): void
    {
        $this->addSql('
            CREATE TABLE dead_letter_messages (
                id VARCHAR(255) PRIMARY KEY,
                original_body TEXT NOT NULL,
                original_routing_key VARCHAR(255) NOT NULL,
                original_headers JSONB NOT NULL DEFAULT \'{}\',
                error_message TEXT NOT NULL,
                error_trace TEXT,
                failure_type VARCHAR(50) NOT NULL,
                attempt_count INTEGER NOT NULL DEFAULT 1,
                failed_at TIMESTAMP(6) NOT NULL,
                next_retry_at TIMESTAMP(6),
                resolved_at TIMESTAMP(6)
            )
        ');

        $this->addSql('
            CREATE INDEX idx_dlq_retryable ON dead_letter_messages (failure_type, next_retry_at)
            WHERE resolved_at IS NULL AND failure_type != \'permanent\'
        ');

        $this->addSql('CREATE INDEX idx_dlq_failed_at ON dead_letter_messages (failed_at)');
        $this->addSql('CREATE INDEX idx_dlq_routing_key ON dead_letter_messages (original_routing_key)');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE dead_letter_messages');
    }
}
```
