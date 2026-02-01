# Use Case Pattern Examples

## CreateOrder UseCase

**File:** `src/Application/Order/UseCase/CreateOrderUseCase.php`

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

---

## ConfirmOrder UseCase

**File:** `src/Application/Order/UseCase/ConfirmOrderUseCase.php`

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

---

## ProcessPayment UseCase (with external service)

**File:** `src/Application/Payment/UseCase/ProcessPaymentUseCase.php`

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

---

## Input/Output DTOs

### CreateOrderInput

**File:** `src/Application/Order/DTO/CreateOrderInput.php`

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

### OrderCreatedOutput

**File:** `src/Application/Order/DTO/OrderCreatedOutput.php`

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

---

## Unit Tests

### CreateOrderUseCaseTest

**File:** `tests/Unit/Application/Order/UseCase/CreateOrderUseCaseTest.php`

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
