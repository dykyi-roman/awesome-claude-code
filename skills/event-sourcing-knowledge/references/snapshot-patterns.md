# Snapshot Patterns

Detailed patterns for Event Sourcing Snapshots in PHP.

## Snapshot Definition

### What is a Snapshot?

A cached state of an aggregate at a specific version, used to optimize loading performance by avoiding full event replay.

### When to Use Snapshots

| Scenario | Without Snapshot | With Snapshot |
|----------|------------------|---------------|
| 10 events | ~1ms load | ~1ms (no benefit) |
| 100 events | ~10ms load | ~2ms load |
| 1000 events | ~100ms load | ~5ms load |
| 10000 events | ~1s load | ~10ms load |

**Rule of thumb:** Consider snapshots when aggregates typically have 50+ events.

## PHP 8.4 Implementation

### Snapshot Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Snapshot;

interface SnapshotInterface
{
    public function aggregateId(): string;

    public function aggregateType(): string;

    public function version(): int;

    public function state(): array;

    public function createdAt(): DateTimeImmutable;
}
```

### Snapshot Value Object

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Snapshot;

final readonly class Snapshot implements SnapshotInterface
{
    public function __construct(
        private string $aggregateId,
        private string $aggregateType,
        private int $version,
        private array $state,
        private DateTimeImmutable $createdAt
    ) {}

    public function aggregateId(): string
    {
        return $this->aggregateId;
    }

    public function aggregateType(): string
    {
        return $this->aggregateType;
    }

    public function version(): int
    {
        return $this->version;
    }

    public function state(): array
    {
        return $this->state;
    }

    public function createdAt(): DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

### Snapshot Store Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Snapshot;

interface SnapshotStoreInterface
{
    /**
     * Get the latest snapshot for an aggregate.
     */
    public function get(string $aggregateId, string $aggregateType): ?SnapshotInterface;

    /**
     * Save a snapshot.
     */
    public function save(SnapshotInterface $snapshot): void;

    /**
     * Delete snapshots for an aggregate (useful when rebuilding).
     */
    public function delete(string $aggregateId, string $aggregateType): void;
}
```

### Database Snapshot Store

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Snapshot;

use Domain\Shared\Snapshot\SnapshotStoreInterface;
use Domain\Shared\Snapshot\SnapshotInterface;
use Domain\Shared\Snapshot\Snapshot;

final readonly class PostgresSnapshotStore implements SnapshotStoreInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function get(string $aggregateId, string $aggregateType): ?SnapshotInterface
    {
        $sql = <<<SQL
            SELECT aggregate_id, aggregate_type, version, state, created_at
            FROM snapshots
            WHERE aggregate_id = :aggregate_id
              AND aggregate_type = :aggregate_type
            ORDER BY version DESC
            LIMIT 1
        SQL;

        $row = $this->connection->fetchAssociative($sql, [
            'aggregate_id' => $aggregateId,
            'aggregate_type' => $aggregateType,
        ]);

        if ($row === false) {
            return null;
        }

        return new Snapshot(
            aggregateId: $row['aggregate_id'],
            aggregateType: $row['aggregate_type'],
            version: (int) $row['version'],
            state: json_decode($row['state'], true, 512, JSON_THROW_ON_ERROR),
            createdAt: new DateTimeImmutable($row['created_at'])
        );
    }

    public function save(SnapshotInterface $snapshot): void
    {
        $this->connection->executeStatement(
            <<<SQL
                INSERT INTO snapshots (aggregate_id, aggregate_type, version, state, created_at)
                VALUES (:aggregate_id, :aggregate_type, :version, :state, :created_at)
                ON CONFLICT (aggregate_id, aggregate_type)
                DO UPDATE SET version = :version, state = :state, created_at = :created_at
            SQL,
            [
                'aggregate_id' => $snapshot->aggregateId(),
                'aggregate_type' => $snapshot->aggregateType(),
                'version' => $snapshot->version(),
                'state' => json_encode($snapshot->state(), JSON_THROW_ON_ERROR),
                'created_at' => $snapshot->createdAt()->format('c'),
            ]
        );
    }

    public function delete(string $aggregateId, string $aggregateType): void
    {
        $this->connection->delete('snapshots', [
            'aggregate_id' => $aggregateId,
            'aggregate_type' => $aggregateType,
        ]);
    }
}
```

### Database Schema

```sql
CREATE TABLE snapshots (
    id BIGSERIAL PRIMARY KEY,
    aggregate_id VARCHAR(255) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    version INT NOT NULL,
    state JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL,

    UNIQUE (aggregate_id, aggregate_type)
);

CREATE INDEX idx_snapshots_aggregate ON snapshots(aggregate_id, aggregate_type);
```

## Aggregate with Snapshot Support

### Snapshotable Aggregate Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Aggregate;

interface SnapshotableInterface
{
    /**
     * Create snapshot state from current aggregate state.
     */
    public function toSnapshot(): array;

    /**
     * Restore aggregate state from snapshot.
     */
    public static function fromSnapshot(string $id, array $state, int $version): static;

    /**
     * Get aggregate type name for snapshot store.
     */
    public static function aggregateType(): string;
}
```

### Event-Sourced Aggregate with Snapshots

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Shared\Aggregate\EventSourcedAggregate;
use Domain\Shared\Aggregate\SnapshotableInterface;

final class Order extends EventSourcedAggregate implements SnapshotableInterface
{
    private OrderId $id;
    private CustomerId $customerId;
    private OrderStatus $status;
    private Money $total;
    /** @var array<OrderLine> */
    private array $lines = [];

    public static function aggregateType(): string
    {
        return 'order';
    }

    public function toSnapshot(): array
    {
        return [
            'id' => $this->id->value,
            'customer_id' => $this->customerId->value,
            'status' => $this->status->value,
            'total_cents' => $this->total->cents(),
            'total_currency' => $this->total->currency(),
            'lines' => array_map(
                fn (OrderLine $line) => $line->toArray(),
                $this->lines
            ),
        ];
    }

    public static function fromSnapshot(string $id, array $state, int $version): static
    {
        $order = new self();
        $order->id = new OrderId($state['id']);
        $order->customerId = new CustomerId($state['customer_id']);
        $order->status = OrderStatus::from($state['status']);
        $order->total = new Money($state['total_cents'], $state['total_currency']);
        $order->lines = array_map(
            fn (array $lineData) => OrderLine::fromArray($lineData),
            $state['lines']
        );
        $order->version = $version;

        return $order;
    }

    // Regular event-sourced methods...
    public static function create(OrderId $id, CustomerId $customerId): self
    {
        $order = new self();
        $order->recordThat(new OrderCreatedEvent(
            orderId: $id->value,
            customerId: $customerId->value,
            createdAt: new DateTimeImmutable()
        ));
        return $order;
    }

    protected function applyOrderCreatedEvent(OrderCreatedEvent $event): void
    {
        $this->id = new OrderId($event->orderId);
        $this->customerId = new CustomerId($event->customerId);
        $this->status = OrderStatus::Draft;
        $this->total = Money::zero('USD');
    }
}
```

## Repository with Snapshot Support

### Snapshot-Enabled Repository

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Shared\EventStore\EventStoreInterface;
use Domain\Shared\Snapshot\SnapshotStoreInterface;
use Domain\Shared\Snapshot\Snapshot;

final readonly class EventSourcedOrderRepository implements OrderRepositoryInterface
{
    private const SNAPSHOT_THRESHOLD = 50;

    public function __construct(
        private EventStoreInterface $eventStore,
        private SnapshotStoreInterface $snapshotStore
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $streamId = $this->streamId($id);

        // Try to load from snapshot first
        $snapshot = $this->snapshotStore->get($id->value, Order::aggregateType());

        if ($snapshot !== null) {
            // Restore from snapshot
            $order = Order::fromSnapshot($id->value, $snapshot->state(), $snapshot->version());

            // Load only events after snapshot
            $events = $this->eventStore->loadFromVersion($streamId, $snapshot->version());
        } else {
            // No snapshot, load all events
            $events = $this->eventStore->load($streamId);

            if (empty($events)) {
                return null;
            }

            $order = Order::reconstitute($id, $events);
        }

        // Apply remaining events
        foreach ($events as $event) {
            $order->apply($event);
        }

        return $order;
    }

    public function save(Order $order): void
    {
        $streamId = $this->streamId($order->id());
        $uncommittedEvents = $order->uncommittedEvents();

        if (empty($uncommittedEvents)) {
            return;
        }

        $previousVersion = $order->version() - count($uncommittedEvents);

        $this->eventStore->append($streamId, $uncommittedEvents, $previousVersion);

        $order->markEventsAsCommitted();

        // Create snapshot if threshold reached
        $this->maybeCreateSnapshot($order);
    }

    private function maybeCreateSnapshot(Order $order): void
    {
        // Check if we should create a snapshot
        $currentSnapshot = $this->snapshotStore->get($order->id()->value, Order::aggregateType());
        $lastSnapshotVersion = $currentSnapshot?->version() ?? 0;

        $eventsSinceSnapshot = $order->version() - $lastSnapshotVersion;

        if ($eventsSinceSnapshot >= self::SNAPSHOT_THRESHOLD) {
            $snapshot = new Snapshot(
                aggregateId: $order->id()->value,
                aggregateType: Order::aggregateType(),
                version: $order->version(),
                state: $order->toSnapshot(),
                createdAt: new DateTimeImmutable()
            );

            $this->snapshotStore->save($snapshot);
        }
    }

    private function streamId(OrderId $id): string
    {
        return 'order-' . $id->value;
    }
}
```

## Snapshot Strategies

### Strategy 1: Periodic (Every N Events)

```php
private function shouldSnapshot(int $currentVersion, int $lastSnapshotVersion): bool
{
    return ($currentVersion - $lastSnapshotVersion) >= self::SNAPSHOT_THRESHOLD;
}
```

### Strategy 2: Time-Based

```php
private function shouldSnapshot(SnapshotInterface $lastSnapshot): bool
{
    $hoursSinceLastSnapshot = (time() - $lastSnapshot->createdAt()->getTimestamp()) / 3600;
    return $hoursSinceLastSnapshot >= 24; // Daily snapshots
}
```

### Strategy 3: On-Demand (Background Process)

```php
final class SnapshotCreator
{
    public function createSnapshotsForAggregatesNeedingThem(): void
    {
        $aggregateIds = $this->findAggregatesNeedingSnapshots();

        foreach ($aggregateIds as $aggregateId) {
            $aggregate = $this->repository->findById($aggregateId);
            $this->createSnapshot($aggregate);
        }
    }

    private function findAggregatesNeedingSnapshots(): array
    {
        // Find aggregates with many events since last snapshot
        $sql = <<<SQL
            SELECT DISTINCT e.stream_id, COUNT(*) as event_count
            FROM event_store e
            LEFT JOIN snapshots s ON s.aggregate_id = SPLIT_PART(e.stream_id, '-', 2)
            WHERE e.version > COALESCE(s.version, 0)
            GROUP BY e.stream_id
            HAVING COUNT(*) > :threshold
        SQL;

        return $this->connection->fetchAllAssociative($sql, [
            'threshold' => self::SNAPSHOT_THRESHOLD,
        ]);
    }
}
```

## Snapshot Invalidation

### When to Invalidate Snapshots

1. **Code changes** that affect state serialization
2. **Bug fixes** in event application logic
3. **Data migrations** that affect aggregate state

### Invalidation Strategy

```php
final class SnapshotInvalidator
{
    public function invalidateAll(string $aggregateType): void
    {
        $this->connection->delete('snapshots', ['aggregate_type' => $aggregateType]);
    }

    public function invalidateByVersion(string $aggregateType, int $beforeVersion): void
    {
        $this->connection->executeStatement(
            'DELETE FROM snapshots WHERE aggregate_type = :type AND version < :version',
            ['type' => $aggregateType, 'version' => $beforeVersion]
        );
    }
}
```

## Detection Patterns

```bash
# Find snapshot store
Grep: "interface.*SnapshotStore|class.*SnapshotStore" --glob "**/*.php"

# Find snapshotable aggregates
Grep: "implements.*Snapshotable|toSnapshot|fromSnapshot" --glob "**/*.php"

# Check for snapshot loading in repository
Grep: "snapshotStore->get|loadFromVersion" --glob "**/Repository/**/*.php"

# Check for snapshot threshold
Grep: "SNAPSHOT_THRESHOLD|shouldSnapshot" --glob "**/*.php"

# Check for snapshot creation
Grep: "snapshotStore->save|maybeCreateSnapshot" --glob "**/*.php"
```

## Performance Considerations

### Snapshot Size

Keep snapshots small by excluding:
- Computed values that can be recalculated
- References to other aggregates (store IDs only)
- Transient state

```php
public function toSnapshot(): array
{
    return [
        'id' => $this->id->value,
        'status' => $this->status->value,
        // Include essential state
        'line_count' => count($this->lines),
        'lines' => array_map(fn ($l) => $l->toCompactArray(), $this->lines),
        // Exclude computed values
        // 'total' => $this->total->cents(),  // Can be recalculated
    ];
}
```

### Memory Efficiency

For aggregates with large collections, consider partial snapshots:

```php
public function toSnapshot(): array
{
    return [
        'id' => $this->id->value,
        'status' => $this->status->value,
        // Store only IDs for large collections
        'line_ids' => array_map(fn ($l) => $l->id()->value, $this->lines),
    ];
}

// Lazy load lines when needed
public function lines(): array
{
    if ($this->linesLoaded === false) {
        $this->lines = $this->lineRepository->findByIds($this->lineIds);
        $this->linesLoaded = true;
    }
    return $this->lines;
}
```
