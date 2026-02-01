# PSR-16 Simple Cache Examples

## Repository Caching

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Persistence;

use App\Domain\User\Entity\User;
use App\Domain\User\Repository\UserRepositoryInterface;
use App\Domain\User\ValueObject\UserId;
use Psr\SimpleCache\CacheInterface;

final readonly class CachedUserRepository implements UserRepositoryInterface
{
    private const TTL = 3600;

    public function __construct(
        private UserRepositoryInterface $repository,
        private CacheInterface $cache,
    ) {
    }

    public function findById(UserId $id): ?User
    {
        $key = 'user:' . $id->toString();

        $cached = $this->cache->get($key);
        if ($cached !== null) {
            return $cached;
        }

        $user = $this->repository->findById($id);

        if ($user !== null) {
            $this->cache->set($key, $user, self::TTL);
        }

        return $user;
    }

    public function save(User $user): void
    {
        $this->repository->save($user);
        $this->cache->delete('user:' . $user->getId()->toString());
    }
}
```

## Configuration Caching

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Config;

use Psr\SimpleCache\CacheInterface;

final readonly class CachedConfigLoader
{
    public function __construct(
        private ConfigLoaderInterface $loader,
        private CacheInterface $cache,
        private int $ttl = 86400,
    ) {
    }

    public function load(string $name): array
    {
        $key = 'config:' . $name;

        $cached = $this->cache->get($key);
        if ($cached !== null) {
            return $cached;
        }

        $config = $this->loader->load($name);
        $this->cache->set($key, $config, $this->ttl);

        return $config;
    }

    public function invalidate(string $name): void
    {
        $this->cache->delete('config:' . $name);
    }
}
```

## Query Result Caching

```php
<?php

declare(strict_types=1);

namespace App\Application\Query;

use Psr\SimpleCache\CacheInterface;

final readonly class CachingQueryBus
{
    public function __construct(
        private QueryBusInterface $queryBus,
        private CacheInterface $cache,
    ) {
    }

    public function handle(object $query): mixed
    {
        if (!$query instanceof CacheableQueryInterface) {
            return $this->queryBus->handle($query);
        }

        $key = $query->getCacheKey();
        $ttl = $query->getCacheTtl();

        $cached = $this->cache->get($key);
        if ($cached !== null) {
            return $cached;
        }

        $result = $this->queryBus->handle($query);
        $this->cache->set($key, $result, $ttl);

        return $result;
    }
}

interface CacheableQueryInterface
{
    public function getCacheKey(): string;
    public function getCacheTtl(): int;
}
```
