# Metrics Patterns Reference

## Metric Types

| Type | Description | Operations | Example |
|------|-------------|-----------|---------|
| **Counter** | Monotonically increasing value | `inc()` | Total HTTP requests, errors |
| **Gauge** | Value that goes up and down | `set()`, `inc()`, `dec()` | Active connections, queue size |
| **Histogram** | Distribution of observations | `observe()` | Request duration, response size |
| **Summary** | Pre-calculated quantiles | `observe()` | Latency percentiles (client-side) |

### When to Use Each Type

| Scenario | Type | Reasoning |
|----------|------|-----------|
| Count of events | Counter | Always increases, can compute rate |
| Current state | Gauge | Snapshot value, goes up/down |
| Latency distribution | Histogram | Server-side percentile calculation |
| Pre-computed percentiles | Summary | No server-side aggregation needed |

## Prometheus PHP Client Setup

### Installation and Registry

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\Storage\Redis;

final readonly class MetricsRegistryFactory
{
    public function create(string $redisHost, int $redisPort = 6379): CollectorRegistry
    {
        $adapter = new Redis([
            'host' => $redisHost,
            'port' => $redisPort,
            'database' => 2,
            'timeout' => 0.5,
            'read_timeout' => 1.0,
            'persistent_connections' => true,
        ]);

        return new CollectorRegistry($adapter);
    }
}
```

### RED Metrics for HTTP Services

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\Counter;
use Prometheus\Histogram;

final class HttpRedMetrics
{
    private readonly Counter $requestsTotal;
    private readonly Counter $errorsTotal;
    private readonly Histogram $requestDuration;

    public function __construct(CollectorRegistry $registry)
    {
        $this->requestsTotal = $registry->getOrRegisterCounter(
            'http',
            'requests_total',
            'Total number of HTTP requests',
            ['method', 'route', 'status_code'],
        );

        $this->errorsTotal = $registry->getOrRegisterCounter(
            'http',
            'errors_total',
            'Total number of HTTP errors (4xx/5xx)',
            ['method', 'route', 'status_code'],
        );

        $this->requestDuration = $registry->getOrRegisterHistogram(
            'http',
            'request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'route'],
            [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        );
    }

    public function recordRequest(string $method, string $route, int $statusCode, float $duration): void
    {
        $this->requestsTotal->inc([$method, $route, (string) $statusCode]);
        $this->requestDuration->observe($duration, [$method, $route]);

        if ($statusCode >= 400) {
            $this->errorsTotal->inc([$method, $route, (string) $statusCode]);
        }
    }
}
```

### PSR-15 Metrics Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class MetricsMiddleware implements MiddlewareInterface
{
    public function __construct(
        private HttpRedMetrics $metrics,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $startTime = microtime(true);

        $response = $handler->handle($request);

        $duration = microtime(true) - $startTime;
        $route = $request->getAttribute('route_name', $request->getUri()->getPath());

        $this->metrics->recordRequest(
            $request->getMethod(),
            $route,
            $response->getStatusCode(),
            $duration,
        );

        return $response;
    }
}
```

### Custom Business Metrics

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\Counter;
use Prometheus\Gauge;
use Prometheus\Histogram;

final class BusinessMetrics
{
    private readonly Counter $ordersCreated;
    private readonly Counter $paymentsProcessed;
    private readonly Histogram $orderProcessingTime;
    private readonly Gauge $cartItemsCount;

    public function __construct(CollectorRegistry $registry)
    {
        $this->ordersCreated = $registry->getOrRegisterCounter(
            'business',
            'orders_created_total',
            'Total orders created',
            ['payment_method', 'currency'],
        );

        $this->paymentsProcessed = $registry->getOrRegisterCounter(
            'business',
            'payments_processed_total',
            'Total payments processed',
            ['gateway', 'status'],
        );

        $this->orderProcessingTime = $registry->getOrRegisterHistogram(
            'business',
            'order_processing_seconds',
            'Time to process an order',
            ['type'],
            [0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
        );

        $this->cartItemsCount = $registry->getOrRegisterGauge(
            'business',
            'active_cart_items',
            'Number of items in active shopping carts',
            [],
        );
    }

    public function recordOrderCreated(string $paymentMethod, string $currency): void
    {
        $this->ordersCreated->inc([$paymentMethod, $currency]);
    }

    public function recordPaymentProcessed(string $gateway, string $status): void
    {
        $this->paymentsProcessed->inc([$gateway, $status]);
    }

    public function observeOrderProcessing(string $type, float $seconds): void
    {
        $this->orderProcessingTime->observe($seconds, [$type]);
    }

    public function setActiveCartItems(int $count): void
    {
        $this->cartItemsCount->set($count, []);
    }
}
```

### /metrics Endpoint

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Action;

use Prometheus\CollectorRegistry;
use Prometheus\RenderTextFormat;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class MetricsAction implements RequestHandlerInterface
{
    public function __construct(
        private CollectorRegistry $registry,
    ) {}

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $renderer = new RenderTextFormat();
        $metrics = $renderer->render($this->registry->getMetricFamilySamples());

        $response = new \Nyholm\Psr7\Response(200);

        return $response
            ->withHeader('Content-Type', RenderTextFormat::MIME_TYPE)
            ->withBody(\Nyholm\Psr7\Stream::create($metrics));
    }
}
```

## Alerting Rules Examples

### Prometheus Alerting Rules (YAML)

```yaml
groups:
  - name: http_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) / rate(http_requests_total[5m]) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High HTTP error rate (> 1%)"
          description: "Error rate is {{ $value | humanizePercentage }} for {{ $labels.route }}"

      - alert: HighLatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High p99 latency (> 2s)"

      - alert: ServiceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Service {{ $labels.instance }} is down"

  - name: business_alerts
    rules:
      - alert: NoOrdersCreated
        expr: rate(business_orders_created_total[15m]) == 0
        for: 15m
        labels:
          severity: warning
        annotations:
          summary: "No orders created in 15 minutes"

      - alert: PaymentFailureSpike
        expr: rate(business_payments_processed_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Payment failure rate spike"
```

## Metrics Naming Conventions

| Convention | Rule | Example |
|------------|------|---------|
| Namespace | Service or domain prefix | `http_`, `business_`, `db_` |
| Name | Snake_case, descriptive | `requests_total`, `duration_seconds` |
| Unit suffix | Always include unit | `_seconds`, `_bytes`, `_total` |
| Counter suffix | End with `_total` | `http_requests_total` |
| Labels | Low cardinality only | `method`, `status_code`, NOT `user_id` |
