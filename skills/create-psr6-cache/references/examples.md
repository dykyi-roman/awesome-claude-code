# PSR-6 Cache Examples

## Repository Caching

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence;

use App\Domain\User\Entity\User;
use App\Domain\User\Repository\UserRepositoryInterface;
use App\Domain\User\ValueObject\UserId;
use Psr\Cache\CacheItemPoolInterface;

final readonly class CachedUserRepository implements UserRepositoryInterface
{
    private const CACHE_TTL = 3600;
    private const CACHE_PREFIX = 'user:';

    public function __construct(
        private UserRepositoryInterface $repository,
        private CacheItemPoolInterface $cache,
    ) {
    }

    public function findById(UserId $id): ?User
    {
        $cacheKey = self::CACHE_PREFIX . $id->toString();
        $item = $this->cache->getItem($cacheKey);

        if ($item->isHit()) {
            return $item->get();
        }

        $user = $this->repository->findById($id);

        if ($user !== null) {
            $item->set($user);
            $item->expiresAfter(self::CACHE_TTL);
            $this->cache->save($item);
        }

        return $user;
    }

    public function save(User $user): void
    {
        $this->repository->save($user);

        $cacheKey = self::CACHE_PREFIX . $user->getId()->toString();
        $this->cache->deleteItem($cacheKey);
    }
}
```

## Batch Operations

```php
<?php

use Psr\Cache\CacheItemPoolInterface;

function warmUpCache(CacheItemPoolInterface $cache, array $users): void
{
    foreach ($users as $user) {
        $item = $cache->getItem('user:' . $user->getId());
        $item->set($user);
        $item->expiresAfter(3600);
        $cache->saveDeferred($item);
    }

    $cache->commit();
}

function getMultipleUsers(CacheItemPoolInterface $cache, array $ids): array
{
    $keys = array_map(fn($id) => 'user:' . $id, $ids);
    $items = $cache->getItems($keys);

    $users = [];
    $missingIds = [];

    foreach ($items as $key => $item) {
        if ($item->isHit()) {
            $users[] = $item->get();
        } else {
            $missingIds[] = str_replace('user:', '', $key);
        }
    }

    return [$users, $missingIds];
}
```

## Cache Tagging (Custom Extension)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Cache;

use Psr\Cache\CacheItemInterface;

interface TaggableCacheItemInterface extends CacheItemInterface
{
    /** @param string[] $tags */
    public function setTags(array $tags): static;

    /** @return string[] */
    public function getTags(): array;
}

final class TaggableCacheItem extends CacheItem implements TaggableCacheItemInterface
{
    /** @var string[] */
    private array $tags = [];

    public function setTags(array $tags): static
    {
        $this->tags = $tags;

        return $this;
    }

    public function getTags(): array
    {
        return $this->tags;
    }
}

interface TaggableCachePoolInterface extends CacheItemPoolInterface
{
    public function invalidateTags(array $tags): bool;
}
```

## DI Container Integration

```php
<?php

// Symfony services.yaml
services:
    Psr\Cache\CacheItemPoolInterface:
        class: App\Infrastructure\Cache\RedisCachePool
        arguments:
            $redis: '@Redis'
            $prefix: 'app:'

    App\Infrastructure\Persistence\CachedUserRepository:
        decorates: App\Infrastructure\Persistence\DoctrineUserRepository
        arguments:
            $repository: '@.inner'
            $cache: '@Psr\Cache\CacheItemPoolInterface'
```
