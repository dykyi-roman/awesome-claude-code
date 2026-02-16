# Mediator Pattern Examples

## Order Processing Mediator

```php
<?php

declare(strict_types=1);

namespace App\Order\Application\Mediator;

use App\Order\Application\Mediator\Colleague\InventoryColleague;
use App\Order\Application\Mediator\Colleague\PaymentColleague;
use App\Order\Application\Mediator\Colleague\ShippingColleague;
use App\Order\Application\Mediator\Colleague\NotificationColleague;

/**
 * Complete order processing mediator example.
 */
final class OrderProcessingMediator implements OrderMediator
{
    private InventoryColleague $inventory;
    private PaymentColleague $payment;
    private ShippingColleague $shipping;
    private NotificationColleague $notification;

    public function __construct(
        InventoryColleague $inventory,
        PaymentColleague $payment,
        ShippingColleague $shipping,
        NotificationColleague $notification,
    ) {
        $this->inventory = $inventory;
        $this->payment = $payment;
        $this->shipping = $shipping;
        $this->notification = $notification;

        $this->inventory->setMediator($this);
        $this->payment->setMediator($this);
        $this->shipping->setMediator($this);
        $this->notification->setMediator($this);
    }

    public function processOrder(Order $order): OrderResult
    {
        // Step 1: Check inventory
        $inventoryResult = $this->inventory->checkAndReserve($order);

        if (!$inventoryResult->isSuccess()) {
            $this->notification->sendOutOfStock($order);
            return OrderResult::failed('Insufficient inventory');
        }

        // Step 2: Process payment
        $paymentResult = $this->payment->charge($order);

        if (!$paymentResult->isSuccess()) {
            // Compensate: Release inventory
            $this->inventory->release($order);
            $this->notification->sendPaymentFailed($order);
            return OrderResult::failed('Payment failed');
        }

        // Step 3: Create shipment
        $shippingResult = $this->shipping->createShipment($order);

        if (!$shippingResult->isSuccess()) {
            // Compensate: Refund payment and release inventory
            $this->payment->refund($paymentResult->transactionId);
            $this->inventory->release($order);
            $this->notification->sendShippingFailed($order);
            return OrderResult::failed('Shipping failed');
        }

        // Step 4: Send confirmation
        $this->notification->sendOrderConfirmation($order, $shippingResult);

        return OrderResult::success($order->id, $shippingResult->trackingNumber);
    }

    public function notify(ColleagueInterface $sender, string $event, mixed $data = null): void
    {
        match ($event) {
            'inventory_low' => $this->onInventoryLow($data),
            'payment_disputed' => $this->onPaymentDisputed($data),
            'shipment_delayed' => $this->onShipmentDelayed($data),
            default => null,
        };
    }

    private function onInventoryLow(array $data): void
    {
        // Alert purchasing department
        $this->notification->alertInventoryLow($data['products']);
    }

    private function onPaymentDisputed(array $data): void
    {
        // Hold shipment and notify support
        $this->shipping->holdShipment($data['orderId']);
        $this->notification->alertPaymentDispute($data);
    }

    private function onShipmentDelayed(array $data): void
    {
        // Notify customer about delay
        $this->notification->sendShipmentDelayNotice($data);
    }
}
```

## Inventory Colleague

```php
<?php

declare(strict_types=1);

namespace App\Order\Application\Mediator\Colleague;

final class InventoryColleague extends AbstractColleague
{
    public function __construct(
        private readonly InventoryRepository $inventory,
        private readonly ReservationService $reservations,
    ) {}

    public function getName(): string
    {
        return 'inventory';
    }

    public function checkAndReserve(Order $order): InventoryResult
    {
        // Check availability
        foreach ($order->lines as $line) {
            $available = $this->inventory->getAvailable($line->productId);

            if ($available < $line->quantity->value) {
                return InventoryResult::failed(
                    "Product {$line->productId} has insufficient stock",
                );
            }
        }

        // Reserve items
        $reservation = $this->reservations->create($order);

        // Notify mediator if inventory is low
        $this->checkLowInventory($order);

        return InventoryResult::success($reservation);
    }

    public function release(Order $order): void
    {
        $this->reservations->release($order->id);
    }

    public function handle(mixed $data): mixed
    {
        return match ($data['action']) {
            'check' => $this->check($data['order']),
            'reserve' => $this->checkAndReserve($data['order']),
            'release' => $this->release($data['order']),
            default => throw new UnknownActionException($data['action']),
        };
    }

    private function checkLowInventory(Order $order): void
    {
        $lowStockProducts = [];

        foreach ($order->lines as $line) {
            $available = $this->inventory->getAvailable($line->productId);
            $threshold = $this->inventory->getLowStockThreshold($line->productId);

            if ($available <= $threshold) {
                $lowStockProducts[] = $line->productId;
            }
        }

        if (!empty($lowStockProducts)) {
            $this->notify('inventory_low', ['products' => $lowStockProducts]);
        }
    }
}
```

## Command Bus as Mediator

```php
<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Bus;

use App\Shared\Application\Command\Command;
use App\Shared\Application\Command\CommandBus;
use App\Shared\Application\Command\CommandHandler;
use App\Shared\Application\Middleware\CommandMiddleware;

/**
 * Command bus mediator with middleware support.
 */
final class CommandBusMediator implements CommandBus
{
    /** @var array<class-string<Command>, CommandHandler> */
    private array $handlers = [];

    /** @var array<CommandMiddleware> */
    private array $middleware = [];

    public function registerHandler(string $commandClass, CommandHandler $handler): void
    {
        $this->handlers[$commandClass] = $handler;
    }

    public function addMiddleware(CommandMiddleware $middleware): void
    {
        $this->middleware[] = $middleware;
    }

    public function dispatch(Command $command): mixed
    {
        $commandClass = get_class($command);

        if (!isset($this->handlers[$commandClass])) {
            throw new NoHandlerException($commandClass);
        }

        $handler = $this->handlers[$commandClass];

        // Build middleware chain
        $chain = $this->buildMiddlewareChain($handler);

        return $chain($command);
    }

    private function buildMiddlewareChain(CommandHandler $handler): callable
    {
        $chain = fn(Command $command) => $handler->handle($command);

        foreach (array_reverse($this->middleware) as $middleware) {
            $chain = fn(Command $command) => $middleware->handle($command, $chain);
        }

        return $chain;
    }
}

// Middleware example
final readonly class LoggingMiddleware implements CommandMiddleware
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function handle(Command $command, callable $next): mixed
    {
        $this->logger->info('Dispatching command', [
            'command' => get_class($command),
        ]);

        $result = $next($command);

        $this->logger->info('Command handled', [
            'command' => get_class($command),
        ]);

        return $result;
    }
}
```

## Event Mediator with Priorities

```php
<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Event;

/**
 * Event mediator supporting handler priorities.
 */
final class PriorityEventMediator implements EventMediator
{
    /** @var array<string, \SplPriorityQueue<callable>> */
    private array $handlers = [];

    public function subscribe(string $eventClass, callable $handler, int $priority = 0): void
    {
        if (!isset($this->handlers[$eventClass])) {
            $this->handlers[$eventClass] = new \SplPriorityQueue();
        }

        $this->handlers[$eventClass]->insert($handler, $priority);
    }

    public function publish(DomainEvent $event): void
    {
        $eventClass = get_class($event);
        $handlers = $this->getHandlersFor($eventClass);

        foreach ($handlers as $handler) {
            try {
                $handler($event);
            } catch (StopPropagationException) {
                break;
            }
        }
    }

    private function getHandlersFor(string $eventClass): iterable
    {
        // Get handlers for exact class
        if (isset($this->handlers[$eventClass])) {
            // Clone to preserve original queue
            $queue = clone $this->handlers[$eventClass];
            foreach ($queue as $handler) {
                yield $handler;
            }
        }

        // Get handlers for parent classes
        foreach (class_parents($eventClass) as $parent) {
            if (isset($this->handlers[$parent])) {
                $queue = clone $this->handlers[$parent];
                foreach ($queue as $handler) {
                    yield $handler;
                }
            }
        }

        // Get handlers for interfaces
        foreach (class_implements($eventClass) as $interface) {
            if (isset($this->handlers[$interface])) {
                $queue = clone $this->handlers[$interface];
                foreach ($queue as $handler) {
                    yield $handler;
                }
            }
        }
    }
}
```

## Unit Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Order\Application\Mediator;

use App\Order\Application\Mediator\OrderProcessingMediator;
use App\Order\Application\Mediator\Colleague\InventoryColleague;
use App\Order\Application\Mediator\Colleague\PaymentColleague;
use App\Order\Application\Mediator\Colleague\ShippingColleague;
use App\Order\Application\Mediator\Colleague\NotificationColleague;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderProcessingMediator::class)]
final class OrderProcessingMediatorTest extends TestCase
{
    private OrderProcessingMediator $mediator;
    private InventoryColleague $inventory;
    private PaymentColleague $payment;
    private ShippingColleague $shipping;
    private NotificationColleague $notification;

    protected function setUp(): void
    {
        $this->inventory = $this->createMock(InventoryColleague::class);
        $this->payment = $this->createMock(PaymentColleague::class);
        $this->shipping = $this->createMock(ShippingColleague::class);
        $this->notification = $this->createMock(NotificationColleague::class);

        $this->mediator = new OrderProcessingMediator(
            $this->inventory,
            $this->payment,
            $this->shipping,
            $this->notification,
        );
    }

    public function testProcessOrderSuccessfully(): void
    {
        $order = $this->createOrder();

        $this->inventory->method('checkAndReserve')
            ->willReturn(InventoryResult::success(new Reservation()));

        $this->payment->method('charge')
            ->willReturn(PaymentResult::success('txn_123'));

        $this->shipping->method('createShipment')
            ->willReturn(ShippingResult::success('TRACK123'));

        $this->notification->expects($this->once())
            ->method('sendOrderConfirmation');

        $result = $this->mediator->processOrder($order);

        $this->assertTrue($result->isSuccess());
        $this->assertSame('TRACK123', $result->trackingNumber);
    }

    public function testReleasesInventoryOnPaymentFailure(): void
    {
        $order = $this->createOrder();

        $this->inventory->method('checkAndReserve')
            ->willReturn(InventoryResult::success(new Reservation()));

        $this->payment->method('charge')
            ->willReturn(PaymentResult::failed('Card declined'));

        $this->inventory->expects($this->once())
            ->method('release')
            ->with($order);

        $this->notification->expects($this->once())
            ->method('sendPaymentFailed');

        $result = $this->mediator->processOrder($order);

        $this->assertFalse($result->isSuccess());
    }

    public function testRefundsPaymentAndReleasesInventoryOnShippingFailure(): void
    {
        $order = $this->createOrder();
        $transactionId = 'txn_123';

        $this->inventory->method('checkAndReserve')
            ->willReturn(InventoryResult::success(new Reservation()));

        $this->payment->method('charge')
            ->willReturn(PaymentResult::success($transactionId));

        $this->shipping->method('createShipment')
            ->willReturn(ShippingResult::failed('Address invalid'));

        $this->payment->expects($this->once())
            ->method('refund')
            ->with($transactionId);

        $this->inventory->expects($this->once())
            ->method('release');

        $result = $this->mediator->processOrder($order);

        $this->assertFalse($result->isSuccess());
    }

    private function createOrder(): Order
    {
        return new Order(
            id: new OrderId('order-123'),
            customerId: new CustomerId('cust-456'),
            lines: [
                new OrderLine(
                    new ProductId('prod-1'),
                    new Quantity(2),
                    Money::fromCents(1000),
                ),
            ],
        );
    }
}
```
