# Bulkhead Pattern Reference

## Isolation Concept

```
┌─────────────────────────────────────────────────────────────────┐
│                   BULKHEAD ISOLATION                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   WITHOUT Bulkhead              WITH Bulkhead                    │
│                                                                  │
│   ┌──────────────────┐         ┌──────────────────┐             │
│   │   Shared Pool    │         │   Pool A (10)    │             │
│   │   (all services) │         │  ┌────────────┐  │             │
│   │  ┌────────────┐  │         │  │ Service A  │  │             │
│   │  │ Service A  │  │         │  └────────────┘  │             │
│   │  │ Service B  │  │         ├──────────────────┤             │
│   │  │ Service C  │  │         │   Pool B (5)     │             │
│   │  │ ■■■■■■■■■■ │  │         │  ┌────────────┐  │             │
│   │  │ exhausted! │  │         │  │ Service B  │  │             │
│   │  └────────────┘  │         │  └────────────┘  │             │
│   │                  │         ├──────────────────┤             │
│   │  Service C slow  │         │   Pool C (5)     │             │
│   │  → A & B blocked │         │  ┌────────────┐  │             │
│   │                  │         │  │ Service C  │  │             │
│   └──────────────────┘         │  └────────────┘  │             │
│                                │                  │             │
│   One failure sinks all        │  C fails → A & B │             │
│                                │  still working   │             │
│                                └──────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Semaphore-Based Bulkhead

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final class SemaphoreBulkhead implements BulkheadInterface
{
    public function __construct(
        private readonly string $name,
        private readonly BulkheadConfig $config,
        private readonly \Redis $redis,
        private readonly string $prefix = 'bulkhead:'
    ) {}

    /**
     * @template T
     * @param callable(): T $operation
     * @return T
     * @throws BulkheadRejectedException
     */
    public function execute(callable $operation): mixed
    {
        if (!$this->acquire()) {
            throw BulkheadRejectedException::limitReached(
                $this->name,
                $this->config->maxConcurrent
            );
        }

        try {
            return $operation();
        } finally {
            $this->release();
        }
    }

    private function acquire(): bool
    {
        $key = $this->prefix . $this->name;
        $deadline = microtime(true) + ($this->config->maxWaitSeconds);

        while (microtime(true) < $deadline) {
            $current = (int)$this->redis->get($key);

            if ($current < $this->config->maxConcurrent) {
                $new = $this->redis->incr($key);
                if ($new <= $this->config->maxConcurrent) {
                    $this->redis->expire($key, $this->config->timeoutSeconds);
                    return true;
                }
                // Another process got in first, decrement and retry
                $this->redis->decr($key);
            }

            usleep(10_000); // 10ms backoff
        }

        return false;
    }

    private function release(): void
    {
        $key = $this->prefix . $this->name;
        $this->redis->decr($key);
    }
}
```

## Bulkhead Configuration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final readonly class BulkheadConfig
{
    public function __construct(
        public int $maxConcurrent,
        public float $maxWaitSeconds = 1.0,
        public int $timeoutSeconds = 30,
    ) {}
}

interface BulkheadInterface
{
    /**
     * @template T
     * @param callable(): T $operation
     * @return T
     * @throws BulkheadRejectedException
     */
    public function execute(callable $operation): mixed;
}

final class BulkheadRejectedException extends \RuntimeException
{
    public static function limitReached(string $name, int $limit): self
    {
        return new self(sprintf(
            'Bulkhead "%s" rejected request: max concurrent limit (%d) reached',
            $name,
            $limit,
        ));
    }
}
```

## Connection Pool Isolation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

use Psr\Log\LoggerInterface;

final class ConnectionPoolBulkhead
{
    /** @var array<string, int> */
    private array $activeCounts = [];

    /** @var array<string, BulkheadConfig> */
    private readonly array $pools;

    /**
     * @param array<string, BulkheadConfig> $pools
     */
    public function __construct(
        array $pools,
        private readonly LoggerInterface $logger
    ) {
        $this->pools = $pools;
        foreach (array_keys($pools) as $name) {
            $this->activeCounts[$name] = 0;
        }
    }

    /**
     * @template T
     * @param callable(): T $operation
     * @return T
     */
    public function execute(string $poolName, callable $operation): mixed
    {
        if (!isset($this->pools[$poolName])) {
            throw new \InvalidArgumentException(
                sprintf('Unknown pool: %s', $poolName)
            );
        }

        $config = $this->pools[$poolName];

        if ($this->activeCounts[$poolName] >= $config->maxConcurrent) {
            $this->logger->warning('Bulkhead pool saturated', [
                'pool' => $poolName,
                'active' => $this->activeCounts[$poolName],
                'limit' => $config->maxConcurrent,
            ]);
            throw BulkheadRejectedException::limitReached($poolName, $config->maxConcurrent);
        }

        $this->activeCounts[$poolName]++;

        try {
            return $operation();
        } finally {
            $this->activeCounts[$poolName]--;
        }
    }

    public function getMetrics(string $poolName): array
    {
        return [
            'pool' => $poolName,
            'active' => $this->activeCounts[$poolName] ?? 0,
            'limit' => $this->pools[$poolName]?->maxConcurrent ?? 0,
            'available' => ($this->pools[$poolName]?->maxConcurrent ?? 0)
                - ($this->activeCounts[$poolName] ?? 0),
        ];
    }
}
```

## Queue-Based Bulkhead

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final class QueueBulkhead implements BulkheadInterface
{
    public function __construct(
        private readonly string $name,
        private readonly BulkheadConfig $config,
        private readonly \Redis $redis,
        private readonly string $prefix = 'queue_bulkhead:'
    ) {}

    public function execute(callable $operation): mixed
    {
        $activeKey = $this->prefix . $this->name . ':active';
        $queueKey = $this->prefix . $this->name . ':queue';
        $requestId = bin2hex(random_bytes(16));

        // Enqueue the request
        $this->redis->rPush($queueKey, $requestId);
        $this->redis->expire($queueKey, $this->config->timeoutSeconds);

        $deadline = microtime(true) + $this->config->maxWaitSeconds;

        while (microtime(true) < $deadline) {
            $active = (int)$this->redis->get($activeKey);
            $next = $this->redis->lIndex($queueKey, 0);

            if ($active < $this->config->maxConcurrent && $next === $requestId) {
                $this->redis->lPop($queueKey);
                $this->redis->incr($activeKey);
                $this->redis->expire($activeKey, $this->config->timeoutSeconds);

                try {
                    return $operation();
                } finally {
                    $this->redis->decr($activeKey);
                }
            }

            usleep(10_000); // 10ms polling interval
        }

        // Timeout: remove from queue
        $this->redis->lRem($queueKey, 1, $requestId);
        throw BulkheadRejectedException::limitReached($this->name, $this->config->maxConcurrent);
    }
}
```

## Bulkhead Registry

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final class BulkheadRegistry
{
    /** @var array<string, BulkheadInterface> */
    private array $bulkheads = [];

    public function __construct(
        private readonly \Redis $redis
    ) {}

    public function get(string $name, BulkheadConfig $config): BulkheadInterface
    {
        if (!isset($this->bulkheads[$name])) {
            $this->bulkheads[$name] = new SemaphoreBulkhead(
                name: $name,
                config: $config,
                redis: $this->redis,
            );
        }

        return $this->bulkheads[$name];
    }
}
```

## Detection Patterns

```bash
# Find bulkhead implementations
Grep: "Bulkhead|Semaphore|maxConcurrent" --glob "**/*.php"

# Detect shared connection pools (anti-pattern)
Grep: "new.*Client\(|ConnectionPool|createConnection" --glob "**/Infrastructure/**/*.php"

# Find queue isolation
Grep: "queue.*bulkhead|separate.*queue|isolated.*queue" --glob "**/*.php"

# Check for resource limits
Grep: "sem_acquire|sem_get|SysvSemaphore" --glob "**/*.php"
```

## Configuration Example

```php
<?php

// DI container wiring — isolated pools per external service
$container->set(BulkheadRegistry::class, function () use ($redis) {
    return new BulkheadRegistry(redis: $redis);
});

// Per-service bulkhead configuration
$container->set('bulkhead.payment', fn() => $container
    ->get(BulkheadRegistry::class)
    ->get('payment-gateway', new BulkheadConfig(
        maxConcurrent: 10,
        maxWaitSeconds: 2.0,
        timeoutSeconds: 30,
    ))
);

$container->set('bulkhead.email', fn() => $container
    ->get(BulkheadRegistry::class)
    ->get('email-service', new BulkheadConfig(
        maxConcurrent: 20,
        maxWaitSeconds: 5.0,
        timeoutSeconds: 60,
    ))
);

$container->set('bulkhead.search', fn() => $container
    ->get(BulkheadRegistry::class)
    ->get('search-engine', new BulkheadConfig(
        maxConcurrent: 15,
        maxWaitSeconds: 1.0,
        timeoutSeconds: 10,
    ))
);
```

## DDD Integration

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Domain Layer                  Application Layer                │
│   ┌───────────────────┐        ┌──────────────────────────┐     │
│   │ ServicePort       │◀───────│ UseCase                  │     │
│   │ (interface)       │        │ calls port, unaware of   │     │
│   │                   │        │ bulkhead isolation        │     │
│   └───────────────────┘        └──────────────────────────┘     │
│            ▲                                                     │
│            │ implements                                          │
│   Infrastructure Layer                                           │
│   ┌───────────────────┐                                         │
│   │ BulkheadAdapter   │──▶ wraps actual service client          │
│   │ (decorator)       │   with SemaphoreBulkhead.execute()      │
│   └───────────────────┘                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

The bulkhead is an Infrastructure wrapper. The Domain defines a port (interface) for the external service call. The Infrastructure adapter decorates the actual client with bulkhead isolation. The Application layer remains unaware of concurrency limits.

## Combining Bulkhead with Circuit Breaker

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience;

use Infrastructure\Resilience\Bulkhead\BulkheadInterface;
use Infrastructure\Resilience\CircuitBreaker\CircuitBreaker;

final readonly class ResilientServiceClient
{
    public function __construct(
        private BulkheadInterface $bulkhead,
        private CircuitBreaker $circuitBreaker
    ) {}

    /**
     * Defense-in-depth: bulkhead limits concurrency,
     * circuit breaker prevents calls to failing services.
     *
     * @template T
     * @param callable(): T $operation
     * @param callable(): T|null $fallback
     * @return T
     */
    public function execute(callable $operation, ?callable $fallback = null): mixed
    {
        return $this->bulkhead->execute(
            fn() => $this->circuitBreaker->execute($operation, $fallback)
        );
    }
}
```

## Anti-patterns

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Shared pool for all services | One slow service exhausts all connections | Isolated pool per external service |
| No wait timeout | Threads block indefinitely | Set maxWaitSeconds, fail fast |
| Bulkhead in domain layer | Infrastructure leak | Keep in Infrastructure as adapter |
| No monitoring | Can't detect saturation | Log rejections, export metrics |
| Over-provisioned limits | No actual protection | Size limits based on downstream capacity |
| No fallback on rejection | Hard failure for users | Provide degraded response |

## Summary

| Bulkhead Type | Implementation | Use Case |
|---------------|----------------|----------|
| **Semaphore** | Redis counter with incr/decr | Multi-instance apps, distributed limiting |
| **Connection Pool** | In-process counter per pool | Single-process, connection isolation |
| **Queue-based** | Redis list + active counter | Fair ordering, request queuing |
| **SysV Semaphore** | `sem_get()`/`sem_acquire()` | Single-server, OS-level isolation |
