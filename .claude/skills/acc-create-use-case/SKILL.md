---
name: acc-create-use-case
description: Generates Application Use Cases for PHP 8.4. Creates orchestration services that coordinate domain objects, handle transactions, and dispatch events. Includes unit tests.
---

# Use Case Generator

Generate Application-layer Use Cases that orchestrate domain operations.

## Use Case Characteristics

- **Single responsibility**: One operation per use case
- **Orchestration**: Coordinates domain objects
- **Transaction boundary**: Manages atomicity
- **Event dispatch**: Publishes domain events
- **No business logic**: Delegates to domain
- **Framework agnostic**: No HTTP/CLI concerns

## Template

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\UseCase;

use Application\{BoundedContext}\DTO\{InputDTO};
use Application\{BoundedContext}\DTO\{OutputDTO};
use Domain\{BoundedContext}\Repository\{Repository}Interface;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;

final readonly class {Name}UseCase
{
    public function __construct(
        private {Repository}Interface ${repository},
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute({InputDTO} $input): {OutputDTO}
    {
        return $this->transaction->transactional(function () use ($input) {
            {useCaseLogic}

            foreach ($aggregate->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return {result};
        });
    }
}
```

## Complete Use Case Examples

### CreateOrder UseCase

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Application\Order\DTO\CreateOrderInput;
use Application\Order\DTO\OrderCreatedOutput;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\ValueObject\Money;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(CreateOrderInput $input): OrderCreatedOutput
    {
        return $this->transaction->transactional(function () use ($input) {
            $order = Order::create(
                id: $this->orders->nextIdentity(),
                customerId: $input->customerId
            );

            foreach ($input->lines as $lineData) {
                $order->addLine(
                    productId: new ProductId($lineData['productId']),
                    productName: $lineData['productName'],
                    quantity: $lineData['quantity'],
                    unitPrice: new Money($lineData['unitPriceCents'], $lineData['currency'])
                );
            }

            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return new OrderCreatedOutput(
                orderId: $order->id()->value,
                total: $order->total()->cents(),
                currency: $order->total()->currency(),
                lineCount: $order->lineCount()
            );
        });
    }
}
```

### ConfirmOrder UseCase

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Application\Order\DTO\ConfirmOrderInput;
use Application\Order\DTO\OrderConfirmedOutput;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Exception\OrderNotFoundException;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(ConfirmOrderInput $input): OrderConfirmedOutput
    {
        return $this->transaction->transactional(function () use ($input) {
            $order = $this->orders->findById($input->orderId);

            if ($order === null) {
                throw new OrderNotFoundException($input->orderId);
            }

            $order->confirm();

            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return new OrderConfirmedOutput(
                orderId: $order->id()->value,
                status: $order->status()->value,
                confirmedAt: new \DateTimeImmutable()
            );
        });
    }
}
```

### ProcessPayment UseCase (with external service)

```php
<?php

declare(strict_types=1);

namespace Application\Payment\UseCase;

use Application\Payment\DTO\ProcessPaymentInput;
use Application\Payment\DTO\PaymentProcessedOutput;
use Application\Payment\Port\PaymentGatewayInterface;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Exception\OrderNotFoundException;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private PaymentGatewayInterface $paymentGateway,
        private EventDispatcherInterface $events,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(ProcessPaymentInput $input): PaymentProcessedOutput
    {
        $order = $this->orders->findById($input->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($input->orderId);
        }

        // Call external service (outside transaction)
        $paymentResult = $this->paymentGateway->charge(
            new PaymentRequest(
                amount: $order->total(),
                currency: $order->total()->currency(),
                token: $input->paymentToken
            )
        );

        if (!$paymentResult->isSuccessful()) {
            return new PaymentProcessedOutput(
                orderId: $order->id()->value,
                success: false,
                errorMessage: $paymentResult->errorMessage()
            );
        }

        // Update order in transaction
        return $this->transaction->transactional(function () use ($order, $paymentResult) {
            $order->markAsPaid($paymentResult->transactionId());

            $this->orders->save($order);

            foreach ($order->releaseEvents() as $event) {
                $this->events->dispatch($event);
            }

            return new PaymentProcessedOutput(
                orderId: $order->id()->value,
                success: true,
                transactionId: $paymentResult->transactionId()
            );
        });
    }
}
```

### Checkout UseCase (orchestrating multiple operations)

```php
<?php

declare(strict_types=1);

namespace Application\Checkout\UseCase;

use Application\Checkout\DTO\CheckoutInput;
use Application\Checkout\DTO\CheckoutOutput;
use Application\Order\UseCase\CreateOrderUseCase;
use Application\Payment\UseCase\ProcessPaymentUseCase;
use Application\Order\DTO\CreateOrderInput;
use Application\Payment\DTO\ProcessPaymentInput;
use Domain\Shared\TransactionManagerInterface;

final readonly class CheckoutUseCase
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
        private ProcessPaymentUseCase $processPayment,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(CheckoutInput $input): CheckoutOutput
    {
        // Create order
        $orderResult = $this->createOrder->execute(
            new CreateOrderInput(
                customerId: $input->customerId,
                lines: $input->items
            )
        );

        // Process payment
        $paymentResult = $this->processPayment->execute(
            new ProcessPaymentInput(
                orderId: new OrderId($orderResult->orderId),
                paymentToken: $input->paymentToken
            )
        );

        if (!$paymentResult->success) {
            // Handle payment failure (could cancel order)
            return new CheckoutOutput(
                success: false,
                orderId: $orderResult->orderId,
                errorMessage: $paymentResult->errorMessage
            );
        }

        return new CheckoutOutput(
            success: true,
            orderId: $orderResult->orderId,
            transactionId: $paymentResult->transactionId
        );
    }
}
```

## Input/Output DTOs

### Input DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

use Domain\Order\ValueObject\CustomerId;

final readonly class CreateOrderInput
{
    /**
     * @param array<array{productId: string, productName: string, quantity: int, unitPriceCents: int, currency: string}> $lines
     */
    public function __construct(
        public CustomerId $customerId,
        public array $lines
    ) {}
}
```

### Output DTO

```php
<?php

declare(strict_types=1);

namespace Application\Order\DTO;

final readonly class OrderCreatedOutput
{
    public function __construct(
        public string $orderId,
        public int $total,
        public string $currency,
        public int $lineCount
    ) {}

    public function toArray(): array
    {
        return [
            'order_id' => $this->orderId,
            'total' => $this->total,
            'currency' => $this->currency,
            'line_count' => $this->lineCount,
        ];
    }
}
```

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\UseCase;

use Application\Order\UseCase\CreateOrderUseCase;
use Application\Order\DTO\CreateOrderInput;
use Application\Order\DTO\OrderCreatedOutput;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderId;
use Domain\Shared\EventDispatcherInterface;
use Domain\Shared\TransactionManagerInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    private OrderRepositoryInterface $orders;
    private EventDispatcherInterface $events;
    private TransactionManagerInterface $transaction;
    private CreateOrderUseCase $useCase;

    protected function setUp(): void
    {
        $this->orders = $this->createMock(OrderRepositoryInterface::class);
        $this->events = $this->createMock(EventDispatcherInterface::class);
        $this->transaction = $this->createMock(TransactionManagerInterface::class);

        $this->transaction->method('transactional')
            ->willReturnCallback(fn (callable $callback) => $callback());

        $this->useCase = new CreateOrderUseCase(
            $this->orders,
            $this->events,
            $this->transaction
        );
    }

    public function testCreatesOrderSuccessfully(): void
    {
        $expectedId = OrderId::generate();

        $this->orders->expects(self::once())
            ->method('nextIdentity')
            ->willReturn($expectedId);

        $this->orders->expects(self::once())
            ->method('save')
            ->with(self::isInstanceOf(Order::class));

        $this->events->expects(self::atLeastOnce())
            ->method('dispatch');

        $input = new CreateOrderInput(
            customerId: new CustomerId('customer-123'),
            lines: [
                [
                    'productId' => 'product-1',
                    'productName' => 'Test Product',
                    'quantity' => 2,
                    'unitPriceCents' => 1000,
                    'currency' => 'USD',
                ],
            ]
        );

        $result = $this->useCase->execute($input);

        self::assertInstanceOf(OrderCreatedOutput::class, $result);
        self::assertSame($expectedId->value, $result->orderId);
        self::assertSame(2000, $result->total);
        self::assertSame('USD', $result->currency);
        self::assertSame(1, $result->lineCount);
    }
}
```

## Use Case Design Principles

### 1. Orchestration, Not Decision

```php
// GOOD: Orchestration - delegates decisions to domain
public function execute(ConfirmOrderInput $input): OrderConfirmedOutput
{
    $order = $this->orders->findById($input->orderId);
    $order->confirm();  // Domain decides if confirmation is valid
    $this->orders->save($order);
    // ...
}

// BAD: Business logic in use case
public function execute(ConfirmOrderInput $input): OrderConfirmedOutput
{
    $order = $this->orders->findById($input->orderId);

    // BAD: Business logic belongs in domain
    if ($order->getStatus() === 'draft' && count($order->getLines()) > 0) {
        $order->setStatus('confirmed');
    }
}
```

### 2. Transaction Management

```php
// GOOD: Clear transaction boundary
public function execute(Input $input): Output
{
    return $this->transaction->transactional(function () use ($input) {
        // All operations here are atomic
        $order = $this->orders->findById($input->orderId);
        $order->confirm();
        $this->orders->save($order);
        return new Output(...);
    });
}
```

### 3. External Services Outside Transaction

```php
// GOOD: External call outside transaction
public function execute(Input $input): Output
{
    // External service call - can fail, can be retried
    $result = $this->externalService->call($input->data);

    // Only then start transaction
    return $this->transaction->transactional(function () use ($result) {
        // Update local state based on external result
    });
}
```

## Generation Instructions

When asked to create a Use Case:

1. **Name by operation** (verb + noun + "UseCase")
2. **Define input DTO** with required data
3. **Define output DTO** with result data
4. **Identify dependencies** (repositories, ports, event dispatcher)
5. **Implement orchestration** following standard flow
6. **Generate tests** for success and error cases

## Usage

To generate a Use Case, provide:
- Name (e.g., "CreateOrder", "ProcessPayment")
- Bounded Context (e.g., "Order", "Payment")
- Input data needed
- Output data returned
- External services involved
- Transaction requirements
