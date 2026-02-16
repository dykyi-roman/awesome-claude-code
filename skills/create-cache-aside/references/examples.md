# Cache-Aside Pattern Examples

## Product Catalog Cache

**File:** `src/Infrastructure/Product/ProductCachedRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Product;

use Domain\Product\Entity\Product;
use Domain\Product\Repository\ProductRepositoryInterface;
use Domain\Shared\Cache\CacheAsideInterface;
use Infrastructure\Cache\CacheInvalidator;
use Infrastructure\Cache\CacheKeyGenerator;

final readonly class ProductCachedRepository implements ProductRepositoryInterface
{
    public function __construct(
        private ProductRepositoryInterface $inner,
        private CacheAsideInterface $cache,
        private CacheKeyGenerator $keyGenerator,
        private CacheInvalidator $invalidator,
    ) {}

    public function findById(string $id): ?Product
    {
        $key = $this->keyGenerator->generate('product', $id);

        return $this->cache->get(
            key: $key,
            loader: fn() => $this->inner->findById($id),
            ttl: 1800,
        );
    }

    public function save(Product $product): void
    {
        $this->inner->save($product);

        $key = $this->keyGenerator->generate('product', $product->getId());
        $this->invalidator->invalidate($key);
        $this->invalidator->invalidateByTag('products');
    }
}
```

---

## Event-Driven Invalidation

```php
<?php

declare(strict_types=1);

namespace Application\Product\Listener;

use Domain\Product\Event\ProductUpdated;
use Infrastructure\Cache\CacheInvalidator;
use Infrastructure\Cache\CacheKeyGenerator;

final readonly class InvalidateProductCacheListener
{
    public function __construct(
        private CacheInvalidator $invalidator,
        private CacheKeyGenerator $keyGenerator,
    ) {}

    public function __invoke(ProductUpdated $event): void
    {
        $key = $this->keyGenerator->generate('product', $event->productId);
        $this->invalidator->invalidate($key);
        $this->invalidator->invalidateByTag('products');
    }
}
```

---

## DI Container Wiring

```php
<?php

declare(strict_types=1);

// config/services.php

use Infrastructure\Cache\CacheAsideExecutor;
use Infrastructure\Cache\CacheInvalidator;
use Infrastructure\Cache\CacheKeyGenerator;
use Infrastructure\Cache\RedisCacheLock;

return static function ($container): void {
    $redis = $container->get(\Redis::class);
    $cache = $container->get(\Psr\SimpleCache\CacheInterface::class);

    $lock = new RedisCacheLock($redis);

    $executor = new CacheAsideExecutor(
        cache: $cache,
        lock: $lock,
        defaultTtl: 3600,
        lockTtl: 10,
    );

    $keyGenerator = new CacheKeyGenerator(prefix: 'myapp');

    $invalidator = new CacheInvalidator(
        cache: $cache,
        redis: $redis,
    );
};
```

---

## Unit Tests

### CacheKeyGeneratorTest

**File:** `tests/Unit/Infrastructure/Cache/CacheKeyGeneratorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Cache;

use Infrastructure\Cache\CacheKeyGenerator;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CacheKeyGenerator::class)]
final class CacheKeyGeneratorTest extends TestCase
{
    private CacheKeyGenerator $generator;

    protected function setUp(): void
    {
        $this->generator = new CacheKeyGenerator(prefix: 'test');
    }

    public function testGeneratesKeyWithPrefixAndContext(): void
    {
        $key = $this->generator->generate('product', '123');

        self::assertSame('test:product:123', $key);
    }

    public function testGeneratesKeyWithMultipleParts(): void
    {
        $key = $this->generator->generate('order', 'user-1', 'status-active');

        self::assertSame('test:order:user-1:status-active', $key);
    }

    public function testHashesLongKeys(): void
    {
        $longPart = str_repeat('a', 300);
        $key = $this->generator->generate('product', $longPart);

        self::assertLessThanOrEqual(250, strlen($key));
        self::assertStringStartsWith('test:product:', $key);
    }

    public function testGenerateHashedProducesDeterministicKeys(): void
    {
        $key1 = $this->generator->generateHashed('product', '123');
        $key2 = $this->generator->generateHashed('product', '123');

        self::assertSame($key1, $key2);
    }

    public function testGenerateHashedProducesDifferentKeysForDifferentInput(): void
    {
        $key1 = $this->generator->generateHashed('product', '123');
        $key2 = $this->generator->generateHashed('product', '456');

        self::assertNotSame($key1, $key2);
    }
}
```

---

### CacheAsideExecutorTest

**File:** `tests/Unit/Infrastructure/Cache/CacheAsideExecutorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Cache;

use Infrastructure\Cache\CacheAsideExecutor;
use Infrastructure\Cache\CacheLockInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\SimpleCache\CacheInterface;

#[Group('unit')]
#[CoversClass(CacheAsideExecutor::class)]
final class CacheAsideExecutorTest extends TestCase
{
    private CacheInterface $cache;
    private CacheLockInterface $lock;

    protected function setUp(): void
    {
        $this->cache = $this->createMock(CacheInterface::class);
        $this->lock = $this->createMock(CacheLockInterface::class);
    }

    public function testReturnsCachedValueOnHit(): void
    {
        $this->cache->method('get')->willReturn('cached-value');

        $executor = new CacheAsideExecutor($this->cache, $this->lock);

        $result = $executor->get('key', fn() => 'computed');

        self::assertSame('cached-value', $result);
    }

    public function testComputesAndCachesOnMiss(): void
    {
        $this->cache->method('get')->willReturn(null);
        $this->lock->method('acquire')->willReturn(true);

        $this->cache->expects(self::once())
            ->method('set')
            ->with('key', 'computed', 3600);

        $executor = new CacheAsideExecutor($this->cache, $this->lock);

        $result = $executor->get('key', fn() => 'computed');

        self::assertSame('computed', $result);
    }

    public function testReleasesLockAfterComputation(): void
    {
        $this->cache->method('get')->willReturn(null);
        $this->lock->method('acquire')->willReturn(true);

        $this->lock->expects(self::once())
            ->method('release')
            ->with('key');

        $executor = new CacheAsideExecutor($this->cache, $this->lock);
        $executor->get('key', fn() => 'value');
    }

    public function testReleasesLockOnException(): void
    {
        $this->cache->method('get')->willReturn(null);
        $this->lock->method('acquire')->willReturn(true);

        $this->lock->expects(self::once())
            ->method('release')
            ->with('key');

        $executor = new CacheAsideExecutor($this->cache, $this->lock);

        $this->expectException(\RuntimeException::class);
        $executor->get('key', fn() => throw new \RuntimeException('fail'));
    }

    public function testInvalidateDeletesKey(): void
    {
        $this->cache->expects(self::once())
            ->method('delete')
            ->with('key');

        $executor = new CacheAsideExecutor($this->cache, $this->lock);
        $executor->invalidate('key');
    }

    public function testInvalidateByTagDeletesAllTaggedKeys(): void
    {
        $this->cache->method('get')
            ->with('tag:products')
            ->willReturn(['product:1', 'product:2']);

        $this->cache->expects(self::exactly(3))
            ->method('delete')
            ->willReturnCallback(function (string $key): bool {
                static $calls = [];
                $calls[] = $key;

                return true;
            });

        $executor = new CacheAsideExecutor($this->cache, $this->lock);
        $executor->invalidateByTag('products');
    }

    public function testUsesCustomTtl(): void
    {
        $this->cache->method('get')->willReturn(null);
        $this->lock->method('acquire')->willReturn(true);

        $this->cache->expects(self::once())
            ->method('set')
            ->with('key', 'value', 600);

        $executor = new CacheAsideExecutor($this->cache, $this->lock);
        $executor->get('key', fn() => 'value', ttl: 600);
    }
}
```

---

### CacheInvalidatorTest

**File:** `tests/Unit/Infrastructure/Cache/CacheInvalidatorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Cache;

use Infrastructure\Cache\CacheInvalidator;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\SimpleCache\CacheInterface;

#[Group('unit')]
#[CoversClass(CacheInvalidator::class)]
final class CacheInvalidatorTest extends TestCase
{
    private CacheInterface $cache;
    private \Redis $redis;

    protected function setUp(): void
    {
        $this->cache = $this->createMock(CacheInterface::class);
        $this->redis = $this->createMock(\Redis::class);
    }

    public function testInvalidateDeletesKey(): void
    {
        $this->cache->expects(self::once())
            ->method('delete')
            ->with('product:123');

        $invalidator = new CacheInvalidator($this->cache, $this->redis);
        $invalidator->invalidate('product:123');
    }

    public function testInvalidateByTagDeletesAllTaggedKeys(): void
    {
        $this->cache->method('get')
            ->with('tag:products')
            ->willReturn(['product:1', 'product:2']);

        $this->cache->expects(self::exactly(3))
            ->method('delete');

        $invalidator = new CacheInvalidator($this->cache, $this->redis);
        $invalidator->invalidateByTag('products');
    }

    public function testInvalidateByTagHandlesEmptyTag(): void
    {
        $this->cache->method('get')
            ->with('tag:empty')
            ->willReturn(null);

        $this->cache->expects(self::never())->method('delete');

        $invalidator = new CacheInvalidator($this->cache, $this->redis);
        $invalidator->invalidateByTag('empty');
    }

    public function testTagKeyAddsKeyToTagSet(): void
    {
        $this->cache->method('get')
            ->with('tag:products')
            ->willReturn(null);

        $this->cache->expects(self::once())
            ->method('set')
            ->with('tag:products', ['product:1']);

        $invalidator = new CacheInvalidator($this->cache, $this->redis);
        $invalidator->tagKey('product:1', 'products');
    }

    public function testTagKeyDeduplicates(): void
    {
        $this->cache->method('get')
            ->with('tag:products')
            ->willReturn(['product:1']);

        $this->cache->expects(self::once())
            ->method('set')
            ->with('tag:products', self::callback(fn(array $v) => count($v) === 1));

        $invalidator = new CacheInvalidator($this->cache, $this->redis);
        $invalidator->tagKey('product:1', 'products');
    }
}
```
