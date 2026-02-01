# Rate Limiter Templates

## RateLimiterInterface

**File:** `src/Infrastructure/Resilience/RateLimiter/RateLimiterInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

interface RateLimiterInterface
{
    public function attempt(string $key, int $tokens = 1): RateLimitResult;

    public function getRemainingTokens(string $key): int;

    public function getRetryAfter(string $key): ?int;

    public function reset(string $key): void;
}
```

---

## RateLimitResult Value Object

**File:** `src/Infrastructure/Resilience/RateLimiter/RateLimitResult.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

final readonly class RateLimitResult
{
    private function __construct(
        public bool $allowed,
        public int $remainingTokens,
        public int $limit,
        public ?int $retryAfterSeconds = null,
        public ?\DateTimeImmutable $resetsAt = null
    ) {}

    public static function allowed(int $remaining, int $limit, \DateTimeImmutable $resetsAt): self
    {
        return new self(
            allowed: true,
            remainingTokens: $remaining,
            limit: $limit,
            resetsAt: $resetsAt
        );
    }

    public static function denied(int $limit, int $retryAfter, \DateTimeImmutable $resetsAt): self
    {
        return new self(
            allowed: false,
            remainingTokens: 0,
            limit: $limit,
            retryAfterSeconds: $retryAfter,
            resetsAt: $resetsAt
        );
    }

    public function isAllowed(): bool
    {
        return $this->allowed;
    }

    public function isDenied(): bool
    {
        return !$this->allowed;
    }

    /** @return array<string, string|int> */
    public function toHeaders(): array
    {
        $headers = [
            'X-RateLimit-Limit' => $this->limit,
            'X-RateLimit-Remaining' => $this->remainingTokens,
        ];

        if ($this->resetsAt !== null) {
            $headers['X-RateLimit-Reset'] = $this->resetsAt->getTimestamp();
        }

        if ($this->retryAfterSeconds !== null) {
            $headers['Retry-After'] = $this->retryAfterSeconds;
        }

        return $headers;
    }
}
```

---

## RateLimitExceededException

**File:** `src/Infrastructure/Resilience/RateLimiter/RateLimitExceededException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

final class RateLimitExceededException extends \RuntimeException
{
    public function __construct(
        public readonly string $key,
        public readonly int $limit,
        public readonly int $retryAfterSeconds
    ) {
        parent::__construct(
            sprintf('Rate limit exceeded for "%s". Retry after %d seconds.', $key, $retryAfterSeconds)
        );
    }
}
```

---

## TokenBucketRateLimiter

**File:** `src/Infrastructure/Resilience/RateLimiter/TokenBucketRateLimiter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

use Psr\Clock\ClockInterface;

final class TokenBucketRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly int $capacity,
        private readonly float $refillRate,
        private readonly ClockInterface $clock,
        private readonly StorageInterface $storage
    ) {}

    public function attempt(string $key, int $tokens = 1): RateLimitResult
    {
        $bucket = $this->getBucket($key);
        $now = $this->clock->now()->getTimestamp();

        $elapsed = $now - $bucket['lastRefill'];
        $refilled = $bucket['tokens'] + ($elapsed * $this->refillRate);
        $currentTokens = min($this->capacity, $refilled);

        if ($currentTokens >= $tokens) {
            $newTokens = $currentTokens - $tokens;
            $this->saveBucket($key, $newTokens, $now);

            return RateLimitResult::allowed(
                remaining: (int) $newTokens,
                limit: $this->capacity,
                resetsAt: $this->calculateResetTime($now, $newTokens)
            );
        }

        $tokensNeeded = $tokens - $currentTokens;
        $retryAfter = (int) ceil($tokensNeeded / $this->refillRate);

        return RateLimitResult::denied(
            limit: $this->capacity,
            retryAfter: $retryAfter,
            resetsAt: $this->clock->now()->modify("+{$retryAfter} seconds")
        );
    }

    public function getRemainingTokens(string $key): int
    {
        $bucket = $this->getBucket($key);
        $now = $this->clock->now()->getTimestamp();

        $elapsed = $now - $bucket['lastRefill'];
        $currentTokens = $bucket['tokens'] + ($elapsed * $this->refillRate);

        return (int) min($this->capacity, $currentTokens);
    }

    public function getRetryAfter(string $key): ?int
    {
        $remaining = $this->getRemainingTokens($key);
        return $remaining > 0 ? null : (int) ceil(1 / $this->refillRate);
    }

    public function reset(string $key): void
    {
        $now = $this->clock->now()->getTimestamp();
        $this->saveBucket($key, (float) $this->capacity, $now);
    }
}
```

---

## SlidingWindowRateLimiter

**File:** `src/Infrastructure/Resilience/RateLimiter/SlidingWindowRateLimiter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

use Psr\Clock\ClockInterface;

final class SlidingWindowRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly int $limit,
        private readonly int $windowSeconds,
        private readonly ClockInterface $clock,
        private readonly StorageInterface $storage
    ) {}

    public function attempt(string $key, int $tokens = 1): RateLimitResult
    {
        $now = $this->clock->now()->getTimestamp();
        $windowStart = $now - $this->windowSeconds;

        $requests = $this->getRequests($key);
        $requests = array_filter($requests, fn(int $time) => $time > $windowStart);

        if (count($requests) + $tokens <= $this->limit) {
            for ($i = 0; $i < $tokens; $i++) {
                $requests[] = $now;
            }
            $this->saveRequests($key, $requests);

            $oldestRequest = min($requests);
            $resetsAt = (new \DateTimeImmutable())->setTimestamp($oldestRequest + $this->windowSeconds);

            return RateLimitResult::allowed(
                remaining: $this->limit - count($requests),
                limit: $this->limit,
                resetsAt: $resetsAt
            );
        }

        $oldestRequest = min($requests);
        $retryAfter = ($oldestRequest + $this->windowSeconds) - $now;

        return RateLimitResult::denied(
            limit: $this->limit,
            retryAfter: max(1, $retryAfter),
            resetsAt: (new \DateTimeImmutable())->setTimestamp($oldestRequest + $this->windowSeconds)
        );
    }
}
```

---

## FixedWindowRateLimiter

**File:** `src/Infrastructure/Resilience/RateLimiter/FixedWindowRateLimiter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

use Psr\Clock\ClockInterface;

final class FixedWindowRateLimiter implements RateLimiterInterface
{
    public function __construct(
        private readonly int $limit,
        private readonly int $windowSeconds,
        private readonly ClockInterface $clock,
        private readonly StorageInterface $storage
    ) {}

    public function attempt(string $key, int $tokens = 1): RateLimitResult
    {
        $now = $this->clock->now()->getTimestamp();
        $windowKey = $this->getWindowKey($key, $now);

        $window = $this->getWindow($windowKey);
        $windowEnd = $window['start'] + $this->windowSeconds;
        $resetsAt = (new \DateTimeImmutable())->setTimestamp($windowEnd);

        if ($window['count'] + $tokens <= $this->limit) {
            $newCount = $window['count'] + $tokens;
            $this->saveWindow($windowKey, $window['start'], $newCount);

            return RateLimitResult::allowed(
                remaining: $this->limit - $newCount,
                limit: $this->limit,
                resetsAt: $resetsAt
            );
        }

        return RateLimitResult::denied(
            limit: $this->limit,
            retryAfter: max(1, $windowEnd - $now),
            resetsAt: $resetsAt
        );
    }
}
```

---

## StorageInterface

**File:** `src/Infrastructure/Resilience/RateLimiter/StorageInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

interface StorageInterface
{
    public function get(string $key): mixed;

    public function set(string $key, mixed $value, ?int $ttlSeconds = null): void;

    public function delete(string $key): void;

    public function increment(string $key, int $amount = 1): int;
}
```

---

## RedisStorage Implementation

**File:** `src/Infrastructure/Resilience/RateLimiter/RedisStorage.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\RateLimiter;

final readonly class RedisStorage implements StorageInterface
{
    private const PREFIX = 'rate_limit:';

    public function __construct(
        private \Redis $redis
    ) {}

    public function get(string $key): mixed
    {
        $value = $this->redis->get(self::PREFIX . $key);
        if ($value === false) {
            return null;
        }

        return json_decode($value, true);
    }

    public function set(string $key, mixed $value, ?int $ttlSeconds = null): void
    {
        $serialized = json_encode($value);

        if ($ttlSeconds !== null) {
            $this->redis->setex(self::PREFIX . $key, $ttlSeconds, $serialized);
        } else {
            $this->redis->set(self::PREFIX . $key, $serialized);
        }
    }

    public function delete(string $key): void
    {
        $this->redis->del(self::PREFIX . $key);
    }

    public function increment(string $key, int $amount = 1): int
    {
        return $this->redis->incrBy(self::PREFIX . $key, $amount);
    }
}
```
