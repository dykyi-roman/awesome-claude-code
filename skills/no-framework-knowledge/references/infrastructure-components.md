# Infrastructure Components in No-Framework PHP

Cache (PSR-6/PSR-16), HTTP Client (PSR-18), Mailer, and Rate Limiting using standalone Composer packages with DDD ports and infrastructure adapters.

## Cache (PSR-6/PSR-16)

### Recommended Packages

| Package | PSR | Backends |
|---------|-----|----------|
| `symfony/cache` | PSR-6, PSR-16 | Redis, Memcached, Filesystem, APCu, Array |
| `phpfastcache/phpfastcache` | PSR-6, PSR-16 | Redis, Memcached, Files, MongoDB |
| `cache/adapter-common` | PSR-6 | Multiple adapters |

```bash
composer require symfony/cache
```

### Configuration

```php
<?php

declare(strict_types=1);

// config/cache.php
use Symfony\Component\Cache\Adapter\RedisAdapter;
use Symfony\Component\Cache\Psr16Cache;

$redisConnection = RedisAdapter::createConnection(
    $_ENV['REDIS_DSN'] ?? 'redis://localhost:6379',
);

$psr6Pool = new RedisAdapter($redisConnection, 'app', 300);
$psr16Cache = new Psr16Cache($psr6Pool);

return $psr16Cache;
```

### DDD: Cache Port Pattern

**Bad: Cache in Domain**
```php
<?php

declare(strict_types=1);

namespace Service;

use Psr\SimpleCache\CacheInterface; // VIOLATION: PSR in Domain

final readonly class OrderPricingService
{
    public function __construct(
        private CacheInterface $cache, // VIOLATION
    ) {}
}
```

**Good: Domain Port + Infrastructure Adapter**
```php
<?php

declare(strict_types=1);

namespace Cache;

use ValueObject\OrderId;
use ValueObject\Money;

interface OrderCacheInterface
{
    public function getTotal(OrderId $id): ?Money;
    public function saveTotal(OrderId $id, Money $total): void;
    public function invalidate(OrderId $id): void;
}
```

```php
<?php

declare(strict_types=1);

namespace Cache;

use Cache\OrderCacheInterface;
use ValueObject\OrderId;
use ValueObject\Money;
use Psr\SimpleCache\CacheInterface;

final readonly class PsrOrderCache implements OrderCacheInterface
{
    private const TTL = 300;

    public function __construct(
        private CacheInterface $cache,
    ) {}

    public function getTotal(OrderId $id): ?Money
    {
        $cents = $this->cache->get("order_total_{$id->value}");

        return $cents !== null ? Money::fromCents((int) $cents) : null;
    }

    public function saveTotal(OrderId $id, Money $total): void
    {
        $this->cache->set("order_total_{$id->value}", $total->cents, self::TTL);
    }

    public function invalidate(OrderId $id): void
    {
        $this->cache->delete("order_total_{$id->value}");
    }
}
```

## HTTP Client (PSR-18)

### Recommended Packages

| Package | PSR | Features |
|---------|-----|----------|
| `guzzlehttp/guzzle` | PSR-18 | Full-featured, middleware, retry |
| `symfony/http-client` | PSR-18 | Scoped clients, async, retry |
| `php-http/curl-client` | PSR-18 | Lightweight cURL wrapper |

```bash
composer require guzzlehttp/guzzle
```

### Basic Usage

```php
<?php

declare(strict_types=1);

use GuzzleHttp\Client;

$client = new Client([
    'base_uri' => 'https://api.example.com/v1/',
    'timeout'  => 10,
    'headers'  => ['Accept' => 'application/json'],
]);

$response = $client->get('orders/123');
$data = json_decode($response->getBody()->getContents(), true, 512, JSON_THROW_ON_ERROR);
```

### DDD: HTTP Client Port Pattern

**Bad: Guzzle in Application**
```php
<?php

declare(strict_types=1);

namespace Payment;

use GuzzleHttp\Client; // VIOLATION

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private Client $client, // VIOLATION: Infrastructure in Application
    ) {}
}
```

**Good: Domain Port + Infrastructure Adapter**
```php
<?php

declare(strict_types=1);

namespace Payment;

use ValueObject\OrderId;
use ValueObject\Money;

interface PaymentGatewayInterface
{
    public function charge(OrderId $orderId, Money $amount): PaymentResult;
}
```

```php
<?php

declare(strict_types=1);

namespace Payment;

use Payment\PaymentGatewayInterface;
use Payment\PaymentResult;
use ValueObject\OrderId;
use ValueObject\Money;
use GuzzleHttp\ClientInterface;
use GuzzleHttp\Exception\GuzzleException;

final readonly class GuzzlePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private ClientInterface $client,
        private string $apiKey,
    ) {}

    public function charge(OrderId $orderId, Money $amount): PaymentResult
    {
        try {
            $response = $this->client->request('POST', 'charges', [
                'json' => [
                    'orderId' => $orderId->value,
                    'amount'  => $amount->cents,
                ],
                'headers' => ['Authorization' => "Bearer {$this->apiKey}"],
            ]);

            $data = json_decode(
                $response->getBody()->getContents(),
                true,
                512,
                JSON_THROW_ON_ERROR,
            );

            return PaymentResult::success($data['transactionId']);
        } catch (GuzzleException $e) {
            return PaymentResult::failure($e->getMessage());
        }
    }
}
```

## Mailer

### Recommended Packages

| Package | Features |
|---------|----------|
| `symfony/mailer` | Standalone, transports (SMTP, SES, Mailgun) |
| `phpmailer/phpmailer` | Classic, SMTP, attachments |
| `swiftmailer/swiftmailer` | Legacy (use symfony/mailer instead) |

```bash
composer require symfony/mailer
```

### DDD: Mailer Port Pattern

```php
<?php

declare(strict_types=1);

namespace Notification;

use ValueObject\OrderId;
use ValueObject\Email;

interface NotificationSenderInterface
{
    public function sendOrderConfirmation(OrderId $orderId, Email $customerEmail): void;
}
```

```php
<?php

declare(strict_types=1);

namespace Notification;

use Notification\NotificationSenderInterface;
use ValueObject\OrderId;
use Domain\User\ValueObject\Email as EmailVO;
use Symfony\Component\Mailer\MailerInterface;
use Symfony\Component\Mime\Email;

final readonly class SymfonyMailerNotificationSender implements NotificationSenderInterface
{
    public function __construct(
        private MailerInterface $mailer,
        private string $fromAddress,
    ) {}

    public function sendOrderConfirmation(OrderId $orderId, EmailVO $customerEmail): void
    {
        $email = (new Email())
            ->from($this->fromAddress)
            ->to($customerEmail->value)
            ->subject('Order Confirmed')
            ->html("<p>Your order #{$orderId->value} has been confirmed.</p>");

        $this->mailer->send($email);
    }
}
```

## Rate Limiting

### Custom Rate Limiter (Token Bucket)

```php
<?php

declare(strict_types=1);

namespace RateLimiter;

use Psr\SimpleCache\CacheInterface;

final readonly class TokenBucketRateLimiter
{
    public function __construct(
        private CacheInterface $cache,
        private int $maxTokens,
        private int $refillRate, // tokens per second
    ) {}

    public function consume(string $key): bool
    {
        $now = microtime(true);
        $bucket = $this->cache->get("rate_limit_{$key}");

        if ($bucket === null) {
            $bucket = ['tokens' => $this->maxTokens - 1, 'lastRefill' => $now];
            $this->cache->set("rate_limit_{$key}", $bucket, 3600);

            return true;
        }

        $elapsed = $now - $bucket['lastRefill'];
        $newTokens = (int) ($elapsed * $this->refillRate);
        $tokens = min($this->maxTokens, $bucket['tokens'] + $newTokens);

        if ($tokens < 1) {
            return false;
        }

        $bucket = ['tokens' => $tokens - 1, 'lastRefill' => $now];
        $this->cache->set("rate_limit_{$key}", $bucket, 3600);

        return true;
    }
}
```

### Rate Limit Middleware (PSR-15)

```php
<?php

declare(strict_types=1);

namespace Middleware;

use RateLimiter\TokenBucketRateLimiter;
use Nyholm\Psr7\Response;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class RateLimitMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TokenBucketRateLimiter $limiter,
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $key = $request->getServerParams()['REMOTE_ADDR'] ?? 'unknown';

        if (!$this->limiter->consume($key)) {
            return new Response(
                status: 429,
                headers: ['Retry-After' => '60'],
                body: json_encode(['error' => 'Too many requests'], JSON_THROW_ON_ERROR),
            );
        }

        return $handler->handle($request);
    }
}
```

## DI Container Wiring

```php
<?php

declare(strict_types=1);

// config/container.php — infrastructure bindings
use Cache\OrderCacheInterface;
use Payment\PaymentGatewayInterface;
use Notification\NotificationSenderInterface;
use Cache\PsrOrderCache;
use Payment\GuzzlePaymentGateway;
use Notification\SymfonyMailerNotificationSender;

$builder->addDefinitions([
    // Cache
    Psr\SimpleCache\CacheInterface::class => DI\factory(require __DIR__ . '/cache.php'),
    OrderCacheInterface::class => DI\autowire(PsrOrderCache::class),

    // HTTP Client
    GuzzleHttp\ClientInterface::class => DI\factory(static fn() => new GuzzleHttp\Client([
        'base_uri' => $_ENV['PAYMENT_API_URL'],
        'timeout' => 30,
    ])),
    PaymentGatewayInterface::class => DI\create(GuzzlePaymentGateway::class)
        ->constructor(DI\get(GuzzleHttp\ClientInterface::class), $_ENV['PAYMENT_API_KEY']),

    // Mailer
    NotificationSenderInterface::class => DI\autowire(SymfonyMailerNotificationSender::class),
]);
```

## Detection Patterns

```bash
# PSR cache in Domain (VIOLATION)
Grep: "use Psr\\SimpleCache|use Psr\\Cache|use Symfony\\.*Cache" --glob "**/Domain/**/*.php"

# HTTP client in Domain (VIOLATION)
Grep: "use GuzzleHttp|use Symfony\\.*HttpClient|use Http\\Client" --glob "**/Domain/**/*.php"

# Mailer in Domain (VIOLATION)
Grep: "use Symfony\\.*Mailer|use PHPMailer" --glob "**/Domain/**/*.php"

# Good: Domain ports exist
Grep: "OrderCacheInterface|PaymentGatewayInterface|NotificationSenderInterface" --glob "**/Domain/**/*.php"

# Good: Infrastructure adapters exist
Grep: "implements.*CacheInterface|implements.*GatewayInterface|implements.*SenderInterface" --glob "**/Infrastructure/**/*.php"
```

## Summary Table

| Component | DDD Layer | Package | Integration Pattern |
|-----------|-----------|---------|---------------------|
| Cache | Domain: OrderCacheInterface port | `symfony/cache` (PSR-16) | Infrastructure PsrOrderCache adapter |
| HTTP Client | Domain: PaymentGatewayInterface port | `guzzlehttp/guzzle` (PSR-18) | Infrastructure GuzzlePaymentGateway adapter |
| Mailer | Domain: NotificationSenderInterface port | `symfony/mailer` | Infrastructure SymfonyMailerNotificationSender |
| Rate Limiting | Presentation: PSR-15 middleware | Custom + PSR-16 cache | RateLimitMiddleware + TokenBucketRateLimiter |
| File Storage | Domain: FileStorageInterface port | `league/flysystem` | Infrastructure FlysystemAdapter |
