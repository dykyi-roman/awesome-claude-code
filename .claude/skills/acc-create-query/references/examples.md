# Query Pattern Examples

## GetOrderDetails Query

**File:** `src/Application/Order/Query/GetOrderDetailsQuery.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

use Domain\Order\ValueObject\OrderId;

final readonly class GetOrderDetailsQuery
{
    public function __construct(
        public OrderId $orderId
    ) {}
}
```

---

## GetOrderDetails Handler

**File:** `src/Application/Order/Handler/GetOrderDetailsHandler.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Query\GetOrderDetailsQuery;
use Application\Order\DTO\OrderDetailsDTO;
use Application\Order\ReadModel\OrderReadModelInterface;
use Domain\Order\Exception\OrderNotFoundException;

final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): OrderDetailsDTO
    {
        $order = $this->readModel->findById($query->orderId->value);

        if ($order === null) {
            throw new OrderNotFoundException($query->orderId);
        }

        return $order;
    }
}
```

---

## OrderDetailsDTO

**File:** `src/Application/Order/DTO/OrderDetailsDTO.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderDetailsDTO
{
    /**
     * @param array<OrderLineDTO> $lines
     */
    public function __construct(
        public string $id,
        public string $customerId,
        public string $customerName,
        public string $status,
        public int $totalCents,
        public string $currency,
        public array $lines,
        public \DateTimeImmutable $createdAt,
        public ?\DateTimeImmutable $confirmedAt
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            id: $data['id'],
            customerId: $data['customer_id'],
            customerName: $data['customer_name'],
            status: $data['status'],
            totalCents: (int) $data['total_cents'],
            currency: $data['currency'],
            lines: array_map(
                fn (array $line) => OrderLineDTO::fromArray($line),
                $data['lines'] ?? []
            ),
            createdAt: new \DateTimeImmutable($data['created_at']),
            confirmedAt: isset($data['confirmed_at'])
                ? new \DateTimeImmutable($data['confirmed_at'])
                : null
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'customer_id' => $this->customerId,
            'customer_name' => $this->customerName,
            'status' => $this->status,
            'total_cents' => $this->totalCents,
            'currency' => $this->currency,
            'lines' => array_map(fn (OrderLineDTO $l) => $l->toArray(), $this->lines),
            'created_at' => $this->createdAt->format('c'),
            'confirmed_at' => $this->confirmedAt?->format('c'),
        ];
    }
}
```

---

## OrderLineDTO

**File:** `src/Application/Order/DTO/OrderLineDTO.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderLineDTO
{
    public function __construct(
        public string $productId,
        public string $productName,
        public int $quantity,
        public int $unitPriceCents,
        public int $totalCents
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            productId: $data['product_id'],
            productName: $data['product_name'],
            quantity: (int) $data['quantity'],
            unitPriceCents: (int) $data['unit_price_cents'],
            totalCents: (int) $data['total_cents']
        );
    }

    public function toArray(): array
    {
        return [
            'product_id' => $this->productId,
            'product_name' => $this->productName,
            'quantity' => $this->quantity,
            'unit_price_cents' => $this->unitPriceCents,
            'total_cents' => $this->totalCents,
        ];
    }
}
```

---

## ListOrders Query (with pagination/filtering)

**File:** `src/Application/Order/Query/ListOrdersQuery.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;

final readonly class ListOrdersQuery
{
    public function __construct(
        public ?CustomerId $customerId = null,
        public ?OrderStatus $status = null,
        public int $limit = 20,
        public int $offset = 0,
        public string $sortBy = 'created_at',
        public string $sortDirection = 'desc'
    ) {
        if ($limit < 1 || $limit > 100) {
            throw new \InvalidArgumentException('Limit must be between 1 and 100');
        }
        if ($offset < 0) {
            throw new \InvalidArgumentException('Offset must be non-negative');
        }
        if (!in_array($sortBy, ['created_at', 'total', 'status'], true)) {
            throw new \InvalidArgumentException('Invalid sort field');
        }
        if (!in_array($sortDirection, ['asc', 'desc'], true)) {
            throw new \InvalidArgumentException('Invalid sort direction');
        }
    }
}
```

---

## ListOrders Handler

**File:** `src/Application/Order/Handler/ListOrdersHandler.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Query\ListOrdersQuery;
use Application\Order\DTO\OrderListItemDTO;
use Application\Order\DTO\PaginatedResultDTO;
use Application\Order\ReadModel\OrderReadModelInterface;

final readonly class ListOrdersHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(ListOrdersQuery $query): PaginatedResultDTO
    {
        $items = $this->readModel->findAll(
            customerId: $query->customerId?->value,
            status: $query->status?->value,
            limit: $query->limit,
            offset: $query->offset,
            sortBy: $query->sortBy,
            sortDirection: $query->sortDirection
        );

        $total = $this->readModel->count(
            customerId: $query->customerId?->value,
            status: $query->status?->value
        );

        return new PaginatedResultDTO(
            items: $items,
            total: $total,
            limit: $query->limit,
            offset: $query->offset
        );
    }
}
```

---

## Read Model Interface

**File:** `src/Application/Order/ReadModel/OrderReadModelInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\ReadModel;

use Application\Order\DTO\OrderDetailsDTO;
use Application\Order\DTO\OrderListItemDTO;

interface OrderReadModelInterface
{
    public function findById(string $id): ?OrderDetailsDTO;

    /**
     * @return array<OrderListItemDTO>
     */
    public function findAll(
        ?string $customerId = null,
        ?string $status = null,
        int $limit = 20,
        int $offset = 0,
        string $sortBy = 'created_at',
        string $sortDirection = 'desc'
    ): array;

    public function count(?string $customerId = null, ?string $status = null): int;
}
```

---

## Unit Tests

### ListOrdersQueryTest

**File:** `tests/Unit/Application/Order/Query/ListOrdersQueryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Query;

use Application\Order\Query\ListOrdersQuery;
use Domain\Order\Enum\OrderStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ListOrdersQuery::class)]
final class ListOrdersQueryTest extends TestCase
{
    public function testCreatesWithDefaults(): void
    {
        $query = new ListOrdersQuery();

        self::assertNull($query->customerId);
        self::assertNull($query->status);
        self::assertSame(20, $query->limit);
        self::assertSame(0, $query->offset);
    }

    public function testCreatesWithFilters(): void
    {
        $query = new ListOrdersQuery(
            status: OrderStatus::Confirmed,
            limit: 50,
            offset: 100
        );

        self::assertSame(OrderStatus::Confirmed, $query->status);
        self::assertSame(50, $query->limit);
        self::assertSame(100, $query->offset);
    }

    public function testRejectsInvalidLimit(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new ListOrdersQuery(limit: 0);
    }

    public function testRejectsNegativeOffset(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new ListOrdersQuery(offset: -1);
    }

    public function testRejectsInvalidSortField(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new ListOrdersQuery(sortBy: 'invalid_field');
    }

    public function testRejectsInvalidSortDirection(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new ListOrdersQuery(sortDirection: 'invalid');
    }
}
```

### GetOrderDetailsHandlerTest

**File:** `tests/Unit/Application/Order/Handler/GetOrderDetailsHandlerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\Handler;

use Application\Order\Handler\GetOrderDetailsHandler;
use Application\Order\Query\GetOrderDetailsQuery;
use Application\Order\DTO\OrderDetailsDTO;
use Application\Order\ReadModel\OrderReadModelInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\Exception\OrderNotFoundException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(GetOrderDetailsHandler::class)]
final class GetOrderDetailsHandlerTest extends TestCase
{
    private OrderReadModelInterface $readModel;
    private GetOrderDetailsHandler $handler;

    protected function setUp(): void
    {
        $this->readModel = $this->createMock(OrderReadModelInterface::class);
        $this->handler = new GetOrderDetailsHandler($this->readModel);
    }

    public function testReturnsOrderDetails(): void
    {
        $orderId = 'order-123';
        $expectedDTO = $this->createOrderDetailsDTO($orderId);

        $this->readModel->expects(self::once())
            ->method('findById')
            ->with($orderId)
            ->willReturn($expectedDTO);

        $query = new GetOrderDetailsQuery(new OrderId($orderId));

        $result = ($this->handler)($query);

        self::assertSame($expectedDTO, $result);
    }

    public function testThrowsWhenNotFound(): void
    {
        $this->readModel->expects(self::once())
            ->method('findById')
            ->willReturn(null);

        $query = new GetOrderDetailsQuery(new OrderId('non-existent'));

        $this->expectException(OrderNotFoundException::class);

        ($this->handler)($query);
    }

    private function createOrderDetailsDTO(string $id): OrderDetailsDTO
    {
        return new OrderDetailsDTO(
            id: $id,
            customerId: 'customer-123',
            customerName: 'John Doe',
            status: 'confirmed',
            totalCents: 1500,
            currency: 'USD',
            lines: [],
            createdAt: new \DateTimeImmutable(),
            confirmedAt: new \DateTimeImmutable()
        );
    }
}
```
