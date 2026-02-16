# Caching Strategies Reference

## Cache-Aside (Lazy Loading)

### How It Works

1. Application checks cache for requested data
2. On cache hit: return cached data
3. On cache miss: fetch from database, store in cache, return

### Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class CacheAsideRepository implements ProductReadRepositoryInterface
{
    public function __construct(
        private ProductRepositoryInterface $repository,
        private CacheInterface $cache,
        private int $ttlSeconds = 300,
    ) {}

    public function findById(ProductId $id): ?Product
    {
        $key = sprintf('product:%s', $id->toString());

        $cached = $this->cache->get($key);
        if ($cached !== null) {
            return $cached;
        }

        $product = $this->repository->findById($id);
        if ($product !== null) {
            $this->cache->set($key, $product, $this->ttlSeconds);
        }

        return $product;
    }
}
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Simple to implement | Stale data between TTL and invalidation |
| Only caches accessed data | Cache miss penalty (cold start) |
| Resilient to cache failure | Application manages cache logic |

## Read-Through

### How It Works

1. Application reads from cache (cache is primary interface)
2. Cache itself fetches from database on miss
3. Application never touches database directly for reads

### Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class ReadThroughCache implements CacheInterface
{
    public function __construct(
        private CacheInterface $innerCache,
        private DataLoaderInterface $dataLoader,
        private int $ttlSeconds = 300,
    ) {}

    public function get(string $key): mixed
    {
        $value = $this->innerCache->get($key);

        if ($value === null) {
            $value = $this->dataLoader->load($key);
            if ($value !== null) {
                $this->innerCache->set($key, $value, $this->ttlSeconds);
            }
        }

        return $value;
    }
}
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Application logic simplified | Cache library must support data loading |
| Cache manages consistency | Tighter coupling with data source |
| Uniform read interface | Less control over loading strategy |

## Write-Through

### How It Works

1. Application writes to cache
2. Cache synchronously writes to database
3. Write only succeeds if both cache and database succeed

### Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class WriteThroughRepository implements ProductRepositoryInterface
{
    public function __construct(
        private ProductRepositoryInterface $dbRepository,
        private CacheInterface $cache,
    ) {}

    public function save(Product $product): void
    {
        // Write to database first
        $this->dbRepository->save($product);

        // Update cache (synchronous)
        $key = sprintf('product:%s', $product->id()->toString());
        $this->cache->set($key, $product);
    }
}
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Cache always up-to-date | Higher write latency (double write) |
| Read-after-write consistency | Writes cached data even if not read |
| Simple consistency model | Requires transactional guarantee |

## Write-Behind (Write-Back)

### How It Works

1. Application writes to cache only
2. Cache asynchronously flushes to database in batches
3. Database may lag behind cache

### Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final class WriteBehindBuffer
{
    /** @var array<string, mixed> */
    private array $pendingWrites = [];

    public function __construct(
        private readonly CacheInterface $cache,
        private readonly DataWriterInterface $writer,
        private readonly int $batchSize = 100,
        private readonly int $flushIntervalMs = 1000,
    ) {}

    public function write(string $key, mixed $value): void
    {
        $this->cache->set($key, $value);
        $this->pendingWrites[$key] = $value;

        if (count($this->pendingWrites) >= $this->batchSize) {
            $this->flush();
        }
    }

    public function flush(): void
    {
        if (empty($this->pendingWrites)) {
            return;
        }

        $batch = $this->pendingWrites;
        $this->pendingWrites = [];

        $this->writer->writeBatch($batch);
    }
}
```

### Pros and Cons

| Pros | Cons |
|------|------|
| Fastest write performance | Risk of data loss on cache failure |
| Batch writes reduce DB load | Complex implementation |
| Absorbs write spikes | Eventual consistency |

## Cache Warming Strategies

### Preload on Startup

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class CacheWarmer
{
    public function __construct(
        private CacheInterface $cache,
        private ProductRepositoryInterface $repository,
    ) {}

    public function warmPopularProducts(int $limit = 1000): void
    {
        $products = $this->repository->findMostPopular($limit);

        foreach ($products as $product) {
            $key = sprintf('product:%s', $product->id()->toString());
            $this->cache->set($key, $product, ttl: 3600);
        }
    }

    public function warmFromAccessLog(string $logFile, int $limit = 500): void
    {
        $keys = $this->parseAccessLog($logFile, $limit);

        foreach ($keys as $key) {
            if (!$this->cache->has($key)) {
                $value = $this->loadFromSource($key);
                if ($value !== null) {
                    $this->cache->set($key, $value);
                }
            }
        }
    }
}
```

### Scheduled Refresh

```php
// Cron job: refresh cache before TTL expires
// Prevents cache stampede by keeping cache always warm

final readonly class ScheduledCacheRefresher
{
    public function refresh(): void
    {
        $keys = $this->cache->getKeysByPattern('product:*');

        foreach ($keys as $key) {
            $ttl = $this->cache->ttl($key);

            // Refresh if TTL is below threshold (e.g., 20% remaining)
            if ($ttl > 0 && $ttl < $this->refreshThreshold) {
                $value = $this->loadFromSource($key);
                $this->cache->set($key, $value, $this->baseTtl);
            }
        }
    }
}
```

## Cache Stampede Prevention

### Problem

When a popular cache key expires, many concurrent requests hit the database simultaneously.

### Solution 1: Locking (Mutex)

```php
public function getWithLock(string $key): mixed
{
    $value = $this->cache->get($key);
    if ($value !== null) {
        return $value;
    }

    $lockKey = sprintf('lock:%s', $key);
    if ($this->cache->add($lockKey, '1', ttl: 10)) {
        try {
            // Only one process fetches from DB
            $value = $this->repository->find($key);
            $this->cache->set($key, $value, $this->ttl);
            return $value;
        } finally {
            $this->cache->delete($lockKey);
        }
    }

    // Other processes wait and retry
    usleep(50_000); // 50ms
    return $this->getWithLock($key);
}
```

### Solution 2: Probabilistic Early Expiry (XFetch)

```php
public function getWithEarlyExpiry(string $key): mixed
{
    $entry = $this->cache->get($key); // includes value + expiry + delta

    if ($entry === null) {
        return $this->recompute($key);
    }

    $ttlRemaining = $entry['expiry'] - time();
    $beta = 1.0; // tuning parameter

    // Probabilistically recompute before expiry
    if ($ttlRemaining - $beta * $entry['delta'] * log(random_int(1, 100) / 100) <= 0) {
        return $this->recompute($key);
    }

    return $entry['value'];
}
```

### Solution 3: Stale-While-Revalidate

```php
public function getWithStaleRevalidate(string $key): mixed
{
    $value = $this->cache->get($key);
    $meta = $this->cache->get(sprintf('meta:%s', $key));

    if ($value !== null) {
        // Check if soft-expired (still in cache but should refresh)
        if ($meta !== null && $meta['soft_expiry'] < time()) {
            // Return stale value but trigger async refresh
            $this->dispatchRefreshJob($key);
        }
        return $value;
    }

    // Hard cache miss — synchronous fetch
    return $this->recompute($key);
}
```

## Distributed Cache Consistency

### Eventual Consistency (Default)

```
Service A writes DB + invalidates cache
Service B reads stale cache (brief window)
Eventually: cache expires or gets invalidated → consistent
```

Acceptable for: product catalogs, user profiles, search results.

### Strong Consistency

```
Service A writes DB + updates cache atomically
All readers see updated value immediately
```

Required for: financial data, inventory counts, session data.

### Consistency Patterns

| Pattern | Consistency | Implementation |
|---------|-------------|----------------|
| TTL-based | Eventual (stale window = TTL) | Simple, fire-and-forget |
| Event invalidation | Near-real-time | Pub/sub on write events |
| Write-through | Immediate | Sync write to both |
| Two-phase | Strong | Distributed transaction (complex) |
| Lease-based | Strong | Cache lease prevents stale reads |

### PHP PSR-16 Cache Decorator with Tags

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Psr\SimpleCache\CacheInterface;

final class TagAwareCache implements TagAwareCacheInterface
{
    public function __construct(
        private readonly CacheInterface $cache,
    ) {}

    /**
     * @param list<string> $tags
     */
    public function set(string $key, mixed $value, int $ttl = 0, array $tags = []): void
    {
        $this->cache->set($key, $value, $ttl > 0 ? $ttl : null);

        foreach ($tags as $tag) {
            $tagKey = sprintf('tag:%s', $tag);
            $members = $this->cache->get($tagKey, []);
            $members[] = $key;
            $this->cache->set($tagKey, array_unique($members));
        }
    }

    public function invalidateTag(string $tag): void
    {
        $tagKey = sprintf('tag:%s', $tag);
        $members = $this->cache->get($tagKey, []);

        foreach ($members as $key) {
            $this->cache->delete($key);
        }

        $this->cache->delete($tagKey);
    }
}
```
