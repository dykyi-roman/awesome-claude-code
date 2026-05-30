# Testing in Yii3

PHPUnit integration, fixtures system, functional testing, database testing, and testing middleware and actions.

## PHPUnit Integration

### Test Structure

```
tests/
├── Unit/
│   ├── Domain/
│   │   ├── Order/
│   │   │   ├── Entity/
│   │   │   │   └── OrderTest.php
│   │   │   └── ValueObject/
│   │   │       └── OrderIdTest.php
│   │   └── Shared/
│   │       └── ValueObject/
│   │           └── MoneyTest.php
│   └── Application/
│       └── Order/
│           └── UseCase/
│               └── CreateOrderUseCaseTest.php
├── Functional/
│   ├── Api/
│   │   └── Order/
│   │       └── CreateOrderActionTest.php
│   └── Middleware/
│       └── AuthMiddlewareTest.php
└── Support/
    ├── Fixture/
    │   └── OrderFixture.php
    └── Factory/
        └── OrderFactory.php
```

### Domain Unit Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Entity;

use Entity\Order;
use ValueObject\OrderId;
use ValueObject\CustomerId;
use ValueObject\OrderStatus;
use Exception\CannotConfirmOrderException;
use ValueObject\Money;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    public function testCreateOrderSetsStatusToDraft(): void
    {
        $order = Order::create(
            id: new OrderId('order-123'),
            customerId: new CustomerId('cust-456'),
            total: Money::fromCents(5000),
        );

        self::assertSame(OrderStatus::Draft, $order->status());
    }

    public function testConfirmOrderChangesStatusToConfirmed(): void
    {
        $order = Order::create(
            id: new OrderId('order-123'),
            customerId: new CustomerId('cust-456'),
            total: Money::fromCents(5000),
        );

        $order->confirm();

        self::assertSame(OrderStatus::Confirmed, $order->status());
    }

    public function testConfirmAlreadyConfirmedOrderThrowsException(): void
    {
        $order = Order::create(
            id: new OrderId('order-123'),
            customerId: new CustomerId('cust-456'),
            total: Money::fromCents(5000),
        );
        $order->confirm();

        $this->expectException(CannotConfirmOrderException::class);

        $order->confirm();
    }

    public function testCreateOrderRecordsDomainEvent(): void
    {
        $order = Order::create(
            id: new OrderId('order-123'),
            customerId: new CustomerId('cust-456'),
            total: Money::fromCents(5000),
        );

        $events = $order->releaseEvents();

        self::assertCount(1, $events);
        self::assertInstanceOf(OrderCreated::class, $events[0]);
    }
}
```

### Application Layer Unit Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\UseCase;

use UseCase\CreateOrderUseCase;
use DTO\CreateOrderDTO;
use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;
use Psr\EventDispatcher\EventDispatcherInterface;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    public function testExecuteSavesOrderAndDispatchesEvents(): void
    {
        $repository = $this->createMock(OrderRepositoryInterface::class);
        $repository->method('nextIdentity')
            ->willReturn(new OrderId('generated-id'));
        $repository->expects(self::once())
            ->method('save');

        $events = $this->createMock(EventDispatcherInterface::class);
        $events->expects(self::atLeastOnce())
            ->method('dispatch');

        $useCase = new CreateOrderUseCase($repository, $events);

        $dto = new CreateOrderDTO(
            customerId: 'cust-123',
            lines: [['product_id' => 'prod-1', 'quantity' => 2]],
        );

        $result = $useCase->execute($dto);

        self::assertSame('generated-id', $result->orderId);
    }
}
```

## Fixtures System

### Fixture Definition

```php
<?php

declare(strict_types=1);

namespace Tests\Support\Fixture;

use Yiisoft\ActiveRecord\Tests\Stubs\ActiveRecord\Customer;
use Yiisoft\Test\Support\Container\SimpleContainer;

final class OrderFixture
{
    public static function confirmed(): array
    {
        return [
            'order-1' => [
                'id' => 'order-confirmed-1',
                'customer_id' => 'cust-1',
                'status' => 'confirmed',
                'total_cents' => 15000,
                'created_at' => '2024-01-15 10:00:00',
            ],
        ];
    }

    public static function draft(): array
    {
        return [
            'order-draft-1' => [
                'id' => 'order-draft-1',
                'customer_id' => 'cust-1',
                'status' => 'draft',
                'total_cents' => 7500,
                'created_at' => '2024-01-16 14:30:00',
            ],
        ];
    }
}
```

### Test Factory (Builder Pattern)

```php
<?php

declare(strict_types=1);

namespace Tests\Support\Factory;

use Entity\Order;
use ValueObject\OrderId;
use ValueObject\CustomerId;
use ValueObject\Money;

final class OrderFactory
{
    private string $id = 'test-order-id';
    private string $customerId = 'test-customer-id';
    private int $totalCents = 10000;

    public static function create(): self
    {
        return new self();
    }

    public function withId(string $id): self
    {
        $clone = clone $this;
        $clone->id = $id;

        return $clone;
    }

    public function withCustomerId(string $customerId): self
    {
        $clone = clone $this;
        $clone->customerId = $customerId;

        return $clone;
    }

    public function withTotal(int $cents): self
    {
        $clone = clone $this;
        $clone->totalCents = $cents;

        return $clone;
    }

    public function build(): Order
    {
        return Order::create(
            id: new OrderId($this->id),
            customerId: new CustomerId($this->customerId),
            total: Money::fromCents($this->totalCents),
        );
    }
}
```

## Functional Testing

### Action Functional Test

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Api\Order;

use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\Group;
use Psr\Http\Message\ServerRequestInterface;
use Yiisoft\Http\Method;
use Yiisoft\Http\Status;

#[Group('functional')]
final class CreateOrderActionTest extends TestCase
{
    public function testCreateOrderReturns201(): void
    {
        $request = $this->createJsonRequest(Method::POST, '/api/v1/orders', [
            'customer_id' => 'cust-123',
            'lines' => [
                ['product_id' => 'prod-1', 'quantity' => 2],
            ],
        ]);

        $response = $this->handleRequest($request);

        self::assertSame(Status::CREATED, $response->getStatusCode());

        $body = json_decode((string) $response->getBody(), true);
        self::assertArrayHasKey('id', $body);
        self::assertArrayHasKey('status', $body);
        self::assertSame('draft', $body['status']);
    }

    public function testCreateOrderWithInvalidDataReturns422(): void
    {
        $request = $this->createJsonRequest(Method::POST, '/api/v1/orders', [
            'customer_id' => '',
            'lines' => [],
        ]);

        $response = $this->handleRequest($request);

        self::assertSame(Status::UNPROCESSABLE_ENTITY, $response->getStatusCode());
    }

    private function createJsonRequest(string $method, string $uri, array $body): ServerRequestInterface
    {
        $factory = new \Nyholm\Psr7\Factory\Psr17Factory();
        $request = $factory->createServerRequest($method, $uri);

        return $request
            ->withHeader('Content-Type', 'application/json')
            ->withParsedBody($body);
    }
}
```

## Database Testing

### Integration Test with Database

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Persistence;

use ValueObject\OrderId;
use Persistence\ActiveRecord\ActiveRecordOrderRepository;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\Group;
use Yiisoft\Db\Connection\ConnectionInterface;

#[Group('integration')]
final class ActiveRecordOrderRepositoryTest extends TestCase
{
    private ConnectionInterface $db;
    private ActiveRecordOrderRepository $repository;

    protected function setUp(): void
    {
        $this->db = $this->createTestDatabase();
        $this->repository = new ActiveRecordOrderRepository(/* ... */);
        $this->loadFixtures();
    }

    protected function tearDown(): void
    {
        $this->db->createCommand('DELETE FROM {{%orders}}')->execute();
    }

    public function testFindByIdReturnsOrderWhenExists(): void
    {
        $order = $this->repository->findById(new OrderId('order-confirmed-1'));

        self::assertNotNull($order);
        self::assertSame('order-confirmed-1', $order->id()->value);
    }

    public function testFindByIdReturnsNullWhenNotExists(): void
    {
        $order = $this->repository->findById(new OrderId('nonexistent'));

        self::assertNull($order);
    }

    public function testSavePersistsNewOrder(): void
    {
        $order = OrderFactory::create()->withId('new-order-1')->build();

        $this->repository->save($order);

        $found = $this->repository->findById(new OrderId('new-order-1'));
        self::assertNotNull($found);
    }
}
```

## Testing Middleware

### Middleware Unit Test

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Middleware;

use Middleware\BearerAuthMiddleware;
use PHPUnit\Framework\TestCase;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Yiisoft\Http\Status;

#[Group('unit')]
#[CoversClass(BearerAuthMiddleware::class)]
final class BearerAuthMiddlewareTest extends TestCase
{
    public function testRequestWithValidTokenPassesThrough(): void
    {
        $tokenValidator = $this->createMock(TokenValidatorInterface::class);
        $tokenValidator->method('validate')
            ->with('valid-token')
            ->willReturn('user-123');

        $middleware = new BearerAuthMiddleware($tokenValidator, $this->responseFactory());

        $request = $this->createRequest(['Authorization' => 'Bearer valid-token']);
        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->expects(self::once())
            ->method('handle')
            ->with(self::callback(
                fn (ServerRequestInterface $r) => $r->getAttribute('userId') === 'user-123',
            ))
            ->willReturn($this->createMock(ResponseInterface::class));

        $middleware->process($request, $handler);
    }

    public function testRequestWithoutTokenReturns401(): void
    {
        $tokenValidator = $this->createMock(TokenValidatorInterface::class);
        $middleware = new BearerAuthMiddleware($tokenValidator, $this->responseFactory());

        $request = $this->createRequest([]);
        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->expects(self::never())->method('handle');

        $response = $middleware->process($request, $handler);

        self::assertSame(Status::UNAUTHORIZED, $response->getStatusCode());
    }

    public function testRequestWithInvalidTokenReturns401(): void
    {
        $tokenValidator = $this->createMock(TokenValidatorInterface::class);
        $tokenValidator->method('validate')
            ->with('invalid-token')
            ->willReturn(null);

        $middleware = new BearerAuthMiddleware($tokenValidator, $this->responseFactory());

        $request = $this->createRequest(['Authorization' => 'Bearer invalid-token']);
        $handler = $this->createMock(RequestHandlerInterface::class);

        $response = $middleware->process($request, $handler);

        self::assertSame(Status::UNAUTHORIZED, $response->getStatusCode());
    }
}
```

## Detection Patterns

```bash
# Find test files
Glob: tests/**/*Test.php

# Check test coverage attributes
Grep: "#\[CoversClass\(" --glob "tests/**/*Test.php"
Grep: "#\[Group\(" --glob "tests/**/*Test.php"

# Tests that depend on container (should be minimal)
Grep: "ContainerInterface\|->get\(" --glob "tests/Unit/**/*.php"

# Tests missing strict_types
Grep: -L "declare\(strict_types=1\)" --glob "tests/**/*.php"

# Verify domain tests have no Yii dependencies
Grep: "use Yiisoft\\\\" --glob "tests/Unit/Domain/**/*.php"
```

## Best Practices

| Practice | Description |
|----------|-------------|
| No container in unit tests | Domain/Application tests use real objects or mocks |
| Factory pattern for test data | Use test builders, not fixtures, for unit tests |
| Fixtures for integration tests | Load known data sets for database tests |
| Test middleware in isolation | Mock `RequestHandlerInterface` |
| Separate test groups | `unit`, `functional`, `integration` |
| Clean database between tests | Use transactions or truncation |
| Assert HTTP status codes | Functional tests check response status |
