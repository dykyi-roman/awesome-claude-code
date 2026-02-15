# Message Broker Adapter Templates

Complete PHP 8.4 templates for all message broker adapter components.

---

## Domain Layer

### MessageId.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Messaging;

use Ramsey\Uuid\Uuid;

final readonly class MessageId implements \Stringable, \JsonSerializable
{
    public function __construct(
        public string $value,
    ) {
        if (!Uuid::isValid($value)) {
            throw new \InvalidArgumentException("Invalid UUID: {$value}");
        }
    }

    public static function generate(): self
    {
        return new self(Uuid::uuid4()->toString());
    }

    public static function fromString(string $value): self
    {
        return new self($value);
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function __toString(): string
    {
        return $this->value;
    }

    public function jsonSerialize(): string
    {
        return $this->value;
    }
}
```

### Message.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Messaging;

final readonly class Message
{
    public function __construct(
        public MessageId $id,
        public string $body,
        public string $routingKey = '',
        public array $headers = [],
        public ?string $correlationId = null,
        public ?string $contentType = 'application/json',
        public ?\DateTimeImmutable $timestamp = null,
    ) {
        if (empty($body)) {
            throw new \InvalidArgumentException('Message body cannot be empty');
        }
    }

    public static function create(
        string $body,
        string $routingKey = '',
        array $headers = [],
    ): self {
        return new self(
            id: MessageId::generate(),
            body: $body,
            routingKey: $routingKey,
            headers: $headers,
            timestamp: new \DateTimeImmutable(),
        );
    }

    public function withHeader(string $key, string $value): self
    {
        $headers = $this->headers;
        $headers[$key] = $value;

        return new self(
            id: $this->id,
            body: $this->body,
            routingKey: $this->routingKey,
            headers: $headers,
            correlationId: $this->correlationId,
            contentType: $this->contentType,
            timestamp: $this->timestamp,
        );
    }

    public function withCorrelationId(string $correlationId): self
    {
        return new self(
            id: $this->id,
            body: $this->body,
            routingKey: $this->routingKey,
            headers: $this->headers,
            correlationId: $correlationId,
            contentType: $this->contentType,
            timestamp: $this->timestamp,
        );
    }

    public function getHeader(string $key, ?string $default = null): ?string
    {
        return $this->headers[$key] ?? $default;
    }

    public function hasHeader(string $key): bool
    {
        return isset($this->headers[$key]);
    }
}
```

### MessageBrokerInterface.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Messaging;

interface MessageBrokerInterface
{
    public function publish(Message $message, string $routingKey = ''): void;

    public function consume(string $queue, callable $handler): void;

    public function acknowledge(Message $message): void;

    public function reject(Message $message, bool $requeue = false): void;
}
```

### MessageSerializerInterface.php

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Messaging;

interface MessageSerializerInterface
{
    public function serialize(Message $message): string;

    public function deserialize(string $data): Message;
}
```

---

## Infrastructure Layer

### JsonMessageSerializer.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageId;
use Domain\Shared\Messaging\MessageSerializerInterface;

final readonly class JsonMessageSerializer implements MessageSerializerInterface
{
    public function serialize(Message $message): string
    {
        $data = [
            'id' => $message->id->value,
            'body' => $message->body,
            'routing_key' => $message->routingKey,
            'headers' => $message->headers,
            'correlation_id' => $message->correlationId,
            'content_type' => $message->contentType,
            'timestamp' => $message->timestamp?->format(\DateTimeInterface::ATOM),
        ];

        return json_encode($data, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
    }

    public function deserialize(string $data): Message
    {
        $decoded = json_decode($data, true, 512, JSON_THROW_ON_ERROR);

        if (!is_array($decoded)) {
            throw new \InvalidArgumentException('Invalid JSON data');
        }

        return new Message(
            id: MessageId::fromString($decoded['id']),
            body: $decoded['body'],
            routingKey: $decoded['routing_key'] ?? '',
            headers: $decoded['headers'] ?? [],
            correlationId: $decoded['correlation_id'] ?? null,
            contentType: $decoded['content_type'] ?? 'application/json',
            timestamp: isset($decoded['timestamp'])
                ? new \DateTimeImmutable($decoded['timestamp'])
                : null,
        );
    }
}
```

### RabbitMq/RabbitMqAdapter.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMq;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Domain\Shared\Messaging\MessageId;
use PhpAmqpLib\Channel\AMQPChannel;
use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

final class RabbitMqAdapter implements MessageBrokerInterface
{
    private AMQPChannel $channel;

    public function __construct(
        private readonly AMQPStreamConnection $connection,
        private readonly string $exchange,
        private readonly string $exchangeType = 'topic',
        private readonly int $prefetchCount = 10,
    ) {
        $this->channel = $this->connection->channel();
        $this->channel->exchange_declare(
            $this->exchange,
            $this->exchangeType,
            passive: false,
            durable: true,
            auto_delete: false,
        );
        $this->channel->basic_qos(
            prefetch_size: 0,
            prefetch_count: $this->prefetchCount,
            a_global: false,
        );
    }

    public function publish(Message $message, string $routingKey = ''): void
    {
        $routingKey = $routingKey ?: $message->routingKey;

        $amqpMessage = new AMQPMessage(
            $message->body,
            [
                'content_type' => $message->contentType,
                'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
                'message_id' => $message->id->value,
                'correlation_id' => $message->correlationId,
                'timestamp' => $message->timestamp?->getTimestamp(),
                'application_headers' => $message->headers,
            ]
        );

        $this->channel->basic_publish(
            $amqpMessage,
            $this->exchange,
            $routingKey,
        );
    }

    public function consume(string $queue, callable $handler): void
    {
        $this->channel->queue_declare(
            $queue,
            passive: false,
            durable: true,
            exclusive: false,
            auto_delete: false,
        );

        $callback = function (AMQPMessage $amqpMessage) use ($handler): void {
            $message = $this->fromAmqpMessage($amqpMessage);
            $handler($message);
        };

        $this->channel->basic_consume(
            $queue,
            consumer_tag: '',
            no_local: false,
            no_ack: false,
            exclusive: false,
            nowait: false,
            callback: $callback,
        );

        while ($this->channel->is_consuming()) {
            $this->channel->wait();
        }
    }

    public function acknowledge(Message $message): void
    {
        $deliveryTag = $message->getHeader('delivery_tag');

        if ($deliveryTag === null) {
            throw new \InvalidArgumentException('Message has no delivery_tag header');
        }

        $this->channel->basic_ack((int) $deliveryTag);
    }

    public function reject(Message $message, bool $requeue = false): void
    {
        $deliveryTag = $message->getHeader('delivery_tag');

        if ($deliveryTag === null) {
            throw new \InvalidArgumentException('Message has no delivery_tag header');
        }

        $this->channel->basic_reject((int) $deliveryTag, $requeue);
    }

    private function fromAmqpMessage(AMQPMessage $amqpMessage): Message
    {
        $headers = $amqpMessage->get_properties()['application_headers'] ?? [];
        $headers['delivery_tag'] = $amqpMessage->getDeliveryTag();

        return new Message(
            id: MessageId::fromString($amqpMessage->get('message_id')),
            body: $amqpMessage->getBody(),
            routingKey: $amqpMessage->getRoutingKey(),
            headers: $headers,
            correlationId: $amqpMessage->get('correlation_id'),
            contentType: $amqpMessage->get('content_type'),
            timestamp: isset($amqpMessage->get_properties()['timestamp'])
                ? (new \DateTimeImmutable())->setTimestamp($amqpMessage->get_properties()['timestamp'])
                : null,
        );
    }

    public function __destruct()
    {
        $this->channel->close();
        $this->connection->close();
    }
}
```

### Kafka/KafkaAdapter.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Kafka;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Domain\Shared\Messaging\MessageId;
use RdKafka\Conf;
use RdKafka\KafkaConsumer;
use RdKafka\Producer;

final class KafkaAdapter implements MessageBrokerInterface
{
    private Producer $producer;
    private ?KafkaConsumer $consumer = null;

    public function __construct(
        private readonly string $brokers,
        private readonly string $groupId = 'default',
        private readonly int $timeoutMs = 10000,
    ) {
        $conf = new Conf();
        $conf->set('metadata.broker.list', $this->brokers);

        $this->producer = new Producer($conf);
    }

    public function publish(Message $message, string $routingKey = ''): void
    {
        $topic = $routingKey ?: $message->routingKey;

        if (empty($topic)) {
            throw new \InvalidArgumentException('Topic (routing key) cannot be empty');
        }

        $kafkaTopic = $this->producer->newTopic($topic);

        $headers = array_merge($message->headers, [
            'message_id' => $message->id->value,
            'correlation_id' => $message->correlationId ?? '',
            'content_type' => $message->contentType ?? '',
            'timestamp' => $message->timestamp?->format(\DateTimeInterface::ATOM) ?? '',
        ]);

        $kafkaTopic->produce(
            RD_KAFKA_PARTITION_UA,
            0,
            $message->body,
            null,
            $headers,
        );

        $this->producer->poll(0);
        $this->producer->flush($this->timeoutMs);
    }

    public function consume(string $queue, callable $handler): void
    {
        $conf = new Conf();
        $conf->set('metadata.broker.list', $this->brokers);
        $conf->set('group.id', $this->groupId);
        $conf->set('auto.offset.reset', 'earliest');

        $this->consumer = new KafkaConsumer($conf);
        $this->consumer->subscribe([$queue]);

        while (true) {
            $kafkaMessage = $this->consumer->consume($this->timeoutMs);

            if ($kafkaMessage->err === RD_KAFKA_RESP_ERR_NO_ERROR) {
                $message = $this->fromKafkaMessage($kafkaMessage);
                $handler($message);
            }
        }
    }

    public function acknowledge(Message $message): void
    {
        if ($this->consumer === null) {
            throw new \RuntimeException('Consumer not initialized');
        }

        $offset = $message->getHeader('offset');
        $partition = $message->getHeader('partition');

        if ($offset === null || $partition === null) {
            throw new \InvalidArgumentException('Message has no offset/partition headers');
        }

        $this->consumer->commit();
    }

    public function reject(Message $message, bool $requeue = false): void
    {
        // Kafka doesn't support message rejection with requeue
        // Typically, you would commit or not commit the offset
        if (!$requeue) {
            $this->acknowledge($message);
        }
    }

    private function fromKafkaMessage(\RdKafka\Message $kafkaMessage): Message
    {
        $headers = $kafkaMessage->headers ?? [];

        return new Message(
            id: MessageId::fromString($headers['message_id'] ?? MessageId::generate()->value),
            body: $kafkaMessage->payload,
            routingKey: $kafkaMessage->topic_name,
            headers: array_merge($headers, [
                'offset' => $kafkaMessage->offset,
                'partition' => $kafkaMessage->partition,
            ]),
            correlationId: $headers['correlation_id'] ?? null,
            contentType: $headers['content_type'] ?? 'application/json',
            timestamp: isset($headers['timestamp'])
                ? new \DateTimeImmutable($headers['timestamp'])
                : null,
        );
    }
}
```

### Sqs/SqsAdapter.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Sqs;

use Aws\Sqs\SqsClient;
use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Domain\Shared\Messaging\MessageId;

final readonly class SqsAdapter implements MessageBrokerInterface
{
    public function __construct(
        private SqsClient $client,
        private string $queueUrl,
        private int $waitTimeSeconds = 20,
        private int $visibilityTimeout = 30,
    ) {
    }

    public function publish(Message $message, string $routingKey = ''): void
    {
        $messageAttributes = [
            'MessageId' => [
                'DataType' => 'String',
                'StringValue' => $message->id->value,
            ],
            'ContentType' => [
                'DataType' => 'String',
                'StringValue' => $message->contentType ?? 'application/json',
            ],
        ];

        if ($message->correlationId !== null) {
            $messageAttributes['CorrelationId'] = [
                'DataType' => 'String',
                'StringValue' => $message->correlationId,
            ];
        }

        foreach ($message->headers as $key => $value) {
            $messageAttributes[$key] = [
                'DataType' => 'String',
                'StringValue' => (string) $value,
            ];
        }

        $this->client->sendMessage([
            'QueueUrl' => $this->queueUrl,
            'MessageBody' => $message->body,
            'MessageAttributes' => $messageAttributes,
        ]);
    }

    public function consume(string $queue, callable $handler): void
    {
        while (true) {
            $result = $this->client->receiveMessage([
                'QueueUrl' => $this->queueUrl,
                'MaxNumberOfMessages' => 1,
                'WaitTimeSeconds' => $this->waitTimeSeconds,
                'VisibilityTimeout' => $this->visibilityTimeout,
                'MessageAttributeNames' => ['All'],
            ]);

            $sqsMessages = $result->get('Messages') ?? [];

            foreach ($sqsMessages as $sqsMessage) {
                $message = $this->fromSqsMessage($sqsMessage);
                $handler($message);
            }
        }
    }

    public function acknowledge(Message $message): void
    {
        $receiptHandle = $message->getHeader('receipt_handle');

        if ($receiptHandle === null) {
            throw new \InvalidArgumentException('Message has no receipt_handle header');
        }

        $this->client->deleteMessage([
            'QueueUrl' => $this->queueUrl,
            'ReceiptHandle' => $receiptHandle,
        ]);
    }

    public function reject(Message $message, bool $requeue = false): void
    {
        if (!$requeue) {
            $this->acknowledge($message);
            return;
        }

        $receiptHandle = $message->getHeader('receipt_handle');

        if ($receiptHandle === null) {
            throw new \InvalidArgumentException('Message has no receipt_handle header');
        }

        $this->client->changeMessageVisibility([
            'QueueUrl' => $this->queueUrl,
            'ReceiptHandle' => $receiptHandle,
            'VisibilityTimeout' => 0,
        ]);
    }

    private function fromSqsMessage(array $sqsMessage): Message
    {
        $attributes = $sqsMessage['MessageAttributes'] ?? [];
        $headers = [];

        foreach ($attributes as $name => $attribute) {
            $headers[$name] = $attribute['StringValue'] ?? '';
        }

        $headers['receipt_handle'] = $sqsMessage['ReceiptHandle'];

        return new Message(
            id: MessageId::fromString($headers['MessageId'] ?? MessageId::generate()->value),
            body: $sqsMessage['Body'],
            routingKey: '',
            headers: $headers,
            correlationId: $headers['CorrelationId'] ?? null,
            contentType: $headers['ContentType'] ?? 'application/json',
            timestamp: new \DateTimeImmutable(),
        );
    }
}
```

### InMemory/InMemoryAdapter.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\InMemory;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;

final class InMemoryAdapter implements MessageBrokerInterface
{
    /** @var array<string, array<Message>> */
    private array $queues = [];

    /** @var array<Message> */
    private array $publishedMessages = [];

    public function publish(Message $message, string $routingKey = ''): void
    {
        $queue = $routingKey ?: $message->routingKey;

        if (!isset($this->queues[$queue])) {
            $this->queues[$queue] = [];
        }

        $this->queues[$queue][] = $message;
        $this->publishedMessages[] = $message;
    }

    public function consume(string $queue, callable $handler): void
    {
        if (!isset($this->queues[$queue])) {
            return;
        }

        foreach ($this->queues[$queue] as $message) {
            $handler($message);
        }

        $this->queues[$queue] = [];
    }

    public function acknowledge(Message $message): void
    {
        // No-op for in-memory
    }

    public function reject(Message $message, bool $requeue = false): void
    {
        // No-op for in-memory
    }

    /** @return array<Message> */
    public function getPublishedMessages(): array
    {
        return $this->publishedMessages;
    }

    public function getQueueMessages(string $queue): array
    {
        return $this->queues[$queue] ?? [];
    }

    public function clear(): void
    {
        $this->queues = [];
        $this->publishedMessages = [];
    }
}
```

### MessageBrokerFactory.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

use Aws\Sqs\SqsClient;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Infrastructure\Messaging\InMemory\InMemoryAdapter;
use Infrastructure\Messaging\Kafka\KafkaAdapter;
use Infrastructure\Messaging\RabbitMq\RabbitMqAdapter;
use Infrastructure\Messaging\Sqs\SqsAdapter;
use PhpAmqpLib\Connection\AMQPStreamConnection;

final readonly class MessageBrokerFactory
{
    public function __construct(
        private array $config,
    ) {
    }

    public function create(string $driver): MessageBrokerInterface
    {
        return match ($driver) {
            'rabbitmq' => $this->createRabbitMq(),
            'kafka' => $this->createKafka(),
            'sqs' => $this->createSqs(),
            'in_memory' => new InMemoryAdapter(),
            default => throw new \InvalidArgumentException("Unsupported broker driver: {$driver}"),
        };
    }

    private function createRabbitMq(): RabbitMqAdapter
    {
        $config = $this->config['rabbitmq'] ?? [];

        $connection = new AMQPStreamConnection(
            $config['host'] ?? 'localhost',
            $config['port'] ?? 5672,
            $config['user'] ?? 'guest',
            $config['password'] ?? 'guest',
            $config['vhost'] ?? '/',
        );

        return new RabbitMqAdapter(
            connection: $connection,
            exchange: $config['exchange'] ?? 'events',
            exchangeType: $config['exchange_type'] ?? 'topic',
            prefetchCount: $config['prefetch_count'] ?? 10,
        );
    }

    private function createKafka(): KafkaAdapter
    {
        $config = $this->config['kafka'] ?? [];

        return new KafkaAdapter(
            brokers: $config['brokers'] ?? 'localhost:9092',
            groupId: $config['group_id'] ?? 'default',
            timeoutMs: $config['timeout_ms'] ?? 10000,
        );
    }

    private function createSqs(): SqsAdapter
    {
        $config = $this->config['sqs'] ?? [];

        $client = new SqsClient([
            'version' => 'latest',
            'region' => $config['region'] ?? 'us-east-1',
            'credentials' => [
                'key' => $config['key'] ?? '',
                'secret' => $config['secret'] ?? '',
            ],
        ]);

        return new SqsAdapter(
            client: $client,
            queueUrl: $config['queue_url'] ?? '',
            waitTimeSeconds: $config['wait_time_seconds'] ?? 20,
            visibilityTimeout: $config['visibility_timeout'] ?? 30,
        );
    }
}
```
