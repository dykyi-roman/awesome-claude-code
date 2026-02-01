# Null Object Pattern Templates

## Interface

**File:** `src/Domain/{BoundedContext}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

interface {Name}Interface
{
    public function {method1}(): {returnType1};

    public function {method2}({params}): {returnType2};

    public function isNull(): bool;
}
```

---

## Null Object Implementation

**File:** `src/Domain/{BoundedContext}/Null{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

final readonly class Null{Name} implements {Name}Interface
{
    public function {method1}(): {returnType1}
    {
        return {neutralValue1};
    }

    public function {method2}({params}): {returnType2}
    {
        return {neutralValue2};
    }

    public function isNull(): bool
    {
        return true;
    }
}
```

---

## Real Implementation

**File:** `src/Domain/{BoundedContext}/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

final readonly class {Name} implements {Name}Interface
{
    public function __construct(
        {properties}
    ) {}

    public function {method1}(): {returnType1}
    {
        return {realImplementation1};
    }

    public function {method2}({params}): {returnType2}
    {
        return {realImplementation2};
    }

    public function isNull(): bool
    {
        return false;
    }
}
```

---

## NullLogger Template

**File:** `src/Infrastructure/Logging/LoggerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

interface LoggerInterface
{
    public function log(string $level, string $message, array $context = []): void;

    public function debug(string $message, array $context = []): void;

    public function info(string $message, array $context = []): void;

    public function warning(string $message, array $context = []): void;

    public function error(string $message, array $context = []): void;

    public function isNull(): bool;
}
```

**File:** `src/Infrastructure/Logging/NullLogger.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

final readonly class NullLogger implements LoggerInterface
{
    public function log(string $level, string $message, array $context = []): void
    {
    }

    public function debug(string $message, array $context = []): void
    {
    }

    public function info(string $message, array $context = []): void
    {
    }

    public function warning(string $message, array $context = []): void
    {
    }

    public function error(string $message, array $context = []): void
    {
    }

    public function isNull(): bool
    {
        return true;
    }
}
```

---

## NullCache Template

**File:** `src/Infrastructure/Cache/CacheInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

interface CacheInterface
{
    public function get(string $key): mixed;

    public function set(string $key, mixed $value, ?int $ttl = null): void;

    public function has(string $key): bool;

    public function delete(string $key): void;

    public function clear(): void;

    public function isNull(): bool;
}
```

**File:** `src/Infrastructure/Cache/NullCache.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class NullCache implements CacheInterface
{
    public function get(string $key): mixed
    {
        return null;
    }

    public function set(string $key, mixed $value, ?int $ttl = null): void
    {
    }

    public function has(string $key): bool
    {
        return false;
    }

    public function delete(string $key): void
    {
    }

    public function clear(): void
    {
    }

    public function isNull(): bool
    {
        return true;
    }
}
```

---

## NullEventDispatcher Template

**File:** `src/Domain/Event/EventDispatcherInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Event;

interface EventDispatcherInterface
{
    public function dispatch(DomainEventInterface $event): void;

    /**
     * @param array<DomainEventInterface> $events
     */
    public function dispatchAll(array $events): void;

    public function isNull(): bool;
}
```

**File:** `src/Domain/Event/NullEventDispatcher.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Event;

final readonly class NullEventDispatcher implements EventDispatcherInterface
{
    public function dispatch(DomainEventInterface $event): void
    {
    }

    public function dispatchAll(array $events): void
    {
    }

    public function isNull(): bool
    {
        return true;
    }
}
```
