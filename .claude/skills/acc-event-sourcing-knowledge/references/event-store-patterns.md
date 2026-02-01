# Event Store Patterns

Detailed patterns for Event Store implementation in PHP.

## Event Store Definition

### What is an Event Store?

An append-only database optimized for storing and retrieving domain events.

### Core Requirements

| Requirement | Description |
|-------------|-------------|
| **Append-only** | Events can only be added, never modified or deleted |
| **Ordered** | Events within a stream maintain order |
| **Immutable** | Stored events never change |
| **Atomic writes** | All events from one command committed together |
| **Optimistic concurrency** | Detect concurrent modifications |
| **Stream-based** | Events grouped into streams (per aggregate) |

## PHP 8.5 Implementation

### Event Store Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\EventStore;

interface EventStoreInterface
{
    /**
     * Append events to a stream.
     *
     * @param string $streamId Aggregate ID
     * @param array<DomainEvent> $events Events to append
     * @param int $expectedVersion Expected stream version for optimistic concurrency
     * @throws ConcurrencyException When expectedVersion doesn't match
     */
    public function append(string $streamId, array $events, int $expectedVersion): void;

    /**
     * Load all events for a stream.
     *
     * @param string $streamId Aggregate ID
     * @return array<DomainEvent>
     */
    public function load(string $streamId): array;

    /**
     * Load events for a stream from a specific version.
     *
     * @param string $streamId Aggregate ID
     * @param int $fromVersion Starting version (exclusive)
     * @return array<DomainEvent>
     */
    public function loadFromVersion(string $streamId, int $fromVersion): array;

    /**
     * Get current stream version.
     *
     * @param string $streamId Aggregate ID
     * @return int Current version (0 if stream doesn't exist)
     */
    public function getVersion(string $streamId): int;
}
```

### Stored Event Structure

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

final readonly class StoredEvent
{
    public function __construct(
        public string $eventId,
        public string $streamId,
        public int $version,
        public string $eventType,
        public string $payload,          // JSON encoded event data
        public string $metadata,         // JSON encoded metadata
        public DateTimeImmutable $occurredAt,
        public ?int $globalPosition = null
    ) {}
}
```

### Database Schema

```sql
CREATE TABLE event_store (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    stream_id VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSONB NOT NULL,
    metadata JSONB NOT NULL,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE (stream_id, version)
);

CREATE INDEX idx_event_store_stream_id ON event_store(stream_id);
CREATE INDEX idx_event_store_event_type ON event_store(event_type);
CREATE INDEX idx_event_store_occurred_at ON event_store(occurred_at);
```

### PostgreSQL Event Store Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

use Domain\Shared\EventStore\EventStoreInterface;
use Domain\Shared\Event\DomainEvent;

final readonly class PostgresEventStore implements EventStoreInterface
{
    public function __construct(
        private Connection $connection,
        private EventSerializer $serializer
    ) {}

    public function append(string $streamId, array $events, int $expectedVersion): void
    {
        $this->connection->transactional(function () use ($streamId, $events, $expectedVersion) {
            // Check current version (with row lock)
            $currentVersion = $this->getVersionForUpdate($streamId);

            if ($currentVersion !== $expectedVersion) {
                throw new ConcurrencyException(
                    "Expected version {$expectedVersion}, got {$currentVersion}"
                );
            }

            $version = $expectedVersion;
            foreach ($events as $event) {
                $version++;
                $this->insertEvent($streamId, $event, $version);
            }
        });
    }

    public function load(string $streamId): array
    {
        $sql = <<<SQL
            SELECT event_id, stream_id, version, event_type, payload, metadata, occurred_at
            FROM event_store
            WHERE stream_id = :stream_id
            ORDER BY version ASC
        SQL;

        $rows = $this->connection->fetchAllAssociative($sql, ['stream_id' => $streamId]);

        return array_map(
            fn (array $row) => $this->serializer->deserialize($row),
            $rows
        );
    }

    public function loadFromVersion(string $streamId, int $fromVersion): array
    {
        $sql = <<<SQL
            SELECT event_id, stream_id, version, event_type, payload, metadata, occurred_at
            FROM event_store
            WHERE stream_id = :stream_id AND version > :from_version
            ORDER BY version ASC
        SQL;

        $rows = $this->connection->fetchAllAssociative($sql, [
            'stream_id' => $streamId,
            'from_version' => $fromVersion,
        ]);

        return array_map(
            fn (array $row) => $this->serializer->deserialize($row),
            $rows
        );
    }

    public function getVersion(string $streamId): int
    {
        $sql = 'SELECT COALESCE(MAX(version), 0) FROM event_store WHERE stream_id = :stream_id';

        return (int) $this->connection->fetchOne($sql, ['stream_id' => $streamId]);
    }

    private function getVersionForUpdate(string $streamId): int
    {
        $sql = <<<SQL
            SELECT COALESCE(MAX(version), 0)
            FROM event_store
            WHERE stream_id = :stream_id
            FOR UPDATE
        SQL;

        return (int) $this->connection->fetchOne($sql, ['stream_id' => $streamId]);
    }

    private function insertEvent(string $streamId, DomainEvent $event, int $version): void
    {
        $serialized = $this->serializer->serialize($event);

        $this->connection->insert('event_store', [
            'event_id' => $event->metadata()->eventId,
            'stream_id' => $streamId,
            'version' => $version,
            'event_type' => $serialized['type'],
            'payload' => $serialized['payload'],
            'metadata' => $serialized['metadata'],
            'occurred_at' => $event->metadata()->occurredAt->format('c'),
        ]);
    }
}
```

### Event Serializer

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

use Domain\Shared\Event\DomainEvent;

final readonly class EventSerializer
{
    public function __construct(
        private EventTypeRegistry $typeRegistry
    ) {}

    public function serialize(DomainEvent $event): array
    {
        return [
            'type' => $this->typeRegistry->getTypeName($event::class),
            'payload' => json_encode($this->extractPayload($event), JSON_THROW_ON_ERROR),
            'metadata' => json_encode($this->extractMetadata($event), JSON_THROW_ON_ERROR),
        ];
    }

    public function deserialize(array $row): DomainEvent
    {
        $className = $this->typeRegistry->getClassName($row['event_type']);
        $payload = json_decode($row['payload'], true, 512, JSON_THROW_ON_ERROR);
        $metadata = json_decode($row['metadata'], true, 512, JSON_THROW_ON_ERROR);

        return $this->hydrate($className, $payload, $metadata);
    }

    private function extractPayload(DomainEvent $event): array
    {
        $reflection = new \ReflectionClass($event);
        $payload = [];

        foreach ($reflection->getProperties() as $property) {
            $name = $property->getName();
            if ($name === 'metadata') {
                continue;
            }
            $payload[$name] = $this->serializeValue($property->getValue($event));
        }

        return $payload;
    }

    private function serializeValue(mixed $value): mixed
    {
        if ($value instanceof \DateTimeInterface) {
            return $value->format('c');
        }
        if ($value instanceof \BackedEnum) {
            return $value->value;
        }
        if (is_object($value) && method_exists($value, 'toArray')) {
            return $value->toArray();
        }
        return $value;
    }
}
```

## Stream Patterns

### Stream Naming Conventions

```php
// Pattern: {aggregate_type}-{aggregate_id}
// Examples:
"order-550e8400-e29b-41d4-a716-446655440000"
"customer-123e4567-e89b-12d3-a456-426614174000"
"inventory-item-987fcdeb-51a2-43e8-b8d6-789012345678"
```

### Category Streams

For projections that need events from multiple aggregates:

```php
interface EventStoreInterface
{
    /**
     * Load events from all streams of a category.
     *
     * @param string $category Stream prefix (e.g., "order")
     * @param int $fromPosition Global position to start from
     * @param int $limit Maximum events to return
     * @return array<StoredEvent>
     */
    public function loadByCategory(string $category, int $fromPosition, int $limit): array;
}

// Implementation
public function loadByCategory(string $category, int $fromPosition, int $limit): array
{
    $sql = <<<SQL
        SELECT *
        FROM event_store
        WHERE stream_id LIKE :category
          AND id > :from_position
        ORDER BY id ASC
        LIMIT :limit
    SQL;

    return $this->connection->fetchAllAssociative($sql, [
        'category' => $category . '-%',
        'from_position' => $fromPosition,
        'limit' => $limit,
    ]);
}
```

### All Stream

For rebuilding all projections:

```php
interface EventStoreInterface
{
    /**
     * Load all events across all streams.
     *
     * @param int $fromPosition Global position to start from
     * @param int $limit Maximum events to return
     * @return array<StoredEvent>
     */
    public function loadAll(int $fromPosition, int $limit): array;
}
```

## Optimistic Concurrency

### Why It's Needed

Prevent lost updates when two processes try to modify the same aggregate.

```
Process A:                          Process B:
1. Load Order (version 5)           1. Load Order (version 5)
2. Add item                         2. Add item
3. Save (expect version 5)          3. Save (expect version 5)
   ✓ Success (now version 6)           ✗ ConcurrencyException!
```

### Implementation

```php
public function append(string $streamId, array $events, int $expectedVersion): void
{
    try {
        $this->connection->transactional(function () use ($streamId, $events, $expectedVersion) {
            // PostgreSQL: Use unique constraint on (stream_id, version)
            $version = $expectedVersion;
            foreach ($events as $event) {
                $version++;
                $this->insertEvent($streamId, $event, $version);
            }
        });
    } catch (UniqueConstraintViolationException $e) {
        throw new ConcurrencyException(
            "Concurrent modification detected for stream {$streamId}",
            previous: $e
        );
    }
}
```

### Retry Strategy

```php
final readonly class RetryingEventStore implements EventStoreInterface
{
    private const MAX_RETRIES = 3;

    public function __construct(
        private EventStoreInterface $inner,
        private AggregateRepositoryInterface $repository
    ) {}

    public function appendWithRetry(string $streamId, callable $action): void
    {
        for ($attempt = 1; $attempt <= self::MAX_RETRIES; $attempt++) {
            try {
                $aggregate = $this->repository->load($streamId);
                $action($aggregate);
                $this->inner->append(
                    $streamId,
                    $aggregate->uncommittedEvents(),
                    $aggregate->version()
                );
                return;
            } catch (ConcurrencyException $e) {
                if ($attempt === self::MAX_RETRIES) {
                    throw $e;
                }
                // Retry with fresh state
            }
        }
    }
}
```

## Event Store Repository

### Repository Using Event Store

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;

final readonly class EventSourcedOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EventStoreInterface $eventStore,
        private SnapshotStoreInterface $snapshotStore
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $streamId = $this->streamId($id);
        $events = $this->eventStore->load($streamId);

        if (empty($events)) {
            return null;
        }

        return Order::reconstitute($id, $events);
    }

    public function save(Order $order): void
    {
        $streamId = $this->streamId($order->id());
        $uncommittedEvents = $order->uncommittedEvents();

        if (empty($uncommittedEvents)) {
            return;
        }

        $this->eventStore->append(
            $streamId,
            $uncommittedEvents,
            $order->version() - count($uncommittedEvents)
        );

        $order->markEventsAsCommitted();
    }

    private function streamId(OrderId $id): string
    {
        return 'order-' . $id->value;
    }
}
```

## Detection Patterns

```bash
# Check for Event Store interface
Grep: "interface.*EventStore" --glob "**/*.php"

# Check for append-only operations
Grep: "function append|function save.*Event" --glob "**/EventStore*.php"

# Warning: Update/Delete in Event Store
Grep: "UPDATE event_store|DELETE FROM event_store" --glob "**/*.php"
Grep: "->update\(|->delete\(" --glob "**/EventStore*.php"

# Check for optimistic concurrency
Grep: "expectedVersion|ConcurrencyException" --glob "**/EventStore*.php"

# Check for stream-based storage
Grep: "streamId|stream_id" --glob "**/EventStore*.php"
```
