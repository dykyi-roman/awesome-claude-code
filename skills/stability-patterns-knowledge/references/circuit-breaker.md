# Circuit Breaker Pattern Reference

## State Machine

```
┌─────────────────────────────────────────────────────────────────┐
│                   CIRCUIT BREAKER STATE MACHINE                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│                        failure >= threshold                      │
│                    ┌──────────────────────────┐                  │
│                    │                          │                  │
│                    ▼                          │                  │
│   ┌──────────┐           ┌──────────┐         │                  │
│   │  CLOSED  │◀──────────│   OPEN   │         │                  │
│   │          │  success  │          │         │                  │
│   │ Requests │  threshold│ Requests │         │                  │
│   │ pass     │  reached  │ blocked  │         │                  │
│   └────┬─────┘           └────┬─────┘         │                  │
│        │                      │               │                  │
│        │                      │ timeout       │                  │
│        │                      │ elapsed       │                  │
│        │                      ▼               │                  │
│        │                ┌──────────┐          │                  │
│        └────────────────│HALF-OPEN │──────────┘                  │
│            success      │          │  failure                    │
│                         │ Limited  │                             │
│                         │ requests │                             │
│                         └──────────┘                             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Basic Implementation

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
    private ?\DateTimeImmutable $lastFailureTime = null;

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

    private function canExecute(): bool
    {
        return match ($this->state) {
            CircuitState::Closed => true,
            CircuitState::Open => $this->shouldAttemptReset(),
            CircuitState::HalfOpen => $this->successCount < $this->config->halfOpenMaxAttempts,
        };
    }

    private function shouldAttemptReset(): bool
    {
        if ($this->openedAt === null) {
            return false;
        }

        $elapsed = $this->clock->now()->getTimestamp() - $this->openedAt->getTimestamp();

        if ($elapsed >= $this->config->openTimeoutSeconds) {
            $this->transitionTo(CircuitState::HalfOpen);
            return true;
        }

        return false;
    }

    private function recordSuccess(): void
    {
        if ($this->state === CircuitState::HalfOpen) {
            $this->successCount++;
            if ($this->successCount >= $this->config->successThreshold) {
                $this->transitionTo(CircuitState::Closed);
            }
        } else {
            $this->failureCount = 0;
        }
    }

    private function recordFailure(\Throwable $exception): void
    {
        $this->failureCount++;
        $this->lastFailureTime = $this->clock->now();

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
        $oldState = $this->state;
        $this->state = $newState;

        match ($newState) {
            CircuitState::Open => $this->onOpen(),
            CircuitState::Closed => $this->onClose(),
            CircuitState::HalfOpen => $this->onHalfOpen(),
        };

        $this->logger->info('Circuit breaker state changed', [
            'circuit' => $this->name,
            'from' => $oldState->value,
            'to' => $newState->value,
        ]);
    }

    private function onOpen(): void
    {
        $this->openedAt = $this->clock->now();
    }

    private function onClose(): void
    {
        $this->failureCount = 0;
        $this->successCount = 0;
        $this->openedAt = null;
    }

    private function onHalfOpen(): void
    {
        $this->successCount = 0;
    }
}
```

## Configuration Best Practices

### Service Type Configuration

```php
<?php

// Payment Gateway - Critical, need fast failover
$paymentConfig = new CircuitBreakerConfig(
    failureThreshold: 3,
    successThreshold: 3,
    openTimeoutSeconds: 30,
    halfOpenMaxAttempts: 2
);

// Email Service - Non-critical, can retry more
$emailConfig = new CircuitBreakerConfig(
    failureThreshold: 10,
    successThreshold: 2,
    openTimeoutSeconds: 60,
    halfOpenMaxAttempts: 5
);

// Internal Microservice - Quick recovery
$internalConfig = new CircuitBreakerConfig(
    failureThreshold: 5,
    successThreshold: 2,
    openTimeoutSeconds: 15,
    halfOpenMaxAttempts: 3
);
```

## Exception Filtering

```php
<?php

final class CircuitBreaker
{
    /** @var array<class-string<\Throwable>> */
    private array $recordedExceptions = [
        ConnectionException::class,
        TimeoutException::class,
        ServiceUnavailableException::class,
    ];

    /** @var array<class-string<\Throwable>> */
    private array $ignoredExceptions = [
        NotFoundException::class,
        ValidationException::class,
        AuthenticationException::class,
    ];

    private function shouldRecordFailure(\Throwable $e): bool
    {
        foreach ($this->ignoredExceptions as $ignored) {
            if ($e instanceof $ignored) {
                return false;
            }
        }

        if ($this->recordedExceptions === []) {
            return true;
        }

        foreach ($this->recordedExceptions as $recorded) {
            if ($e instanceof $recorded) {
                return true;
            }
        }

        return false;
    }
}
```

## Metrics and Monitoring

```php
<?php

final class CircuitBreakerMetrics
{
    public function __construct(
        public readonly string $name,
        public readonly CircuitState $state,
        public readonly int $failureCount,
        public readonly int $successCount,
        public readonly int $totalCalls,
        public readonly int $failedCalls,
        public readonly int $rejectedCalls,
        public readonly float $failureRate,
        public readonly ?\DateTimeImmutable $lastFailure,
        public readonly ?\DateTimeImmutable $lastStateChange
    ) {}

    public function toArray(): array
    {
        return [
            'name' => $this->name,
            'state' => $this->state->value,
            'failure_count' => $this->failureCount,
            'success_count' => $this->successCount,
            'total_calls' => $this->totalCalls,
            'failed_calls' => $this->failedCalls,
            'rejected_calls' => $this->rejectedCalls,
            'failure_rate' => $this->failureRate,
            'last_failure' => $this->lastFailure?->format('c'),
            'last_state_change' => $this->lastStateChange?->format('c'),
        ];
    }
}
```

## Anti-patterns

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Single global breaker | All services fail together | Per-service breakers |
| No fallback | Hard failure when open | Implement graceful degradation |
| Breaker in domain | Infrastructure leak | Keep in Infrastructure layer |
| No monitoring | Can't observe circuit health | Add metrics/logging |
| Wrong thresholds | Too sensitive/insensitive | Tune based on SLAs |
| No manual override | Can't intervene | Add force open/close |
