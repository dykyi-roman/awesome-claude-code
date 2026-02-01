# Circuit Breaker Pattern Templates

## CircuitState Enum

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitState.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

enum CircuitState: string
{
    case Closed = 'closed';
    case Open = 'open';
    case HalfOpen = 'half_open';

    public function allowsRequest(): bool
    {
        return $this !== self::Open;
    }

    public function canTransitionTo(self $next): bool
    {
        return match ($this) {
            self::Closed => $next === self::Open,
            self::Open => $next === self::HalfOpen,
            self::HalfOpen => in_array($next, [self::Closed, self::Open], true),
        };
    }

    public function isTripping(): bool
    {
        return $this === self::Closed;
    }

    public function isRecovering(): bool
    {
        return $this === self::HalfOpen;
    }
}
```

---

## CircuitBreakerConfig

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitBreakerConfig.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

final readonly class CircuitBreakerConfig
{
    public function __construct(
        public int $failureThreshold = 5,
        public int $successThreshold = 3,
        public int $openTimeoutSeconds = 30,
        public int $halfOpenMaxAttempts = 3
    ) {
        if ($this->failureThreshold < 1) {
            throw new \InvalidArgumentException('Failure threshold must be at least 1');
        }
        if ($this->successThreshold < 1) {
            throw new \InvalidArgumentException('Success threshold must be at least 1');
        }
        if ($this->openTimeoutSeconds < 1) {
            throw new \InvalidArgumentException('Open timeout must be at least 1 second');
        }
    }

    public static function default(): self
    {
        return new self();
    }

    public static function aggressive(): self
    {
        return new self(
            failureThreshold: 3,
            successThreshold: 5,
            openTimeoutSeconds: 60
        );
    }

    public static function lenient(): self
    {
        return new self(
            failureThreshold: 10,
            successThreshold: 2,
            openTimeoutSeconds: 15
        );
    }
}
```

---

## CircuitBreakerException

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitBreakerException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

final class CircuitBreakerException extends \RuntimeException
{
    public function __construct(
        public readonly string $serviceName,
        public readonly CircuitState $state
    ) {
        parent::__construct(
            sprintf('Circuit breaker for "%s" is %s', $serviceName, $state->value)
        );
    }

    public static function open(string $serviceName): self
    {
        return new self($serviceName, CircuitState::Open);
    }
}
```

---

## CircuitBreaker

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitBreaker.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

use Psr\Clock\ClockInterface;
use Psr\Log\LoggerInterface;

final class CircuitBreaker
{
    private CircuitState $state = CircuitState::Closed;
    private int $failureCount = 0;
    private int $successCount = 0;
    private ?\DateTimeImmutable $openedAt = null;

    public function __construct(
        private readonly string $name,
        private readonly CircuitBreakerConfig $config,
        private readonly ClockInterface $clock,
        private readonly LoggerInterface $logger
    ) {}

    /**
     * @template T
     * @param callable(): T $operation
     * @param callable(): T|null $fallback
     * @return T
     * @throws CircuitBreakerException
     */
    public function execute(callable $operation, ?callable $fallback = null): mixed
    {
        if (!$this->canExecute()) {
            if ($fallback !== null) {
                return $fallback();
            }
            throw CircuitBreakerException::open($this->name);
        }

        try {
            $result = $operation();
            $this->recordSuccess();
            return $result;
        } catch (\Throwable $e) {
            $this->recordFailure($e);
            throw $e;
        }
    }

    public function canExecute(): bool
    {
        if ($this->state === CircuitState::Closed) {
            return true;
        }

        if ($this->state === CircuitState::Open) {
            if ($this->shouldAttemptReset()) {
                $this->transitionTo(CircuitState::HalfOpen);
                return true;
            }
            return false;
        }

        return $this->successCount < $this->config->halfOpenMaxAttempts;
    }

    private function shouldAttemptReset(): bool
    {
        if ($this->openedAt === null) {
            return false;
        }

        $now = $this->clock->now();
        $elapsed = $now->getTimestamp() - $this->openedAt->getTimestamp();

        return $elapsed >= $this->config->openTimeoutSeconds;
    }

    private function recordSuccess(): void
    {
        $this->failureCount = 0;

        if ($this->state === CircuitState::HalfOpen) {
            $this->successCount++;

            if ($this->successCount >= $this->config->successThreshold) {
                $this->transitionTo(CircuitState::Closed);
            }
        }
    }

    private function recordFailure(\Throwable $exception): void
    {
        $this->failureCount++;

        if ($this->state === CircuitState::HalfOpen) {
            $this->transitionTo(CircuitState::Open);
            return;
        }

        if ($this->failureCount >= $this->config->failureThreshold) {
            $this->transitionTo(CircuitState::Open);
        }
    }

    private function transitionTo(CircuitState $newState): void
    {
        $this->state = $newState;

        if ($newState === CircuitState::Open) {
            $this->openedAt = $this->clock->now();
        }

        if ($newState === CircuitState::Closed) {
            $this->reset();
        }

        if ($newState === CircuitState::HalfOpen) {
            $this->successCount = 0;
        }
    }

    private function reset(): void
    {
        $this->failureCount = 0;
        $this->successCount = 0;
        $this->openedAt = null;
    }

    public function getState(): CircuitState
    {
        return $this->state;
    }

    public function forceOpen(): void
    {
        $this->transitionTo(CircuitState::Open);
    }

    public function forceClose(): void
    {
        $this->transitionTo(CircuitState::Closed);
    }
}
```

---

## CircuitBreakerFactory

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitBreakerFactory.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

use Psr\Clock\ClockInterface;
use Psr\Log\LoggerInterface;

final readonly class CircuitBreakerFactory
{
    /**
     * @param array<string, CircuitBreakerConfig> $serviceConfigs
     */
    public function __construct(
        private ClockInterface $clock,
        private LoggerInterface $logger,
        private CircuitBreakerConfig $defaultConfig = new CircuitBreakerConfig(),
        private array $serviceConfigs = []
    ) {}

    public function create(string $serviceName): CircuitBreaker
    {
        $config = $this->serviceConfigs[$serviceName] ?? $this->defaultConfig;

        return new CircuitBreaker(
            name: $serviceName,
            config: $config,
            clock: $this->clock,
            logger: $this->logger
        );
    }
}
```

---

## CircuitBreakerRegistry

**File:** `src/Infrastructure/Resilience/CircuitBreaker/CircuitBreakerRegistry.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\CircuitBreaker;

final class CircuitBreakerRegistry
{
    /** @var array<string, CircuitBreaker> */
    private array $breakers = [];

    public function __construct(
        private readonly CircuitBreakerFactory $factory
    ) {}

    public function get(string $serviceName): CircuitBreaker
    {
        if (!isset($this->breakers[$serviceName])) {
            $this->breakers[$serviceName] = $this->factory->create($serviceName);
        }

        return $this->breakers[$serviceName];
    }

    /**
     * @return array<string, CircuitState>
     */
    public function getStates(): array
    {
        $states = [];
        foreach ($this->breakers as $name => $breaker) {
            $states[$name] = $breaker->getState();
        }
        return $states;
    }

    public function resetAll(): void
    {
        foreach ($this->breakers as $breaker) {
            $breaker->forceClose();
        }
    }
}
```
