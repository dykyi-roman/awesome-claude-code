# Outbox Pattern Implementation Strategies

## Overview

The Transactional Outbox pattern ensures reliable message publishing by storing messages in the same database transaction as domain changes.

## Publishing Strategies

### 1. Polling Publisher

Most common approach. A background process periodically queries the outbox table.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox;

use Application\Shared\Outbox\OutboxPublisher;
use Psr\Log\LoggerInterface;

final readonly class OutboxPollingWorker
{
    public function __construct(
        private OutboxPublisher $publisher,
        private LoggerInterface $logger,
        private int $pollIntervalMs = 1000,
        private int $batchSize = 100
    ) {}

    public function run(): never
    {
        $this->logger->info('Outbox polling worker started');

        while (true) {
            try {
                $processed = $this->publisher->processOutbox($this->batchSize);

                if ($processed > 0) {
                    $this->logger->info("Processed {$processed} outbox messages");
                }
            } catch (\Throwable $e) {
                $this->logger->error('Outbox processing failed', [
                    'exception' => $e->getMessage(),
                ]);
            }

            usleep($this->pollIntervalMs * 1000);
        }
    }
}
```

**Pros:**
- Simple implementation
- Works with any database
- Easy to monitor and debug

**Cons:**
- Polling latency (configurable)
- Database load from frequent queries
- Ordering requires additional logic

### 2. Transaction Log Tailing (CDC)

Uses Change Data Capture to stream database changes. Debezium is the most popular tool.

```yaml
# Debezium connector configuration
name: outbox-connector
config:
  connector.class: io.debezium.connector.postgresql.PostgresConnector
  database.hostname: postgres
  database.port: 5432
  database.user: app
  database.dbname: myapp
  table.include.list: public.outbox_messages
  transforms: outbox
  transforms.outbox.type: io.debezium.transforms.outbox.EventRouter
  transforms.outbox.table.field.event.key: aggregate_id
  transforms.outbox.table.field.event.payload: payload
  transforms.outbox.route.by.field: event_type
```

**Pros:**
- Near real-time publishing
- No polling overhead
- Guaranteed ordering

**Cons:**
- Additional infrastructure (Debezium, Kafka Connect)
- More complex setup and operations
- Database-specific configuration

### 3. Listen/Notify (PostgreSQL)

Uses PostgreSQL LISTEN/NOTIFY for immediate notification.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox;

final readonly class PostgresNotifyOutboxTrigger
{
    public function createTriggerSQL(): string
    {
        return <<<SQL
            CREATE OR REPLACE FUNCTION notify_outbox_insert()
            RETURNS TRIGGER AS $$
            BEGIN
                PERFORM pg_notify('outbox_channel', NEW.id::text);
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            CREATE TRIGGER outbox_insert_trigger
            AFTER INSERT ON outbox_messages
            FOR EACH ROW
            EXECUTE FUNCTION notify_outbox_insert();
        SQL;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox;

final readonly class PostgresListenWorker
{
    public function __construct(
        private \PDO $connection,
        private OutboxPublisher $publisher
    ) {}

    public function run(): never
    {
        $this->connection->exec('LISTEN outbox_channel');

        while (true) {
            $result = $this->connection->pgsqlGetNotify(PDO::FETCH_ASSOC, 10000);

            if ($result) {
                $this->publisher->processMessage($result['payload']);
            }
        }
    }
}
```

## Ordering Guarantees

### Per-Aggregate Ordering

Events for the same aggregate must be processed in order.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox;

final readonly class OrderedOutboxProcessor
{
    public function __construct(
        private OutboxRepositoryInterface $outbox,
        private EventPublisherInterface $publisher
    ) {}

    public function processWithOrdering(int $batchSize = 100): void
    {
        // Group by aggregate, process oldest first per aggregate
        $messages = $this->outbox->findUnprocessedGroupedByAggregate($batchSize);

        foreach ($messages as $aggregateId => $aggregateMessages) {
            // Process in order for this aggregate
            usort($aggregateMessages, fn($a, $b) =>
                $a->createdAt <=> $b->createdAt
            );

            foreach ($aggregateMessages as $message) {
                if (!$this->tryProcess($message)) {
                    // Stop processing this aggregate on failure
                    break;
                }
            }
        }
    }

    private function tryProcess(OutboxMessage $message): bool
    {
        try {
            $this->publisher->publish($message);
            $this->outbox->markAsProcessed($message->id);
            return true;
        } catch (\Throwable) {
            $this->outbox->incrementRetry($message->id);
            return false;
        }
    }
}
```

### Partitioned Publishing

For high-throughput scenarios, partition by aggregate ID.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox;

final readonly class PartitionedOutboxWorker
{
    public function __construct(
        private int $partitionCount,
        private int $currentPartition
    ) {}

    public function getPartitionCondition(string $aggregateId): int
    {
        return abs(crc32($aggregateId)) % $this->partitionCount;
    }

    public function shouldProcess(string $aggregateId): bool
    {
        return $this->getPartitionCondition($aggregateId) === $this->currentPartition;
    }
}
```

## Cleanup Strategies

### Immediate Deletion

Delete after successful processing (simplest).

```php
public function markAsProcessed(string $id): void
{
    $this->connection->delete('outbox_messages', ['id' => $id]);
}
```

### Soft Delete with TTL

Mark as processed, delete later.

```php
public function markAsProcessed(string $id): void
{
    $this->connection->update(
        'outbox_messages',
        ['processed_at' => new \DateTimeImmutable()],
        ['id' => $id]
    );
}

public function cleanupOld(\DateInterval $retention): int
{
    $cutoff = (new \DateTimeImmutable())->sub($retention);
    return $this->connection->delete(
        'outbox_messages',
        'processed_at < :cutoff',
        ['cutoff' => $cutoff]
    );
}
```

### Archive Strategy

Move to archive table for audit/debugging.

```sql
INSERT INTO outbox_messages_archive
SELECT * FROM outbox_messages
WHERE processed_at < NOW() - INTERVAL '7 days';

DELETE FROM outbox_messages
WHERE processed_at < NOW() - INTERVAL '7 days';
```

## Monitoring

### Key Metrics

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Outbox\Monitoring;

final readonly class OutboxMetrics
{
    public function __construct(
        private \PDO $connection,
        private MetricsCollectorInterface $metrics
    ) {}

    public function collect(): void
    {
        // Unprocessed count
        $stmt = $this->connection->query(
            'SELECT COUNT(*) FROM outbox_messages WHERE processed_at IS NULL'
        );
        $this->metrics->gauge('outbox_unprocessed_count', $stmt->fetchColumn());

        // Oldest unprocessed age
        $stmt = $this->connection->query(
            'SELECT EXTRACT(EPOCH FROM NOW() - MIN(created_at))
             FROM outbox_messages WHERE processed_at IS NULL'
        );
        $this->metrics->gauge('outbox_oldest_age_seconds', $stmt->fetchColumn() ?? 0);

        // High retry count
        $stmt = $this->connection->query(
            'SELECT COUNT(*) FROM outbox_messages
             WHERE processed_at IS NULL AND retry_count > 0'
        );
        $this->metrics->gauge('outbox_retry_count', $stmt->fetchColumn());
    }
}
```

### Alerts

- **Unprocessed count growing**: Worker may be down
- **Old messages not processed**: Publishing failures
- **High retry count**: Poison messages or broker issues
