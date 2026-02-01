# Decorator Pattern Examples

## Logging Decorator

**File:** `src/Infrastructure/Order/Decorator/LoggingOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\Decorator;

use Domain\Order\Decorator\AbstractOrderServiceDecorator;
use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\OrderId;
use Psr\Log\LoggerInterface;

final readonly class LoggingOrderServiceDecorator extends AbstractOrderServiceDecorator
{
    public function __construct(
        OrderServiceInterface $wrapped,
        private LoggerInterface $logger
    ) {
        parent::__construct($wrapped);
    }

    public function create(CreateOrderCommand $command): Order
    {
        $this->logger->info('Creating order', [
            'customer_id' => $command->customerId,
            'items_count' => count($command->items),
        ]);

        $order = parent::create($command);

        $this->logger->info('Order created', [
            'order_id' => $order->id()->toString(),
        ]);

        return $order;
    }

    public function cancel(OrderId $id): void
    {
        $this->logger->info('Cancelling order', [
            'order_id' => $id->toString(),
        ]);

        parent::cancel($id);

        $this->logger->info('Order cancelled', [
            'order_id' => $id->toString(),
        ]);
    }
}
```

---

## Caching Decorator

**File:** `src/Infrastructure/Order/Decorator/CachingOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\Decorator;

use Domain\Order\Decorator\AbstractOrderServiceDecorator;
use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\OrderId;
use Psr\Cache\CacheItemPoolInterface;

final readonly class CachingOrderServiceDecorator extends AbstractOrderServiceDecorator
{
    private const CACHE_TTL = 3600;
    private const CACHE_PREFIX = 'order:';

    public function __construct(
        OrderServiceInterface $wrapped,
        private CacheItemPoolInterface $cache
    ) {
        parent::__construct($wrapped);
    }

    public function findById(OrderId $id): ?Order
    {
        $cacheKey = self::CACHE_PREFIX . $id->toString();
        $item = $this->cache->getItem($cacheKey);

        if ($item->isHit()) {
            return $item->get();
        }

        $order = parent::findById($id);

        if ($order !== null) {
            $item->set($order);
            $item->expiresAfter(self::CACHE_TTL);
            $this->cache->save($item);
        }

        return $order;
    }

    public function cancel(OrderId $id): void
    {
        parent::cancel($id);

        $cacheKey = self::CACHE_PREFIX . $id->toString();
        $this->cache->deleteItem($cacheKey);
    }
}
```

---

## Metrics Decorator

**File:** `src/Infrastructure/Order/Decorator/MetricsOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\Decorator;

use Domain\Order\Decorator\AbstractOrderServiceDecorator;
use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\OrderId;
use Infrastructure\Metrics\MetricsCollectorInterface;

final readonly class MetricsOrderServiceDecorator extends AbstractOrderServiceDecorator
{
    public function __construct(
        OrderServiceInterface $wrapped,
        private MetricsCollectorInterface $metrics
    ) {
        parent::__construct($wrapped);
    }

    public function create(CreateOrderCommand $command): Order
    {
        $startTime = microtime(true);

        try {
            $order = parent::create($command);

            $this->metrics->increment('orders.created');
            $this->metrics->histogram(
                'orders.create.duration',
                microtime(true) - $startTime
            );

            return $order;
        } catch (\Throwable $e) {
            $this->metrics->increment('orders.create.failed');
            throw $e;
        }
    }

    public function cancel(OrderId $id): void
    {
        $startTime = microtime(true);

        parent::cancel($id);

        $this->metrics->increment('orders.cancelled');
        $this->metrics->histogram(
            'orders.cancel.duration',
            microtime(true) - $startTime
        );
    }
}
```

---

## Transaction Decorator

**File:** `src/Infrastructure/Order/Decorator/TransactionalOrderServiceDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\Decorator;

use Domain\Order\Decorator\AbstractOrderServiceDecorator;
use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\OrderId;
use Infrastructure\Persistence\TransactionInterface;

final readonly class TransactionalOrderServiceDecorator extends AbstractOrderServiceDecorator
{
    public function __construct(
        OrderServiceInterface $wrapped,
        private TransactionInterface $transaction
    ) {
        parent::__construct($wrapped);
    }

    public function create(CreateOrderCommand $command): Order
    {
        return $this->transaction->execute(
            fn() => parent::create($command)
        );
    }

    public function cancel(OrderId $id): void
    {
        $this->transaction->execute(
            fn() => parent::cancel($id)
        );
    }
}
```

---

## Stacking Decorators

**File:** `src/Infrastructure/Order/OrderServiceFactory.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order;

use Domain\Order\Service\OrderServiceInterface;
use Infrastructure\Order\Decorator\CachingOrderServiceDecorator;
use Infrastructure\Order\Decorator\LoggingOrderServiceDecorator;
use Infrastructure\Order\Decorator\MetricsOrderServiceDecorator;
use Infrastructure\Order\Decorator\TransactionalOrderServiceDecorator;

final readonly class OrderServiceFactory
{
    public function __construct(
        private OrderService $baseService,
        private TransactionInterface $transaction,
        private CacheItemPoolInterface $cache,
        private LoggerInterface $logger,
        private MetricsCollectorInterface $metrics
    ) {}

    public function create(): OrderServiceInterface
    {
        $service = $this->baseService;

        $service = new TransactionalOrderServiceDecorator($service, $this->transaction);
        $service = new CachingOrderServiceDecorator($service, $this->cache);
        $service = new MetricsOrderServiceDecorator($service, $this->metrics);
        $service = new LoggingOrderServiceDecorator($service, $this->logger);

        return $service;
    }
}
```

---

## Notifier Decorators

**File:** `src/Domain/Notification/Decorator/SlackNotifierDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification\Decorator;

use Domain\Notification\Message;
use Domain\Notification\NotifierInterface;

final readonly class SlackNotifierDecorator extends AbstractNotifierDecorator
{
    public function __construct(
        NotifierInterface $wrapped,
        private SlackClient $slack
    ) {
        parent::__construct($wrapped);
    }

    public function send(Message $message): void
    {
        parent::send($message);

        $this->slack->post(
            channel: '#notifications',
            text: $message->content()
        );
    }
}
```

---

## Unit Tests

### LoggingOrderServiceDecoratorTest

**File:** `tests/Unit/Infrastructure/Order/Decorator/LoggingOrderServiceDecoratorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Order\Decorator;

use Domain\Order\Service\OrderServiceInterface;
use Infrastructure\Order\Decorator\LoggingOrderServiceDecorator;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

#[Group('unit')]
#[CoversClass(LoggingOrderServiceDecorator::class)]
final class LoggingOrderServiceDecoratorTest extends TestCase
{
    public function testLogsOrderCreation(): void
    {
        $innerService = $this->createMock(OrderServiceInterface::class);
        $logger = $this->createMock(LoggerInterface::class);

        $order = $this->createOrder();
        $command = $this->createCommand();

        $innerService->expects($this->once())
            ->method('create')
            ->with($command)
            ->willReturn($order);

        $logger->expects($this->exactly(2))
            ->method('info');

        $decorator = new LoggingOrderServiceDecorator($innerService, $logger);

        $result = $decorator->create($command);

        self::assertSame($order, $result);
    }
}
```

---

### CachingOrderServiceDecoratorTest

**File:** `tests/Unit/Infrastructure/Order/Decorator/CachingOrderServiceDecoratorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Order\Decorator;

use Domain\Order\Service\OrderServiceInterface;
use Infrastructure\Order\Decorator\CachingOrderServiceDecorator;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Cache\CacheItemInterface;
use Psr\Cache\CacheItemPoolInterface;

#[Group('unit')]
#[CoversClass(CachingOrderServiceDecorator::class)]
final class CachingOrderServiceDecoratorTest extends TestCase
{
    public function testReturnsCachedOrder(): void
    {
        $innerService = $this->createMock(OrderServiceInterface::class);
        $cache = $this->createMock(CacheItemPoolInterface::class);
        $cacheItem = $this->createMock(CacheItemInterface::class);

        $order = $this->createOrder();

        $cache->expects($this->once())
            ->method('getItem')
            ->willReturn($cacheItem);

        $cacheItem->expects($this->once())
            ->method('isHit')
            ->willReturn(true);

        $cacheItem->expects($this->once())
            ->method('get')
            ->willReturn($order);

        $innerService->expects($this->never())
            ->method('findById');

        $decorator = new CachingOrderServiceDecorator($innerService, $cache);

        $result = $decorator->findById($order->id());

        self::assertSame($order, $result);
    }

    public function testCachesMissedOrder(): void
    {
        $innerService = $this->createMock(OrderServiceInterface::class);
        $cache = $this->createMock(CacheItemPoolInterface::class);
        $cacheItem = $this->createMock(CacheItemInterface::class);

        $order = $this->createOrder();

        $cacheItem->method('isHit')->willReturn(false);

        $innerService->expects($this->once())
            ->method('findById')
            ->willReturn($order);

        $cache->expects($this->once())
            ->method('save')
            ->with($cacheItem);

        $decorator = new CachingOrderServiceDecorator($innerService, $cache);

        $result = $decorator->findById($order->id());

        self::assertSame($order, $result);
    }
}
```
