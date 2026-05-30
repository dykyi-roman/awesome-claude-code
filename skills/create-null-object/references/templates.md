# Null Object Pattern Templates

## Interface

**File:** `src/{architecture-path}/{Name}Interface.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

interface {Name}Interface
{
    public function {method1}(): {returnType1};

    public function {method2}({params}): {returnType2};

    public function isNull(): bool;
}
```

---

## Null Object Implementation

**File:** `src/{architecture-path}/Null{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

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

**File:** `src/{architecture-path}/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace {BoundedContext};

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

**File:** `src/{architecture-path}/Logging/LoggerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Logging;

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

**File:** `src/{architecture-path}/Logging/NullLogger.php`

```php
<?php

declare(strict_types=1);

namespace Logging;

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

**File:** `src/{architecture-path}/Cache/CacheInterface.php`

```php
<?php

declare(strict_types=1);

namespace Cache;

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

**File:** `src/{architecture-path}/Cache/NullCache.php`

```php
<?php

declare(strict_types=1);

namespace Cache;

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

**File:** `src/{architecture-path}/Event/EventDispatcherInterface.php`

```php
<?php

declare(strict_types=1);

namespace Event;

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

**File:** `src/{architecture-path}/Event/NullEventDispatcher.php`

```php
<?php

declare(strict_types=1);

namespace Event;

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
