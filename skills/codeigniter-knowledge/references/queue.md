# Queue System in CodeIgniter 4

Queue handling with `codeigniter4/queue` package: jobs, workers, chained jobs, retry strategies, queue events, and DDD integration.

## Overview

CodeIgniter 4 does not include a built-in queue system. The official `codeigniter4/queue` package provides job queuing with database-backed persistence, priority handling, retry logic, and chained jobs.

### Installation

```bash
composer require codeigniter4/queue
php spark queue:table
php spark migrate
php spark queue:publish
```

## Creating Jobs

### Generate Job Class

```bash
php spark queue:job ProcessPayment
```

### Job Implementation

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;

final class ProcessPayment extends BaseJob
{
    protected int $retryAfter = 60;  // Retry delay in seconds
    protected int $tries = 3;        // Max attempts

    public function process(): bool
    {
        $orderId = $this->data['orderId'];
        $amount = $this->data['amount'];

        // Process payment via use case
        $useCase = service('processPaymentUseCase');
        $useCase->execute($orderId, $amount);

        return true;
    }
}
```

### Job Registration

```php
<?php

declare(strict_types=1);

// app/Config/Queue.php
namespace Config;

use App\Jobs\ProcessPayment;
use App\Jobs\SendNotification;
use App\Jobs\GenerateReport;
use CodeIgniter\Queue\Config\Queue as BaseQueue;

final class Queue extends BaseQueue
{
    public array $jobHandlers = [
        'process-payment'   => ProcessPayment::class,
        'send-notification' => SendNotification::class,
        'generate-report'   => GenerateReport::class,
    ];

    public string $defaultHandler = 'database';

    public array $database = [
        'dbGroup'   => 'default',
        'getShared' => true,
    ];
}
```

## Pushing Jobs to Queue

### Basic Push

```php
<?php

declare(strict_types=1);

// Push a job to the queue
$result = service('queue')->push('payments', 'process-payment', [
    'orderId' => $order->id()->value(),
    'amount'  => $order->total()->cents(),
]);

if (!$result->getStatus()) {
    throw new \RuntimeException('Failed to queue payment: ' . $result->getError());
}
```

### Chained Jobs

Execute jobs sequentially — next job runs only after previous succeeds:

```php
<?php

declare(strict_types=1);

service('queue')->chain(static function ($chain): void {
    $chain
        ->push('reports', 'generate-report', ['userId' => 123])
        ->push('notifications', 'send-notification', [
            'message' => 'Report ready',
            'userId'  => 123,
        ]);
});
```

## Running Queue Workers

### Spark Commands

```bash
# Run worker (persistent, with polling interval)
php spark queue:work payments -wait 10

# Run with job limit (for CRON)
php spark queue:work payments -max-jobs 50 --stop-when-empty

# Run with priority override
php spark queue:work payments -priority high,low

# Clear queue
php spark queue:clear payments

# Retry failed jobs
php spark queue:retry payments
```

### Supervisor Configuration

```ini
[program:ci4-queue-payments]
command=php /var/www/spark queue:work payments -wait 10
autostart=true
autorestart=true
numprocs=2
user=www-data
redirect_stderr=true
stdout_logfile=/var/log/ci4-queue-payments.log
```

## Queue Events

The `codeigniter4/queue` package provides lifecycle events:

### Job Events

| Event Constant | When Fired |
|---------------|------------|
| `QueueEventManager::JOB_PUSHED` | Job added to queue |
| `QueueEventManager::JOB_PUSH_FAILED` | Push attempt failed |
| `QueueEventManager::JOB_PROCESSING_STARTED` | Worker begins processing |
| `QueueEventManager::JOB_PROCESSING_COMPLETED` | Job completed successfully |
| `QueueEventManager::JOB_FAILED` | Job failed after all retries |

### Worker Events

| Event Constant | When Fired |
|---------------|------------|
| `QueueEventManager::WORKER_STARTED` | Worker begins |
| `QueueEventManager::WORKER_STOPPED` | Worker halts |

### Listening to Queue Events

```php
<?php

declare(strict_types=1);

// app/Config/Events.php
use CodeIgniter\Events\Events;
use CodeIgniter\Queue\Events\QueueEvent;
use CodeIgniter\Queue\Events\QueueEventManager;

Events::on(QueueEventManager::JOB_PROCESSING_COMPLETED, static function (QueueEvent $event): void {
    service('logger')->info('Job completed', [
        'job'  => $event->getJobClass(),
        'time' => $event->getProcessingTime(),
    ]);
});

Events::on(QueueEventManager::JOB_FAILED, static function (QueueEvent $event): void {
    service('logger')->error('Job failed', [
        'job'      => $event->getJobClass(),
        'error'    => $event->getExceptionMessage(),
        'attempts' => $event->getAttempts(),
    ]);
});

Events::on(QueueEventManager::WORKER_STOPPED, static function (QueueEvent $event): void {
    service('logger')->warning('Queue worker stopped', [
        'queue'  => $event->getQueue(),
        'reason' => $event->getMetadata('stopReason'),
    ]);
});
```

## DDD Integration

### Pattern: Domain Events to Queue Jobs

Domain events should be dispatched synchronously. Infrastructure listeners decide which events need async processing and push them to the queue.

**Bad: Queue in Domain**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Entity;

final class Order
{
    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        // VIOLATION: Infrastructure concern in Domain
        service('queue')->push('notifications', 'send-notification', [
            'orderId' => $this->id->value(),
        ]);
    }
}
```

**Good: Domain event into Infrastructure listener into Queue**
```php
<?php

declare(strict_types=1);

// Domain: pure event
namespace App\Domain\Order\Event;

final readonly class OrderConfirmed
{
    public function __construct(
        public OrderId $orderId,
    ) {}
}
```

```php
<?php

declare(strict_types=1);

// Infrastructure: listener pushes to queue
// app/Config/Events.php
use CodeIgniter\Events\Events;

Events::on('order.confirmed', static function (object $event): void {
    service('queue')->push('notifications', 'send-notification', [
        'orderId' => $event->orderId->value(),
        'type'    => 'order_confirmation',
    ]);
});
```

```php
<?php

declare(strict_types=1);

// Infrastructure: job delegates to UseCase
namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;

final class SendNotification extends BaseJob
{
    protected int $retryAfter = 30;
    protected int $tries = 3;

    public function process(): bool
    {
        $useCase = service('sendOrderNotificationUseCase');
        $useCase->execute($this->data['orderId'], $this->data['type']);

        return true;
    }
}
```

### Queue Service Registration

```php
<?php

declare(strict_types=1);

// app/Config/Services.php
namespace Config;

use CodeIgniter\Config\BaseService;

final class Services extends BaseService
{
    public static function processPaymentUseCase(bool $getShared = true): \App\Application\Payment\ProcessPaymentUseCase
    {
        if ($getShared) {
            return static::getSharedInstance('processPaymentUseCase');
        }

        return new \App\Application\Payment\ProcessPaymentUseCase(
            service('paymentGateway'),
            service('orderRepository'),
            service('eventDispatcher'),
        );
    }
}
```

## Resilience Patterns

### Job with Error Handling

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;
use Psr\Log\LoggerInterface;

final class ProcessPayment extends BaseJob
{
    protected int $retryAfter = 60;
    protected int $tries = 3;

    public function process(): bool
    {
        $logger = service('logger');

        try {
            $useCase = service('processPaymentUseCase');
            $useCase->execute($this->data['orderId'], $this->data['amount']);

            $logger->info('Payment processed', ['orderId' => $this->data['orderId']]);

            return true;
        } catch (\RuntimeException $e) {
            $logger->error('Payment processing failed', [
                'orderId' => $this->data['orderId'],
                'error'   => $e->getMessage(),
                'attempt' => $this->data['_attempt'] ?? 1,
            ]);

            throw $e; // Re-throw to trigger retry
        }
    }
}
```

### Database Transactions in Jobs

```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;

final class ProcessOrder extends BaseJob
{
    protected int $retryAfter = 30;
    protected int $tries = 2;

    public function process(): bool
    {
        $db = db_connect();
        $db->transStrict(false);
        $db->transBegin();

        try {
            $useCase = service('processOrderUseCase');
            $useCase->execute($this->data['orderId']);

            $db->transCommit();

            return true;
        } catch (\Throwable $e) {
            $db->transRollback();

            throw $e;
        }
    }
}
```

## Detection Patterns

```bash
# Queue in Domain layer (VIOLATION)
Grep: "service\('queue'\)" --glob "**/Domain/**/*.php"
Grep: "use CodeIgniter\\Queue" --glob "**/Domain/**/*.php"

# Queue in Application layer (VIOLATION)
Grep: "service\('queue'\)" --glob "**/Application/**/*.php"

# Jobs exist
Glob: app/Jobs/*.php

# Job handlers registered
Grep: "jobHandlers" --glob "app/Config/Queue.php"

# Jobs have retry configuration
Grep: "retryAfter|\\$tries" --glob "app/Jobs/**/*.php" --output_mode count

# Queue events monitored
Grep: "QueueEventManager" --glob "app/Config/Events.php" --output_mode count
```

## Summary Table

| Aspect | DDD Layer | CI4 Component | Integration Pattern |
|--------|-----------|--------------|---------------------|
| Queue Push | Infrastructure | `service('queue')->push()` | Event listener pushes jobs |
| Job Handler | Infrastructure | `BaseJob` subclass | Job delegates to UseCase |
| Job Config | Infrastructure | `Config\Queue` | `$jobHandlers` array |
| Retry Strategy | Infrastructure | `$retryAfter`, `$tries` | Per-job configuration |
| Queue Events | Infrastructure | `QueueEventManager` | Logging, monitoring listeners |
| Domain Events | Domain | Pure PHP classes | Entity collects, UseCase dispatches |
| Worker | Infrastructure | `spark queue:work` | Supervisor for production |
| Chained Jobs | Infrastructure | `service('queue')->chain()` | Sequential job execution |
