---
name: acc-check-caching-strategy
description: Analyzes PHP code for caching opportunities and issues. Detects missing cache, cache invalidation problems, over-caching, repeated expensive operations.
---

# Caching Strategy Analysis

Analyze PHP code for caching opportunities and issues.

## Detection Patterns

### 1. Missing Cache Opportunities

```php
// CACHEABLE: Repeated expensive computation
public function getExchangeRate(string $currency): float
{
    return $this->api->fetchRate($currency); // API call each time
}

// CACHEABLE: Repeated database query
public function getSettings(): array
{
    return $this->repository->findAll(); // Same query repeatedly
}

// CACHEABLE: Configuration that rarely changes
public function getFeatureFlags(): array
{
    return $this->configLoader->load(); // File read each request
}
```

### 2. Cache Invalidation Issues

```php
// STALE DATA: No invalidation
$cache->set('user_' . $id, $user, 3600);
// Later: user updated but cache not cleared

// STALE DATA: Time-based only
$cache->set('products', $products, 86400);
// Products change but cache lives for 24h

// RACE CONDITION: Invalidate before update
$this->cache->delete('user_' . $id);
$this->repository->update($user);
// Another request may cache old data between these lines
```

### 3. Over-Caching

```php
// OVER-CACHED: User-specific data with long TTL
$cache->set('user_dashboard_' . $userId, $data, 86400);
// User dashboard may need fresh data

// OVER-CACHED: Rapidly changing data
$cache->set('stock_count_' . $productId, $count, 3600);
// Stock changes frequently

// OVER-CACHED: Huge cache entries
$cache->set('all_products', $allProducts); // 10MB cache entry
```

### 4. Cache Stampede

```php
// STAMPEDE: Many requests rebuild cache simultaneously
public function getData(): array
{
    $data = $this->cache->get('key');
    if (!$data) {
        $data = $this->expensiveOperation(); // All concurrent requests hit this
        $this->cache->set('key', $data, 3600);
    }
    return $data;
}

// FIXED: Lock during rebuild
public function getData(): array
{
    $data = $this->cache->get('key');
    if (!$data) {
        $lock = $this->lockFactory->createLock('key_rebuild');
        if ($lock->acquire()) {
            $data = $this->expensiveOperation();
            $this->cache->set('key', $data, 3600);
            $lock->release();
        } else {
            $data = $this->cache->get('key'); // Wait for other process
        }
    }
    return $data;
}
```

### 5. Wrong Cache Key

```php
// BAD: Missing important parameters
$cache->get('user_data'); // Same for all users?

// BAD: Too specific
$cache->get('user_' . $id . '_' . $requestId); // Never hits

// BAD: Collision risk
$cache->get(md5($query)); // Different queries may collide

// GOOD: Meaningful, unique key
$cache->get(sprintf('user:%d:profile:v1', $userId));
```

### 6. Cache Storage Issues

```php
// PROBLEM: Storing large objects
$cache->set('report', $largeReport); // 50MB serialized

// PROBLEM: Storing non-serializable
$cache->set('connection', $pdoConnection); // Can't serialize

// PROBLEM: Storing closures
$cache->set('callback', function() { }); // Fails
```

### 7. TTL Issues

```php
// TOO SHORT: Cache overhead exceeds benefit
$cache->set('data', $data, 1); // 1 second TTL

// TOO LONG: Stale data risk
$cache->set('exchange_rates', $rates, 604800); // 1 week

// NO TTL: Memory leak risk
$cache->set('data', $data); // Never expires

// FIXED: Appropriate TTL
$cache->set('exchange_rates', $rates, 300); // 5 minutes
```

### 8. Cache Warming

```php
// COLD START: First request is slow
// No warming strategy, first user waits

// BETTER: Warm cache on deploy/schedule
public function warmCache(): void
{
    $this->cache->set('config', $this->loadConfig());
    $this->cache->set('categories', $this->loadCategories());
}
```

## Grep Patterns

```bash
# API calls without cache
Grep: "->request\(|->get\(|->fetch\(" --glob "**/*.php"

# Repository calls that could be cached
Grep: "Repository->find|Repository->get" --glob "**/*.php"

# Cache operations
Grep: "->cache->|Cache::|redis->|memcache" --glob "**/*.php"

# Missing TTL
Grep: "->set\([^,]+,[^,]+\)\s*;" --glob "**/*.php"
```

## Caching Patterns

### Read-Through Cache

```php
public function get(string $key, callable $loader, int $ttl = 3600): mixed
{
    $value = $this->cache->get($key);
    if ($value === null) {
        $value = $loader();
        $this->cache->set($key, $value, $ttl);
    }
    return $value;
}
```

### Write-Through Cache

```php
public function update(Entity $entity): void
{
    $this->repository->save($entity);
    $this->cache->set('entity:' . $entity->getId(), $entity);
}
```

### Cache-Aside with Locking

```php
public function getWithLock(string $key, callable $loader): mixed
{
    $value = $this->cache->get($key);
    if ($value !== null) {
        return $value;
    }

    $lock = $this->lockFactory->createLock($key);
    if ($lock->acquire()) {
        try {
            $value = $loader();
            $this->cache->set($key, $value);
        } finally {
            $lock->release();
        }
    } else {
        usleep(100000);
        return $this->getWithLock($key, $loader);
    }
    return $value;
}
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Cache stampede risk | 🔴 Critical |
| Missing invalidation | 🟠 Major |
| Missing cache for hot path | 🟠 Major |
| Wrong cache key | 🟠 Major |
| Overly long TTL | 🟡 Minor |
| Over-caching user data | 🟡 Minor |

## Output Format

```markdown
### Caching Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Missing Cache|Invalidation|Stampede|...]

**Issue:**
[Description of the caching problem]

**Code:**
```php
// Current code
```

**Fix:**
```php
// With proper caching
```

**Expected Improvement:**
Response time: 500ms → 5ms (on cache hit)
Database load: 1000 QPS → 100 QPS
```
