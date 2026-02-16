# Retry Patterns Reference

## Backoff Strategies

```
┌─────────────────────────────────────────────────────────────────┐
│                   BACKOFF STRATEGY COMPARISON                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Delay                                                          │
│   (ms)                                                           │
│    │                                                             │
│ 10s│                                              ┌────          │
│    │                                         ┌────┘              │
│    │                                    ┌────┘                   │
│    │                               ┌────┘  Exponential           │
│  5s│                          ┌────┘                             │
│    │                     ┌────┘                                  │
│    │                ┌────┘                                       │
│    │           ┌────┘─────────────────────────── Linear          │
│  1s│      ┌────┘────────────────────────────────                 │
│    │ ┌────┴─────────────────────────────────────  Fixed          │
│    │─┴───────────────────────────────────────────────────        │
│    └─────┬──────┬──────┬──────┬──────┬──────┬─────▶ Attempt      │
│          1      2      3      4      5      6                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Strategy Formulas

| Strategy | Formula | Example (base=100ms) |
|----------|---------|---------------------|
| **Fixed** | `delay` | 100, 100, 100, 100 |
| **Linear** | `delay * attempt` | 100, 200, 300, 400 |
| **Exponential** | `delay * 2^(attempt-1)` | 100, 200, 400, 800 |
| **Decorrelated** | `min(cap, random(base, prev*3))` | Random within bounds |

## Jitter Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

enum JitterType: string
{
    case None = 'none';
    case Full = 'full';
    case Equal = 'equal';
    case Decorrelated = 'decorrelated';
}

final readonly class JitterCalculator
{
    public function apply(int $delay, JitterType $type): int
    {
        return match ($type) {
            JitterType::None => $delay,
            JitterType::Full => random_int(0, $delay),
            JitterType::Equal => $delay / 2 + random_int(0, $delay / 2),
            JitterType::Decorrelated => $this->decorrelated($delay),
        };
    }

    private function decorrelated(int $delay): int
    {
        static $previous = 0;
        $cap = $delay * 10;
        $result = min($cap, random_int($delay, max($delay, $previous * 3)));
        $previous = $result;
        return $result;
    }
}
```

## Complete Retry Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

use Psr\Log\LoggerInterface;

final class RetryExecutor
{
    public function __construct(
        private readonly LoggerInterface $logger,
        private readonly JitterCalculator $jitter = new JitterCalculator()
    ) {}

    /**
     * @template T
     * @param callable(RetryContext): T $operation
     * @return T
     * @throws RetryExhaustedException
     */
    public function execute(
        callable $operation,
        RetryPolicy $policy
    ): mixed {
        $attempt = 0;
        $exceptions = [];

        while ($attempt < $policy->maxAttempts) {
            $attempt++;

            $context = new RetryContext(
                attempt: $attempt,
                maxAttempts: $policy->maxAttempts,
                exceptions: $exceptions
            );

            try {
                return $operation($context);
            } catch (\Throwable $e) {
                $exceptions[] = $e;

                if (!$this->shouldRetry($e, $policy, $attempt)) {
                    throw new RetryExhaustedException($attempt, $exceptions, $e);
                }

                $delay = $this->calculateDelay($policy, $attempt);

                $this->logger->warning('Operation failed, retrying', [
                    'attempt' => $attempt,
                    'delay_ms' => $delay,
                    'exception' => $e->getMessage(),
                ]);

                $this->sleep($delay);
            }
        }

        throw new RetryExhaustedException($attempt, $exceptions);
    }

    private function shouldRetry(\Throwable $e, RetryPolicy $policy, int $attempt): bool
    {
        if ($attempt >= $policy->maxAttempts) {
            return false;
        }

        foreach ($policy->nonRetryableExceptions as $class) {
            if ($e instanceof $class) {
                return false;
            }
        }

        if ($policy->retryableExceptions === []) {
            return true;
        }

        foreach ($policy->retryableExceptions as $class) {
            if ($e instanceof $class) {
                return true;
            }
        }

        return false;
    }

    private function calculateDelay(RetryPolicy $policy, int $attempt): int
    {
        $delay = match ($policy->strategy) {
            BackoffStrategy::Fixed => $policy->baseDelayMs,
            BackoffStrategy::Linear => $policy->baseDelayMs * $attempt,
            BackoffStrategy::Exponential => (int)($policy->baseDelayMs * (2 ** ($attempt - 1))),
        };

        $delay = min($delay, $policy->maxDelayMs);

        if ($policy->useJitter) {
            $delay = $this->jitter->apply($delay, JitterType::Equal);
        }

        return max(0, $delay);
    }

    private function sleep(int $milliseconds): void
    {
        if ($milliseconds > 0) {
            usleep($milliseconds * 1000);
        }
    }
}
```

## Retry Policy Configuration

```php
<?php

// HTTP API - Quick retries with exponential backoff
$httpPolicy = new RetryPolicy(
    maxAttempts: 3,
    baseDelayMs: 100,
    maxDelayMs: 5000,
    strategy: BackoffStrategy::Exponential,
    useJitter: true,
    retryableExceptions: [
        ConnectionException::class,
        TimeoutException::class,
        ServiceUnavailableException::class,
    ],
    nonRetryableExceptions: [
        ClientException::class,
        AuthenticationException::class,
    ]
);

// Database - Fewer retries, quick recovery
$dbPolicy = new RetryPolicy(
    maxAttempts: 3,
    baseDelayMs: 50,
    maxDelayMs: 1000,
    strategy: BackoffStrategy::Exponential,
    retryableExceptions: [
        DeadlockException::class,
        ConnectionLostException::class,
    ]
);

// Message Queue - Many retries, longer delays
$mqPolicy = new RetryPolicy(
    maxAttempts: 10,
    baseDelayMs: 1000,
    maxDelayMs: 60000,
    strategy: BackoffStrategy::Exponential,
    useJitter: true
);
```

## Idempotency Considerations

```php
<?php

// SAFE to retry - Idempotent operations
$safeOperations = [
    'GET requests',
    'Read queries',
    'Idempotent writes (with idempotency key)',
    'Delete by ID (if already deleted = success)',
];

// UNSAFE to retry - Non-idempotent operations
$unsafeOperations = [
    'POST without idempotency key',
    'Increment operations',
    'Email sending (without deduplication)',
    'Payment processing (without idempotency)',
];

// Making operations idempotent
final readonly class IdempotentOperation
{
    public function __construct(
        private readonly string $idempotencyKey,
        private readonly IdempotencyStore $store
    ) {}

    public function execute(callable $operation): mixed
    {
        $existing = $this->store->find($this->idempotencyKey);
        if ($existing !== null) {
            return $existing->result;
        }

        $result = $operation();

        $this->store->save($this->idempotencyKey, $result);

        return $result;
    }
}
```

## Integration with Circuit Breaker

```php
<?php

final readonly class ResilientExecutor
{
    public function __construct(
        private CircuitBreaker $circuitBreaker,
        private RetryExecutor $retryExecutor
    ) {}

    public function execute(
        callable $operation,
        ?callable $fallback = null
    ): mixed {
        return $this->circuitBreaker->execute(
            operation: fn() => $this->retryExecutor->execute(
                $operation,
                RetryPolicy::default()
            ),
            fallback: $fallback
        );
    }
}
```

## Anti-patterns

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Retry non-idempotent | Duplicate side effects | Use idempotency keys |
| No max attempts | Infinite retries | Always set maxAttempts |
| No backoff | Hammering failed service | Use exponential backoff |
| No jitter | Thundering herd | Add jitter |
| Retry all exceptions | Retrying unrecoverable | Filter retryable exceptions |
| Inside transaction | Long locks, timeouts | Retry outside transaction |
