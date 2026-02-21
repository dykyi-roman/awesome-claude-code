# Queue System in Yii3

yiisoft/yii-queue message handling, channels, push/consume/failure middleware pipelines, console commands, and DDD integration.

## Queue Architecture (yiisoft/yii-queue)

### Core Components

| Component | Description |
|-----------|-------------|
| `MessageInterface` | Task payload (or use default `Message` class) |
| Handler | Callable that processes queued messages |
| `QueueInterface` | Push messages, run/listen |
| Adapter | Transport backend (AMQP, Redis, Db, sync) |
| `QueueProviderInterface` | Manage multiple named queue channels |
| Middleware | Push, Consume, and Failure pipelines |

### Message and Handler

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Message;

use Yiisoft\Queue\Message\Message;

$message = new Message('order.confirm', ['orderId' => $orderId->value]);
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Handler;

use Domain\Order\ValueObject\OrderId;
use Application\Order\UseCase\ConfirmOrderUseCase;
use Yiisoft\Queue\Message\MessageInterface;

final readonly class ConfirmOrderHandler
{
    public function __construct(
        private ConfirmOrderUseCase $useCase,
    ) {}

    public function __invoke(MessageInterface $message): void
    {
        /** @var array{orderId: string} $data */
        $data = $message->getData();
        $this->useCase->execute(new OrderId($data['orderId']));
    }
}
```

### Pushing to Queue

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Listener;

use Domain\Order\Event\OrderCreated;
use Yiisoft\Queue\Message\Message;
use Yiisoft\Queue\QueueInterface;

final readonly class OrderCreatedQueueListener
{
    public function __construct(
        private QueueInterface $queue,
    ) {}

    public function __invoke(OrderCreated $event): void
    {
        $this->queue->push(
            new Message('notification.order-created', [
                'orderId' => $event->orderId,
                'customerId' => $event->customerId,
            ]),
        );
    }
}
```

## Queue Channels (QueueProviderInterface)

| Provider | Description |
|----------|-------------|
| `AdapterFactoryQueueProvider` | Create queues from adapter factories |
| `PrototypeQueueProvider` | Create queues from a prototype queue instance |
| `CompositeQueueProvider` | Combine multiple providers into one |

One channel per bounded context (e.g., `orders`, `notifications`, `payments`).

```php
<?php

declare(strict_types=1);

use Yiisoft\Queue\Provider\AdapterFactoryQueueProvider;
use Yiisoft\Queue\Provider\CompositeQueueProvider;
use Yiisoft\Queue\Provider\QueueProviderInterface;

$provider = new CompositeQueueProvider(
    new AdapterFactoryQueueProvider($factory, ['orders', 'notifications']),
);

$ordersQueue = $provider->get('orders');
$ordersQueue->push($message);
```

## Middleware Pipelines

### Push Middleware (before queuing)

Modify messages before they enter the queue: add metadata, correlation IDs, timestamps.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Middleware;

use Yiisoft\Queue\Middleware\Push\PushMiddlewareInterface;
use Yiisoft\Queue\Middleware\Push\PushRequest;

final readonly class AddCorrelationIdMiddleware implements PushMiddlewareInterface
{
    public function processPush(PushRequest $request, callable $next): PushRequest
    {
        $message = $request->getMessage()->withMetadata(
            array_merge($request->getMessage()->getMetadata(), [
                'correlationId' => bin2hex(random_bytes(16)),
                'timestamp' => (new \DateTimeImmutable())->format('c'),
            ]),
        );

        return $next(new PushRequest($message, $request->getAdapter()));
    }
}
```

### Consume Middleware (during processing)

Wrap handler execution with logging, tracing, transaction management.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Middleware;

use Psr\Log\LoggerInterface;
use Yiisoft\Queue\Middleware\Consume\ConsumeMiddlewareInterface;
use Yiisoft\Queue\Middleware\Consume\ConsumeRequest;

final readonly class LoggingConsumeMiddleware implements ConsumeMiddlewareInterface
{
    public function __construct(
        private LoggerInterface $logger,
    ) {}

    public function processConsume(ConsumeRequest $request, callable $next): ConsumeRequest
    {
        $this->logger->info('Processing message', [
            'handler' => $request->getMessage()->getHandlerName(),
        ]);

        try {
            return $next($request);
        } catch (\Throwable $e) {
            $this->logger->error('Message processing failed', [
                'error' => $e->getMessage(),
            ]);

            throw $e;
        }
    }
}
```

### Failure Middleware (on exception)

Retry with delay, send to dead letter queue, log and alert.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Middleware;

use Yiisoft\Queue\Middleware\Failure\FailureMiddlewareInterface;
use Yiisoft\Queue\Middleware\Failure\FailureHandlingRequest;

final readonly class RetryFailureMiddleware implements FailureMiddlewareInterface
{
    private const int MAX_RETRIES = 3;

    public function processFailure(FailureHandlingRequest $request, callable $next): FailureHandlingRequest
    {
        $meta = $request->getMessage()->getMetadata();
        $attempt = ($meta['attempt'] ?? 0) + 1;

        if ($attempt <= self::MAX_RETRIES) {
            $message = $request->getMessage()->withMetadata(
                array_merge($meta, ['attempt' => $attempt]),
            );

            $request->getQueue()->push($message);

            return $request;
        }

        // Exceeded max retries -- pass to next failure handler (e.g., DLQ)
        return $next($request);
    }
}
```

## Console Commands

```bash
# Process all pending messages and exit
./yii queue:run

# Continuously listen for new messages
./yii queue:listen
```

## DDD Integration

### Domain Layer -- No Queue Dependency

Domain events are pure PHP objects. Domain does NOT know about queues. Infrastructure listeners push to queue.

**Bad: Queue in Domain**

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Yiisoft\Queue\QueueInterface;  // VIOLATION: Infrastructure in Domain

final class Order
{
    public function __construct(
        private readonly OrderId $id,
        private OrderStatus $status,
        private QueueInterface $queue,  // VIOLATION: Queue dependency in Domain
    ) {}

    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        // VIOLATION: Pushing to queue from Domain
        $this->queue->push(
            new Message('order.confirmed', ['orderId' => $this->id->value]),
        );
    }
}
```

**Good: Infrastructure listener pushes to queue**

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\Event\OrderConfirmed;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderStatus;
use Domain\Shared\Aggregate\AggregateRoot;

final class Order extends AggregateRoot
{
    public function __construct(
        private readonly OrderId $id,
        private OrderStatus $status,
    ) {}

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotConfirmOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
        $this->recordEvent(new OrderConfirmed($this->id->value));
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Listener;

use Domain\Order\Event\OrderConfirmed;
use Yiisoft\Queue\Message\Message;
use Yiisoft\Queue\QueueInterface;

final readonly class OrderConfirmedQueueListener
{
    public function __construct(
        private QueueInterface $queue,
    ) {}

    public function __invoke(OrderConfirmed $event): void
    {
        $this->queue->push(
            new Message('notification.order-confirmed', [
                'orderId' => $event->orderId,
            ]),
        );
    }
}
```

### Handler Delegates to UseCase

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Handler;

use Application\Notification\UseCase\SendConfirmationEmailUseCase;
use Domain\Order\ValueObject\OrderId;
use Yiisoft\Queue\Message\MessageInterface;

final readonly class SendConfirmationEmailHandler
{
    public function __construct(
        private SendConfirmationEmailUseCase $useCase,
    ) {}

    public function __invoke(MessageInterface $message): void
    {
        /** @var array{orderId: string} $data */
        $data = $message->getData();
        $this->useCase->execute(new OrderId($data['orderId']));
    }
}
```

## Detection Patterns

```bash
# Queue in Domain (MUST be zero)
Grep: "use Yiisoft\\Queue\\" --glob "**/Domain/**/*.php"
Grep: "QueueInterface" --glob "**/Domain/**/*.php"

# Queue in Application (should be minimal)
Grep: "use Yiisoft\\Queue\\" --glob "**/Application/**/*.php"

# Handler definitions
Grep: "MessageInterface" --glob "**/Infrastructure/Queue/**/*.php"
Glob: **/Infrastructure/Queue/Handler/*Handler.php

# Middleware definitions
Grep: "PushMiddlewareInterface\|ConsumeMiddlewareInterface\|FailureMiddlewareInterface" --glob "**/*.php"

# Queue configuration
Grep: "QueueInterface" --glob "config/**/*.php"
Glob: config/common/di/queue*.php

# Missing failure middleware
Grep: "FailureMiddlewareInterface" --glob "**/*.php" --output_mode count
```

## Summary Table

| Aspect | DDD Layer | Pattern |
|--------|-----------|---------|
| Message creation | Infrastructure | Push from event listener |
| Handler | Infrastructure | Delegates to UseCase |
| Retry/Failure | Infrastructure | Failure middleware pipeline |
| Domain Events | Domain | Pure PHP, no queue dependency |
| Queue Config | Infrastructure | `config/common/di/` |
| Channels | Infrastructure | One per bounded context |
