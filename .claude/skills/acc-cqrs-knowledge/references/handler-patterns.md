# Handler Patterns

Detailed patterns for CQRS Command and Query Handler implementation in PHP.

## Handler Definition

### What is a Handler?

A Handler executes the logic for a single Command or Query. One handler per message.

### Characteristics

- **Single responsibility**: handles exactly one message type
- **Single public method**: `execute()`, `handle()`, or `__invoke()`
- **Injected dependencies**: repositories, services, event dispatchers
- **CommandHandler**: modifies state, dispatches events
- **QueryHandler**: reads state, no side effects

## PHP 8.4 Implementation

### Command Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Command\CreateOrderCommand;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Shared\EventDispatcherInterface;

final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: $command->customerId,
            lines: $command->lines
        );

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }

        return $order->id();
    }
}
```

### Query Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

use Application\Order\Query\GetOrderDetailsQuery;
use Application\Order\DTO\OrderDetailsDTO;
use Application\Order\ReadModel\OrderReadModelInterface;

final readonly class GetOrderDetailsHandler
{
    public function __construct(
        private OrderReadModelInterface $readModel
    ) {}

    public function __invoke(GetOrderDetailsQuery $query): ?OrderDetailsDTO
    {
        return $this->readModel->findById($query->orderId);
    }
}
```

## Handler Structure Patterns

### Transaction Management

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

final readonly class ConfirmOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function __invoke(ConfirmOrderCommand $command): void
    {
        $this->transaction->transactional(function () use ($command) {
            $order = $this->orders->findById($command->orderId);

            if ($order === null) {
                throw new OrderNotFoundException($command->orderId);
            }

            $order->confirm();

            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }
        });
    }
}
```

### Authorization in Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

final readonly class CancelOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private AuthorizationServiceInterface $auth,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(CancelOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        // Authorization check
        if (!$this->auth->canCancel($command->userId, $order)) {
            throw new UnauthorizedException('Cannot cancel this order');
        }

        $order->cancel($command->reason);

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }
    }
}
```

### Handler with External Service

```php
<?php

declare(strict_types=1);

namespace Application\Payment\Handler;

final readonly class ProcessPaymentHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private PaymentGatewayInterface $paymentGateway,
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(ProcessPaymentCommand $command): PaymentResult
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        // Call external service
        $paymentResult = $this->paymentGateway->charge(
            new PaymentRequest(
                amount: $order->total(),
                currency: $order->currency(),
                method: $command->paymentMethod
            )
        );

        if ($paymentResult->isSuccessful()) {
            $order->markAsPaid($paymentResult->transactionId());
            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }
        }

        return $paymentResult;
    }
}
```

## Async Handler Patterns

### Async Command Handler

```php
<?php

declare(strict_types=1);

namespace Application\Email\Handler;

use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
final readonly class SendWelcomeEmailHandler
{
    public function __construct(
        private EmailServiceInterface $emailService,
        private UserReadModelInterface $users
    ) {}

    public function __invoke(SendWelcomeEmailCommand $command): void
    {
        $user = $this->users->findById($command->userId);

        if ($user === null) {
            return; // User deleted before email sent
        }

        $this->emailService->send(
            to: $user->email,
            template: 'welcome',
            data: ['name' => $user->name]
        );
    }
}
```

### Retry Configuration

```php
<?php

declare(strict_types=1);

namespace Application\Payment\Handler;

use Symfony\Component\Messenger\Attribute\AsMessageHandler;
use Symfony\Component\Messenger\Exception\RecoverableMessageHandlingException;

#[AsMessageHandler]
final readonly class ProcessWebhookHandler
{
    public function __invoke(ProcessWebhookCommand $command): void
    {
        try {
            $this->processWebhook($command);
        } catch (TemporaryFailureException $e) {
            // Will be retried
            throw new RecoverableMessageHandlingException(
                message: 'Temporary failure, will retry',
                previous: $e
            );
        }
    }
}
```

## Handler Composition

### Handler Calling Domain Service

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

final readonly class ApplyDiscountHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private DiscountServiceInterface $discountService,  // Domain service
        private EventDispatcherInterface $events
    ) {}

    public function __invoke(ApplyDiscountCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        // Domain service calculates discount
        $discount = $this->discountService->calculate(
            order: $order,
            code: $command->discountCode
        );

        // Entity applies it
        $order->applyDiscount($discount);

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }
    }
}
```

### Handler with Multiple Aggregates (Anti-Pattern)

```php
// BAD - Handler modifies multiple aggregates
final readonly class CreateOrderAndReserveStockHandler
{
    public function __invoke(CreateOrderCommand $command): void
    {
        // Creates order aggregate
        $order = Order::create(...);
        $this->orders->save($order);

        // BAD: Also modifies inventory aggregate
        foreach ($command->lines as $line) {
            $product = $this->products->findById($line->productId);
            $product->reserveStock($line->quantity);  // Different aggregate!
            $this->products->save($product);
        }
    }
}

// GOOD - Use events for cross-aggregate operations
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(...);
        $this->orders->save($order);

        // Dispatch event, let another handler reserve stock
        $this->events->dispatch(new OrderCreatedEvent($order->id()));

        return $order->id();
    }
}

// Separate handler for stock reservation
final readonly class ReserveStockOnOrderCreatedHandler
{
    public function __invoke(OrderCreatedEvent $event): void
    {
        // Handle stock reservation separately
    }
}
```

## Error Handling

### Domain Exception Handling

```php
<?php

declare(strict_types=1);

namespace Application\Order\Handler;

final readonly class ConfirmOrderHandler
{
    public function __invoke(ConfirmOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        try {
            $order->confirm();
        } catch (InvalidStateTransitionException $e) {
            // Domain exception - rethrow as application exception
            throw new CannotConfirmOrderException(
                orderId: $command->orderId,
                reason: $e->getMessage(),
                previous: $e
            );
        }

        $this->orders->save($order);
    }
}
```

## Detection Patterns

```bash
# Good - Handler classes exist
Glob: **/Handler/**/*Handler.php
Grep: "final readonly class.*Handler" --glob "**/*.php"

# Good - Single __invoke method
Grep: "public function __invoke" --glob "**/*Handler.php"

# Warning - Multiple public methods (except constructor)
Grep: "public function (?!__construct|__invoke)" --glob "**/*Handler.php"

# Warning - Handler modifying multiple aggregates
Grep: "->save\(" --glob "**/*Handler.php" | head -1
# If count > 1 per handler, investigate

# Bad - Business logic in handler
Grep: "if \(.*->get.*\(\) ===|switch \(.*->get" --glob "**/*Handler.php"

# Bad - Query handler with side effects
Grep: "->save\(|->persist\(|->dispatch\(" --glob "**/Query/**/*Handler.php"
```

## Handler Organization

### Directory Structure

```
Application/
├── Order/
│   ├── Command/
│   │   ├── CreateOrderCommand.php
│   │   └── ConfirmOrderCommand.php
│   ├── Query/
│   │   ├── GetOrderDetailsQuery.php
│   │   └── ListOrdersQuery.php
│   └── Handler/
│       ├── CreateOrderHandler.php
│       ├── ConfirmOrderHandler.php
│       ├── GetOrderDetailsHandler.php
│       └── ListOrdersHandler.php
```

### Alternative: Handlers Next to Messages

```
Application/
├── Order/
│   ├── Command/
│   │   ├── CreateOrderCommand.php
│   │   ├── CreateOrderHandler.php
│   │   ├── ConfirmOrderCommand.php
│   │   └── ConfirmOrderHandler.php
│   └── Query/
│       ├── GetOrderDetailsQuery.php
│       ├── GetOrderDetailsHandler.php
│       ├── ListOrdersQuery.php
│       └── ListOrdersHandler.php
```
