# Layer Boundaries

Detailed description of each layer's responsibilities and boundaries in Clean Architecture.

## Layer Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                     FRAMEWORKS & DRIVERS                             │
│  Symfony, Laravel, Doctrine, PHPUnit, HTTP server, Database drivers  │
├──────────────────────────────────────────────────────────────────────┤
│                     INTERFACE ADAPTERS                               │
│  Controllers, Repositories (impl), Presenters, ViewModels, Gateways │
├──────────────────────────────────────────────────────────────────────┤
│                     APPLICATION BUSINESS RULES                       │
│  Use Cases, Application Services, DTOs, Ports (interfaces)          │
├──────────────────────────────────────────────────────────────────────┤
│                     ENTERPRISE BUSINESS RULES                        │
│  Entities, Value Objects, Domain Services, Domain Events, Specs     │
└──────────────────────────────────────────────────────────────────────┘
```

## Enterprise Business Rules (Domain Layer)

### Purpose

Contains the most general and high-level business rules. Would exist even if there were no automated system.

### Contents

| Component | Description | Example |
|-----------|-------------|---------|
| **Entity** | Objects with identity and lifecycle | Order, Customer, Product |
| **Value Object** | Immutable objects without identity | Money, Email, Address |
| **Aggregate** | Cluster of entities/VOs with root | Order with OrderLines |
| **Domain Service** | Stateless domain logic across entities | PricingService, DiscountCalculator |
| **Domain Event** | Record of something that happened | OrderConfirmed, PaymentReceived |
| **Repository Interface** | Abstract persistence contract | OrderRepositoryInterface |
| **Specification** | Business rule encapsulation | IsOrderEligibleForDiscount |
| **Enum** | Fixed set of domain values | OrderStatus, PaymentMethod |
| **Exception** | Domain-specific errors | InsufficientFundsException |

### Rules

1. **No external dependencies** — Pure PHP only
2. **No framework code** — No Doctrine, Symfony, Laravel imports
3. **No infrastructure** — No database, cache, queue knowledge
4. **Self-validating** — Entities and VOs validate themselves
5. **Rich behavior** — Logic lives in entities, not services

### PHP 8.5 Example

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\Money;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Event\OrderConfirmedEvent;

final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function addLine(Product $product, int $quantity): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotModifyConfirmedOrderException();
        }

        $this->lines[] = new OrderLine($product, $quantity);
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException($this->status, OrderStatus::Confirmed);
        }

        if (empty($this->lines)) {
            throw new CannotConfirmEmptyOrderException();
        }

        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id, $this->total());
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn (Money $carry, OrderLine $line) => $carry->add($line->total()),
            Money::zero('USD')
        );
    }
}
```

## Application Business Rules (Application Layer)

### Purpose

Contains application-specific business rules. Orchestrates the flow of data to and from entities, directing them to use their enterprise-wide rules.

### Contents

| Component | Description | Example |
|-----------|-------------|---------|
| **Use Case** | Single application operation | CreateOrderUseCase |
| **Application Service** | Orchestrates multiple use cases | CheckoutService |
| **Command** | Input DTO for write operation | CreateOrderCommand |
| **Query** | Input DTO for read operation | GetOrderDetailsQuery |
| **Result DTO** | Output DTO | OrderCreatedResult |
| **Port** | Interface for external services | PaymentGatewayInterface |
| **Event Handler** | Reacts to domain events | SendEmailOnOrderConfirmed |

### Rules

1. **Depends only on Domain** — No infrastructure imports
2. **Framework agnostic** — No HTTP, no CLI specifics
3. **Orchestrates, doesn't decide** — Business logic in Domain
4. **Defines Ports** — Interfaces for external services
5. **Manages transactions** — Transaction boundaries here

### PHP 8.5 Example

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Application\Order\Command\CreateOrderCommand;
use Application\Shared\EventDispatcherInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        return $this->transaction->transactional(function () use ($command) {
            $order = new Order(
                id: OrderId::generate(),
                customerId: $command->customerId
            );

            foreach ($command->lines as $lineData) {
                $order->addLine($lineData->product, $lineData->quantity);
            }

            $order->confirm();

            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return $order->id();
        });
    }
}
```

### Port Definition

```php
<?php

declare(strict_types=1);

namespace Application\Order\Port;

use Application\Order\DTO\ShippingRequest;
use Application\Order\DTO\ShippingResponse;

interface ShippingServiceInterface
{
    public function calculateRates(ShippingRequest $request): array;
    public function createShipment(ShippingRequest $request): ShippingResponse;
}
```

## Interface Adapters Layer

### Purpose

Converts data from the format most convenient for use cases and entities, to the format most convenient for external agencies like databases or the web.

### Contents

| Component | Description | Example |
|-----------|-------------|---------|
| **Controller** | HTTP request handler | OrderController |
| **Action** | Single endpoint handler | CreateOrderAction |
| **Repository Impl** | Implements domain interface | DoctrineOrderRepository |
| **Gateway** | Implements application port | StripePaymentGateway |
| **Presenter** | Formats output | OrderJsonPresenter |
| **ViewModel** | View-specific data structure | OrderViewModel |

### Rules

1. **Implements interfaces from inner layers** — Domain/Application contracts
2. **Converts data formats** — Entity ↔ Database, DTO ↔ JSON
3. **No business logic** — Only transformation and routing
4. **Framework knowledge allowed** — But keep it minimal

### PHP 8.5 Examples

**Controller (Driving Adapter):**

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\UseCase\CreateOrderUseCase;
use Application\Order\Command\CreateOrderCommand;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $command = CreateOrderCommand::fromArray($request->toArray());

        $orderId = $this->createOrder->execute($command);

        return new JsonResponse(
            ['order_id' => $orderId->value],
            JsonResponse::HTTP_CREATED
        );
    }
}
```

**Repository Implementation (Driven Adapter):**

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

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

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }
}
```

**Gateway (Driven Adapter):**

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment;

use Application\Order\Port\PaymentGatewayInterface;
use Application\Order\DTO\PaymentRequest;
use Application\Order\DTO\PaymentResponse;
use Stripe\StripeClient;

final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private StripeClient $stripe
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        $charge = $this->stripe->charges->create([
            'amount' => $request->amount->cents(),
            'currency' => $request->currency->value,
            'source' => $request->token,
        ]);

        return new PaymentResponse(
            transactionId: $charge->id,
            status: $this->mapStatus($charge->status)
        );
    }
}
```

## Frameworks & Drivers Layer

### Purpose

The outermost layer where all the details live. We keep these things on the outside where they can do little harm.

### Contents

| Component | Description | Example |
|-----------|-------------|---------|
| **Framework config** | Routing, services, DI | routes.yaml, services.yaml |
| **Database config** | Connection, migrations | doctrine.yaml, migrations/ |
| **Web server** | HTTP handling | index.php, nginx.conf |
| **External services** | Third-party SDKs | Stripe SDK, AWS SDK |

### Rules

1. **Configuration only** — No business logic
2. **Wiring** — Dependency injection setup
3. **Glue code** — Connects everything together
4. **Easily replaceable** — Swap frameworks without touching core

### Example: Service Wiring

```yaml
# config/services.yaml (Symfony)
services:
    # Domain interfaces → Infrastructure implementations
    Domain\Order\Repository\OrderRepositoryInterface:
        class: Infrastructure\Persistence\DoctrineOrderRepository

    # Application ports → Infrastructure adapters
    Application\Order\Port\PaymentGatewayInterface:
        class: Infrastructure\Payment\StripePaymentGateway

    # Use Cases
    Application\Order\UseCase\CreateOrderUseCase:
        autowire: true
```

## Directory Structure

```
src/
├── Domain/                          # Enterprise Business Rules
│   ├── Order/
│   │   ├── Entity/
│   │   │   ├── Order.php
│   │   │   └── OrderLine.php
│   │   ├── ValueObject/
│   │   │   ├── OrderId.php
│   │   │   └── Money.php
│   │   ├── Repository/
│   │   │   └── OrderRepositoryInterface.php
│   │   ├── Service/
│   │   │   └── DiscountCalculator.php
│   │   ├── Event/
│   │   │   └── OrderConfirmedEvent.php
│   │   └── Enum/
│   │       └── OrderStatus.php
│   └── Shared/
│       └── ValueObject/
│           └── AggregateId.php
│
├── Application/                     # Application Business Rules
│   ├── Order/
│   │   ├── UseCase/
│   │   │   ├── CreateOrderUseCase.php
│   │   │   └── ConfirmOrderUseCase.php
│   │   ├── Command/
│   │   │   ├── CreateOrderCommand.php
│   │   │   └── ConfirmOrderCommand.php
│   │   ├── Query/
│   │   │   └── GetOrderDetailsQuery.php
│   │   ├── DTO/
│   │   │   └── OrderDetailsDTO.php
│   │   ├── Port/
│   │   │   └── ShippingServiceInterface.php
│   │   └── EventHandler/
│   │       └── SendOrderConfirmationEmail.php
│   └── Shared/
│       ├── TransactionManagerInterface.php
│       └── EventDispatcherInterface.php
│
├── Infrastructure/                  # Interface Adapters (Driven)
│   ├── Persistence/
│   │   ├── DoctrineOrderRepository.php
│   │   └── Mapping/
│   │       └── Order.orm.xml
│   ├── Payment/
│   │   └── StripePaymentGateway.php
│   ├── Shipping/
│   │   └── FedExShippingService.php
│   └── Messaging/
│       └── RabbitMqEventDispatcher.php
│
├── Presentation/                    # Interface Adapters (Driving)
│   ├── Api/
│   │   └── Order/
│   │       ├── CreateOrderAction.php
│   │       └── GetOrderAction.php
│   ├── Web/
│   │   └── Order/
│   │       └── OrderController.php
│   └── Console/
│       └── ProcessOrdersCommand.php
│
└── Framework/                       # Frameworks & Drivers
    ├── Kernel.php
    └── config/
        ├── routes.yaml
        ├── services.yaml
        └── packages/
```

## Detection Patterns

```bash
# Check layer boundaries - Domain should be pure
Grep: "use (Infrastructure|Presentation|Application)\\\\" --glob "**/Domain/**/*.php"

# Check layer boundaries - Application should not use Infrastructure
Grep: "use Infrastructure\\\\" --glob "**/Application/**/*.php"

# Check for framework in Domain
Grep: "use (Doctrine|Symfony|Illuminate)\\\\" --glob "**/Domain/**/*.php"

# Check for HTTP in Application
Grep: "Request|Response|JsonResponse" --glob "**/Application/**/*.php"

# Verify Ports exist in Application
Glob: **/Application/**/Port/*Interface.php

# Verify Adapters implement Ports
Grep: "implements.*Interface" --glob "**/Infrastructure/**/*.php"
```
