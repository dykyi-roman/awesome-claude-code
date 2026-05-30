# Laravel Queues Advanced

Job middleware, batching, chaining, retry strategies, dead letter queue, Horizon, and CQRS patterns.

## Job Middleware

Custom middleware wraps cross-cutting concerns around job execution.

**Detection:**
```bash
# Job middleware usage
Grep: "function middleware\\(\\)" --glob "**/Jobs/**/*.php"
Grep: "WithoutOverlapping|RateLimited|ThrottlesExceptions" --glob "**/Jobs/**/*.php"

# Jobs without middleware (potential missing concurrency control)
Grep: "implements ShouldQueue" --glob "**/Jobs/**/*.php" --output_mode count
```

**Rate limiting middleware:**
```php
<?php

declare(strict_types=1);

namespace Middleware;

use Closure;
use Illuminate\Support\Facades\Redis;

final readonly class RateLimitedMiddleware
{
    public function __construct(
        private string $key,
        private int $maxAttempts = 1,
        private int $decaySeconds = 5,
    ) {}

    public function handle(object $job, Closure $next): void
    {
        Redis::throttle($this->key)
            ->block(0)
            ->allow($this->maxAttempts)
            ->every($this->decaySeconds)
            ->then(
                fn () => $next($job),
                fn () => $job->release($this->decaySeconds),
            );
    }
}
```

**Preventing job overlaps (aggregate concurrency):**
```php
<?php

declare(strict_types=1);

namespace Job;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\Middleware\WithoutOverlapping;

final class ProcessOrderPayment implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public function __construct(
        private readonly string $orderId,
    ) {}

    /** @return array<object> */
    public function middleware(): array
    {
        return [
            (new WithoutOverlapping($this->orderId))
                ->releaseAfter(60)
                ->expireAfter(180),
        ];
    }

    public function handle(ProcessPaymentUseCase $useCase): void
    {
        $useCase->execute(new ProcessPaymentCommand(
            orderId: new OrderId($this->orderId),
        ));
    }
}
```

## Retry and Backoff Strategies

```php
<?php

declare(strict_types=1);

namespace Job;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

final class SendOrderNotification implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public int $tries = 5;
    public int $maxExceptions = 3;
    public int $timeout = 120;
    public bool $failOnTimeout = true;

    /** @return array<int> */
    public function backoff(): array
    {
        return [1, 5, 10, 30, 60]; // Exponential backoff in seconds
    }

    public function retryUntil(): \DateTime
    {
        return now()->addMinutes(30);
    }

    public function handle(): void
    {
        // ...
    }
}
```

| Property | Default | Recommended | Description |
|----------|---------|-------------|-------------|
| `$tries` | 1 | 3-5 | Maximum retry attempts |
| `$maxExceptions` | - | 3 | Fail after N unhandled exceptions |
| `$timeout` | 60 | 120 | Seconds per attempt |
| `$backoff` | 0 | [1,5,10] | Delay between retries (array = exponential) |
| `$failOnTimeout` | false | true | Mark as failed on timeout |

## Failed Jobs / Dead Letter Queue

Failed jobs are stored in the `failed_jobs` table after exhausting retries.

```bash
# Console commands
php bin/artisan queue:failed           # List failed jobs
php bin/artisan queue:retry {id}       # Retry specific job
php bin/artisan queue:retry all        # Retry all failed jobs
php bin/artisan queue:forget {id}      # Delete a failed job
php bin/artisan queue:flush            # Delete all failed jobs
```

**Custom failure handling:**
```php
<?php

declare(strict_types=1);

namespace Job;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;
use Psr\Log\LoggerInterface;

final class ProcessPayment implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public int $tries = 3;

    public function __construct(
        private readonly string $orderId,
    ) {}

    public function handle(ProcessPaymentUseCase $useCase): void
    {
        $useCase->execute(new ProcessPaymentCommand(
            orderId: new OrderId($this->orderId),
        ));
    }

    public function failed(\Throwable $exception): void
    {
        app(LoggerInterface::class)->critical('Payment processing permanently failed', [
            'order_id' => $this->orderId,
            'error' => $exception->getMessage(),
        ]);
    }
}
```

**Global failed job handler:**
```php
// In AppServiceProvider::boot()
use Illuminate\Queue\Events\JobFailed;
use Illuminate\Support\Facades\Queue;

Queue::failing(function (JobFailed $event) {
    Log::critical('Job permanently failed', [
        'connection' => $event->connectionName,
        'job' => $event->job->getName(),
        'exception' => $event->exception->getMessage(),
    ]);
});
```

## Job Batching (Bulk Operations)

Process multiple jobs as a batch with progress tracking and failure handling.

```php
<?php

declare(strict_types=1);

namespace Job;

use Illuminate\Bus\Batchable;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

final class ProcessOrderLine implements ShouldQueue
{
    use Batchable, InteractsWithQueue, Queueable;

    public function __construct(
        private readonly string $orderLineId,
    ) {}

    public function handle(): void
    {
        if ($this->batch()?->cancelled()) {
            return;
        }

        // Process individual line
    }
}
```

**Dispatching a batch:**
```php
use Illuminate\Support\Facades\Bus;

$batch = Bus::batch(
    $order->lines()->map(
        fn (OrderLine $line) => new ProcessOrderLine($line->id()->value()),
    )->toArray(),
)
->then(fn (Batch $batch) => Log::info('All lines processed', ['batch' => $batch->id]))
->catch(fn (Batch $batch, \Throwable $e) => Log::error('Batch failed', ['error' => $e->getMessage()]))
->finally(fn (Batch $batch) => OrderBatchCompleted::dispatch($batch->id))
->onQueue('order-processing')
->dispatch();
```

## Job Chaining (Saga Pattern)

Execute jobs sequentially with automatic failure handling.

```php
use Illuminate\Support\Facades\Bus;

Bus::chain([
    new ValidateOrderJob($orderId),
    new ReserveInventoryJob($orderId),
    new ProcessPaymentJob($orderId),
    new SendConfirmationJob($orderId),
])
->onQueue('order-processing')
->catch(function (\Throwable $e) use ($orderId) {
    Log::error('Order chain failed', [
        'order_id' => $orderId,
        'error' => $e->getMessage(),
    ]);
    CompensateOrderJob::dispatch($orderId);
})
->dispatch();
```

## Unique Jobs (Idempotency)

Prevent duplicate job processing.

```php
<?php

declare(strict_types=1);

namespace Job;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldBeUnique;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

final class UpdateSearchIndex implements ShouldQueue, ShouldBeUnique
{
    use InteractsWithQueue, Queueable;

    public int $uniqueFor = 3600;

    public function __construct(
        private readonly string $productId,
    ) {}

    public function uniqueId(): string
    {
        return $this->productId;
    }

    public function handle(): void
    {
        // Index update — runs only once per product per hour
    }
}
```

| Interface | Lock Duration |
|-----------|--------------|
| `ShouldBeUnique` | Until job completes |
| `ShouldBeUniqueUntilProcessing` | Until processing starts (allows requeue) |

## Horizon (Production Monitoring)

```php
// config/horizon.php
'environments' => [
    'production' => [
        'supervisor-1' => [
            'connection' => 'redis',
            'queue' => ['default', 'order-processing', 'notifications'],
            'balance' => 'auto',
            'processes' => 10,
            'tries' => 3,
            'timeout' => 120,
            'nice' => 0,
        ],
    ],
],
```

**Supervisor config for Horizon:**
```ini
[program:horizon]
process_name=%(program_name)s
command=php /app/artisan horizon
autostart=true
autorestart=true
user=www-data
redirect_stderr=true
stdout_logfile=/app/storage/logs/horizon.log
stopwaitsecs=3600
```

## CQRS with Queues

**Command bus via queued jobs:**
```php
<?php

declare(strict_types=1);

namespace Job;

use Command\PlaceOrderCommand;
use UseCase\PlaceOrderUseCase;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

final class PlaceOrderJob implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public function __construct(
        private readonly PlaceOrderCommand $command,
    ) {}

    /** @return array<object> */
    public function middleware(): array
    {
        return [
            (new WithoutOverlapping($this->command->customerId->value()))
                ->releaseAfter(30),
        ];
    }

    public function handle(PlaceOrderUseCase $useCase): void
    {
        $useCase->execute($this->command);
    }
}
```

**Async domain event publishing:**
```php
<?php

declare(strict_types=1);

namespace Job;

use Event\OrderConfirmedEvent;
use Domain\EventDispatcherInterface;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Queue\InteractsWithQueue;

final class PublishDomainEvent implements ShouldQueue
{
    use InteractsWithQueue, Queueable;

    public int $tries = 3;

    public function __construct(
        private readonly object $domainEvent,
    ) {}

    public function handle(EventDispatcherInterface $dispatcher): void
    {
        $dispatcher->dispatch($this->domainEvent);
    }
}
```

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Concurrency | `WithoutOverlapping` middleware keyed by aggregate ID |
| Retry Strategy | 3-5 tries, exponential backoff `[1,5,10,30]`, `retryUntil()` for time-bound |
| Failed Jobs | Always implement `failed()` method; global `Queue::failing()` for alerts |
| Batching | Use `Bus::batch()` for bulk operations with progress tracking |
| Chaining | Use `Bus::chain()` for saga-like sequential workflows |
| Idempotency | `ShouldBeUnique` with `uniqueId()` keyed by entity ID |
| CQRS | Wrap Use Case commands in queued jobs; async domain events via jobs |
| Production | Horizon for monitoring, Supervisor for process management |
