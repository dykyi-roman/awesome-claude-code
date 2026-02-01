# Rate Limiter Examples

## API Rate Limiting Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Infrastructure\Resilience\RateLimiter\RateLimiterInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class RateLimitMiddleware implements MiddlewareInterface
{
    public function __construct(
        private RateLimiterInterface $rateLimiter,
        private ResponseFactoryInterface $responseFactory
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        $key = $this->resolveKey($request);
        $result = $this->rateLimiter->attempt($key);

        if ($result->isDenied()) {
            $response = $this->responseFactory->createResponse(429);
            foreach ($result->toHeaders() as $name => $value) {
                $response = $response->withHeader($name, (string) $value);
            }
            return $response;
        }

        $response = $handler->handle($request);

        foreach ($result->toHeaders() as $name => $value) {
            $response = $response->withHeader($name, (string) $value);
        }

        return $response;
    }

    private function resolveKey(ServerRequestInterface $request): string
    {
        $userId = $request->getAttribute('user_id');
        if ($userId !== null) {
            return sprintf('user:%s', $userId);
        }

        return sprintf('ip:%s', $request->getServerParams()['REMOTE_ADDR'] ?? 'unknown');
    }
}
```

---

## Per-User Rate Limiting

```php
<?php

declare(strict_types=1);

namespace Application\RateLimiting;

use Infrastructure\Resilience\RateLimiter\TokenBucketRateLimiter;
use Infrastructure\Resilience\RateLimiter\RateLimitExceededException;

final readonly class ApiRateLimiter
{
    public function __construct(
        private TokenBucketRateLimiter $limiter
    ) {}

    public function checkLimit(string $userId, string $action): void
    {
        $key = sprintf('%s:%s', $userId, $action);
        $result = $this->limiter->attempt($key);

        if ($result->isDenied()) {
            throw new RateLimitExceededException(
                key: $key,
                limit: $result->limit,
                retryAfterSeconds: $result->retryAfterSeconds ?? 60
            );
        }
    }
}
```

---

## Unit Tests

### TokenBucketRateLimiterTest

**File:** `tests/Unit/Infrastructure/Resilience/RateLimiter/TokenBucketRateLimiterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\RateLimiter;

use Infrastructure\Resilience\RateLimiter\TokenBucketRateLimiter;
use Infrastructure\Resilience\RateLimiter\StorageInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Clock\ClockInterface;

#[Group('unit')]
#[CoversClass(TokenBucketRateLimiter::class)]
final class TokenBucketRateLimiterTest extends TestCase
{
    private ClockInterface $clock;
    private StorageInterface $storage;

    protected function setUp(): void
    {
        $this->clock = new class implements ClockInterface {
            public int $time;
            public function __construct() { $this->time = time(); }
            public function now(): \DateTimeImmutable {
                return (new \DateTimeImmutable())->setTimestamp($this->time);
            }
        };

        $this->storage = new class implements StorageInterface {
            private array $data = [];
            public function get(string $key): mixed { return $this->data[$key] ?? null; }
            public function set(string $key, mixed $value, ?int $ttl = null): void { $this->data[$key] = $value; }
            public function delete(string $key): void { unset($this->data[$key]); }
            public function increment(string $key, int $amount = 1): int {
                $this->data[$key] = ($this->data[$key] ?? 0) + $amount;
                return $this->data[$key];
            }
        };
    }

    public function testAllowsRequestsWithinCapacity(): void
    {
        $limiter = new TokenBucketRateLimiter(
            capacity: 10,
            refillRate: 1.0,
            clock: $this->clock,
            storage: $this->storage
        );

        $result = $limiter->attempt('test-key');

        self::assertTrue($result->isAllowed());
        self::assertSame(9, $result->remainingTokens);
    }

    public function testDeniesWhenBucketEmpty(): void
    {
        $limiter = new TokenBucketRateLimiter(
            capacity: 2,
            refillRate: 0.1,
            clock: $this->clock,
            storage: $this->storage
        );

        $limiter->attempt('test-key');
        $limiter->attempt('test-key');
        $result = $limiter->attempt('test-key');

        self::assertTrue($result->isDenied());
        self::assertGreaterThan(0, $result->retryAfterSeconds);
    }

    public function testRefillsTokensOverTime(): void
    {
        $limiter = new TokenBucketRateLimiter(
            capacity: 10,
            refillRate: 1.0,
            clock: $this->clock,
            storage: $this->storage
        );

        for ($i = 0; $i < 10; $i++) {
            $limiter->attempt('test-key');
        }

        self::assertSame(0, $limiter->getRemainingTokens('test-key'));

        $this->clock->time += 5;

        self::assertSame(5, $limiter->getRemainingTokens('test-key'));
    }

    public function testResetRestoresFullCapacity(): void
    {
        $limiter = new TokenBucketRateLimiter(
            capacity: 10,
            refillRate: 1.0,
            clock: $this->clock,
            storage: $this->storage
        );

        for ($i = 0; $i < 10; $i++) {
            $limiter->attempt('test-key');
        }

        $limiter->reset('test-key');

        self::assertSame(10, $limiter->getRemainingTokens('test-key'));
    }
}
```

### RateLimitResultTest

**File:** `tests/Unit/Infrastructure/Resilience/RateLimiter/RateLimitResultTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\RateLimiter;

use Infrastructure\Resilience\RateLimiter\RateLimitResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(RateLimitResult::class)]
final class RateLimitResultTest extends TestCase
{
    public function testAllowedResult(): void
    {
        $resetsAt = new \DateTimeImmutable('+1 hour');
        $result = RateLimitResult::allowed(5, 10, $resetsAt);

        self::assertTrue($result->isAllowed());
        self::assertFalse($result->isDenied());
        self::assertSame(5, $result->remainingTokens);
        self::assertSame(10, $result->limit);
    }

    public function testDeniedResult(): void
    {
        $resetsAt = new \DateTimeImmutable('+30 seconds');
        $result = RateLimitResult::denied(10, 30, $resetsAt);

        self::assertFalse($result->isAllowed());
        self::assertTrue($result->isDenied());
        self::assertSame(0, $result->remainingTokens);
        self::assertSame(30, $result->retryAfterSeconds);
    }

    public function testToHeadersIncludesAllFields(): void
    {
        $resetsAt = new \DateTimeImmutable('+1 hour');
        $result = RateLimitResult::denied(100, 60, $resetsAt);

        $headers = $result->toHeaders();

        self::assertSame(100, $headers['X-RateLimit-Limit']);
        self::assertSame(0, $headers['X-RateLimit-Remaining']);
        self::assertSame(60, $headers['Retry-After']);
    }
}
```
