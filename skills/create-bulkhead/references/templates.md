# Bulkhead Pattern Templates

## BulkheadInterface

**File:** `src/Infrastructure/Resilience/Bulkhead/BulkheadInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

interface BulkheadInterface
{
    /**
     * @template T
     * @param callable(): T $operation
     * @return T
     * @throws BulkheadFullException
     */
    public function execute(callable $operation): mixed;

    public function tryAcquire(): bool;

    public function release(): void;

    public function getAvailablePermits(): int;

    public function getActiveCount(): int;

    public function getName(): string;
}
```

---

## BulkheadConfig Value Object

**File:** `src/Infrastructure/Resilience/Bulkhead/BulkheadConfig.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final readonly class BulkheadConfig
{
    public function __construct(
        public int $maxConcurrentCalls = 10,
        public int $maxWaitDuration = 0,
        public bool $fairness = true
    ) {
        if ($this->maxConcurrentCalls < 1) {
            throw new \InvalidArgumentException('Max concurrent calls must be at least 1');
        }
        if ($this->maxWaitDuration < 0) {
            throw new \InvalidArgumentException('Max wait duration must be non-negative');
        }
    }

    public static function default(): self
    {
        return new self();
    }

    public static function forCpuBound(int $cpuCores): self
    {
        return new self(maxConcurrentCalls: $cpuCores);
    }

    public static function forIoBound(int $cpuCores): self
    {
        return new self(maxConcurrentCalls: $cpuCores * 10);
    }

    public static function forExternalService(int $maxConnections): self
    {
        return new self(
            maxConcurrentCalls: $maxConnections,
            maxWaitDuration: 5000
        );
    }
}
```

---

## BulkheadFullException

**File:** `src/Infrastructure/Resilience/Bulkhead/BulkheadFullException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

final class BulkheadFullException extends \RuntimeException
{
    public function __construct(
        public readonly string $bulkheadName,
        public readonly int $maxPermits,
        public readonly int $activeCount
    ) {
        parent::__construct(
            sprintf(
                'Bulkhead "%s" is full. Max permits: %d, Active: %d',
                $bulkheadName,
                $maxPermits,
                $activeCount
            )
        );
    }
}
```

---

## SemaphoreBulkhead

**File:** `src/Infrastructure/Resilience/Bulkhead/SemaphoreBulkhead.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

use Psr\Log\LoggerInterface;

final class SemaphoreBulkhead implements BulkheadInterface
{
    private int $activeCount = 0;
    private \SplQueue $waitQueue;
    private array $metrics = [
        'acquired' => 0,
        'rejected' => 0,
        'released' => 0,
    ];

    public function __construct(
        private readonly string $name,
        private readonly BulkheadConfig $config,
        private readonly LoggerInterface $logger
    ) {
        $this->waitQueue = new \SplQueue();
    }

    public function execute(callable $operation): mixed
    {
        if (!$this->acquire()) {
            throw new BulkheadFullException(
                $this->name,
                $this->config->maxConcurrentCalls,
                $this->activeCount
            );
        }

        try {
            return $operation();
        } finally {
            $this->release();
        }
    }

    public function tryAcquire(): bool
    {
        if ($this->activeCount < $this->config->maxConcurrentCalls) {
            $this->activeCount++;
            $this->metrics['acquired']++;

            $this->logger->debug('Bulkhead permit acquired', [
                'bulkhead' => $this->name,
                'active' => $this->activeCount,
                'max' => $this->config->maxConcurrentCalls,
            ]);

            return true;
        }

        return false;
    }

    public function release(): void
    {
        if ($this->activeCount > 0) {
            $this->activeCount--;
            $this->metrics['released']++;

            $this->logger->debug('Bulkhead permit released', [
                'bulkhead' => $this->name,
                'active' => $this->activeCount,
            ]);
        }
    }

    public function getAvailablePermits(): int
    {
        return max(0, $this->config->maxConcurrentCalls - $this->activeCount);
    }

    public function getActiveCount(): int
    {
        return $this->activeCount;
    }

    public function getName(): string
    {
        return $this->name;
    }

    public function getMetrics(): array
    {
        return [
            ...$this->metrics,
            'active' => $this->activeCount,
            'available' => $this->getAvailablePermits(),
            'max' => $this->config->maxConcurrentCalls,
        ];
    }

    private function acquire(): bool
    {
        if ($this->tryAcquire()) {
            return true;
        }

        if ($this->config->maxWaitDuration === 0) {
            $this->metrics['rejected']++;
            return false;
        }

        $deadline = microtime(true) + ($this->config->maxWaitDuration / 1000);

        while (microtime(true) < $deadline) {
            if ($this->tryAcquire()) {
                return true;
            }
            usleep(1000);
        }

        $this->metrics['rejected']++;
        $this->logger->warning('Bulkhead wait timeout', [
            'bulkhead' => $this->name,
            'wait_duration_ms' => $this->config->maxWaitDuration,
        ]);

        return false;
    }
}
```

---

## BulkheadRegistry

**File:** `src/Infrastructure/Resilience/Bulkhead/BulkheadRegistry.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

use Psr\Log\LoggerInterface;

final class BulkheadRegistry
{
    /** @var array<string, BulkheadInterface> */
    private array $bulkheads = [];

    /** @var array<string, BulkheadConfig> */
    private array $configs = [];

    public function __construct(
        private readonly LoggerInterface $logger,
        private readonly BulkheadConfig $defaultConfig = new BulkheadConfig()
    ) {}

    public function register(string $name, BulkheadConfig $config): self
    {
        $this->configs[$name] = $config;
        return $this;
    }

    public function get(string $name): BulkheadInterface
    {
        if (!isset($this->bulkheads[$name])) {
            $config = $this->configs[$name] ?? $this->defaultConfig;
            $this->bulkheads[$name] = new SemaphoreBulkhead($name, $config, $this->logger);
        }

        return $this->bulkheads[$name];
    }

    public function has(string $name): bool
    {
        return isset($this->bulkheads[$name]);
    }

    /**
     * @return array<string, array>
     */
    public function getAllMetrics(): array
    {
        $metrics = [];
        foreach ($this->bulkheads as $name => $bulkhead) {
            if ($bulkhead instanceof SemaphoreBulkhead) {
                $metrics[$name] = $bulkhead->getMetrics();
            }
        }
        return $metrics;
    }
}
```

---

## DistributedSemaphoreBulkhead (Redis-based)

**File:** `src/Infrastructure/Resilience/Bulkhead/DistributedSemaphoreBulkhead.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

use Psr\Log\LoggerInterface;

final class DistributedSemaphoreBulkhead implements BulkheadInterface
{
    private const KEY_PREFIX = 'bulkhead:';
    private const PERMIT_TTL = 60;

    private ?string $permitId = null;

    public function __construct(
        private readonly string $name,
        private readonly BulkheadConfig $config,
        private readonly \Redis $redis,
        private readonly LoggerInterface $logger
    ) {}

    public function execute(callable $operation): mixed
    {
        if (!$this->acquire()) {
            throw new BulkheadFullException(
                $this->name,
                $this->config->maxConcurrentCalls,
                $this->getActiveCount()
            );
        }

        try {
            return $operation();
        } finally {
            $this->release();
        }
    }

    public function tryAcquire(): bool
    {
        $key = $this->getKey();
        $permitId = uniqid('permit_', true);

        $script = <<<'LUA'
            local key = KEYS[1]
            local maxPermits = tonumber(ARGV[1])
            local permitId = ARGV[2]
            local ttl = tonumber(ARGV[3])

            local current = redis.call('SCARD', key)
            if current < maxPermits then
                redis.call('SADD', key, permitId)
                redis.call('EXPIRE', key, ttl)
                return permitId
            end
            return nil
        LUA;

        $result = $this->redis->eval(
            $script,
            [$key, $this->config->maxConcurrentCalls, $permitId, self::PERMIT_TTL],
            1
        );

        if ($result !== null) {
            $this->permitId = $permitId;

            $this->logger->debug('Distributed bulkhead permit acquired', [
                'bulkhead' => $this->name,
                'permit_id' => $permitId,
            ]);

            return true;
        }

        return false;
    }

    public function release(): void
    {
        if ($this->permitId === null) {
            return;
        }

        $this->redis->sRem($this->getKey(), $this->permitId);

        $this->logger->debug('Distributed bulkhead permit released', [
            'bulkhead' => $this->name,
            'permit_id' => $this->permitId,
        ]);

        $this->permitId = null;
    }

    public function getAvailablePermits(): int
    {
        return max(0, $this->config->maxConcurrentCalls - $this->getActiveCount());
    }

    public function getActiveCount(): int
    {
        return (int) $this->redis->sCard($this->getKey());
    }

    public function getName(): string
    {
        return $this->name;
    }

    private function acquire(): bool
    {
        if ($this->tryAcquire()) {
            return true;
        }

        if ($this->config->maxWaitDuration === 0) {
            return false;
        }

        $deadline = microtime(true) + ($this->config->maxWaitDuration / 1000);

        while (microtime(true) < $deadline) {
            if ($this->tryAcquire()) {
                return true;
            }
            usleep(10000);
        }

        return false;
    }

    private function getKey(): string
    {
        return self::KEY_PREFIX . $this->name;
    }
}
```

---

## BulkheadDecorator Attribute

**File:** `src/Infrastructure/Resilience/Bulkhead/BulkheadDecorator.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Bulkhead;

#[\Attribute(\Attribute::TARGET_METHOD)]
final readonly class BulkheadDecorator
{
    public function __construct(
        public string $name,
        public int $maxConcurrent = 10,
        public int $maxWaitMs = 0
    ) {}

    public function getConfig(): BulkheadConfig
    {
        return new BulkheadConfig(
            maxConcurrentCalls: $this->maxConcurrent,
            maxWaitDuration: $this->maxWaitMs
        );
    }
}
```
