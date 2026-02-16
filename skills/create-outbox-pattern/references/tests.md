# Outbox Pattern Unit Tests

## OutboxMessageTest

**File:** `tests/Unit/Domain/Shared/Outbox/OutboxMessageTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Outbox;

use Domain\Shared\Outbox\OutboxMessage;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OutboxMessage::class)]
final class OutboxMessageTest extends TestCase
{
    public function testCreateCreatesUnprocessedMessage(): void
    {
        $message = OutboxMessage::create(
            id: 'msg-123',
            aggregateType: 'Order',
            aggregateId: 'order-456',
            eventType: 'order.placed',
            payload: ['order_id' => 'order-456']
        );

        $this->assertSame('msg-123', $message->id);
        $this->assertSame('Order', $message->aggregateType);
        $this->assertSame('order-456', $message->aggregateId);
        $this->assertSame('order.placed', $message->eventType);
        $this->assertFalse($message->isProcessed());
        $this->assertSame(0, $message->retryCount);
    }

    public function testPayloadAsArrayDecodesJson(): void
    {
        $payload = ['key' => 'value', 'nested' => ['a' => 1]];

        $message = OutboxMessage::create(
            id: 'msg-123',
            aggregateType: 'Test',
            aggregateId: 'test-1',
            eventType: 'test.event',
            payload: $payload
        );

        $this->assertSame($payload, $message->payloadAsArray());
    }

    public function testWithProcessedMarksAsProcessed(): void
    {
        $message = OutboxMessage::create(
            id: 'msg-123',
            aggregateType: 'Test',
            aggregateId: 'test-1',
            eventType: 'test.event',
            payload: []
        );

        $processed = $message->withProcessed();

        $this->assertFalse($message->isProcessed());
        $this->assertTrue($processed->isProcessed());
    }

    public function testWithRetryIncrementedIncrementsCount(): void
    {
        $message = OutboxMessage::create(
            id: 'msg-123',
            aggregateType: 'Test',
            aggregateId: 'test-1',
            eventType: 'test.event',
            payload: []
        );

        $retried = $message->withRetryIncremented();

        $this->assertSame(0, $message->retryCount);
        $this->assertSame(1, $retried->retryCount);
    }

    public function testIsPoisonedReturnsTrueWhenMaxRetriesExceeded(): void
    {
        $message = OutboxMessage::reconstitute(
            id: 'msg-123',
            aggregateType: 'Test',
            aggregateId: 'test-1',
            eventType: 'test.event',
            payload: '{}',
            createdAt: new \DateTimeImmutable(),
            correlationId: null,
            causationId: null,
            processedAt: null,
            retryCount: 5
        );

        $this->assertTrue($message->isPoisoned(5));
        $this->assertFalse($message->isPoisoned(6));
    }
}
```

---

## OutboxProcessorTest

**File:** `tests/Unit/Application/Shared/Outbox/OutboxProcessorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Shared\Outbox;

use Application\Shared\Outbox\OutboxProcessor;
use Application\Shared\Port\Output\DeadLetterRepositoryInterface;
use Application\Shared\Port\Output\MessagePublisherInterface;
use Domain\Shared\Outbox\OutboxMessage;
use Domain\Shared\Outbox\OutboxRepositoryInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(OutboxProcessor::class)]
final class OutboxProcessorTest extends TestCase
{
    public function testProcessesMessagesSuccessfully(): void
    {
        $message = OutboxMessage::create(
            id: 'msg-1',
            aggregateType: 'Order',
            aggregateId: 'order-123',
            eventType: 'order.placed',
            payload: ['order_id' => 'order-123']
        );

        $outbox = $this->createMock(OutboxRepositoryInterface::class);
        $outbox->method('findUnprocessed')->willReturn([$message]);
        $outbox->expects($this->once())->method('markAsProcessed')->with('msg-1');

        $publisher = $this->createMock(MessagePublisherInterface::class);
        $publisher->expects($this->once())->method('publish');

        $processor = new OutboxProcessor(
            $outbox,
            $publisher,
            $this->createMock(DeadLetterRepositoryInterface::class),
            new NullLogger()
        );

        $result = $processor->process(100);

        $this->assertSame(1, $result->processed);
        $this->assertSame(0, $result->failed);
        $this->assertSame(0, $result->deadLettered);
    }

    public function testRetriesFailedMessages(): void
    {
        $message = OutboxMessage::create(
            id: 'msg-1',
            aggregateType: 'Order',
            aggregateId: 'order-123',
            eventType: 'order.placed',
            payload: []
        );

        $outbox = $this->createMock(OutboxRepositoryInterface::class);
        $outbox->method('findUnprocessed')->willReturn([$message]);
        $outbox->expects($this->once())->method('incrementRetry')->with('msg-1');

        $publisher = $this->createMock(MessagePublisherInterface::class);
        $publisher->method('publish')->willThrowException(new \RuntimeException('Broker down'));

        $processor = new OutboxProcessor(
            $outbox,
            $publisher,
            $this->createMock(DeadLetterRepositoryInterface::class),
            new NullLogger()
        );

        $result = $processor->process(100);

        $this->assertSame(0, $result->processed);
        $this->assertSame(1, $result->failed);
    }

    public function testMovesToDeadLetterAfterMaxRetries(): void
    {
        $message = OutboxMessage::reconstitute(
            id: 'msg-1',
            aggregateType: 'Order',
            aggregateId: 'order-123',
            eventType: 'order.placed',
            payload: '{}',
            createdAt: new \DateTimeImmutable(),
            correlationId: null,
            causationId: null,
            processedAt: null,
            retryCount: 5
        );

        $outbox = $this->createMock(OutboxRepositoryInterface::class);
        $outbox->method('findUnprocessed')->willReturn([$message]);
        $outbox->expects($this->once())->method('delete')->with('msg-1');

        $publisher = $this->createMock(MessagePublisherInterface::class);
        $publisher->method('publish')->willThrowException(new \RuntimeException());

        $deadLetter = $this->createMock(DeadLetterRepositoryInterface::class);
        $deadLetter->expects($this->once())->method('store');

        $processor = new OutboxProcessor($outbox, $publisher, $deadLetter, new NullLogger());

        $result = $processor->process(100);

        $this->assertSame(0, $result->processed);
        $this->assertSame(0, $result->failed);
        $this->assertSame(1, $result->deadLettered);
    }
}
```
