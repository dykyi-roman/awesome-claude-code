# Infrastructure Components in CodeIgniter 4

Cache, CURLRequest HTTP Client, Email, and Throttler with DDD ports and infrastructure adapters.

## Cache

### Configuration (app/Config/Cache.php)

CI4 supports multiple cache handlers: file, redis, memcached, predis, apcu, wincache, dummy.

```php
<?php

declare(strict_types=1);

namespace Config;

use CodeIgniter\Config\BaseConfig;

final class Cache extends BaseConfig
{
    public string $handler = 'redis';
    public string $backupHandler = 'file';
    public string $prefix = 'ci4_';
    public int $ttl = 300;

    public array $redis = [
        'host'     => '127.0.0.1',
        'password' => null,
        'port'     => 6379,
        'timeout'  => 0,
        'database' => 0,
    ];

    public array $memcached = [
        'host'   => '127.0.0.1',
        'port'   => 11211,
        'weight' => 1,
        'raw'    => false,
    ];
}
```

### Cache Methods

| Method | Purpose |
|--------|---------|
| `get($key)` | Retrieve cached item (null if miss) |
| `save($key, $data, $ttl)` | Store data with TTL |
| `delete($key)` | Remove specific item |
| `deleteMatching($pattern)` | Glob-style deletion (File/Redis only) |
| `increment($key, $offset)` | Atomic increment |
| `decrement($key, $offset)` | Atomic decrement |
| `remember($key, $ttl, $callback)` | Get or compute and cache |
| `clean()` | Clear entire cache |
| `getCacheInfo()` | Cache statistics |
| `getMetadata($key)` | Expiry and metadata |

### DDD: Cache Port Pattern

**Bad: Cache in Domain**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Service;

use CodeIgniter\Cache\CacheInterface; // VIOLATION

final readonly class OrderPricingService
{
    public function __construct(
        private CacheInterface $cache, // VIOLATION: Infrastructure in Domain
    ) {}

    public function calculateTotal(OrderId $orderId): Money
    {
        return $this->cache->remember("order_total_{$orderId->value()}", 300, function () use ($orderId) {
            return $this->doCalculate($orderId);
        });
    }
}
```

**Good: Domain Port + Infrastructure Adapter**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Cache;

use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Shared\ValueObject\Money;

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

namespace App\Infrastructure\Cache;

use App\Domain\Order\Cache\OrderCacheInterface;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Shared\ValueObject\Money;
use CodeIgniter\Cache\CacheInterface;

final readonly class CIOrderCache implements OrderCacheInterface
{
    private const TTL = 300;

    public function __construct(
        private CacheInterface $cache,
    ) {}

    public function getTotal(OrderId $id): ?Money
    {
        $cents = $this->cache->get("order_total_{$id->value()}");

        return $cents !== null ? Money::fromCents((int) $cents) : null;
    }

    public function saveTotal(OrderId $id, Money $total): void
    {
        $this->cache->save("order_total_{$id->value()}", $total->cents(), self::TTL);
    }

    public function invalidate(OrderId $id): void
    {
        $this->cache->delete("order_total_{$id->value()}");
    }
}
```

## CURLRequest (HTTP Client)

### Basic Usage

```php
<?php

declare(strict_types=1);

$client = service('curlrequest');

// GET request
$response = $client->get('https://api.example.com/orders', [
    'headers' => ['Accept' => 'application/json'],
    'timeout' => 5,
]);

$data = json_decode($response->getBody(), true);
$status = $response->getStatusCode(); // 200

// POST with JSON
$response = $client->post('https://api.example.com/orders', [
    'json' => ['customer_id' => 123, 'total' => 5000],
    'headers' => ['Authorization' => 'Bearer token123'],
]);

// With base URI
$client = service('curlrequest', [
    'baseURI' => 'https://api.example.com/v1/',
    'timeout' => 10,
]);
$response = $client->get('orders/123');
```

### Configuration Options

| Option | Type | Purpose |
|--------|------|---------|
| `baseURI` | string | Base URL for relative paths |
| `timeout` | int | Request timeout (seconds) |
| `connect_timeout` | int | Connection timeout |
| `headers` | array | HTTP headers |
| `auth` | array | `[username, password, type]` |
| `json` | array | JSON body (auto Content-Type) |
| `form_params` | array | Form-encoded body |
| `query` | array | Query parameters |
| `verify` | bool/string | SSL verification |
| `http_errors` | bool | Throw on 4xx/5xx (default: true) |
| `allow_redirects` | bool/array | Follow redirects |

### DDD: HTTP Client Port Pattern

**Bad: CURLRequest in Application**
```php
<?php

declare(strict_types=1);

namespace App\Application\Payment;

use CodeIgniter\HTTP\CURLRequest; // VIOLATION

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private CURLRequest $client, // VIOLATION: Infrastructure in Application
    ) {}

    public function execute(string $orderId, int $amount): void
    {
        $this->client->post('https://payment.example.com/charge', [
            'json' => ['orderId' => $orderId, 'amount' => $amount],
        ]);
    }
}
```

**Good: Domain Port + Infrastructure Adapter**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Payment;

interface PaymentGatewayInterface
{
    public function charge(OrderId $orderId, Money $amount): PaymentResult;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Payment;

use App\Domain\Payment\PaymentGatewayInterface;
use App\Domain\Payment\PaymentResult;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\Shared\ValueObject\Money;
use CodeIgniter\HTTP\CURLRequest;

final readonly class CIPaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private CURLRequest $client,
        private string $apiUrl,
        private string $apiKey,
    ) {}

    public function charge(OrderId $orderId, Money $amount): PaymentResult
    {
        try {
            $response = $this->client->post("{$this->apiUrl}/charge", [
                'json' => [
                    'orderId' => $orderId->value(),
                    'amount'  => $amount->cents(),
                ],
                'headers' => ['Authorization' => "Bearer {$this->apiKey}"],
                'timeout' => 30,
            ]);

            $data = json_decode($response->getBody(), true);

            return PaymentResult::success($data['transactionId']);
        } catch (\Exception $e) {
            return PaymentResult::failure($e->getMessage());
        }
    }
}
```

## Email

### Configuration (app/Config/Email.php)

```php
<?php

declare(strict_types=1);

namespace Config;

use CodeIgniter\Config\BaseConfig;

final class Email extends BaseConfig
{
    public string $protocol = 'smtp';
    public string $SMTPHost = 'smtp.example.com';
    public int $SMTPPort = 587;
    public string $SMTPUser = '';
    public string $SMTPPass = '';
    public string $SMTPCrypto = 'tls';
    public string $mailType = 'html';
    public string $charset = 'UTF-8';
    public bool $wordWrap = true;
}
```

### DDD: Mailer Port Pattern

**Bad: Email service in Domain**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Service;

final readonly class OrderNotificationService
{
    public function sendConfirmation(Order $order): void
    {
        $email = service('email'); // VIOLATION: Infrastructure in Domain
        $email->setTo($order->customerEmail());
        $email->setSubject('Order Confirmed');
        $email->setMessage("Order #{$order->id()->value()} confirmed.");
        $email->send(); // VIOLATION
    }
}
```

**Good: Domain Port + Infrastructure Adapter**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Notification;

interface NotificationSenderInterface
{
    public function sendOrderConfirmation(OrderId $orderId, Email $customerEmail): void;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Notification;

use App\Domain\Notification\NotificationSenderInterface;
use App\Domain\Order\ValueObject\OrderId;
use App\Domain\User\ValueObject\Email as EmailVO;

final readonly class CIEmailNotificationSender implements NotificationSenderInterface
{
    public function sendOrderConfirmation(OrderId $orderId, EmailVO $customerEmail): void
    {
        $email = service('email');
        $email->setFrom('orders@example.com', 'Order System');
        $email->setTo($customerEmail->value());
        $email->setSubject('Order Confirmed');
        $email->setMessage("Your order #{$orderId->value()} has been confirmed.");

        if (!$email->send()) {
            throw new \RuntimeException('Failed to send order confirmation email');
        }
    }
}
```

## Throttler (Rate Limiting)

### Basic Usage

```php
<?php

declare(strict_types=1);

$throttler = service('throttler');

// Allow 60 requests per minute
if ($throttler->check('api_' . $request->getIPAddress(), 60, MINUTE) === false) {
    return service('response')
        ->setStatusCode(429)
        ->setJSON(['error' => 'Too many requests']);
}
```

### Rate Limiting Filter

```php
<?php

declare(strict_types=1);

namespace App\Filters;

use CodeIgniter\Filters\FilterInterface;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;

final readonly class RateLimitFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null)
    {
        $throttler = service('throttler');
        $maxRequests = (int) ($arguments[0] ?? 60);
        $key = 'api_' . $request->getIPAddress();

        if ($throttler->check($key, $maxRequests, MINUTE) === false) {
            $response = service('response');

            return $response
                ->setStatusCode(429)
                ->setHeader('Retry-After', (string) $throttler->getTokenTime())
                ->setJSON(['error' => 'Rate limit exceeded']);
        }
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null)
    {
    }
}
```

### Route Configuration

```php
<?php

declare(strict_types=1);

// app/Config/Filters.php
public array $aliases = [
    'throttle' => \App\Filters\RateLimitFilter::class,
];

// app/Config/Routes.php
$routes->group('api', ['filter' => 'throttle:100'], static function ($routes) {
    $routes->resource('orders');
});
```

## Detection Patterns

```bash
# Cache in Domain (VIOLATION)
Grep: "use CodeIgniter\\Cache" --glob "**/Domain/**/*.php"
Grep: "cache\(|service\('cache'\)" --glob "**/Domain/**/*.php"

# HTTP Client in Domain (VIOLATION)
Grep: "use CodeIgniter\\HTTP\\CURLRequest" --glob "**/Domain/**/*.php"
Grep: "service\('curlrequest'\)" --glob "**/Domain/**/*.php"

# Email in Domain (VIOLATION)
Grep: "service\('email'\)" --glob "**/Domain/**/*.php"

# Cache in Application (should use domain port)
Grep: "use CodeIgniter\\Cache" --glob "**/Application/**/*.php"

# HTTP Client in Application (should use domain port)
Grep: "use CodeIgniter\\HTTP\\CURLRequest" --glob "**/Application/**/*.php"

# Good: Domain ports exist
Grep: "CacheInterface|PaymentGatewayInterface|NotificationSenderInterface" --glob "**/Domain/**/*.php"

# Throttler usage
Grep: "throttle\|Throttler" --glob "app/Config/**/*.php" --output_mode count
```

## Summary Table

| Component | DDD Layer | CI4 Class | Integration Pattern |
|-----------|-----------|-----------|---------------------|
| Cache | Domain: OrderCacheInterface port | `CacheInterface` (service('cache')) | Infrastructure CIOrderCache adapter |
| HTTP Client | Domain: PaymentGatewayInterface port | `CURLRequest` (service('curlrequest')) | Infrastructure CIPaymentGateway adapter |
| Email | Domain: NotificationSenderInterface port | `Email` (service('email')) | Infrastructure CIEmailNotificationSender |
| Rate Limiting | Presentation: Filter | `Throttler` (service('throttler')) | RateLimitFilter on routes |
| File Storage | Domain: FileStorageInterface port | `Filesystem` | Infrastructure adapter |
