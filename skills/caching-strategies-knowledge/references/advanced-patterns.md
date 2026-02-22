# Advanced Caching Patterns Reference

## Cache Stampede Prevention Deep Dive

### Locking (Mutex) Pattern

When a cache key expires, only one process recomputes while others wait:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class StampedeSafeCache
{
    public function __construct(
        private \Redis $redis,
        private int $lockTtlSeconds = 10,
        private int $waitIntervalUs = 50_000,
        private int $maxWaitAttempts = 100,
    ) {}

    public function getOrCompute(string $key, callable $compute, int $ttl): mixed
    {
        $value = $this->redis->get($key);
        if ($value !== false) {
            return unserialize($value);
        }

        $lockKey = sprintf('lock:%s', $key);

        if ($this->redis->set($lockKey, '1', ['NX', 'EX' => $this->lockTtlSeconds])) {
            try {
                $result = $compute();
                $this->redis->setex($key, $ttl, serialize($result));
                return $result;
            } finally {
                $this->redis->del($lockKey);
            }
        }

        for ($i = 0; $i < $this->maxWaitAttempts; $i++) {
            usleep($this->waitIntervalUs);
            $value = $this->redis->get($key);
            if ($value !== false) {
                return unserialize($value);
            }
        }

        return $compute();
    }
}
```

### Probabilistic Early Expiry (XFetch)

Recompute before TTL expires with increasing probability as expiry approaches:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class XFetchCache
{
    public function __construct(
        private \Redis $redis,
        private float $beta = 1.0,
    ) {}

    public function get(string $key, callable $compute, int $ttl): mixed
    {
        $raw = $this->redis->get($key);

        if ($raw !== false) {
            $entry = unserialize($raw);
            $remaining = $entry['deadline'] - microtime(true);
            $threshold = $entry['delta'] * $this->beta * log(mt_rand(1, PHP_INT_MAX) / PHP_INT_MAX);

            if ($remaining + $threshold > 0) {
                return $entry['value'];
            }
        }

        $start = microtime(true);
        $value = $compute();
        $delta = microtime(true) - $start;

        $entry = [
            'value' => $value,
            'delta' => $delta,
            'deadline' => microtime(true) + $ttl,
        ];

        $this->redis->setex($key, $ttl + 60, serialize($entry));

        return $value;
    }
}
```

### Stale-While-Revalidate

Serve stale data while asynchronously refreshing:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Psr\SimpleCache\CacheInterface;

final readonly class StaleWhileRevalidateCache
{
    public function __construct(
        private CacheInterface $cache,
        private int $softTtl,
        private int $hardTtl,
    ) {}

    public function get(string $key, callable $compute): mixed
    {
        $entry = $this->cache->get($key);

        if ($entry === null) {
            return $this->recompute($key, $compute);
        }

        if ($entry['soft_expiry'] < time()) {
            $this->scheduleRecompute($key, $compute);
        }

        return $entry['value'];
    }

    private function recompute(string $key, callable $compute): mixed
    {
        $value = $compute();
        $this->cache->set($key, [
            'value' => $value,
            'soft_expiry' => time() + $this->softTtl,
        ], $this->hardTtl);

        return $value;
    }

    private function scheduleRecompute(string $key, callable $compute): void
    {
        if (function_exists('fastcgi_finish_request')) {
            register_shutdown_function(fn() => $this->recompute($key, $compute));
        }
    }
}
```

## Cache Warming Strategies

### Access-Pattern-Based Warming

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class AccessPatternWarmer
{
    public function __construct(
        private \Redis $redis,
        private CacheInterface $cache,
    ) {}

    public function recordAccess(string $key): void
    {
        $this->redis->zIncrBy('cache:access_frequency', 1, $key);
    }

    public function warmTopKeys(int $limit = 500): int
    {
        $topKeys = $this->redis->zRevRange('cache:access_frequency', 0, $limit - 1);
        $warmed = 0;

        foreach ($topKeys as $key) {
            if (!$this->cache->has($key)) {
                $value = $this->loadFromSource($key);
                if ($value !== null) {
                    $this->cache->set($key, $value);
                    $warmed++;
                }
            }
        }

        return $warmed;
    }
}
```

## Write-Back vs Write-Through Deep Comparison

| Aspect | Write-Through | Write-Back (Write-Behind) |
|--------|---------------|---------------------------|
| Write latency | Higher (sync DB write) | Lower (cache only) |
| Data safety | Safe (DB always updated) | Risk of data loss on crash |
| Consistency | Strong | Eventual |
| DB load | Per-write | Batched, lower load |
| Implementation | Simple | Complex (needs queue/buffer) |
| Use case | Financial, orders | Analytics, counters, logs |
| Recovery | Trivial (DB is truth) | Complex (replay buffer) |

### Write-Through with Retry

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class WriteThroughWithRetry
{
    public function __construct(
        private CacheInterface $cache,
        private RepositoryInterface $repository,
        private int $maxRetries = 3,
    ) {}

    public function write(string $key, mixed $value): void
    {
        $this->repository->save($key, $value);
        $this->cache->set($key, $value);
    }
}
```

## Distributed Cache Coherence

### Pub/Sub Invalidation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class PubSubCacheInvalidator
{
    private const string CHANNEL = 'cache:invalidation';

    public function __construct(
        private \Redis $redis,
        private CacheInterface $localCache,
    ) {}

    public function invalidate(string $key): void
    {
        $this->localCache->delete($key);
        $this->redis->publish(self::CHANNEL, json_encode([
            'key' => $key,
            'node' => gethostname(),
            'timestamp' => microtime(true),
        ]));
    }

    public function listen(): void
    {
        $this->redis->subscribe([self::CHANNEL], function (string $channel, string $message): void {
            $data = json_decode($message, true);
            if ($data['node'] !== gethostname()) {
                $this->localCache->delete($data['key']);
            }
        });
    }
}
```

### Multi-Node Consistency Strategies

| Strategy | Consistency | Latency | Complexity |
|----------|-------------|---------|------------|
| TTL only | Eventual (stale window) | None | Low |
| Pub/Sub invalidation | Near-real-time | ~1-5ms | Medium |
| Write-through all nodes | Strong | High | High |
| Version-based (ETag) | Strong (on read) | Per-read check | Medium |
| Lease-based | Strong | Lock overhead | High |

## Cache Key Design Patterns

### Hierarchical Keys

```
entity:{type}:{id}                    → user:123
entity:{type}:{id}:{field}            → user:123:profile
collection:{type}:{filters}:{page}    → products:category=5:page=1
computed:{operation}:{params_hash}     → report:monthly:abc123
```

### Key Versioning

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class VersionedCacheKey
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function key(string $base): string
    {
        $version = $this->redis->get(sprintf('version:%s', $base)) ?: '1';
        return sprintf('%s:v%s', $base, $version);
    }

    public function invalidate(string $base): void
    {
        $this->redis->incr(sprintf('version:%s', $base));
    }
}
```
