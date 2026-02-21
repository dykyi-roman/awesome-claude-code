# Infrastructure Components in Yii3

Cache (`yiisoft/cache`), Rate Limiter (`yiisoft/rate-limiter`), HTTP Client (PSR-18), Mailer (`yiisoft/mailer`), and DDD integration via domain port pattern.

## Cache (yiisoft/cache)

### PSR-16 Compliance

| Feature | Description |
|---------|-------------|
| PSR-16 wrapper | Wraps any PSR-16 (`SimpleCacheInterface`) implementation |
| Default TTL | Configurable per cache instance |
| Key prefix | Namespace keys to avoid collisions between modules |
| Stampede prevention | "Probably early expiration" algorithm avoids cache stampedes |
| Invalidation dependencies | Tag, callback, file, and value-based invalidation |

### TTL Value Object

```php
<?php

declare(strict_types=1);

use Yiisoft\Cache\Metadata\CacheItem;

// TTL helpers
$ttl = 30 * 60;           // 30 minutes in seconds
$ttl = 60 * 60;           // 1 hour in seconds

// Cache with TTL
$cache->set('order:123', $data, $ttl);

// Forever (null TTL)
$cache->set('config:app', $data);
```

### Cache Handlers

| Handler | Package | Use Case |
|---------|---------|----------|
| `ArrayCache` | `yiisoft/cache` | Current request only, testing |
| `NullCache` | `yiisoft/cache` | No caching (development, testing) |
| `FileCache` | `yiisoft/cache-file` | File-based, no external dependencies |
| Redis | `yiisoft/cache-redis` | Production, distributed cache |
| Memcached | `yiisoft/cache-memcached` | Production, distributed cache |
| Database | `yiisoft/cache-db` | Persistent cache via DB |
| APCu | `yiisoft/cache-apcu` | Single-server, in-memory |

### Bad: Cache in Domain Layer

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Service;

use Psr\SimpleCache\CacheInterface; // VIOLATION: PSR package in Domain

final readonly class OrderService
{
    public function __construct(
        private CacheInterface $cache, // Domain depends on infrastructure concern
    ) {}

    public function findById(string $id): ?Order
    {
        return $this->cache->get("order:{$id}");
    }
}
```

### Good: Domain Defines Own Port

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Port;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;

interface OrderCacheInterface
{
    public function getById(OrderId $id): ?Order;

    public function store(Order $order): void;

    public function invalidate(OrderId $id): void;
}
```

### Infrastructure Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Domain\Order\Entity\Order;
use Domain\Order\Port\OrderCacheInterface;
use Domain\Order\ValueObject\OrderId;
use Psr\SimpleCache\CacheInterface;

final readonly class PsrOrderCache implements OrderCacheInterface
{
    private const int TTL_SECONDS = 1800; // 30 minutes

    public function __construct(
        private CacheInterface $cache,
        private OrderMapper $mapper,
    ) {}

    public function getById(OrderId $id): ?Order
    {
        $data = $this->cache->get("order:{$id->value}");

        return $data !== null ? $this->mapper->toDomain($data) : null;
    }

    public function store(Order $order): void
    {
        $this->cache->set(
            "order:{$order->id()->value}",
            $this->mapper->toArray($order),
            self::TTL_SECONDS,
        );
    }

    public function invalidate(OrderId $id): void
    {
        $this->cache->delete("order:{$id->value}");
    }
}
```

### DI Configuration

```php
<?php

declare(strict_types=1);

// config/common/di/cache.php

use Domain\Order\Port\OrderCacheInterface;
use Infrastructure\Cache\PsrOrderCache;
use Psr\SimpleCache\CacheInterface;
use Yiisoft\Cache\Cache;
use Yiisoft\Cache\File\FileCache;
use Yiisoft\Definitions\Reference;

return [
    CacheInterface::class => [
        'class' => Cache::class,
        '__construct()' => [
            Reference::to(FileCache::class),
        ],
    ],
    OrderCacheInterface::class => PsrOrderCache::class,
];
```

## Rate Limiter (yiisoft/rate-limiter)

### Overview

| Feature | Description |
|---------|-------------|
| Algorithm | GCRA (Generic Cell Rate Algorithm) |
| Integration | PSR-15 middleware |
| Response | HTTP 429 Too Many Requests when threshold exceeded |
| Headers | `X-Rate-Limit-Limit`, `X-Rate-Limit-Remaining`, `X-Rate-Limit-Reset` |

### Built-in Policies

| Policy | Description |
|--------|-------------|
| `LimitPerIp` | Separate counters per client IP (default) |
| `LimitAlways` | Count all requests uniformly |
| `LimitCallback` | Custom logic (e.g., per user ID, per API key) |

### Storage Options

| Storage | Package | Use Case |
|---------|---------|----------|
| `SimpleCacheStorage` | `yiisoft/rate-limiter` | Any PSR-16 cache backend |
| `ApcuStorage` | `yiisoft/rate-limiter` | APCu extension, handles concurrency |

### DI Configuration

```php
<?php

declare(strict_types=1);

// config/web/di/rate-limiter.php

use Yiisoft\RateLimiter\Counter;
use Yiisoft\RateLimiter\CounterInterface;
use Yiisoft\RateLimiter\Storage\SimpleCacheStorage;
use Yiisoft\RateLimiter\Storage\StorageInterface;

return [
    StorageInterface::class => SimpleCacheStorage::class,
    CounterInterface::class => [
        'class' => Counter::class,
        '__construct()' => [
            'limit' => 100,
            'periodInSeconds' => 60,
        ],
    ],
];
```

### Route Middleware

```php
<?php

declare(strict_types=1);

// config/web/routes.php

use Yiisoft\RateLimiter\Middleware\RateLimiterMiddleware;
use Yiisoft\Router\Route;
use Yiisoft\Router\Group;

return [
    Group::create('/api/v1')
        ->routes(
            Route::post('/orders')
                ->middleware(RateLimiterMiddleware::class)
                ->action([CreateOrderAction::class, '__invoke'])
                ->name('orders.create'),
        ),
];
```

### Custom Rate Policy (per user)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Psr\Http\Message\ServerRequestInterface;
use Yiisoft\RateLimiter\Policy\LimitCallback;

final readonly class UserRateLimitPolicy
{
    public static function create(): LimitCallback
    {
        return new LimitCallback(
            static function (ServerRequestInterface $request): string {
                $userId = $request->getAttribute('userId');

                return $userId !== null
                    ? "user:{$userId}"
                    : 'ip:' . ($request->getServerParams()['REMOTE_ADDR'] ?? 'unknown');
            },
        );
    }
}
```

## HTTP Client (PSR-18)

### Note on yiisoft/yii-http-client

`yiisoft/yii-http-client` is deprecated. Use any PSR-18 implementation (Guzzle, Symfony HttpClient, etc.) with PSR-17 factories.

### Bad: HTTP Client in Domain Layer

```php
<?php

declare(strict_types=1);

namespace Domain\Payment\Service;

use GuzzleHttp\Client; // VIOLATION: infrastructure dependency in Domain

final readonly class PaymentService
{
    public function __construct(
        private Client $httpClient, // Domain depends on Guzzle
    ) {}
}
```

### Good: Domain Defines Own Port

```php
<?php

declare(strict_types=1);

namespace Domain\Payment\Port;

use Domain\Payment\ValueObject\Money;
use Domain\Payment\ValueObject\PaymentResult;

interface PaymentGatewayClientInterface
{
    public function charge(Money $amount, string $token): PaymentResult;
}
```

### Infrastructure Adapter with Guzzle

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Domain\Payment\Port\PaymentGatewayClientInterface;
use Domain\Payment\ValueObject\Money;
use Domain\Payment\ValueObject\PaymentResult;
use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class GuzzlePaymentGatewayClient implements PaymentGatewayClientInterface
{
    public function __construct(
        private ClientInterface $httpClient,
        private RequestFactoryInterface $requestFactory,
        private StreamFactoryInterface $streamFactory,
        private string $apiUrl,
        private string $apiKey,
    ) {}

    public function charge(Money $amount, string $token): PaymentResult
    {
        $body = $this->streamFactory->createStream(json_encode([
            'amount' => $amount->cents(),
            'currency' => $amount->currency()->value,
            'token' => $token,
        ], JSON_THROW_ON_ERROR));

        $request = $this->requestFactory
            ->createRequest('POST', $this->apiUrl . '/charges')
            ->withHeader('Authorization', 'Bearer ' . $this->apiKey)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body);

        $response = $this->httpClient->sendRequest($request);
        $data = json_decode(
            (string) $response->getBody(),
            true,
            512,
            JSON_THROW_ON_ERROR,
        );

        return new PaymentResult(
            success: $response->getStatusCode() === 200,
            transactionId: $data['id'] ?? null,
        );
    }
}
```

### DI Configuration for HTTP Client

```php
<?php

declare(strict_types=1);

// config/common/di/http-client.php

use Domain\Payment\Port\PaymentGatewayClientInterface;
use GuzzleHttp\Client;
use Infrastructure\Http\GuzzlePaymentGatewayClient;
use Psr\Http\Client\ClientInterface;

return [
    ClientInterface::class => [
        'class' => Client::class,
        '__construct()' => [
            'config' => [
                'timeout' => 30,
                'connect_timeout' => 5,
            ],
        ],
    ],
    PaymentGatewayClientInterface::class => [
        'class' => GuzzlePaymentGatewayClient::class,
        '__construct()' => [
            'apiUrl' => $params['payment']['apiUrl'],
            'apiKey' => $params['payment']['apiKey'],
        ],
    ],
];
```

## Mailer (yiisoft/mailer)

### Overview

| Feature | Description |
|---------|-------------|
| Interface | `MailerInterface` for sending messages |
| Templates | `yiisoft/view` template rendering |
| Transports | Symfony Mailer, SwiftMailer, or custom transport |
| Message builder | Fluent API for composing emails |

### Bad: Mailer in Domain Layer

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Service;

use Yiisoft\Mailer\MailerInterface; // VIOLATION: infrastructure dependency in Domain

final readonly class OrderNotificationService
{
    public function __construct(
        private MailerInterface $mailer, // Domain depends on Yii mailer
    ) {}
}
```

### Good: Domain Defines Own Port

```php
<?php

declare(strict_types=1);

namespace Domain\Notification\Port;

use Domain\Notification\ValueObject\EmailAddress;
use Domain\Notification\ValueObject\NotificationMessage;

interface NotificationSenderInterface
{
    public function send(EmailAddress $to, NotificationMessage $message): void;
}
```

### Infrastructure Adapter

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Mail;

use Domain\Notification\Port\NotificationSenderInterface;
use Domain\Notification\ValueObject\EmailAddress;
use Domain\Notification\ValueObject\NotificationMessage;
use Yiisoft\Mailer\MailerInterface;

final readonly class YiiMailerAdapter implements NotificationSenderInterface
{
    public function __construct(
        private MailerInterface $mailer,
        private string $fromAddress,
    ) {}

    public function send(EmailAddress $to, NotificationMessage $message): void
    {
        $this->mailer
            ->compose(
                $message->template(),
                ['data' => $message->context()],
            )
            ->setFrom($this->fromAddress)
            ->setTo($to->value)
            ->setSubject($message->subject())
            ->send();
    }
}
```

### DI Configuration

```php
<?php

declare(strict_types=1);

// config/common/di/mailer.php

use Domain\Notification\Port\NotificationSenderInterface;
use Infrastructure\Mail\YiiMailerAdapter;
use Yiisoft\Mailer\MailerInterface;
use Yiisoft\Mailer\Symfony\Mailer;

return [
    MailerInterface::class => [
        'class' => Mailer::class,
    ],
    NotificationSenderInterface::class => [
        'class' => YiiMailerAdapter::class,
        '__construct()' => [
            'fromAddress' => $params['mail']['from'],
        ],
    ],
];
```

## Detection Patterns

```bash
# Cache in Domain (MUST be zero)
Grep: "use Psr\\SimpleCache\\" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\Cache\\" --glob "**/Domain/**/*.php"

# Cache in Application (should use domain port)
Grep: "CacheInterface" --glob "**/Application/**/*.php"

# HTTP Client in Domain (MUST be zero)
Grep: "use Psr\\Http\\Client\\" --glob "**/Domain/**/*.php"
Grep: "use GuzzleHttp\\" --glob "**/Domain/**/*.php"

# Mailer in Domain (MUST be zero)
Grep: "use Yiisoft\\Mailer\\" --glob "**/Domain/**/*.php"

# Rate Limiter configuration
Grep: "RateLimiter" --glob "config/**/*.php"
Grep: "CounterInterface" --glob "config/**/*.php"

# Infrastructure adapters exist
Grep: "implements.*CacheInterface" --glob "**/Infrastructure/**/*.php"
Grep: "implements.*ClientInterface" --glob "**/Infrastructure/**/*.php"
Grep: "implements.*NotificationSenderInterface" --glob "**/Infrastructure/**/*.php"

# Domain ports defined
Grep: "interface.*CacheInterface" --glob "**/Domain/**/Port/*.php"
Grep: "interface.*ClientInterface" --glob "**/Domain/**/Port/*.php"
Grep: "interface.*SenderInterface" --glob "**/Domain/**/Port/*.php"

# Cache DI configuration
Glob: config/common/di/cache.php
Glob: config/web/di/rate-limiter.php

# HTTP client DI configuration
Glob: config/common/di/http-client.php
```

## Summary Table

| Component | DDD Layer | Interface Location | Implementation | Yii Package |
|-----------|-----------|-------------------|----------------|-------------|
| Cache | Domain port + Infra adapter | `Domain\*\Port\*CacheInterface` | `PsrOrderCache` | `yiisoft/cache` (PSR-16) |
| Rate Limiter | Presentation (middleware) | -- | `RateLimiterMiddleware` | `yiisoft/rate-limiter` |
| HTTP Client | Domain port + Infra adapter | `Domain\*\Port\*ClientInterface` | `GuzzlePaymentGatewayClient` | Any PSR-18 |
| Mailer | Domain port + Infra adapter | `Domain\*\Port\*SenderInterface` | `YiiMailerAdapter` | `yiisoft/mailer` |
