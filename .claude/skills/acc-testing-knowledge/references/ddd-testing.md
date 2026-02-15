# DDD Testing Patterns

Detailed patterns for testing Domain-Driven Design components in PHP 8.4.

## Value Object Testing

### Characteristics to Test

1. **Creation** — valid construction
2. **Validation** — invalid input rejection
3. **Immutability** — no state changes
4. **Equality** — same value = equal

### Complete Example

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared;

use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Money::class)]
final class MoneyTest extends TestCase
{
    // Creation
    public function test_creates_with_valid_amount(): void
    {
        $money = Money::EUR(1000);

        self::assertSame(1000, $money->amount);
        self::assertSame('EUR', $money->currency);
    }

    // Validation
    public function test_throws_for_negative_amount(): void
    {
        $this->expectException(InvalidArgumentException::class);

        Money::EUR(-100);
    }

    #[DataProvider('invalidCurrenciesProvider')]
    public function test_throws_for_invalid_currency(string $currency): void
    {
        $this->expectException(InvalidArgumentException::class);

        new Money(100, $currency);
    }

    public static function invalidCurrenciesProvider(): array
    {
        return [
            'empty' => [''],
            'lowercase' => ['eur'],
            'too short' => ['EU'],
            'too long' => ['EURO'],
        ];
    }

    // Equality
    public function test_equals_returns_true_for_same_value(): void
    {
        $money1 = Money::EUR(1000);
        $money2 = Money::EUR(1000);

        self::assertTrue($money1->equals($money2));
    }

    public function test_equals_returns_false_for_different_amount(): void
    {
        $money1 = Money::EUR(1000);
        $money2 = Money::EUR(2000);

        self::assertFalse($money1->equals($money2));
    }

    public function test_equals_returns_false_for_different_currency(): void
    {
        $money1 = Money::EUR(1000);
        $money2 = Money::USD(1000);

        self::assertFalse($money1->equals($money2));
    }

    // Operations
    public function test_add_returns_new_instance(): void
    {
        $money1 = Money::EUR(1000);
        $money2 = Money::EUR(500);

        $result = $money1->add($money2);

        self::assertSame(1500, $result->amount);
        self::assertSame(1000, $money1->amount); // Original unchanged
    }

    public function test_add_throws_for_different_currencies(): void
    {
        $this->expectException(DomainException::class);

        Money::EUR(1000)->add(Money::USD(500));
    }
}
```

## Entity Testing

### Characteristics to Test

1. **Identity** — unique identifier
2. **State transitions** — valid/invalid transitions
3. **Business rules** — invariant enforcement
4. **Domain events** — event recording

### Complete Example

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order;

use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    private Order $order;

    protected function setUp(): void
    {
        $this->order = new Order(
            OrderId::fromString('order-123'),
            CustomerId::fromString('customer-456')
        );
    }

    // Identity
    public function test_has_unique_identity(): void
    {
        self::assertSame('order-123', $this->order->id()->toString());
    }

    public function test_identity_equals_same_id(): void
    {
        $sameId = OrderId::fromString('order-123');

        self::assertTrue($this->order->id()->equals($sameId));
    }

    // Initial state
    public function test_is_pending_when_created(): void
    {
        self::assertTrue($this->order->isPending());
        self::assertFalse($this->order->isConfirmed());
    }

    // State transitions
    public function test_confirm_changes_status(): void
    {
        $this->order->addItem(ProductMother::book(), 1);

        $this->order->confirm();

        self::assertTrue($this->order->isConfirmed());
        self::assertFalse($this->order->isPending());
    }

    public function test_confirm_throws_when_empty(): void
    {
        $this->expectException(DomainException::class);
        $this->expectExceptionMessage('Cannot confirm empty order');

        $this->order->confirm();
    }

    public function test_confirm_throws_when_already_confirmed(): void
    {
        $this->order->addItem(ProductMother::book(), 1);
        $this->order->confirm();

        $this->expectException(DomainException::class);

        $this->order->confirm();
    }

    public function test_cancel_throws_when_shipped(): void
    {
        $this->order->addItem(ProductMother::book(), 1);
        $this->order->confirm();
        $this->order->ship();

        $this->expectException(DomainException::class);

        $this->order->cancel();
    }

    // Business rules
    public function test_add_item_increases_total(): void
    {
        $this->order->addItem(ProductMother::withPrice(Money::EUR(100)), 2);

        self::assertEquals(Money::EUR(200), $this->order->total());
    }

    public function test_cannot_exceed_maximum_items(): void
    {
        for ($i = 0; $i < Order::MAX_ITEMS; $i++) {
            $this->order->addItem(ProductMother::book(), 1);
        }

        $this->expectException(DomainException::class);

        $this->order->addItem(ProductMother::book(), 1);
    }

    // Domain events
    public function test_records_order_placed_event(): void
    {
        $this->order->addItem(ProductMother::book(), 1);

        $events = $this->order->releaseEvents();

        self::assertCount(1, $events);
        self::assertInstanceOf(OrderPlacedEvent::class, $events[0]);
        self::assertTrue($events[0]->orderId->equals($this->order->id()));
    }

    public function test_records_order_confirmed_event(): void
    {
        $this->order->addItem(ProductMother::book(), 1);
        $this->order->releaseEvents(); // Clear previous events

        $this->order->confirm();

        $events = $this->order->releaseEvents();
        self::assertCount(1, $events);
        self::assertInstanceOf(OrderConfirmedEvent::class, $events[0]);
    }
}
```

## Aggregate Testing

### Characteristics to Test

1. **Root access only** — modifications through root
2. **Invariants** — consistency rules
3. **Transactions** — atomic changes
4. **Events** — aggregate-level events

### Complete Example

```php
#[Group('unit')]
#[CoversClass(ShoppingCart::class)]
final class ShoppingCartTest extends TestCase
{
    private ShoppingCart $cart;

    protected function setUp(): void
    {
        $this->cart = new ShoppingCart(
            CartId::generate(),
            CustomerId::generate()
        );
    }

    // Aggregate root access
    public function test_items_added_through_cart(): void
    {
        $product = ProductMother::book();

        $this->cart->addProduct($product, 2);

        self::assertCount(1, $this->cart->items());
        self::assertSame(2, $this->cart->items()[0]->quantity());
    }

    // Invariants
    public function test_total_quantity_cannot_exceed_limit(): void
    {
        $this->cart->addProduct(ProductMother::book(), ShoppingCart::MAX_QUANTITY);

        $this->expectException(DomainException::class);

        $this->cart->addProduct(ProductMother::pen(), 1);
    }

    public function test_total_price_cannot_exceed_limit(): void
    {
        $expensive = ProductMother::withPrice(Money::EUR(10000));

        $this->expectException(DomainException::class);

        $this->cart->addProduct($expensive, 100);
    }

    // Consistency
    public function test_adding_same_product_increases_quantity(): void
    {
        $product = ProductMother::book();

        $this->cart->addProduct($product, 1);
        $this->cart->addProduct($product, 2);

        self::assertCount(1, $this->cart->items());
        self::assertSame(3, $this->cart->items()[0]->quantity());
    }

    // Atomic operations
    public function test_checkout_creates_order(): void
    {
        $this->cart->addProduct(ProductMother::book(), 1);

        $order = $this->cart->checkout();

        self::assertTrue($this->cart->isEmpty());
        self::assertCount(1, $order->items());
    }

    public function test_checkout_fails_for_empty_cart(): void
    {
        $this->expectException(DomainException::class);

        $this->cart->checkout();
    }
}
```

## Domain Service Testing

### Characteristics to Test

1. **Business logic** — spanning multiple aggregates
2. **Dependencies** — injected via interfaces
3. **Side effects** — events, notifications

### Complete Example

```php
#[Group('unit')]
#[CoversClass(TransferMoneyService::class)]
final class TransferMoneyServiceTest extends TestCase
{
    private TransferMoneyService $service;
    private InMemoryAccountRepository $accountRepository;
    private CollectingEventDispatcher $eventDispatcher;

    protected function setUp(): void
    {
        $this->accountRepository = new InMemoryAccountRepository();
        $this->eventDispatcher = new CollectingEventDispatcher();
        $this->service = new TransferMoneyService(
            $this->accountRepository,
            $this->eventDispatcher
        );
    }

    public function test_transfers_money_between_accounts(): void
    {
        $source = AccountMother::withBalance(Money::EUR(1000));
        $target = AccountMother::withBalance(Money::EUR(500));
        $this->accountRepository->save($source);
        $this->accountRepository->save($target);

        $this->service->transfer(
            $source->id(),
            $target->id(),
            Money::EUR(300)
        );

        $updatedSource = $this->accountRepository->findById($source->id());
        $updatedTarget = $this->accountRepository->findById($target->id());
        self::assertEquals(Money::EUR(700), $updatedSource->balance());
        self::assertEquals(Money::EUR(800), $updatedTarget->balance());
    }

    public function test_throws_for_insufficient_funds(): void
    {
        $source = AccountMother::withBalance(Money::EUR(100));
        $target = AccountMother::withBalance(Money::EUR(500));
        $this->accountRepository->save($source);
        $this->accountRepository->save($target);

        $this->expectException(InsufficientFundsException::class);

        $this->service->transfer(
            $source->id(),
            $target->id(),
            Money::EUR(300)
        );
    }

    public function test_dispatches_money_transferred_event(): void
    {
        $source = AccountMother::withBalance(Money::EUR(1000));
        $target = AccountMother::withBalance(Money::EUR(500));
        $this->accountRepository->save($source);
        $this->accountRepository->save($target);

        $this->service->transfer(
            $source->id(),
            $target->id(),
            Money::EUR(300)
        );

        $events = $this->eventDispatcher->dispatchedEvents();
        self::assertCount(1, $events);
        self::assertInstanceOf(MoneyTransferredEvent::class, $events[0]);
    }
}
```

## Application Service Testing

### Characteristics to Test

1. **Orchestration** — coordinates domain objects
2. **Transaction** — unit of work
3. **DTO mapping** — input/output transformation

### Complete Example

```php
#[Group('unit')]
#[CoversClass(PlaceOrderHandler::class)]
final class PlaceOrderHandlerTest extends TestCase
{
    private PlaceOrderHandler $handler;
    private InMemoryOrderRepository $orderRepository;
    private InMemoryProductRepository $productRepository;
    private CollectingEventDispatcher $eventDispatcher;

    protected function setUp(): void
    {
        $this->orderRepository = new InMemoryOrderRepository();
        $this->productRepository = new InMemoryProductRepository();
        $this->eventDispatcher = new CollectingEventDispatcher();
        $this->handler = new PlaceOrderHandler(
            $this->orderRepository,
            $this->productRepository,
            $this->eventDispatcher
        );
    }

    public function test_creates_order_from_command(): void
    {
        $product = ProductMother::book();
        $this->productRepository->save($product);

        $command = new PlaceOrderCommand(
            customerId: 'customer-123',
            items: [
                ['productId' => $product->id()->toString(), 'quantity' => 2],
            ]
        );

        $orderId = $this->handler->handle($command);

        $order = $this->orderRepository->findById(OrderId::fromString($orderId));
        self::assertNotNull($order);
        self::assertCount(1, $order->items());
    }

    public function test_throws_when_product_not_found(): void
    {
        $command = new PlaceOrderCommand(
            customerId: 'customer-123',
            items: [
                ['productId' => 'non-existent', 'quantity' => 1],
            ]
        );

        $this->expectException(ProductNotFoundException::class);

        $this->handler->handle($command);
    }

    public function test_dispatches_domain_events(): void
    {
        $product = ProductMother::book();
        $this->productRepository->save($product);

        $command = new PlaceOrderCommand(
            customerId: 'customer-123',
            items: [
                ['productId' => $product->id()->toString(), 'quantity' => 1],
            ]
        );

        $this->handler->handle($command);

        $events = $this->eventDispatcher->dispatchedEvents();
        self::assertNotEmpty($events);
    }
}
```

## Test Doubles for DDD

### InMemory Repository

```php
final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */
    private array $orders = [];

    public function save(Order $order): void
    {
        $this->orders[$order->id()->toString()] = $order;
    }

    public function findById(OrderId $id): ?Order
    {
        return $this->orders[$id->toString()] ?? null;
    }

    public function findByCustomer(CustomerId $customerId): array
    {
        return array_values(array_filter(
            $this->orders,
            fn(Order $o) => $o->customerId()->equals($customerId)
        ));
    }

    public function delete(Order $order): void
    {
        unset($this->orders[$order->id()->toString()]);
    }
}
```

### Collecting Event Dispatcher

```php
final class CollectingEventDispatcher implements EventDispatcherInterface
{
    /** @var list<object> */
    private array $events = [];

    public function dispatch(object $event): object
    {
        $this->events[] = $event;
        return $event;
    }

    /** @return list<object> */
    public function dispatchedEvents(): array
    {
        return $this->events;
    }

    public function clear(): void
    {
        $this->events = [];
    }
}
```

### Frozen Clock

```php
final class FrozenClock implements ClockInterface
{
    public function __construct(
        private DateTimeImmutable $now
    ) {}

    public function now(): DateTimeImmutable
    {
        return $this->now;
    }

    public static function at(string $datetime): self
    {
        return new self(new DateTimeImmutable($datetime));
    }
}
```
