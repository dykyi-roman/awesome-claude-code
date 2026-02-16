# Message Broker Adapter Examples

Real-world usage examples and unit tests for message broker adapters.

---

## Example 1: Order Event Publishing

### Order Domain Event

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

final readonly class OrderCreated
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public float $total,
        public \DateTimeImmutable $occurredAt,
    ) {
    }

    public function toArray(): array
    {
        return [
            'order_id' => $this->orderId,
            'customer_id' => $this->customerId,
            'total' => $this->total,
            'occurred_at' => $this->occurredAt->format(\DateTimeInterface::ATOM),
        ];
    }
}
```

### UseCase with Event Publishing

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase\CreateOrder;

use Domain\Order\Order;
use Domain\Order\OrderId;
use Domain\Order\OrderRepositoryInterface;
use Domain\Order\Event\OrderCreated;
use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private MessageBrokerInterface $broker,
    ) {
    }

    public function execute(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            OrderId::generate(),
            customerId: $command->customerId,
            items: $command->items,
        );

        $this->orders->save($order);

        $event = new OrderCreated(
            orderId: $order->id()->toString(),
            customerId: $command->customerId,
            total: $order->total(),
            occurredAt: new \DateTimeImmutable(),
        );

        $message = Message::create(
            body: json_encode($event->toArray(), JSON_THROW_ON_ERROR),
            routingKey: 'orders.created',
            headers: [
                'event_type' => 'OrderCreated',
                'aggregate_type' => 'Order',
                'aggregate_id' => $order->id()->toString(),
            ],
        );

        if ($command->correlationId !== null) {
            $message = $message->withCorrelationId($command->correlationId);
        }

        $this->broker->publish($message);

        return $order->id();
    }
}
```

---

## Example 2: Consumer Worker with Graceful Shutdown

### Console Command

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Console;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Psr\Log\LoggerInterface;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

final class ConsumeMessagesCommand extends Command
{
    private bool $shouldStop = false;

    public function __construct(
        private readonly MessageBrokerInterface $broker,
        private readonly MessageHandlerInterface $handler,
        private readonly LoggerInterface $logger,
    ) {
        parent::__construct();
    }

    protected function configure(): void
    {
        $this
            ->setName('messages:consume')
            ->setDescription('Consume messages from broker')
            ->addOption('queue', null, InputOption::VALUE_REQUIRED, 'Queue name', 'default');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        $queue = $input->getOption('queue');

        $this->setupSignalHandlers();

        $output->writeln("Starting consumer for queue: {$queue}");

        try {
            $this->broker->consume($queue, function (Message $message): void {
                if ($this->shouldStop) {
                    return;
                }

                try {
                    $this->handler->handle($message);
                    $this->broker->acknowledge($message);
                    $this->logger->info('Message processed', [
                        'message_id' => $message->id->value,
                        'routing_key' => $message->routingKey,
                    ]);
                } catch (\Throwable $e) {
                    $this->logger->error('Message processing failed', [
                        'message_id' => $message->id->value,
                        'error' => $e->getMessage(),
                    ]);
                    $this->broker->reject($message, requeue: true);
                }
            });
        } catch (\Throwable $e) {
            $output->writeln("Error: {$e->getMessage()}");
            return Command::FAILURE;
        }

        $output->writeln('Consumer stopped gracefully');
        return Command::SUCCESS;
    }

    private function setupSignalHandlers(): void
    {
        pcntl_async_signals(true);

        pcntl_signal(SIGTERM, function (): void {
            $this->shouldStop = true;
            $this->logger->info('Received SIGTERM, stopping consumer');
        });

        pcntl_signal(SIGINT, function (): void {
            $this->shouldStop = true;
            $this->logger->info('Received SIGINT, stopping consumer');
        });
    }
}
```

### Message Handler

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Messaging;

use Domain\Shared\Messaging\Message;
use Psr\Log\LoggerInterface;

interface MessageHandlerInterface
{
    public function handle(Message $message): void;
}

final readonly class DomainEventHandler implements MessageHandlerInterface
{
    public function __construct(
        private EventDispatcherInterface $dispatcher,
        private LoggerInterface $logger,
    ) {
    }

    public function handle(Message $message): void
    {
        $eventType = $message->getHeader('event_type');

        if ($eventType === null) {
            throw new \InvalidArgumentException('Message has no event_type header');
        }

        $payload = json_decode($message->body, true, 512, JSON_THROW_ON_ERROR);

        $event = $this->deserializeEvent($eventType, $payload);

        $this->logger->info('Dispatching domain event', [
            'event_type' => $eventType,
            'message_id' => $message->id->value,
            'correlation_id' => $message->correlationId,
        ]);

        $this->dispatcher->dispatch($event);
    }

    private function deserializeEvent(string $eventType, array $payload): object
    {
        $className = "Domain\\Event\\{$eventType}";

        if (!class_exists($className)) {
            throw new \InvalidArgumentException("Unknown event type: {$eventType}");
        }

        return $className::fromArray($payload);
    }
}
```

---

## Example 3: Broker Factory with Environment Config

### .env Configuration

```env
MESSAGE_BROKER_DRIVER=rabbitmq

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/
RABBITMQ_EXCHANGE=events
RABBITMQ_EXCHANGE_TYPE=topic
RABBITMQ_PREFETCH_COUNT=10

KAFKA_BROKERS=localhost:9092
KAFKA_GROUP_ID=app
KAFKA_TIMEOUT_MS=10000

AWS_SQS_REGION=us-east-1
AWS_SQS_KEY=your-key
AWS_SQS_SECRET=your-secret
AWS_SQS_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/123456789/my-queue
AWS_SQS_WAIT_TIME_SECONDS=20
AWS_SQS_VISIBILITY_TIMEOUT=30
```

### DI Configuration (Symfony)

```yaml
# config/services.yaml
parameters:
    message_broker.config:
        rabbitmq:
            host: '%env(RABBITMQ_HOST)%'
            port: '%env(int:RABBITMQ_PORT)%'
            user: '%env(RABBITMQ_USER)%'
            password: '%env(RABBITMQ_PASSWORD)%'
            vhost: '%env(RABBITMQ_VHOST)%'
            exchange: '%env(RABBITMQ_EXCHANGE)%'
            exchange_type: '%env(RABBITMQ_EXCHANGE_TYPE)%'
            prefetch_count: '%env(int:RABBITMQ_PREFETCH_COUNT)%'
        kafka:
            brokers: '%env(KAFKA_BROKERS)%'
            group_id: '%env(KAFKA_GROUP_ID)%'
            timeout_ms: '%env(int:KAFKA_TIMEOUT_MS)%'
        sqs:
            region: '%env(AWS_SQS_REGION)%'
            key: '%env(AWS_SQS_KEY)%'
            secret: '%env(AWS_SQS_SECRET)%'
            queue_url: '%env(AWS_SQS_QUEUE_URL)%'
            wait_time_seconds: '%env(int:AWS_SQS_WAIT_TIME_SECONDS)%'
            visibility_timeout: '%env(int:AWS_SQS_VISIBILITY_TIMEOUT)%'

services:
    Infrastructure\Messaging\MessageBrokerFactory:
        arguments:
            $config: '%message_broker.config%'

    Domain\Shared\Messaging\MessageBrokerInterface:
        factory: ['@Infrastructure\Messaging\MessageBrokerFactory', 'create']
        arguments:
            $driver: '%env(MESSAGE_BROKER_DRIVER)%'
```

---

## Example 4: Integration with Outbox Pattern

### OutboxProcessor with Message Broker

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Outbox;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageBrokerInterface;
use Domain\Shared\Outbox\OutboxMessage;
use Domain\Shared\Outbox\OutboxRepositoryInterface;
use Psr\Log\LoggerInterface;

final readonly class OutboxProcessor
{
    public function __construct(
        private OutboxRepositoryInterface $outbox,
        private MessageBrokerInterface $broker,
        private LoggerInterface $logger,
        private int $maxRetries = 3,
    ) {
    }

    public function process(int $batchSize = 100): int
    {
        $messages = $this->outbox->findUnprocessed($batchSize);
        $processed = 0;

        foreach ($messages as $outboxMessage) {
            try {
                $this->publishMessage($outboxMessage);
                $this->outbox->markAsProcessed($outboxMessage->id);
                $processed++;

                $this->logger->info('Outbox message published', [
                    'message_id' => $outboxMessage->id,
                    'event_type' => $outboxMessage->eventType,
                ]);
            } catch (\Throwable $e) {
                $this->handleFailure($outboxMessage, $e);
            }
        }

        return $processed;
    }

    private function publishMessage(OutboxMessage $outboxMessage): void
    {
        $message = Message::create(
            body: $outboxMessage->payload,
            routingKey: $this->buildRoutingKey($outboxMessage),
            headers: [
                'event_type' => $outboxMessage->eventType,
                'aggregate_type' => $outboxMessage->aggregateType,
                'aggregate_id' => $outboxMessage->aggregateId,
            ],
        );

        if ($outboxMessage->correlationId !== null) {
            $message = $message->withCorrelationId($outboxMessage->correlationId);
        }

        $this->broker->publish($message);
    }

    private function buildRoutingKey(OutboxMessage $message): string
    {
        $parts = [
            strtolower($message->aggregateType),
            strtolower(str_replace('\\', '.', $message->eventType)),
        ];

        return implode('.', $parts);
    }

    private function handleFailure(OutboxMessage $message, \Throwable $e): void
    {
        $this->logger->error('Outbox message publish failed', [
            'message_id' => $message->id,
            'error' => $e->getMessage(),
            'retry_count' => $message->retryCount,
        ]);

        if ($message->retryCount >= $this->maxRetries) {
            $this->logger->critical('Outbox message max retries exceeded', [
                'message_id' => $message->id,
            ]);
            $this->outbox->delete($message->id);
            return;
        }

        $this->outbox->incrementRetry($message->id);
    }
}
```

---

## Example 5: Unit Tests

### MessageTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Messaging;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Message::class)]
final class MessageTest extends TestCase
{
    public function testCreateGeneratesNewMessage(): void
    {
        $message = Message::create(
            body: '{"order_id": "123"}',
            routingKey: 'orders.created',
            headers: ['event_type' => 'OrderCreated'],
        );

        self::assertInstanceOf(MessageId::class, $message->id);
        self::assertSame('{"order_id": "123"}', $message->body);
        self::assertSame('orders.created', $message->routingKey);
        self::assertSame(['event_type' => 'OrderCreated'], $message->headers);
        self::assertInstanceOf(\DateTimeImmutable::class, $message->timestamp);
    }

    public function testWithHeaderAddsNewHeader(): void
    {
        $original = Message::create(
            body: 'test',
            headers: ['key1' => 'value1'],
        );

        $modified = $original->withHeader('key2', 'value2');

        self::assertSame(['key1' => 'value1'], $original->headers);
        self::assertSame(['key1' => 'value1', 'key2' => 'value2'], $modified->headers);
    }

    public function testWithCorrelationIdSetsCorrelationId(): void
    {
        $original = Message::create(body: 'test');
        $modified = $original->withCorrelationId('correlation-123');

        self::assertNull($original->correlationId);
        self::assertSame('correlation-123', $modified->correlationId);
    }

    public function testGetHeaderReturnsValue(): void
    {
        $message = Message::create(
            body: 'test',
            headers: ['key1' => 'value1'],
        );

        self::assertSame('value1', $message->getHeader('key1'));
        self::assertNull($message->getHeader('missing'));
        self::assertSame('default', $message->getHeader('missing', 'default'));
    }

    public function testHasHeaderChecksExistence(): void
    {
        $message = Message::create(
            body: 'test',
            headers: ['key1' => 'value1'],
        );

        self::assertTrue($message->hasHeader('key1'));
        self::assertFalse($message->hasHeader('missing'));
    }

    public function testConstructorThrowsOnEmptyBody(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Message body cannot be empty');

        new Message(
            id: MessageId::generate(),
            body: '',
        );
    }
}
```

### JsonMessageSerializerTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Messaging;

use Domain\Shared\Messaging\Message;
use Domain\Shared\Messaging\MessageId;
use Infrastructure\Messaging\JsonMessageSerializer;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(JsonMessageSerializer::class)]
final class JsonMessageSerializerTest extends TestCase
{
    private JsonMessageSerializer $serializer;

    protected function setUp(): void
    {
        $this->serializer = new JsonMessageSerializer();
    }

    public function testSerializeReturnsJsonString(): void
    {
        $message = new Message(
            id: MessageId::fromString('550e8400-e29b-41d4-a716-446655440000'),
            body: '{"order_id": "123"}',
            routingKey: 'orders.created',
            headers: ['event_type' => 'OrderCreated'],
            correlationId: 'correlation-123',
            contentType: 'application/json',
            timestamp: new \DateTimeImmutable('2025-01-01 12:00:00'),
        );

        $json = $this->serializer->serialize($message);

        $expected = [
            'id' => '550e8400-e29b-41d4-a716-446655440000',
            'body' => '{"order_id": "123"}',
            'routing_key' => 'orders.created',
            'headers' => ['event_type' => 'OrderCreated'],
            'correlation_id' => 'correlation-123',
            'content_type' => 'application/json',
            'timestamp' => '2025-01-01T12:00:00+00:00',
        ];

        self::assertJsonStringEqualsJsonString(json_encode($expected), $json);
    }

    public function testDeserializeReturnsMessage(): void
    {
        $json = json_encode([
            'id' => '550e8400-e29b-41d4-a716-446655440000',
            'body' => '{"order_id": "123"}',
            'routing_key' => 'orders.created',
            'headers' => ['event_type' => 'OrderCreated'],
            'correlation_id' => 'correlation-123',
            'content_type' => 'application/json',
            'timestamp' => '2025-01-01T12:00:00+00:00',
        ]);

        $message = $this->serializer->deserialize($json);

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $message->id->value);
        self::assertSame('{"order_id": "123"}', $message->body);
        self::assertSame('orders.created', $message->routingKey);
        self::assertSame(['event_type' => 'OrderCreated'], $message->headers);
        self::assertSame('correlation-123', $message->correlationId);
        self::assertSame('application/json', $message->contentType);
        self::assertSame('2025-01-01T12:00:00+00:00', $message->timestamp->format(\DateTimeInterface::ATOM));
    }

    public function testDeserializeThrowsOnInvalidJson(): void
    {
        $this->expectException(\JsonException::class);

        $this->serializer->deserialize('invalid json');
    }

    public function testDeserializeThrowsOnNonArrayJson(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Invalid JSON data');

        $this->serializer->deserialize('"string"');
    }
}
```

### InMemoryAdapterTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Messaging\InMemory;

use Domain\Shared\Messaging\Message;
use Infrastructure\Messaging\InMemory\InMemoryAdapter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(InMemoryAdapter::class)]
final class InMemoryAdapterTest extends TestCase
{
    private InMemoryAdapter $adapter;

    protected function setUp(): void
    {
        $this->adapter = new InMemoryAdapter();
    }

    public function testPublishStoresMessage(): void
    {
        $message = Message::create(body: 'test', routingKey: 'test.queue');

        $this->adapter->publish($message);

        $published = $this->adapter->getPublishedMessages();
        self::assertCount(1, $published);
        self::assertSame($message, $published[0]);
    }

    public function testConsumeCallsHandlerForEachMessage(): void
    {
        $message1 = Message::create(body: 'test1', routingKey: 'test.queue');
        $message2 = Message::create(body: 'test2', routingKey: 'test.queue');

        $this->adapter->publish($message1);
        $this->adapter->publish($message2);

        $received = [];
        $this->adapter->consume('test.queue', function (Message $msg) use (&$received): void {
            $received[] = $msg;
        });

        self::assertCount(2, $received);
        self::assertSame($message1, $received[0]);
        self::assertSame($message2, $received[1]);
    }

    public function testConsumeClearsQueue(): void
    {
        $message = Message::create(body: 'test', routingKey: 'test.queue');

        $this->adapter->publish($message);
        $this->adapter->consume('test.queue', fn () => null);

        self::assertEmpty($this->adapter->getQueueMessages('test.queue'));
    }

    public function testGetQueueMessagesReturnsMessagesForSpecificQueue(): void
    {
        $message1 = Message::create(body: 'test1', routingKey: 'queue1');
        $message2 = Message::create(body: 'test2', routingKey: 'queue2');

        $this->adapter->publish($message1);
        $this->adapter->publish($message2);

        $queue1Messages = $this->adapter->getQueueMessages('queue1');
        $queue2Messages = $this->adapter->getQueueMessages('queue2');

        self::assertCount(1, $queue1Messages);
        self::assertSame($message1, $queue1Messages[0]);
        self::assertCount(1, $queue2Messages);
        self::assertSame($message2, $queue2Messages[0]);
    }

    public function testClearRemovesAllMessages(): void
    {
        $message = Message::create(body: 'test', routingKey: 'test.queue');

        $this->adapter->publish($message);
        $this->adapter->clear();

        self::assertEmpty($this->adapter->getPublishedMessages());
        self::assertEmpty($this->adapter->getQueueMessages('test.queue'));
    }

    public function testAcknowledgeIsNoOp(): void
    {
        $message = Message::create(body: 'test');

        $this->adapter->acknowledge($message);

        $this->expectNotToPerformAssertions();
    }

    public function testRejectIsNoOp(): void
    {
        $message = Message::create(body: 'test');

        $this->adapter->reject($message, requeue: true);

        $this->expectNotToPerformAssertions();
    }
}
```

### MessageBrokerFactoryTest.php

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Messaging;

use Infrastructure\Messaging\InMemory\InMemoryAdapter;
use Infrastructure\Messaging\MessageBrokerFactory;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(MessageBrokerFactory::class)]
final class MessageBrokerFactoryTest extends TestCase
{
    public function testCreateInMemoryReturnsInMemoryAdapter(): void
    {
        $factory = new MessageBrokerFactory([]);

        $adapter = $factory->create('in_memory');

        self::assertInstanceOf(InMemoryAdapter::class, $adapter);
    }

    public function testCreateThrowsOnUnsupportedDriver(): void
    {
        $factory = new MessageBrokerFactory([]);

        $this->expectException(\InvalidArgumentException::class);
        $this->expectExceptionMessage('Unsupported broker driver: invalid');

        $factory->create('invalid');
    }
}
```
