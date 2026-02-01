# Bulkhead Pattern Examples

## External Service Isolation

**File:** `src/Infrastructure/Payment/PaymentGatewayAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment;

use Infrastructure\Resilience\Bulkhead\BulkheadRegistry;
use Infrastructure\Resilience\Bulkhead\BulkheadConfig;
use Infrastructure\Resilience\Bulkhead\BulkheadFullException;

final readonly class PaymentGatewayAdapter
{
    public function __construct(
        private PaymentApiClient $client,
        private BulkheadRegistry $bulkheads
    ) {
        $this->bulkheads->register(
            'payment-gateway',
            BulkheadConfig::forExternalService(maxConnections: 20)
        );
    }

    public function charge(PaymentRequest $request): PaymentResult
    {
        $bulkhead = $this->bulkheads->get('payment-gateway');

        try {
            return $bulkhead->execute(
                fn() => $this->client->charge($request)
            );
        } catch (BulkheadFullException $e) {
            return PaymentResult::serviceOverloaded($request->id);
        }
    }
}
```

---

## Database Connection Pool

**File:** `src/Infrastructure/Persistence/ConnectionPool.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Infrastructure\Resilience\Bulkhead\SemaphoreBulkhead;
use Infrastructure\Resilience\Bulkhead\BulkheadConfig;

final class ConnectionPool
{
    private SemaphoreBulkhead $bulkhead;

    public function __construct(
        private readonly ConnectionFactory $factory,
        int $maxConnections,
        LoggerInterface $logger
    ) {
        $this->bulkhead = new SemaphoreBulkhead(
            name: 'db-pool',
            config: new BulkheadConfig(maxConcurrentCalls: $maxConnections),
            logger: $logger
        );
    }

    /**
     * @template T
     * @param callable(Connection): T $operation
     * @return T
     */
    public function execute(callable $operation): mixed
    {
        return $this->bulkhead->execute(function () use ($operation) {
            $connection = $this->factory->create();
            try {
                return $operation($connection);
            } finally {
                $connection->close();
            }
        });
    }

    public function getAvailableConnections(): int
    {
        return $this->bulkhead->getAvailablePermits();
    }
}
```

---

## Multiple Isolated Services

**File:** `src/Application/Service/OrderService.php`

```php
<?php

declare(strict_types=1);

namespace Application\Service;

use Infrastructure\Resilience\Bulkhead\BulkheadRegistry;
use Infrastructure\Resilience\Bulkhead\BulkheadConfig;

final readonly class OrderService
{
    public function __construct(
        private InventoryClient $inventory,
        private PaymentClient $payment,
        private ShippingClient $shipping,
        private BulkheadRegistry $bulkheads
    ) {
        $this->bulkheads
            ->register('inventory', new BulkheadConfig(maxConcurrentCalls: 50))
            ->register('payment', new BulkheadConfig(maxConcurrentCalls: 20))
            ->register('shipping', new BulkheadConfig(maxConcurrentCalls: 30));
    }

    public function placeOrder(OrderRequest $request): OrderResult
    {
        $inventoryResult = $this->bulkheads->get('inventory')->execute(
            fn() => $this->inventory->reserve($request->items)
        );

        $paymentResult = $this->bulkheads->get('payment')->execute(
            fn() => $this->payment->charge($request->payment)
        );

        $shippingResult = $this->bulkheads->get('shipping')->execute(
            fn() => $this->shipping->schedule($request->shipping)
        );

        return new OrderResult($inventoryResult, $paymentResult, $shippingResult);
    }
}
```

---

## Unit Tests

### SemaphoreBulkheadTest

**File:** `tests/Unit/Infrastructure/Resilience/Bulkhead/SemaphoreBulkheadTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\Bulkhead;

use Infrastructure\Resilience\Bulkhead\BulkheadConfig;
use Infrastructure\Resilience\Bulkhead\BulkheadFullException;
use Infrastructure\Resilience\Bulkhead\SemaphoreBulkhead;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(SemaphoreBulkhead::class)]
final class SemaphoreBulkheadTest extends TestCase
{
    public function testExecutesOperationWithinCapacity(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 5);

        $result = $bulkhead->execute(fn() => 'success');

        self::assertSame('success', $result);
    }

    public function testReleasesPermitAfterExecution(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 1);

        $bulkhead->execute(fn() => 'first');
        self::assertSame(1, $bulkhead->getAvailablePermits());

        $bulkhead->execute(fn() => 'second');
        self::assertSame(1, $bulkhead->getAvailablePermits());
    }

    public function testReleasesPermitOnException(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 1);

        try {
            $bulkhead->execute(fn() => throw new \RuntimeException('fail'));
        } catch (\RuntimeException) {}

        self::assertSame(1, $bulkhead->getAvailablePermits());
    }

    public function testThrowsWhenFull(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 1);

        $bulkhead->tryAcquire();

        $this->expectException(BulkheadFullException::class);
        $bulkhead->execute(fn() => 'should fail');
    }

    public function testTracksActiveCount(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 5);

        $bulkhead->tryAcquire();
        $bulkhead->tryAcquire();

        self::assertSame(2, $bulkhead->getActiveCount());
        self::assertSame(3, $bulkhead->getAvailablePermits());

        $bulkhead->release();

        self::assertSame(1, $bulkhead->getActiveCount());
        self::assertSame(4, $bulkhead->getAvailablePermits());
    }

    public function testTryAcquireReturnsFalseWhenFull(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 2);

        self::assertTrue($bulkhead->tryAcquire());
        self::assertTrue($bulkhead->tryAcquire());
        self::assertFalse($bulkhead->tryAcquire());
    }

    public function testGetNameReturnsConfiguredName(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 5);

        self::assertSame('test-bulkhead', $bulkhead->getName());
    }

    public function testMetricsAreTracked(): void
    {
        $bulkhead = $this->createBulkhead(maxConcurrent: 2);

        $bulkhead->execute(fn() => null);
        $bulkhead->execute(fn() => null);

        $bulkhead->tryAcquire();
        $bulkhead->tryAcquire();
        $bulkhead->tryAcquire();

        $metrics = $bulkhead->getMetrics();

        self::assertSame(4, $metrics['acquired']);
        self::assertSame(1, $metrics['rejected']);
        self::assertSame(2, $metrics['released']);
    }

    private function createBulkhead(int $maxConcurrent): SemaphoreBulkhead
    {
        return new SemaphoreBulkhead(
            name: 'test-bulkhead',
            config: new BulkheadConfig(maxConcurrentCalls: $maxConcurrent),
            logger: new NullLogger()
        );
    }
}
```

---

### BulkheadConfigTest

**File:** `tests/Unit/Infrastructure/Resilience/Bulkhead/BulkheadConfigTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\Bulkhead;

use Infrastructure\Resilience\Bulkhead\BulkheadConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(BulkheadConfig::class)]
final class BulkheadConfigTest extends TestCase
{
    public function testDefaultConfig(): void
    {
        $config = BulkheadConfig::default();

        self::assertSame(10, $config->maxConcurrentCalls);
        self::assertSame(0, $config->maxWaitDuration);
        self::assertTrue($config->fairness);
    }

    public function testForCpuBound(): void
    {
        $config = BulkheadConfig::forCpuBound(cpuCores: 8);

        self::assertSame(8, $config->maxConcurrentCalls);
    }

    public function testForIoBound(): void
    {
        $config = BulkheadConfig::forIoBound(cpuCores: 8);

        self::assertSame(80, $config->maxConcurrentCalls);
    }

    public function testForExternalService(): void
    {
        $config = BulkheadConfig::forExternalService(maxConnections: 25);

        self::assertSame(25, $config->maxConcurrentCalls);
        self::assertSame(5000, $config->maxWaitDuration);
    }

    public function testThrowsOnInvalidMaxConcurrent(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new BulkheadConfig(maxConcurrentCalls: 0);
    }

    public function testThrowsOnNegativeWaitDuration(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new BulkheadConfig(maxWaitDuration: -1);
    }
}
```
