# Event Store Pattern Templates

## StoredEvent

**File:** `src/Domain/{BoundedContext}/EventStore/StoredEvent.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\EventStore;

final readonly class StoredEvent
{
    public function __construct(
        public string $aggregateId,
        public string $aggregateType,
        public string $eventType,
        public string $payload,
        public int $version,
        public \DateTimeImmutable $createdAt
    ) {
        if ($this->version < 1) {
            throw new \InvalidArgumentException('Event version must be at least 1');
        }
    }

    public static function fromDomainEvent(
        string $aggregateId,
        string $aggregateType,
        int $version,
        object $event
    ): self {
        return new self(
            aggregateId: $aggregateId,
            aggregateType: $aggregateType,
            eventType: $event::class,
            payload: json_encode($event, JSON_THROW_ON_ERROR),
            version: $version,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function toArray(): array
    {
        return [
            'aggregate_id' => $this->aggregateId,
            'aggregate_type' => $this->aggregateType,
            'event_type' => $this->eventType,
            'payload' => $this->payload,
            'version' => $this->version,
            'created_at' => $this->createdAt->format('Y-m-d H:i:s.u'),
        ];
    }

    public static function fromArray(array $data): self
    {
        return new self(
            aggregateId: $data['aggregate_id'],
            aggregateType: $data['aggregate_type'],
            eventType: $data['event_type'],
            payload: $data['payload'],
            version: (int) $data['version'],
            createdAt: new \DateTimeImmutable($data['created_at'])
        );
    }
}
```

---

## EventStreamInterface

**File:** `src/Domain/{BoundedContext}/EventStore/EventStreamInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\EventStore;

interface EventStreamInterface extends \IteratorAggregate, \Countable
{
    public function getVersion(): int;

    public function isEmpty(): bool;
}
```

---

## EventStream

**File:** `src/Domain/{BoundedContext}/EventStore/EventStream.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\EventStore;

final class EventStream implements EventStreamInterface
{
    /** @var list<StoredEvent> */
    private array $events;

    /**
     * @param list<StoredEvent> $events
     */
    private function __construct(array $events = [])
    {
        $this->events = $events;
    }

    public static function empty(): self
    {
        return new self();
    }

    /**
     * @param list<StoredEvent> $events
     */
    public static function fromEvents(array $events): self
    {
        return new self($events);
    }

    public function append(StoredEvent $event): self
    {
        $new = clone $this;
        $new->events[] = $event;

        return $new;
    }

    public function getVersion(): int
    {
        if ($this->events === []) {
            return 0;
        }

        return max(array_map(
            static fn(StoredEvent $event): int => $event->version,
            $this->events
        ));
    }

    public function isEmpty(): bool
    {
        return $this->events === [];
    }

    /**
     * @return \ArrayIterator<int, StoredEvent>
     */
    public function getIterator(): \ArrayIterator
    {
        return new \ArrayIterator($this->events);
    }

    public function count(): int
    {
        return count($this->events);
    }

    /**
     * @return list<StoredEvent>
     */
    public function toArray(): array
    {
        return $this->events;
    }
}
```

---

## EventStoreInterface

**File:** `src/Domain/{BoundedContext}/EventStore/EventStoreInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\EventStore;

interface EventStoreInterface
{
    /**
     * @throws ConcurrencyException When expected version does not match current version
     */
    public function append(string $aggregateId, EventStream $events, int $expectedVersion): void;

    public function load(string $aggregateId): EventStream;

    public function loadFromVersion(string $aggregateId, int $fromVersion): EventStream;
}
```

---

## ConcurrencyException

**File:** `src/Domain/{BoundedContext}/EventStore/ConcurrencyException.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\EventStore;

final class ConcurrencyException extends \RuntimeException
{
    public function __construct(
        public readonly string $aggregateId,
        public readonly int $expectedVersion,
        public readonly int $actualVersion
    ) {
        parent::__construct(
            sprintf(
                'Concurrency conflict for aggregate "%s": expected version %d, actual version %d',
                $aggregateId,
                $expectedVersion,
                $actualVersion
            )
        );
    }
}
```

---

## DoctrineEventStore

**File:** `src/Infrastructure/{BoundedContext}/EventStore/DoctrineEventStore.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\EventStore;

use Doctrine\DBAL\Connection;
use Domain\{BoundedContext}\EventStore\ConcurrencyException;
use Domain\{BoundedContext}\EventStore\EventStoreInterface;
use Domain\{BoundedContext}\EventStore\EventStream;
use Domain\{BoundedContext}\EventStore\StoredEvent;

final readonly class DoctrineEventStore implements EventStoreInterface
{
    private const TABLE_NAME = 'event_store';

    public function __construct(
        private Connection $connection
    ) {}

    public function append(string $aggregateId, EventStream $events, int $expectedVersion): void
    {
        if ($events->isEmpty()) {
            return;
        }

        $this->connection->beginTransaction();

        try {
            $currentVersion = $this->getCurrentVersion($aggregateId);

            if ($currentVersion !== $expectedVersion) {
                throw new ConcurrencyException($aggregateId, $expectedVersion, $currentVersion);
            }

            foreach ($events as $event) {
                $this->connection->insert(self::TABLE_NAME, $event->toArray());
            }

            $this->connection->commit();
        } catch (\Throwable $e) {
            $this->connection->rollBack();
            throw $e;
        }
    }

    public function load(string $aggregateId): EventStream
    {
        return $this->loadFromVersion($aggregateId, 0);
    }

    public function loadFromVersion(string $aggregateId, int $fromVersion): EventStream
    {
        $rows = $this->connection->fetchAllAssociative(
            sprintf(
                'SELECT * FROM %s WHERE aggregate_id = ? AND version > ? ORDER BY version ASC',
                self::TABLE_NAME
            ),
            [$aggregateId, $fromVersion]
        );

        $events = array_map(
            static fn(array $row): StoredEvent => StoredEvent::fromArray($row),
            $rows
        );

        return EventStream::fromEvents($events);
    }

    private function getCurrentVersion(string $aggregateId): int
    {
        $result = $this->connection->fetchOne(
            sprintf(
                'SELECT COALESCE(MAX(version), 0) FROM %s WHERE aggregate_id = ?',
                self::TABLE_NAME
            ),
            [$aggregateId]
        );

        return (int) $result;
    }
}
```

---

## Database Migration

```sql
CREATE TABLE event_store (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    aggregate_id VARCHAR(36) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSON NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),

    UNIQUE INDEX idx_aggregate_version (aggregate_id, version),
    INDEX idx_aggregate_type (aggregate_type),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```
