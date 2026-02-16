# Idempotent Consumer Examples

Real-world integration examples for Idempotent Consumer pattern.

---

## 1. Payment Processing

### PaymentMessageHandler.php

```php
<?php

declare(strict_types=1);

namespace Application\Payment\Handler;

use Application\Shared\Idempotency\IdempotencyStoreInterface;
use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Payment\PaymentId;
use Domain\Payment\PaymentRepositoryInterface;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use Psr\Log\LoggerInterface;

final readonly class PaymentMessageHandler
{
    public function __construct(
        private PaymentRepositoryInterface $payments,
        private IdempotentConsumerMiddleware $idempotency,
        private LoggerInterface $logger,
    ) {}

    public function handle(PaymentMessage $message): void
    {
        $key = IdempotencyKey::fromMessage(
            $message->messageId(),
            self::class
        );

        $result = $this->idempotency->process(
            $key,
            fn () => $this->processPayment($message),
            new \DateTimeImmutable('+30 days')
        );

        match ($result->status) {
            ProcessingStatus::Processed => $this->logger->info(
                'Payment processed',
                ['paymentId' => $result->data, 'messageId' => $message->messageId()]
            ),
            ProcessingStatus::Duplicate => $this->logger->info(
                'Duplicate payment message skipped',
                ['messageId' => $message->messageId()]
            ),
            ProcessingStatus::Failed => $this->logger->error(
                'Payment processing failed',
                ['messageId' => $message->messageId(), 'error' => $result->error]
            ),
        };
    }

    private function processPayment(PaymentMessage $message): string
    {
        $payment = Payment::create(
            PaymentId::fromString($message->paymentId()),
            Money::fromCents($message->amountCents()),
            $message->customerId()
        );

        $this->payments->save($payment);

        return $payment->id()->toString();
    }
}
```

---

## 2. Event Subscriber with Idempotency

### OrderCreatedEventSubscriber.php

```php
<?php

declare(strict_types=1);

namespace Application\Inventory\EventSubscriber;

use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Inventory\InventoryService;
use Domain\Order\Event\OrderCreatedEvent;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use Psr\Log\LoggerInterface;

final readonly class OrderCreatedEventSubscriber
{
    public function __construct(
        private InventoryService $inventory,
        private IdempotentConsumerMiddleware $idempotency,
        private LoggerInterface $logger,
    ) {}

    public function __invoke(OrderCreatedEvent $event): void
    {
        $key = IdempotencyKey::fromMessage(
            $event->eventId,
            self::class
        );

        $result = $this->idempotency->process(
            $key,
            fn () => $this->reserveInventory($event)
        );

        if ($result->status === ProcessingStatus::Failed) {
            $this->logger->error(
                'Failed to reserve inventory for order',
                [
                    'orderId' => $event->orderId,
                    'eventId' => $event->eventId,
                    'error' => $result->error,
                ]
            );
            throw new \RuntimeException($result->error);
        }

        if ($result->status === ProcessingStatus::Duplicate) {
            $this->logger->info(
                'Inventory already reserved for order',
                ['orderId' => $event->orderId, 'eventId' => $event->eventId]
            );
        }
    }

    private function reserveInventory(OrderCreatedEvent $event): void
    {
        foreach ($event->items as $item) {
            $this->inventory->reserve(
                productId: $item['product_id'],
                quantity: $item['quantity'],
                orderId: $event->orderId
            );
        }
    }
}
```

---

## 3. Webhook Processing

### WebhookController.php

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Webhook\Stripe;

use Application\Payment\UseCase\ProcessStripeWebhook\ProcessStripeWebhookCommand;
use Application\Payment\UseCase\ProcessStripeWebhook\ProcessStripeWebhookHandler;
use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class StripeWebhookAction
{
    public function __construct(
        private ProcessStripeWebhookHandler $handler,
        private IdempotentConsumerMiddleware $idempotency,
        private StripeWebhookResponder $responder,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();
        $eventId = $body['id'] ?? '';

        if ($eventId === '') {
            return $this->responder->badRequest('Missing event ID');
        }

        $key = IdempotencyKey::fromMessage($eventId, 'stripe_webhook');

        $result = $this->idempotency->process(
            $key,
            function () use ($body) {
                $command = new ProcessStripeWebhookCommand(
                    eventId: $body['id'],
                    eventType: $body['type'],
                    payload: $body['data'] ?? []
                );

                return $this->handler->handle($command);
            },
            new \DateTimeImmutable('+14 days')
        );

        return match ($result->status) {
            ProcessingStatus::Processed => $this->responder->success(),
            ProcessingStatus::Duplicate => $this->responder->success(),
            ProcessingStatus::Failed => $this->responder->error($result->error),
        };
    }
}
```

---

## 4. RabbitMQ Consumer with Idempotency

### OrderMessageConsumer.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\RabbitMq\Consumer;

use Application\Order\UseCase\ProcessOrder\ProcessOrderCommand;
use Application\Order\UseCase\ProcessOrder\ProcessOrderHandler;
use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use PhpAmqpLib\Message\AMQPMessage;
use Psr\Log\LoggerInterface;

final readonly class OrderMessageConsumer
{
    public function __construct(
        private ProcessOrderHandler $handler,
        private IdempotentConsumerMiddleware $idempotency,
        private LoggerInterface $logger,
    ) {}

    public function consume(AMQPMessage $message): void
    {
        $data = json_decode($message->getBody(), true, 512, JSON_THROW_ON_ERROR);
        $messageId = $message->get('message_id') ?? $data['message_id'] ?? '';

        if ($messageId === '') {
            $this->logger->error('Message without ID rejected', ['body' => $data]);
            $message->nack(requeue: false);
            return;
        }

        $key = IdempotencyKey::fromMessage($messageId, 'order_consumer');

        $result = $this->idempotency->process(
            $key,
            function () use ($data) {
                $command = new ProcessOrderCommand(
                    orderId: $data['order_id'],
                    customerId: $data['customer_id'],
                    items: $data['items']
                );

                return $this->handler->handle($command);
            }
        );

        match ($result->status) {
            ProcessingStatus::Processed => $message->ack(),
            ProcessingStatus::Duplicate => $message->ack(),
            ProcessingStatus::Failed => $this->handleFailure($message, $result->error),
        };
    }

    private function handleFailure(AMQPMessage $message, ?string $error): void
    {
        $retryCount = (int) ($message->get('application_headers')['x-retry-count'] ?? 0);

        if ($retryCount >= 3) {
            $this->logger->error('Message moved to DLQ after 3 retries', ['error' => $error]);
            $message->nack(requeue: false);
            return;
        }

        $this->logger->warning('Message requeued for retry', [
            'error' => $error,
            'retryCount' => $retryCount,
        ]);

        $message->nack(requeue: true);
    }
}
```

---

## 5. Symfony Messenger Integration

### IdempotentMessageMiddleware.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Symfony\Middleware;

use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Domain\Shared\Idempotency\IdempotencyKey;
use Domain\Shared\Idempotency\ProcessingStatus;
use Infrastructure\Messaging\Symfony\Stamp\IdempotencyKeyStamp;
use Psr\Log\LoggerInterface;
use Symfony\Component\Messenger\Envelope;
use Symfony\Component\Messenger\Middleware\MiddlewareInterface;
use Symfony\Component\Messenger\Middleware\StackInterface;
use Symfony\Component\Messenger\Stamp\ReceivedStamp;

final readonly class IdempotentMessageMiddleware implements MiddlewareInterface
{
    public function __construct(
        private IdempotentConsumerMiddleware $idempotency,
        private LoggerInterface $logger,
    ) {}

    public function handle(Envelope $envelope, StackInterface $stack): Envelope
    {
        if ($envelope->last(ReceivedStamp::class) === null) {
            return $stack->next()->handle($envelope, $stack);
        }

        $stamp = $envelope->last(IdempotencyKeyStamp::class);

        if ($stamp === null) {
            $this->logger->warning('Message without IdempotencyKeyStamp', [
                'messageClass' => get_class($envelope->getMessage()),
            ]);
            return $stack->next()->handle($envelope, $stack);
        }

        $key = IdempotencyKey::fromMessage(
            $stamp->messageId(),
            $stamp->handlerName()
        );

        $result = $this->idempotency->process(
            $key,
            fn () => $stack->next()->handle($envelope, $stack)
        );

        if ($result->status === ProcessingStatus::Duplicate) {
            $this->logger->info('Duplicate message skipped', [
                'messageId' => $stamp->messageId(),
                'handler' => $stamp->handlerName(),
            ]);
        }

        return $envelope;
    }
}
```

### IdempotencyKeyStamp.php

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Symfony\Stamp;

use Symfony\Component\Messenger\Stamp\StampInterface;

final readonly class IdempotencyKeyStamp implements StampInterface
{
    public function __construct(
        private string $messageId,
        private string $handlerName,
    ) {}

    public function messageId(): string
    {
        return $this->messageId;
    }

    public function handlerName(): string
    {
        return $this->handlerName;
    }
}
```

---

## 6. DI Configuration

### Symfony services.yaml

```yaml
services:
  _defaults:
    autowire: true
    autoconfigure: true

  # Domain
  Domain\Shared\Idempotency\:
    resource: '../src/Domain/Shared/Idempotency/*'

  # Application
  Application\Shared\Idempotency\IdempotencyStoreInterface:
    alias: Infrastructure\Idempotency\DatabaseIdempotencyStore
    # Or use Redis:
    # alias: Infrastructure\Idempotency\RedisIdempotencyStore

  Application\Shared\Idempotency\IdempotentConsumerMiddleware:
    arguments:
      $store: '@Application\Shared\Idempotency\IdempotencyStoreInterface'

  # Infrastructure - Database
  Infrastructure\Idempotency\DatabaseIdempotencyStore:
    arguments:
      $connection: '@doctrine.dbal.default_connection'

  # Infrastructure - Redis
  Infrastructure\Idempotency\RedisIdempotencyStore:
    arguments:
      $redis: '@snc_redis.default'
      $prefix: 'idempotency:'

  # Console
  Infrastructure\Console\PurgeExpiredIdempotencyKeysCommand:
    tags: ['console.command']

  # Messaging
  Infrastructure\Messaging\Symfony\Middleware\IdempotentMessageMiddleware:
    tags:
      - { name: 'messenger.middleware', priority: 100 }
```

### Laravel app/Providers/IdempotencyServiceProvider.php

```php
<?php

declare(strict_types=1);

namespace App\Providers;

use Application\Shared\Idempotency\IdempotencyStoreInterface;
use Application\Shared\Idempotency\IdempotentConsumerMiddleware;
use Infrastructure\Idempotency\RedisIdempotencyStore;
use Illuminate\Support\ServiceProvider;

final class IdempotencyServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->singleton(IdempotencyStoreInterface::class, function ($app) {
            return new RedisIdempotencyStore(
                redis: $app->make('redis')->connection(),
                prefix: config('idempotency.prefix', 'idempotency:')
            );
        });

        $this->app->singleton(IdempotentConsumerMiddleware::class);
    }

    public function boot(): void
    {
        if ($this->app->runningInConsole()) {
            $this->commands([
                \Infrastructure\Console\PurgeExpiredIdempotencyKeysCommand::class,
            ]);
        }
    }
}
```

---

## 7. Cleanup Cron Job

### crontab

```bash
# Purge expired idempotency keys daily at 2 AM
0 2 * * * cd /var/www/app && php bin/console idempotency:purge-expired
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: idempotency-cleanup
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: my-app:latest
            command: ["php", "bin/console", "idempotency:purge-expired"]
          restartPolicy: OnFailure
```

---

## 8. Testing Integration

### Integration Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Application\Payment;

use Application\Payment\Handler\PaymentMessageHandler;
use Application\Payment\Message\PaymentMessage;
use Domain\Payment\PaymentRepositoryInterface;
use Tests\Integration\IntegrationTestCase;

final class PaymentIdempotencyTest extends IntegrationTestCase
{
    private PaymentMessageHandler $handler;
    private PaymentRepositoryInterface $payments;

    protected function setUp(): void
    {
        parent::setUp();

        $this->handler = $this->getContainer()->get(PaymentMessageHandler::class);
        $this->payments = $this->getContainer()->get(PaymentRepositoryInterface::class);
    }

    public function testDuplicateMessageDoesNotCreateDuplicatePayment(): void
    {
        $message = new PaymentMessage(
            messageId: 'msg-123',
            paymentId: 'pay-456',
            customerId: 'cus-789',
            amountCents: 10000
        );

        $this->handler->handle($message);
        $this->handler->handle($message);

        $payments = $this->payments->findByCustomerId('cus-789');

        self::assertCount(1, $payments);
    }

    public function testDifferentMessageIdsCreateSeparatePayments(): void
    {
        $message1 = new PaymentMessage(
            messageId: 'msg-123',
            paymentId: 'pay-456',
            customerId: 'cus-789',
            amountCents: 10000
        );

        $message2 = new PaymentMessage(
            messageId: 'msg-999',
            paymentId: 'pay-888',
            customerId: 'cus-789',
            amountCents: 20000
        );

        $this->handler->handle($message1);
        $this->handler->handle($message2);

        $payments = $this->payments->findByCustomerId('cus-789');

        self::assertCount(2, $payments);
    }
}
```

---

## Summary

All examples follow these principles:

1. **Deterministic keys** — messageId + handlerName
2. **Check before process** — always verify idempotency first
3. **Mark after success** — only mark processed after successful completion
4. **Handle duplicates gracefully** — log and acknowledge duplicates
5. **TTL management** — use appropriate TTL for each use case (payments = 30 days, events = 7 days)
6. **Failed message handling** — retry with limits, then DLQ
7. **Correlation** — preserve message IDs across all layers for traceability
