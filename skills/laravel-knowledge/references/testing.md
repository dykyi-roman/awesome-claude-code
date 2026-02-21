# Testing in Laravel

Detailed patterns for Feature tests, Unit tests, Pest PHP, factories, database testing, and mocking.

## Feature Tests vs Unit Tests

### Classification

| Aspect | Unit Test | Feature Test |
|--------|-----------|--------------|
| Scope | Single class/method | Full HTTP request cycle |
| Speed | Very fast | Slower (boots app) |
| Dependencies | Mocked | Real (database, queue) |
| Location | `tests/Unit/` | `tests/Feature/` |
| Use for | Domain, Application layer | Controllers, API endpoints |

### Feature Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Feature\Order;

use App\Infrastructure\Persistence\Eloquent\Model\CustomerModel;
use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class CreateOrderTest extends TestCase
{
    use RefreshDatabase;

    public function test_creates_order_successfully(): void
    {
        $customer = CustomerModel::factory()->create();

        $response = $this->postJson('/api/orders', [
            'customer_id' => $customer->id,
            'lines' => [
                ['product_id' => 'a1b2c3d4-e5f6-7890-abcd-ef1234567890', 'quantity' => 2],
            ],
        ]);

        $response->assertCreated()
            ->assertJsonStructure([
                'data' => ['id', 'status', 'customer', 'total', 'created_at'],
            ]);

        $this->assertDatabaseHas('orders', [
            'customer_id' => $customer->id,
            'status' => 'draft',
        ]);
    }

    public function test_returns_422_for_empty_lines(): void
    {
        $customer = CustomerModel::factory()->create();

        $response = $this->postJson('/api/orders', [
            'customer_id' => $customer->id,
            'lines' => [],
        ]);

        $response->assertUnprocessable()
            ->assertJsonValidationErrors(['lines']);
    }
}
```

### Unit Test for Domain Entity

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\Exception\InvalidOrderStateException;
use App\Domain\Order\ValueObject\CustomerId;
use App\Domain\Order\ValueObject\OrderId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    public function test_new_order_has_draft_status(): void
    {
        $order = new Order(
            id: OrderId::generate(),
            customerId: new CustomerId('cust-123'),
        );

        self::assertTrue($order->status()->isDraft());
    }

    public function test_cannot_confirm_non_draft_order(): void
    {
        $order = $this->createConfirmedOrder();

        $this->expectException(InvalidOrderStateException::class);
        $order->confirm();
    }

    private function createConfirmedOrder(): Order
    {
        $order = new Order(
            id: OrderId::generate(),
            customerId: new CustomerId('cust-123'),
        );
        $order->addLine(/* ... */);
        $order->confirm();

        return $order;
    }
}
```

## Pest PHP Testing Framework

### Pest Feature Test

```php
<?php

declare(strict_types=1);

use App\Infrastructure\Persistence\Eloquent\Model\CustomerModel;
use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;

uses(\Illuminate\Foundation\Testing\RefreshDatabase::class);

describe('Order API', function () {
    test('creates order successfully', function () {
        $customer = CustomerModel::factory()->create();

        $response = $this->postJson('/api/orders', [
            'customer_id' => $customer->id,
            'lines' => [
                ['product_id' => fake()->uuid(), 'quantity' => 2],
            ],
        ]);

        $response->assertCreated();
        expect($response->json('data.status'))->toBe('draft');
    });

    test('rejects order without lines', function () {
        $customer = CustomerModel::factory()->create();

        $this->postJson('/api/orders', [
            'customer_id' => $customer->id,
            'lines' => [],
        ])->assertUnprocessable();
    });
});
```

### Pest Architecture Test

```php
<?php

declare(strict_types=1);

arch('Domain has no Laravel dependencies')
    ->expect('App\\Domain')
    ->not->toUse('Illuminate');

arch('Controllers are invokable')
    ->expect('App\\Http\\Controllers')
    ->toBeInvokable();

arch('Use cases are final and readonly')
    ->expect('App\\Application')
    ->classes()
    ->toBeFinal()
    ->toBeReadonly();
```

## Model Factories and Seeders

### Factory

```php
<?php

declare(strict_types=1);

namespace Database\Factories;

use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;
use Illuminate\Database\Eloquent\Factories\Factory;

/** @extends Factory<OrderModel> */
final class OrderModelFactory extends Factory
{
    protected $model = OrderModel::class;

    /** @return array<string, mixed> */
    public function definition(): array
    {
        return [
            'id' => $this->faker->uuid(),
            'customer_id' => CustomerModel::factory(),
            'status' => 'draft',
            'total_cents' => $this->faker->numberBetween(1000, 100000),
            'currency' => 'USD',
        ];
    }

    public function confirmed(): static
    {
        return $this->state(['status' => 'confirmed']);
    }

    public function cancelled(): static
    {
        return $this->state(['status' => 'cancelled']);
    }
}
```

### Detection Patterns

```bash
# Find factories
Glob: database/factories/**/*Factory.php
Grep: "extends Factory" --glob "**/*.php"

# Find seeders
Glob: database/seeders/**/*Seeder.php
```

## Database Testing

### RefreshDatabase vs DatabaseTransactions

| Trait | Behavior | Use When |
|-------|----------|----------|
| `RefreshDatabase` | Migrates + wraps in transaction | Need clean schema |
| `DatabaseTransactions` | Wraps each test in transaction, rollbacks | Schema already migrated |
| `LazilyRefreshDatabase` | Migrates only when DB accessed | Mixed test suites |

### Testing with Database

```php
<?php

declare(strict_types=1);

namespace Tests\Feature\Order;

use App\Infrastructure\Persistence\Eloquent\Model\OrderModel;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

final class OrderListTest extends TestCase
{
    use RefreshDatabase;

    public function test_lists_only_customer_orders(): void
    {
        $customer = CustomerModel::factory()->create();
        OrderModel::factory()->count(3)->create(['customer_id' => $customer->id]);
        OrderModel::factory()->count(2)->create(); // Other customer

        $response = $this->actingAs($customer)
            ->getJson('/api/orders');

        $response->assertOk();
        expect($response->json('data'))->toHaveCount(3);
    }
}
```

## Mocking with Mockery

### Mocking in Service Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order;

use App\Application\Order\UseCase\CreateOrderUseCase;
use App\Application\Order\Command\CreateOrderCommand;
use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Order\ValueObject\CustomerId;
use App\Domain\Order\ValueObject\OrderId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    public function test_creates_and_saves_order(): void
    {
        $repository = \Mockery::mock(OrderRepositoryInterface::class);
        $repository->shouldReceive('nextIdentity')
            ->once()
            ->andReturn(new OrderId('order-123'));
        $repository->shouldReceive('save')
            ->once();

        $useCase = new CreateOrderUseCase($repository);

        $result = $useCase->execute(new CreateOrderCommand(
            customerId: new CustomerId('cust-456'),
            lines: [['product_id' => 'prod-789', 'quantity' => 1]],
        ));

        self::assertEquals('order-123', $result->value());
    }

    protected function tearDown(): void
    {
        \Mockery::close();
        parent::tearDown();
    }
}
```

### Faking Laravel Services

```php
public function test_dispatches_event_on_order_creation(): void
{
    Event::fake([OrderCreatedEvent::class]);

    $this->postJson('/api/orders', $this->validPayload());

    Event::assertDispatched(OrderCreatedEvent::class, function ($event) {
        return $event->orderId !== null;
    });
}
```

## Testing Jobs, Events, Notifications

### Job Testing

```php
public function test_dispatches_order_processing_job(): void
{
    Queue::fake();

    $this->postJson('/api/orders/order-123/confirm');

    Queue::assertPushed(ProcessOrderJob::class, function ($job) {
        return $job->orderId === 'order-123';
    });
}
```

### Notification Testing

```php
public function test_sends_order_confirmation_notification(): void
{
    Notification::fake();

    $customer = CustomerModel::factory()->create();
    $order = OrderModel::factory()->create(['customer_id' => $customer->id]);

    $this->postJson("/api/orders/{$order->id}/confirm");

    Notification::assertSentTo(
        $customer,
        OrderConfirmedNotification::class,
    );
}
```

### Detection Patterns

```bash
# Find test files
Glob: tests/**/*Test.php

# Find tests without attributes (missing coverage tracking)
Grep: "final class.*Test extends" --glob "tests/**/*.php" -B 3

# Feature tests without database trait
Grep: "class.*Test extends TestCase" --glob "tests/Feature/**/*.php"
```
