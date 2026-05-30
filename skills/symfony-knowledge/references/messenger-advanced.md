# Symfony Messenger Advanced

Retry strategies, dead letter queues, transports, middleware, worker management, and advanced CQRS patterns.

## Multiple Bus Configuration

Separate buses enforce CQRS boundaries: commands mutate state, queries return data, events notify.

**Detection:**
```bash
# Single bus usage (potential violation)
Grep: "MessageBusInterface" --glob "**/Application/**/*.php" --output_mode count
Grep: "command\\.bus|query\\.bus|event\\.bus" --glob "**/config/**/*.yaml"
```

**Bad — single bus for everything:**
```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        buses:
            messenger.bus.default: ~  # Single bus — no separation
```

**Good — three buses with dedicated middleware:**
```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        default_bus: command.bus
        buses:
            command.bus:
                middleware:
                    - validation
                    - App\Shared\Infrastructure\Messenger\Middleware\DomainEventMiddleware
                    - doctrine_transaction
            query.bus:
                middleware:
                    - validation
            event.bus:
                default_middleware:
                    allow_no_handlers: true
                middleware:
                    - validation
```

## Transport Configuration

Transports define how messages are physically delivered (AMQP, Redis, Doctrine, in-memory).

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        transports:
            async:
                dsn: '%env(MESSENGER_TRANSPORT_DSN)%'  # amqp://guest:guest@rabbitmq:5672/%2f/messages
                options:
                    exchange:
                        name: app_exchange
                        type: topic
                    queues:
                        app_commands:
                            binding_keys: ['command.#']
                        app_events:
                            binding_keys: ['event.#']
                retry_strategy:
                    max_retries: 3
                    delay: 1000
                    multiplier: 2
                    max_delay: 60000

            async_priority_high:
                dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
                options:
                    queues:
                        high_priority: ~

            failed:
                dsn: 'doctrine://default?queue_name=failed'

        failure_transport: failed

        routing:
            App\Order\Application\Command\PlaceOrderCommand: async
            App\Payment\Application\Command\ProcessPaymentCommand: async_priority_high
            App\Shared\Domain\Event\DomainEvent: async
```

## Retry Strategy

Configure exponential backoff to handle transient failures.

**Detection:**
```bash
# Missing retry strategy
Grep: "retry_strategy" --glob "**/config/packages/messenger.yaml"

# Handlers without failure handling
Grep: "#\\[AsMessageHandler" --glob "src/**/*.php" --output_mode count
```

| Parameter | Default | Recommended | Description |
|-----------|---------|-------------|-------------|
| `max_retries` | 3 | 3-5 | Maximum retry attempts |
| `delay` | 1000 | 1000 | Initial delay in ms |
| `multiplier` | 2 | 2-3 | Delay multiplier per retry |
| `max_delay` | 0 | 60000 | Maximum delay cap in ms |
| `service` | null | custom | Custom retry strategy service |

**Custom retry strategy for domain-specific logic:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messenger;

use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Retry\RetryStrategyInterface;
use Symfony\Component\Messenger\Stamp\RedeliveryStamp;

final readonly class DomainAwareRetryStrategy implements RetryStrategyInterface
{
    public function __construct(
        private int $maxRetries = 3,
        private int $delayMs = 1000,
        private float $multiplier = 2.0,
    ) {}

    public function isRetryable(Envelope $message, ?\Throwable $throwable = null): bool
    {
        if ($throwable instanceof \App\Shared\Domain\Exception\NonRetryableException) {
            return false;
        }

        $retries = RedeliveryStamp::getRetryCountFromEnvelope($message);

        return $retries < $this->maxRetries;
    }

    public function getWaitingTime(Envelope $message, ?\Throwable $throwable = null): int
    {
        $retries = RedeliveryStamp::getRetryCountFromEnvelope($message);

        return (int) ($this->delayMs * ($this->multiplier ** $retries));
    }
}
```

## Failed Transport / Dead Letter Queue

Messages that exhaust all retries are moved to the failed transport.

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        failure_transport: failed
        transports:
            failed:
                dsn: 'doctrine://default?queue_name=failed'
```

**Console commands for failed message management:**
```bash
# List failed messages
php bin/console messenger:failed:show

# Retry specific failed message
php bin/console messenger:failed:retry 42

# Retry all failed messages
php bin/console messenger:failed:retry

# Remove a failed message
php bin/console messenger:failed:remove 42
```

**Custom failed message handler for alerting:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messenger;

use Psr\Log\LoggerInterface;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Messenger\Event\WorkerMessageFailedEvent;

#[AsEventListener(event: WorkerMessageFailedEvent::class)]
final readonly class FailedMessageAlertListener
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function __invoke(WorkerMessageFailedEvent $event): void
    {
        if ($event->willRetry()) {
            return;
        }

        $this->logger->critical('Message permanently failed', [
            'message_class' => $event->getEnvelope()->getMessage()::class,
            'error' => $event->getThrowable()->getMessage(),
            'trace' => $event->getThrowable()->getTraceAsString(),
        ]);
    }
}
```

## Middleware Pipeline

Custom middleware for cross-cutting concerns: logging, correlation, validation, transactions.

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Psr\Log\LoggerInterface;
use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Middleware\MiddlewareInterface;
use Symfony\Component\Messenger\Middleware\StackInterface;
use Symfony\Component\Messenger\Stamp\BusNameStamp;

final readonly class CommandLoggingMiddleware implements MiddlewareInterface
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function handle(Envelope $envelope, StackInterface $stack): Envelope
    {
        $messageClass = $envelope->getMessage()::class;

        $this->logger->info('Handling message', [
            'message' => $messageClass,
            'bus' => $envelope->last(BusNameStamp::class)?->getBusName(),
        ]);

        $startTime = microtime(true);

        try {
            $envelope = $stack->next()->handle($envelope, $stack);

            $this->logger->info('Message handled', [
                'message' => $messageClass,
                'duration_ms' => round((microtime(true) - $startTime) * 1000, 2),
            ]);

            return $envelope;
        } catch (\Throwable $e) {
            $this->logger->error('Message handling failed', [
                'message' => $messageClass,
                'error' => $e->getMessage(),
                'duration_ms' => round((microtime(true) - $startTime) * 1000, 2),
            ]);

            throw $e;
        }
    }
}
```

**Domain event dispatching middleware:**
```php
<?php

declare(strict_types=1);

namespace Middleware;

use Domain\AggregateRoot;
use Domain\EventDispatcherInterface;
use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Middleware\MiddlewareInterface;
use Symfony\Component\Messenger\Middleware\StackInterface;
use Symfony\Component\Messenger\Stamp\HandledStamp;

final readonly class DomainEventMiddleware implements MiddlewareInterface
{
    public function __construct(
        private EventDispatcherInterface $eventDispatcher,
    ) {}

    public function handle(Envelope $envelope, StackInterface $stack): Envelope
    {
        $envelope = $stack->next()->handle($envelope, $stack);

        $handledStamp = $envelope->last(HandledStamp::class);
        $result = $handledStamp?->getResult();

        if ($result instanceof AggregateRoot) {
            foreach ($result->releaseEvents() as $event) {
                $this->eventDispatcher->dispatch($event);
            }
        }

        return $envelope;
    }
}
```

## Stamps and Envelope

Stamps carry metadata through the middleware pipeline.

| Stamp | Purpose | Example |
|-------|---------|---------|
| `BusNameStamp` | Identifies which bus dispatched the message | Auto-added by bus |
| `DelayStamp` | Delays message processing | `new DelayStamp(5000)` — 5 sec delay |
| `HandledStamp` | Result from handler | Auto-added after handling |
| `SentStamp` | Message was sent to transport | Auto-added by SendMessageMiddleware |
| `RedeliveryStamp` | Retry count and error info | Auto-added on retry |
| `TransportMessageIdStamp` | Transport-level message ID | Auto-added by transport |

**Custom correlation stamp for tracing:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messenger\Stamp;

use Symfony\Component\Messenger\Stamp\StampInterface;

final readonly class CorrelationStamp implements StampInterface
{
    public function __construct(
        public string $correlationId,
        public string $causationId,
    ) {}
}
```

## Worker Management

### Supervisor Configuration

```ini
; /etc/supervisor/conf.d/messenger-worker.conf
[program:messenger-consume]
command=php /app/bin/console messenger:consume async async_priority_high --time-limit=3600 --memory-limit=128M
user=www-data
numprocs=2
process_name=%(program_name)s_%(process_num)02d
autostart=true
autorestart=true
startsecs=0
startretries=10
stderr_logfile=/var/log/supervisor/messenger-worker-err.log
stdout_logfile=/var/log/supervisor/messenger-worker-out.log
```

### Worker Options

| Option | Recommended | Description |
|--------|-------------|-------------|
| `--time-limit` | 3600 | Restart worker after N seconds |
| `--memory-limit` | 128M | Restart worker when memory exceeds limit |
| `--limit` | 0 (unlimited) | Process N messages then stop |
| `--sleep` | 1 | Sleep seconds when no messages |
| `--bus` | specific bus | Consume from specific bus only |

**Graceful shutdown:** Workers handle `SIGTERM` — they finish the current message before stopping. Always send `SIGTERM`, never `SIGKILL`.

## Async vs Sync Domain Events

| Pattern | When | How |
|---------|------|-----|
| Sync (same aggregate) | Immediate consistency needed | `dispatch_after_current_bus` middleware |
| Async (cross-aggregate) | Eventual consistency acceptable | Route to async transport |
| Async (cross-context) | Different bounded contexts | Separate transport + serializer |

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        buses:
            event.bus:
                middleware:
                    - dispatch_after_current_bus  # Collects events, dispatches after command completes
```

## Message Serialization

Custom serializer for versioned message schemas and cross-service communication.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messenger;

use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Transport\Serialization\SerializerInterface;

final readonly class JsonMessageSerializer implements SerializerInterface
{
    public function decode(array $encodedEnvelope): Envelope
    {
        $body = json_decode($encodedEnvelope['body'], true, flags: JSON_THROW_ON_ERROR);
        $type = $encodedEnvelope['headers']['type'] ?? throw new \RuntimeException('Missing type header');
        $version = (int) ($encodedEnvelope['headers']['version'] ?? 1);

        $messageClass = $this->resolveClass($type, $version);
        $message = $messageClass::fromArray($body['data']);

        return new Envelope($message);
    }

    public function encode(Envelope $envelope): array
    {
        $message = $envelope->getMessage();

        return [
            'body' => json_encode([
                'data' => $message->toArray(),
                'occurred_at' => (new \DateTimeImmutable())->format(\DateTimeInterface::RFC3339_EXTENDED),
            ], JSON_THROW_ON_ERROR),
            'headers' => [
                'type' => $message::class,
                'version' => '1',
                'content-type' => 'application/json',
            ],
        ];
    }

    private function resolveClass(string $type, int $version): string
    {
        // Version migration logic
        return $type;
    }
}
```

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Bus Configuration | Three separate buses: command, query, event |
| Transports | AMQP for production, Doctrine for failed, in-memory for tests |
| Retry Strategy | Exponential backoff: 3-5 retries, 1s initial, 2x multiplier, 60s cap |
| Failed Transport | Always configure `failure_transport`; monitor with alerts |
| Middleware | Logging, correlation, validation, domain event dispatching |
| Workers | Supervisor with `--time-limit=3600 --memory-limit=128M` |
| Domain Events | Sync within aggregate, async across aggregates/contexts |
| Serialization | Custom serializer for cross-service communication; include version header |
