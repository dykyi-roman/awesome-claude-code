---
name: check-observability-coverage
description: Analyzes PHP code for observability gaps. Detects missing structured logging, absent correlation IDs, missing health endpoints, unstructured log calls, and missing OpenTelemetry setup.
---

# Observability Coverage Check

Analyze PHP code for observability gaps that hinder debugging, monitoring, and incident response in production.

## Detection Patterns

### 1. Unstructured Logging

```php
<?php

declare(strict_types=1);

// BAD: Raw error_log with unstructured output
final class PaymentService
{
    public function charge(Money $amount): void
    {
        error_log('Payment failed for amount ' . $amount->cents());
    }
}

// BAD: echo/print_r/var_dump in production code
final class OrderService
{
    public function process(Order $order): void
    {
        echo 'Processing order: ' . $order->id();
        print_r($order->items());
        var_dump($order->status());
    }
}

// GOOD: Structured logging with context
final readonly class PaymentService
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function charge(Money $amount, UserId $userId): void
    {
        $this->logger->error('Payment charge failed', [
            'user_id' => $userId->toString(),
            'amount_cents' => $amount->cents(),
            'currency' => $amount->currency()->value,
            'gateway' => 'stripe',
            'timestamp' => (new DateTimeImmutable())->format(DateTimeInterface::RFC3339),
        ]);
    }
}
```

### 2. Missing Correlation IDs

```php
<?php

declare(strict_types=1);

// BAD: No request tracing across services
final readonly class ApiClient
{
    public function call(string $endpoint, array $payload): Response
    {
        return $this->httpClient->post($endpoint, [
            'json' => $payload,
            // No correlation ID forwarded
        ]);
    }
}

// BAD: Logger without correlation context
final readonly class OrderHandler
{
    public function handle(CreateOrderCommand $command): void
    {
        $this->logger->info('Order created');
        // Which request triggered this? No way to trace.
    }
}

// GOOD: Correlation ID propagated across services
final readonly class ApiClient
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private CorrelationIdProvider $correlationProvider,
    ) {}

    public function call(string $endpoint, array $payload): Response
    {
        return $this->httpClient->post($endpoint, [
            'json' => $payload,
            'headers' => [
                'X-Request-ID' => $this->correlationProvider->get(),
                'X-Correlation-ID' => $this->correlationProvider->get(),
            ],
        ]);
    }
}

// GOOD: Logger processor adds correlation ID automatically
final readonly class CorrelationIdProcessor
{
    public function __construct(
        private CorrelationIdProvider $correlationProvider,
    ) {}

    public function __invoke(LogRecord $record): LogRecord
    {
        return $record->with(extra: [
            'correlation_id' => $this->correlationProvider->get(),
        ]);
    }
}
```

### 3. Missing Health Endpoints

```php
<?php

declare(strict_types=1);

// BAD: No health check endpoints -- load balancer cannot detect unhealthy instances
// Application has NO /health, /ready, or /live routes

// GOOD: Comprehensive health check
final readonly class HealthAction
{
    public function __construct(
        private PDO $database,
        private \Redis $redis,
        private AMQPConnection $queue,
    ) {}

    public function __invoke(): JsonResponse
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'queue' => $this->checkQueue(),
        ];

        $healthy = !in_array(false, $checks, true);

        return new JsonResponse(
            data: $checks,
            status: $healthy ? 200 : 503,
        );
    }

    private function checkDatabase(): bool
    {
        try {
            $this->database->query('SELECT 1');
            return true;
        } catch (\PDOException) {
            return false;
        }
    }

    private function checkRedis(): bool
    {
        try {
            return $this->redis->ping() === true;
        } catch (\RedisException) {
            return false;
        }
    }

    private function checkQueue(): bool
    {
        try {
            return $this->queue->isConnected();
        } catch (\AMQPException) {
            return false;
        }
    }
}
```

### 4. Missing Metrics Endpoint

```php
<?php

declare(strict_types=1);

// BAD: No Prometheus metrics exposed
// No /metrics endpoint, no counter/histogram tracking

// GOOD: Prometheus metrics endpoint with business metrics
final readonly class MetricsAction
{
    public function __construct(
        private CollectorRegistry $registry,
    ) {}

    public function __invoke(): Response
    {
        $renderer = new RenderTextFormat();
        $result = $renderer->render($this->registry->getMetricFamilySamples());

        return new Response($result, 200, [
            'Content-Type' => RenderTextFormat::MIME_TYPE,
        ]);
    }
}

// GOOD: Track business metrics
final readonly class OrderService
{
    public function __construct(
        private Counter $ordersCreated,
        private Histogram $orderProcessingDuration,
    ) {}

    public function create(OrderData $data): Order
    {
        $start = microtime(true);
        try {
            $order = $this->processOrder($data);
            $this->ordersCreated->incBy(1, ['status' => 'success']);
            return $order;
        } catch (\Throwable $e) {
            $this->ordersCreated->incBy(1, ['status' => 'failure']);
            throw $e;
        } finally {
            $this->orderProcessingDuration->observe(
                microtime(true) - $start,
                ['operation' => 'create'],
            );
        }
    }
}
```

### 5. Missing Tracing / OpenTelemetry Setup

```php
<?php

declare(strict_types=1);

// BAD: No tracing spans in cross-service communication
final readonly class OrderService
{
    public function create(OrderData $data): Order
    {
        $order = $this->repository->save(Order::create($data));
        $this->paymentService->charge($order->total());
        $this->inventoryService->reserve($order->items());
        // Cannot trace which step failed or which was slow
        return $order;
    }
}

// GOOD: OpenTelemetry spans for cross-service calls
final readonly class OrderService
{
    public function __construct(
        private TracerInterface $tracer,
        private OrderRepository $repository,
        private PaymentService $paymentService,
        private InventoryService $inventoryService,
    ) {}

    public function create(OrderData $data): Order
    {
        $span = $this->tracer->spanBuilder('order.create')
            ->setAttribute('order.items_count', count($data->items))
            ->startSpan();

        try {
            $order = $this->repository->save(Order::create($data));
            $span->setAttribute('order.id', $order->id()->toString());

            $paymentSpan = $this->tracer->spanBuilder('payment.charge')->startSpan();
            try {
                $this->paymentService->charge($order->total());
            } finally {
                $paymentSpan->end();
            }

            $inventorySpan = $this->tracer->spanBuilder('inventory.reserve')->startSpan();
            try {
                $this->inventoryService->reserve($order->items());
            } finally {
                $inventorySpan->end();
            }

            return $order;
        } catch (\Throwable $e) {
            $span->recordException($e);
            $span->setStatus(StatusCode::STATUS_ERROR, $e->getMessage());
            throw $e;
        } finally {
            $span->end();
        }
    }
}
```

## Grep Patterns

```bash
# Unstructured logging
Grep: "error_log\(|print_r\(|var_dump\(|var_export\(" --glob "**/*.php"
Grep: "echo\s+['\"]|echo\s+\\\$" --glob "**/src/**/*.php"

# Check for PSR-3 Logger usage
Grep: "LoggerInterface|LoggerAwareInterface" --glob "**/*.php"

# Missing correlation ID propagation
Grep: "X-Request-ID|X-Correlation-ID|correlation_id" --glob "**/*.php"

# Health check endpoints
Grep: "/health|/ready|/live|HealthCheck|HealthAction" --glob "**/*.php"

# Metrics endpoints
Grep: "/metrics|PrometheusMetrics|CollectorRegistry|Counter::class|Histogram::class" --glob "**/*.php"

# OpenTelemetry / tracing
Grep: "TracerInterface|spanBuilder|OpenTelemetry|Jaeger|Zipkin" --glob "**/*.php"

# Structured context in log calls
Grep: "->info\(|->error\(|->warning\(|->debug\(|->critical\(" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| var_dump/print_r in production code | 🔴 Critical |
| No health check endpoints | 🔴 Critical |
| Missing correlation ID propagation | 🟠 Major |
| No structured logging (error_log only) | 🟠 Major |
| No metrics/Prometheus endpoint | 🟠 Major |
| Missing OpenTelemetry tracing | 🟡 Minor |
| Log messages without context array | 🟡 Minor |

## Output Format

```markdown
### Observability Gap: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Unstructured Log|Missing Correlation|No Health Check|No Metrics|No Tracing]

**Issue:**
[Description of the observability gap]

**Impact:**
- Cannot trace requests across services
- No alerting on failures
- Debugging in production is guesswork

**Code:**
```php
// Current code without observability
```

**Fix:**
```php
// With proper observability
```
```

## When This Is Acceptable

- **Development/test environment** -- var_dump/print_r may be used temporarily during local debugging
- **CLI commands** -- Console output via `echo` is standard for CLI tools
- **Early prototype stage** -- Before production deployment, minimal logging is acceptable
- **Single-service monolith** -- Correlation IDs are less critical when there are no cross-service calls

### False Positive Indicators
- Code is in a test file or fixture
- echo/print_r is inside a Console Command `execute()` method
- Health check exists but is registered in routing config, not discoverable via grep
