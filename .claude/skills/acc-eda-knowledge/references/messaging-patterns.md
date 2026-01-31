# Messaging Patterns

Detailed patterns for message brokers in Event-Driven Architecture.

## Messaging Models

### Point-to-Point (Queue)

```
┌──────────┐     ┌─────────┐     ┌──────────┐
│ Producer │────▶│  Queue  │────▶│ Consumer │
└──────────┘     └─────────┘     └──────────┘

- One message, one consumer
- Load balancing across consumers
- Message removed after consumption
```

### Publish-Subscribe (Topic)

```
┌──────────┐     ┌─────────┐     ┌──────────┐
│ Producer │────▶│Exchange/│────▶│Consumer A│
└──────────┘     │  Topic  │     └──────────┘
                 │         │     ┌──────────┐
                 │         │────▶│Consumer B│
                 └─────────┘     └──────────┘

- One message, many consumers
- Each subscriber gets a copy
- Fanout distribution
```

## RabbitMQ Patterns

### Exchange Types

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

enum ExchangeType: string
{
    case Direct = 'direct';   // Route by exact routing key
    case Topic = 'topic';     // Route by pattern (*.order.*, order.#)
    case Fanout = 'fanout';   // Broadcast to all queues
    case Headers = 'headers'; // Route by message headers
}
```

### Exchange Setup

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

use PhpAmqpLib\Channel\AMQPChannel;

final readonly class RabbitMQSetup
{
    public function __construct(
        private AMQPChannel $channel
    ) {}

    public function declareExchange(
        string $name,
        ExchangeType $type,
        bool $durable = true
    ): void {
        $this->channel->exchange_declare(
            exchange: $name,
            type: $type->value,
            passive: false,
            durable: $durable,
            auto_delete: false
        );
    }

    public function declareQueue(
        string $name,
        bool $durable = true,
        array $arguments = []
    ): void {
        $this->channel->queue_declare(
            queue: $name,
            passive: false,
            durable: $durable,
            exclusive: false,
            auto_delete: false,
            nowait: false,
            arguments: $arguments
        );
    }

    public function bindQueue(
        string $queue,
        string $exchange,
        string $routingKey = ''
    ): void {
        $this->channel->queue_bind(
            queue: $queue,
            exchange: $exchange,
            routing_key: $routingKey
        );
    }
}
```

### Producer Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

use PhpAmqpLib\Channel\AMQPChannel;
use PhpAmqpLib\Message\AMQPMessage;

final readonly class RabbitMQProducer
{
    public function __construct(
        private AMQPChannel $channel,
        private string $exchangeName
    ) {}

    public function publish(
        string $routingKey,
        array $payload,
        array $headers = []
    ): void {
        $message = new AMQPMessage(
            json_encode($payload, JSON_THROW_ON_ERROR),
            [
                'content_type' => 'application/json',
                'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
                'message_id' => $headers['message_id'] ?? Uuid::uuid4()->toString(),
                'timestamp' => time(),
                'application_headers' => new AMQPTable($headers),
            ]
        );

        $this->channel->basic_publish(
            msg: $message,
            exchange: $this->exchangeName,
            routing_key: $routingKey
        );
    }

    public function publishBatch(array $messages): void
    {
        $this->channel->batch_basic_publish_init();

        foreach ($messages as $msg) {
            $this->channel->batch_basic_publish(
                msg: $msg['message'],
                exchange: $this->exchangeName,
                routing_key: $msg['routing_key']
            );
        }

        $this->channel->batch_basic_publish_flush();
    }
}
```

### Consumer Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

use PhpAmqpLib\Channel\AMQPChannel;
use PhpAmqpLib\Message\AMQPMessage;

final class RabbitMQConsumer
{
    private bool $running = true;

    public function __construct(
        private readonly AMQPChannel $channel,
        private readonly string $queueName,
        private readonly MessageHandlerInterface $handler,
        private readonly LoggerInterface $logger
    ) {}

    public function consume(int $prefetchCount = 1): void
    {
        $this->channel->basic_qos(
            prefetch_size: 0,
            prefetch_count: $prefetchCount,
            a_global: false
        );

        $this->channel->basic_consume(
            queue: $this->queueName,
            consumer_tag: '',
            no_local: false,
            no_ack: false,
            exclusive: false,
            nowait: false,
            callback: fn (AMQPMessage $msg) => $this->processMessage($msg)
        );

        while ($this->running && $this->channel->is_consuming()) {
            $this->channel->wait();
        }
    }

    private function processMessage(AMQPMessage $message): void
    {
        try {
            $payload = json_decode($message->getBody(), true, 512, JSON_THROW_ON_ERROR);

            $this->handler->handle($payload, $message->get_properties());

            $message->ack();

        } catch (RetryableException $e) {
            $this->logger->warning('Message will be retried', [
                'error' => $e->getMessage(),
            ]);
            $message->nack(requeue: true);

        } catch (\Throwable $e) {
            $this->logger->error('Message processing failed', [
                'error' => $e->getMessage(),
            ]);
            $message->nack(requeue: false); // Goes to DLQ
        }
    }

    public function stop(): void
    {
        $this->running = false;
    }
}
```

### Dead Letter Queue

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

final readonly class DeadLetterQueueSetup
{
    public function setup(
        AMQPChannel $channel,
        string $mainQueue,
        string $dlqExchange,
        string $dlqQueue
    ): void {
        // Declare DLQ exchange
        $channel->exchange_declare(
            exchange: $dlqExchange,
            type: 'direct',
            durable: true
        );

        // Declare DLQ
        $channel->queue_declare(
            queue: $dlqQueue,
            durable: true
        );

        $channel->queue_bind($dlqQueue, $dlqExchange, $mainQueue);

        // Declare main queue with DLQ
        $channel->queue_declare(
            queue: $mainQueue,
            durable: true,
            arguments: new AMQPTable([
                'x-dead-letter-exchange' => $dlqExchange,
                'x-dead-letter-routing-key' => $mainQueue,
            ])
        );
    }
}
```

## Retry Patterns

### Exponential Backoff

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class RetryPolicy
{
    public function __construct(
        private int $maxRetries = 3,
        private int $baseDelayMs = 1000,
        private float $multiplier = 2.0,
        private int $maxDelayMs = 30000
    ) {}

    public function getDelay(int $attempt): int
    {
        $delay = (int) ($this->baseDelayMs * pow($this->multiplier, $attempt - 1));
        return min($delay, $this->maxDelayMs);
    }

    public function shouldRetry(int $attempt): bool
    {
        return $attempt < $this->maxRetries;
    }
}
```

### Delayed Retry with TTL

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMQ;

final readonly class DelayedRetryHandler
{
    public function __construct(
        private AMQPChannel $channel,
        private RetryPolicy $policy
    ) {}

    public function scheduleRetry(
        AMQPMessage $message,
        string $originalQueue,
        int $attempt
    ): void {
        if (!$this->policy->shouldRetry($attempt)) {
            $message->nack(requeue: false); // To DLQ
            return;
        }

        $delay = $this->policy->getDelay($attempt);
        $retryQueue = "{$originalQueue}.retry.{$delay}ms";

        // Create delay queue if not exists
        $this->channel->queue_declare(
            queue: $retryQueue,
            durable: true,
            arguments: new AMQPTable([
                'x-message-ttl' => $delay,
                'x-dead-letter-exchange' => '',
                'x-dead-letter-routing-key' => $originalQueue,
            ])
        );

        // Publish to delay queue
        $retryMessage = new AMQPMessage(
            $message->getBody(),
            array_merge($message->get_properties(), [
                'application_headers' => new AMQPTable([
                    'x-retry-count' => $attempt,
                ]),
            ])
        );

        $this->channel->basic_publish($retryMessage, '', $retryQueue);
        $message->ack();
    }
}
```

## Message Deduplication

### Idempotency Key

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

interface IdempotencyStoreInterface
{
    public function exists(string $key): bool;
    public function store(string $key, int $ttlSeconds): void;
}

final readonly class RedisIdempotencyStore implements IdempotencyStoreInterface
{
    public function __construct(
        private \Redis $redis,
        private string $prefix = 'idempotency:'
    ) {}

    public function exists(string $key): bool
    {
        return (bool) $this->redis->exists($this->prefix . $key);
    }

    public function store(string $key, int $ttlSeconds): void
    {
        $this->redis->setex(
            $this->prefix . $key,
            $ttlSeconds,
            '1'
        );
    }
}
```

### Idempotent Consumer Wrapper

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class IdempotentConsumer implements MessageHandlerInterface
{
    public function __construct(
        private MessageHandlerInterface $inner,
        private IdempotencyStoreInterface $store,
        private int $ttlSeconds = 86400 // 24 hours
    ) {}

    public function handle(array $payload, array $properties): void
    {
        $messageId = $properties['message_id'] ?? null;

        if ($messageId === null) {
            throw new \InvalidArgumentException('Message ID required for idempotency');
        }

        if ($this->store->exists($messageId)) {
            return; // Already processed
        }

        $this->inner->handle($payload, $properties);

        $this->store->store($messageId, $this->ttlSeconds);
    }
}
```

## Message Ordering

### Partition Key

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class OrderedProducer
{
    public function __construct(
        private ProducerInterface $producer
    ) {}

    public function publish(
        string $routingKey,
        array $payload,
        string $partitionKey
    ): void {
        // Use consistent hashing to route to specific queue/partition
        $partition = $this->getPartition($partitionKey);

        $this->producer->publish(
            "{$routingKey}.{$partition}",
            $payload,
            ['partition_key' => $partitionKey]
        );
    }

    private function getPartition(string $key): int
    {
        // Consistent hashing
        return crc32($key) % 10; // 10 partitions
    }
}
```

## Kafka Patterns (Alternative)

### Kafka Producer

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Kafka;

use RdKafka\Producer;
use RdKafka\ProducerTopic;

final readonly class KafkaEventProducer implements EventPublisherInterface
{
    private ProducerTopic $topic;

    public function __construct(
        private Producer $producer,
        string $topicName
    ) {
        $this->topic = $producer->newTopic($topicName);
    }

    public function publish(DomainEvent $event): void
    {
        $this->topic->produce(
            partition: RD_KAFKA_PARTITION_UA,
            msgflags: 0,
            payload: json_encode($event->toArray()),
            key: $event->aggregateId() // Ensures ordering per aggregate
        );

        $this->producer->poll(0);
    }

    public function flush(int $timeoutMs = 10000): void
    {
        $this->producer->flush($timeoutMs);
    }
}
```

### Kafka Consumer

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Kafka;

use RdKafka\KafkaConsumer;

final class KafkaEventConsumer
{
    private bool $running = true;

    public function __construct(
        private readonly KafkaConsumer $consumer,
        private readonly MessageHandlerInterface $handler,
        private readonly LoggerInterface $logger
    ) {}

    public function consume(array $topics, int $timeoutMs = 1000): void
    {
        $this->consumer->subscribe($topics);

        while ($this->running) {
            $message = $this->consumer->consume($timeoutMs);

            match ($message->err) {
                RD_KAFKA_RESP_ERR_NO_ERROR => $this->processMessage($message),
                RD_KAFKA_RESP_ERR__PARTITION_EOF => null, // End of partition
                RD_KAFKA_RESP_ERR__TIMED_OUT => null, // No message
                default => $this->logger->error('Kafka error: ' . $message->errstr()),
            };
        }
    }

    private function processMessage($message): void
    {
        try {
            $payload = json_decode($message->payload, true, 512, JSON_THROW_ON_ERROR);

            $this->handler->handle($payload, [
                'key' => $message->key,
                'offset' => $message->offset,
                'partition' => $message->partition,
            ]);

            $this->consumer->commit($message);

        } catch (\Throwable $e) {
            $this->logger->error('Failed to process message', [
                'offset' => $message->offset,
                'error' => $e->getMessage(),
            ]);
        }
    }

    public function stop(): void
    {
        $this->running = false;
    }
}
```

## Configuration Example

### Symfony Messenger Configuration

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        transports:
            async:
                dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
                options:
                    exchange:
                        name: events
                        type: topic
                    queues:
                        order_events:
                            binding_keys:
                                - 'order.*'
                retry_strategy:
                    max_retries: 3
                    delay: 1000
                    multiplier: 2
                    max_delay: 30000

            failed:
                dsn: 'doctrine://default?queue_name=failed'

        routing:
            'Domain\Order\Event\OrderPlaced': async
            'Domain\Order\Event\OrderShipped': async

        failure_transport: failed
```

## Directory Structure

```
src/Infrastructure/Messaging/
├── RabbitMQ/
│   ├── RabbitMQProducer.php
│   ├── RabbitMQConsumer.php
│   ├── RabbitMQSetup.php
│   ├── DelayedRetryHandler.php
│   └── DeadLetterQueueSetup.php
├── Kafka/
│   ├── KafkaEventProducer.php
│   └── KafkaEventConsumer.php
├── IdempotencyStoreInterface.php
├── RedisIdempotencyStore.php
├── RetryPolicy.php
└── EventEnvelope.php
```
