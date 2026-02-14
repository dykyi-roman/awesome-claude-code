---
name: acc-create-cache-aside
description: Generates Cache-Aside pattern for PHP 8.5. Creates cache executor with PSR-16 integration, stampede protection via distributed locking, tag-based invalidation, and key generation. Includes unit tests.
---

# Cache-Aside Generator

Creates Cache-Aside infrastructure with stampede protection and tag-based invalidation.

## When to Use

| Scenario | Example |
|----------|---------|
| Read-heavy workloads | Product catalog, user profiles |
| Expensive queries | Complex reports, aggregated data |
| External API responses | Third-party API caching |
| Computed values | Pricing calculations, search results |

## Component Characteristics

### CacheAsideInterface
- `get(string $key, callable $loader, int $ttl): mixed` — load from cache or compute
- `invalidate(string $key): void` — remove specific cache entry
- `invalidateByTag(string $tag): void` — remove all entries tagged with given tag

### CacheKeyGenerator
- Builds deterministic cache keys from prefix and parameters
- Hashes long keys to prevent exceeding storage limits
- Supports tag-based key grouping

### CacheAsideExecutor
- PSR-16 SimpleCache integration
- Configurable TTL per cache operation
- Stampede protection via distributed locking
- Prevents thundering herd on cache miss

### CacheInvalidator
- Tag-based invalidation (invalidate all entries for a tag)
- Pattern-based clearing (wildcard key matching)
- Batch invalidation support

---

## Generation Process

### Step 1: Generate Domain Components

**Path:** `src/Domain/Shared/Cache/`

1. `CacheAsideInterface.php` — Cache-aside contract
2. `CacheKeyGeneratorInterface.php` — Key generation contract

### Step 2: Generate Infrastructure Components

**Path:** `src/Infrastructure/Cache/`

1. `CacheKeyGenerator.php` — Key builder with hashing
2. `CacheAsideExecutor.php` — PSR-16 cache executor with locking
3. `CacheInvalidator.php` — Tag-based and pattern-based invalidation
4. `CacheLockInterface.php` — Distributed lock contract
5. `RedisCacheLock.php` — Redis-based lock implementation

### Step 3: Generate Tests

1. `CacheKeyGeneratorTest.php` — Key generation and hashing tests
2. `CacheAsideExecutorTest.php` — Cache hit/miss, stampede protection tests
3. `CacheInvalidatorTest.php` — Tag and pattern invalidation tests

---

## File Placement

| Component | Path |
|-----------|------|
| Domain Interfaces | `src/Domain/Shared/Cache/` |
| Infrastructure | `src/Infrastructure/Cache/` |
| Unit Tests | `tests/Unit/Infrastructure/Cache/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `CacheAsideInterface` | `CacheAsideInterface` |
| Key Generator | `CacheKeyGenerator` | `CacheKeyGenerator` |
| Executor | `CacheAsideExecutor` | `CacheAsideExecutor` |
| Invalidator | `CacheInvalidator` | `CacheInvalidator` |
| Lock Interface | `CacheLockInterface` | `CacheLockInterface` |
| Lock Impl | `{Store}CacheLock` | `RedisCacheLock` |
| Test | `{ClassName}Test` | `CacheAsideExecutorTest` |

---

## Quick Template Reference

### CacheAsideInterface

```php
interface CacheAsideInterface
{
    /**
     * @template T
     * @param callable(): T $loader
     * @return T
     */
    public function get(string $key, callable $loader, int $ttl = 3600): mixed;
    public function invalidate(string $key): void;
    public function invalidateByTag(string $tag): void;
}
```

### CacheKeyGenerator

```php
final readonly class CacheKeyGenerator
{
    public function __construct(private string $prefix = 'app');
    public function generate(string $context, string ...$parts): string;
    public function generateHashed(string $context, string ...$parts): string;
}
```

### CacheLockInterface

```php
interface CacheLockInterface
{
    public function acquire(string $key, int $ttl = 10): bool;
    public function release(string $key): void;
}
```

---

## Usage Example

```php
$executor = new CacheAsideExecutor($cache, $lock, defaultTtl: 3600);

// Cache-aside: returns cached value or computes via loader
$product = $executor->get(
    key: 'product:123',
    loader: fn() => $repository->findById(123),
    ttl: 1800
);

// Invalidate on update
$executor->invalidate('product:123');

// Tag-based invalidation
$invalidator->invalidateByTag('products');
```

---

## Pattern Comparison

| Pattern | Description | Use Case |
|---------|-------------|----------|
| Cache-Aside | App manages cache (check → miss → load → store) | Read-heavy, tolerates stale data |
| Read-Through | Cache loads data on miss (transparent to app) | Simpler app code, cache manages loading |
| Write-Through | Write to cache and DB simultaneously | Strong consistency needed |
| Write-Behind | Write to cache, async write to DB | High write throughput, eventual consistency |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No TTL | Stale data served forever | Always set TTL, even long ones |
| Thundering herd | All requests compute on cache miss | Stampede protection with locking |
| Cache poisoning | Invalid data cached | Validate data before caching |
| Inconsistent invalidation | Update DB but forget cache | Use events/listeners for invalidation |
| Key collisions | Different data for same key | Use prefix + context + params |
| Over-caching | Memory waste, stale data | Cache only expensive/frequent operations |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — CacheAsideInterface, CacheKeyGenerator, CacheAsideExecutor, CacheInvalidator, lock templates
- `references/examples.md` — Repository integration, event-driven invalidation, and unit tests
