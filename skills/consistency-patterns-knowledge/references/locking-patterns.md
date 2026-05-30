# Locking Patterns Reference

## Optimistic Locking

### Doctrine Version Field

Doctrine ORM supports optimistic locking via `#[ORM\Version]` on an integer or datetime column. On every flush, Doctrine increments the version and adds `WHERE version = :current` to the UPDATE query. If the row was modified concurrently, `OptimisticLockException` is thrown.

```php
<?php

declare(strict_types=1);

namespace Model;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'orders')]
final class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'string', length: 36)]
    private string $id;

    #[ORM\Column(type: 'string', length: 32)]
    private string $status;

    #[ORM\Column(type: 'integer')]
    private int $totalCents;

    #[ORM\Version]
    #[ORM\Column(type: 'integer')]
    private int $version = 1;

    public function __construct(string $id, int $totalCents)
    {
        $this->id = $id;
        $this->status = 'pending';
        $this->totalCents = $totalCents;
    }

    public function confirm(): void
    {
        if ($this->status !== 'pending') {
            throw new InvalidOrderStateException($this->id, $this->status, 'pending');
        }

        $this->status = 'confirmed';
    }

    public function getVersion(): int
    {
        return $this->version;
    }
}
```

### StaleObjectStateException Handling

When using Doctrine, wrap flush calls and handle the version mismatch:

```php
<?php

declare(strict_types=1);

namespace UseCase;

use Doctrine\ORM\EntityManagerInterface;
use Doctrine\ORM\OptimisticLockException;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private OrderRepositoryInterface $repository,
        private int $maxRetries = 3,
    ) {}

    public function execute(string $orderId): void
    {
        for ($attempt = 1; $attempt <= $this->maxRetries; $attempt++) {
            try {
                $this->entityManager->beginTransaction();

                $order = $this->repository->findById($orderId);
                $order->confirm();
                $this->entityManager->flush();
                $this->entityManager->commit();

                return;
            } catch (OptimisticLockException $e) {
                $this->entityManager->rollback();
                $this->entityManager->clear();

                if ($attempt === $this->maxRetries) {
                    throw new ConcurrencyException(
                        sprintf('Failed to confirm order %s after %d attempts', $orderId, $this->maxRetries),
                        previous: $e,
                    );
                }

                usleep(random_int(10_000, 100_000));
            }
        }
    }
}
```

### Compare-and-Swap (CAS) Pattern

For non-ORM scenarios, implement CAS manually:

```php
<?php

declare(strict_types=1);

namespace Persistence;

final readonly class CasRepository
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    public function updateWithVersion(string $table, string $id, array $data, int $expectedVersion): bool
    {
        $sets = [];
        $params = [':id' => $id, ':expected_version' => $expectedVersion];

        foreach ($data as $column => $value) {
            $sets[] = sprintf('%s = :%s', $column, $column);
            $params[':' . $column] = $value;
        }

        $sets[] = 'version = version + 1';

        $sql = sprintf(
            'UPDATE %s SET %s WHERE id = :id AND version = :expected_version',
            $table,
            implode(', ', $sets),
        );

        $stmt = $this->pdo->prepare($sql);
        $stmt->execute($params);

        return $stmt->rowCount() === 1;
    }
}
```

## Pessimistic Locking

### SELECT FOR UPDATE with Timeout

```php
<?php

declare(strict_types=1);

namespace Persistence;

use Doctrine\ORM\EntityManagerInterface;
use Doctrine\DBAL\LockMode;

final readonly class PessimisticOrderRepository
{
    public function __construct(
        private EntityManagerInterface $entityManager,
    ) {}

    public function findAndLock(string $orderId): Order
    {
        $this->entityManager->getConnection()->executeStatement(
            'SET innodb_lock_wait_timeout = 5',
        );

        $order = $this->entityManager->find(
            Order::class,
            $orderId,
            LockMode::PESSIMISTIC_WRITE,
        );

        if ($order === null) {
            throw new OrderNotFoundException($orderId);
        }

        return $order;
    }

    public function findForShare(string $orderId): Order
    {
        return $this->entityManager->find(
            Order::class,
            $orderId,
            LockMode::PESSIMISTIC_READ,
        );
    }
}
```

### Deadlock Prevention

Rules to prevent deadlocks in pessimistic locking:

| Rule | Description | Implementation |
|------|-------------|----------------|
| **Lock ordering** | Always acquire locks in same order | Sort entities by ID before locking |
| **Lock timeout** | Set maximum wait time | `innodb_lock_wait_timeout` |
| **Short transactions** | Minimize lock duration | Keep business logic outside lock scope |
| **Retry on deadlock** | Catch deadlock and retry | Detect SQLSTATE 40001 |

```php
<?php

declare(strict_types=1);

namespace Persistence;

final readonly class DeadlockRetryExecutor
{
    public function __construct(
        private int $maxRetries = 3,
    ) {}

    public function execute(callable $operation): mixed
    {
        for ($attempt = 1; $attempt <= $this->maxRetries; $attempt++) {
            try {
                return $operation();
            } catch (\PDOException $e) {
                if ($e->getCode() !== '40001' || $attempt === $this->maxRetries) {
                    throw $e;
                }
                usleep(random_int(1_000, 10_000) * $attempt);
            }
        }

        throw new \LogicException('Unreachable');
    }
}
```

## Distributed Locks

### Redis SETNX + TTL

The basic distributed lock pattern using Redis SET with NX (Not eXists) and PX (millisecond expiry):

```php
<?php

declare(strict_types=1);

namespace Lock;

final readonly class RedisDistributedLock
{
    public function __construct(
        private \Redis $redis,
        private int $defaultTtlMs = 10_000,
    ) {}

    public function acquire(string $resource, string $token, ?int $ttlMs = null): bool
    {
        $ttl = $ttlMs ?? $this->defaultTtlMs;
        $key = sprintf('lock:%s', $resource);

        return $this->redis->set($key, $token, ['NX', 'PX' => $ttl]) === true;
    }

    public function release(string $resource, string $token): bool
    {
        $script = <<<'LUA'
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
        LUA;

        return $this->redis->eval($script, [sprintf('lock:%s', $resource), $token], 1) === 1;
    }

    public function extend(string $resource, string $token, int $ttlMs): bool
    {
        $script = <<<'LUA'
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("pexpire", KEYS[1], ARGV[2])
            else
                return 0
            end
        LUA;

        return $this->redis->eval(
            $script,
            [sprintf('lock:%s', $resource), $token, (string) $ttlMs],
            1,
        ) === 1;
    }
}
```

### Redlock Algorithm

Redlock provides stronger guarantees across multiple Redis instances:

| Step | Action | Description |
|------|--------|-------------|
| 1 | Get current time | Record start timestamp |
| 2 | Acquire on N instances | Try SET NX PX on each Redis node |
| 3 | Calculate elapsed time | Must be less than TTL |
| 4 | Verify quorum | Need N/2+1 successful acquisitions |
| 5 | Use or release | If quorum met, lock acquired; otherwise release all |

### Symfony Lock Component

```php
<?php

declare(strict_types=1);

namespace Lock;

use Symfony\Component\Lock\LockFactory;
use Symfony\Component\Lock\Store\RedisStore;

final readonly class SymfonyLockAdapter
{
    private LockFactory $factory;

    public function __construct(\Redis $redis)
    {
        $store = new RedisStore($redis);
        $this->factory = new LockFactory($store);
    }

    public function executeWithLock(string $resource, callable $operation, float $ttl = 30.0): mixed
    {
        $lock = $this->factory->createLock($resource, $ttl);

        if (!$lock->acquire()) {
            throw new LockAcquisitionException($resource);
        }

        try {
            return $operation();
        } finally {
            $lock->release();
        }
    }

    public function executeBlockingLock(string $resource, callable $operation, float $ttl = 30.0): mixed
    {
        $lock = $this->factory->createLock($resource, $ttl);
        $lock->acquire(blocking: true);

        try {
            return $operation();
        } finally {
            $lock->release();
        }
    }
}
```

## Lock Selection Guide

| Scenario | Lock Type | Rationale |
|----------|-----------|-----------|
| Low contention, read-heavy | Optimistic (Version) | No lock overhead on reads |
| High contention, write-heavy | Pessimistic (FOR UPDATE) | Prevents wasted retries |
| Cross-process / multi-instance | Distributed (Redis) | Shared lock state |
| Critical section, high durability | Redlock | Tolerates Redis node failures |
| Symfony application | Symfony Lock | Framework integration, multiple backends |
| Queue worker processing | SKIP LOCKED | Non-blocking row-level queue |
