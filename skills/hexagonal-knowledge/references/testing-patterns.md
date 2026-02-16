# Testing Patterns for Hexagonal Architecture

Detailed testing strategies for Hexagonal Architecture in PHP.

## Testing Pyramid

```
            ┌─────────────────┐
            │   E2E Tests     │  Few, slow, expensive
            │  (Full Stack)   │
            └────────┬────────┘
                     │
        ┌────────────▼────────────┐
        │   Integration Tests     │  Some, medium
        │   (Adapters + Ports)    │
        └────────────┬────────────┘
                     │
    ┌────────────────▼────────────────┐
    │         Unit Tests              │  Many, fast, cheap
    │  (Domain, Use Cases, Adapters)  │
    └─────────────────────────────────┘
```

## Testing Strategies by Component

### 1. Domain Layer Tests (Unit)

Test business logic in isolation.

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Entity;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\Exception\CannotConfirmEmptyOrderException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    public function testConfirmsOrderWithLines(): void
    {
        $order = $this->createOrderWithLine();

        $order->confirm();

        self::assertSame(OrderStatus::Confirmed, $order->status());
    }

    public function testCannotConfirmEmptyOrder(): void
    {
        $order = $this->createEmptyOrder();

        $this->expectException(CannotConfirmEmptyOrderException::class);

        $order->confirm();
    }

    private function createOrderWithLine(): Order
    {
        $order = new Order(
            id: OrderId::generate(),
            customerId: new CustomerId('customer-123')
        );

        $order->addLine(
            productId: new ProductId('product-1'),
            productName: 'Test Product',
            quantity: 1,
            unitPrice: new Money(1000, 'USD')
        );

        return $order;
    }
}
```

### 2. Use Case Tests (Unit with Mocked Ports)

Test application logic with mocked dependencies.

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\UseCase;

use Application\Order\UseCase\CreateOrderUseCase;
use Application\Order\DTO\CreateOrderRequest;
use Domain\Order\Entity\Order;
use Domain\Order\Port\Output\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Application\Shared\Port\Output\EventPublisherInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    private OrderRepositoryInterface $orderRepository;
    private EventPublisherInterface $eventPublisher;
    private CreateOrderUseCase $useCase;

    protected function setUp(): void
    {
        $this->orderRepository = $this->createMock(OrderRepositoryInterface::class);
        $this->eventPublisher = $this->createMock(EventPublisherInterface::class);

        $this->useCase = new CreateOrderUseCase(
            $this->orderRepository,
            $this->eventPublisher
        );
    }

    public function testCreatesOrderSuccessfully(): void
    {
        $orderId = OrderId::generate();

        $this->orderRepository
            ->expects(self::once())
            ->method('nextIdentity')
            ->willReturn($orderId);

        $this->orderRepository
            ->expects(self::once())
            ->method('save')
            ->with(self::isInstanceOf(Order::class));

        $this->eventPublisher
            ->expects(self::atLeastOnce())
            ->method('publish');

        $request = new CreateOrderRequest(
            customerId: 'customer-123',
            lines: [
                ['productId' => 'p1', 'quantity' => 2, 'price' => 1000],
            ]
        );

        $response = $this->useCase->execute($request);

        self::assertSame($orderId->value, $response->orderId);
    }
}
```

### 3. Driving Adapter Tests (Integration)

Test HTTP/CLI adapters with real use case implementations.

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure\Http\Controller;

use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Symfony\Component\HttpFoundation\Response;

final class CreateOrderControllerTest extends WebTestCase
{
    public function testCreatesOrderViaHttp(): void
    {
        $client = static::createClient();

        $client->request('POST', '/api/orders', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode([
            'customer_id' => 'customer-123',
            'lines' => [
                ['product_id' => 'product-1', 'quantity' => 2],
            ],
        ]));

        self::assertSame(Response::HTTP_CREATED, $client->getResponse()->getStatusCode());

        $responseData = json_decode($client->getResponse()->getContent(), true);
        self::assertArrayHasKey('order_id', $responseData);
    }

    public function testReturns400ForInvalidRequest(): void
    {
        $client = static::createClient();

        $client->request('POST', '/api/orders', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode([
            'customer_id' => 'customer-123',
            'lines' => [],  // Empty lines should fail
        ]));

        self::assertSame(Response::HTTP_BAD_REQUEST, $client->getResponse()->getStatusCode());
    }
}
```

### 4. Driven Adapter Tests (Integration)

Test repository implementations with real database.

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure\Persistence;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Infrastructure\Persistence\Doctrine\DoctrineOrderRepository;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;

final class DoctrineOrderRepositoryTest extends KernelTestCase
{
    private EntityManagerInterface $em;
    private DoctrineOrderRepository $repository;

    protected function setUp(): void
    {
        $kernel = self::bootKernel();
        $this->em = $kernel->getContainer()->get('doctrine.orm.entity_manager');
        $this->repository = new DoctrineOrderRepository($this->em);

        $this->em->beginTransaction();
    }

    protected function tearDown(): void
    {
        $this->em->rollback();
    }

    public function testSavesAndRetrievesOrder(): void
    {
        $order = new Order(
            id: OrderId::generate(),
            customerId: new CustomerId('customer-123')
        );

        $this->repository->save($order);

        $this->em->clear();

        $found = $this->repository->findById($order->id());

        self::assertNotNull($found);
        self::assertTrue($order->id()->equals($found->id()));
    }

    public function testReturnsNullForNonExistentOrder(): void
    {
        $found = $this->repository->findById(OrderId::generate());

        self::assertNull($found);
    }
}
```

### 5. External Service Adapter Tests

Test with mocked external services or test containers.

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure\ExternalService;

use Application\Payment\DTO\PaymentRequest;
use Infrastructure\ExternalService\Payment\StripePaymentAdapter;
use PHPUnit\Framework\TestCase;
use Stripe\StripeClient;

final class StripePaymentAdapterTest extends TestCase
{
    private StripePaymentAdapter $adapter;

    protected function setUp(): void
    {
        // Use Stripe test mode
        $this->adapter = new StripePaymentAdapter(
            new StripeClient(getenv('STRIPE_TEST_KEY'))
        );
    }

    public function testChargesSuccessfully(): void
    {
        $request = new PaymentRequest(
            orderId: 'order-123',
            amount: 1000,
            currency: 'usd',
            token: 'tok_visa'  // Stripe test token
        );

        $response = $this->adapter->charge($request);

        self::assertTrue($response->isSuccess());
        self::assertNotEmpty($response->transactionId);
    }

    public function testHandlesDeclinedCard(): void
    {
        $request = new PaymentRequest(
            orderId: 'order-123',
            amount: 1000,
            currency: 'usd',
            token: 'tok_chargeDeclined'  // Stripe test token for declined
        );

        $response = $this->adapter->charge($request);

        self::assertFalse($response->isSuccess());
        self::assertNotEmpty($response->errorMessage);
    }
}
```

## In-Memory Adapters for Testing

### In-Memory Repository

```php
<?php

declare(strict_types=1);

namespace Tests\Doubles;

use Domain\Order\Entity\Order;
use Domain\Order\Port\Output\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;

final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */
    private array $orders = [];

    public function findById(OrderId $id): ?Order
    {
        return $this->orders[$id->value] ?? null;
    }

    public function save(Order $order): void
    {
        $this->orders[$order->id()->value] = $order;
    }

    public function remove(Order $order): void
    {
        unset($this->orders[$order->id()->value]);
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }

    // Test helpers
    public function clear(): void
    {
        $this->orders = [];
    }

    public function count(): int
    {
        return count($this->orders);
    }

    public function all(): array
    {
        return array_values($this->orders);
    }
}
```

### Fake Event Publisher

```php
<?php

declare(strict_types=1);

namespace Tests\Doubles;

use Application\Shared\Port\Output\EventPublisherInterface;
use Domain\Shared\Event\DomainEvent;

final class FakeEventPublisher implements EventPublisherInterface
{
    /** @var array<DomainEvent> */
    private array $publishedEvents = [];

    public function publish(DomainEvent $event): void
    {
        $this->publishedEvents[] = $event;
    }

    public function publishAll(array $events): void
    {
        foreach ($events as $event) {
            $this->publish($event);
        }
    }

    // Test helpers
    public function publishedEvents(): array
    {
        return $this->publishedEvents;
    }

    public function lastEvent(): ?DomainEvent
    {
        return end($this->publishedEvents) ?: null;
    }

    public function hasPublished(string $eventClass): bool
    {
        foreach ($this->publishedEvents as $event) {
            if ($event instanceof $eventClass) {
                return true;
            }
        }
        return false;
    }

    public function clear(): void
    {
        $this->publishedEvents = [];
    }
}
```

## Test Organization

```
tests/
├── Unit/
│   ├── Domain/
│   │   └── Order/
│   │       ├── Entity/
│   │       │   └── OrderTest.php
│   │       └── ValueObject/
│   │           └── MoneyTest.php
│   └── Application/
│       └── Order/
│           └── UseCase/
│               └── CreateOrderUseCaseTest.php
├── Integration/
│   └── Infrastructure/
│       ├── Http/
│       │   └── Controller/
│       │       └── CreateOrderControllerTest.php
│       ├── Persistence/
│       │   └── DoctrineOrderRepositoryTest.php
│       └── ExternalService/
│           └── StripePaymentAdapterTest.php
├── E2E/
│   └── OrderWorkflowTest.php
└── Doubles/
    ├── InMemoryOrderRepository.php
    └── FakeEventPublisher.php
```

## Testing Best Practices

### 1. Test at the Right Level

| What to Test | Test Level | Dependencies |
|--------------|------------|--------------|
| Domain logic | Unit | None |
| Use case orchestration | Unit | Mocked ports |
| Adapter correctness | Integration | Real infra |
| Full workflows | E2E | Everything |

### 2. Use Test Doubles Appropriately

| Double Type | When to Use |
|-------------|-------------|
| Mock | Verify interactions |
| Stub | Provide canned answers |
| Fake | Lightweight working implementation |
| Spy | Record calls for verification |

### 3. Isolation Through Ports

```php
// Use case is testable because it depends on ports, not implementations
final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,  // Port - easy to mock
        private EventPublisherInterface $events    // Port - easy to mock
    ) {}
}
```
