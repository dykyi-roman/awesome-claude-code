# Snapshot Pattern Examples

## OrderAggregate with Snapshot Support

**File:** `src/Domain/Order/Order.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order;

use Domain\Order\Snapshot\Snapshot;

final class Order
{
    private int $version = 0;

    /** @var array<int, object> */
    private array $uncommittedEvents = [];

    public function __construct(
        private readonly string $id,
        private string $status = 'new',
        private int $totalAmount = 0
    ) {}

    public static function fromSnapshot(Snapshot $snapshot): self
    {
        /** @var array{status: string, total_amount: int} $state */
        $state = json_decode($snapshot->state, true, 512, JSON_THROW_ON_ERROR);

        $order = new self(
            id: $snapshot->aggregateId,
            status: $state['status'],
            totalAmount: $state['total_amount']
        );
        $order->version = $snapshot->version;

        return $order;
    }

    public function toSnapshot(): string
    {
        return json_encode([
            'status' => $this->status,
            'total_amount' => $this->totalAmount,
        ], JSON_THROW_ON_ERROR);
    }

    public function apply(object $event): void
    {
        $this->version++;

        match ($event::class) {
            OrderPlaced::class => $this->applyOrderPlaced($event),
            OrderItemAdded::class => $this->applyOrderItemAdded($event),
            OrderConfirmed::class => $this->applyOrderConfirmed($event),
            default => null,
        };
    }

    public function getVersion(): int
    {
        return $this->version;
    }

    public function getId(): string
    {
        return $this->id;
    }

    private function applyOrderPlaced(OrderPlaced $event): void
    {
        $this->status = 'placed';
    }

    private function applyOrderItemAdded(OrderItemAdded $event): void
    {
        $this->totalAmount += $event->amount;
    }

    private function applyOrderConfirmed(OrderConfirmed $event): void
    {
        $this->status = 'confirmed';
    }
}
```

---

## Event Sourcing + Snapshot Integration

**File:** `src/Application/Order/LoadOrderHandler.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order;

use Application\Order\Snapshot\AggregateSnapshotter;
use Domain\Order\EventStore\EventStoreInterface;
use Domain\Order\Order;

final readonly class LoadOrderHandler
{
    public function __construct(
        private AggregateSnapshotter $snapshotter,
        private EventStoreInterface $eventStore
    ) {}

    public function handle(string $orderId): Order
    {
        $result = $this->snapshotter->loadWithSnapshot($orderId, $this->eventStore);

        $snapshot = $result['snapshot'];
        $remainingEvents = $result['remainingEvents'];

        $order = $snapshot !== null
            ? Order::fromSnapshot($snapshot)
            : new Order($orderId);

        foreach ($remainingEvents as $event) {
            $order->apply($event);
        }

        $this->snapshotter->takeSnapshotIfNeeded(
            aggregateId: $orderId,
            aggregateType: 'Order',
            version: $order->getVersion(),
            state: $order->toSnapshot(),
            eventsSinceSnapshot: count($remainingEvents)
        );

        return $order;
    }
}
```

---

## Unit Tests

### SnapshotTest

**File:** `tests/Unit/Domain/{BC}/Snapshot/SnapshotTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Snapshot;

use Domain\Order\Snapshot\Snapshot;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Snapshot::class)]
final class SnapshotTest extends TestCase
{
    public function testConstruction(): void
    {
        $createdAt = new \DateTimeImmutable('2025-01-15 10:00:00');
        $snapshot = new Snapshot(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            version: 5,
            state: '{"status":"confirmed"}',
            createdAt: $createdAt
        );

        self::assertSame('order-123', $snapshot->aggregateId);
        self::assertSame('Order', $snapshot->aggregateType);
        self::assertSame(5, $snapshot->version);
        self::assertSame('{"status":"confirmed"}', $snapshot->state);
        self::assertSame($createdAt, $snapshot->createdAt);
    }

    public function testFromArrayToArrayRoundtrip(): void
    {
        $data = [
            'aggregate_id' => 'order-456',
            'aggregate_type' => 'Order',
            'version' => 10,
            'state' => '{"status":"placed","total_amount":500}',
            'created_at' => '2025-01-15 12:30:00',
        ];

        $snapshot = Snapshot::fromArray($data);
        $result = $snapshot->toArray();

        self::assertSame($data, $result);
    }

    public function testRejectsInvalidVersion(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Snapshot version must be at least 1');

        new Snapshot(
            aggregateId: 'order-789',
            aggregateType: 'Order',
            version: 0,
            state: '{}',
            createdAt: new \DateTimeImmutable()
        );
    }

    public function testRejectsNegativeVersion(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new Snapshot(
            aggregateId: 'order-789',
            aggregateType: 'Order',
            version: -1,
            state: '{}',
            createdAt: new \DateTimeImmutable()
        );
    }
}
```

---

### SnapshotStrategyTest

**File:** `tests/Unit/Application/{BC}/Snapshot/SnapshotStrategyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Snapshot;

use Application\Order\Snapshot\SnapshotStrategy;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(SnapshotStrategy::class)]
final class SnapshotStrategyTest extends TestCase
{
    public function testBelowThresholdReturnsFalse(): void
    {
        $strategy = new SnapshotStrategy(eventThreshold: 100);

        self::assertFalse($strategy->shouldTakeSnapshot(99));
    }

    public function testAtThresholdReturnsTrue(): void
    {
        $strategy = new SnapshotStrategy(eventThreshold: 100);

        self::assertTrue($strategy->shouldTakeSnapshot(100));
    }

    public function testAboveThresholdReturnsTrue(): void
    {
        $strategy = new SnapshotStrategy(eventThreshold: 100);

        self::assertTrue($strategy->shouldTakeSnapshot(150));
    }

    public function testCustomThreshold(): void
    {
        $strategy = new SnapshotStrategy(eventThreshold: 50);

        self::assertFalse($strategy->shouldTakeSnapshot(49));
        self::assertTrue($strategy->shouldTakeSnapshot(50));
        self::assertTrue($strategy->shouldTakeSnapshot(51));
    }

    public function testDefaultThreshold(): void
    {
        $strategy = new SnapshotStrategy();

        self::assertFalse($strategy->shouldTakeSnapshot(99));
        self::assertTrue($strategy->shouldTakeSnapshot(100));
    }
}
```

---

### AggregateSnapshotterTest

**File:** `tests/Unit/Application/{BC}/Snapshot/AggregateSnapshotterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Snapshot;

use Application\Order\Snapshot\AggregateSnapshotter;
use Application\Order\Snapshot\SnapshotStrategy;
use Domain\Order\EventStore\EventStoreInterface;
use Domain\Order\EventStore\EventStream;
use Domain\Order\Snapshot\Snapshot;
use Domain\Order\Snapshot\SnapshotStoreInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(AggregateSnapshotter::class)]
final class AggregateSnapshotterTest extends TestCase
{
    private SnapshotStoreInterface&MockObject $snapshotStore;
    private EventStoreInterface&MockObject $eventStore;

    protected function setUp(): void
    {
        $this->snapshotStore = $this->createMock(SnapshotStoreInterface::class);
        $this->eventStore = $this->createMock(EventStoreInterface::class);
    }

    public function testLoadWithSnapshotPresent(): void
    {
        $snapshot = new Snapshot(
            aggregateId: 'order-123',
            aggregateType: 'Order',
            version: 5,
            state: '{"status":"placed"}',
            createdAt: new \DateTimeImmutable()
        );

        $this->snapshotStore
            ->expects(self::once())
            ->method('load')
            ->with('order-123')
            ->willReturn($snapshot);

        $remainingEvents = new EventStream([]);
        $this->eventStore
            ->expects(self::once())
            ->method('loadFrom')
            ->with('order-123', 6)
            ->willReturn($remainingEvents);

        $strategy = new SnapshotStrategy(eventThreshold: 100);
        $snapshotter = new AggregateSnapshotter($this->snapshotStore, $strategy);

        $result = $snapshotter->loadWithSnapshot('order-123', $this->eventStore);

        self::assertSame($snapshot, $result['snapshot']);
        self::assertSame($remainingEvents, $result['remainingEvents']);
    }

    public function testLoadWithoutSnapshot(): void
    {
        $this->snapshotStore
            ->expects(self::once())
            ->method('load')
            ->with('order-456')
            ->willReturn(null);

        $allEvents = new EventStream([]);
        $this->eventStore
            ->expects(self::once())
            ->method('loadFrom')
            ->with('order-456', 0)
            ->willReturn($allEvents);

        $strategy = new SnapshotStrategy(eventThreshold: 100);
        $snapshotter = new AggregateSnapshotter($this->snapshotStore, $strategy);

        $result = $snapshotter->loadWithSnapshot('order-456', $this->eventStore);

        self::assertNull($result['snapshot']);
        self::assertSame($allEvents, $result['remainingEvents']);
    }

    public function testTakeSnapshotIfNeededWhenThresholdMet(): void
    {
        $this->snapshotStore
            ->expects(self::once())
            ->method('save')
            ->with(self::callback(function (Snapshot $snapshot): bool {
                return $snapshot->aggregateId === 'order-789'
                    && $snapshot->aggregateType === 'Order'
                    && $snapshot->version === 150
                    && $snapshot->state === '{"status":"confirmed"}';
            }));

        $strategy = new SnapshotStrategy(eventThreshold: 100);
        $snapshotter = new AggregateSnapshotter($this->snapshotStore, $strategy);

        $snapshotter->takeSnapshotIfNeeded(
            aggregateId: 'order-789',
            aggregateType: 'Order',
            version: 150,
            state: '{"status":"confirmed"}',
            eventsSinceSnapshot: 100
        );
    }

    public function testTakeSnapshotIfNeededSkipsWhenBelowThreshold(): void
    {
        $this->snapshotStore
            ->expects(self::never())
            ->method('save');

        $strategy = new SnapshotStrategy(eventThreshold: 100);
        $snapshotter = new AggregateSnapshotter($this->snapshotStore, $strategy);

        $snapshotter->takeSnapshotIfNeeded(
            aggregateId: 'order-789',
            aggregateType: 'Order',
            version: 50,
            state: '{"status":"placed"}',
            eventsSinceSnapshot: 50
        );
    }
}
```
