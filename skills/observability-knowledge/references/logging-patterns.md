# Logging Patterns Reference

## Structured Logging Format (JSON)

Every log entry should be a single JSON line with consistent structure:

```json
{
  "timestamp": "2024-11-15T14:32:08.123Z",
  "level": "ERROR",
  "channel": "payment",
  "message": "Payment processing failed",
  "context": {
    "order_id": "ord-123",
    "amount_cents": 5000,
    "gateway": "stripe",
    "error_code": "card_declined"
  },
  "extra": {
    "correlation_id": "req-abc-def-123",
    "service": "payment-service",
    "environment": "production",
    "user_id": "usr-456",
    "ip": "192.168.1.1"
  }
}
```

## Log Levels (RFC 5424)

| Level | Numeric | Usage | Example |
|-------|---------|-------|---------|
| EMERGENCY | 0 | System completely down | Database cluster unreachable |
| ALERT | 1 | Must fix immediately | Payment gateway certificate expiring |
| CRITICAL | 2 | Component failure | Cache server connection lost |
| ERROR | 3 | Operation failed | Order creation failed due to validation |
| WARNING | 4 | Handled degradation | Fallback cache used, retry succeeded |
| NOTICE | 5 | Significant normal event | User role changed, config reloaded |
| INFO | 6 | Standard operation | Request processed, job completed |
| DEBUG | 7 | Detailed diagnostics | SQL queries, cache hit/miss |

## Monolog Setup

### Base Configuration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\RotatingFileHandler;
use Monolog\Handler\StreamHandler;
use Monolog\Level;
use Monolog\Logger;

final readonly class LoggerFactory
{
    public function create(string $channel, string $logPath, string $environment): Logger
    {
        $logger = new Logger($channel);

        $jsonFormatter = new JsonFormatter();
        $jsonFormatter->includeStacktraces(true);

        if ($environment === 'production') {
            $handler = new RotatingFileHandler(
                filename: $logPath . '/' . $channel . '.log',
                maxFiles: 14,
                level: Level::Info,
            );
        } else {
            $handler = new StreamHandler(
                stream: 'php://stderr',
                level: Level::Debug,
            );
        }

        $handler->setFormatter($jsonFormatter);
        $logger->pushHandler($handler);

        return $logger;
    }
}
```

### Processors

#### CorrelationIdProcessor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging\Processor;

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
            ]),
        );
    }
}
```

#### RequestContextProcessor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging\Processor;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;
use Psr\Http\Message\ServerRequestInterface;

final class RequestContextProcessor implements ProcessorInterface
{
    private ?ServerRequestInterface $request = null;

    public function setRequest(ServerRequestInterface $request): void
    {
        $this->request = $request;
    }

    public function __invoke(LogRecord $record): LogRecord
    {
        if ($this->request === null) {
            return $record;
        }

        return $record->with(
            extra: array_merge($record->extra, [
                'http_method' => $this->request->getMethod(),
                'http_uri' => (string) $this->request->getUri(),
                'http_user_agent' => $this->request->getHeaderLine('User-Agent'),
                'client_ip' => $this->request->getServerParams()['REMOTE_ADDR'] ?? 'unknown',
            ]),
        );
    }
}
```

#### UserContextProcessor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging\Processor;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

final class UserContextProcessor implements ProcessorInterface
{
    private ?string $userId = null;
    private ?string $userRole = null;

    public function setUser(string $userId, string $role): void
    {
        $this->userId = $userId;
        $this->userRole = $role;
    }

    public function __invoke(LogRecord $record): LogRecord
    {
        if ($this->userId === null) {
            return $record;
        }

        return $record->with(
            extra: array_merge($record->extra, [
                'user_id' => $this->userId,
                'user_role' => $this->userRole,
            ]),
        );
    }
}
```

## Context Propagation

### PSR-15 Middleware for Correlation ID

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CorrelationIdMiddleware implements MiddlewareInterface
{
    private const string HEADER = 'X-Correlation-ID';

    public function __construct(
        private CorrelationIdHolder $holder,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $correlationId = $request->getHeaderLine(self::HEADER);

        if ($correlationId === '') {
            $correlationId = uuid_create(UUID_TYPE_RANDOM);
        }

        $this->holder->set($correlationId);

        $request = $request->withAttribute('correlation_id', $correlationId);

        $response = $handler->handle($request);

        return $response->withHeader(self::HEADER, $correlationId);
    }
}
```

## Log Aggregation Patterns

| Pattern | Description | Tools |
|---------|-------------|-------|
| **Centralized** | All logs shipped to central store | ELK, Loki, CloudWatch |
| **Sidecar** | Agent per container collects logs | Fluentd, Filebeat |
| **Direct** | App writes directly to aggregator | Monolog Gelf/Logstash handler |
| **Stdout/Stderr** | App writes to stdout, orchestrator collects | Docker logging driver, K8s |

### Monolog Handler for Logstash

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Monolog\Formatter\LogstashFormatter;
use Monolog\Handler\SocketHandler;
use Monolog\Level;
use Monolog\Logger;

final readonly class LogstashLoggerFactory
{
    public function create(string $channel, string $logstashHost, int $logstashPort): Logger
    {
        $logger = new Logger($channel);

        $handler = new SocketHandler(
            connectionString: sprintf('tcp://%s:%d', $logstashHost, $logstashPort),
            level: Level::Info,
        );

        $handler->setFormatter(new LogstashFormatter(
            applicationName: $channel,
        ));

        $logger->pushHandler($handler);

        return $logger;
    }
}
```

## Logging Best Practices

| Practice | Description |
|----------|-------------|
| Always use structured format | JSON, not free-text messages |
| Include correlation ID | Links logs across services |
| Use appropriate log level | Do not log DEBUG in production |
| Log at boundaries | Entry/exit of services and layers |
| Sanitize sensitive data | Never log passwords, tokens, PII |
| Use contextual fields | Pass data in `context`, not message string |
| Set log rotation | Prevent disk exhaustion |
| Sample verbose logs | Reduce volume for high-traffic paths |
