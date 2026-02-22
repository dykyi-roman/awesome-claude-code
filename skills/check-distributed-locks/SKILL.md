---
name: check-distributed-locks
description: Analyzes PHP code for distributed lock issues. Detects missing TTL on locks, lock without try/finally, unsafe Redis SETNX patterns, missing lock release, and deadlock risks.
---

# Distributed Lock Check

Analyze PHP code for distributed locking anti-patterns that cause deadlocks, race conditions, and resource starvation in multi-instance deployments.

## Detection Patterns

### 1. Missing TTL on Locks

```php
<?php

declare(strict_types=1);

// BAD: Lock without expiration -- if process dies, lock is held forever
final readonly class CacheRefreshService
{
    public function refresh(string $key): void
    {
        $this->redis->set('lock:' . $key, '1');
        // No TTL! If process crashes here, lock is orphaned forever

        try {
            $data = $this->expensiveQuery();
            $this->cache->set($key, $data);
        } finally {
            $this->redis->del('lock:' . $key);
        }
    }
}

// GOOD: Lock with TTL
final readonly class CacheRefreshService
{
    public function refresh(string $key): void
    {
        $acquired = $this->redis->set('lock:' . $key, uniqid(), ['NX', 'EX' => 30]);

        if (!$acquired) {
            return; // Another process holds the lock
        }

        try {
            $data = $this->expensiveQuery();
            $this->cache->set($key, $data);
        } finally {
            $this->redis->del('lock:' . $key);
        }
    }
}
```

### 2. Lock Without try/finally

```php
<?php

declare(strict_types=1);

// BAD: Lock acquired but not released on exception
final readonly class ImportService
{
    public function importBatch(array $items): void
    {
        $lock = $this->lockFactory->createLock('import', 300);
        $lock->acquire(true);

        $this->processItems($items);
        // If processItems() throws, lock is never released!

        $lock->release();
    }
}

// GOOD: Lock release guaranteed in finally block
final readonly class ImportService
{
    public function importBatch(array $items): void
    {
        $lock = $this->lockFactory->createLock('import', 300);
        $lock->acquire(true);

        try {
            $this->processItems($items);
        } finally {
            $lock->release();
        }
    }
}
```

### 3. Unsafe Redis SETNX Pattern

```php
<?php

declare(strict_types=1);

// BAD: SETNX without EXPIRE -- race condition between two commands
final readonly class RedisLock
{
    public function acquire(string $key): bool
    {
        $acquired = $this->redis->setnx('lock:' . $key, '1');

        if ($acquired) {
            $this->redis->expire('lock:' . $key, 30);
            // Race condition: if process dies between SETNX and EXPIRE,
            // lock has no TTL and is held forever
        }

        return $acquired;
    }
}

// BAD: SET without NX -- overwrites existing lock
$this->redis->set('lock:' . $key, '1', 30);
// This always succeeds, even if another process holds the lock!

// GOOD: Atomic SET NX EX (single command, no race)
final readonly class RedisLock
{
    public function acquire(string $key, int $ttl = 30): bool
    {
        $token = bin2hex(random_bytes(16));

        $acquired = $this->redis->set(
            'lock:' . $key,
            $token,
            ['NX', 'EX' => $ttl],
        );

        if ($acquired) {
            $this->tokens[$key] = $token;
        }

        return (bool) $acquired;
    }

    public function release(string $key): void
    {
        // Lua script: only delete if token matches (owner check)
        $script = <<<'LUA'
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
        LUA;

        $this->redis->eval($script, ['lock:' . $key, $this->tokens[$key]], 1);
    }
}
```

### 4. Missing Symfony Lock Component

```php
<?php

declare(strict_types=1);

// BAD: Custom lock implementation when framework provides one
final class CustomFileLock
{
    private $fileHandle;

    public function acquire(string $name): bool
    {
        $this->fileHandle = fopen('/tmp/' . $name . '.lock', 'c');

        return flock($this->fileHandle, LOCK_EX | LOCK_NB);
    }

    public function release(): void
    {
        flock($this->fileHandle, LOCK_UN);
        fclose($this->fileHandle);
    }
}

// GOOD: Use Symfony Lock component with Redis store
// config/packages/lock.yaml:
// framework:
//     lock: '%env(REDIS_URL)%'

final readonly class OrderProcessingService
{
    public function __construct(
        private LockFactory $lockFactory,
    ) {}

    public function processOrder(OrderId $orderId): void
    {
        $lock = $this->lockFactory->createLock(
            resource: 'order-processing:' . $orderId->toString(),
            ttl: 60,
        );

        if (!$lock->acquire(false)) {
            throw new OrderAlreadyBeingProcessedException($orderId);
        }

        try {
            $this->doProcessOrder($orderId);
        } finally {
            $lock->release();
        }
    }
}
```

### 5. Deadlock Patterns -- Inconsistent Lock Ordering

```php
<?php

declare(strict_types=1);

// BAD: Acquiring multiple locks in inconsistent order
final readonly class TransferService
{
    public function transfer(AccountId $from, AccountId $to, Money $amount): void
    {
        // Thread A: locks account-1, then account-2
        // Thread B: locks account-2, then account-1
        // DEADLOCK!
        $lockFrom = $this->lockFactory->createLock('account:' . $from->toString(), 30);
        $lockTo = $this->lockFactory->createLock('account:' . $to->toString(), 30);

        $lockFrom->acquire(true);
        $lockTo->acquire(true); // May deadlock if another transfer is from $to to $from

        try {
            $this->debit($from, $amount);
            $this->credit($to, $amount);
        } finally {
            $lockTo->release();
            $lockFrom->release();
        }
    }
}

// GOOD: Consistent lock ordering (alphabetical/numerical)
final readonly class TransferService
{
    public function transfer(AccountId $from, AccountId $to, Money $amount): void
    {
        // Always lock in consistent order (lower ID first)
        $ids = [$from->toString(), $to->toString()];
        sort($ids);

        $lockFirst = $this->lockFactory->createLock('account:' . $ids[0], 30);
        $lockSecond = $this->lockFactory->createLock('account:' . $ids[1], 30);

        $lockFirst->acquire(true);
        try {
            $lockSecond->acquire(true);
            try {
                $this->debit($from, $amount);
                $this->credit($to, $amount);
            } finally {
                $lockSecond->release();
            }
        } finally {
            $lockFirst->release();
        }
    }
}
```

## Grep Patterns

```bash
# Locks without TTL
Grep: "->set\(['\"]lock:|->setnx\(" --glob "**/*.php"
Grep: "createLock\([^)]*\)" --glob "**/*.php"

# SETNX without atomic EXPIRE
Grep: "setnx\(" --glob "**/*.php"

# Lock without try/finally
Grep: "->acquire\(|->lock\(" --glob "**/*.php"

# flock usage (local file lock)
Grep: "flock\(" --glob "**/src/**/*.php"

# Custom lock implementations
Grep: "class.*Lock|class.*Mutex|class.*Semaphore" --glob "**/*.php"

# Symfony Lock component usage
Grep: "LockFactory|LockInterface|use Symfony\\\\Component\\\\Lock" --glob "**/*.php"

# Multiple lock acquisitions in same method (deadlock risk)
Grep: "createLock.*\n.*createLock|acquire.*\n.*acquire" --glob "**/*.php"

# Lock release patterns
Grep: "->release\(\)" --glob "**/*.php"
Grep: "finally" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Lock without TTL | 🔴 Critical |
| SETNX without atomic EXPIRE | 🔴 Critical |
| Deadlock from inconsistent lock ordering | 🔴 Critical |
| Lock without try/finally | 🟠 Major |
| Custom file-based lock (flock) | 🟠 Major |
| Missing lock ownership verification | 🟠 Major |
| Lock release without owner check | 🟡 Minor |
| Custom lock when framework provides one | 🟡 Minor |

## Output Format

```markdown
### Distributed Lock Issue: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [No TTL|No Finally|Unsafe SETNX|Deadlock|File Lock]

**Issue:**
[Description of the distributed lock problem]

**Risk:**
- Permanent lock hold on process crash
- Deadlock between concurrent processes
- Race condition on lock acquisition

**Code:**
```php
// Problematic locking pattern
```

**Fix:**
```php
// Safe distributed locking
```
```

## When This Is Acceptable

- **Single-instance deployment** -- File-based locking is fine when only one process runs
- **Short-lived CLI scripts** -- One-shot scripts with no concurrency don't need distributed locks
- **In-memory locks for thread safety** -- PHP-FPM worker process isolation makes in-memory locks irrelevant (each request is isolated)
- **Database advisory locks** -- Using `pg_advisory_lock()` or `GET_LOCK()` is valid for single-database setups

### False Positive Indicators
- Lock is in test code or a test double
- flock is used for log file rotation (not coordination)
- Custom lock class wraps Symfony Lock component internally
- SETNX is immediately followed by EXPIRE in a Lua script (atomic)
