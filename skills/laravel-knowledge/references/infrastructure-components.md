# Laravel Infrastructure Components

Cache, HTTP Client, Rate Limiting, Task Scheduling, and Locks with DDD alignment.

## Cache

PSR-16 compatible caching with multiple drivers, tags, and atomic locks.

**Detection:**
```bash
# Cache usage
Grep: "Cache::|CacheInterface|CacheManager" --glob "src/**/*.php"
Grep: "cache\\(" --glob "src/**/*.php"

# Cache in Domain layer — violation
Grep: "use Illuminate\\Support\\Facades\\Cache|use Illuminate\\Cache" --glob "**/Domain/**/*.php"
Grep: "cache\\(" --glob "**/Domain/**/*.php"
```

**Bad — Cache facade in Domain:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Catalog\Service;

use Illuminate\Support\Facades\Cache;

// VIOLATION: Infrastructure dependency in Domain
final readonly class ProductPriceService
{
    public function getPrice(string $productId): int
    {
        return Cache::remember("price:{$productId}", 3600, fn () => $this->calculate($productId));
    }
}
```

**Good — Domain port + Infrastructure adapter:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Catalog\Service;

// Domain port
interface PriceCacheInterface
{
    public function get(string $productId): ?int;
    public function set(string $productId, int $priceCents, int $ttl = 3600): void;
    public function forget(string $productId): void;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use App\Domain\Catalog\Service\PriceCacheInterface;
use Illuminate\Cache\CacheManager;

final readonly class LaravelPriceCache implements PriceCacheInterface
{
    public function __construct(
        private CacheManager $cache,
    ) {}

    public function get(string $productId): ?int
    {
        return $this->cache->store('redis')->get("price:{$productId}");
    }

    public function set(string $productId, int $priceCents, int $ttl = 3600): void
    {
        $this->cache->store('redis')->put("price:{$productId}", $priceCents, $ttl);
    }

    public function forget(string $productId): void
    {
        $this->cache->store('redis')->forget("price:{$productId}");
    }
}
```

**Cache tags for aggregate invalidation:**
```php
// Store with tags
Cache::tags(['orders', "customer:{$customerId}"])->put("order:{$orderId}", $data, 3600);

// Flush by tag (invalidate all customer's cached orders)
Cache::tags(["customer:{$customerId}"])->flush();
```

**Stale-While-Revalidate (Laravel 12):**
```php
// Fresh for 5 seconds, stale for 10 — background refresh
$value = Cache::flexible('users', [5, 10], function () {
    return DB::table('users')->get();
});
```

## Atomic Locks (Distributed Concurrency)

Protect aggregate operations from concurrent modification.

**Detection:**
```bash
# Lock usage
Grep: "Cache::lock|->lock\\(" --glob "src/**/*.php"
Grep: "withoutOverlapping" --glob "src/**/*.php"
```

**DDD use case — aggregate concurrency protection:**
```php
<?php

declare(strict_types=1);

namespace App\Application\Order\UseCase;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use Illuminate\Cache\CacheManager;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private CacheManager $cache,
    ) {}

    public function execute(ConfirmOrderCommand $command): void
    {
        $lock = $this->cache->lock(
            name: "order:{$command->orderId->value()}",
            seconds: 30,
        );

        if (!$lock->get()) {
            throw new OrderAlreadyBeingProcessedException($command->orderId);
        }

        try {
            $order = $this->orders->findById($command->orderId);
            $order->confirm();
            $this->orders->save($order);
        } finally {
            $lock->release();
        }
    }
}
```

**Auto-release with closure:**
```php
Cache::lock('processing-order:' . $orderId, 30)->get(function () use ($orderId) {
    // Lock auto-released after closure completes or times out
    $this->processOrder($orderId);
});
```

## HTTP Client

Infrastructure adapters for external API integration.

**Detection:**
```bash
# HTTP Client usage
Grep: "Http::|HttpClient" --glob "src/**/*.php"
Grep: "use Illuminate\\Support\\Facades\\Http" --glob "src/**/*.php"

# Direct HTTP in Domain — violation
Grep: "Http::|curl_|file_get_contents\\(" --glob "**/Domain/**/*.php"
```

**DDD adapter for external API:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Payment\Port;

// Domain port
interface PaymentGatewayInterface
{
    public function charge(PaymentId $id, Money $amount, CardToken $token): PaymentResult;
    public function refund(PaymentId $id, Money $amount): RefundResult;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Payment;

use App\Domain\Payment\Port\PaymentGatewayInterface;
use App\Domain\Payment\ValueObject\CardToken;
use App\Domain\Payment\ValueObject\Money;
use App\Domain\Payment\ValueObject\PaymentId;
use App\Domain\Payment\ValueObject\PaymentResult;
use App\Domain\Payment\ValueObject\RefundResult;
use Illuminate\Support\Facades\Http;

final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private string $apiKey,
    ) {}

    public function charge(PaymentId $id, Money $amount, CardToken $token): PaymentResult
    {
        $response = Http::withToken($this->apiKey)
            ->retry(3, 100, throw: false)
            ->timeout(10)
            ->post('https://api.stripe.com/v1/charges', [
                'amount' => $amount->cents(),
                'currency' => $amount->currency()->value,
                'source' => $token->value,
                'idempotency_key' => $id->value(),
            ]);

        $response->throw();

        return new PaymentResult(
            externalId: $response->json('id'),
            status: $response->json('status'),
        );
    }

    public function refund(PaymentId $id, Money $amount): RefundResult
    {
        $response = Http::withToken($this->apiKey)
            ->retry(2, 200)
            ->post('https://api.stripe.com/v1/refunds', [
                'charge' => $id->value(),
                'amount' => $amount->cents(),
            ])
            ->throw();

        return new RefundResult($response->json('id'));
    }
}
```

**Concurrent requests with pooling:**
```php
use Illuminate\Http\Client\Pool;
use Illuminate\Support\Facades\Http;

$responses = Http::pool(fn (Pool $pool) => [
    $pool->as('inventory')->get("https://api.warehouse.com/stock/{$productId}"),
    $pool->as('pricing')->get("https://api.pricing.com/price/{$productId}"),
    $pool->as('shipping')->get("https://api.shipping.com/estimate/{$productId}"),
], concurrency: 3);
```

**Macros for reusable clients:**
```php
// In AppServiceProvider::boot()
Http::macro('stripe', fn () => Http::withToken(config('services.stripe.key'))
    ->baseUrl('https://api.stripe.com/v1')
    ->retry(3, 100)
    ->timeout(10)
);

// Usage
$response = Http::stripe()->post('/charges', $data);
```

## Rate Limiting

API rate limiting with multiple strategies.

**Detection:**
```bash
# Rate limiter usage
Grep: "RateLimiter::|throttle" --glob "src/**/*.php"
Grep: "rate_limiter" --glob "**/config/**/*.php"
```

**Named rate limiters:**
```php
// In AppServiceProvider::boot()
use Illuminate\Cache\RateLimiting\Limit;
use Illuminate\Support\Facades\RateLimiter;

RateLimiter::for('api', function ($request) {
    return $request->user()
        ? Limit::perMinute(1000)->by($request->user()->id)
        : Limit::perMinute(60)->by($request->ip());
});

RateLimiter::for('uploads', function ($request) {
    return $request->user()->isPremium()
        ? Limit::none()
        : Limit::perDay(10)->by($request->user()->id);
});
```

**Apply via route middleware:**
```php
Route::middleware('throttle:api')->group(function () {
    Route::get('/orders', ListOrdersController::class);
});

Route::middleware('throttle:uploads')->group(function () {
    Route::post('/imports', ImportDataController::class);
});
```

**Manual rate limiting in service:**
```php
use Illuminate\Support\Facades\RateLimiter;

$executed = RateLimiter::attempt(
    key: 'send-email:' . $userId,
    maxAttempts: 5,
    callback: fn () => $this->mailer->send($email),
    decaySeconds: 60,
);

if (!$executed) {
    throw new TooManyRequestsException('Email rate limit exceeded');
}
```

## Task Scheduling

Scheduled domain operations with distributed locking.

**Detection:**
```bash
# Scheduled tasks
Grep: "Schedule::|->schedule\\(" --glob "**/console.php"
Grep: "Schedule::" --glob "**/Kernel.php"
Grep: "onOneServer|withoutOverlapping" --glob "**/console.php"
```

**Scheduled domain operations:**
```php
// routes/console.php
use Illuminate\Support\Facades\Schedule;

Schedule::job(new GenerateDailyReportJob())
    ->dailyAt('06:00')
    ->timezone('UTC')
    ->onOneServer()
    ->withoutOverlapping();

Schedule::job(new ProcessPendingPaymentsJob())
    ->everyFiveMinutes()
    ->onOneServer();

Schedule::job(new CleanupExpiredOrdersJob())
    ->daily()
    ->onOneServer()
    ->onSuccess(fn () => Log::info('Expired orders cleaned'))
    ->onFailure(fn () => Log::critical('Cleanup failed'));
```

**Invokable class for testable scheduled tasks:**
```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Console;

use App\Application\Order\UseCase\CleanupExpiredOrdersUseCase;

final readonly class CleanupExpiredOrdersJob
{
    public function __construct(
        private CleanupExpiredOrdersUseCase $useCase,
    ) {}

    public function __invoke(): void
    {
        $this->useCase->execute();
    }
}
```

## Summary

| Component | DDD Layer | Interface Location | Implementation |
|-----------|-----------|-------------------|----------------|
| Cache | Infrastructure | Domain port (`PriceCacheInterface`) | `LaravelPriceCache` in Infrastructure |
| Locks | Application | `CacheManager::lock()` in Application | Redis/Database lock driver |
| HTTP Client | Infrastructure | Domain port (`PaymentGatewayInterface`) | Adapter with `Http::` macro in Infrastructure |
| Rate Limiter | Infrastructure | Route middleware or `RateLimiter::attempt()` | Named limiters in `AppServiceProvider` |
| Scheduler | Infrastructure | `routes/console.php` or invokable class | `onOneServer()` for distributed locking |
