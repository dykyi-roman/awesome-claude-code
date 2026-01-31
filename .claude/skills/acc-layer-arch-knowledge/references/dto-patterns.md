# DTO Patterns in Layered Architecture

Data Transfer Object patterns for communication between layers.

## DTO Types by Layer

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          DTO FLOW                                         │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Presentation          Application           Domain          Infrastructure
│  ─────────────         ───────────           ──────          ──────────────
│  Request DTO    ──→    Command/Query DTO                                 │
│  Response DTO   ←──    Result DTO      ←──   Entity    ←──   DB Record   │
│  Resource/View  ←──    Read Model                                        │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Presentation Layer DTOs

### Request DTO

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Request;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class CreateOrderRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Uuid]
        public string $customerId,

        #[Assert\NotBlank]
        #[Assert\Count(min: 1, minMessage: 'At least one line is required')]
        #[Assert\All([
            new Assert\Collection([
                'product_id' => [new Assert\NotBlank(), new Assert\Uuid()],
                'quantity' => [new Assert\NotBlank(), new Assert\Positive()],
                'unit_price' => [new Assert\NotBlank(), new Assert\Positive()],
            ])
        ])]
        public array $lines
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            customerId: $data['customer_id'] ?? '',
            lines: $data['lines'] ?? []
        );
    }
}
```

### Response Resource

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Response;

use Application\Order\DTO\OrderDTO;

final readonly class OrderResource
{
    public function __construct(
        public string $id,
        public string $customerId,
        public string $status,
        public array $lines,
        public string $total,
        public string $createdAt
    ) {}

    public static function fromDTO(OrderDTO $dto): self
    {
        return new self(
            id: $dto->id,
            customerId: $dto->customerId,
            status: $dto->status,
            lines: array_map(
                fn (OrderLineDTO $line) => OrderLineResource::fromDTO($line)->toArray(),
                $dto->lines
            ),
            total: number_format($dto->totalCents / 100, 2),
            createdAt: $dto->createdAt->format('c')
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'customer_id' => $this->customerId,
            'status' => $this->status,
            'lines' => $this->lines,
            'total' => $this->total,
            'created_at' => $this->createdAt,
        ];
    }
}
```

## Application Layer DTOs

### Command DTO (Write Operation)

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class CreateOrderDTO
{
    /**
     * @param array<array{product_id: string, quantity: int, unit_price: int}> $lines
     */
    public function __construct(
        public string $customerId,
        public array $lines
    ) {}

    public static function fromRequest(CreateOrderRequest $request): self
    {
        return new self(
            customerId: $request->customerId,
            lines: $request->lines
        );
    }
}
```

### Query DTO (Read Operation)

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class GetOrderQuery
{
    public function __construct(
        public string $orderId
    ) {}
}

final readonly class ListOrdersQuery
{
    public function __construct(
        public ?string $customerId = null,
        public ?string $status = null,
        public int $page = 1,
        public int $perPage = 20
    ) {}
}
```

### Result DTO (Return from Application)

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

use Domain\Order\Entity\Order;

final readonly class OrderDTO
{
    /**
     * @param array<OrderLineDTO> $lines
     */
    public function __construct(
        public string $id,
        public string $customerId,
        public string $status,
        public array $lines,
        public int $totalCents,
        public \DateTimeImmutable $createdAt
    ) {}

    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->id()->value,
            customerId: $order->customerId()->value,
            status: $order->status()->value,
            lines: array_map(
                fn ($line) => OrderLineDTO::fromEntity($line),
                $order->lines()
            ),
            totalCents: $order->total()->cents(),
            createdAt: $order->createdAt()
        );
    }
}
```

### Collection DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderListDTO
{
    /**
     * @param array<OrderDTO> $items
     */
    public function __construct(
        public array $items,
        public int $total,
        public int $page,
        public int $perPage
    ) {}

    public static function fromEntities(array $orders, int $total, int $page, int $perPage): self
    {
        return new self(
            items: array_map(fn ($order) => OrderDTO::fromEntity($order), $orders),
            total: $total,
            page: $page,
            perPage: $perPage
        );
    }

    public function hasMore(): bool
    {
        return ($this->page * $this->perPage) < $this->total;
    }
}
```

## DTO Mapping Patterns

### Manual Mapping (Explicit)

```php
// Presentation → Application
$dto = new CreateOrderDTO(
    customerId: $request->customerId,
    lines: $request->lines
);

// Application → Domain
$order = Order::create(
    id: $this->orderRepository->nextIdentity(),
    customerId: new CustomerId($dto->customerId),
    lines: array_map(fn ($l) => new OrderLineData(
        productId: new ProductId($l['product_id']),
        quantity: $l['quantity'],
        unitPrice: new Money($l['unit_price'], 'USD')
    ), $dto->lines)
);

// Domain → Application
$result = OrderDTO::fromEntity($order);

// Application → Presentation
$response = OrderResource::fromDTO($result);
```

### Static Factory Method

```php
final readonly class OrderDTO
{
    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->id()->value,
            customerId: $order->customerId()->value,
            status: $order->status()->value,
            lines: array_map(
                fn ($line) => OrderLineDTO::fromEntity($line),
                $order->lines()
            ),
            totalCents: $order->total()->cents(),
            createdAt: $order->createdAt()
        );
    }
}
```

### Assembler Pattern

```php
<?php

declare(strict_types=1);

namespace Application\Order\Assembler;

use Application\Order\DTO\OrderDTO;
use Application\Order\DTO\OrderLineDTO;
use Domain\Order\Entity\Order;

final readonly class OrderAssembler
{
    public function __construct(
        private OrderLineAssembler $lineAssembler
    ) {}

    public function toDTO(Order $entity): OrderDTO
    {
        return new OrderDTO(
            id: $entity->id()->value,
            customerId: $entity->customerId()->value,
            status: $entity->status()->value,
            lines: array_map(
                fn ($line) => $this->lineAssembler->toDTO($line),
                $entity->lines()
            ),
            totalCents: $entity->total()->cents(),
            createdAt: $entity->createdAt()
        );
    }

    public function toDTOCollection(array $entities): array
    {
        return array_map(fn ($e) => $this->toDTO($e), $entities);
    }
}
```

### Auto-Mapping with Attributes

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Mapper;

#[Attribute(Attribute::TARGET_PROPERTY)]
final readonly class MapFrom
{
    public function __construct(
        public string $source,
        public ?string $transformer = null
    ) {}
}

final readonly class OrderDTO
{
    public function __construct(
        #[MapFrom('id.value')]
        public string $id,

        #[MapFrom('customerId.value')]
        public string $customerId,

        #[MapFrom('status.value')]
        public string $status,

        #[MapFrom('total.cents')]
        public int $totalCents
    ) {}
}
```

## Read Model DTOs

### Read Model (Denormalized View)

```php
<?php

declare(strict_types=1);

namespace Application\Order\ReadModel;

final readonly class OrderSummaryReadModel
{
    public function __construct(
        public string $id,
        public string $customerName,
        public string $customerEmail,
        public int $lineCount,
        public string $formattedTotal,
        public string $status,
        public string $createdAt
    ) {}

    public static function fromRow(array $row): self
    {
        return new self(
            id: $row['order_id'],
            customerName: $row['customer_name'],
            customerEmail: $row['customer_email'],
            lineCount: (int) $row['line_count'],
            formattedTotal: '$' . number_format($row['total_cents'] / 100, 2),
            status: $row['status'],
            createdAt: $row['created_at']
        );
    }
}
```

### Dashboard DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderDashboardDTO
{
    public function __construct(
        public int $totalOrders,
        public int $pendingOrders,
        public int $completedOrders,
        public int $totalRevenueCents,
        public array $recentOrders,
        public array $topCustomers
    ) {}
}
```

## DTO Best Practices

### 1. Immutability

```php
// Always use readonly
final readonly class OrderDTO
{
    public function __construct(
        public string $id,
        public string $status
    ) {}
}

// Never allow mutation
// BAD: public function setStatus(string $status): void
```

### 2. Type Safety

```php
// Use strict types everywhere
final readonly class CreateOrderDTO
{
    /**
     * @param array<array{product_id: string, quantity: int, unit_price: int}> $lines
     */
    public function __construct(
        public string $customerId,
        public array $lines  // Documented array structure
    ) {}
}
```

### 3. Validation at Boundaries

```php
// Validate in Presentation layer
final readonly class CreateOrderRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Uuid]
        public string $customerId,

        #[Assert\NotBlank]
        #[Assert\Count(min: 1)]
        public array $lines
    ) {}
}

// Application DTOs trust the data is valid
final readonly class CreateOrderDTO
{
    public function __construct(
        public string $customerId,  // Already validated
        public array $lines         // Already validated
    ) {}
}
```

### 4. Null Handling

```php
final readonly class OrderDTO
{
    public function __construct(
        public string $id,
        public ?string $shippingAddress,  // Nullable field
        public ?\DateTimeImmutable $shippedAt  // Nullable timestamp
    ) {}

    // Helper for presentation
    public function isShipped(): bool
    {
        return $this->shippedAt !== null;
    }
}
```

## Directory Structure

```
src/
├── Presentation/
│   └── Api/
│       └── Order/
│           ├── Request/
│           │   ├── CreateOrderRequest.php
│           │   └── UpdateOrderRequest.php
│           └── Response/
│               ├── OrderResource.php
│               └── OrderLineResource.php
│
├── Application/
│   └── Order/
│       ├── DTO/
│       │   ├── CreateOrderDTO.php
│       │   ├── OrderDTO.php
│       │   ├── OrderLineDTO.php
│       │   └── OrderListDTO.php
│       ├── Query/
│       │   ├── GetOrderQuery.php
│       │   └── ListOrdersQuery.php
│       ├── ReadModel/
│       │   └── OrderSummaryReadModel.php
│       └── Assembler/
│           └── OrderAssembler.php
```
