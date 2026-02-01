# Object Pool Pattern Templates

## Pool Interface

**File:** `src/Infrastructure/Pool/PoolInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

/**
 * @template T
 */
interface PoolInterface
{
    /**
     * @return T
     * @throws PoolExhaustedException
     */
    public function acquire(): mixed;

    /**
     * @param T $object
     */
    public function release(mixed $object): void;

    public function getAvailableCount(): int;

    public function getActiveCount(): int;

    public function getMaxSize(): int;

    public function clear(): void;
}
```

---

## Pool Configuration

**File:** `src/Infrastructure/Pool/PoolConfig.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

final readonly class PoolConfig
{
    public function __construct(
        public int $minSize = 0,
        public int $maxSize = 10,
        public int $maxWaitTimeMs = 5000,
        public int $idleTimeoutSeconds = 300,
        public bool $validateOnAcquire = true,
        public bool $validateOnRelease = false
    ) {
        if ($this->minSize < 0) {
            throw new \InvalidArgumentException('Min size must be non-negative');
        }
        if ($this->maxSize < 1) {
            throw new \InvalidArgumentException('Max size must be at least 1');
        }
        if ($this->minSize > $this->maxSize) {
            throw new \InvalidArgumentException('Min size cannot exceed max size');
        }
    }

    public static function default(): self
    {
        return new self();
    }

    public static function forDatabase(): self
    {
        return new self(
            minSize: 2,
            maxSize: 20,
            maxWaitTimeMs: 10000,
            idleTimeoutSeconds: 600,
            validateOnAcquire: true
        );
    }

    public static function forHttpClients(): self
    {
        return new self(
            minSize: 0,
            maxSize: 50,
            maxWaitTimeMs: 3000,
            idleTimeoutSeconds: 120
        );
    }
}
```

---

## Poolable Interface

**File:** `src/Infrastructure/Pool/PoolableInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

interface PoolableInterface
{
    public function reset(): void;

    public function isValid(): bool;

    public function close(): void;
}
```

---

## Pool Exceptions

**File:** `src/Infrastructure/Pool/PoolExhaustedException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

final class PoolExhaustedException extends \RuntimeException
{
    public function __construct(
        public readonly string $poolName,
        public readonly int $maxSize
    ) {
        parent::__construct(
            sprintf('Pool "%s" exhausted (max size: %d)', $poolName, $maxSize)
        );
    }
}
```

**File:** `src/Infrastructure/Pool/InvalidPoolObjectException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

final class InvalidPoolObjectException extends \RuntimeException
{
    public function __construct(string $reason)
    {
        parent::__construct(sprintf('Pool object is invalid: %s', $reason));
    }
}
```

---

## Generic Object Pool

**File:** `src/Infrastructure/Pool/ObjectPool.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

use Psr\Log\LoggerInterface;

/**
 * @template T of PoolableInterface
 * @implements PoolInterface<T>
 */
final class ObjectPool implements PoolInterface
{
    /** @var \SplQueue<PooledObject<T>> */
    private \SplQueue $available;

    /** @var \SplObjectStorage<T, PooledObject<T>> */
    private \SplObjectStorage $active;

    private int $totalCreated = 0;

    /**
     * @param callable(): T $factory
     */
    public function __construct(
        private readonly string $name,
        private readonly mixed $factory,
        private readonly PoolConfig $config,
        private readonly LoggerInterface $logger
    ) {
        $this->available = new \SplQueue();
        $this->active = new \SplObjectStorage();

        $this->warmUp();
    }

    /**
     * @return T
     */
    public function acquire(): mixed
    {
        $deadline = microtime(true) + ($this->config->maxWaitTimeMs / 1000);

        while (true) {
            if ($this->available->count() > 0) {
                return $this->acquireFromPool();
            }

            if ($this->totalCreated < $this->config->maxSize) {
                return $this->createNew();
            }

            if (microtime(true) >= $deadline) {
                throw new PoolExhaustedException($this->name, $this->config->maxSize);
            }

            usleep(1000);
        }
    }

    /**
     * @param T $object
     */
    public function release(mixed $object): void
    {
        if (!$this->active->contains($object)) {
            $this->logger->warning('Releasing object not from this pool', [
                'pool' => $this->name,
            ]);
            return;
        }

        $pooledObject = $this->active[$object];
        $this->active->detach($object);

        if ($this->config->validateOnRelease && !$object->isValid()) {
            $this->logger->debug('Released object invalid, discarding', [
                'pool' => $this->name,
            ]);
            $object->close();
            $this->totalCreated--;
            return;
        }

        $object->reset();
        $pooledObject->markReturned();
        $this->available->enqueue($pooledObject);

        $this->logger->debug('Object released to pool', [
            'pool' => $this->name,
            'available' => $this->available->count(),
        ]);
    }

    public function getAvailableCount(): int
    {
        return $this->available->count();
    }

    public function getActiveCount(): int
    {
        return $this->active->count();
    }

    public function getMaxSize(): int
    {
        return $this->config->maxSize;
    }

    public function clear(): void
    {
        while ($this->available->count() > 0) {
            $pooledObject = $this->available->dequeue();
            $pooledObject->object->close();
        }

        foreach ($this->active as $object) {
            $object->close();
        }

        $this->active = new \SplObjectStorage();
        $this->totalCreated = 0;

        $this->logger->info('Pool cleared', ['pool' => $this->name]);
    }

    /**
     * @return T
     */
    private function acquireFromPool(): mixed
    {
        while ($this->available->count() > 0) {
            $pooledObject = $this->available->dequeue();

            if ($this->isExpired($pooledObject)) {
                $pooledObject->object->close();
                $this->totalCreated--;
                continue;
            }

            if ($this->config->validateOnAcquire && !$pooledObject->object->isValid()) {
                $pooledObject->object->close();
                $this->totalCreated--;
                continue;
            }

            $pooledObject->markAcquired();
            $this->active->attach($pooledObject->object, $pooledObject);

            $this->logger->debug('Object acquired from pool', [
                'pool' => $this->name,
                'available' => $this->available->count(),
            ]);

            return $pooledObject->object;
        }

        return $this->createNew();
    }

    /**
     * @return T
     */
    private function createNew(): mixed
    {
        $object = ($this->factory)();
        $pooledObject = new PooledObject($object);
        $pooledObject->markAcquired();

        $this->active->attach($object, $pooledObject);
        $this->totalCreated++;

        $this->logger->debug('New object created for pool', [
            'pool' => $this->name,
            'total' => $this->totalCreated,
        ]);

        return $object;
    }

    private function warmUp(): void
    {
        for ($i = 0; $i < $this->config->minSize; $i++) {
            $object = ($this->factory)();
            $this->available->enqueue(new PooledObject($object));
            $this->totalCreated++;
        }

        if ($this->config->minSize > 0) {
            $this->logger->info('Pool warmed up', [
                'pool' => $this->name,
                'count' => $this->config->minSize,
            ]);
        }
    }

    private function isExpired(PooledObject $pooledObject): bool
    {
        if ($this->config->idleTimeoutSeconds === 0) {
            return false;
        }

        $idleTime = time() - $pooledObject->lastUsedAt;
        return $idleTime > $this->config->idleTimeoutSeconds;
    }
}
```

---

## Pooled Object Wrapper

**File:** `src/Infrastructure/Pool/PooledObject.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Pool;

/**
 * @template T
 */
final class PooledObject
{
    public int $createdAt;
    public int $lastUsedAt;
    public int $timesUsed = 0;

    /**
     * @param T $object
     */
    public function __construct(
        public readonly mixed $object
    ) {
        $this->createdAt = time();
        $this->lastUsedAt = time();
    }

    public function markAcquired(): void
    {
        $this->lastUsedAt = time();
        $this->timesUsed++;
    }

    public function markReturned(): void
    {
        $this->lastUsedAt = time();
    }
}
```
