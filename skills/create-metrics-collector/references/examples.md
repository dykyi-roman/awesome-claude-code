# Metrics Collector Examples

## Business Metrics in Use Case

**File:** `src/Application/Order/CreateOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order;

use Infrastructure\Metrics\Counter;
use Infrastructure\Metrics\Histogram;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private Counter $ordersCreated,
        private Histogram $orderProcessingDuration
    ) {}

    public function execute(CreateOrderRequest $request): CreateOrderResponse
    {
        $startTime = microtime(true);

        $order = Order::create($request);
        $this->orders->save($order);

        $duration = microtime(true) - $startTime;

        $this->ordersCreated->increment(['channel' => $request->channel]);
        $this->orderProcessingDuration->observe($duration, ['channel' => $request->channel]);

        return new CreateOrderResponse($order->id()->toString());
    }
}
```

---

## Connection Pool Gauge

**File:** `src/Infrastructure/Database/MonitoredConnectionPool.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

use Infrastructure\Metrics\Gauge;

final class MonitoredConnectionPool
{
    private int $activeConnections = 0;

    public function __construct(
        private readonly ConnectionPool $pool,
        private readonly Gauge $activeConnectionsGauge
    ) {}

    public function acquire(): \PDO
    {
        $connection = $this->pool->acquire();
        $this->activeConnections++;
        $this->activeConnectionsGauge->set((float) $this->activeConnections);

        return $connection;
    }

    public function release(\PDO $connection): void
    {
        $this->pool->release($connection);
        $this->activeConnections--;
        $this->activeConnectionsGauge->set((float) $this->activeConnections);
    }
}
```

---

## Metrics Service Registration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\Storage\Redis;

final readonly class MetricsServiceFactory
{
    public static function create(\Redis $redis): PrometheusMetricsCollector
    {
        $adapter = Redis::fromExistingConnection($redis);
        $registry = new CollectorRegistry($adapter);

        return new PrometheusMetricsCollector($registry, 'myapp');
    }

    public static function createNull(): NullMetricsCollector
    {
        return new NullMetricsCollector();
    }
}
```

---

## Middleware Pipeline Registration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Metrics\MetricsMiddleware;
use Infrastructure\Metrics\MetricsCollectorInterface;

final readonly class MiddlewarePipeline
{
    public static function configure(MetricsCollectorInterface $collector): array
    {
        return [
            new MetricsMiddleware($collector),
        ];
    }
}
```

---

## Unit Tests

### NullMetricsCollectorTest

**File:** `tests/Unit/Infrastructure/Metrics/NullMetricsCollectorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Metrics;

use Infrastructure\Metrics\NullMetricsCollector;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(NullMetricsCollector::class)]
final class NullMetricsCollectorTest extends TestCase
{
    public function testIncrementDoesNothing(): void
    {
        $collector = new NullMetricsCollector();

        $collector->increment('test_counter', ['label' => 'value']);

        self::assertTrue(true);
    }

    public function testGaugeDoesNothing(): void
    {
        $collector = new NullMetricsCollector();

        $collector->gauge('test_gauge', 42.0, ['label' => 'value']);

        self::assertTrue(true);
    }

    public function testHistogramDoesNothing(): void
    {
        $collector = new NullMetricsCollector();

        $collector->histogram('test_histogram', 0.5, ['label' => 'value']);

        self::assertTrue(true);
    }

    public function testImplementsInterface(): void
    {
        $collector = new NullMetricsCollector();

        self::assertInstanceOf(\Infrastructure\Metrics\MetricsCollectorInterface::class, $collector);
    }
}
```

---

### MetricsMiddlewareTest

**File:** `tests/Unit/Infrastructure/Metrics/MetricsMiddlewareTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Metrics;

use Infrastructure\Metrics\MetricsCollectorInterface;
use Infrastructure\Metrics\MetricsMiddleware;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\UriInterface;
use Psr\Http\Server\RequestHandlerInterface;

#[Group('unit')]
#[CoversClass(MetricsMiddleware::class)]
final class MetricsMiddlewareTest extends TestCase
{
    public function testRecordsRequestCountAndDuration(): void
    {
        $collector = $this->createMock(MetricsCollectorInterface::class);

        $collector->expects(self::once())
            ->method('increment')
            ->with(
                'http_requests_total',
                self::callback(function (array $labels): bool {
                    return $labels['method'] === 'GET'
                        && $labels['path'] === '/api/users'
                        && $labels['status'] === '200';
                })
            );

        $collector->expects(self::once())
            ->method('histogram')
            ->with(
                'http_request_duration_seconds',
                self::isType('float'),
                self::callback(function (array $labels): bool {
                    return $labels['method'] === 'GET' && $labels['path'] === '/api/users';
                })
            );

        $middleware = new MetricsMiddleware($collector);
        $request = $this->createRequest('GET', '/api/users');
        $response = $this->createMock(ResponseInterface::class);
        $response->method('getStatusCode')->willReturn(200);

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($response);

        $middleware->process($request, $handler);
    }

    public function testRecords500OnException(): void
    {
        $collector = $this->createMock(MetricsCollectorInterface::class);

        $collector->expects(self::once())
            ->method('increment')
            ->with(
                'http_requests_total',
                self::callback(fn(array $labels) => $labels['status'] === '500')
            );

        $middleware = new MetricsMiddleware($collector);
        $request = $this->createRequest('POST', '/api/orders');

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willThrowException(new \RuntimeException('fail'));

        $this->expectException(\RuntimeException::class);

        $middleware->process($request, $handler);
    }

    public function testPassesThroughResponse(): void
    {
        $collector = new \Infrastructure\Metrics\NullMetricsCollector();
        $middleware = new MetricsMiddleware($collector);

        $request = $this->createRequest('GET', '/health');
        $expectedResponse = $this->createMock(ResponseInterface::class);
        $expectedResponse->method('getStatusCode')->willReturn(200);

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($expectedResponse);

        $result = $middleware->process($request, $handler);

        self::assertSame($expectedResponse, $result);
    }

    private function createRequest(string $method, string $path): ServerRequestInterface
    {
        $uri = $this->createMock(UriInterface::class);
        $uri->method('getPath')->willReturn($path);

        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getMethod')->willReturn($method);
        $request->method('getUri')->willReturn($uri);

        return $request;
    }
}
```
