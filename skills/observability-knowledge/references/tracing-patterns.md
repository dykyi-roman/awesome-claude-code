# Tracing Patterns Reference

## OpenTelemetry PHP SDK Setup

### Composer Dependencies

```json
{
  "require": {
    "open-telemetry/sdk": "^1.0",
    "open-telemetry/exporter-otlp": "^1.0",
    "open-telemetry/transport-grpc": "^1.0"
  }
}
```

### Tracer Provider Configuration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Telemetry;

use OpenTelemetry\API\Trace\TracerProviderInterface;
use OpenTelemetry\Contrib\Otlp\SpanExporter;
use OpenTelemetry\SDK\Resource\ResourceInfo;
use OpenTelemetry\SDK\Resource\ResourceInfoFactory;
use OpenTelemetry\SDK\Trace\Sampler\AlwaysOnSampler;
use OpenTelemetry\SDK\Trace\SpanProcessor\BatchSpanProcessor;
use OpenTelemetry\SDK\Trace\TracerProvider;
use OpenTelemetry\SemConv\ResourceAttributes;

final readonly class TracerProviderFactory
{
    public function create(
        string $serviceName,
        string $serviceVersion,
        string $otlpEndpoint,
    ): TracerProviderInterface {
        $resource = ResourceInfoFactory::defaultResource()->merge(
            ResourceInfo::create([
                ResourceAttributes::SERVICE_NAME => $serviceName,
                ResourceAttributes::SERVICE_VERSION => $serviceVersion,
                ResourceAttributes::DEPLOYMENT_ENVIRONMENT => $_ENV['APP_ENV'] ?? 'production',
            ]),
        );

        $exporter = new SpanExporter($otlpEndpoint);

        $spanProcessor = new BatchSpanProcessor(
            exporter: $exporter,
            maxQueueSize: 2048,
            scheduledDelayMillis: 5000,
            maxExportBatchSize: 512,
        );

        return new TracerProvider(
            spanProcessors: [$spanProcessor],
            sampler: new AlwaysOnSampler(),
            resource: $resource,
        );
    }
}
```

## Creating Spans

### Basic Span Creation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Telemetry;

use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\API\Trace\TracerInterface;

final readonly class SpanHelper
{
    public function __construct(
        private TracerInterface $tracer,
    ) {}

    public function wrapInternal(string $name, callable $operation, array $attributes = []): mixed
    {
        $span = $this->tracer
            ->spanBuilder($name)
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

    public function wrapDatabaseQuery(string $query, callable $operation): mixed
    {
        $span = $this->tracer
            ->spanBuilder('DB query')
            ->setSpanKind(SpanKind::KIND_CLIENT)
            ->setAttribute('db.system', 'mysql')
            ->setAttribute('db.statement', $this->sanitizeQuery($query))
            ->startSpan();

        $scope = $span->activate();

        try {
            $result = $operation();
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

    private function sanitizeQuery(string $query): string
    {
        return preg_replace('/\'[^\']*\'/', '?', $query) ?? $query;
    }
}
```

### Span Kinds

| Kind | Description | Example |
|------|-------------|---------|
| `KIND_INTERNAL` | Default, internal operation | Business logic, computation |
| `KIND_SERVER` | Handling incoming request | HTTP server, gRPC server |
| `KIND_CLIENT` | Making outgoing request | HTTP client, DB query |
| `KIND_PRODUCER` | Publishing message | RabbitMQ publish, Kafka produce |
| `KIND_CONSUMER` | Consuming message | RabbitMQ consume, Kafka consume |

## Context Propagation Across HTTP Calls

### Outgoing Request (Inject Context)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\API\Trace\TracerInterface;
use OpenTelemetry\Context\Context;
use OpenTelemetry\Context\Propagation\TextMapPropagatorInterface;
use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

final readonly class TracedHttpClient implements ClientInterface
{
    public function __construct(
        private ClientInterface $inner,
        private TracerInterface $tracer,
        private TextMapPropagatorInterface $propagator,
    ) {}

    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        $span = $this->tracer
            ->spanBuilder(sprintf('%s %s', $request->getMethod(), $request->getUri()->getHost()))
            ->setSpanKind(SpanKind::KIND_CLIENT)
            ->setAttribute('http.method', $request->getMethod())
            ->setAttribute('http.url', (string) $request->getUri())
            ->startSpan();

        $scope = $span->activate();

        $headers = [];
        $this->propagator->inject($headers, context: Context::getCurrent());

        foreach ($headers as $name => $value) {
            $request = $request->withHeader($name, $value);
        }

        try {
            $response = $this->inner->sendRequest($request);

            $span->setAttribute('http.status_code', $response->getStatusCode());
            $span->setStatus(
                $response->getStatusCode() >= 400
                    ? StatusCode::STATUS_ERROR
                    : StatusCode::STATUS_OK,
            );

            return $response;
        } catch (\Throwable $e) {
            $span->setStatus(StatusCode::STATUS_ERROR, $e->getMessage());
            $span->recordException($e);

            throw $e;
        } finally {
            $scope->detach();
            $span->end();
        }
    }
}
```

### Incoming Request (Extract Context)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use OpenTelemetry\API\Trace\SpanKind;
use OpenTelemetry\API\Trace\StatusCode;
use OpenTelemetry\API\Trace\TracerInterface;
use OpenTelemetry\Context\Propagation\TextMapPropagatorInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class TracingMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TracerInterface $tracer,
        private TextMapPropagatorInterface $propagator,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $parentContext = $this->propagator->extract($request->getHeaders());

        $span = $this->tracer
            ->spanBuilder(sprintf('%s %s', $request->getMethod(), $request->getUri()->getPath()))
            ->setParent($parentContext)
            ->setSpanKind(SpanKind::KIND_SERVER)
            ->setAttribute('http.method', $request->getMethod())
            ->setAttribute('http.url', (string) $request->getUri())
            ->startSpan();

        $scope = $span->activate();

        try {
            $response = $handler->handle($request);

            $span->setAttribute('http.status_code', $response->getStatusCode());
            $span->setStatus(
                $response->getStatusCode() >= 500
                    ? StatusCode::STATUS_ERROR
                    : StatusCode::STATUS_OK,
            );

            return $response;
        } catch (\Throwable $e) {
            $span->setStatus(StatusCode::STATUS_ERROR, $e->getMessage());
            $span->recordException($e);

            throw $e;
        } finally {
            $scope->detach();
            $span->end();
        }
    }
}
```

## Trace Sampling Strategies

| Strategy | Description | Use Case |
|----------|-------------|----------|
| **AlwaysOn** | Sample every trace | Dev/staging, low traffic |
| **AlwaysOff** | Never sample | Disable tracing |
| **TraceIdRatio** | Sample X% of traces | Production (e.g., 10%) |
| **ParentBased** | Follow parent's decision | Microservice chains |
| **RateLimiting** | Max N traces per second | High-traffic production |

### Rate-Based Sampling

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Telemetry;

use OpenTelemetry\SDK\Trace\Sampler\TraceIdRatioBasedSampler;
use OpenTelemetry\SDK\Trace\Sampler\ParentBased;
use OpenTelemetry\SDK\Trace\SamplerInterface;

final readonly class SamplerFactory
{
    public function createForEnvironment(string $environment): SamplerInterface
    {
        $ratio = match ($environment) {
            'production' => 0.1,
            'staging' => 0.5,
            default => 1.0,
        };

        return new ParentBased(
            root: new TraceIdRatioBasedSampler($ratio),
        );
    }
}
```

## Span Attributes (Semantic Conventions)

| Attribute | Type | Description |
|-----------|------|-------------|
| `http.method` | string | HTTP method (GET, POST) |
| `http.url` | string | Full URL |
| `http.status_code` | int | Response status code |
| `db.system` | string | Database type (mysql, pgsql) |
| `db.statement` | string | Sanitized SQL query |
| `messaging.system` | string | Queue type (rabbitmq, kafka) |
| `messaging.destination` | string | Queue/topic name |
| `rpc.system` | string | RPC system (grpc) |
| `exception.type` | string | Exception class name |
| `exception.message` | string | Error message |

## Trace-to-Log Correlation

Link traces and logs by including trace context in log entries:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging\Processor;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;
use OpenTelemetry\API\Trace\Span;

final readonly class TraceContextProcessor implements ProcessorInterface
{
    public function __invoke(LogRecord $record): LogRecord
    {
        $spanContext = Span::getCurrent()->getContext();

        if (!$spanContext->isValid()) {
            return $record;
        }

        return $record->with(
            extra: array_merge($record->extra, [
                'trace_id' => $spanContext->getTraceId(),
                'span_id' => $spanContext->getSpanId(),
                'trace_flags' => $spanContext->getTraceFlags(),
            ]),
        );
    }
}
```

This processor adds `trace_id` and `span_id` to every log entry, enabling direct navigation from a log line to the corresponding trace in Jaeger or Zipkin.
