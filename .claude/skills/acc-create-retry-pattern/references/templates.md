# Retry Pattern Templates

## RetryPolicy

**File:** `src/Infrastructure/Resilience/Retry/RetryPolicy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

final readonly class RetryPolicy
{
    /**
     * @param array<class-string<\Throwable>> $retryableExceptions
     * @param array<class-string<\Throwable>> $nonRetryableExceptions
     */
    public function __construct(
        public int $maxAttempts = 3,
        public int $baseDelayMs = 100,
        public int $maxDelayMs = 10000,
        public float $multiplier = 2.0,
        public bool $useJitter = true,
        public BackoffStrategy $strategy = BackoffStrategy::Exponential,
        public array $retryableExceptions = [],
        public array $nonRetryableExceptions = []
    ) {
        if ($this->maxAttempts < 1) {
            throw new \InvalidArgumentException('Max attempts must be at least 1');
        }
        if ($this->baseDelayMs < 0) {
            throw new \InvalidArgumentException('Base delay must be non-negative');
        }
    }

    public static function default(): self
    {
        return new self();
    }

    public static function immediate(int $maxAttempts = 3): self
    {
        return new self(
            maxAttempts: $maxAttempts,
            baseDelayMs: 0,
            strategy: BackoffStrategy::Fixed
        );
    }

    public static function exponential(int $maxAttempts = 5, int $baseDelayMs = 100): self
    {
        return new self(
            maxAttempts: $maxAttempts,
            baseDelayMs: $baseDelayMs,
            strategy: BackoffStrategy::Exponential
        );
    }

    public static function linear(int $maxAttempts = 5, int $baseDelayMs = 500): self
    {
        return new self(
            maxAttempts: $maxAttempts,
            baseDelayMs: $baseDelayMs,
            strategy: BackoffStrategy::Linear,
            multiplier: 1.0
        );
    }

    public function shouldRetry(\Throwable $exception, int $attempt): bool
    {
        if ($attempt >= $this->maxAttempts) {
            return false;
        }

        foreach ($this->nonRetryableExceptions as $nonRetryable) {
            if ($exception instanceof $nonRetryable) {
                return false;
            }
        }

        if ($this->retryableExceptions === []) {
            return true;
        }

        foreach ($this->retryableExceptions as $retryable) {
            if ($exception instanceof $retryable) {
                return true;
            }
        }

        return false;
    }

    public function calculateDelay(int $attempt): int
    {
        $delay = match ($this->strategy) {
            BackoffStrategy::Fixed => $this->baseDelayMs,
            BackoffStrategy::Linear => $this->baseDelayMs * $attempt,
            BackoffStrategy::Exponential => (int) ($this->baseDelayMs * ($this->multiplier ** ($attempt - 1))),
        };

        $delay = min($delay, $this->maxDelayMs);

        if ($this->useJitter) {
            $jitter = random_int(0, (int) ($delay * 0.3));
            $delay = $delay + $jitter - (int) ($delay * 0.15);
        }

        return max(0, $delay);
    }
}
```

---

## BackoffStrategy Enum

**File:** `src/Infrastructure/Resilience/Retry/BackoffStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

enum BackoffStrategy: string
{
    case Fixed = 'fixed';
    case Linear = 'linear';
    case Exponential = 'exponential';
}
```

---

## RetryContext

**File:** `src/Infrastructure/Resilience/Retry/RetryContext.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

final readonly class RetryContext
{
    /**
     * @param array<\Throwable> $exceptions
     */
    public function __construct(
        public int $attempt,
        public int $maxAttempts,
        public int $delayMs,
        public array $exceptions = [],
        public ?\Throwable $lastException = null
    ) {}

    public function isFirstAttempt(): bool
    {
        return $this->attempt === 1;
    }

    public function isLastAttempt(): bool
    {
        return $this->attempt >= $this->maxAttempts;
    }

    public function getRemainingAttempts(): int
    {
        return max(0, $this->maxAttempts - $this->attempt);
    }
}
```

---

## RetryException

**File:** `src/Infrastructure/Resilience/Retry/RetryException.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

final class RetryException extends \RuntimeException
{
    /**
     * @param array<\Throwable> $attempts
     */
    public function __construct(
        public readonly int $attemptCount,
        public readonly array $attempts,
        ?\Throwable $lastException = null
    ) {
        parent::__construct(
            sprintf('Operation failed after %d attempts', $attemptCount),
            0,
            $lastException
        );
    }

    public function getLastAttemptException(): ?\Throwable
    {
        return $this->attempts[array_key_last($this->attempts)] ?? null;
    }
}
```

---

## RetryExecutor

**File:** `src/Infrastructure/Resilience/Retry/RetryExecutor.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

use Psr\Log\LoggerInterface;

final readonly class RetryExecutor
{
    public function __construct(
        private LoggerInterface $logger,
        private ?SleepInterface $sleep = null
    ) {}

    /**
     * @template T
     * @param callable(RetryContext): T $operation
     * @param callable(\Throwable, RetryContext): void|null $onRetry
     * @return T
     * @throws RetryException
     */
    public function execute(
        callable $operation,
        RetryPolicy $policy,
        ?callable $onRetry = null
    ): mixed {
        $attempt = 0;
        $exceptions = [];

        while (true) {
            $attempt++;

            $context = new RetryContext(
                attempt: $attempt,
                maxAttempts: $policy->maxAttempts,
                delayMs: $policy->calculateDelay($attempt),
                exceptions: $exceptions,
                lastException: $exceptions[array_key_last($exceptions)] ?? null
            );

            try {
                return $operation($context);
            } catch (\Throwable $e) {
                $exceptions[] = $e;

                if (!$policy->shouldRetry($e, $attempt)) {
                    throw new RetryException($attempt, $exceptions, $e);
                }

                $delay = $policy->calculateDelay($attempt);

                $this->logger->warning('Operation failed, retrying', [
                    'attempt' => $attempt,
                    'max_attempts' => $policy->maxAttempts,
                    'delay_ms' => $delay,
                    'exception' => $e->getMessage(),
                ]);

                if ($onRetry !== null) {
                    $onRetry($e, $context);
                }

                $this->sleep($delay);
            }
        }
    }

    private function sleep(int $milliseconds): void
    {
        if ($this->sleep !== null) {
            $this->sleep->sleep($milliseconds);
            return;
        }

        if ($milliseconds > 0) {
            usleep($milliseconds * 1000);
        }
    }
}
```

---

## SleepInterface (for testing)

**File:** `src/Infrastructure/Resilience/Retry/SleepInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

interface SleepInterface
{
    public function sleep(int $milliseconds): void;
}
```

---

## RetryableOperation Attribute

**File:** `src/Infrastructure/Resilience/Retry/RetryableOperation.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Resilience\Retry;

#[\Attribute(\Attribute::TARGET_METHOD)]
final readonly class RetryableOperation
{
    /**
     * @param array<class-string<\Throwable>> $retryOn
     */
    public function __construct(
        public int $maxAttempts = 3,
        public int $delayMs = 100,
        public BackoffStrategy $strategy = BackoffStrategy::Exponential,
        public array $retryOn = []
    ) {}

    public function toPolicy(): RetryPolicy
    {
        return new RetryPolicy(
            maxAttempts: $this->maxAttempts,
            baseDelayMs: $this->delayMs,
            strategy: $this->strategy,
            retryableExceptions: $this->retryOn
        );
    }
}
```
