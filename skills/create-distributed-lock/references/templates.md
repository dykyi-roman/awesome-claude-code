# Distributed Lock Templates

## LockInterface

**File:** `src/{architecture-path}/Lock/LockInterface.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

interface LockInterface
{
    /**
     * Attempts to acquire a lock on the given resource.
     * Returns true if the lock was acquired, false otherwise.
     */
    public function acquire(string $resource): bool;

    /**
     * Releases the lock on the given resource.
     * Only releases if the current instance holds the lock.
     */
    public function release(string $resource): void;

    /**
     * Checks if the lock is currently held by this instance.
     */
    public function isAcquired(string $resource): bool;

    /**
     * Refreshes the TTL of an acquired lock.
     * Returns true if the refresh was successful.
     */
    public function refresh(string $resource): bool;
}
```

---

## LockConfig

**File:** `src/{architecture-path}/Lock/LockConfig.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

final readonly class LockConfig
{
    public function __construct(
        public int $ttlSeconds = 30,
        public bool $autoRelease = true,
        public int $retryCount = 3,
        public int $retryDelayMs = 200
    ) {
        if ($this->ttlSeconds < 1) {
            throw new \InvalidArgumentException('TTL must be at least 1 second');
        }

        if ($this->retryCount < 0) {
            throw new \InvalidArgumentException('Retry count cannot be negative');
        }

        if ($this->retryDelayMs < 0) {
            throw new \InvalidArgumentException('Retry delay cannot be negative');
        }
    }

    public static function default(): self
    {
        return new self();
    }

    public static function shortLived(): self
    {
        return new self(ttlSeconds: 5, retryCount: 1, retryDelayMs: 100);
    }

    public static function longRunning(): self
    {
        return new self(ttlSeconds: 300, retryCount: 5, retryDelayMs: 500);
    }
}
```

---

## LockException

**File:** `src/{architecture-path}/Lock/LockException.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

final class LockException extends \RuntimeException
{
    public function __construct(
        public readonly string $resource,
        string $reason
    ) {
        parent::__construct(
            sprintf('Cannot acquire lock on "%s": %s', $resource, $reason)
        );
    }

    public static function cannotAcquire(string $resource): self
    {
        return new self($resource, 'resource is locked by another process');
    }

    public static function notHeld(string $resource): self
    {
        return new self($resource, 'lock is not held by this instance');
    }
}
```

---

## RedisLockAdapter

**File:** `src/{architecture-path}/Lock/RedisLockAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

final class RedisLockAdapter implements LockInterface
{
    private const KEY_PREFIX = 'lock:';

    private const RELEASE_SCRIPT = <<<'LUA'
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("del", KEYS[1])
        else
            return 0
        end
    LUA;

    private const REFRESH_SCRIPT = <<<'LUA'
        if redis.call("get", KEYS[1]) == ARGV[1] then
            return redis.call("expire", KEYS[1], ARGV[2])
        else
            return 0
        end
    LUA;

    /** @var array<string, string> */
    private array $tokens = [];

    public function __construct(
        private readonly \Redis $redis,
        private readonly LockConfig $config
    ) {}

    public function acquire(string $resource): bool
    {
        $key = $this->buildKey($resource);
        $token = $this->generateToken();

        for ($attempt = 0; $attempt <= $this->config->retryCount; $attempt++) {
            $result = $this->redis->set(
                $key,
                $token,
                ['NX', 'EX' => $this->config->ttlSeconds]
            );

            if ($result !== false) {
                $this->tokens[$resource] = $token;
                return true;
            }

            if ($attempt < $this->config->retryCount) {
                usleep($this->config->retryDelayMs * 1000);
            }
        }

        return false;
    }

    public function release(string $resource): void
    {
        $token = $this->tokens[$resource] ?? null;

        if ($token === null) {
            return;
        }

        $this->redis->eval(
            self::RELEASE_SCRIPT,
            [$this->buildKey($resource), $token],
            1
        );

        unset($this->tokens[$resource]);
    }

    public function isAcquired(string $resource): bool
    {
        $token = $this->tokens[$resource] ?? null;

        if ($token === null) {
            return false;
        }

        $storedToken = $this->redis->get($this->buildKey($resource));

        return $storedToken === $token;
    }

    public function refresh(string $resource): bool
    {
        $token = $this->tokens[$resource] ?? null;

        if ($token === null) {
            return false;
        }

        $result = $this->redis->eval(
            self::REFRESH_SCRIPT,
            [$this->buildKey($resource), $token, $this->config->ttlSeconds],
            1
        );

        return (bool) $result;
    }

    private function buildKey(string $resource): string
    {
        return self::KEY_PREFIX . $resource;
    }

    private function generateToken(): string
    {
        return bin2hex(random_bytes(16));
    }
}
```

---

## LockFactory

**File:** `src/{architecture-path}/Lock/LockFactory.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

final readonly class LockFactory
{
    public function __construct(
        private \Redis $redis,
        private LockConfig $defaultConfig = new LockConfig()
    ) {}

    public function create(?LockConfig $config = null): LockInterface
    {
        return new RedisLockAdapter(
            redis: $this->redis,
            config: $config ?? $this->defaultConfig
        );
    }

    public function createForResource(string $resource, ?LockConfig $config = null): AcquiredLock
    {
        $lock = $this->create($config);

        if (!$lock->acquire($resource)) {
            throw LockException::cannotAcquire($resource);
        }

        return new AcquiredLock($lock, $resource);
    }
}
```

---

## AcquiredLock (RAII wrapper)

**File:** `src/{architecture-path}/Lock/AcquiredLock.php`

```php
<?php

declare(strict_types=1);

namespace Lock;

final class AcquiredLock
{
    private bool $released = false;

    public function __construct(
        private readonly LockInterface $lock,
        private readonly string $resource
    ) {}

    public function release(): void
    {
        if (!$this->released) {
            $this->lock->release($this->resource);
            $this->released = true;
        }
    }

    public function refresh(): bool
    {
        return $this->lock->refresh($this->resource);
    }

    public function __destruct()
    {
        $this->release();
    }
}
```
