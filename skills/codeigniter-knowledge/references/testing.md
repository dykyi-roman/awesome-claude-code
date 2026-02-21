# Testing in CodeIgniter 4

PHPUnit with CIUnitTestCase, DatabaseTestTrait, feature testing, mocking services, and controller testing.

## PHPUnit with CIUnitTestCase

### Basic Test Setup

```php
<?php

declare(strict_types=1);

namespace Tests\Unit;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\ValueObject\Money;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Order\ValueObject\OrderStatus;
use CodeIgniter\Test\CIUnitTestCase;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends CIUnitTestCase
{
    public function testConfirmDraftOrder(): void
    {
        $order = new Order(
            id: new OrderId('order-001'),
            customerId: 'cust-001',
            total: new Money(5000),
            status: OrderStatus::Draft,
        );

        $order->confirm();

        $this->assertSame(OrderStatus::Confirmed, $order->status());
    }

    public function testCannotConfirmShippedOrder(): void
    {
        $order = new Order(
            id: new OrderId('order-002'),
            customerId: 'cust-001',
            total: new Money(5000),
            status: OrderStatus::Shipped,
        );

        $this->expectException(\DomainException::class);
        $order->confirm();
    }

    public function testConfirmReleasesEvent(): void
    {
        $order = new Order(
            id: new OrderId('order-003'),
            customerId: 'cust-001',
            total: new Money(1000),
        );

        $order->confirm();
        $events = $order->releaseEvents();

        $this->assertCount(1, $events);
        $this->assertInstanceOf(\App\Domain\Order\Event\OrderConfirmedEvent::class, $events[0]);
    }
}
```

### Test Configuration

```xml
<!-- phpunit.xml.dist -->
<?xml version="1.0" encoding="UTF-8"?>
<phpunit
    bootstrap="vendor/codeigniter4/framework/system/Test/bootstrap.php"
    colors="true"
    failOnRisky="true"
    failOnWarning="true"
>
    <testsuites>
        <testsuite name="unit">
            <directory>tests/Unit</directory>
        </testsuite>
        <testsuite name="feature">
            <directory>tests/Feature</directory>
        </testsuite>
    </testsuites>
    <php>
        <env name="CI_ENVIRONMENT" value="testing"/>
        <env name="database.tests.DBDriver" value="SQLite3"/>
        <env name="database.tests.database" value=":memory:"/>
    </php>
</phpunit>
```

## DatabaseTestTrait for DB Testing

### Database Test Setup

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Models\OrderModel;
use CodeIgniter\Test\CIUnitTestCase;
use CodeIgniter\Test\DatabaseTestTrait;
use PHPUnit\Framework\Attributes\Group;

#[Group('feature')]
final class OrderModelTest extends CIUnitTestCase
{
    use DatabaseTestTrait;

    protected $migrateOnce = true;
    protected $seedOnce    = false;
    protected $seed        = 'Tests\Support\Seeds\OrderTestSeeder';
    protected $DBGroup     = 'tests';

    public function testFindActiveOrders(): void
    {
        $model = new OrderModel();
        $orders = $model->where('status', 'confirmed')->findAll();

        $this->assertNotEmpty($orders);
        $this->seeInDatabase('orders', ['status' => 'confirmed']);
    }

    public function testInsertOrder(): void
    {
        $model = new OrderModel();
        $model->insert([
            'id'          => 'test-order-new',
            'customer_id' => 'cust-001',
            'status'      => 'draft',
            'total'       => 7500,
        ]);

        $this->seeInDatabase('orders', [
            'id'     => 'test-order-new',
            'status' => 'draft',
        ]);
    }

    public function testSoftDelete(): void
    {
        $model = new OrderModel();
        $model->delete('test-order-001');

        $this->dontSeeInDatabase('orders', [
            'id'         => 'test-order-001',
            'deleted_at' => null,
        ]);
    }
}
```

### Database Assertions

| Assertion | Description |
|-----------|-------------|
| `seeInDatabase($table, $criteria)` | Assert row exists matching criteria |
| `dontSeeInDatabase($table, $criteria)` | Assert no row matches criteria |
| `seeNumRecords($num, $table, $criteria)` | Assert exact count of matching rows |
| `grabFromDatabase($table, $column, $criteria)` | Get a value from matching row |

## Feature Testing with HTTP

### HTTP Testing (FeatureTestTrait)

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use CodeIgniter\Test\CIUnitTestCase;
use CodeIgniter\Test\FeatureTestTrait;
use PHPUnit\Framework\Attributes\Group;

#[Group('feature')]
final class OrderApiTest extends CIUnitTestCase
{
    use FeatureTestTrait;

    public function testListOrders(): void
    {
        $result = $this->get('api/orders');

        $result->assertStatus(200);
        $result->assertJSONFragment(['status' => 'success']);
    }

    public function testCreateOrder(): void
    {
        $result = $this->withBody(json_encode([
            'customer_id' => 'cust-001',
            'items'       => [
                ['product_id' => 1, 'quantity' => 2],
            ],
        ]))->post('api/orders');

        $result->assertStatus(201);
        $result->assertJSONFragment(['status' => 'created']);
    }

    public function testCreateOrderValidationFails(): void
    {
        $result = $this->withBody(json_encode([
            'customer_id' => '',
        ]))->post('api/orders');

        $result->assertStatus(422);
        $result->assertJSONFragment(['errors' => true]);
    }

    public function testShowNotFound(): void
    {
        $result = $this->get('api/orders/nonexistent');

        $result->assertStatus(404);
    }

    public function testAuthRequired(): void
    {
        $result = $this->get('api/admin/dashboard');

        $result->assertStatus(401);
    }

    public function testWithAuthHeaders(): void
    {
        $result = $this->withHeaders([
            'Authorization' => 'Bearer valid-token-here',
        ])->get('api/orders');

        $result->assertStatus(200);
    }
}
```

### Response Assertions

| Assertion | Description |
|-----------|-------------|
| `assertStatus($code)` | Assert HTTP status code |
| `assertOK()` | Assert 200 status |
| `assertRedirect()` | Assert 3xx redirect |
| `assertJSONFragment($data)` | Assert JSON contains fragment |
| `assertJSONExact($data)` | Assert JSON equals exactly |
| `assertHeader($name, $value)` | Assert response header |
| `assertSee($text)` | Assert body contains text |
| `assertDontSee($text)` | Assert body does not contain text |

## Mocking Services

### Using Services::injectMock

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Shared\EventDispatcherInterface;
use CodeIgniter\Test\CIUnitTestCase;
use CodeIgniter\Test\FeatureTestTrait;
use Config\Services;
use PHPUnit\Framework\Attributes\Group;

#[Group('feature')]
final class ConfirmOrderTest extends CIUnitTestCase
{
    use FeatureTestTrait;

    private OrderRepositoryInterface $mockRepo;
    private EventDispatcherInterface $mockEvents;

    protected function setUp(): void
    {
        parent::setUp();

        $this->mockRepo = $this->createMock(OrderRepositoryInterface::class);
        $this->mockEvents = $this->createMock(EventDispatcherInterface::class);

        Services::injectMock('orderRepository', $this->mockRepo);
        Services::injectMock('eventDispatcher', $this->mockEvents);
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        Services::reset();
    }

    public function testConfirmOrderDispatches(): void
    {
        $this->mockRepo
            ->expects($this->once())
            ->method('findById')
            ->willReturn($this->createDraftOrder());

        $this->mockRepo
            ->expects($this->once())
            ->method('save');

        $this->mockEvents
            ->expects($this->once())
            ->method('dispatch');

        $result = $this->put('api/orders/order-001/confirm');

        $result->assertStatus(200);
    }
}
```

### Mocking the Email Service

```php
<?php

declare(strict_types=1);

$mockEmail = $this->createMock(\CodeIgniter\Email\Email::class);
$mockEmail->method('send')->willReturn(true);

Services::injectMock('email', $mockEmail);
```

## Controller Testing

### Direct Controller Unit Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Controllers;

use App\Controllers\Api\OrderController;
use CodeIgniter\Test\CIUnitTestCase;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;

#[Group('unit')]
#[CoversClass(OrderController::class)]
final class OrderControllerTest extends CIUnitTestCase
{
    public function testShowReturnsJson(): void
    {
        $mockService = $this->createMock(\App\Application\Order\OrderService::class);
        $mockService->method('findById')->willReturn(
            new \App\Application\Order\DTO\OrderDTO(
                id: 'order-001',
                status: 'confirmed',
                total: 5000,
            )
        );

        \Config\Services::injectMock('orderService', $mockService);

        $result = $this->get('api/orders/order-001');

        $result->assertStatus(200);
        $result->assertJSONFragment(['id' => 'order-001']);
    }
}
```

## Detection Patterns

```bash
# Find all test files
Glob: tests/**/*Test.php

# Find tests using DatabaseTestTrait
Grep: "use DatabaseTestTrait" --glob "tests/**/*.php"

# Find tests using FeatureTestTrait
Grep: "use FeatureTestTrait" --glob "tests/**/*.php"

# Find service mocking
Grep: "Services::injectMock" --glob "tests/**/*.php"

# Tests missing tearDown (potential mock leaks)
Grep: "injectMock" --glob "tests/**/*.php"
# Cross-check with Services::reset() in tearDown

# Find assertions used
Grep: "assert(Status|OK|JSON|See|Header)" --glob "tests/**/*.php"

# Tests without Group attribute
Grep: "final class.*Test extends" --glob "tests/**/*.php"
# Cross-check with presence of #[Group(...)]
```

## Running Tests

```bash
# Run all tests
php vendor/bin/phpunit

# Run specific suite
php vendor/bin/phpunit --testsuite unit

# Run with coverage
php vendor/bin/phpunit --coverage-html build/coverage

# Run specific test file
php vendor/bin/phpunit tests/Unit/OrderTest.php

# Run via CI4 spark
php spark test
php spark test --group unit
```
