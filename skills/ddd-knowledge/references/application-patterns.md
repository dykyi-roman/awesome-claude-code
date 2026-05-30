# Application Patterns

Detailed patterns for orchestrating the domain — Use Cases, Query Handlers, DTOs, Ports, Event Handlers, Application Services. These cover the **orchestration** responsibility from [`layer-architecture.md`](layer-architecture.md). Physical placement varies by architecture (Layered 3-tier merges entry-points into Application; N-Tier keeps Presentation as a separate layer; PBF scopes everything per feature; MVC may not have a distinct Application layer at all).

## Use Case (Command Handler)

### Definition
Single application operation that orchestrates domain objects.

### Characteristics
- One public method (`execute` or `__invoke`)
- Receives DTO, returns DTO
- Orchestrates, doesn't decide
- Manages transactions
- No business logic

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace UseCase;

use DTO\ConfirmOrderCommand;
use DTO\OrderConfirmedResult;
use Repository\OrderRepositoryInterface;
use Exception\OrderNotFoundException;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository,
        private EventDispatcherInterface $eventDispatcher,
        private TransactionManagerInterface $transactionManager
    ) {}

    public function execute(ConfirmOrderCommand $command): OrderConfirmedResult
    {
        return $this->transactionManager->transactional(function () use ($command) {
            $order = $this->orderRepository->findById($command->orderId);

            if ($order === null) {
                throw new OrderNotFoundException($command->orderId);
            }

            // Domain does the business logic
            $order->confirm();

            $this->orderRepository->save($order);

            // Dispatch domain events
            foreach ($order->releaseEvents() as $event) {
                $this->eventDispatcher->dispatch($event);
            }

            return new OrderConfirmedResult(
                orderId: $order->id()->value,
                total: $order->total()->amount,
                confirmedAt: new \DateTimeImmutable()
            );
        });
    }
}
```

### Anti-Pattern: Business Logic in UseCase

```php
// BAD - Business logic in Application layer
final readonly class ConfirmOrderUseCase
{
    public function execute(ConfirmOrderCommand $command): OrderConfirmedResult
    {
        $order = $this->orderRepository->findById($command->orderId);

        // BAD: Business logic belongs in Domain
        if ($order->getStatus() === 'draft') {
            if (count($order->getLines()) > 0) {
                if ($order->getTotal() > 0) {
                    $order->setStatus('confirmed');  // BAD: Anemic model
                }
            }
        }

        // ...
    }
}
```

### Detection Patterns

Suffix-based globs work across architectures:

```bash
# Use Cases and Handlers
Glob: **/*UseCase.php
Glob: **/*Handler.php
Glob: **/UseCase/**/*.php
Glob: **/Handler/**/*.php

# Anti-pattern: business logic inside a Use Case (if/switch on entity state)
Grep: "if \(.*->get.*\(\) ===|switch \(.*->get" --glob "**/*UseCase.php"
Grep: "if \(.*->get.*\(\) ===|switch \(.*->get" --glob "**/*Handler.php"

# Anti-pattern: direct property access on entities inside orchestration
Grep: "->status ===|->state ===" --glob "**/*UseCase.php"
```

## Query Handler (CQRS Read Side)

### Definition
Read-only operation optimized for queries.

### Characteristics
- No side effects
- Can bypass domain model
- Optimized for reading
- Returns read-specific DTOs

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Query;

use DTO\OrderListQuery;
use DTO\OrderListItem;

final readonly class GetOrderListHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    /**
     * @return array<OrderListItem>
     */
    public function handle(OrderListQuery $query): array
    {
        return $this->readModel->findForCustomer(
            customerId: $query->customerId,
            status: $query->status,
            limit: $query->limit,
            offset: $query->offset
        );
    }
}
```

## Data Transfer Object (DTO)

### Definition
Simple object for transferring data between layers.

### Characteristics
- No behavior
- Immutable
- Public properties or getters
- Validates format, not business rules

### PHP 8.4 Implementation

**Command DTO (Input):**

```php
<?php

declare(strict_types=1);

namespace DTO;

use ValueObject\OrderId;

final readonly class ConfirmOrderCommand
{
    public function __construct(
        public OrderId $orderId,
        public ?string $notes = null
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            orderId: new OrderId($data['order_id']),
            notes: $data['notes'] ?? null
        );
    }
}
```

**Result DTO (Output):**

```php
<?php

declare(strict_types=1);

namespace DTO;

final readonly class OrderConfirmedResult
{
    public function __construct(
        public string $orderId,
        public int $total,
        public \DateTimeImmutable $confirmedAt
    ) {}

    public function toArray(): array
    {
        return [
            'order_id' => $this->orderId,
            'total' => $this->total,
            'confirmed_at' => $this->confirmedAt->format('c'),
        ];
    }
}
```

### DTO vs Value Object

| Aspect | DTO | Value Object |
|--------|-----|--------------|
| Typical placement | orchestration code (Application / use-case / orchestration folder) | with the domain model (Domain / Model / wherever the model lives) |
| Validation | Format only | Business rules |
| Behavior | None | Domain methods |
| Mutability | Immutable | Immutable |
| Purpose | Data transfer | Domain concept |

### Detection Patterns

```bash
# DTOs by file or class-name suffix
Glob: **/*DTO.php
Glob: **/*Command.php
Glob: **/*Query.php
Glob: **/*Result.php
Glob: **/DTO/**/*.php

# Readonly DTOs (immutability check)
Grep: "final readonly class" --glob "**/*DTO.php"
Grep: "final readonly class" --glob "**/DTO/**/*.php"

# Anti-pattern: DTO with logic (allow fromArray/toArray mapping helpers)
Grep: "public function [a-z]" --glob "**/*DTO.php" | grep -v "fromArray\|toArray"
```

## Application Service

### Definition
Orchestrates multiple use cases or complex workflows.

### Characteristics
- Coordinates use cases
- Handles cross-cutting concerns
- May span multiple aggregates
- Transaction boundary

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Service;

final readonly class CheckoutService
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
        private ProcessPaymentUseCase $processPayment,
        private SendConfirmationUseCase $sendConfirmation,
        private TransactionManagerInterface $transactionManager
    ) {}

    public function checkout(CheckoutCommand $command): CheckoutResult
    {
        return $this->transactionManager->transactional(function () use ($command) {
            // Orchestrate multiple use cases
            $order = $this->createOrder->execute(
                new CreateOrderCommand($command->customerId, $command->items)
            );

            $payment = $this->processPayment->execute(
                new ProcessPaymentCommand($order->orderId, $command->paymentMethod)
            );

            $this->sendConfirmation->execute(
                new SendConfirmationCommand($order->orderId, $command->email)
            );

            return new CheckoutResult($order->orderId, $payment->transactionId);
        });
    }
}
```

## Port (Interface for External Services)

### Definition
Interface representing the application's need for an external capability — payment gateways, email senders, SMS clients, third-party search, etc. The concept is most explicit in **Hexagonal Architecture**, where Ports are a defining structural element; it is also used in **Clean Architecture** to enforce the Application → Infrastructure dependency inversion. In **Layered 3-tier (Domain-centric)** and **N-Tier (4-tier Classical)**, the same role is filled by ordinary interfaces declared where the consumer needs them.

### Characteristics
- Abstracts an external dependency
- Uses orchestration/domain types in its signature (no framework types)
- Implemented by an adapter that lives wherever the architecture places external integrations

### Placement varies by architecture

| Architecture | Driving Port (input) | Driven Port (output) | Adapter |
|---|---|---|---|
| Clean | typically `Application/{Context}/Port/` (project-conventional) | typically `Application/{Context}/Port/` or `Domain/{Context}/Port/` | `Infrastructure/` |
| Hexagonal | `Application/{Context}/Port/Input/` | `Domain/{Context}/Port/Output/` | `Infrastructure/{Http,Persistence,External}/` |
| Layered (3-tier Domain-centric) | usually no separate Driving Port (entry-points call Use Cases directly inside Application/Http) | interface declared alongside its consumer in Domain | `Infrastructure/` (generic) |
| N-Tier (4-tier Classical) | usually not separated as a Port | interface declared in Domain alongside consumer | `Infrastructure/External/` |
| PBF | per inner architecture, scoped to `{Feature}/` | per inner architecture, scoped to `{Feature}/` | per inner architecture, scoped to `{Feature}/` |

See [`layer-architecture.md`](layer-architecture.md) for the full architecture table.

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace Port;

use DTO\PaymentRequest;
use DTO\PaymentResponse;

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;

    public function refund(string $transactionId, int $amount): RefundResponse;
}
```

### Port vs Repository

| Aspect | Port | Repository |
|--------|------|------------|
| Typical placement | with the orchestration code that needs the external capability | with the domain model |
| Works with | DTOs | Domain objects (aggregate roots) |
| Purpose | External services (payment, email, search, etc.) | Aggregate persistence |
| Example | `PaymentGatewayInterface` | `OrderRepository` |
| Architecture role | Most explicit in Hexagonal; used implicitly in others | Universal across architectures |

## Event Handler (Application Events)

### Definition
Reacts to domain events with application-level side effects.

### PHP 8.4 Implementation

```php
<?php

declare(strict_types=1);

namespace EventHandler;

use Event\OrderConfirmedEvent;

final readonly class SendOrderConfirmationEmail
{
    public function __construct(
        private EmailServiceInterface $emailService,
        private CustomerQueryInterface $customerQuery
    ) {}

    public function __invoke(OrderConfirmedEvent $event): void
    {
        $customer = $this->customerQuery->findByOrderId($event->orderId);

        $this->emailService->send(
            to: $customer->email,
            template: 'order_confirmed',
            data: [
                'order_id' => $event->orderId->value,
                'total' => $event->total->amount,
            ]
        );
    }
}
```

## Example folder shape

The example below shows a **Clean / N-Tier 4-tier**-style arrangement where the Application layer is the orchestration home and each bounded context owns its own UseCase / Query / DTO / EventHandler / Port subfolders. **Layered 3-tier (Domain-centric)** projects place orchestration directly under `Domain/{Context}/Handler/{UseCase}/` (since the Application layer in that architecture is reserved for entry-points). **PBF** projects wrap whichever inner shape is chosen inside `{Feature}/`. **MVC** typically has no Application layer — orchestration lives in the Controller.

```
Application/                      # Clean / N-Tier 4-tier shape
├── Order/
│   ├── UseCase/
│   │   ├── CreateOrderUseCase.php
│   │   ├── ConfirmOrderUseCase.php
│   │   └── CancelOrderUseCase.php
│   ├── Query/
│   │   ├── GetOrderHandler.php
│   │   └── GetOrderListHandler.php
│   ├── DTO/
│   │   ├── CreateOrderCommand.php
│   │   ├── ConfirmOrderCommand.php
│   │   ├── OrderResult.php
│   │   └── OrderListItem.php
│   ├── EventHandler/
│   │   └── SendOrderConfirmationEmail.php
│   └── Port/
│       └── InventoryServiceInterface.php
├── Payment/
│   └── ...
└── Shared/
    ├── TransactionManagerInterface.php
    └── EventDispatcherInterface.php
```

## Validation Strategy

DDD distinguishes three validation responsibilities. Where they physically run varies by architecture (Layered 3-tier and MVC merge entry-points with orchestration; Clean / Hexagonal / N-Tier keep them in separate layers).

### Input format validation (entry-point responsibility)
- Format validation
- Required fields
- Type coercion
- Runs in: `Presentation/` (Clean / N-Tier), `Infrastructure/Http/` (Hexagonal), `Application/Http/` (Layered 3-tier), `Controller/` (MVC)

### DTO / cross-field validation (orchestration responsibility)
- Cross-field validation
- Format consistency
- Runs in: orchestration code (Use Case, Application Service, Handler) regardless of folder

### Business validation (domain responsibility)
- Business rules
- Invariants
- State transitions
- Runs in: the entity / aggregate / domain service — wherever the domain model lives

```php
// Presentation: format
if (!Uuid::isValid($request->get('order_id'))) {
    throw new InvalidInputException('Invalid order_id format');
}

// Application: DTO construction
$command = new ConfirmOrderCommand(
    orderId: new OrderId($request->get('order_id'))  // VO validates
);

// Domain: business rule
$order->confirm();  // Throws if invalid state
```