---
name: acc-create-event-store
description: Generates Event Store pattern for PHP 8.5. Creates event sourcing storage infrastructure with event streams, stored events, optimistic locking, and version tracking. Includes unit tests.
---

# Event Store Generator

Creates Event Store infrastructure for event sourcing with aggregate history and event replay.

## When to Use

| Scenario | Example |
|----------|---------|
| Event sourcing | Aggregate state from events |
| Audit trail | Complete change history |
| Event replay | Rebuild projections from events |
| Temporal queries | Query state at any point in time |

## Component Characteristics

### StoredEvent
- Immutable event wrapper
- Contains aggregate metadata (id, type, version)
- Serialized payload
- Creation timestamp

### EventStream
- Ordered collection of stored events
- Implements IteratorAggregate
- Tracks current version
- Supports appending new events

### EventStoreInterface
- Append events with optimistic locking
- Load full event stream for aggregate
- Load events from specific version
- Stream-based reading for large aggregates

---

## Generation Process

### Step 1: Generate Domain Components

**Path:** `src/Domain/{BoundedContext}/EventStore/`

1. `StoredEvent.php` — Immutable stored event value object
2. `EventStreamInterface.php` — Event stream contract
3. `EventStream.php` — Event stream implementation
4. `EventStoreInterface.php` — Event store contract

### Step 2: Generate Infrastructure

**Path:** `src/Infrastructure/{BoundedContext}/EventStore/`

1. `DoctrineEventStore.php` — Doctrine DBAL implementation with optimistic locking
2. Database migration SQL

### Step 3: Generate Tests

1. `StoredEventTest.php` — Stored event immutability tests
2. `EventStreamTest.php` — Stream operations tests
3. `DoctrineEventStoreTest.php` — Integration tests

---

## File Placement

| Component | Path |
|-----------|------|
| StoredEvent | `src/Domain/{BoundedContext}/EventStore/` |
| EventStream | `src/Domain/{BoundedContext}/EventStore/` |
| EventStoreInterface | `src/Domain/{BoundedContext}/EventStore/` |
| DoctrineEventStore | `src/Infrastructure/{BoundedContext}/EventStore/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/EventStore/` |
| Integration Tests | `tests/Integration/Infrastructure/{BoundedContext}/EventStore/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Stored Event | `StoredEvent` | `StoredEvent` |
| Stream Interface | `EventStreamInterface` | `EventStreamInterface` |
| Stream | `EventStream` | `EventStream` |
| Store Interface | `EventStoreInterface` | `EventStoreInterface` |
| Store Impl | `Doctrine{Name}EventStore` | `DoctrineEventStore` |
| Exception | `ConcurrencyException` | `ConcurrencyException` |
| Test | `{ClassName}Test` | `StoredEventTest` |

---

## Quick Template Reference

### StoredEvent

```php
final readonly class StoredEvent
{
    public function __construct(
        public string $aggregateId,
        public string $aggregateType,
        public string $eventType,
        public string $payload,
        public int $version,
        public \DateTimeImmutable $createdAt
    ) {}

    public static function fromDomainEvent(string $aggregateId, string $aggregateType, int $version, object $event): self;
    public function toArray(): array;
    public static function fromArray(array $data): self;
}
```

### EventStoreInterface

```php
interface EventStoreInterface
{
    public function append(string $aggregateId, EventStream $events, int $expectedVersion): void;
    public function load(string $aggregateId): EventStream;
    public function loadFromVersion(string $aggregateId, int $fromVersion): EventStream;
}
```

### EventStream

```php
final class EventStream implements \IteratorAggregate, \Countable
{
    public static function empty(): self;
    public static function fromEvents(array $events): self;
    public function append(StoredEvent $event): self;
    public function getVersion(): int;
    public function isEmpty(): bool;
    public function getIterator(): \ArrayIterator;
    public function count(): int;
}
```

---

## Usage Example

```php
// Append events
$events = EventStream::fromEvents([
    StoredEvent::fromDomainEvent($orderId, 'Order', 1, $orderCreated),
    StoredEvent::fromDomainEvent($orderId, 'Order', 2, $itemAdded),
]);
$eventStore->append($orderId, $events, expectedVersion: 0);

// Load and replay
$stream = $eventStore->load($orderId);
foreach ($stream as $event) {
    $aggregate->apply($event);
}
```

---

## Database Schema

```sql
CREATE TABLE event_store (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    aggregate_id VARCHAR(36) NOT NULL,
    aggregate_type VARCHAR(255) NOT NULL,
    event_type VARCHAR(255) NOT NULL,
    payload JSON NOT NULL,
    version INT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE INDEX idx_aggregate_version (aggregate_id, version),
    INDEX idx_aggregate_type (aggregate_type),
    INDEX idx_event_type (event_type),
    INDEX idx_created_at (created_at)
);
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Mutable Events | History changes | Immutable StoredEvent |
| Missing Version | No optimistic locking | Version per aggregate |
| No Idempotency | Duplicate appends | Unique aggregate_id + version |
| Large Payloads | Slow reads | Serialize only essential data |
| No Snapshots | Slow rebuilds for long streams | Use acc-create-snapshot |
| Global Stream Only | Can't load per-aggregate | Per-aggregate stream support |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — StoredEvent, EventStream, EventStoreInterface, DoctrineEventStore templates
- `references/examples.md` — Order event store usage and tests
