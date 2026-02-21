# Queue System in No-Framework PHP

Message queues with standalone packages: `enqueue/enqueue`, `php-amqplib/php-amqplib`, custom workers, retry strategies, and DDD integration.

## Overview

No-framework PHP projects use standalone queue libraries for background job processing. Key options:

| Package | Transport | Use Case |
|---------|-----------|----------|
| `enqueue/enqueue` | AMQP, Redis, SQS, DB, FS | Universal queue abstraction |
| `php-amqplib/php-amqplib` | RabbitMQ | Direct RabbitMQ client |
| `enqueue/redis` | Redis | Redis-backed queues |
| Custom | Database | Simple queue with PDO |

```bash
# Enqueue with AMQP transport
composer require enqueue/amqp-bunny enqueue/enqueue

# Or direct RabbitMQ
composer require php-amqplib/php-amqplib
```

## Enqueue Setup

### Producer Configuration

```php
<?php

declare(strict_types=1);

// config/queue.php
use Enqueue\AmqpBunny\AmqpConnectionFactory;

return static function (): AmqpConnectionFactory {
    return new AmqpConnectionFactory([
        'host' => $_ENV['RABBITMQ_HOST'] ?? 'localhost',
        'port' => (int) ($_ENV['RABBITMQ_PORT'] ?? 5672),
        'user' => $_ENV['RABBITMQ_USER'] ?? 'guest',
        'pass' => $_ENV['RABBITMQ_PASS'] ?? 'guest',
        'vhost' => $_ENV['RABBITMQ_VHOST'] ?? '/',
    ]);
};
```

### Sending Messages

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue;

use Enqueue\AmqpBunny\AmqpConnectionFactory;
use Interop\Queue\Message;

final readonly class EnqueueProducer
{
    public function __construct(
        private AmqpConnectionFactory $factory,
    ) {}

    public function send(string $queue, array $payload): void
    {
        $context = $this->factory->createContext();
        $destination = $context->createQueue($queue);
        $message = $context->createMessage(
            json_encode($payload, JSON_THROW_ON_ERROR),
        );
        $message->setContentType('application/json');

        $context->createProducer()->send($destination, $message);
    }
}
```

### Consumer Worker

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue;

use Enqueue\AmqpBunny\AmqpConnectionFactory;
use Interop\Queue\Message;
use Psr\Log\LoggerInterface;

final readonly class EnqueueWorker
{
    public function __construct(
        private AmqpConnectionFactory $factory,
        private JobDispatcher $jobDispatcher,
        private LoggerInterface $logger,
    ) {}

    public function run(string $queueName, int $timeout = 10000): void
    {
        $context = $this->factory->createContext();
        $queue = $context->createQueue($queueName);
        $consumer = $context->createConsumer($queue);

        $this->logger->info('Worker started', ['queue' => $queueName]);

        while (true) {
            $message = $consumer->receive($timeout);

            if ($message === null) {
                continue;
            }

            try {
                $payload = json_decode($message->getBody(), true, 512, JSON_THROW_ON_ERROR);
                $this->jobDispatcher->dispatch($payload);
                $consumer->acknowledge($message);

                $this->logger->info('Job processed', ['queue' => $queueName]);
            } catch (\Throwable $e) {
                $consumer->reject($message, true); // Requeue
                $this->logger->error('Job failed', [
                    'queue' => $queueName,
                    'error' => $e->getMessage(),
                ]);
            }
        }
    }
}
```

## php-amqplib (Direct RabbitMQ)

### Producer

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\RabbitMQ;

use PhpAmqpLib\Connection\AMQPStreamConnection;
use PhpAmqpLib\Message\AMQPMessage;

final readonly class RabbitMQProducer
{
    public function __construct(
        private AMQPStreamConnection $connection,
    ) {}

    public function publish(string $queue, array $payload): void
    {
        $channel = $this->connection->channel();
        $channel->queue_declare($queue, false, true, false, false);

        $message = new AMQPMessage(
            json_encode($payload, JSON_THROW_ON_ERROR),
            [
                'content_type' => 'application/json',
                'delivery_mode' => AMQPMessage::DELIVERY_MODE_PERSISTENT,
            ],
        );

        $channel->basic_publish($message, '', $queue);
        $channel->close();
    }
}
```

## DDD Integration

### Domain Port: QueueInterface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Port;

interface QueueInterface
{
    public function push(string $queue, string $jobName, array $data): void;
}
```

### Infrastructure Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue;

use Application\Shared\Port\QueueInterface;

final readonly class EnqueueAdapter implements QueueInterface
{
    public function __construct(
        private EnqueueProducer $producer,
    ) {}

    public function push(string $queue, string $jobName, array $data): void
    {
        $this->producer->send($queue, [
            'job' => $jobName,
            'data' => $data,
            'timestamp' => time(),
        ]);
    }
}
```

### Pattern: Domain Events -> Queue

**Bad: Queue in Domain**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Infrastructure\Queue\EnqueueProducer; // VIOLATION

final class Order
{
    public function confirm(EnqueueProducer $producer): void // VIOLATION
    {
        $this->status = OrderStatus::Confirmed;
        $producer->send('notifications', ['orderId' => $this->id->value]); // VIOLATION
    }
}
```

**Good: Domain event -> Infrastructure listener -> Queue**
```php
<?php

declare(strict_types=1);

// Infrastructure listener registered in config/events.php
namespace Infrastructure\Listener;

use Application\Shared\Port\QueueInterface;
use Domain\Order\Event\OrderConfirmed;

final readonly class QueueOrderConfirmationNotification
{
    public function __construct(
        private QueueInterface $queue,
    ) {}

    public function __invoke(OrderConfirmed $event): void
    {
        $this->queue->push('notifications', 'send-order-confirmation', [
            'orderId' => $event->orderId->value,
            'total' => $event->total->cents,
        ]);
    }
}
```

## Job Dispatcher

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue;

use Psr\Container\ContainerInterface;
use Psr\Log\LoggerInterface;

final readonly class JobDispatcher
{
    /** @param array<string, class-string> $handlers */
    public function __construct(
        private ContainerInterface $container,
        private LoggerInterface $logger,
        private array $handlers,
    ) {}

    public function dispatch(array $payload): void
    {
        $jobName = $payload['job'] ?? throw new \RuntimeException('Missing job name');
        $handlerClass = $this->handlers[$jobName]
            ?? throw new \RuntimeException("No handler for job: {$jobName}");

        $handler = $this->container->get($handlerClass);
        $handler->handle($payload['data'] ?? []);

        $this->logger->info('Job handled', ['job' => $jobName]);
    }
}
```

## Job Handler

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Handler;

use Application\Order\UseCase\SendOrderNotificationUseCase;

final readonly class SendOrderConfirmationHandler
{
    public function __construct(
        private SendOrderNotificationUseCase $useCase,
    ) {}

    public function handle(array $data): void
    {
        $this->useCase->execute($data['orderId'], 'confirmation');
    }
}
```

## CLI Worker Entry Point

```php
<?php

declare(strict_types=1);

// bin/worker
require dirname(__DIR__) . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(dirname(__DIR__));
$dotenv->load();

$container = require dirname(__DIR__) . '/config/container.php';

$queueName = $argv[1] ?? 'default';
$worker = $container->get(Infrastructure\Queue\EnqueueWorker::class);
$worker->run($queueName);
```

## Supervisor Configuration

```ini
[program:app-worker-notifications]
command=php /var/www/bin/worker notifications
autostart=true
autorestart=true
numprocs=2
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/app-worker-notifications.log
```

## Detection Patterns

```bash
# Queue library in Domain (VIOLATION)
Grep: "use Enqueue|use PhpAmqpLib|use Interop\\Queue" --glob "**/Domain/**/*.php"
Grep: "QueueInterface|Producer" --glob "**/Domain/**/Entity/**/*.php"

# Queue in Application (should use port)
Grep: "use Enqueue|use PhpAmqpLib" --glob "**/Application/**/*.php"

# Good: Application port exists
Grep: "interface QueueInterface" --glob "**/Application/**/*.php"

# Good: Infrastructure adapter
Grep: "implements QueueInterface" --glob "**/Infrastructure/**/*.php"

# Worker entry point exists
Glob: bin/worker
Glob: bin/console

# Job handlers exist
Grep: "class.*Handler" --glob "**/Infrastructure/Queue/Handler/**/*.php"
```

## Summary Table

| Aspect | DDD Layer | Package | Integration Pattern |
|--------|-----------|---------|---------------------|
| Queue Port | Application: QueueInterface | N/A | Port interface |
| Queue Producer | Infrastructure | `enqueue/amqp-bunny` or `php-amqplib` | EnqueueAdapter |
| Queue Consumer | Infrastructure | `enqueue/amqp-bunny` | EnqueueWorker |
| Job Dispatcher | Infrastructure | PSR-11 container | Routes job names to handlers |
| Job Handlers | Infrastructure | Custom classes | Delegate to UseCases |
| Domain Events | Domain | Pure PHP | Entity collects, UseCase dispatches |
| Event->Queue | Infrastructure | Listener | QueueOrderConfirmationNotification |
| CLI Worker | Infrastructure | bin/worker script | Supervisor for production |
