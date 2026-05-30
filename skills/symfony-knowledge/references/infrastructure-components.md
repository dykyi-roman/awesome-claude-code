# Symfony Infrastructure Components

Cache, Lock, RateLimiter, HTTP Client, Serializer, and Scheduler patterns with DDD alignment.

## Cache

PSR-6/16 cache with pools, tags, and chain adapters.

**Detection:**
```bash
# Cache usage
Grep: "CacheInterface|CacheItemPoolInterface" --glob "src/**/*.php"
Grep: "TagAwareCacheInterface" --glob "src/**/*.php"

# Cache in Domain layer — violation
Grep: "use Symfony\\\\Component\\\\Cache|use Symfony\\\\Contracts\\\\Cache" --glob "**/Domain/**/*.php"
Grep: "CacheInterface" --glob "**/Domain/**/*.php"
```

**Bad — Symfony Cache in Domain layer:**
```php
<?php

declare(strict_types=1);

namespace Service;

use Symfony\Contracts\Cache\CacheInterface;

// VIOLATION: Infrastructure dependency in Domain
final readonly class ProductPriceCalculator
{
    public function __construct(
        private CacheInterface $cache,
    ) {}
}
```

**Good — Domain port + Infrastructure adapter:**
```php
<?php

declare(strict_types=1);

namespace Service;

// Domain port — pure PHP
interface PriceCacheInterface
{
    public function get(string $productId): ?Money;
    public function set(string $productId, Money $price, int $ttl = 3600): void;
    public function invalidate(string $productId): void;
}
```

```php
<?php

declare(strict_types=1);

namespace Cache;

use Service\PriceCacheInterface;
use ValueObject\Money;
use Symfony\Contracts\Cache\CacheInterface;
use Symfony\Contracts\Cache\ItemInterface;

final readonly class SymfonyPriceCache implements PriceCacheInterface
{
    public function __construct(
        private CacheInterface $catalogCache,
    ) {}

    public function get(string $productId): ?Money
    {
        return $this->catalogCache->get(
            'price_' . $productId,
            fn () => null,
        );
    }

    public function set(string $productId, Money $price, int $ttl = 3600): void
    {
        $this->catalogCache->get(
            'price_' . $productId,
            function (ItemInterface $item) use ($price, $ttl): Money {
                $item->expiresAfter($ttl);

                return $price;
            },
        );
    }

    public function invalidate(string $productId): void
    {
        $this->catalogCache->delete('price_' . $productId);
    }
}
```

**Cache pool configuration:**
```yaml
# config/packages/cache.yaml
framework:
    cache:
        pools:
            catalog.cache:
                adapter: cache.adapter.redis
                default_lifetime: 3600
            query.cache:
                adapter: cache.adapter.redis
                default_lifetime: 600
                tags: true
```

## Lock

Distributed locking for concurrency control in aggregates.

**Detection:**
```bash
# Lock usage
Grep: "LockFactory|LockInterface" --glob "src/**/*.php"
Grep: "lock:" --glob "**/config/packages/*.yaml"
```

**DDD use case — protect aggregate from concurrent modifications:**
```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use Symfony\Component\Lock\LockFactory;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private LockFactory $lockFactory,
    ) {}

    public function execute(ConfirmOrderCommand $command): void
    {
        $lock = $this->lockFactory->createLock(
            resource: 'order_' . $command->orderId->value,
            ttl: 30.0,
        );

        if (!$lock->acquire()) {
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

**Lock configuration:**
```yaml
# config/packages/lock.yaml
framework:
    lock:
        order: '%env(LOCK_DSN)%'      # redis://redis:6379
        inventory: '%env(LOCK_DSN)%'
```

## RateLimiter

API rate limiting with token bucket, sliding window, and fixed window algorithms.

**Detection:**
```bash
# RateLimiter usage
Grep: "RateLimiterFactory|RateLimiter" --glob "src/**/*.php"
Grep: "rate_limiter:" --glob "**/config/packages/*.yaml"
```

**Configuration:**
```yaml
# config/packages/rate_limiter.yaml
framework:
    rate_limiter:
        api_global:
            policy: token_bucket
            limit: 100
            rate: { interval: '1 minute', amount: 100 }

        api_authenticated:
            policy: sliding_window
            limit: 1000
            interval: '1 hour'

        login_attempt:
            policy: fixed_window
            limit: 5
            interval: '15 minutes'
```

**Rate limiting middleware:**
```php
<?php

declare(strict_types=1);

namespace RateLimiter;

use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\KernelEvents;
use Symfony\Component\RateLimiter\RateLimiterFactory;

#[AsEventListener(event: KernelEvents::REQUEST, priority: 200)]
final readonly class ApiRateLimitListener
{
    public function __construct(
        private RateLimiterFactory $apiGlobalLimiter,
    ) {}

    public function __invoke(RequestEvent $event): void
    {
        if (!$event->isMainRequest()) {
            return;
        }

        $request = $event->getRequest();

        if (!str_starts_with($request->getPathInfo(), '/api')) {
            return;
        }

        $limiter = $this->apiGlobalLimiter->create($request->getClientIp());
        $limit = $limiter->consume();

        if (!$limit->isAccepted()) {
            $retryAfter = $limit->getRetryAfter();
            $response = new \Symfony\Component\HttpFoundation\JsonResponse(
                ['error' => 'Rate limit exceeded'],
                429,
            );
            $response->headers->set('Retry-After', (string) $retryAfter->getTimestamp());
            $response->headers->set('X-RateLimit-Limit', (string) $limit->getLimit());
            $response->headers->set('X-RateLimit-Remaining', (string) $limit->getRemainingTokens());

            $event->setResponse($response);
        }
    }
}
```

## HTTP Client

Scoped HTTP clients for external service integration.

**Detection:**
```bash
# HTTP Client usage
Grep: "HttpClientInterface" --glob "src/**/*.php"
Grep: "use Symfony\\\\Contracts\\\\HttpClient" --glob "src/**/*.php"

# SSRF risk: unconfigured clients
Grep: "HttpClient::create\\(\\)" --glob "src/**/*.php"
```

**DDD adapter for external API:**
```php
<?php

declare(strict_types=1);

namespace Port;

// Domain port — no framework dependency
interface PaymentGatewayInterface
{
    public function charge(PaymentId $id, Money $amount, CardToken $token): PaymentResult;
    public function refund(PaymentId $id, Money $amount): RefundResult;
}
```

```php
<?php

declare(strict_types=1);

namespace Payment\Infrastructure\Gateway;

use Port\PaymentGatewayInterface;
use ValueObject\CardToken;
use ValueObject\Money;
use ValueObject\PaymentId;
use ValueObject\PaymentResult;
use ValueObject\RefundResult;
use Symfony\Contracts\HttpClient\HttpClientInterface;

final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private HttpClientInterface $stripeClient,
    ) {}

    public function charge(PaymentId $id, Money $amount, CardToken $token): PaymentResult
    {
        $response = $this->stripeClient->request('POST', '/v1/charges', [
            'body' => [
                'amount' => $amount->cents(),
                'currency' => $amount->currency()->value,
                'source' => $token->value,
                'idempotency_key' => $id->value,
            ],
        ]);

        $data = $response->toArray();

        return new PaymentResult(
            externalId: $data['id'],
            status: $data['status'],
        );
    }

    public function refund(PaymentId $id, Money $amount): RefundResult
    {
        $response = $this->stripeClient->request('POST', '/v1/refunds', [
            'body' => [
                'charge' => $id->value,
                'amount' => $amount->cents(),
            ],
        ]);

        return new RefundResult($response->toArray()['id']);
    }
}
```

**Scoped client configuration with SSRF protection:**
```yaml
# config/packages/http_client.yaml
framework:
    http_client:
        scoped_clients:
            stripe.client:
                base_uri: 'https://api.stripe.com'
                auth_bearer: '%env(STRIPE_SECRET_KEY)%'
                headers:
                    Content-Type: 'application/x-www-form-urlencoded'
                retry_failed:
                    max_retries: 2
                    delay: 1000
                    multiplier: 2
            # SSRF protection: use NoPrivateNetworkHttpClient for untrusted URLs
```

## Serializer

Symfony Serializer for DTO mapping, Value Object normalization, and API response formatting.

**Detection:**
```bash
# Serializer usage
Grep: "SerializerInterface|NormalizerInterface|DenormalizerInterface" --glob "src/**/*.php"
Grep: "#\\[Groups|#\\[Ignore|#\\[SerializedName" --glob "src/**/*.php"
```

**Custom normalizer for Value Objects:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Serializer;

use ValueObject\Money;
use Symfony\Component\Serializer\Normalizer\NormalizerInterface;

final class MoneyNormalizer implements NormalizerInterface
{
    /** @param Money $data */
    public function normalize(mixed $data, ?string $format = null, array $context = []): array
    {
        return [
            'amount' => $data->cents(),
            'currency' => $data->currency()->value,
        ];
    }

    public function supportsNormalization(mixed $data, ?string $format = null, array $context = []): bool
    {
        return $data instanceof Money;
    }

    public function getSupportedTypes(?string $format): array
    {
        return [Money::class => true];
    }
}
```

**DTO with serialization attributes:**
```php
<?php

declare(strict_types=1);

namespace DTO;

use Symfony\Component\Serializer\Attribute\Groups;
use Symfony\Component\Serializer\Attribute\SerializedName;

final readonly class OrderResponseDTO
{
    public function __construct(
        #[Groups(['api', 'admin'])]
        public string $id,

        #[Groups(['api', 'admin'])]
        public string $status,

        #[Groups(['api', 'admin'])]
        #[SerializedName('total')]
        public MoneyDTO $totalAmount,

        #[Groups(['admin'])]
        public ?string $internalNote = null,
    ) {}
}
```

## Scheduler

Recurring tasks with distributed locking for multi-instance deployments.

**Detection:**
```bash
# Scheduler usage
Grep: "AsPeriodicTask|AsCronTask|RecurringMessage" --glob "src/**/*.php"
Grep: "scheduler:" --glob "**/config/packages/*.yaml"
```

**Scheduled message with cron expression:**
```php
<?php

declare(strict_types=1);

namespace Scheduler;

use Command\GenerateDailyReportCommand;
use Symfony\Component\Scheduler\Attribute\AsSchedule;
use Symfony\Component\Scheduler\RecurringMessage;
use Symfony\Component\Scheduler\Schedule;
use Symfony\Component\Scheduler\ScheduleProviderInterface;

#[AsSchedule('default')]
final readonly class AppScheduleProvider implements ScheduleProviderInterface
{
    public function getSchedule(): Schedule
    {
        return (new Schedule())
            ->add(
                RecurringMessage::cron(
                    '0 6 * * *',
                    new GenerateDailyReportCommand(date: new \DateTimeImmutable('yesterday')),
                ),
            )
            ->add(
                RecurringMessage::every(
                    '5 minutes',
                    new ProcessPendingPaymentsCommand(),
                ),
            );
    }
}
```

**Lock for distributed scheduler (prevent duplicate execution):**
```yaml
# config/packages/scheduler.yaml
framework:
    scheduler:
        default:
            lock: '%env(LOCK_DSN)%'    # Ensures only one instance runs scheduled task
```

## Summary

| Component | DDD Layer | Interface Location | Implementation |
|-----------|-----------|-------------------|----------------|
| Cache | Infrastructure | Domain port (`PriceCacheInterface`) | `SymfonyPriceCache` in Infrastructure |
| Lock | Application | Symfony `LockFactory` in Application | Configured via `lock.yaml` |
| RateLimiter | Infrastructure | Kernel listener | `rate_limiter.yaml` config |
| HTTP Client | Infrastructure | Domain port (`PaymentGatewayInterface`) | Scoped client adapter in Infrastructure |
| Serializer | Infrastructure | Normalizer interface | Custom normalizers for Value Objects |
| Scheduler | Infrastructure | `ScheduleProviderInterface` | Cron/periodic messages dispatched via Messenger |
