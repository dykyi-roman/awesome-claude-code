# Testing in Symfony

PHPUnit integration, functional tests, database testing, service mocking, and Messenger handler testing.

## Test Types Overview

| Type | Base Class | Boots Kernel | Database | Speed |
|------|-----------|-------------|----------|-------|
| Unit | `TestCase` | No | No | Fast |
| Integration | `KernelTestCase` | Yes | Optional | Medium |
| Functional | `WebTestCase` | Yes | Yes | Slow |
| End-to-End | `WebTestCase` + browser | Yes | Yes | Slowest |

## Unit Tests (Domain and Application)

Domain and Application layers should be testable without Symfony kernel.

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Order\Domain\Entity;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\Event\OrderConfirmedEvent;
use App\Order\Domain\Exception\InvalidOrderStateException;
use App\Order\Domain\ValueObject\CustomerId;
use App\Order\Domain\ValueObject\OrderId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Order::class)]
final class OrderTest extends TestCase
{
    public function testConfirmChangesStatusAndRecordsEvent(): void
    {
        $order = new Order(
            id: new OrderId('550e8400-e29b-41d4-a716-446655440000'),
            customerId: new CustomerId('customer-1'),
        );

        $order->confirm();
        $events = $order->releaseEvents();

        self::assertCount(1, $events);
        self::assertInstanceOf(OrderConfirmedEvent::class, $events[0]);
    }

    public function testConfirmOnAlreadyConfirmedThrowsException(): void
    {
        $order = new Order(
            id: new OrderId('550e8400-e29b-41d4-a716-446655440000'),
            customerId: new CustomerId('customer-1'),
        );

        $order->confirm();

        $this->expectException(InvalidOrderStateException::class);
        $order->confirm();
    }
}
```

**Detection:**
```bash
# Tests extending wrong base class
Grep: "extends KernelTestCase" --glob "**/Unit/**/*Test.php"
Grep: "extends WebTestCase" --glob "**/Unit/**/*Test.php"

# Missing test attributes
Grep: "class.*Test extends" --glob "**/*Test.php" | grep -v "CoversClass"

# Domain tests with framework imports
Grep: "use Symfony\\\\" --glob "**/Unit/**/Domain/**/*Test.php"
```

## KernelTestCase (Integration Tests)

Test services with the real container but no HTTP layer.

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Order\Application;

use App\Order\Application\Command\CreateOrderCommand;
use App\Order\Application\Handler\CreateOrderHandler;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;

#[Group('integration')]
#[CoversClass(CreateOrderHandler::class)]
final class CreateOrderHandlerTest extends KernelTestCase
{
    private CreateOrderHandler $handler;
    private OrderRepositoryInterface $repository;

    protected function setUp(): void
    {
        self::bootKernel();
        $container = static::getContainer();

        $this->handler = $container->get(CreateOrderHandler::class);
        $this->repository = $container->get(OrderRepositoryInterface::class);
    }

    public function testHandlerCreatesAndPersistsOrder(): void
    {
        $command = new CreateOrderCommand(
            customerId: 'customer-123',
            items: [['product_id' => 'prod-1', 'quantity' => 2]],
        );

        $orderId = ($this->handler)($command);

        $order = $this->repository->findById($orderId);
        self::assertNotNull($order);
        self::assertSame('customer-123', $order->customerId()->value);
    }
}
```

## WebTestCase (Functional Tests)

Full HTTP request testing with the built-in HTTP client.

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Order\Presentation;

use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Symfony\Component\HttpFoundation\Response;

#[Group('functional')]
#[CoversClass(CreateOrderAction::class)]
final class CreateOrderActionTest extends WebTestCase
{
    public function testCreateOrderReturns201(): void
    {
        $client = static::createClient();

        $client->request('POST', '/api/orders', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode([
            'customer_id' => '550e8400-e29b-41d4-a716-446655440000',
            'items' => [
                ['product_id' => 'prod-1', 'quantity' => 3],
            ],
        ], JSON_THROW_ON_ERROR));

        self::assertResponseStatusCodeSame(Response::HTTP_CREATED);

        $response = json_decode(
            $client->getResponse()->getContent(),
            true,
            512,
            JSON_THROW_ON_ERROR,
        );

        self::assertArrayHasKey('id', $response);
    }

    public function testCreateOrderWithInvalidDataReturns422(): void
    {
        $client = static::createClient();

        $client->request('POST', '/api/orders', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode([
            'customer_id' => '',
            'items' => [],
        ], JSON_THROW_ON_ERROR));

        self::assertResponseStatusCodeSame(Response::HTTP_UNPROCESSABLE_ENTITY);
    }
}
```

## Database Testing with Fixtures

### Fixture Class

```php
<?php

declare(strict_types=1);

namespace Tests\Fixtures\Order;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\ValueObject\CustomerId;
use App\Order\Domain\ValueObject\OrderId;
use Doctrine\Bundle\FixturesBundle\Fixture;
use Doctrine\Persistence\ObjectManager;

final class OrderFixture extends Fixture
{
    public const string ORDER_ID = '550e8400-e29b-41d4-a716-446655440000';

    public function load(ObjectManager $manager): void
    {
        $order = new Order(
            id: new OrderId(self::ORDER_ID),
            customerId: new CustomerId('customer-1'),
        );

        $manager->persist($order);
        $manager->flush();

        $this->addReference('order_1', $order);
    }
}
```

### Using Fixtures in Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Order;

use Doctrine\Common\DataFixtures\Purger\ORMPurger;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;
use Tests\Fixtures\Order\OrderFixture;

final class ShowOrderActionTest extends WebTestCase
{
    protected function setUp(): void
    {
        self::bootKernel();
        $em = static::getContainer()->get(EntityManagerInterface::class);

        $purger = new ORMPurger($em);
        $purger->purge();

        $fixture = new OrderFixture();
        $fixture->load($em);
    }

    public function testShowOrderReturns200(): void
    {
        $client = static::createClient();
        $client->request('GET', '/api/orders/' . OrderFixture::ORDER_ID);

        self::assertResponseIsSuccessful();
    }
}
```

## Service Mocking in Container

Override services for test isolation.

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Order;

use App\Order\Domain\Repository\OrderRepositoryInterface;
use App\Order\Domain\Entity\Order;
use App\Order\Domain\ValueObject\OrderId;
use Symfony\Bundle\FrameworkBundle\Test\WebTestCase;

final class ShowOrderWithMockTest extends WebTestCase
{
    public function testShowOrderUsesRepository(): void
    {
        $client = static::createClient();
        $container = static::getContainer();

        $mockRepo = $this->createMock(OrderRepositoryInterface::class);
        $mockRepo->method('findById')
            ->willReturn($this->createOrderStub());

        $container->set(OrderRepositoryInterface::class, $mockRepo);

        $client->request('GET', '/api/orders/550e8400-e29b-41d4-a716-446655440000');

        self::assertResponseIsSuccessful();
    }

    private function createOrderStub(): Order
    {
        return new Order(
            id: new OrderId('550e8400-e29b-41d4-a716-446655440000'),
            customerId: new CustomerId('customer-1'),
        );
    }
}
```

## Testing Messenger Handlers

### Handler Unit Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Order\Application;

use App\Order\Application\Command\ConfirmOrderCommand;
use App\Order\Application\Handler\ConfirmOrderHandler;
use App\Order\Domain\Entity\Order;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use App\Order\Domain\ValueObject\OrderId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ConfirmOrderHandler::class)]
final class ConfirmOrderHandlerTest extends TestCase
{
    public function testHandlerConfirmsOrder(): void
    {
        $orderId = new OrderId('550e8400-e29b-41d4-a716-446655440000');
        $order = $this->createMock(Order::class);
        $order->expects(self::once())->method('confirm');

        $repository = $this->createMock(OrderRepositoryInterface::class);
        $repository->method('findById')->with($orderId)->willReturn($order);
        $repository->expects(self::once())->method('save')->with($order);

        $handler = new ConfirmOrderHandler($repository);
        ($handler)(new ConfirmOrderCommand($orderId));
    }
}
```

### Testing Dispatched Messages

```php
<?php

declare(strict_types=1);

namespace Tests\Functional\Order;

use App\Order\Application\Command\CreateOrderCommand;
use App\Order\Domain\Event\OrderCreatedEvent;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;
use Symfony\Component\Messenger\MessageBusInterface;
use Symfony\Component\Messenger\Transport\InMemory\InMemoryTransport;

final class MessengerDispatchTest extends KernelTestCase
{
    public function testOrderCreatedEventIsDispatched(): void
    {
        self::bootKernel();
        $container = static::getContainer();

        $bus = $container->get(MessageBusInterface::class);
        $bus->dispatch(new CreateOrderCommand(
            customerId: 'customer-1',
            items: [['product_id' => 'prod-1', 'quantity' => 1]],
        ));

        /** @var InMemoryTransport $transport */
        $transport = $container->get('messenger.transport.async');

        self::assertCount(1, $transport->getSent());
        self::assertInstanceOf(
            OrderCreatedEvent::class,
            $transport->getSent()[0]->getMessage(),
        );
    }
}
```

### Messenger Test Configuration

```yaml
# config/packages/test/messenger.yaml
framework:
    messenger:
        transports:
            async: 'in-memory://'
```

## Test Organization

| Directory | Content | Base Class |
|-----------|---------|-----------|
| `tests/Unit/` | Domain + Application tests | `TestCase` |
| `tests/Integration/` | Service + repository tests | `KernelTestCase` |
| `tests/Functional/` | HTTP endpoint tests | `WebTestCase` |
| `tests/Fixtures/` | Shared fixture classes | `Fixture` |
