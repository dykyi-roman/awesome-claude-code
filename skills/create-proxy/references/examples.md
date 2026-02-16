# Proxy Pattern Examples

## Lazy Loading Repository Proxy

**File:** `src/Infrastructure/User/Proxy/LazyUserRepositoryProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\User\Proxy;

use Domain\User\Entity\User;
use Domain\User\Repository\UserRepositoryInterface;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\UserId;

final class LazyUserRepositoryProxy implements UserRepositoryInterface
{
    private ?UserRepositoryInterface $realRepository = null;

    public function __construct(
        private \Closure $factory
    ) {}

    public function findById(UserId $id): ?User
    {
        return $this->getRealRepository()->findById($id);
    }

    public function findByEmail(Email $email): ?User
    {
        return $this->getRealRepository()->findByEmail($email);
    }

    public function save(User $user): void
    {
        $this->getRealRepository()->save($user);
    }

    public function delete(UserId $id): void
    {
        $this->getRealRepository()->delete($id);
    }

    private function getRealRepository(): UserRepositoryInterface
    {
        if ($this->realRepository === null) {
            $this->realRepository = ($this->factory)();
        }

        return $this->realRepository;
    }
}
```

---

## Caching Service Proxy

**File:** `src/Infrastructure/Product/Proxy/CachingProductServiceProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Product\Proxy;

use Domain\Product\Entity\Product;
use Domain\Product\Service\ProductServiceInterface;
use Domain\Product\ValueObject\ProductId;
use Psr\Cache\CacheItemPoolInterface;

final readonly class CachingProductServiceProxy implements ProductServiceInterface
{
    private const CACHE_TTL = 3600;
    private const CACHE_PREFIX = 'product:';

    public function __construct(
        private ProductServiceInterface $realService,
        private CacheItemPoolInterface $cache
    ) {}

    public function findById(ProductId $id): ?Product
    {
        $cacheKey = self::CACHE_PREFIX . $id->toString();
        $item = $this->cache->getItem($cacheKey);

        if ($item->isHit()) {
            return $item->get();
        }

        $product = $this->realService->findById($id);

        if ($product !== null) {
            $item->set($product);
            $item->expiresAfter(self::CACHE_TTL);
            $this->cache->save($item);
        }

        return $product;
    }

    public function update(Product $product): void
    {
        $this->realService->update($product);

        $cacheKey = self::CACHE_PREFIX . $product->id()->toString();
        $this->cache->deleteItem($cacheKey);
    }

    public function search(array $criteria): array
    {
        $cacheKey = self::CACHE_PREFIX . 'search:' . md5(serialize($criteria));
        $item = $this->cache->getItem($cacheKey);

        if ($item->isHit()) {
            return $item->get();
        }

        $results = $this->realService->search($criteria);

        $item->set($results);
        $item->expiresAfter(self::CACHE_TTL);
        $this->cache->save($item);

        return $results;
    }
}
```

---

## Access Control Proxy

**File:** `src/Infrastructure/Order/Proxy/AccessControlOrderServiceProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Order\Proxy;

use Domain\Order\Entity\Order;
use Domain\Order\Service\OrderServiceInterface;
use Domain\Order\ValueObject\CreateOrderCommand;
use Domain\Order\ValueObject\OrderId;
use Domain\Security\AuthorizationServiceInterface;
use Domain\Security\Exception\AccessDeniedException;

final readonly class AccessControlOrderServiceProxy implements OrderServiceInterface
{
    public function __construct(
        private OrderServiceInterface $realService,
        private AuthorizationServiceInterface $authorizationService
    ) {}

    public function create(CreateOrderCommand $command): Order
    {
        if (!$this->authorizationService->can('order.create')) {
            throw new AccessDeniedException('Cannot create orders');
        }

        return $this->realService->create($command);
    }

    public function findById(OrderId $id): ?Order
    {
        if (!$this->authorizationService->can('order.view')) {
            throw new AccessDeniedException('Cannot view orders');
        }

        return $this->realService->findById($id);
    }

    public function cancel(OrderId $id): void
    {
        if (!$this->authorizationService->can('order.cancel')) {
            throw new AccessDeniedException('Cannot cancel orders');
        }

        $order = $this->realService->findById($id);

        if ($order !== null && !$this->authorizationService->canAccessResource($order)) {
            throw new AccessDeniedException('Cannot cancel this specific order');
        }

        $this->realService->cancel($id);
    }
}
```

---

## Logging Proxy

**File:** `src/Infrastructure/Payment/Proxy/LoggingPaymentServiceProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment\Proxy;

use Domain\Payment\PaymentServiceInterface;
use Domain\Payment\PaymentStatus;
use Domain\Payment\ValueObject\Amount;
use Domain\Payment\ValueObject\PaymentToken;
use Domain\Payment\ValueObject\TransactionId;
use Psr\Log\LoggerInterface;

final readonly class LoggingPaymentServiceProxy implements PaymentServiceInterface
{
    public function __construct(
        private PaymentServiceInterface $realService,
        private LoggerInterface $logger
    ) {}

    public function charge(Amount $amount, PaymentToken $token): TransactionId
    {
        $this->logger->info('Charging payment', [
            'amount' => $amount->toString(),
            'currency' => $amount->currency()->code(),
        ]);

        $startTime = microtime(true);

        try {
            $transactionId = $this->realService->charge($amount, $token);

            $this->logger->info('Payment charged successfully', [
                'transaction_id' => $transactionId->value(),
                'duration' => microtime(true) - $startTime,
            ]);

            return $transactionId;
        } catch (\Throwable $e) {
            $this->logger->error('Payment charge failed', [
                'amount' => $amount->toString(),
                'error' => $e->getMessage(),
                'duration' => microtime(true) - $startTime,
            ]);

            throw $e;
        }
    }

    public function refund(TransactionId $transactionId, Amount $amount): void
    {
        $this->logger->info('Refunding payment', [
            'transaction_id' => $transactionId->value(),
            'amount' => $amount->toString(),
        ]);

        try {
            $this->realService->refund($transactionId, $amount);

            $this->logger->info('Payment refunded successfully', [
                'transaction_id' => $transactionId->value(),
            ]);
        } catch (\Throwable $e) {
            $this->logger->error('Payment refund failed', [
                'transaction_id' => $transactionId->value(),
                'error' => $e->getMessage(),
            ]);

            throw $e;
        }
    }

    public function getStatus(TransactionId $transactionId): PaymentStatus
    {
        return $this->realService->getStatus($transactionId);
    }
}
```

---

## Unit Tests

### LazyUserRepositoryProxyTest

**File:** `tests/Unit/Infrastructure/User/Proxy/LazyUserRepositoryProxyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\User\Proxy;

use Domain\User\Repository\UserRepositoryInterface;
use Domain\User\ValueObject\UserId;
use Infrastructure\User\Proxy\LazyUserRepositoryProxy;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(LazyUserRepositoryProxy::class)]
final class LazyUserRepositoryProxyTest extends TestCase
{
    public function testRealRepositoryNotCreatedUntilFirstCall(): void
    {
        $factoryCalled = false;

        $factory = function () use (&$factoryCalled) {
            $factoryCalled = true;
            return $this->createMock(UserRepositoryInterface::class);
        };

        $proxy = new LazyUserRepositoryProxy($factory);

        self::assertFalse($factoryCalled, 'Factory should not be called during proxy construction');

        $proxy->findById(new UserId(1));

        self::assertTrue($factoryCalled, 'Factory should be called on first method invocation');
    }

    public function testRealRepositoryCreatedOnlyOnce(): void
    {
        $callCount = 0;

        $factory = function () use (&$callCount) {
            $callCount++;
            $mock = $this->createMock(UserRepositoryInterface::class);
            $mock->method('findById')->willReturn(null);
            return $mock;
        };

        $proxy = new LazyUserRepositoryProxy($factory);

        $proxy->findById(new UserId(1));
        $proxy->findById(new UserId(2));
        $proxy->findById(new UserId(3));

        self::assertSame(1, $callCount, 'Factory should be called exactly once');
    }
}
```

---

### CachingProductServiceProxyTest

**File:** `tests/Unit/Infrastructure/Product/Proxy/CachingProductServiceProxyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Product\Proxy;

use Domain\Product\Service\ProductServiceInterface;
use Domain\Product\ValueObject\ProductId;
use Infrastructure\Product\Proxy\CachingProductServiceProxy;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Cache\CacheItemInterface;
use Psr\Cache\CacheItemPoolInterface;

#[Group('unit')]
#[CoversClass(CachingProductServiceProxy::class)]
final class CachingProductServiceProxyTest extends TestCase
{
    public function testReturnsCachedProduct(): void
    {
        $realService = $this->createMock(ProductServiceInterface::class);
        $cache = $this->createMock(CacheItemPoolInterface::class);
        $cacheItem = $this->createMock(CacheItemInterface::class);

        $product = $this->createProduct();

        $cache->expects($this->once())
            ->method('getItem')
            ->willReturn($cacheItem);

        $cacheItem->expects($this->once())
            ->method('isHit')
            ->willReturn(true);

        $cacheItem->expects($this->once())
            ->method('get')
            ->willReturn($product);

        $realService->expects($this->never())
            ->method('findById');

        $proxy = new CachingProductServiceProxy($realService, $cache);

        $result = $proxy->findById($product->id());

        self::assertSame($product, $result);
    }

    public function testCachesMissedProduct(): void
    {
        $realService = $this->createMock(ProductServiceInterface::class);
        $cache = $this->createMock(CacheItemPoolInterface::class);
        $cacheItem = $this->createMock(CacheItemInterface::class);

        $product = $this->createProduct();

        $cacheItem->method('isHit')->willReturn(false);

        $realService->expects($this->once())
            ->method('findById')
            ->willReturn($product);

        $cache->expects($this->once())
            ->method('save')
            ->with($cacheItem);

        $proxy = new CachingProductServiceProxy($realService, $cache);

        $result = $proxy->findById($product->id());

        self::assertSame($product, $result);
    }
}
```
