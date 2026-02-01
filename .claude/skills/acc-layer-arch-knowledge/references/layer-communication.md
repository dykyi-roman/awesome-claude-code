# Layer Communication Patterns

Detailed patterns for communication between layers in Layered Architecture.

## Communication Rules

### Strict Layering

```
Presentation → Application → Domain → Infrastructure
     ↓              ↓           ↓           ↓
    Uses         Uses        Uses       Implements
  App DTOs    Domain Objs   Repo Intf   Repo Intf
```

**Rules:**
1. Each layer only calls the layer directly below
2. No skipping layers (Controller → Repository)
3. No upward dependencies (Domain → Application)
4. Use interfaces for dependency inversion

### Relaxed Layering

```
Presentation ─────┬──→ Application
                  └──→ Domain (read-only)

Application ──────┬──→ Domain
                  └──→ Infrastructure

Domain ───────────→ Infrastructure (via interfaces)
```

**Allows:**
- Presentation reading domain objects directly (for simple queries)
- But still no skipping Application for writes

## Data Flow Patterns

### Request Flow (Top-Down)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ Presentation │ ──→ │ Application  │ ──→ │    Domain    │ ──→ │Infrastructure│
│              │     │              │     │              │     │              │
│  Request DTO │     │  App DTO     │     │   Entity     │     │   DB Record  │
│  (validated) │     │  (mapped)    │     │  (created)   │     │  (persisted) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### Response Flow (Bottom-Up)

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│Infrastructure│ ──→ │    Domain    │ ──→ │ Application  │ ──→ │ Presentation │
│              │     │              │     │              │     │              │
│   DB Record  │     │   Entity     │     │   App DTO    │     │  Response    │
│   (loaded)   │     │(reconstituted│     │  (mapped)    │     │  (formatted) │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

## PHP 8.5 Implementation

### Presentation → Application

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\Service\OrderServiceInterface;
use Application\Order\DTO\CreateOrderDTO;
use Presentation\Api\Order\Request\CreateOrderRequest;

final readonly class OrderController
{
    public function __construct(
        private OrderServiceInterface $orderService
    ) {}

    public function create(CreateOrderRequest $request): JsonResponse
    {
        // Map presentation request to application DTO
        $dto = new CreateOrderDTO(
            customerId: $request->customerId(),
            lines: $request->lines()
        );

        // Call application layer
        $result = $this->orderService->createOrder($dto);

        // Map application DTO to presentation response
        return new JsonResponse(
            OrderResource::fromDTO($result)->toArray(),
            201
        );
    }
}
```

### Application → Domain

```php
<?php

declare(strict_types=1);

namespace Application\Order\Service;

use Application\Order\DTO\CreateOrderDTO;
use Application\Order\DTO\OrderDTO;
use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\ValueObject\Money;

final readonly class OrderService implements OrderServiceInterface
{
    public function createOrder(CreateOrderDTO $dto): OrderDTO
    {
        // Map application DTO to domain value objects
        $customerId = new CustomerId($dto->customerId);

        $lines = array_map(fn ($line) => [
            'productId' => new ProductId($line['product_id']),
            'quantity' => $line['quantity'],
            'unitPrice' => new Money($line['unit_price'], $line['currency']),
        ], $dto->lines);

        // Call domain layer
        $order = Order::create(
            id: $this->orderRepository->nextIdentity(),
            customerId: $customerId,
            lines: $lines
        );

        // Use infrastructure through domain interface
        $this->orderRepository->save($order);

        // Map domain entity to application DTO
        return OrderDTO::fromEntity($order);
    }
}
```

### Domain → Infrastructure (via Interface)

```php
<?php

declare(strict_types=1);

// Domain defines interface
namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
}

// Infrastructure implements interface
namespace Infrastructure\Persistence\Order;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }
}
```

## DTO Mapping Strategies

### Manual Mapping

```php
// Presentation → Application
$appDTO = new CreateOrderDTO(
    customerId: $request->get('customer_id'),
    lines: $request->get('lines')
);

// Application → Domain (in use case)
$order = Order::create(
    id: $this->orders->nextIdentity(),
    customerId: new CustomerId($dto->customerId),
    lines: $dto->lines
);

// Domain → Application
return OrderDTO::fromEntity($order);

// Application → Presentation
return OrderResource::fromDTO($orderDTO);
```

### Static Factory Methods

```php
final readonly class OrderDTO
{
    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->id()->value,
            customerId: $order->customerId()->value,
            status: $order->status()->value,
            totalCents: $order->total()->cents(),
            createdAt: $order->createdAt()
        );
    }
}

final readonly class OrderResource
{
    public static function fromDTO(OrderDTO $dto): self
    {
        return new self(
            id: $dto->id,
            status: $dto->status,
            total: $dto->totalCents / 100,
            createdAt: $dto->createdAt->format('c')
        );
    }
}
```

### Assembler Pattern

```php
final readonly class OrderAssembler
{
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

    public function toResource(OrderDTO $dto): OrderResource
    {
        return new OrderResource(
            id: $dto->id,
            status: $dto->status,
            lines: array_map(
                fn ($line) => $this->lineAssembler->toResource($line),
                $dto->lines
            ),
            total: $dto->totalCents / 100,
            createdAt: $dto->createdAt->format('c')
        );
    }
}
```

## Dependency Direction

### Correct Dependency Direction

```
┌────────────────┐
│  Presentation  │  Depends on Application
│                │  ────────────────────→
└────────┬───────┘
         │
         ▼
┌────────────────┐
│  Application   │  Depends on Domain
│                │  ────────────────────→
└────────┬───────┘
         │
         ▼
┌────────────────┐
│    Domain      │  Depends on nothing
│                │  (defines interfaces)
└────────┬───────┘
         │
         ▼
┌────────────────┐
│ Infrastructure │  Implements Domain interfaces
│                │  ←────────────────────
└────────────────┘
```

### Dependency Inversion for Infrastructure

```php
// Domain layer defines interface
namespace Domain\Order\Repository;

interface OrderRepositoryInterface
{
    public function save(Order $order): void;
}

// Application layer uses interface
namespace Application\Order\Service;

final readonly class OrderService
{
    public function __construct(
        private OrderRepositoryInterface $orders  // Interface, not implementation
    ) {}
}

// Infrastructure implements interface
namespace Infrastructure\Persistence;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function save(Order $order): void
    {
        $this->em->persist($order);
    }
}

// DI Container wires implementation to interface
// services.yaml
// Domain\Order\Repository\OrderRepositoryInterface:
//     class: Infrastructure\Persistence\DoctrineOrderRepository
```

## Cross-Cutting Concerns

### Logging

```php
// Logging in Application layer
final readonly class OrderService implements OrderServiceInterface
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private LoggerInterface $logger
    ) {}

    public function createOrder(CreateOrderDTO $dto): OrderDTO
    {
        $this->logger->info('Creating order', ['customer' => $dto->customerId]);

        $order = Order::create(...);
        $this->orders->save($order);

        $this->logger->info('Order created', ['order_id' => $order->id()->value]);

        return OrderDTO::fromEntity($order);
    }
}
```

### Transaction Management

```php
// Transaction boundary in Application layer
final readonly class OrderService implements OrderServiceInterface
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private TransactionManagerInterface $transaction
    ) {}

    public function createOrder(CreateOrderDTO $dto): OrderDTO
    {
        return $this->transaction->transactional(function () use ($dto) {
            $order = Order::create(...);
            $this->orders->save($order);
            return OrderDTO::fromEntity($order);
        });
    }
}
```

## Detection Patterns

```bash
# Check layer dependencies
Grep: "use Presentation\\\\" --glob "**/Application/**/*.php"  # Should be 0
Grep: "use Application\\\\" --glob "**/Domain/**/*.php"        # Should be 0
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"     # Should be 0

# Check for layer skipping
Grep: "Repository" --glob "**/Presentation/**/*.php"           # Warning

# Verify interfaces in domain
Glob: **/Domain/**/Repository/*Interface.php
```
