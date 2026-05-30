# Rate Limiting Pattern Reference

## Algorithm Comparison

```
┌─────────────────────────────────────────────────────────────────┐
│                   RATE LIMITING ALGORITHMS                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Requests                                                       │
│    │                                                             │
│    │   Token Bucket           Sliding Window                     │
│    │   ┌──┐                   ────────────                       │
│    │   │  │ burst             Smooth rate                        │
│    │   │  │ allowed           enforcement                        │
│    │───┤  ├──────── limit     ─────────────── limit              │
│    │   │  │                                                      │
│    │   └──┘                                                      │
│    └────────────▶ Time        └──────────────▶ Time              │
│                                                                  │
│   Fixed Window                Leaky Bucket                       │
│   ┌────┐┌────┐                ════════════                       │
│   │    ││    │                Constant rate                       │
│   │    ││    │ edge           output, queue                      │
│   │────┘└────│── burst        ─────────────── limit              │
│   │    ││    │                                                    │
│   └────┘└────┘                                                   │
│   └────────────▶ Time         └──────────────▶ Time              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Token Bucket Implementation

```php
<?php

declare(strict_types=1);

namespace RateLimiter;

final class TokenBucketRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly \Redis $redis,
        private readonly string $prefix = 'rate_limiter:'
    ) {}

    public function attempt(string $key, int $capacity, float $refillRate): RateLimitResult
    {
        $redisKey = $this->prefix . $key;
        $now = microtime(true);

        $data = $this->redis->hGetAll($redisKey);
        $tokens = (float)($data['tokens'] ?? $capacity);
        $lastRefill = (float)($data['last_refill'] ?? $now);

        // Refill tokens based on elapsed time
        $elapsed = $now - $lastRefill;
        $tokens = min($capacity, $tokens + ($elapsed * $refillRate));

        $allowed = $tokens >= 1.0;
        if ($allowed) {
            $tokens -= 1.0;
        }

        $this->redis->hMSet($redisKey, [
            'tokens' => (string)$tokens,
            'last_refill' => (string)$now,
        ]);
        $this->redis->expire($redisKey, (int)ceil($capacity / $refillRate) + 1);

        return new RateLimitResult(
            allowed: $allowed,
            limit: $capacity,
            remaining: (int)floor($tokens),
            retryAfterSeconds: $allowed ? 0 : (int)ceil(1.0 / $refillRate),
        );
    }
}
```

## Sliding Window Implementation

```php
<?php

declare(strict_types=1);

namespace RateLimiter;

final class SlidingWindowRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly \Redis $redis,
        private readonly string $prefix = 'sliding_window:'
    ) {}

    public function attempt(string $key, int $limit, int $windowSeconds): RateLimitResult
    {
        $redisKey = $this->prefix . $key;
        $now = microtime(true);
        $windowStart = $now - $windowSeconds;

        // Atomic operation using Redis sorted set
        $pipe = $this->redis->multi(\Redis::PIPELINE);
        $pipe->zRemRangeByScore($redisKey, '-inf', (string)$windowStart);
        $pipe->zCard($redisKey);
        $pipe->zAdd($redisKey, $now, (string)$now . ':' . random_int(0, PHP_INT_MAX));
        $pipe->expire($redisKey, $windowSeconds + 1);
        $results = $pipe->exec();

        $currentCount = (int)$results[1];
        $allowed = $currentCount < $limit;

        if (!$allowed) {
            $this->redis->zRemRangeByScore($redisKey, (string)$now, (string)$now);
        }

        return new RateLimitResult(
            allowed: $allowed,
            limit: $limit,
            remaining: max(0, $limit - $currentCount - ($allowed ? 1 : 0)),
            retryAfterSeconds: $allowed ? 0 : $windowSeconds,
        );
    }
}
```

## Fixed Window and Leaky Bucket

```php
<?php

declare(strict_types=1);

namespace RateLimiter;

final class FixedWindowRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly \Redis $redis,
        private readonly string $prefix = 'fixed_window:'
    ) {}

    public function attempt(string $key, int $limit, int $windowSeconds): RateLimitResult
    {
        $window = (int)(time() / $windowSeconds);
        $redisKey = $this->prefix . $key . ':' . $window;

        $count = $this->redis->incr($redisKey);
        if ($count === 1) {
            $this->redis->expire($redisKey, $windowSeconds);
        }

        $allowed = $count <= $limit;
        $resetAt = ($window + 1) * $windowSeconds;

        return new RateLimitResult(
            allowed: $allowed,
            limit: $limit,
            remaining: max(0, $limit - $count),
            retryAfterSeconds: $allowed ? 0 : $resetAt - time(),
        );
    }
}

final readonly class LeakyBucketRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private \Redis $redis,
        private string $prefix = 'leaky_bucket:'
    ) {}

    public function attempt(string $key, int $capacity, float $leakRate): RateLimitResult
    {
        $redisKey = $this->prefix . $key;
        $now = microtime(true);

        $data = $this->redis->hGetAll($redisKey);
        $level = (float)($data['level'] ?? 0);
        $lastLeak = (float)($data['last_leak'] ?? $now);

        // Leak tokens based on elapsed time
        $elapsed = $now - $lastLeak;
        $level = max(0, $level - ($elapsed * $leakRate));

        $allowed = $level < $capacity;
        if ($allowed) {
            $level += 1.0;
        }

        $this->redis->hMSet($redisKey, [
            'level' => (string)$level,
            'last_leak' => (string)$now,
        ]);
        $this->redis->expire($redisKey, (int)ceil($capacity / $leakRate) + 1);

        return new RateLimitResult(
            allowed: $allowed,
            limit: $capacity,
            remaining: (int)floor($capacity - $level),
            retryAfterSeconds: $allowed ? 0 : (int)ceil(1.0 / $leakRate),
        );
    }
}
```

## Rate Limit Result and Interface

```php
<?php

declare(strict_types=1);

namespace RateLimiter;

interface RateLimiterInterface
{
    public function attempt(string $key, int ...$params): RateLimitResult;
}

final readonly class RateLimitResult
{
    public function __construct(
        public bool $allowed,
        public int $limit,
        public int $remaining,
        public int $retryAfterSeconds,
    ) {}
}
```

## PSR-15 Rate Limit Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use RateLimiter\RateLimiterInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class RateLimitMiddleware implements MiddlewareInterface
{
    public function __construct(
        private RateLimiterInterface $rateLimiter,
        private ResponseFactoryInterface $responseFactory,
        private KeyResolverInterface $keyResolver,
        private int $limit = 100,
        private int $windowSeconds = 60,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        $key = $this->keyResolver->resolve($request);
        $result = $this->rateLimiter->attempt($key, $this->limit, $this->windowSeconds);

        if (!$result->allowed) {
            $response = $this->responseFactory->createResponse(429);
            return $this->addHeaders($response, $result);
        }

        $response = $handler->handle($request);

        return $this->addHeaders($response, $result);
    }

    private function addHeaders(ResponseInterface $response, $result): ResponseInterface
    {
        return $response
            ->withHeader('X-RateLimit-Limit', (string)$result->limit)
            ->withHeader('X-RateLimit-Remaining', (string)$result->remaining)
            ->withHeader('X-RateLimit-Reset', (string)(time() + $result->retryAfterSeconds))
            ->withHeader('Retry-After', (string)$result->retryAfterSeconds);
    }
}
```

## Key Resolution Strategies

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Psr\Http\Message\ServerRequestInterface;

interface KeyResolverInterface
{
    public function resolve(ServerRequestInterface $request): string;
}

// Rate limit per IP address
final readonly class IpKeyResolver implements KeyResolverInterface
{
    public function resolve(ServerRequestInterface $request): string
    {
        $params = $request->getServerParams();
        $ip = $params['HTTP_X_FORWARDED_FOR'] ?? $params['REMOTE_ADDR'] ?? 'unknown';
        return 'ip:' . $ip;
    }
}

// Rate limit per API key
final readonly class ApiKeyResolver implements KeyResolverInterface
{
    public function resolve(ServerRequestInterface $request): string
    {
        $apiKey = $request->getHeaderLine('X-API-Key');
        return 'api_key:' . ($apiKey ?: 'anonymous');
    }
}

// Rate limit per user + endpoint
final readonly class UserEndpointKeyResolver implements KeyResolverInterface
{
    public function resolve(ServerRequestInterface $request): string
    {
        $userId = $request->getAttribute('user_id', 'anonymous');
        $endpoint = $request->getMethod() . ':' . $request->getUri()->getPath();
        return 'user_endpoint:' . $userId . ':' . $endpoint;
    }
}
```

## Detection Patterns

```bash
# Find rate limiter implementations
Grep: "RateLimiter|TokenBucket|SlidingWindow|LeakyBucket" --glob "**/*.php"

# Find middleware with rate limiting
Grep: "RateLimit|throttle|X-RateLimit" --glob "**/Middleware/**/*.php"

# Detect missing rate limiting on controllers
Grep: "#\[Route\(|#\[Get\(|#\[Post\(" --glob "**/Controller/**/*.php"

# Check for in-memory-only limiters (anti-pattern in multi-instance)
Grep: "class.*RateLimiter(?!.*Redis|.*\\\\Redis)" --glob "**/*.php"
```

## Configuration Example

```php
<?php

// DI container wiring
$container->set(RateLimiterInterface::class, function () use ($redis) {
    return new SlidingWindowRateLimiter(
        redis: $redis,
        prefix: 'app:rate_limit:',
    );
});

// Tiered rate limits per authentication level
$container->set('rate_limit.public', fn() => new RateLimitMiddleware(
    rateLimiter: $container->get(RateLimiterInterface::class),
    responseFactory: $container->get(ResponseFactoryInterface::class),
    keyResolver: new IpKeyResolver(),
    limit: 60,
    windowSeconds: 60,
));

$container->set('rate_limit.authenticated', fn() => new RateLimitMiddleware(
    rateLimiter: $container->get(RateLimiterInterface::class),
    responseFactory: $container->get(ResponseFactoryInterface::class),
    keyResolver: new ApiKeyResolver(),
    limit: 1000,
    windowSeconds: 60,
));

$container->set('rate_limit.admin', fn() => new RateLimitMiddleware(
    rateLimiter: $container->get(RateLimiterInterface::class),
    responseFactory: $container->get(ResponseFactoryInterface::class),
    keyResolver: new UserEndpointKeyResolver(),
    limit: 10000,
    windowSeconds: 60,
));
```

## DDD Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Domain Layer                 Application Layer                 │
│   ┌──────────────────┐        ┌─────────────────────────┐       │
│   │ RateLimitPort    │◀───────│ UseCase                 │       │
│   │ (interface)      │        │ uses port for checking  │       │
│   └──────────────────┘        └─────────────────────────┘       │
│            ▲                                                     │
│            │ implements                                          │
│   Infrastructure Layer                                           │
│   ┌──────────────────┐                                          │
│   │ RedisRateLimiter │                                          │
│   │ (adapter)        │                                          │
│   └──────────────────┘                                          │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

Rate limiting is an Infrastructure concern. The Domain layer defines a port (interface) if business logic needs to check rate limits. The concrete implementation (Redis, APCu) lives in Infrastructure and is injected via the DI container.

## Anti-patterns

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No rate limiting on public APIs | DDoS, abuse, cost overrun | Always rate limit public endpoints |
| In-memory only (multi-instance) | Each instance has separate counters | Use Redis for shared state |
| Single limit for all users | Power users blocked, abusers unthrottled | Tiered limits per auth level |
| No Retry-After header | Clients retry immediately | Include Retry-After in 429 response |
| Fixed window only | Edge-of-window burst allows 2x rate | Use sliding window or token bucket |
| Rate limit in domain layer | Infrastructure leak | Keep in middleware/infrastructure |

## Summary

| Algorithm | Use Case | Pros | Cons |
|-----------|----------|------|------|
| **Token Bucket** | General API limiting | Allows controlled bursts, simple | Burst can overwhelm downstream |
| **Fixed Window** | Simple counters, dashboards | Very simple, low memory | Edge bursts allow 2x rate |
| **Sliding Window** | Precise rate enforcement | No edge bursts, accurate | Higher memory (sorted set) |
| **Leaky Bucket** | Constant throughput needed | Smooth output, no bursts | Rejects bursty but valid traffic |
