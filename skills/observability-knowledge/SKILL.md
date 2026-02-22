---
name: observability-knowledge
description: Observability knowledge base. Provides three pillars (logs, metrics, traces), structured logging, distributed tracing, metrics collection (RED/USE), SLI/SLO/SLA definitions for observability audits and generation.
---

# Observability Knowledge Base

Quick reference for the three pillars of observability, instrumentation patterns, and SLI/SLO/SLA definitions in PHP applications.

## Three Pillars Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      THREE PILLARS OF OBSERVABILITY                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│   │      LOGS        │  │     METRICS      │  │     TRACES       │          │
│   │                  │  │                  │  │                  │          │
│   │  What happened   │  │  How much/many   │  │  How requests    │          │
│   │  (discrete       │  │  (aggregated     │  │  flow through    │          │
│   │   events)        │  │   measurements)  │  │  services)       │          │
│   │                  │  │                  │  │                  │          │
│   │  • Errors        │  │  • Counters      │  │  • Spans         │          │
│   │  • Audit trail   │  │  • Gauges        │  │  • Context       │          │
│   │  • Debug info    │  │  • Histograms    │  │  • Latency       │          │
│   │                  │  │                  │  │                  │          │
│   │  JSON structured │  │  Prometheus      │  │  OpenTelemetry   │          │
│   │  Monolog         │  │  StatsD          │  │  Jaeger/Zipkin   │          │
│   └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│            │                     │                      │                    │
│            └─────────────────────┼──────────────────────┘                    │
│                                  │                                           │
│                        ┌─────────▼─────────┐                                │
│                        │  CORRELATION ID   │                                │
│                        │  (links all three │                                │
│                        │   pillars)        │                                │
│                        └───────────────────┘                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Structured Logging

### JSON Log Format

| Field | Type | Description | Required |
|-------|------|-------------|----------|
| `timestamp` | ISO 8601 | When event occurred | Yes |
| `level` | string | RFC 5424 log level | Yes |
| `message` | string | Human-readable description | Yes |
| `channel` | string | Logger channel name | Yes |
| `context` | object | Structured event data | No |
| `correlation_id` | string | Request/trace identifier | Yes |
| `service` | string | Service/app name | Yes |
| `environment` | string | prod/staging/dev | Yes |

### Log Levels (RFC 5424)

| Level | Code | When to Use |
|-------|------|-------------|
| **EMERGENCY** | 0 | System is unusable |
| **ALERT** | 1 | Immediate action required |
| **CRITICAL** | 2 | Critical conditions (component failure) |
| **ERROR** | 3 | Runtime errors (not requiring immediate action) |
| **WARNING** | 4 | Exceptional but handled conditions |
| **NOTICE** | 5 | Normal but significant events |
| **INFO** | 6 | Informational messages (request processed) |
| **DEBUG** | 7 | Detailed debug information |

### Monolog Context Processor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

final readonly class CorrelationIdProcessor implements ProcessorInterface
{
    public function __construct(
        private CorrelationIdHolder $holder,
    ) {}

    public function __invoke(LogRecord $record): LogRecord
    {
        return $record->with(
            extra: array_merge($record->extra, [
                'correlation_id' => $this->holder->get(),
                'service' => $_ENV['APP_SERVICE_NAME'] ?? 'unknown',
                'environment' => $_ENV['APP_ENV'] ?? 'unknown',
            ]),
        );
    }
}
```

### Correlation ID Holder

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

final class CorrelationIdHolder
{
    private ?string $correlationId = null;

    public function set(string $correlationId): void
    {
        $this->correlationId = $correlationId;
    }

    public function get(): string
    {
        if ($this->correlationId === null) {
            $this->correlationId = uuid_create(UUID_TYPE_RANDOM);
        }

        return $this->correlationId;
    }
}
```

## Distributed Tracing

### OpenTelemetry Concepts

| Concept | Description |
|---------|-------------|
| **Trace** | End-to-end journey of a request across services |
| **Span** | Single unit of work within a trace (has start/end time) |
| **SpanContext** | Trace ID + Span ID + flags, propagated across boundaries |
| **Attributes** | Key-value metadata on spans |
| **Events** | Timestamped annotations within a span |
| **Links** | Connections between spans in different traces |
| **Baggage** | Cross-cutting key-value pairs propagated with context |

### W3C Trace Context Header

```
traceparent: {version}-{trace-id}-{parent-id}-{trace-flags}
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

tracestate: vendor1=value1,vendor2=value2
```

| Part | Length | Description |
|------|--------|-------------|
| version | 2 hex | Always `00` |
| trace-id | 32 hex | Globally unique trace identifier |
| parent-id | 16 hex | ID of parent span |
| trace-flags | 2 hex | `01` = sampled |

### OpenTelemetry PHP SDK Setup

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Telemetry;

use OpenTelemetry\API\Globals;
use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\API\Trace\TracerInterface;

final readonly class TracingService
{
    private TracerInterface $tracer;

    public function __construct(string $serviceName = 'my-app')
    {
        $this->tracer = Globals::tracerProvider()->getTracer($serviceName);
    }

    public function traceOperation(string $operationName, callable $operation, array $attributes = []): mixed
    {
        $span = $this->tracer
            ->spanBuilder($operationName)
            ->setSpanKind(SpanKind::KIND_INTERNAL)
            ->startSpan();

        $scope = $span->activate();

        try {
            foreach ($attributes as $key => $value) {
                $span->setAttribute($key, $value);
            }

            $result = $operation();
            $span->setStatus(StatusCode::STATUS_OK);

            return $result;
        } catch (\Throwable $e) {
            $span->setStatus(StatusCode::STATUS_ERROR, $e->getMessage());
            $span->recordException($e);

            throw $e;
        } finally {
            $scope->detach();
            $span->end();
        }
    }

    public function traceHttpClient(string $method, string $url, callable $request): mixed
    {
        $span = $this->tracer
            ->spanBuilder(sprintf('%s %s', $method, $url))
            ->setSpanKind(SpanKind::KIND_CLIENT)
            ->setAttribute('http.method', $method)
            ->setAttribute('http.url', $url)
            ->startSpan();

        $scope = $span->activate();

        try {
            $result = $request();
            $span->setStatus(StatusCode::STATUS_OK);

            return $result;
        } catch (\Throwable $e) {
            $span->setStatus(StatusCode::STATUS_ERROR, $e->getMessage());

            throw $e;
        } finally {
            $scope->detach();
            $span->end();
        }
    }
}
```

## Metrics

### RED Method (Request-Driven Services)

| Metric | What | Unit | Example |
|--------|------|------|---------|
| **R**ate | Requests per second | req/s | HTTP requests per second by endpoint |
| **E**rrors | Failed requests per second | err/s | 5xx responses per second |
| **D**uration | Latency distribution | ms | Response time p50, p95, p99 |

### USE Method (Resource-Oriented)

| Metric | What | Example |
|--------|------|---------|
| **U**tilization | % time resource is busy | CPU usage, disk I/O |
| **S**aturation | Queued work | Request queue length |
| **E**rrors | Error count | Disk errors, connection failures |

### Golden Signals (Google SRE)

| Signal | Description | RED Equivalent |
|--------|-------------|----------------|
| **Latency** | Time to service a request | Duration |
| **Traffic** | Demand on the system | Rate |
| **Errors** | Rate of failed requests | Errors |
| **Saturation** | How full the system is | (USE method) |

### Prometheus PHP Client

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Metrics;

use Prometheus\CollectorRegistry;
use Prometheus\RenderTextFormat;
use Prometheus\Storage\Redis;

final class PrometheusMetricsCollector
{
    private readonly CollectorRegistry $registry;

    public function __construct(\Redis $redis)
    {
        $adapter = Redis::fromExistingConnection($redis);
        $this->registry = new CollectorRegistry($adapter);
    }

    public function incrementRequestCount(string $method, string $route, int $statusCode): void
    {
        $counter = $this->registry->getOrRegisterCounter(
            'app',
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'route', 'status_code'],
        );

        $counter->inc([$method, $route, (string) $statusCode]);
    }

    public function observeRequestDuration(string $method, string $route, float $durationSeconds): void
    {
        $histogram = $this->registry->getOrRegisterHistogram(
            'app',
            'http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'route'],
            [0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        );

        $histogram->observe($durationSeconds, [$method, $route]);
    }

    public function setActiveConnections(int $count): void
    {
        $gauge = $this->registry->getOrRegisterGauge(
            'app',
            'active_connections',
            'Current active connections',
            [],
        );

        $gauge->set($count, []);
    }

    public function renderMetrics(): string
    {
        $renderer = new RenderTextFormat();

        return $renderer->render($this->registry->getMetricFamilySamples());
    }
}
```

## SLI / SLO / SLA

| Concept | Definition | Example |
|---------|------------|---------|
| **SLI** (Service Level Indicator) | Measurable metric of service behavior | Request latency p99 < 200ms |
| **SLO** (Service Level Objective) | Target value for an SLI | 99.9% of requests within 200ms |
| **SLA** (Service Level Agreement) | Contract with consequences | 99.5% uptime or credit issued |

### Common SLIs

| SLI Type | Formula | Target (SLO) |
|----------|---------|---------------|
| **Availability** | `successful_requests / total_requests` | 99.9% (three nines) |
| **Latency** | `requests < threshold / total_requests` | 99% < 200ms, 99.9% < 1s |
| **Error Rate** | `error_requests / total_requests` | < 0.1% |
| **Throughput** | `requests / time_window` | > 1000 req/s |
| **Freshness** | `time_since_last_update` | < 5 minutes |

### Error Budget

```
Error Budget = 1 - SLO

Example: SLO = 99.9%
Error Budget = 0.1% = ~43 minutes/month downtime allowed

Budget remaining = Error Budget - Actual Errors
If budget exhausted → freeze deployments, focus on reliability
```

## Quick Reference Tables

### Observability Tool Selection

| Need | Tool/Library | PHP Integration |
|------|-------------|----------------|
| Structured logging | Monolog | `monolog/monolog` |
| Log aggregation | ELK Stack, Loki | Monolog handlers |
| Metrics collection | Prometheus | `promphp/prometheus_client_php` |
| Metrics visualization | Grafana | Prometheus data source |
| Distributed tracing | Jaeger, Zipkin | OpenTelemetry PHP SDK |
| APM | Datadog, New Relic | PHP extensions/agents |
| Error tracking | Sentry | `sentry/sentry-php` |
| Health checks | Custom endpoint | PSR-15 middleware |

### Alerting Thresholds

| Alert | Condition | Severity |
|-------|-----------|----------|
| High error rate | > 1% of requests 5xx | Critical |
| High latency | p99 > 2s for 5 min | Warning |
| Service down | Health check fails 3x | Critical |
| Disk usage | > 85% used | Warning |
| Queue backlog | > 10k unprocessed | Warning |
| Memory usage | > 90% for 10 min | Critical |

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| No structured logging (plain text) | Logger config, log output | Warning |
| Missing correlation IDs | Middleware, log processors | Critical |
| No metrics endpoint | Routes, health controllers | Warning |
| Untraced external calls | HTTP clients, adapters | Warning |
| Swallowed exceptions without logging | Catch blocks | Critical |
| No health check endpoint | Routes, controllers | Warning |
| Missing request/response logging | Middleware | Warning |
| No alerting rules defined | Monitoring config | Warning |

## Detection Patterns

```bash
# Logging setup
Grep: "Monolog|LoggerInterface|PsrLogLoggerInterface" --glob "**/*.php"
Grep: "monolog" --glob "**/composer.json"
Grep: "structured|json_formatter|JsonFormatter" --glob "**/*.php"

# Correlation IDs
Grep: "correlation.id|correlationId|X-Correlation-ID|X-Request-ID" --glob "**/*.php"

# Metrics
Grep: "Prometheus|CollectorRegistry|Counter|Histogram|Gauge" --glob "**/*.php"
Grep: "prometheus|promphp" --glob "**/composer.json"
Grep: "/metrics|metricsEndpoint" --glob "**/*.php"

# Tracing
Grep: "OpenTelemetry|Tracer|Span|SpanBuilder" --glob "**/*.php"
Grep: "open-telemetry|opentelemetry" --glob "**/composer.json"
Grep: "traceparent|tracestate|W3C" --glob "**/*.php"

# Health checks
Grep: "health|healthcheck|readiness|liveness" --glob "**/*.php"
Grep: "/health|/ready|/live" --glob "**/routes*.php"

# Error tracking
Grep: "Sentry|sentry|Bugsnag|Rollbar" --glob "**/*.php"
Grep: "sentry/sentry" --glob "**/composer.json"

# Log levels and context
Grep: "->error\(|->critical\(|->warning\(|->info\(" --glob "**/*.php"
Grep: "LogLevel::" --glob "**/*.php"
```

## References

For detailed information, load these reference files:

- `references/logging-patterns.md` — Structured logging, Monolog setup, context processors, log aggregation patterns
- `references/metrics-patterns.md` — Counter/Gauge/Histogram types, Prometheus PHP client, RED metrics, alerting rules
- `references/tracing-patterns.md` — OpenTelemetry PHP SDK, span creation, context propagation, sampling strategies
