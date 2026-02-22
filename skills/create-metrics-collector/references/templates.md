# Metrics Collector Templates

## MetricsCollectorInterface

**File:** `src/Infrastructure/Metrics/MetricsCollectorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

interface MetricsCollectorInterface
{
    /**
     * Increment a counter metric.
     *
     * @param array<string, string> $labels
     */
    public function increment(string $name, array $labels = [], float $value = 1.0): void;

    /**
     * Set a gauge metric to an arbitrary value.
     *
     * @param array<string, string> $labels
     */
    public function gauge(string $name, float $value, array $labels = []): void;

    /**
     * Observe a value for a histogram metric.
     *
     * @param array<string, string> $labels
     */
    public function histogram(string $name, float $value, array $labels = []): void;
}
```

---

## Counter

**File:** `src/Infrastructure/Metrics/Counter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

final readonly class Counter
{
    public function __construct(
        private MetricsCollectorInterface $collector,
        private string $name,
        private string $description = ''
    ) {}

    /**
     * @param array<string, string> $labels
     */
    public function increment(array $labels = [], float $value = 1.0): void
    {
        $this->collector->increment($this->name, $labels, $value);
    }

    public function name(): string
    {
        return $this->name;
    }

    public function description(): string
    {
        return $this->description;
    }
}
```

---

## Gauge

**File:** `src/Infrastructure/Metrics/Gauge.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

final readonly class Gauge
{
    public function __construct(
        private MetricsCollectorInterface $collector,
        private string $name,
        private string $description = ''
    ) {}

    /**
     * @param array<string, string> $labels
     */
    public function set(float $value, array $labels = []): void
    {
        $this->collector->gauge($this->name, $value, $labels);
    }

    public function name(): string
    {
        return $this->name;
    }

    public function description(): string
    {
        return $this->description;
    }
}
```

---

## Histogram

**File:** `src/Infrastructure/Metrics/Histogram.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

final readonly class Histogram
{
    public function __construct(
        private MetricsCollectorInterface $collector,
        private string $name,
        private string $description = ''
    ) {}

    /**
     * @param array<string, string> $labels
     */
    public function observe(float $value, array $labels = []): void
    {
        $this->collector->histogram($this->name, $value, $labels);
    }

    public function name(): string
    {
        return $this->name;
    }

    public function description(): string
    {
        return $this->description;
    }
}
```

---

## PrometheusMetricsCollector

**File:** `src/Infrastructure/Metrics/PrometheusMetricsCollector.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\RenderTextFormat;

final readonly class PrometheusMetricsCollector implements MetricsCollectorInterface
{
    private const DEFAULT_NAMESPACE = 'app';

    public function __construct(
        private CollectorRegistry $registry,
        private string $namespace = self::DEFAULT_NAMESPACE
    ) {}

    public function increment(string $name, array $labels = [], float $value = 1.0): void
    {
        $counter = $this->registry->getOrRegisterCounter(
            $this->namespace,
            $name,
            $name,
            array_keys($labels)
        );

        $counter->incBy($value, array_values($labels));
    }

    public function gauge(string $name, float $value, array $labels = []): void
    {
        $gauge = $this->registry->getOrRegisterGauge(
            $this->namespace,
            $name,
            $name,
            array_keys($labels)
        );

        $gauge->set($value, array_values($labels));
    }

    public function histogram(string $name, float $value, array $labels = []): void
    {
        $histogram = $this->registry->getOrRegisterHistogram(
            $this->namespace,
            $name,
            $name,
            array_keys($labels)
        );

        $histogram->observe($value, array_values($labels));
    }

    public function render(): string
    {
        $renderer = new RenderTextFormat();

        return $renderer->render($this->registry->getMetricFamilySamples());
    }
}
```

---

## NullMetricsCollector

**File:** `src/Infrastructure/Metrics/NullMetricsCollector.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

final readonly class NullMetricsCollector implements MetricsCollectorInterface
{
    public function increment(string $name, array $labels = [], float $value = 1.0): void
    {
    }

    public function gauge(string $name, float $value, array $labels = []): void
    {
    }

    public function histogram(string $name, float $value, array $labels = []): void
    {
    }
}
```

---

## MetricsMiddleware

**File:** `src/Infrastructure/Metrics/MetricsMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class MetricsMiddleware implements MiddlewareInterface
{
    public function __construct(
        private MetricsCollectorInterface $collector
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        $startTime = microtime(true);

        try {
            $response = $handler->handle($request);

            $this->recordMetrics($request, $response->getStatusCode(), $startTime);

            return $response;
        } catch (\Throwable $exception) {
            $this->recordMetrics($request, 500, $startTime);

            throw $exception;
        }
    }

    private function recordMetrics(
        ServerRequestInterface $request,
        int $statusCode,
        float $startTime
    ): void {
        $method = $request->getMethod();
        $path = $request->getUri()->getPath();
        $duration = microtime(true) - $startTime;

        $this->collector->increment(
            'http_requests_total',
            ['method' => $method, 'path' => $path, 'status' => (string) $statusCode]
        );

        $this->collector->histogram(
            'http_request_duration_seconds',
            $duration,
            ['method' => $method, 'path' => $path]
        );
    }
}
```

---

## MetricsAction

**File:** `src/Infrastructure/Metrics/MetricsAction.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class MetricsAction
{
    public function __construct(
        private PrometheusMetricsCollector $collector
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $metrics = $this->collector->render();

        return new \Nyholm\Psr7\Response(
            200,
            ['Content-Type' => 'text/plain; version=0.0.4; charset=utf-8'],
            $metrics
        );
    }
}
```
