# Snapshot Pattern Templates

## Snapshot

**File:** `src/Domain/{BC}/Snapshot/Snapshot.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BC}\Snapshot;

final readonly class Snapshot
{
    public function __construct(
        public string $aggregateId,
        public string $aggregateType,
        public int $version,
        public string $state,
        public \DateTimeImmutable $createdAt
    ) {
        if ($this->version < 1) {
            throw new \InvalidArgumentException('Snapshot version must be at least 1');
        }
    }

    /**
     * @param array{
     *     aggregate_id: string,
     *     aggregate_type: string,
     *     version: int,
     *     state: string,
     *     created_at: string
     * } $data
     */
    public static function fromArray(array $data): self
    {
        return new self(
            aggregateId: $data['aggregate_id'],
            aggregateType: $data['aggregate_type'],
            version: (int) $data['version'],
            state: $data['state'],
            createdAt: new \DateTimeImmutable($data['created_at'])
        );
    }

    /**
     * @return array{
     *     aggregate_id: string,
     *     aggregate_type: string,
     *     version: int,
     *     state: string,
     *     created_at: string
     * }
     */
    public function toArray(): array
    {
        return [
            'aggregate_id' => $this->aggregateId,
            'aggregate_type' => $this->aggregateType,
            'version' => $this->version,
            'state' => $this->state,
            'created_at' => $this->createdAt->format('Y-m-d H:i:s'),
        ];
    }
}
```

---

## SnapshotStoreInterface

**File:** `src/Domain/{BC}/Snapshot/SnapshotStoreInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BC}\Snapshot;

interface SnapshotStoreInterface
{
    public function save(Snapshot $snapshot): void;

    public function load(string $aggregateId): ?Snapshot;

    public function delete(string $aggregateId): void;
}
```

---

## SnapshotStrategy

**File:** `src/Application/{BC}/Snapshot/SnapshotStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BC}\Snapshot;

final readonly class SnapshotStrategy
{
    public function __construct(
        private int $eventThreshold = 100
    ) {
        if ($this->eventThreshold < 1) {
            throw new \InvalidArgumentException('Event threshold must be at least 1');
        }
    }

    public function shouldTakeSnapshot(int $eventsSinceLastSnapshot): bool
    {
        return $eventsSinceLastSnapshot >= $this->eventThreshold;
    }
}
```

---

## AggregateSnapshotter

**File:** `src/Application/{BC}/Snapshot/AggregateSnapshotter.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BC}\Snapshot;

use Domain\{BC}\EventStore\EventStoreInterface;
use Domain\{BC}\EventStore\EventStream;
use Domain\{BC}\Snapshot\Snapshot;
use Domain\{BC}\Snapshot\SnapshotStoreInterface;

final readonly class AggregateSnapshotter
{
    public function __construct(
        private SnapshotStoreInterface $snapshotStore,
        private SnapshotStrategy $strategy
    ) {}

    /**
     * @return array{snapshot: ?Snapshot, remainingEvents: EventStream}
     */
    public function loadWithSnapshot(string $aggregateId, EventStoreInterface $eventStore): array
    {
        $snapshot = $this->snapshotStore->load($aggregateId);

        $fromVersion = $snapshot !== null ? $snapshot->version + 1 : 0;
        $remainingEvents = $eventStore->loadFrom($aggregateId, $fromVersion);

        return [
            'snapshot' => $snapshot,
            'remainingEvents' => $remainingEvents,
        ];
    }

    public function takeSnapshotIfNeeded(
        string $aggregateId,
        string $aggregateType,
        int $version,
        string $state,
        int $eventsSinceSnapshot
    ): void {
        if (!$this->strategy->shouldTakeSnapshot($eventsSinceSnapshot)) {
            return;
        }

        $snapshot = new Snapshot(
            aggregateId: $aggregateId,
            aggregateType: $aggregateType,
            version: $version,
            state: $state,
            createdAt: new \DateTimeImmutable()
        );

        $this->snapshotStore->save($snapshot);
    }
}
```

---

## DoctrineSnapshotStore

**File:** `src/Infrastructure/{BC}/Snapshot/DoctrineSnapshotStore.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BC}\Snapshot;

use Doctrine\DBAL\Connection;
use Domain\{BC}\Snapshot\Snapshot;
use Domain\{BC}\Snapshot\SnapshotStoreInterface;

final readonly class DoctrineSnapshotStore implements SnapshotStoreInterface
{
    private const TABLE_NAME = 'snapshots';

    public function __construct(
        private Connection $connection
    ) {}

    public function save(Snapshot $snapshot): void
    {
        $this->connection->executeStatement(
            'INSERT INTO ' . self::TABLE_NAME . ' (aggregate_id, aggregate_type, version, state, created_at)
             VALUES (:aggregate_id, :aggregate_type, :version, :state, :created_at)
             ON DUPLICATE KEY UPDATE
                aggregate_type = VALUES(aggregate_type),
                version = VALUES(version),
                state = VALUES(state),
                created_at = VALUES(created_at)',
            [
                'aggregate_id' => $snapshot->aggregateId,
                'aggregate_type' => $snapshot->aggregateType,
                'version' => $snapshot->version,
                'state' => $snapshot->state,
                'created_at' => $snapshot->createdAt->format('Y-m-d H:i:s'),
            ]
        );
    }

    public function load(string $aggregateId): ?Snapshot
    {
        $row = $this->connection->fetchAssociative(
            'SELECT aggregate_id, aggregate_type, version, state, created_at
             FROM ' . self::TABLE_NAME . '
             WHERE aggregate_id = :aggregate_id',
            ['aggregate_id' => $aggregateId]
        );

        if ($row === false) {
            return null;
        }

        return Snapshot::fromArray($row);
    }

    public function delete(string $aggregateId): void
    {
        $this->connection->executeStatement(
            'DELETE FROM ' . self::TABLE_NAME . ' WHERE aggregate_id = :aggregate_id',
            ['aggregate_id' => $aggregateId]
        );
    }
}
```

---

## Database Migration

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
