# Layer Responsibilities

Detailed description of each layer's responsibilities in Layered Architecture.

## Presentation Layer

### Purpose

Handle all user interaction and display concerns. This is the entry point to the application.

### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Request handling | Receive and parse incoming requests |
| Input validation | Validate format, required fields, types |
| Authorization | Check user permissions |
| Response formatting | Transform data for output |
| Error presentation | Format errors for users |
| Session/State management | Manage user sessions |

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Controller | Handle HTTP requests | `OrderController` |
| Action | Single endpoint handler | `CreateOrderAction` |
| View | Render output | `order/show.twig` |
| Presenter | Format data for view | `OrderPresenter` |
| Request | Validated input | `CreateOrderRequest` |
| Response | Formatted output | `OrderResource` |

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\Service\OrderServiceInterface;
use Presentation\Api\Order\Request\CreateOrderRequest;
use Presentation\Api\Order\Response\OrderResource;
use Symfony\Component\HttpFoundation\JsonResponse;

final readonly class OrderController
{
    public function __construct(
        private OrderServiceInterface $orderService
    ) {}

    public function store(CreateOrderRequest $request): JsonResponse
    {
        // Validation already done by Request class
        $order = $this->orderService->createOrder(
            customerId: $request->customerId(),
            lines: $request->lines()
        );

        return new JsonResponse(
            OrderResource::fromDTO($order)->toArray(),
            JsonResponse::HTTP_CREATED
        );
    }
}
```

### Request Object

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
        private string $customerId,

        #[Assert\NotBlank]
        #[Assert\Count(min: 1)]
        private array $lines
    ) {}

    public function customerId(): string
    {
        return $this->customerId;
    }

    public function lines(): array
    {
        return $this->lines;
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
        public string $status,
        public array $lines,
        public int $totalCents,
        public string $createdAt
    ) {}

    public static function fromDTO(OrderDTO $dto): self
    {
        return new self(
            id: $dto->id,
            status: $dto->status,
            lines: array_map(
                fn ($line) => OrderLineResource::fromDTO($line)->toArray(),
                $dto->lines
            ),
            totalCents: $dto->totalCents,
            createdAt: $dto->createdAt->format('c')
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'status' => $this->status,
            'lines' => $this->lines,
            'total' => $this->totalCents,
            'created_at' => $this->createdAt,
        ];
    }
}
```

## Application Layer

### Purpose

Orchestrate business operations and coordinate between layers. Contains no business logic itself.

### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Orchestration | Coordinate domain operations |
| Transaction management | Define transaction boundaries |
| DTO transformation | Map between layers |
| Security | Business-level authorization |
| Event publishing | Dispatch application events |
| Workflow coordination | Multi-step processes |

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Service | Orchestrate operations | `OrderService` |
| DTO | Transfer data | `CreateOrderDTO` |
| Facade | Simplified interface | `CheckoutFacade` |
| Event Handler | React to events | `SendEmailOnOrderCreated` |

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\Service;

use Application\Order\DTO\CreateOrderDTO;
use Application\Order\DTO\OrderDTO;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Shared\TransactionManagerInterface;
use Application\Shared\EventDispatcherInterface;

final readonly class OrderService implements OrderServiceInterface
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository,
        private TransactionManagerInterface $transactionManager,
        private EventDispatcherInterface $eventDispatcher
    ) {}

    public function createOrder(CreateOrderDTO $dto): OrderDTO
    {
        return $this->transactionManager->transactional(function () use ($dto) {
            // Create domain object
            $order = Order::create(
                id: $this->orderRepository->nextIdentity(),
                customerId: $dto->customerId,
                lines: $dto->lines
            );

            // Persist
            $this->orderRepository->save($order);

            // Publish events
            foreach ($order->releaseEvents() as $event) {
                $this->eventDispatcher->dispatch($event);
            }

            // Return DTO
            return OrderDTO::fromEntity($order);
        });
    }
}
```

### Application DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

use Domain\Order\Entity\Order;

final readonly class OrderDTO
{
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

## Domain Layer

### Purpose

Contain all business logic and rules. The heart of the application.

### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Business logic | Core algorithms and rules |
| Invariant protection | Ensure valid state |
| Domain events | Record what happened |
| Business validation | Validate business rules |
| Domain calculations | Business calculations |

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Entity | Identity + behavior | `Order` |
| Value Object | Immutable concept | `Money` |
| Domain Service | Cross-entity logic | `PricingService` |
| Repository Interface | Persistence contract | `OrderRepositoryInterface` |
| Domain Event | What happened | `OrderCreatedEvent` |
| Specification | Business rule | `OrderEligibleForDiscount` |

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Event\OrderCreatedEvent;
use Domain\Order\Exception\CannotConfirmEmptyOrderException;

final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    private array $events = [];
    private \DateTimeImmutable $createdAt;

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId
    ) {
        $this->status = OrderStatus::Draft;
        $this->createdAt = new \DateTimeImmutable();
    }

    public static function create(OrderId $id, CustomerId $customerId, array $lines): self
    {
        $order = new self($id, $customerId);

        foreach ($lines as $lineData) {
            $order->addLine($lineData);
        }

        $order->events[] = new OrderCreatedEvent(
            orderId: $id->value,
            customerId: $customerId->value,
            createdAt: $order->createdAt
        );

        return $order;
    }

    public function confirm(): void
    {
        if (empty($this->lines)) {
            throw new CannotConfirmEmptyOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn (Money $sum, OrderLine $line) => $sum->add($line->total()),
            Money::zero('USD')
        );
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

## Infrastructure Layer

### Purpose

Provide technical capabilities to upper layers. Implements interfaces defined in domain.

### Responsibilities

| Responsibility | Description |
|----------------|-------------|
| Data persistence | Database operations |
| External services | API integrations |
| Caching | Cache operations |
| Messaging | Queue operations |
| File storage | File operations |
| Framework integration | Framework-specific code |

### Components

| Component | Purpose | Example |
|-----------|---------|---------|
| Repository Impl | Persistence | `DoctrineOrderRepository` |
| API Client | External service | `StripePaymentClient` |
| Cache Adapter | Caching | `RedisOrderCache` |
| Message Publisher | Async messaging | `RabbitMQPublisher` |

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Order;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function findByCustomerId(CustomerId $customerId): array
    {
        return $this->em->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.customerId = :customerId')
            ->setParameter('customerId', $customerId->value)
            ->getQuery()
            ->getResult();
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

## Layer Organization

### Directory Structure

```
src/
├── Presentation/
│   ├── Api/
│   │   └── Order/
│   │       ├── OrderController.php
│   │       ├── Request/
│   │       │   └── CreateOrderRequest.php
│   │       └── Response/
│   │           └── OrderResource.php
│   ├── Web/
│   │   └── Order/
│   │       └── OrderWebController.php
│   └── Console/
│       └── ProcessOrdersCommand.php
│
├── Application/
│   └── Order/
│       ├── Service/
│       │   ├── OrderServiceInterface.php
│       │   └── OrderService.php
│       ├── DTO/
│       │   ├── CreateOrderDTO.php
│       │   └── OrderDTO.php
│       └── EventHandler/
│           └── SendEmailOnOrderCreated.php
│
├── Domain/
│   └── Order/
│       ├── Entity/
│       │   ├── Order.php
│       │   └── OrderLine.php
│       ├── ValueObject/
│       │   ├── OrderId.php
│       │   └── Money.php
│       ├── Repository/
│       │   └── OrderRepositoryInterface.php
│       ├── Event/
│       │   └── OrderCreatedEvent.php
│       └── Enum/
│           └── OrderStatus.php
│
└── Infrastructure/
    ├── Persistence/
    │   └── Order/
    │       └── DoctrineOrderRepository.php
    ├── ExternalService/
    │   └── Payment/
    │       └── StripePaymentClient.php
    └── Cache/
        └── RedisOrderCache.php
```
