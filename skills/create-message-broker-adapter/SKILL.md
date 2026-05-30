---
name: create-message-broker-adapter
description: Generates Message Broker Adapter components for PHP 8.4. Creates unified broker interface with RabbitMQ, Kafka, SQS adapters, message serialization, and unit tests.
---

# Message Broker Adapter Generator

Creates unified message broker abstraction with adapter implementations for multiple broker technologies.

## When to Use

| Scenario | Example |
|----------|---------|
| Broker abstraction | Switch between RabbitMQ/Kafka/SQS without code changes |
| Multi-broker support | Different brokers for different bounded contexts |
| Testing isolation | InMemory adapter for tests |
| Migration path | Gradual migration from one broker to another |
| Vendor independence | Avoid lock-in to specific message broker |

## Component Characteristics

### MessageBrokerInterface
- Abstraction the application code depends on
- publish(Message): void
- consume(string queue, callable handler): void
- acknowledge(Message): void
- reject(Message, bool requeue): void

### Message
- Immutable value object
- Body (string), headers (array), routingKey, metadata
- Correlation ID and message ID
- Timestamp and content type

### MessageSerializerInterface
- Serialize/deserialize messages
- JSON implementation by default
- Extensible for Avro, Protobuf

### RabbitMqAdapter
- php-amqplib based
- Exchange and queue declaration
- Publish confirm mode
- Consumer with prefetch

### KafkaAdapter
- RdKafka based
- Topic partitioning
- Consumer groups
- Offset management

### SqsAdapter
- AWS SDK based
- FIFO and standard queues
- Long polling
- Visibility timeout

### InMemoryAdapter
- For testing only
- Tracks published messages
- Synchronous consumption

---

## Generation Process

### Step 1: Analyze Request

Determine:
- Which broker adapters needed (RabbitMQ, Kafka, SQS, or all)
- Queue/topic naming conventions
- Serialization format

### Step 2: Generate Core Components

1. **Types & Contracts**
   - `Message.php` — Immutable message value object
   - `MessageBrokerInterface.php` — Broker abstraction
   - `MessageSerializerInterface.php` — Serialization contract
   - `MessageId.php` — Message identity value object

2. **Broker Adapters**
   - `JsonMessageSerializer.php` — JSON serializer
   - `RabbitMq/RabbitMqAdapter.php` — RabbitMQ implementation
   - `Kafka/KafkaAdapter.php` — Kafka implementation
   - `Sqs/SqsAdapter.php` — AWS SQS implementation
   - `InMemory/InMemoryAdapter.php` — Testing adapter
   - `MessageBrokerFactory.php` — Config-based adapter factory

3. **Tests**
   - `MessageTest.php`
   - `JsonMessageSerializerTest.php`
   - `InMemoryAdapterTest.php`
   - `MessageBrokerFactoryTest.php`

---

## File Placement

| Component group | Path |
|-----------------|------|
| Types & Contracts | `src/{architecture-path}/Messaging/` |
| Serializer + Factory | `src/{architecture-path}/Messaging/` |
| Broker Adapters | `src/{architecture-path}/Messaging/{Broker}/` |
| Unit Tests | `tests/Unit/{architecture-path}/Messaging/` |

> `{architecture-path}` represents your project's architecture-specific folders. The broker abstraction typically lives with other shared messaging types; concrete broker adapters live at the integration boundary with each external broker. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `MessageBrokerInterface` | `MessageBrokerInterface` |
| Message VO | `Message` | `Message` |
| Adapter | `{Broker}Adapter` | `RabbitMqAdapter` |
| Serializer | `{Format}MessageSerializer` | `JsonMessageSerializer` |
| Factory | `MessageBrokerFactory` | `MessageBrokerFactory` |
| Test | `{ClassName}Test` | `RabbitMqAdapterTest` |

---

## Quick Template Reference

### MessageBrokerInterface

```php
interface MessageBrokerInterface
{
    public function publish(Message $message, string $routingKey = ''): void;
    public function consume(string $queue, callable $handler): void;
    public function acknowledge(Message $message): void;
    public function reject(Message $message, bool $requeue = false): void;
}
```

### Message

```php
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
    ) {}

    public static function create(string $body, string $routingKey = '', array $headers = []): self;
    public function withHeader(string $key, string $value): self;
    public function withCorrelationId(string $correlationId): self;
}
```

---

## Usage Example

```php
// Publish
$message = Message::create(
    body: json_encode(['order_id' => $orderId, 'total' => $total]),
    routingKey: 'orders.created'
);
$broker->publish($message);

// Consume
$broker->consume('order_processing', function (Message $message) use ($handler) {
    $handler->handle($message);
    $this->broker->acknowledge($message);
});
```

---

## DI Configuration

```yaml
Domain\Shared\Messaging\MessageBrokerInterface:
    factory: ['@Infrastructure\Messaging\MessageBrokerFactory', 'create']
    arguments:
        $driver: '%env(MESSAGE_BROKER_DRIVER)%'
```

---

## References

For complete PHP templates and test examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — Order event publishing example and unit tests
