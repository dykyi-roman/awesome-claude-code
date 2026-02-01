# Application Patterns

Detailed patterns for Application layer implementation in PHP.

## Use Case (Command Handler)

### Definition
Single application operation that orchestrates domain objects.

### Characteristics
- One public method (`execute` or `__invoke`)
- Receives DTO, returns DTO
- Orchestrates, doesn't decide
- Manages transactions
- No business logic

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Application\Order\DTO\ConfirmOrderCommand;
use Application\Order\DTO\OrderConfirmedResult;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Exception\OrderNotFoundException;

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

```bash
# Good - UseCase structure
Glob: **/Application/**/*UseCase.php
Glob: **/Application/**/*Handler.php

# Warning - Business logic in UseCase
Grep: "if \(.*->get.*\(\) ===|switch \(.*->get" --glob "**/Application/**/*.php"

# Warning - Direct property access
Grep: "->status ===|->state ===" --glob "**/Application/**/*.php"
```

## Query Handler (CQRS Read Side)

### Definition
Read-only operation optimized for queries.

### Characteristics
- No side effects
- Can bypass domain model
- Optimized for reading
- Returns read-specific DTOs

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\Query;

use Application\Order\DTO\OrderListQuery;
use Application\Order\DTO\OrderListItem;

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

### PHP 8.5 Implementation

**Command DTO (Input):**

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

use Domain\Order\ValueObject\OrderId;

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

namespace Application\Order\DTO;

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
| Location | Application | Domain |
| Validation | Format only | Business rules |
| Behavior | None | Domain methods |
| Mutability | Immutable | Immutable |
| Purpose | Data transfer | Domain concept |

### Detection Patterns

```bash
# Good - DTOs exist
Glob: **/Application/**/*DTO.php
Glob: **/Application/**/*Command.php
Glob: **/Application/**/*Query.php
Glob: **/Application/**/*Result.php

# Good - Readonly DTOs
Grep: "final readonly class" --glob "**/Application/**/*DTO.php"

# Bad - DTO with logic
Grep: "public function [a-z]" --glob "**/Application/**/*DTO.php" | grep -v "fromArray\|toArray"
```

## Application Service

### Definition
Orchestrates multiple use cases or complex workflows.

### Characteristics
- Coordinates use cases
- Handles cross-cutting concerns
- May span multiple aggregates
- Transaction boundary

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Checkout\Service;

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
Interface for external service integration, defined in Application.

### Characteristics
- Abstracts external dependency
- Defined in Application layer
- Implemented in Infrastructure
- Uses Application/Domain types

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Payment\Port;

use Application\Payment\DTO\PaymentRequest;
use Application\Payment\DTO\PaymentResponse;

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;

    public function refund(string $transactionId, int $amount): RefundResponse;
}
```

### Port vs Repository

| Aspect | Port | Repository |
|--------|------|------------|
| Defined in | Application | Domain |
| Works with | DTOs | Domain objects |
| Purpose | External services | Persistence |
| Example | PaymentGateway | OrderRepository |

## Event Handler (Application Events)

### Definition
Reacts to domain events with application-level side effects.

### PHP 8.5 Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

use Domain\Order\Event\OrderConfirmedEvent;

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

## Application Layer Structure

```
Application/
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

### Input Validation (Presentation)
- Format validation
- Required fields
- Type coercion

### DTO Validation (Application)
- Cross-field validation
- Format consistency

### Business Validation (Domain)
- Business rules
- Invariants
- State transitions

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