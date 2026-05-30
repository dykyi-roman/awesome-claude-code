---
name: create-metrics-collector
description: Generates Metrics Collector for PHP 8.4. Creates MetricsCollectorInterface, Counter/Gauge/Histogram wrappers, PrometheusMetricsCollector, MetricsMiddleware for RED metrics. Includes unit tests.
---

# Metrics Collector Generator

Creates metrics collection infrastructure for application observability and monitoring.

## When to Use

| Scenario | Example |
|----------|---------|
| Request monitoring | Track request rate, errors, duration (RED) |
| Business metrics | Count orders, revenue, active users |
| Performance profiling | Histogram of response times |
| Health dashboards | Expose `/metrics` for Prometheus scraping |

## Component Characteristics

### MetricsCollectorInterface
- Metrics contract for increment, gauge, histogram operations
- Backend-agnostic: swap Prometheus for StatsD or custom
- Supports labels for dimensional metrics

### Counter
- Monotonically increasing metric wrapper
- Tracks totals: requests, errors, processed items
- Supports labels for per-endpoint counts

### Gauge
- Point-in-time value metric wrapper
- Tracks current state: active connections, queue size
- Can increase and decrease

### Histogram
- Distribution metric wrapper
- Tracks request duration, response size
- Configurable bucket boundaries

### PrometheusMetricsCollector
- Prometheus PHP client adapter
- Registers counters, gauges, histograms
- Thread-safe with shared storage

### MetricsMiddleware
- PSR-15 middleware collecting RED metrics automatically
- Rate: total request count per endpoint
- Errors: error count by status code
- Duration: response time histogram

### MetricsAction
- `/metrics` endpoint exposing Prometheus format
- Returns `text/plain` with all registered metrics

### NullMetricsCollector
- Null Object pattern for testing and development
- All operations are no-ops
- Drop-in replacement without side effects

---

## Generation Process

### Step 1: Generate Core Components

Place alongside other observability infrastructure.

1. `MetricsCollectorInterface.php` — Metrics contract
2. `Counter.php` — Counter metric wrapper
3. `Gauge.php` — Gauge metric wrapper
4. `Histogram.php` — Histogram metric wrapper

### Step 2: Generate Implementations

Co-located with the core components.

1. `PrometheusMetricsCollector.php` — Prometheus adapter
2. `NullMetricsCollector.php` — Null Object for testing

### Step 3: Generate HTTP Components

Place alongside other HTTP middleware / entry points.

1. `MetricsMiddleware.php` — PSR-15 RED metrics middleware
2. `MetricsAction.php` — `/metrics` endpoint action

### Step 4: Generate Tests

1. `NullMetricsCollectorTest.php` — Null object behavior tests
2. `MetricsMiddlewareTest.php` — Middleware metrics tests

---

## File Placement

| Component | Path |
|-----------|------|
| All Classes | `src/{architecture-path}/Metrics/` |
| Unit Tests | `tests/Unit/{architecture-path}/Metrics/` |

> `{architecture-path}` represents your project's architecture-specific folders. Metrics components typically live alongside other observability infrastructure (logging, tracing). Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `MetricsCollectorInterface` | `MetricsCollectorInterface` |
| Counter | `Counter` | `Counter` |
| Gauge | `Gauge` | `Gauge` |
| Histogram | `Histogram` | `Histogram` |
| Prometheus | `PrometheusMetricsCollector` | `PrometheusMetricsCollector` |
| Null Object | `NullMetricsCollector` | `NullMetricsCollector` |
| Middleware | `MetricsMiddleware` | `MetricsMiddleware` |
| Action | `MetricsAction` | `MetricsAction` |
| Test | `{ClassName}Test` | `MetricsMiddlewareTest` |

---

## Quick Template Reference

### MetricsCollectorInterface

```php
interface MetricsCollectorInterface
{
    /** @param array<string, string> $labels */
    public function increment(string $name, array $labels = [], float $value = 1.0): void;

    /** @param array<string, string> $labels */
    public function gauge(string $name, float $value, array $labels = []): void;

    /** @param array<string, string> $labels */
    public function histogram(string $name, float $value, array $labels = []): void;
}
```

### MetricsMiddleware

```php
final readonly class MetricsMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface;
}
```

### NullMetricsCollector

```php
final readonly class NullMetricsCollector implements MetricsCollectorInterface
{
    public function increment(string $name, array $labels = [], float $value = 1.0): void {}
    public function gauge(string $name, float $value, array $labels = []): void {}
    public function histogram(string $name, float $value, array $labels = []): void {}
}
```

---

## Usage Example

```php
// Middleware auto-collects RED metrics
$middleware = new MetricsMiddleware($collector);

// Manual metrics in use cases
$collector->increment('orders_created_total', ['channel' => 'web']);
$collector->gauge('active_connections', $pool->activeCount());
$collector->histogram('payment_duration_seconds', $elapsed, ['gateway' => 'stripe']);

// Expose via /metrics endpoint
$app->get('/metrics', new MetricsAction($collector));
```

---

## RED Metrics Pattern

```
Rate     ──→ http_requests_total{method, path, status}
Errors   ──→ http_requests_total{status=~"5.."}
Duration ──→ http_request_duration_seconds{method, path}
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| High cardinality labels | Prometheus storage explosion | Limit label values, no user IDs |
| No null implementation | Cannot disable metrics in tests | NullMetricsCollector |
| Inline metric names | Typos, inconsistency | Define constants or enum |
| Missing error metrics | Cannot calculate error rate | Track status codes |
| No histogram buckets | Default buckets don't fit use case | Configure per metric |
| Metrics in domain layer | Infrastructure leak | Keep in infrastructure only |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — MetricsCollectorInterface, Counter, Gauge, Histogram, Prometheus, Middleware templates
- `references/examples.md` — Integration examples and tests
