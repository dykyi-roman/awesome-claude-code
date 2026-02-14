# Cache-Aside Pattern Templates

## CacheAsideInterface

**File:** `src/Domain/Shared/Cache/CacheAsideInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Cache;

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

---

## CacheKeyGeneratorInterface

**File:** `src/Domain/Shared/Cache/CacheKeyGeneratorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Cache;

interface CacheKeyGeneratorInterface
{
    public function generate(string $context, string ...$parts): string;

    public function generateHashed(string $context, string ...$parts): string;
}
```

---

## CacheKeyGenerator

**File:** `src/Infrastructure/Cache/CacheKeyGenerator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Domain\Shared\Cache\CacheKeyGeneratorInterface;

final readonly class CacheKeyGenerator implements CacheKeyGeneratorInterface
{
    private const MAX_KEY_LENGTH = 250;

    public function __construct(
        private string $prefix = 'app'
    ) {}

    public function generate(string $context, string ...$parts): string
    {
        $key = sprintf('%s:%s:%s', $this->prefix, $context, implode(':', $parts));

        if (strlen($key) > self::MAX_KEY_LENGTH) {
            return $this->generateHashed($context, ...$parts);
        }

        return $key;
    }

    public function generateHashed(string $context, string ...$parts): string
    {
        $raw = sprintf('%s:%s', $context, implode(':', $parts));

        return sprintf('%s:%s:%s', $this->prefix, $context, hash('xxh128', $raw));
    }
}
```

---

## CacheLockInterface

**File:** `src/Infrastructure/Cache/CacheLockInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

interface CacheLockInterface
{
    public function acquire(string $key, int $ttl = 10): bool;

    public function release(string $key): void;
}
```

---

## RedisCacheLock

**File:** `src/Infrastructure/Cache/RedisCacheLock.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class RedisCacheLock implements CacheLockInterface
{
    private const LOCK_PREFIX = 'lock:';

    public function __construct(
        private \Redis $redis
    ) {}

    public function acquire(string $key, int $ttl = 10): bool
    {
        $lockKey = self::LOCK_PREFIX . $key;

        $result = $this->redis->set(
            $lockKey,
            '1',
            ['NX', 'EX' => $ttl]
        );

        return $result === true;
    }

    public function release(string $key): void
    {
        $lockKey = self::LOCK_PREFIX . $key;

        $this->redis->del($lockKey);
    }
}
```

---

## CacheAsideExecutor

**File:** `src/Infrastructure/Cache/CacheAsideExecutor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Domain\Shared\Cache\CacheAsideInterface;
use Psr\SimpleCache\CacheInterface;

final readonly class CacheAsideExecutor implements CacheAsideInterface
{
    public function __construct(
        private CacheInterface $cache,
        private CacheLockInterface $lock,
        private int $defaultTtl = 3600,
        private int $lockTtl = 10,
        private int $lockWaitMs = 50,
        private int $lockMaxRetries = 20,
    ) {}

    public function get(string $key, callable $loader, int $ttl = 0): mixed
    {
        $ttl = $ttl > 0 ? $ttl : $this->defaultTtl;

        $cached = $this->cache->get($key);

        if ($cached !== null) {
            return $cached;
        }

        if ($this->lock->acquire($key, $this->lockTtl)) {
            try {
                $cached = $this->cache->get($key);

                if ($cached !== null) {
                    return $cached;
                }

                $value = $loader();
                $this->cache->set($key, $value, $ttl);

                return $value;
            } finally {
                $this->lock->release($key);
            }
        }

        return $this->waitForCacheOrCompute($key, $loader, $ttl);
    }

    public function invalidate(string $key): void
    {
        $this->cache->delete($key);
    }

    public function invalidateByTag(string $tag): void
    {
        $tagKey = sprintf('tag:%s', $tag);
        $members = $this->cache->get($tagKey);

        if (!is_array($members)) {
            return;
        }

        foreach ($members as $key) {
            $this->cache->delete($key);
        }

        $this->cache->delete($tagKey);
    }

    private function waitForCacheOrCompute(string $key, callable $loader, int $ttl): mixed
    {
        for ($i = 0; $i < $this->lockMaxRetries; $i++) {
            usleep($this->lockWaitMs * 1000);

            $cached = $this->cache->get($key);

            if ($cached !== null) {
                return $cached;
            }
        }

        return $loader();
    }
}
```

---

## CacheInvalidator

**File:** `src/Infrastructure/Cache/CacheInvalidator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

use Psr\SimpleCache\CacheInterface;

final readonly class CacheInvalidator
{
    public function __construct(
        private CacheInterface $cache,
        private \Redis $redis,
    ) {}

    public function invalidate(string $key): void
    {
        $this->cache->delete($key);
    }

    public function invalidateByTag(string $tag): void
    {
        $tagKey = sprintf('tag:%s', $tag);
        $members = $this->cache->get($tagKey);

        if (!is_array($members)) {
            return;
        }

        foreach ($members as $key) {
            $this->cache->delete($key);
        }

        $this->cache->delete($tagKey);
    }

    public function invalidateByPattern(string $pattern): void
    {
        $cursor = null;
        $keys = [];

        do {
            $result = $this->redis->scan($cursor, $pattern, 100);

            if ($result !== false) {
                $keys = array_merge($keys, $result);
            }
        } while ($cursor > 0);

        foreach ($keys as $key) {
            $this->cache->delete($key);
        }
    }

    public function tagKey(string $key, string $tag): void
    {
        $tagKey = sprintf('tag:%s', $tag);
        $members = $this->cache->get($tagKey) ?? [];

        if (!is_array($members)) {
            $members = [];
        }

        $members[] = $key;
        $members = array_unique($members);

        $this->cache->set($tagKey, $members);
    }

    public function tagKeys(array $keys, string $tag): void
    {
        foreach ($keys as $key) {
            $this->tagKey($key, $tag);
        }
    }
}
```
