# Distributed Lock Examples

## Order Processing with Lock

**File:** `src/{architecture-path}/UseCase/ProcessOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Order;

use Lock\LockException;
use Lock\LockFactory;

final readonly class ProcessOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private LockFactory $lockFactory
    ) {}

    public function execute(string $orderId): void
    {
        $acquiredLock = $this->lockFactory->createForResource(
            resource: 'order:' . $orderId
        );

        try {
            $order = $this->orders->findById($orderId);
            $order->process();
            $this->orders->save($order);
        } finally {
            $acquiredLock->release();
        }
    }
}
```

---

## Inventory Reservation with Lock

**File:** `src/{architecture-path}/UseCase/ReserveStockUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Inventory;

use Lock\LockConfig;
use Lock\LockFactory;

final readonly class ReserveStockUseCase
{
    public function __construct(
        private InventoryRepositoryInterface $inventory,
        private LockFactory $lockFactory
    ) {}

    public function execute(string $productId, int $quantity): ReservationResult
    {
        $config = new LockConfig(ttlSeconds: 10, retryCount: 5, retryDelayMs: 100);
        $lock = $this->lockFactory->create($config);

        $resource = 'inventory:' . $productId;

        if (!$lock->acquire($resource)) {
            return ReservationResult::unavailable($productId);
        }

        try {
            $stock = $this->inventory->getStock($productId);

            if ($stock->available() < $quantity) {
                return ReservationResult::insufficientStock($productId, $stock->available());
            }

            $stock->reserve($quantity);
            $this->inventory->saveStock($stock);

            return ReservationResult::reserved($productId, $quantity);
        } finally {
            $lock->release($resource);
        }
    }
}
```

---

## Singleton Cron Job

**File:** `src/{architecture-path}/Console/SingletonCommand.php`

```php
<?php

declare(strict_types=1);

namespace Console;

use Lock\LockConfig;
use Lock\LockInterface;

final class SingletonCommand
{
    public function __construct(
        private readonly LockInterface $lock
    ) {}

    public function run(string $jobName, callable $job): int
    {
        $resource = 'cron:' . $jobName;

        if (!$this->lock->acquire($resource)) {
            return 0;
        }

        try {
            return $job();
        } finally {
            $this->lock->release($resource);
        }
    }
}
```

---

## Unit Tests

### LockConfigTest

**File:** `tests/Unit/LockConfigTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Lock;

use Lock\LockConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(LockConfig::class)]
final class LockConfigTest extends TestCase
{
    public function testDefaultValues(): void
    {
        $config = new LockConfig();

        self::assertSame(30, $config->ttlSeconds);
        self::assertTrue($config->autoRelease);
        self::assertSame(3, $config->retryCount);
        self::assertSame(200, $config->retryDelayMs);
    }

    public function testCustomValues(): void
    {
        $config = new LockConfig(
            ttlSeconds: 60,
            autoRelease: false,
            retryCount: 5,
            retryDelayMs: 500
        );

        self::assertSame(60, $config->ttlSeconds);
        self::assertFalse($config->autoRelease);
        self::assertSame(5, $config->retryCount);
        self::assertSame(500, $config->retryDelayMs);
    }

    public function testRejectsZeroTtl(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new LockConfig(ttlSeconds: 0);
    }

    public function testRejectsNegativeRetryCount(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new LockConfig(retryCount: -1);
    }

    public function testRejectsNegativeRetryDelay(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new LockConfig(retryDelayMs: -1);
    }

    public function testShortLivedFactory(): void
    {
        $config = LockConfig::shortLived();

        self::assertSame(5, $config->ttlSeconds);
        self::assertSame(1, $config->retryCount);
    }

    public function testLongRunningFactory(): void
    {
        $config = LockConfig::longRunning();

        self::assertSame(300, $config->ttlSeconds);
        self::assertSame(5, $config->retryCount);
    }
}
```

---

### RedisLockAdapterTest

**File:** `tests/Unit/RedisLockAdapterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Lock;

use Lock\LockConfig;
use Lock\RedisLockAdapter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(RedisLockAdapter::class)]
final class RedisLockAdapterTest extends TestCase
{
    public function testAcquiresLockSuccessfully(): void
    {
        $redis = $this->createMock(\Redis::class);
        $redis->method('set')->willReturn(true);

        $lock = new RedisLockAdapter($redis, new LockConfig());

        self::assertTrue($lock->acquire('test-resource'));
    }

    public function testFailsToAcquireWhenLocked(): void
    {
        $redis = $this->createMock(\Redis::class);
        $redis->method('set')->willReturn(false);

        $config = new LockConfig(retryCount: 0);
        $lock = new RedisLockAdapter($redis, $config);

        self::assertFalse($lock->acquire('test-resource'));
    }

    public function testReleasesLockWithLuaScript(): void
    {
        $redis = $this->createMock(\Redis::class);
        $redis->method('set')->willReturn(true);
        $redis->expects(self::once())->method('eval');

        $lock = new RedisLockAdapter($redis, new LockConfig());
        $lock->acquire('test-resource');
        $lock->release('test-resource');
    }

    public function testIsNotAcquiredWhenNeverAcquired(): void
    {
        $redis = $this->createMock(\Redis::class);

        $lock = new RedisLockAdapter($redis, new LockConfig());

        self::assertFalse($lock->isAcquired('test-resource'));
    }

    public function testIsAcquiredWhenTokenMatches(): void
    {
        $redis = $this->createMock(\Redis::class);
        $redis->method('set')->willReturn(true);

        $lock = new RedisLockAdapter($redis, new LockConfig());
        $lock->acquire('test-resource');

        $redis->method('get')->willReturnCallback(function () use ($lock) {
            $reflection = new \ReflectionClass($lock);
            $prop = $reflection->getProperty('tokens');
            $tokens = $prop->getValue($lock);
            return $tokens['test-resource'] ?? null;
        });

        self::assertTrue($lock->isAcquired('test-resource'));
    }

    public function testRefreshReturnsFalseWhenNotHeld(): void
    {
        $redis = $this->createMock(\Redis::class);

        $lock = new RedisLockAdapter($redis, new LockConfig());

        self::assertFalse($lock->refresh('test-resource'));
    }

    public function testReleaseIsIdempotent(): void
    {
        $redis = $this->createMock(\Redis::class);

        $lock = new RedisLockAdapter($redis, new LockConfig());
        $lock->release('never-acquired');

        self::assertFalse($lock->isAcquired('never-acquired'));
    }
}
```
