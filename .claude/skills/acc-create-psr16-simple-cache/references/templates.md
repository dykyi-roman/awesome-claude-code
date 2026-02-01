# PSR-16 Simple Cache Templates

## File Cache

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use DateInterval;
use DateTimeImmutable;
use Psr\SimpleCache\CacheInterface;

final class FileCache implements CacheInterface
{
    public function __construct(
        private readonly string $directory,
    ) {
        if (!is_dir($directory)) {
            mkdir($directory, 0777, true);
        }
    }

    public function get(string $key, mixed $default = null): mixed
    {
        $file = $this->getFilePath($key);

        if (!file_exists($file)) {
            return $default;
        }

        $data = unserialize(file_get_contents($file));

        if ($data['expiration'] !== null && $data['expiration'] < time()) {
            unlink($file);

            return $default;
        }

        return $data['value'];
    }

    public function set(string $key, mixed $value, null|int|DateInterval $ttl = null): bool
    {
        $expiration = $this->calculateExpiration($ttl);

        $data = serialize([
            'value' => $value,
            'expiration' => $expiration,
        ]);

        return file_put_contents($this->getFilePath($key), $data, LOCK_EX) !== false;
    }

    public function delete(string $key): bool
    {
        $file = $this->getFilePath($key);

        if (file_exists($file)) {
            return unlink($file);
        }

        return true;
    }

    public function clear(): bool
    {
        $files = glob($this->directory . '/*.cache');

        foreach ($files as $file) {
            unlink($file);
        }

        return true;
    }

    public function getMultiple(iterable $keys, mixed $default = null): iterable
    {
        $result = [];

        foreach ($keys as $key) {
            $result[$key] = $this->get($key, $default);
        }

        return $result;
    }

    public function setMultiple(iterable $values, null|int|DateInterval $ttl = null): bool
    {
        foreach ($values as $key => $value) {
            $this->set($key, $value, $ttl);
        }

        return true;
    }

    public function deleteMultiple(iterable $keys): bool
    {
        foreach ($keys as $key) {
            $this->delete($key);
        }

        return true;
    }

    public function has(string $key): bool
    {
        return $this->get($key, $this) !== $this;
    }

    private function getFilePath(string $key): string
    {
        return $this->directory . '/' . md5($key) . '.cache';
    }

    private function calculateExpiration(null|int|DateInterval $ttl): ?int
    {
        if ($ttl === null) {
            return null;
        }

        if ($ttl instanceof DateInterval) {
            return (new DateTimeImmutable())->add($ttl)->getTimestamp();
        }

        return time() + $ttl;
    }
}
```

## Chained Cache

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use DateInterval;
use Psr\SimpleCache\CacheInterface;

final readonly class ChainedCache implements CacheInterface
{
    /** @param CacheInterface[] $caches */
    public function __construct(
        private array $caches,
    ) {
    }

    public function get(string $key, mixed $default = null): mixed
    {
        foreach ($this->caches as $index => $cache) {
            $value = $cache->get($key, $this);

            if ($value !== $this) {
                // Populate earlier caches
                for ($i = 0; $i < $index; $i++) {
                    $this->caches[$i]->set($key, $value);
                }

                return $value;
            }
        }

        return $default;
    }

    public function set(string $key, mixed $value, null|int|DateInterval $ttl = null): bool
    {
        $success = true;

        foreach ($this->caches as $cache) {
            if (!$cache->set($key, $value, $ttl)) {
                $success = false;
            }
        }

        return $success;
    }

    public function delete(string $key): bool
    {
        $success = true;

        foreach ($this->caches as $cache) {
            if (!$cache->delete($key)) {
                $success = false;
            }
        }

        return $success;
    }

    public function clear(): bool
    {
        $success = true;

        foreach ($this->caches as $cache) {
            if (!$cache->clear()) {
                $success = false;
            }
        }

        return $success;
    }

    public function getMultiple(iterable $keys, mixed $default = null): iterable
    {
        $result = [];

        foreach ($keys as $key) {
            $result[$key] = $this->get($key, $default);
        }

        return $result;
    }

    public function setMultiple(iterable $values, null|int|DateInterval $ttl = null): bool
    {
        foreach ($values as $key => $value) {
            $this->set($key, $value, $ttl);
        }

        return true;
    }

    public function deleteMultiple(iterable $keys): bool
    {
        foreach ($keys as $key) {
            $this->delete($key);
        }

        return true;
    }

    public function has(string $key): bool
    {
        foreach ($this->caches as $cache) {
            if ($cache->has($key)) {
                return true;
            }
        }

        return false;
    }
}

// Usage: Memory cache first, then Redis
$cache = new ChainedCache([
    new ArrayCache(),
    new RedisCache($redis),
]);
```

## Null Cache

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use DateInterval;
use Psr\SimpleCache\CacheInterface;

final readonly class NullCache implements CacheInterface
{
    public function get(string $key, mixed $default = null): mixed
    {
        return $default;
    }

    public function set(string $key, mixed $value, null|int|DateInterval $ttl = null): bool
    {
        return true;
    }

    public function delete(string $key): bool
    {
        return true;
    }

    public function clear(): bool
    {
        return true;
    }

    public function getMultiple(iterable $keys, mixed $default = null): iterable
    {
        $result = [];

        foreach ($keys as $key) {
            $result[$key] = $default;
        }

        return $result;
    }

    public function setMultiple(iterable $values, null|int|DateInterval $ttl = null): bool
    {
        return true;
    }

    public function deleteMultiple(iterable $keys): bool
    {
        return true;
    }

    public function has(string $key): bool
    {
        return false;
    }
}
```
