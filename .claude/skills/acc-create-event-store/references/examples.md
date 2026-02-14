# Event Store Pattern Examples

## Order Event Store Usage

**File:** `src/Infrastructure/Order/EventStore/OrderEventSourcedRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\EventStore;

use Domain\Order\Entity\Order;
use Domain\Order\EventStore\EventStoreInterface;
use Domain\Order\EventStore\EventStream;
use Domain\Order\EventStore\StoredEvent;

final readonly class OrderEventSourcedRepository
{
    public function __construct(
        private EventStoreInterface $eventStore
    ) {}

    public function save(Order $order): void
    {
        $uncommittedEvents = $order->getUncommittedEvents();

        $storedEvents = [];
        $version = $order->getLastCommittedVersion();

        foreach ($uncommittedEvents as $event) {
            $version++;
            $storedEvents[] = StoredEvent::fromDomainEvent(
                aggregateId: $order->getId()->toString(),
                aggregateType: 'Order',
                version: $version,
                event: $event
            );
        }

        $this->eventStore->append(
            aggregateId: $order->getId()->toString(),
            events: EventStream::fromEvents($storedEvents),
            expectedVersion: $order->getLastCommittedVersion()
        );
    }

    public function load(string $aggregateId): Order
    {
        $stream = $this->eventStore->load($aggregateId);

        if ($stream->isEmpty()) {
            throw new \RuntimeException(
                sprintf('Order "%s" not found in event store', $aggregateId)
            );
        }

        return Order::reconstitute($stream);
    }
}
```

---

## Event Replay / Rebuild

```php
<?php

declare(strict_types=1);

// Rebuild aggregate from full event history
$stream = $eventStore->load($aggregateId);
$order = Order::reconstitute($stream);

// Load only events after a certain version (for partial replay)
$recentEvents = $eventStore->loadFromVersion($aggregateId, fromVersion: 50);
foreach ($recentEvents as $event) {
    $projection->project($event);
}
```

---

## Unit Tests

### StoredEventTest

**File:** `tests/Unit/Domain/Order/EventStore/StoredEventTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\EventStore;

use Domain\Order\EventStore\StoredEvent;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(StoredEvent::class)]
final class StoredEventTest extends TestCase
{
    public function testConstructsWithValidData(): void
    {
        $now = new \DateTimeImmutable();

        $event = new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'OrderCreated',
            payload: '{"total": 100}',
            version: 1,
            createdAt: $now
        );

        self::assertSame('order-123', $event->aggregateId);
        self::assertSame('Order', $event->aggregateType);
        self::assertSame('OrderCreated', $event->eventType);
        self::assertSame('{"total": 100}', $event->payload);
        self::assertSame(1, $event->version);
        self::assertSame($now, $event->createdAt);
    }

    public function testRejectsInvalidVersion(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'OrderCreated',
            payload: '{}',
            version: 0,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function testToArrayReturnsExpectedFormat(): void
    {
        $now = new \DateTimeImmutable('2025-01-15 10:30:00.000000');

        $event = new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'OrderCreated',
            payload: '{"total": 100}',
            version: 1,
            createdAt: $now
        );

        $array = $event->toArray();

        self::assertSame('order-123', $array['aggregate_id']);
        self::assertSame('Order', $array['aggregate_type']);
        self::assertSame('OrderCreated', $array['event_type']);
        self::assertSame(1, $array['version']);
    }

    public function testFromArrayRoundTrip(): void
    {
        $original = new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'OrderCreated',
            payload: '{"total": 100}',
            version: 1,
            createdAt: new \DateTimeImmutable('2025-01-15 10:30:00.000000')
        );

        $restored = StoredEvent::fromArray($original->toArray());

        self::assertSame($original->aggregateId, $restored->aggregateId);
        self::assertSame($original->aggregateType, $restored->aggregateType);
        self::assertSame($original->eventType, $restored->eventType);
        self::assertSame($original->payload, $restored->payload);
        self::assertSame($original->version, $restored->version);
    }
}
```

---

### EventStreamTest

**File:** `tests/Unit/Domain/Order/EventStore/EventStreamTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\EventStore;

use Domain\Order\EventStore\EventStream;
use Domain\Order\EventStore\StoredEvent;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(EventStream::class)]
final class EventStreamTest extends TestCase
{
    public function testEmptyStreamHasZeroVersion(): void
    {
        $stream = EventStream::empty();

        self::assertSame(0, $stream->getVersion());
        self::assertTrue($stream->isEmpty());
        self::assertCount(0, $stream);
    }

    public function testFromEventsCreatesStream(): void
    {
        $events = [
            $this->createEvent(1),
            $this->createEvent(2),
        ];

        $stream = EventStream::fromEvents($events);

        self::assertSame(2, $stream->getVersion());
        self::assertFalse($stream->isEmpty());
        self::assertCount(2, $stream);
    }

    public function testAppendReturnsNewInstance(): void
    {
        $stream = EventStream::empty();
        $newStream = $stream->append($this->createEvent(1));

        self::assertTrue($stream->isEmpty());
        self::assertFalse($newStream->isEmpty());
        self::assertCount(1, $newStream);
    }

    public function testGetVersionReturnsMaxVersion(): void
    {
        $stream = EventStream::fromEvents([
            $this->createEvent(1),
            $this->createEvent(3),
            $this->createEvent(2),
        ]);

        self::assertSame(3, $stream->getVersion());
    }

    public function testIsIterable(): void
    {
        $stream = EventStream::fromEvents([
            $this->createEvent(1),
            $this->createEvent(2),
        ]);

        $versions = [];
        foreach ($stream as $event) {
            $versions[] = $event->version;
        }

        self::assertSame([1, 2], $versions);
    }

    private function createEvent(int $version): StoredEvent
    {
        return new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'TestEvent',
            payload: '{}',
            version: $version,
            createdAt: new \DateTimeImmutable()
        );
    }
}
```

---

### DoctrineEventStoreTest

**File:** `tests/Integration/Infrastructure/Order/EventStore/DoctrineEventStoreTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure\Order\EventStore;

use Doctrine\DBAL\Connection;
use Domain\Order\EventStore\ConcurrencyException;
use Domain\Order\EventStore\EventStream;
use Domain\Order\EventStore\StoredEvent;
use Infrastructure\Order\EventStore\DoctrineEventStore;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('integration')]
#[CoversClass(DoctrineEventStore::class)]
final class DoctrineEventStoreTest extends TestCase
{
    private Connection $connection;
    private DoctrineEventStore $store;

    protected function setUp(): void
    {
        $this->connection = $this->createMock(Connection::class);
        $this->store = new DoctrineEventStore($this->connection);
    }

    public function testAppendStoresEvents(): void
    {
        $this->connection->expects(self::once())->method('beginTransaction');
        $this->connection->method('fetchOne')->willReturn(0);
        $this->connection->expects(self::exactly(2))->method('insert');
        $this->connection->expects(self::once())->method('commit');

        $events = EventStream::fromEvents([
            $this->createEvent(1),
            $this->createEvent(2),
        ]);

        $this->store->append('order-123', $events, expectedVersion: 0);
    }

    public function testAppendThrowsOnConcurrencyConflict(): void
    {
        $this->connection->expects(self::once())->method('beginTransaction');
        $this->connection->method('fetchOne')->willReturn(5);
        $this->connection->expects(self::once())->method('rollBack');

        $this->expectException(ConcurrencyException::class);

        $events = EventStream::fromEvents([$this->createEvent(6)]);
        $this->store->append('order-123', $events, expectedVersion: 3);
    }

    public function testLoadReturnsEventStream(): void
    {
        $this->connection->method('fetchAllAssociative')->willReturn([
            [
                'aggregate_id' => 'order-123',
                'aggregate_type' => 'Order',
                'event_type' => 'OrderCreated',
                'payload' => '{}',
                'version' => '1',
                'created_at' => '2025-01-15 10:30:00.000000',
            ],
        ]);

        $stream = $this->store->load('order-123');

        self::assertCount(1, $stream);
        self::assertSame(1, $stream->getVersion());
    }

    public function testLoadFromVersionFiltersEvents(): void
    {
        $this->connection->method('fetchAllAssociative')->willReturn([]);

        $stream = $this->store->loadFromVersion('order-123', fromVersion: 5);

        self::assertTrue($stream->isEmpty());
    }

    private function createEvent(int $version): StoredEvent
    {
        return new StoredEvent(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            eventType: 'OrderCreated',
            payload: '{}',
            version: $version,
            createdAt: new \DateTimeImmutable()
        );
    }
}
```
