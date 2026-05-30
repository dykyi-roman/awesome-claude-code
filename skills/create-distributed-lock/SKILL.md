---
name: create-distributed-lock
description: Generates Distributed Lock for PHP 8.4. Creates LockInterface, LockFactory, RedisLockAdapter with TTL, and database lock adapter. Includes unit tests.
---

# Distributed Lock Generator

Creates distributed locking infrastructure for concurrency control and mutual exclusion.

## When to Use

| Scenario | Example |
|----------|---------|
| Resource contention | Prevent concurrent writes to same entity |
| Scheduled tasks | Ensure cron job runs on single node |
| Inventory management | Prevent overselling with stock locks |
| Distributed coordination | Leader election, singleton processes |

## Component Characteristics

### LockInterface
- Contract for lock implementations
- Methods: acquire, release, isAcquired, refresh
- Supports blocking and non-blocking acquisition

### LockConfig
- Configuration Value Object
- TTL, auto-release flag, retry count, retry delay
- Immutable with sensible defaults

### RedisLockAdapter
- Redis SETNX + TTL implementation
- Atomic acquire using SET NX EX
- Safe release using Lua script (compare-and-delete)
- Token-based ownership verification

### LockFactory
- Creates locks by resource name
- Injects configured adapter and settings
- Supports per-lock TTL override

### LockException
- Thrown on lock acquisition failure
- Contains resource name and reason

---

## Generation Process

### Step 1: Generate Core Components

Place alongside other concurrency/coordination infrastructure.

1. `LockInterface.php` — Lock contract
2. `LockConfig.php` — Configuration value object
3. `LockException.php` — Lock acquisition exception

### Step 2: Generate Lock Adapter

Co-located with the core components.

1. `RedisLockAdapter.php` — Redis SETNX + TTL lock implementation

### Step 3: Generate Factory

Co-located with the adapter.

1. `LockFactory.php` — Creates configured lock instances

### Step 4: Generate Tests

1. `LockConfigTest.php` — Configuration validation tests
2. `RedisLockAdapterTest.php` — Lock behavior tests

---

## File Placement

| Component | Path |
|-----------|------|
| All Classes | `src/{architecture-path}/Lock/` |
| Unit Tests | `tests/Unit/{architecture-path}/Lock/` |

> `{architecture-path}` represents your project's architecture-specific folders. The distributed lock typically lives alongside other concurrency/coordination infrastructure (caching, queues). Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `LockInterface` | `LockInterface` |
| Config VO | `LockConfig` | `LockConfig` |
| Redis Adapter | `RedisLockAdapter` | `RedisLockAdapter` |
| Factory | `LockFactory` | `LockFactory` |
| Exception | `LockException` | `LockException` |
| Test | `{ClassName}Test` | `RedisLockAdapterTest` |

---

## Quick Template Reference

### LockInterface

```php
interface LockInterface
{
    public function acquire(string $resource): bool;
    public function release(string $resource): void;
    public function isAcquired(string $resource): bool;
    public function refresh(string $resource): bool;
}
```

### LockConfig

```php
final readonly class LockConfig
{
    public function __construct(
        public int $ttlSeconds = 30,
        public bool $autoRelease = true,
        public int $retryCount = 3,
        public int $retryDelayMs = 200
    ) {}
}
```

### RedisLockAdapter

```php
final class RedisLockAdapter implements LockInterface
{
    public function acquire(string $resource): bool;
    public function release(string $resource): void;
    public function isAcquired(string $resource): bool;
    public function refresh(string $resource): bool;
}
```

---

## Usage Example

```php
$lock = $lockFactory->create('order-processing');

try {
    if (!$lock->acquire('order:12345')) {
        throw LockException::cannotAcquire('order:12345');
    }

    $order->process();
} finally {
    $lock->release('order:12345');
}
```

---

## Lock Lifecycle

```
acquire() ──→ SET resource token NX EX ttl
                │
         Success? ──→ Lock held (token stored)
                │              │
               NO         refresh() ──→ Extend TTL
                │              │
         Retry? ──→ Sleep → retry     release() ──→ Compare token → DEL
                │
         LockException
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No TTL | Dead locks on crash | Always set TTL |
| DEL without token check | Release others' locks | Use Lua compare-and-delete |
| Spin lock without delay | CPU waste on contention | Use retry delay |
| No auto-release | Lock leak on exception | Use try/finally or auto-release |
| Single Redis node | No fault tolerance | Consider Redlock for HA |
| Infinite retry | Thread stuck forever | Set max retry count |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — LockInterface, LockConfig, RedisLockAdapter, LockFactory templates
- `references/examples.md` — Usage examples and tests
