# Outbox Pattern Templates

## Domain Layer Components

### OutboxMessage Entity

**File:** `src/Domain/Shared/Outbox/OutboxMessage.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Outbox;

final readonly class OutboxMessage
{
    private function __construct(
        public string $id,
        public string $aggregateType,
        public string $aggregateId,
        public string $eventType,
        public string $payload,
        public \DateTimeImmutable $createdAt,
        public ?string $correlationId,
        public ?string $causationId,
        public ?\DateTimeImmutable $processedAt,
        public int $retryCount
    ) {}

    public static function create(
        string $id,
        string $aggregateType,
        string $aggregateId,
        string $eventType,
        array $payload,
        ?string $correlationId = null,
        ?string $causationId = null
    ): self {
        return new self(
            id: $id,
            aggregateType: $aggregateType,
            aggregateId: $aggregateId,
            eventType: $eventType,
            payload: json_encode($payload, JSON_THROW_ON_ERROR),
            createdAt: new \DateTimeImmutable(),
            correlationId: $correlationId,
            causationId: $causationId,
            processedAt: null,
            retryCount: 0
        );
    }

    public static function reconstitute(
        string $id,
        string $aggregateType,
        string $aggregateId,
        string $eventType,
        string $payload,
        \DateTimeImmutable $createdAt,
        ?string $correlationId,
        ?string $causationId,
        ?\DateTimeImmutable $processedAt,
        int $retryCount
    ): self {
        return new self(
            $id, $aggregateType, $aggregateId, $eventType, $payload,
            $createdAt, $correlationId, $causationId, $processedAt, $retryCount
        );
    }

    public function isProcessed(): bool
    {
        return $this->processedAt !== null;
    }

    public function isPoisoned(int $maxRetries): bool
    {
        return $this->retryCount >= $maxRetries;
    }

    public function payloadAsArray(): array
    {
        return json_decode($this->payload, true, 512, JSON_THROW_ON_ERROR);
    }

    public function withProcessed(): self
    {
        return new self(
            $this->id, $this->aggregateType, $this->aggregateId, $this->eventType,
            $this->payload, $this->createdAt, $this->correlationId, $this->causationId,
            new \DateTimeImmutable(), $this->retryCount
        );
    }

    public function withRetryIncremented(): self
    {
        return new self(
            $this->id, $this->aggregateType, $this->aggregateId, $this->eventType,
            $this->payload, $this->createdAt, $this->correlationId, $this->causationId,
            $this->processedAt, $this->retryCount + 1
        );
    }
}
```

---

### OutboxRepositoryInterface

**File:** `src/Domain/Shared/Outbox/OutboxRepositoryInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Outbox;

interface OutboxRepositoryInterface
{
    public function save(OutboxMessage $message): void;

    /** @param array<OutboxMessage> $messages */
    public function saveAll(array $messages): void;

    /** @return array<OutboxMessage> */
    public function findUnprocessed(int $limit = 100): array;

    public function findById(string $id): ?OutboxMessage;

    public function markAsProcessed(string $id): void;

    public function incrementRetry(string $id): void;

    public function delete(string $id): void;

    public function countUnprocessed(): int;

    public function deleteProcessedBefore(\DateTimeImmutable $before): int;
}
```

---

## Application Layer Components

### MessagePublisherInterface

**File:** `src/Application/Shared/Port/Output/MessagePublisherInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Port\Output;

interface MessagePublisherInterface
{
    public function publish(
        string $routingKey,
        string $payload,
        array $headers = []
    ): void;
}
```

---

### DeadLetterRepositoryInterface

**File:** `src/Application/Shared/Port/Output/DeadLetterRepositoryInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Port\Output;

use Domain\Shared\Outbox\OutboxMessage;

interface DeadLetterRepositoryInterface
{
    public function store(OutboxMessage $message, \Throwable $error): void;
}
```

---

### ProcessingResult

**File:** `src/Application/Shared/Outbox/ProcessingResult.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Outbox;

final readonly class ProcessingResult
{
    public function __construct(
        public int $processed,
        public int $failed,
        public int $deadLettered
    ) {}

    public function total(): int
    {
        return $this->processed + $this->failed + $this->deadLettered;
    }

    public function hasFailures(): bool
    {
        return $this->failed > 0 || $this->deadLettered > 0;
    }
}
```

---

### MessageResult Enum

**File:** `src/Application/Shared/Outbox/MessageResult.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Outbox;

enum MessageResult
{
    case Processed;
    case Failed;
    case DeadLettered;
}
```

---

### OutboxProcessor

**File:** `src/Application/Shared/Outbox/OutboxProcessor.php`

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Outbox;

use Application\Shared\Port\Output\DeadLetterRepositoryInterface;
use Application\Shared\Port\Output\MessagePublisherInterface;
use Domain\Shared\Outbox\OutboxMessage;
use Domain\Shared\Outbox\OutboxRepositoryInterface;
use Psr\Log\LoggerInterface;

final readonly class OutboxProcessor
{
    private const MAX_RETRIES = 5;

    public function __construct(
        private OutboxRepositoryInterface $outbox,
        private MessagePublisherInterface $publisher,
        private DeadLetterRepositoryInterface $deadLetter,
        private LoggerInterface $logger
    ) {}

    public function process(int $batchSize = 100): ProcessingResult
    {
        $messages = $this->outbox->findUnprocessed($batchSize);
        $processed = 0;
        $failed = 0;
        $deadLettered = 0;

        foreach ($messages as $message) {
            $result = $this->processMessage($message);

            match ($result) {
                MessageResult::Processed => $processed++,
                MessageResult::Failed => $failed++,
                MessageResult::DeadLettered => $deadLettered++,
            };
        }

        return new ProcessingResult($processed, $failed, $deadLettered);
    }

    private function processMessage(OutboxMessage $message): MessageResult
    {
        try {
            $this->publisher->publish(
                routingKey: $message->eventType,
                payload: $message->payload,
                headers: [
                    'message_id' => $message->id,
                    'correlation_id' => $message->correlationId,
                    'causation_id' => $message->causationId,
                    'aggregate_type' => $message->aggregateType,
                    'aggregate_id' => $message->aggregateId,
                    'created_at' => $message->createdAt->format('c'),
                ]
            );

            $this->outbox->markAsProcessed($message->id);
            return MessageResult::Processed;
        } catch (\Throwable $e) {
            return $this->handleFailure($message, $e);
        }
    }

    private function handleFailure(OutboxMessage $message, \Throwable $error): MessageResult
    {
        if ($message->isPoisoned(self::MAX_RETRIES)) {
            $this->deadLetter->store($message, $error);
            $this->outbox->delete($message->id);
            return MessageResult::DeadLettered;
        }

        $this->outbox->incrementRetry($message->id);
        return MessageResult::Failed;
    }
}
```

---

## Infrastructure Layer

### DoctrineOutboxRepository

**File:** `src/Infrastructure/Persistence/Doctrine/Repository/DoctrineOutboxRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine\Repository;

use Doctrine\DBAL\Connection;
use Domain\Shared\Outbox\OutboxMessage;
use Domain\Shared\Outbox\OutboxRepositoryInterface;

final readonly class DoctrineOutboxRepository implements OutboxRepositoryInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function save(OutboxMessage $message): void
    {
        $this->connection->insert('outbox_messages', [
            'id' => $message->id,
            'aggregate_type' => $message->aggregateType,
            'aggregate_id' => $message->aggregateId,
            'event_type' => $message->eventType,
            'payload' => $message->payload,
            'created_at' => $message->createdAt->format('Y-m-d H:i:s.u'),
            'correlation_id' => $message->correlationId,
            'causation_id' => $message->causationId,
            'processed_at' => null,
            'retry_count' => 0,
        ]);
    }

    public function saveAll(array $messages): void
    {
        foreach ($messages as $message) {
            $this->save($message);
        }
    }

    public function findUnprocessed(int $limit = 100): array
    {
        $rows = $this->connection->fetchAllAssociative(
            'SELECT * FROM outbox_messages
             WHERE processed_at IS NULL
             ORDER BY created_at ASC
             LIMIT :limit',
            ['limit' => $limit],
            ['limit' => \PDO::PARAM_INT]
        );

        return array_map($this->hydrate(...), $rows);
    }

    public function findById(string $id): ?OutboxMessage
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM outbox_messages WHERE id = :id',
            ['id' => $id]
        );

        return $row ? $this->hydrate($row) : null;
    }

    public function markAsProcessed(string $id): void
    {
        $this->connection->update(
            'outbox_messages',
            ['processed_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s.u')],
            ['id' => $id]
        );
    }

    public function incrementRetry(string $id): void
    {
        $this->connection->executeStatement(
            'UPDATE outbox_messages SET retry_count = retry_count + 1 WHERE id = :id',
            ['id' => $id]
        );
    }

    public function delete(string $id): void
    {
        $this->connection->delete('outbox_messages', ['id' => $id]);
    }

    public function countUnprocessed(): int
    {
        return (int) $this->connection->fetchOne(
            'SELECT COUNT(*) FROM outbox_messages WHERE processed_at IS NULL'
        );
    }

    public function deleteProcessedBefore(\DateTimeImmutable $before): int
    {
        return $this->connection->executeStatement(
            'DELETE FROM outbox_messages WHERE processed_at < :before',
            ['before' => $before->format('Y-m-d H:i:s.u')]
        );
    }

    private function hydrate(array $row): OutboxMessage
    {
        return OutboxMessage::reconstitute(
            id: $row['id'],
            aggregateType: $row['aggregate_type'],
            aggregateId: $row['aggregate_id'],
            eventType: $row['event_type'],
            payload: $row['payload'],
            createdAt: new \DateTimeImmutable($row['created_at']),
            correlationId: $row['correlation_id'],
            causationId: $row['causation_id'],
            processedAt: $row['processed_at']
                ? new \DateTimeImmutable($row['processed_at'])
                : null,
            retryCount: (int) $row['retry_count']
        );
    }
}
```

---

### Console Command

**File:** `src/Infrastructure/Console/OutboxProcessCommand.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Application\Shared\Outbox\OutboxProcessor;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(
    name: 'outbox:process',
    description: 'Process pending outbox messages'
)]
final class OutboxProcessCommand extends Command
{
    public function __construct(
        private readonly OutboxProcessor $processor
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this
            ->addOption('batch-size', 'b', InputOption::VALUE_REQUIRED, 'Messages per batch', 100)
            ->addOption('daemon', 'd', InputOption::VALUE_NONE, 'Run as daemon')
            ->addOption('interval', 'i', InputOption::VALUE_REQUIRED, 'Poll interval (ms)', 1000);
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $batchSize = (int) $input->getOption('batch-size');
        $daemon = $input->getOption('daemon');
        $interval = (int) $input->getOption('interval');

        if ($daemon) {
            return $this->runDaemon($output, $batchSize, $interval);
        }

        return $this->runOnce($output, $batchSize);
    }

    private function runOnce(OutputInterface $output, int $batchSize): int
    {
        $result = $this->processor->process($batchSize);

        $output->writeln(sprintf(
            'Processed: %d, Failed: %d, Dead-lettered: %d',
            $result->processed,
            $result->failed,
            $result->deadLettered
        ));

        return Command::SUCCESS;
    }

    private function runDaemon(OutputInterface $output, int $batchSize, int $interval): int
    {
        $output->writeln('Starting outbox processor daemon...');

        while (true) {
            $result = $this->processor->process($batchSize);

            if ($result->total() > 0) {
                $output->writeln(sprintf(
                    '[%s] Processed: %d, Failed: %d, Dead-lettered: %d',
                    date('Y-m-d H:i:s'),
                    $result->processed,
                    $result->failed,
                    $result->deadLettered
                ));
            }

            usleep($interval * 1000);
        }
    }
}
```

---

### Database Migration

**File:** `migrations/Version*_CreateOutboxTable.php`

```php
<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20240101000000_CreateOutboxTable extends AbstractMigration
{
    public function up(Schema $schema): void
    {
        $this->addSql('
            CREATE TABLE outbox_messages (
                id VARCHAR(36) PRIMARY KEY,
                aggregate_type VARCHAR(255) NOT NULL,
                aggregate_id VARCHAR(255) NOT NULL,
                event_type VARCHAR(255) NOT NULL,
                payload JSONB NOT NULL,
                correlation_id VARCHAR(255),
                causation_id VARCHAR(255),
                created_at TIMESTAMP(6) NOT NULL,
                processed_at TIMESTAMP(6),
                retry_count INT NOT NULL DEFAULT 0
            )
        ');

        $this->addSql('
            CREATE INDEX idx_outbox_unprocessed
            ON outbox_messages (processed_at, created_at)
            WHERE processed_at IS NULL
        ');

        $this->addSql('
            CREATE INDEX idx_outbox_aggregate
            ON outbox_messages (aggregate_id, created_at)
        ');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE outbox_messages');
    }
}
```
