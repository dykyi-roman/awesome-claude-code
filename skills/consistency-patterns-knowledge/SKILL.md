---
name: consistency-patterns-knowledge
description: Consistency Patterns knowledge base. Provides strong vs eventual consistency, idempotency keys, optimistic/pessimistic locking, conflict resolution, and saga compensation patterns for distributed systems audits.
---

# Consistency Patterns Knowledge Base

Quick reference for consistency guarantees, locking strategies, idempotency, and conflict resolution in distributed PHP applications.

## Strong vs Eventual Consistency

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CONSISTENCY DECISION TREE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                   Is data safety-critical?                                    │
│                      (money, inventory)                                       │
│                        /          \                                           │
│                      YES           NO                                         │
│                      /              \                                         │
│              Single write      Can tolerate                                   │
│              location?         stale reads?                                   │
│               /      \           /       \                                    │
│             YES      NO        YES       NO                                  │
│              |        |         |          |                                  │
│              ▼        ▼         ▼          ▼                                  │
│          ┌───────┐ ┌────────┐ ┌────────┐ ┌──────────┐                        │
│          │Strong │ │Saga +  │ │Eventual│ │Lineariz- │                        │
│          │(ACID) │ │Compen- │ │Consist.│ │able      │                        │
│          │       │ │sation  │ │+ TTL   │ │Reads     │                        │
│          └───────┘ └────────┘ └────────┘ └──────────┘                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Property | Strong Consistency | Eventual Consistency |
|----------|-------------------|---------------------|
| **Guarantee** | All reads return latest write | Reads may return stale data temporarily |
| **Latency** | Higher (synchronous coordination) | Lower (async propagation) |
| **Availability** | Lower (CAP theorem trade-off) | Higher (tolerates partitions) |
| **Scalability** | Limited by coordination | Highly scalable |
| **Complexity** | Simpler app logic, harder infra | Simpler infra, harder app logic |
| **Use Cases** | Financial transactions, inventory | Social feeds, analytics, caches |
| **PHP Pattern** | DB transactions, SELECT FOR UPDATE | Event-driven sync, CQRS read models |

## Idempotency Keys

### Overview

Idempotency ensures that performing the same operation multiple times produces the same result. Critical for payment processing, message handling, and API retries.

| Aspect | Details |
|--------|---------|
| **What** | Unique key identifying a specific operation attempt |
| **Why** | Safe retries, at-least-once delivery semantics, duplicate prevention |
| **Format** | UUIDv4 or `{client-id}:{operation}:{unique-ref}` |
| **Storage** | Redis (fast, TTL) or DB (durable, queryable) |
| **TTL** | 24-72 hours depending on retry window |

### Delivery Guarantees

| Guarantee | Description | Idempotency Needed? |
|-----------|-------------|---------------------|
| **At-most-once** | Fire and forget, may lose messages | No |
| **At-least-once** | Retries until ACK, may duplicate | Yes |
| **Exactly-once** | Process exactly once (hard) | Built-in deduplication |

### Idempotency Middleware (PSR-15)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class IdempotencyMiddleware implements MiddlewareInterface
{
    private const string HEADER = 'Idempotency-Key';

    public function __construct(
        private \Redis $redis,
        private int $ttlSeconds = 86400,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        if ($request->getMethod() === 'GET') {
            return $handler->handle($request);
        }

        $key = $request->getHeaderLine(self::HEADER);
        if ($key === '') {
            return $handler->handle($request);
        }

        $cacheKey = sprintf('idempotency:%s', $key);
        $cached = $this->redis->get($cacheKey);

        if ($cached !== false) {
            return unserialize($cached, ['allowed_classes' => true]);
        }

        $response = $handler->handle($request);

        $this->redis->setex($cacheKey, $this->ttlSeconds, serialize($response));

        return $response;
    }
}
```

## Optimistic Locking

Assumes conflicts are rare. Reads a version, performs work, writes only if version unchanged.

| Component | Description |
|-----------|-------------|
| **Mechanism** | Version column incremented on each update |
| **Conflict Detection** | `WHERE version = :expected` in UPDATE |
| **On Conflict** | Throw exception, retry or return error |
| **Best For** | Read-heavy workloads, low contention |
| **Doctrine** | `#[ORM\Version]` attribute on integer/datetime column |

### Doctrine Versioned Entity

```php
<?php

declare(strict_types=1);

namespace Domain\Model;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'products')]
final class Product
{
    #[ORM\Id]
    #[ORM\Column(type: 'string', length: 36)]
    private string $id;

    #[ORM\Column(type: 'string', length: 255)]
    private string $name;

    #[ORM\Column(type: 'integer')]
    private int $stock;

    #[ORM\Version]
    #[ORM\Column(type: 'integer')]
    private int $version = 1;

    public function __construct(string $id, string $name, int $stock)
    {
        $this->id = $id;
        $this->name = $name;
        $this->stock = $stock;
    }

    public function decrementStock(int $quantity): void
    {
        if ($this->stock < $quantity) {
            throw new InsufficientStockException($this->id, $this->stock, $quantity);
        }

        $this->stock -= $quantity;
    }

    public function getVersion(): int
    {
        return $this->version;
    }
}
```

### Handling Optimistic Lock Failures

```php
<?php

declare(strict_types=1);

namespace Application\UseCase;

use Doctrine\ORM\OptimisticLockException;

final readonly class DecrementStockUseCase
{
    public function __construct(
        private ProductRepositoryInterface $repository,
        private int $maxRetries = 3,
    ) {}

    public function execute(string $productId, int $quantity): void
    {
        $attempt = 0;

        while ($attempt < $this->maxRetries) {
            try {
                $product = $this->repository->findById($productId);
                $product->decrementStock($quantity);
                $this->repository->save($product);

                return;
            } catch (OptimisticLockException) {
                $attempt++;
                if ($attempt >= $this->maxRetries) {
                    throw new ConcurrencyConflictException($productId);
                }
                usleep(random_int(10_000, 50_000));
            }
        }
    }
}
```

## Pessimistic Locking

Assumes conflicts are likely. Acquires a lock before reading, blocks other transactions.

| Lock Type | SQL | Behavior |
|-----------|-----|----------|
| **Exclusive (FOR UPDATE)** | `SELECT ... FOR UPDATE` | Blocks reads and writes |
| **Shared (FOR SHARE)** | `SELECT ... FOR SHARE` | Allows reads, blocks writes |
| **NOWAIT** | `SELECT ... FOR UPDATE NOWAIT` | Fails immediately if locked |
| **SKIP LOCKED** | `SELECT ... FOR UPDATE SKIP LOCKED` | Skips locked rows (queue pattern) |

### Deadlock Prevention Rules

1. Always acquire locks in consistent order (e.g., by entity ID ascending)
2. Use lock timeouts (`SET innodb_lock_wait_timeout = 5`)
3. Keep transactions short (< 1 second)
4. Avoid user interaction within transactions

## Conflict Resolution Strategies

| Strategy | Description | Consistency | Complexity |
|----------|-------------|-------------|------------|
| **Last Write Wins (LWW)** | Latest timestamp wins | Weak | Low |
| **First Write Wins** | First write preserved, reject subsequent | Strong | Low |
| **Merge Function** | Custom logic merges conflicting writes | Application-defined | High |
| **CRDTs** | Conflict-free Replicated Data Types | Eventual (mathematically guaranteed) | Medium |
| **Manual Resolution** | Human decides on conflict | Strongest | Variable |

### CRDT Basics

| CRDT Type | Operations | Example Use |
|-----------|-----------|-------------|
| **G-Counter** | Increment only | Page view counter |
| **PN-Counter** | Increment and decrement | Inventory count |
| **G-Set** | Add only | Tag collection |
| **OR-Set** | Add and remove | Shopping cart items |
| **LWW-Register** | Last write wins register | User profile fields |

## Saga Compensation vs Distributed Transactions

| Aspect | Distributed Transaction (2PC) | Saga Pattern |
|--------|------------------------------|-------------|
| **Coordination** | Transaction coordinator | Choreography or orchestration |
| **Locking** | Holds locks across services | No cross-service locks |
| **Consistency** | Strong (ACID) | Eventual (compensating actions) |
| **Availability** | Lower (blocking) | Higher (non-blocking) |
| **Complexity** | Simpler logic, complex infra | Complex logic, simpler infra |
| **Failure Handling** | Rollback | Compensating transactions |
| **Latency** | Higher (2-phase commit) | Lower (async steps) |
| **Scalability** | Poor (locks span services) | Good (independent services) |

### Redis Atomic Operations

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Lock;

final readonly class RedisAtomicOperations
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function acquireLock(string $resource, string $token, int $ttlMs): bool
    {
        return $this->redis->set(
            sprintf('lock:%s', $resource),
            $token,
            ['NX', 'PX' => $ttlMs],
        ) === true;
    }

    public function releaseLock(string $resource, string $token): bool
    {
        $script = <<<'LUA'
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
        LUA;

        return $this->redis->eval(
            $script,
            [sprintf('lock:%s', $resource), $token],
            1,
        ) === 1;
    }

    public function compareAndSwap(string $key, string $expected, string $newValue, int $ttl): bool
    {
        $script = <<<'LUA'
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("setex", KEYS[1], ARGV[3], ARGV[2])
            else
                return 0
            end
        LUA;

        return $this->redis->eval(
            $script,
            [$key, $expected, $newValue, (string) $ttl],
            1,
        ) !== 0;
    }
}
```

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| No locking on shared mutable state | Repositories, aggregates | Critical |
| Missing idempotency on payment endpoints | API controllers, handlers | Critical |
| Optimistic lock exception swallowed silently | Catch blocks, use cases | Critical |
| Long-running pessimistic locks | Transaction scopes | Warning |
| No retry on optimistic lock failure | Use cases, command handlers | Warning |
| Distributed transaction across services | Service-to-service calls | Critical |
| Missing version field on aggregates | Doctrine entities | Warning |
| Idempotency key without TTL | Redis/cache stores | Warning |

## Detection Patterns

```bash
# Optimistic locking
Grep: "@Version|ORM\\\\Version|version" --glob "**/Entity/**/*.php"
Grep: "OptimisticLockException|StaleObjectStateException" --glob "**/*.php"
Grep: "LOCK_OPTIMISTIC|LockMode::OPTIMISTIC" --glob "**/*.php"

# Pessimistic locking
Grep: "FOR UPDATE|FOR SHARE|LOCK_PESSIMISTIC" --glob "**/*.php"
Grep: "LockMode::PESSIMISTIC|SKIP LOCKED|NOWAIT" --glob "**/*.php"

# Idempotency patterns
Grep: "Idempotency|idempotency.key|IdempotencyKey" --glob "**/*.php"
Grep: "deduplication|dedup|duplicate.check" --glob "**/*.php"

# Distributed locks
Grep: "SETNX|NX.*PX|redis.*lock|Lock::acquire" --glob "**/*.php"
Grep: "Redlock|RedisLock|LockFactory" --glob "**/*.php"

# Saga patterns
Grep: "compensat|SagaStep|SagaOrchestrator" --glob "**/*.php"
Grep: "CompensatingAction|rollback|undo" --glob "**/Saga/**/*.php"

# Consistency indicators
Grep: "EventualConsistency|ReadModel|Projection" --glob "**/*.php"
Grep: "transaction|beginTransaction|commit|rollback" --glob "**/*.php"
```

## References

For detailed information, load these reference files:

- `references/locking-patterns.md` — Optimistic locking, pessimistic locking, distributed locks, Redlock algorithm, Symfony Lock component
- `references/idempotency-patterns.md` — Idempotency key generation, deduplication store, PSR-15 middleware, delivery guarantees, non-idempotent operations
