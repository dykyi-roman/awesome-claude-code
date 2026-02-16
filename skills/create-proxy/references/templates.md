# Proxy Pattern Templates

## Subject Interface

**File:** `src/Domain/{BoundedContext}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

interface {Name}Interface
{
    public function {operation}({params}): {returnType};
}
```

---

## Lazy Loading Proxy

**File:** `src/Infrastructure/{BoundedContext}/Proxy/Lazy{Name}Proxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Proxy;

use Domain\{BoundedContext}\{Name}Interface;

final class Lazy{Name}Proxy implements {Name}Interface
{
    private ?{Name}Interface $realSubject = null;

    public function __construct(
        private \Closure $factory
    ) {}

    public function {operation}({params}): {returnType}
    {
        return $this->getRealSubject()->{operation}({args});
    }

    private function getRealSubject(): {Name}Interface
    {
        if ($this->realSubject === null) {
            $this->realSubject = ($this->factory)();
        }

        return $this->realSubject;
    }
}
```

---

## Caching Proxy

**File:** `src/Infrastructure/{BoundedContext}/Proxy/Caching{Name}Proxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Proxy;

use Domain\{BoundedContext}\{Name}Interface;
use Psr\Cache\CacheItemPoolInterface;

final readonly class Caching{Name}Proxy implements {Name}Interface
{
    private const TTL = 3600;

    public function __construct(
        private {Name}Interface $realSubject,
        private CacheItemPoolInterface $cache
    ) {}

    public function {operation}({params}): {returnType}
    {
        $cacheKey = $this->buildCacheKey('{operation}', {args});
        $item = $this->cache->getItem($cacheKey);

        if ($item->isHit()) {
            return $item->get();
        }

        $result = $this->realSubject->{operation}({args});

        $item->set($result);
        $item->expiresAfter(self::TTL);
        $this->cache->save($item);

        return $result;
    }

    private function buildCacheKey(string $method, mixed ...$args): string
    {
        return md5($method . serialize($args));
    }
}
```

---

## Access Control Proxy

**File:** `src/Infrastructure/{BoundedContext}/Proxy/AccessControl{Name}Proxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Proxy;

use Domain\{BoundedContext}\{Name}Interface;
use Domain\Security\AuthorizationServiceInterface;
use Domain\Security\Exception\AccessDeniedException;

final readonly class AccessControl{Name}Proxy implements {Name}Interface
{
    public function __construct(
        private {Name}Interface $realSubject,
        private AuthorizationServiceInterface $authorizationService
    ) {}

    public function {operation}({params}): {returnType}
    {
        if (!$this->authorizationService->canAccess('{operation}')) {
            throw new AccessDeniedException('Access denied to {operation}');
        }

        return $this->realSubject->{operation}({args});
    }
}
```

---

## Logging Proxy

**File:** `src/Infrastructure/{BoundedContext}/Proxy/Logging{Name}Proxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Proxy;

use Domain\{BoundedContext}\{Name}Interface;
use Psr\Log\LoggerInterface;

final readonly class Logging{Name}Proxy implements {Name}Interface
{
    public function __construct(
        private {Name}Interface $realSubject,
        private LoggerInterface $logger
    ) {}

    public function {operation}({params}): {returnType}
    {
        $this->logger->info('Calling {operation}', ['params' => {args}]);

        $startTime = microtime(true);

        try {
            $result = $this->realSubject->{operation}({args});

            $this->logger->info('{operation} completed', [
                'duration' => microtime(true) - $startTime,
            ]);

            return $result;
        } catch (\Throwable $e) {
            $this->logger->error('{operation} failed', [
                'exception' => $e->getMessage(),
                'duration' => microtime(true) - $startTime,
            ]);

            throw $e;
        }
    }
}
```

---

## Repository Lazy Proxy

**File:** `src/Infrastructure/User/Proxy/LazyUserRepositoryProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\User\Proxy;

use Domain\User\Entity\User;
use Domain\User\Repository\UserRepositoryInterface;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\UserId;

final class LazyUserRepositoryProxy implements UserRepositoryInterface
{
    private ?UserRepositoryInterface $realRepository = null;

    public function __construct(
        private \Closure $factory
    ) {}

    public function findById(UserId $id): ?User
    {
        return $this->getRealRepository()->findById($id);
    }

    public function findByEmail(Email $email): ?User
    {
        return $this->getRealRepository()->findByEmail($email);
    }

    public function save(User $user): void
    {
        $this->getRealRepository()->save($user);
    }

    private function getRealRepository(): UserRepositoryInterface
    {
        if ($this->realRepository === null) {
            $this->realRepository = ($this->factory)();
        }

        return $this->realRepository;
    }
}
```
