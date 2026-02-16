# Read Model / Projection Examples

## Order Summary Read Model

**File:** `src/Domain/Order/ReadModel/OrderSummaryReadModel.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ReadModel;

final readonly class OrderSummaryReadModel
{
    public function __construct(
        public string $id,
        public string $orderNumber,
        public string $customerId,
        public string $customerName,
        public string $customerEmail,
        public string $status,
        public int $itemCount,
        public int $totalCents,
        public string $currency,
        public ?string $shippingCity,
        public ?string $trackingNumber,
        public \DateTimeImmutable $createdAt,
        public \DateTimeImmutable $updatedAt,
        public ?\DateTimeImmutable $shippedAt = null,
        public ?\DateTimeImmutable $deliveredAt = null
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            id: $data['id'],
            orderNumber: $data['order_number'],
            customerId: $data['customer_id'],
            customerName: $data['customer_name'],
            customerEmail: $data['customer_email'],
            status: $data['status'],
            itemCount: (int) $data['item_count'],
            totalCents: (int) $data['total_cents'],
            currency: $data['currency'],
            shippingCity: $data['shipping_city'],
            trackingNumber: $data['tracking_number'],
            createdAt: new \DateTimeImmutable($data['created_at']),
            updatedAt: new \DateTimeImmutable($data['updated_at']),
            shippedAt: $data['shipped_at'] ? new \DateTimeImmutable($data['shipped_at']) : null,
            deliveredAt: $data['delivered_at'] ? new \DateTimeImmutable($data['delivered_at']) : null
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'order_number' => $this->orderNumber,
            'customer_id' => $this->customerId,
            'customer_name' => $this->customerName,
            'customer_email' => $this->customerEmail,
            'status' => $this->status,
            'item_count' => $this->itemCount,
            'total_cents' => $this->totalCents,
            'currency' => $this->currency,
            'shipping_city' => $this->shippingCity,
            'tracking_number' => $this->trackingNumber,
            'created_at' => $this->createdAt->format('c'),
            'updated_at' => $this->updatedAt->format('c'),
            'shipped_at' => $this->shippedAt?->format('c'),
            'delivered_at' => $this->deliveredAt?->format('c'),
        ];
    }

    public function getFormattedTotal(): string
    {
        return sprintf('%s %.2f', $this->currency, $this->totalCents / 100);
    }

    public function isCompleted(): bool
    {
        return $this->status === 'delivered';
    }

    public function isPending(): bool
    {
        return in_array($this->status, ['pending', 'confirmed', 'paid'], true);
    }
}
```

---

## Order Summary Repository

**File:** `src/Infrastructure/Order/ReadModel/DoctrineOrderSummaryRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\ReadModel;

use Doctrine\DBAL\Connection;
use Domain\Order\ReadModel\OrderSearchCriteria;
use Domain\Order\ReadModel\OrderSummaryReadModel;
use Domain\Order\ReadModel\OrderSummaryReadModelRepositoryInterface;

final readonly class DoctrineOrderSummaryRepository implements OrderSummaryReadModelRepositoryInterface
{
    private const TABLE = 'order_summaries';

    public function __construct(
        private Connection $connection
    ) {}

    public function findById(string $id): ?OrderSummaryReadModel
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM ' . self::TABLE . ' WHERE id = :id',
            ['id' => $id]
        );

        return $row ? OrderSummaryReadModel::fromArray($row) : null;
    }

    public function findByCustomerId(string $customerId, int $limit = 50): array
    {
        $rows = $this->connection->fetchAllAssociative(
            'SELECT * FROM ' . self::TABLE . '
             WHERE customer_id = :customerId
             ORDER BY created_at DESC
             LIMIT :limit',
            ['customerId' => $customerId, 'limit' => $limit]
        );

        return array_map(fn($row) => OrderSummaryReadModel::fromArray($row), $rows);
    }

    public function findByStatus(string $status, int $limit = 100, int $offset = 0): array
    {
        $rows = $this->connection->fetchAllAssociative(
            'SELECT * FROM ' . self::TABLE . '
             WHERE status = :status
             ORDER BY created_at DESC
             LIMIT :limit OFFSET :offset',
            ['status' => $status, 'limit' => $limit, 'offset' => $offset]
        );

        return array_map(fn($row) => OrderSummaryReadModel::fromArray($row), $rows);
    }

    public function search(OrderSearchCriteria $criteria): array
    {
        $qb = $this->connection->createQueryBuilder()
            ->select('*')
            ->from(self::TABLE);

        if ($criteria->customerId !== null) {
            $qb->andWhere('customer_id = :customerId')
               ->setParameter('customerId', $criteria->customerId);
        }

        if ($criteria->status !== null) {
            $qb->andWhere('status = :status')
               ->setParameter('status', $criteria->status);
        }

        $qb->orderBy($criteria->sortBy, $criteria->sortDirection)
           ->setMaxResults($criteria->limit)
           ->setFirstResult($criteria->offset);

        $rows = $qb->executeQuery()->fetchAllAssociative();

        return array_map(fn($row) => OrderSummaryReadModel::fromArray($row), $rows);
    }
}
```

---

## Order Summary Projection

**File:** `src/Application/Order/Projection/OrderSummaryProjection.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Projection;

use Domain\Order\Event\OrderCreated;
use Domain\Order\Event\OrderPaid;
use Domain\Order\Event\OrderShipped;
use Domain\Order\Event\OrderDelivered;
use Domain\Order\Event\OrderCancelled;
use Domain\Shared\Event\DomainEventInterface;
use Psr\Log\LoggerInterface;

final class OrderSummaryProjection implements OrderSummaryProjectionInterface
{
    public function __construct(
        private readonly OrderSummaryStore $store,
        private readonly CustomerReadService $customerService,
        private readonly LoggerInterface $logger
    ) {}

    public function project(DomainEventInterface $event): void
    {
        match ($event::class) {
            OrderCreated::class => $this->whenOrderCreated($event),
            OrderPaid::class => $this->whenOrderPaid($event),
            OrderShipped::class => $this->whenOrderShipped($event),
            OrderDelivered::class => $this->whenOrderDelivered($event),
            OrderCancelled::class => $this->whenOrderCancelled($event),
            default => null,
        };
    }

    public function reset(): void
    {
        $this->store->truncate();
        $this->logger->info('OrderSummary projection reset');
    }

    public function subscribedEvents(): array
    {
        return [
            OrderCreated::class,
            OrderPaid::class,
            OrderShipped::class,
            OrderDelivered::class,
            OrderCancelled::class,
        ];
    }

    private function whenOrderCreated(OrderCreated $event): void
    {
        $customer = $this->customerService->findById($event->customerId);

        $this->store->insert([
            'id' => $event->orderId,
            'order_number' => $event->orderNumber,
            'customer_id' => $event->customerId,
            'customer_name' => $customer?->name ?? 'Unknown',
            'customer_email' => $customer?->email ?? '',
            'status' => 'pending',
            'item_count' => count($event->items),
            'total_cents' => $event->totalCents,
            'currency' => $event->currency,
            'shipping_city' => $event->shippingAddress['city'] ?? null,
            'created_at' => $event->occurredAt->format('Y-m-d H:i:s'),
            'updated_at' => $event->occurredAt->format('Y-m-d H:i:s'),
        ]);
    }

    private function whenOrderShipped(OrderShipped $event): void
    {
        $this->store->update($event->orderId, [
            'status' => 'shipped',
            'tracking_number' => $event->trackingNumber,
            'shipped_at' => $event->occurredAt->format('Y-m-d H:i:s'),
            'updated_at' => $event->occurredAt->format('Y-m-d H:i:s'),
        ]);
    }
}
```

---

## Unit Tests

### Read Model Test

**File:** `tests/Unit/Domain/Order/ReadModel/OrderSummaryReadModelTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\ReadModel;

use Domain\Order\ReadModel\OrderSummaryReadModel;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderSummaryReadModel::class)]
final class OrderSummaryReadModelTest extends TestCase
{
    public function testFromArrayCreatesReadModel(): void
    {
        $data = [
            'id' => 'order-123',
            'order_number' => 'ORD-2024-001',
            'customer_id' => 'cust-456',
            'customer_name' => 'John Doe',
            'customer_email' => 'john@example.com',
            'status' => 'pending',
            'item_count' => 3,
            'total_cents' => 9999,
            'currency' => 'USD',
            'shipping_city' => 'New York',
            'tracking_number' => null,
            'created_at' => '2024-01-15T10:00:00+00:00',
            'updated_at' => '2024-01-15T10:00:00+00:00',
            'shipped_at' => null,
            'delivered_at' => null,
        ];

        $readModel = OrderSummaryReadModel::fromArray($data);

        self::assertSame('order-123', $readModel->id);
        self::assertSame('ORD-2024-001', $readModel->orderNumber);
        self::assertSame(3, $readModel->itemCount);
    }

    public function testGetFormattedTotal(): void
    {
        $readModel = $this->createReadModel(totalCents: 9999, currency: 'USD');

        self::assertSame('USD 99.99', $readModel->getFormattedTotal());
    }

    public function testIsCompleted(): void
    {
        $pending = $this->createReadModel(status: 'pending');
        $delivered = $this->createReadModel(status: 'delivered');

        self::assertFalse($pending->isCompleted());
        self::assertTrue($delivered->isCompleted());
    }
}
```

### Projection Test

**File:** `tests/Unit/Application/Order/Projection/OrderSummaryProjectionTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Projection;

use Application\Order\Projection\OrderSummaryProjection;
use Domain\Order\Event\OrderCreated;
use Infrastructure\Order\Projection\OrderSummaryStore;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(OrderSummaryProjection::class)]
final class OrderSummaryProjectionTest extends TestCase
{
    public function testProjectsOrderCreated(): void
    {
        $store = $this->createMock(OrderSummaryStore::class);
        $customerService = $this->createMock(CustomerReadService::class);

        $store->expects($this->once())
            ->method('insert')
            ->with($this->callback(function (array $data) {
                return $data['id'] === 'order-123'
                    && $data['status'] === 'pending';
            }));

        $projection = new OrderSummaryProjection(
            $store,
            $customerService,
            new NullLogger()
        );

        $event = new OrderCreated(
            orderId: 'order-123',
            orderNumber: 'ORD-001',
            customerId: 'cust-123',
            items: ['item1'],
            totalCents: 9999,
            currency: 'USD',
            shippingAddress: ['city' => 'NYC'],
            occurredAt: new \DateTimeImmutable()
        );

        $projection->project($event);
    }

    public function testResetTruncatesStore(): void
    {
        $store = $this->createMock(OrderSummaryStore::class);
        $store->expects($this->once())->method('truncate');

        $projection = new OrderSummaryProjection(
            $store,
            $this->createMock(CustomerReadService::class),
            new NullLogger()
        );

        $projection->reset();
    }
}
```
