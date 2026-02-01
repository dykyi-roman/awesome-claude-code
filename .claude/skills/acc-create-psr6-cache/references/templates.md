# PSR-6 Cache Templates

## Redis Cache Pool

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use Psr\Cache\CacheItemInterface;
use Psr\Cache\CacheItemPoolInterface;
use Redis;

final class RedisCachePool implements CacheItemPoolInterface
{
    /** @var array<string, CacheItem> */
    private array $deferred = [];

    public function __construct(
        private readonly Redis $redis,
        private readonly string $prefix = 'cache:',
    ) {
    }

    public function getItem(string $key): CacheItemInterface
    {
        $this->validateKey($key);

        if (isset($this->deferred[$key])) {
            return clone $this->deferred[$key];
        }

        $item = new CacheItem($key);
        $value = $this->redis->get($this->prefix . $key);

        if ($value !== false) {
            $data = unserialize($value);
            $item->set($data);
            $item->markAsHit();
        } else {
            $item->markAsMiss();
        }

        return $item;
    }

    /** @return iterable<string, CacheItemInterface> */
    public function getItems(array $keys = []): iterable
    {
        $items = [];

        foreach ($keys as $key) {
            $items[$key] = $this->getItem($key);
        }

        return $items;
    }

    public function hasItem(string $key): bool
    {
        $this->validateKey($key);

        return $this->redis->exists($this->prefix . $key) > 0;
    }

    public function clear(): bool
    {
        $keys = $this->redis->keys($this->prefix . '*');

        if (!empty($keys)) {
            $this->redis->del($keys);
        }

        $this->deferred = [];

        return true;
    }

    public function deleteItem(string $key): bool
    {
        $this->validateKey($key);

        unset($this->deferred[$key]);
        $this->redis->del($this->prefix . $key);

        return true;
    }

    public function deleteItems(array $keys): bool
    {
        foreach ($keys as $key) {
            $this->deleteItem($key);
        }

        return true;
    }

    public function save(CacheItemInterface $item): bool
    {
        if (!$item instanceof CacheItem) {
            return false;
        }

        $key = $this->prefix . $item->getKey();
        $value = serialize($item->get());
        $expiration = $item->getExpiration();

        if ($expiration !== null) {
            $ttl = $expiration->getTimestamp() - time();

            if ($ttl <= 0) {
                return $this->deleteItem($item->getKey());
            }

            $this->redis->setex($key, $ttl, $value);
        } else {
            $this->redis->set($key, $value);
        }

        unset($this->deferred[$item->getKey()]);

        return true;
    }

    public function saveDeferred(CacheItemInterface $item): bool
    {
        if (!$item instanceof CacheItem) {
            return false;
        }

        $this->deferred[$item->getKey()] = $item;

        return true;
    }

    public function commit(): bool
    {
        $this->redis->multi();

        foreach ($this->deferred as $item) {
            $this->save($item);
        }

        $this->redis->exec();
        $this->deferred = [];

        return true;
    }

    private function validateKey(string $key): void
    {
        if ($key === '' || preg_match('/[{}()\/\\\\@:]/', $key)) {
            throw new InvalidArgumentException('Invalid cache key');
        }
    }
}
```

## File Cache Pool

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use Psr\Cache\CacheItemInterface;
use Psr\Cache\CacheItemPoolInterface;

final class FileCachePool implements CacheItemPoolInterface
{
    /** @var array<string, CacheItem> */
    private array $deferred = [];

    public function __construct(
        private readonly string $directory,
    ) {
        if (!is_dir($directory)) {
            mkdir($directory, 0777, true);
        }
    }

    public function getItem(string $key): CacheItemInterface
    {
        $this->validateKey($key);

        if (isset($this->deferred[$key])) {
            return clone $this->deferred[$key];
        }

        $item = new CacheItem($key);
        $file = $this->getFilePath($key);

        if (file_exists($file)) {
            $data = unserialize(file_get_contents($file));

            if ($data['expiration'] === null || $data['expiration'] > time()) {
                $item->set($data['value']);
                $item->markAsHit();

                return $item;
            }

            unlink($file);
        }

        $item->markAsMiss();

        return $item;
    }

    /** @return iterable<string, CacheItemInterface> */
    public function getItems(array $keys = []): iterable
    {
        $items = [];

        foreach ($keys as $key) {
            $items[$key] = $this->getItem($key);
        }

        return $items;
    }

    public function hasItem(string $key): bool
    {
        return $this->getItem($key)->isHit();
    }

    public function clear(): bool
    {
        $files = glob($this->directory . '/*.cache');

        foreach ($files as $file) {
            unlink($file);
        }

        $this->deferred = [];

        return true;
    }

    public function deleteItem(string $key): bool
    {
        $this->validateKey($key);

        unset($this->deferred[$key]);

        $file = $this->getFilePath($key);

        if (file_exists($file)) {
            unlink($file);
        }

        return true;
    }

    public function deleteItems(array $keys): bool
    {
        foreach ($keys as $key) {
            $this->deleteItem($key);
        }

        return true;
    }

    public function save(CacheItemInterface $item): bool
    {
        if (!$item instanceof CacheItem) {
            return false;
        }

        $expiration = $item->getExpiration();

        $data = [
            'value' => $item->get(),
            'expiration' => $expiration?->getTimestamp(),
        ];

        file_put_contents(
            $this->getFilePath($item->getKey()),
            serialize($data),
            LOCK_EX,
        );

        unset($this->deferred[$item->getKey()]);

        return true;
    }

    public function saveDeferred(CacheItemInterface $item): bool
    {
        if (!$item instanceof CacheItem) {
            return false;
        }

        $this->deferred[$item->getKey()] = $item;

        return true;
    }

    public function commit(): bool
    {
        foreach ($this->deferred as $item) {
            $this->save($item);
        }

        $this->deferred = [];

        return true;
    }

    private function getFilePath(string $key): string
    {
        return $this->directory . '/' . md5($key) . '.cache';
    }

    private function validateKey(string $key): void
    {
        if ($key === '' || preg_match('/[{}()\/\\\\@:]/', $key)) {
            throw new InvalidArgumentException('Invalid cache key');
        }
    }
}
```

## Exceptions

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use Psr\Cache\CacheException;
use Psr\Cache\InvalidArgumentException as PsrInvalidArgumentException;

final class InvalidArgumentException extends \InvalidArgumentException implements PsrInvalidArgumentException
{
}

final class CachePoolException extends \RuntimeException implements CacheException
{
}
```
