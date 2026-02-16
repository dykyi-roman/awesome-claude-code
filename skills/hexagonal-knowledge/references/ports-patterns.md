# Ports Patterns

Detailed patterns for Hexagonal Architecture Ports in PHP.

## Port Definition

### What is a Port?

A Port is an interface that defines how the application core interacts with the outside world. Ports are technology-agnostic contracts.

### Port Types

| Type | Direction | Purpose | Example |
|------|-----------|---------|---------|
| **Driving Port** | Inbound | How to use the app | `CreateOrderUseCaseInterface` |
| **Driven Port** | Outbound | What the app needs | `OrderRepositoryInterface` |

## Driving Ports (Primary/Input)

### Definition

Interfaces that define how external actors can interact with the application.

### Location

Application layer — these are the entry points to use cases.

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\Port\Input;

use Application\Order\DTO\CreateOrderRequest;
use Application\Order\DTO\CreateOrderResponse;

interface CreateOrderUseCaseInterface
{
    public function execute(CreateOrderRequest $request): CreateOrderResponse;
}
```

### Use Case Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Application\Order\Port\Input\CreateOrderUseCaseInterface;
use Application\Order\DTO\CreateOrderRequest;
use Application\Order\DTO\CreateOrderResponse;
use Domain\Order\Entity\Order;
use Domain\Order\Port\Output\OrderRepositoryInterface;

final readonly class CreateOrderUseCase implements CreateOrderUseCaseInterface
{
    public function __construct(
        private OrderRepositoryInterface $orders
    ) {}

    public function execute(CreateOrderRequest $request): CreateOrderResponse
    {
        $order = Order::create(
            id: $this->orders->nextIdentity(),
            customerId: $request->customerId,
            lines: $request->lines
        );

        $this->orders->save($order);

        return new CreateOrderResponse(
            orderId: $order->id()->value,
            total: $order->total()->cents()
        );
    }
}
```

### Multiple Driving Ports per Use Case

```php
// Query port
interface GetOrderUseCaseInterface
{
    public function execute(GetOrderRequest $request): OrderResponse;
}

// Command port
interface ConfirmOrderUseCaseInterface
{
    public function execute(ConfirmOrderRequest $request): void;
}

// Combined in one use case class if needed
final readonly class OrderUseCase implements
    GetOrderUseCaseInterface,
    ConfirmOrderUseCaseInterface
{
    public function execute(GetOrderRequest|ConfirmOrderRequest $request): mixed
    {
        // ...
    }
}
```

## Driven Ports (Secondary/Output)

### Definition

Interfaces that define what the application core needs from external systems.

### Location

- **Domain layer**: For persistence (repositories)
- **Application layer**: For external services

### Repository Port (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Port\Output;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    public function findByCustomerId(CustomerId $customerId): array;

    public function save(Order $order): void;

    public function remove(Order $order): void;

    public function nextIdentity(): OrderId;
}
```

### External Service Port (Application Layer)

```php
<?php

declare(strict_types=1);

namespace Application\Payment\Port\Output;

use Application\Payment\DTO\PaymentRequest;
use Application\Payment\DTO\PaymentResponse;

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;

    public function refund(string $transactionId, int $amount): RefundResponse;

    public function getTransaction(string $transactionId): TransactionDetails;
}
```

### Notification Port

```php
<?php

declare(strict_types=1);

namespace Application\Notification\Port\Output;

use Application\Notification\DTO\EmailMessage;
use Application\Notification\DTO\SmsMessage;

interface NotificationServiceInterface
{
    public function sendEmail(EmailMessage $message): void;

    public function sendSms(SmsMessage $message): void;
}
```

### Event Publisher Port

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Port\Output;

use Domain\Shared\Event\DomainEvent;

interface EventPublisherInterface
{
    public function publish(DomainEvent $event): void;

    /**
     * @param array<DomainEvent> $events
     */
    public function publishAll(array $events): void;
}
```

## Port Design Guidelines

### 1. Use Domain/Application Types

```php
// GOOD: Uses domain types
interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
}

// BAD: Uses infrastructure types
interface OrderRepositoryInterface
{
    public function findById(string $id): ?array;  // No domain types
}
```

### 2. Technology Agnostic

```php
// GOOD: No technology hints
interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
}

// BAD: Technology in interface
interface StripeGatewayInterface  // Specific to Stripe
{
    public function createCharge(array $stripeParams): StripeCharge;
}
```

### 3. Single Responsibility

```php
// GOOD: Focused interfaces
interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
}

interface OrderQueryInterface
{
    public function findByStatus(OrderStatus $status): array;
    public function countByCustomer(CustomerId $id): int;
}

// BAD: God interface
interface OrderDataAccessInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
    public function sendNotification(Order $order): void;
    public function generateReport(): array;
}
```

### 4. Coarse-Grained for Driving Ports

```php
// GOOD: Use case level granularity
interface CheckoutUseCaseInterface
{
    public function execute(CheckoutRequest $request): CheckoutResponse;
}

// BAD: Too fine-grained
interface AddToCartInterface { }
interface ValidateCartInterface { }
interface ProcessPaymentInterface { }
interface SendConfirmationInterface { }
```

### 5. Fine-Grained for Driven Ports (ISP)

```php
// GOOD: Segregated interfaces
interface OrderReaderInterface
{
    public function findById(OrderId $id): ?Order;
}

interface OrderWriterInterface
{
    public function save(Order $order): void;
}

// Consumer uses only what it needs
final readonly class GetOrderUseCase
{
    public function __construct(
        private OrderReaderInterface $reader  // Only reader
    ) {}
}
```

## Port Organization

### Directory Structure

```
Application/
├── Order/
│   ├── Port/
│   │   ├── Input/                      # Driving ports
│   │   │   ├── CreateOrderUseCaseInterface.php
│   │   │   ├── GetOrderUseCaseInterface.php
│   │   │   └── ConfirmOrderUseCaseInterface.php
│   │   └── Output/                     # Driven ports (app level)
│   │       └── InventoryServiceInterface.php
│   └── UseCase/                        # Implementations
│       ├── CreateOrderUseCase.php
│       └── GetOrderUseCase.php

Domain/
├── Order/
│   └── Port/
│       └── Output/                     # Driven ports (domain level)
│           └── OrderRepositoryInterface.php
```

## Detection Patterns

```bash
# Find driving ports
Glob: **/Port/Input/*Interface.php
Grep: "interface.*UseCaseInterface" --glob "**/*.php"

# Find driven ports
Glob: **/Port/Output/*Interface.php
Grep: "interface.*(Repository|Gateway|Service)Interface" --glob "**/*.php"

# Check ports use domain types
Grep: "function.*\(.*string \$id\)" --glob "**/Port/**/*.php"  # Should be minimal

# Verify ports are in correct layer
Grep: "namespace.*Domain.*Port" --glob "**/Domain/**/*.php"
Grep: "namespace.*Application.*Port" --glob "**/Application/**/*.php"
```
