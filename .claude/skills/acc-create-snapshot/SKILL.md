---
name: acc-create-snapshot
description: Generates Snapshot pattern for PHP 8.5. Creates aggregate snapshot infrastructure for event sourcing performance optimization with configurable strategies and version tracking. Includes unit tests.
---

# Snapshot Generator

Creates Snapshot infrastructure for optimizing event sourcing aggregate rebuilds.

## When to Use

| Scenario | Example |
|----------|---------|
| Long event streams | Aggregates with 100+ events in their history |
| Slow aggregate rebuild | Event replay taking too long for read operations |
| Frequent reads | Aggregates loaded many times per second |
| Large aggregates | Complex state requiring many events to reconstruct |

## Component Characteristics

### Snapshot
- Immutable state capture of an aggregate at a point in time
- Properties: aggregateId, aggregateType, version, state (JSON), createdAt
- Supports `fromArray()` / `toArray()` for serialization
- Version must be >= 1

### SnapshotStoreInterface
- `save(Snapshot $snapshot): void` — persist snapshot (upsert)
- `load(string $aggregateId): ?Snapshot` — retrieve latest snapshot
- `delete(string $aggregateId): void` — remove all snapshots for aggregate

### SnapshotStrategy
- Configurable event threshold (default: 100)
- `shouldTakeSnapshot(int $eventsSinceLastSnapshot): bool`
- Determines when a new snapshot should be captured

### AggregateSnapshotter
- Application service coordinating snapshot operations
- Loads aggregate from snapshot + remaining events
- Takes snapshots when strategy threshold is met

---

## Generation Process

### Step 1: Generate Domain Components

**Path:** `src/Domain/{BC}/Snapshot/`

1. `Snapshot.php` — Immutable snapshot value object
2. `SnapshotStoreInterface.php` — Repository interface for snapshot persistence

### Step 2: Generate Application Components

**Path:** `src/Application/{BC}/Snapshot/`

1. `SnapshotStrategy.php` — Configurable threshold strategy
2. `AggregateSnapshotter.php` — Application service for snapshot operations

### Step 3: Generate Infrastructure Components

**Path:** `src/Infrastructure/{BC}/Snapshot/`

1. `DoctrineSnapshotStore.php` — Doctrine DBAL implementation of SnapshotStoreInterface
2. Database migration SQL for snapshots table

### Step 4: Generate Tests

1. `SnapshotTest.php` — Construction, serialization, validation tests
2. `SnapshotStrategyTest.php` — Threshold behavior tests
3. `AggregateSnapshotterTest.php` — Load and take snapshot tests

---

## File Placement

| Component | Path |
|-----------|------|
| Snapshot, SnapshotStoreInterface | `src/Domain/{BC}/Snapshot/` |
| SnapshotStrategy, AggregateSnapshotter | `src/Application/{BC}/Snapshot/` |
| DoctrineSnapshotStore | `src/Infrastructure/{BC}/Snapshot/` |
| Unit Tests | `tests/Unit/Domain/{BC}/Snapshot/`, `tests/Unit/Application/{BC}/Snapshot/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Value Object | `Snapshot` | `Snapshot` |
| Store Interface | `SnapshotStoreInterface` | `SnapshotStoreInterface` |
| Strategy | `SnapshotStrategy` | `SnapshotStrategy` |
| Application Service | `AggregateSnapshotter` | `AggregateSnapshotter` |
| Infrastructure Store | `DoctrineSnapshotStore` | `DoctrineSnapshotStore` |
| Test | `{ClassName}Test` | `SnapshotTest` |

---

## Quick Template Reference

### Snapshot

```php
final readonly class Snapshot
{
    public function __construct(
        public string $aggregateId,
        public string $aggregateType,
        public int $version,
        public string $state,
        public \DateTimeImmutable $createdAt
    ) {
        // version >= 1 validation
    }

    public static function fromArray(array $data): self;
    public function toArray(): array;
}
```

### SnapshotStoreInterface

```php
interface SnapshotStoreInterface
{
    public function save(Snapshot $snapshot): void;
    public function load(string $aggregateId): ?Snapshot;
    public function delete(string $aggregateId): void;
}
```

### SnapshotStrategy

```php
final readonly class SnapshotStrategy
{
    public function __construct(
        private int $eventThreshold = 100
    ) {}

    public function shouldTakeSnapshot(int $eventsSinceLastSnapshot): bool;
}
```

---

## Usage Example

```php
$snapshotter = new AggregateSnapshotter($snapshotStore, $strategy);

// Load aggregate from snapshot + remaining events
$result = $snapshotter->loadWithSnapshot($aggregateId, $eventStore);
$snapshot = $result['snapshot'];
$remainingEvents = $result['remainingEvents'];

$aggregate = $snapshot !== null
    ? Order::fromSnapshot($snapshot)
    : new Order($aggregateId);

foreach ($remainingEvents as $event) {
    $aggregate->apply($event);
}

// Take snapshot if threshold reached
$snapshotter->takeSnapshotIfNeeded(
    aggregateId: $aggregateId,
    aggregateType: 'Order',
    version: $aggregate->getVersion(),
    state: $aggregate->toSnapshot(),
    eventsSinceSnapshot: count($remainingEvents)
);
```

---

## Database Schema

```sql
CREATE TABLE snapshots (
    id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    aggregate_id VARCHAR(36) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    version INT UNSIGNED NOT NULL,
    state JSON NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_snapshots_aggregate_id (aggregate_id),
    INDEX idx_snapshots_aggregate_type (aggregate_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Snapshot Every Event | Storage bloat, no performance gain | Use threshold strategy (e.g., every 100 events) |
| Mutable Snapshots | State corruption, debugging nightmares | Make Snapshot immutable (final readonly) |
| Missing Version | Cannot determine event replay start point | Always track version in snapshot |
| No Cleanup | Unbounded storage growth | Implement retention policy, keep only latest |
| Tight Coupling | Snapshot tied to infrastructure | Domain interface, infrastructure implementation |
| Skipping Validation | Invalid snapshots persisted | Validate version >= 1, non-empty state |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Snapshot, SnapshotStoreInterface, SnapshotStrategy, AggregateSnapshotter, DoctrineSnapshotStore templates
- `references/examples.md` — OrderAggregate integration, event sourcing examples and tests
