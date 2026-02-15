# Integration Testing Patterns

Detailed patterns and examples for integration testing in PHP 8.4.

## Test Class Structure

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure;

use PHPUnit\Framework\Attributes\Group;
use Tests\IntegrationTestCase;

#[Group('integration')]
final class DoctrineOrderRepositoryTest extends IntegrationTestCase
{
    private OrderRepositoryInterface $repository;

    protected function setUp(): void
    {
        parent::setUp();
        $this->repository = $this->getContainer()->get(OrderRepositoryInterface::class);
        $this->beginTransaction();
    }

    protected function tearDown(): void
    {
        $this->rollbackTransaction();
        parent::tearDown();
    }
}
```

## Database Testing

### Transaction Rollback Pattern

```php
abstract class DatabaseTestCase extends TestCase
{
    protected Connection $connection;

    protected function setUp(): void
    {
        parent::setUp();
        $this->connection = $this->getContainer()->get(Connection::class);
        $this->connection->beginTransaction();
    }

    protected function tearDown(): void
    {
        $this->connection->rollBack();
        parent::tearDown();
    }
}
```

### SQLite In-Memory

```php
// phpunit.xml
<php>
    <env name="DATABASE_URL" value="sqlite:///:memory:" />
</php>

// Test setup
protected function setUp(): void
{
    parent::setUp();
    $this->runMigrations();
}

private function runMigrations(): void
{
    $this->getContainer()
        ->get(MigrationRunner::class)
        ->migrate();
}
```

### Testcontainers (Real Database)

```php
use Testcontainers\Container\PostgreSqlContainer;

final class PostgresRepositoryTest extends TestCase
{
    private static PostgreSqlContainer $postgres;

    public static function setUpBeforeClass(): void
    {
        self::$postgres = PostgreSqlContainer::make('15.0')
            ->withDatabase('test_db')
            ->start();
    }

    public static function tearDownAfterClass(): void
    {
        self::$postgres->stop();
    }

    protected function setUp(): void
    {
        $this->connection = DriverManager::getConnection([
            'url' => self::$postgres->getDsn(),
        ]);
    }
}
```

## Repository Testing

### CRUD Operations

```php
public function test_saves_order(): void
{
    $order = OrderMother::pending();

    $this->repository->save($order);

    $found = $this->repository->findById($order->id());
    self::assertNotNull($found);
}

public function test_updates_existing_order(): void
{
    $order = OrderMother::pending();
    $this->repository->save($order);

    $order->confirm();
    $this->repository->save($order);

    $found = $this->repository->findById($order->id());
    self::assertTrue($found->isConfirmed());
}

public function test_deletes_order(): void
{
    $order = OrderMother::pending();
    $this->repository->save($order);

    $this->repository->delete($order);

    $found = $this->repository->findById($order->id());
    self::assertNull($found);
}

public function test_returns_null_for_nonexistent_order(): void
{
    $result = $this->repository->findById(OrderId::generate());

    self::assertNull($result);
}
```

### Query Methods

```php
public function test_finds_orders_by_customer(): void
{
    $customerId = CustomerId::generate();
    $order1 = OrderMother::forCustomer($customerId);
    $order2 = OrderMother::forCustomer($customerId);
    $order3 = OrderMother::forCustomer(CustomerId::generate());

    $this->repository->save($order1);
    $this->repository->save($order2);
    $this->repository->save($order3);

    $orders = $this->repository->findByCustomer($customerId);

    self::assertCount(2, $orders);
}

public function test_finds_pending_orders(): void
{
    $pending = OrderMother::pending();
    $confirmed = OrderMother::confirmed();

    $this->repository->save($pending);
    $this->repository->save($confirmed);

    $orders = $this->repository->findPending();

    self::assertCount(1, $orders);
    self::assertTrue($orders[0]->id()->equals($pending->id()));
}
```

## HTTP Client Testing

### VCR Pattern (Recorded Responses)

```php
use VCR\VCR;

#[Group('integration')]
final class StripePaymentGatewayTest extends TestCase
{
    protected function setUp(): void
    {
        VCR::turnOn();
        VCR::insertCassette('stripe_payments.yml');
    }

    protected function tearDown(): void
    {
        VCR::eject();
        VCR::turnOff();
    }

    public function test_charges_card(): void
    {
        $gateway = new StripePaymentGateway($this->apiKey);

        $result = $gateway->charge(
            Money::USD(1000),
            new CardToken('tok_visa')
        );

        self::assertTrue($result->isSuccessful());
    }
}
```

### Mock HTTP Client

```php
use Symfony\Component\HttpClient\MockHttpClient;
use Symfony\Component\HttpClient\Response\MockResponse;

public function test_fetches_exchange_rate(): void
{
    $mockResponse = new MockResponse(json_encode([
        'rates' => ['EUR' => 0.85],
    ]));
    $httpClient = new MockHttpClient($mockResponse);

    $service = new ExchangeRateService($httpClient);

    $rate = $service->getRate('USD', 'EUR');

    self::assertEquals(0.85, $rate);
}
```

## Message Queue Testing

### In-Memory Transport

```php
// config/packages/test/messenger.yaml
framework:
    messenger:
        transports:
            async: 'in-memory://'

// Test
public function test_dispatches_order_confirmation_message(): void
{
    $order = OrderMother::pending();

    $this->commandBus->dispatch(new ConfirmOrderCommand($order->id()));

    $messages = $this->getMessengerTransport('async')->get();
    self::assertCount(1, $messages);
    self::assertInstanceOf(
        SendOrderConfirmationEmail::class,
        $messages[0]->getMessage()
    );
}
```

### Handler Testing

```php
public function test_handles_order_created_event(): void
{
    $event = new OrderCreatedEvent(
        OrderId::generate(),
        CustomerId::generate(),
        new DateTimeImmutable()
    );

    $this->handler->__invoke($event);

    // Assert side effects (email sent, notification created, etc.)
    $notifications = $this->notificationRepository->findByCustomer(
        $event->customerId
    );
    self::assertCount(1, $notifications);
}
```

## Cache Testing

### Redis Testing

```php
use Predis\Client;

final class RedisCacheTest extends IntegrationTestCase
{
    private Client $redis;
    private RedisCache $cache;

    protected function setUp(): void
    {
        $this->redis = new Client(['host' => 'localhost']);
        $this->redis->flushdb();
        $this->cache = new RedisCache($this->redis);
    }

    public function test_stores_and_retrieves_value(): void
    {
        $this->cache->set('key', 'value', 60);

        self::assertSame('value', $this->cache->get('key'));
    }

    public function test_expires_after_ttl(): void
    {
        $this->cache->set('key', 'value', 1);

        sleep(2);

        self::assertNull($this->cache->get('key'));
    }
}
```

## Test Fixtures

### JSON Fixtures

```php
final class FixtureLoader
{
    public static function load(string $name): array
    {
        $path = __DIR__ . '/fixtures/' . $name . '.json';
        return json_decode(file_get_contents($path), true);
    }
}

// Usage
public function test_imports_products(): void
{
    $data = FixtureLoader::load('products');

    $this->importer->import($data);

    self::assertCount(10, $this->productRepository->findAll());
}
```

### Database Fixtures

```php
final class OrderFixture
{
    public static function load(
        Connection $connection,
        int $count = 10
    ): void {
        for ($i = 0; $i < $count; $i++) {
            $connection->insert('orders', [
                'id' => Uuid::uuid4()->toString(),
                'customer_id' => Uuid::uuid4()->toString(),
                'status' => 'pending',
                'created_at' => (new DateTimeImmutable())->format('Y-m-d H:i:s'),
            ]);
        }
    }
}
```

## Performance Considerations

1. **Minimize DB operations** — use transactions, rollback instead of truncate
2. **Use SQLite for speed** — when DB-specific features not needed
3. **Parallel execution** — separate databases per process
4. **Group slow tests** — run separately: `phpunit --group=integration`
5. **Fixture caching** — load once per test class, not per test
