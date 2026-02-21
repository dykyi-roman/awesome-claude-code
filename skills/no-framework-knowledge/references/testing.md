# Testing in No-Framework PHP

PHPUnit standalone, mocking strategies, HTTP testing with PSR-7, database testing, and CI integration.

## Detection Patterns

```bash
# Check for PHPUnit
Grep: "phpunit/phpunit" --glob "**/composer.json"

# Check for Mockery
Grep: "mockery/mockery" --glob "**/composer.json"

# Find test configuration
Glob: **/phpunit.xml
Glob: **/phpunit.xml.dist

# Check test structure
Glob: **/tests/Unit/**/*Test.php
Glob: **/tests/Integration/**/*Test.php
Glob: **/tests/Functional/**/*Test.php

# Detect tests without strict types
Grep: "^<\?php" --glob "**/tests/**/*Test.php" -A 2

# Find tests with no group attribute
Grep: "class.*Test extends" --glob "**/tests/**/*Test.php"

# Check for test coverage configuration
Grep: "coverage|cobertura|clover" --glob "**/phpunit.xml*"
```

## PHPUnit Standalone Setup

**phpunit.xml.dist:**

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:noNamespaceSchemaLocation="vendor/phpunit/phpunit/phpunit.xsd"
         bootstrap="vendor/autoload.php"
         colors="true"
         cacheDirectory="var/cache/phpunit"
         failOnRisky="true"
         failOnWarning="true"
         strict="true">

    <testsuites>
        <testsuite name="Unit">
            <directory>tests/Unit</directory>
        </testsuite>
        <testsuite name="Integration">
            <directory>tests/Integration</directory>
        </testsuite>
        <testsuite name="Functional">
            <directory>tests/Functional</directory>
        </testsuite>
    </testsuites>

    <source>
        <include>
            <directory>src</directory>
        </include>
        <exclude>
            <directory>src/Infrastructure/Persistence/Migration</directory>
        </exclude>
    </source>

    <php>
        <env name="APP_ENV" value="test"/>
        <env name="DB_NAME" value="app_test"/>
    </php>
</phpunit>
```

## Unit Testing Domain Objects

**Good — testing Value Object with real objects:**

```php
declare(strict_types=1);

namespace Tests\Unit\Domain\Order\ValueObject;

use Domain\Order\ValueObject\Money;
use Domain\Order\ValueObject\Currency;
use Domain\Order\Exception\InvalidMoneyException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Money::class)]
final class MoneyTest extends TestCase
{
    public function testAddsSameCurrency(): void
    {
        $a = new Money(1000, Currency::USD);
        $b = new Money(500, Currency::USD);

        $result = $a->add($b);

        self::assertSame(1500, $result->cents);
        self::assertTrue($result->currency->equals(Currency::USD));
    }

    public function testRejectsNegativeAmount(): void
    {
        $this->expectException(InvalidMoneyException::class);

        new Money(-1, Currency::USD);
    }

    public function testRejectsDifferentCurrencyAddition(): void
    {
        $this->expectException(InvalidMoneyException::class);

        $usd = new Money(100, Currency::USD);
        $eur = new Money(100, Currency::EUR);

        $usd->add($eur);
    }
}
```

**Good — testing Entity behavior with mocked repository:**

```php
declare(strict_types=1);

namespace Tests\Unit\Application\Order\UseCase;

use Application\Order\Command\CreateOrderCommand;
use Application\Order\UseCase\CreateOrderUseCase;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Shared\Event\EventDispatcherInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    public function testCreatesOrderAndDispatchesEvents(): void
    {
        $repository = $this->createMock(OrderRepositoryInterface::class);
        $repository->expects(self::once())
            ->method('save')
            ->with(self::isInstanceOf(Order::class));

        $events = $this->createMock(EventDispatcherInterface::class);
        $events->expects(self::atLeastOnce())
            ->method('dispatch');

        $useCase = new CreateOrderUseCase(
            orders: $repository,
            events: $events,
        );

        $command = new CreateOrderCommand(
            customerId: 'cust-123',
            lines: [['product_id' => 'prod-1', 'quantity' => 2, 'price' => 1000]],
        );

        $result = $useCase->execute($command);

        self::assertInstanceOf(OrderId::class, $result);
    }
}
```

## HTTP Testing with PSR-7 Test Doubles

**Testing PSR-15 actions without a running server:**

```php
declare(strict_types=1);

namespace Tests\Functional\Presentation\Api\Order;

use Nyholm\Psr7\ServerRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Presentation\Api\Order\CreateOrderAction;

#[Group('functional')]
#[CoversClass(CreateOrderAction::class)]
final class CreateOrderActionTest extends TestCase
{
    public function testReturns201OnValidRequest(): void
    {
        $container = require dirname(__DIR__, 4) . '/config/container-test.php';
        $action = $container->get(CreateOrderAction::class);

        $request = (new ServerRequest('POST', '/api/v1/orders'))
            ->withHeader('Content-Type', 'application/json')
            ->withParsedBody([
                'customer_id' => '550e8400-e29b-41d4-a716-446655440000',
                'lines' => [
                    ['product_id' => 'prod-1', 'quantity' => 1, 'price' => 2500],
                ],
            ]);

        $response = $action->handle($request);

        self::assertSame(201, $response->getStatusCode());

        $body = json_decode((string) $response->getBody(), true, 512, JSON_THROW_ON_ERROR);
        self::assertArrayHasKey('id', $body);
    }

    public function testReturns422OnInvalidRequest(): void
    {
        $container = require dirname(__DIR__, 4) . '/config/container-test.php';
        $action = $container->get(CreateOrderAction::class);

        $request = (new ServerRequest('POST', '/api/v1/orders'))
            ->withParsedBody([]);

        $response = $action->handle($request);

        self::assertSame(422, $response->getStatusCode());
    }
}
```

## Database Testing Without Framework Helpers

```php
declare(strict_types=1);

namespace Tests\Integration\Infrastructure\Persistence;

use Doctrine\ORM\EntityManagerInterface;
use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderId;
use Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('integration')]
#[CoversClass(DoctrineOrderRepository::class)]
final class DoctrineOrderRepositoryTest extends TestCase
{
    private EntityManagerInterface $em;
    private DoctrineOrderRepository $repository;

    protected function setUp(): void
    {
        $container = require dirname(__DIR__, 3) . '/config/container-test.php';
        $this->em = $container->get(EntityManagerInterface::class);
        $this->repository = new DoctrineOrderRepository($this->em);

        $this->em->beginTransaction();
    }

    protected function tearDown(): void
    {
        $this->em->rollback();
        $this->em->close();
    }

    public function testSavesAndFindsOrder(): void
    {
        $order = new Order(
            id: OrderId::generate(),
            customerId: new CustomerId('cust-001'),
        );

        $this->repository->save($order);
        $this->em->clear();

        $found = $this->repository->findById($order->id());

        self::assertNotNull($found);
        self::assertTrue($order->id()->equals($found->id()));
    }

    public function testReturnsNullForNonExistentOrder(): void
    {
        $found = $this->repository->findById(new OrderId('non-existent'));

        self::assertNull($found);
    }
}
```

## In-Memory Repository for Testing

```php
declare(strict_types=1);

namespace Tests\Stub;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\CustomerId;
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

    public function delete(OrderId $id): void
    {
        unset($this->orders[$id->value]);
    }

    /** @return array<Order> */
    public function findByCustomer(CustomerId $customerId): array
    {
        return array_filter(
            $this->orders,
            static fn(Order $order): bool => $order->customerId()->equals($customerId),
        );
    }
}
```

## CI Pipeline Integration

**GitHub Actions example (.github/workflows/test.yml):**

```yaml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: app_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports: ['5432:5432']
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: xdebug
      - run: composer install --no-interaction
      - run: vendor/bin/phpunit --testsuite=Unit --coverage-clover=coverage.xml
      - run: vendor/bin/phpunit --testsuite=Integration
      - run: vendor/bin/phpstan analyse
```

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| No tests at all | Critical | Quality assurance |
| Missing strict types in tests | Warning | Consistency |
| No test isolation (shared state) | Warning | Flaky tests |
| Mocking final/readonly classes | Warning | Test reliability |
| No integration tests for repositories | Warning | Persistence bugs |
| Missing CI pipeline | Info | Automation |
