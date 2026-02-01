# Retry Pattern Examples

## HTTP Client with Retry

**File:** `src/Infrastructure/Http/ResilientHttpClient.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Resilience\Retry\RetryExecutor;
use Infrastructure\Resilience\Retry\RetryPolicy;

final readonly class ResilientHttpClient
{
    public function __construct(
        private HttpClientInterface $client,
        private RetryExecutor $retryExecutor
    ) {}

    public function get(string $url): Response
    {
        $policy = new RetryPolicy(
            maxAttempts: 3,
            baseDelayMs: 200,
            retryableExceptions: [
                ConnectionException::class,
                TimeoutException::class,
            ],
            nonRetryableExceptions: [
                ClientException::class,
            ]
        );

        return $this->retryExecutor->execute(
            operation: fn() => $this->client->get($url),
            policy: $policy
        );
    }
}
```

---

## Database Operations with Retry

**File:** `src/Infrastructure/Persistence/ResilientRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Infrastructure\Resilience\Retry\RetryExecutor;
use Infrastructure\Resilience\Retry\RetryPolicy;
use Infrastructure\Resilience\Retry\RetryContext;

final readonly class ResilientRepository
{
    public function __construct(
        private Connection $connection,
        private RetryExecutor $retryExecutor
    ) {}

    public function executeWithRetry(callable $operation): mixed
    {
        $policy = RetryPolicy::exponential(
            maxAttempts: 3,
            baseDelayMs: 50
        );

        return $this->retryExecutor->execute(
            operation: fn(RetryContext $ctx) => $operation(),
            policy: $policy,
            onRetry: function (\Throwable $e, RetryContext $ctx): void {
                if ($e instanceof DeadlockException) {
                    $this->connection->reconnect();
                }
            }
        );
    }
}
```

---

## Message Consumer with Retry

**File:** `src/Application/Messaging/MessageHandler.php`

```php
<?php

declare(strict_types=1);

namespace Application\Messaging;

use Infrastructure\Resilience\Retry\RetryExecutor;
use Infrastructure\Resilience\Retry\RetryPolicy;
use Infrastructure\Resilience\Retry\RetryException;

final readonly class MessageHandler
{
    public function __construct(
        private MessageProcessorInterface $processor,
        private RetryExecutor $retryExecutor,
        private DeadLetterQueue $deadLetter
    ) {}

    public function handle(Message $message): void
    {
        $policy = new RetryPolicy(
            maxAttempts: 5,
            baseDelayMs: 1000,
            maxDelayMs: 30000
        );

        try {
            $this->retryExecutor->execute(
                operation: fn() => $this->processor->process($message),
                policy: $policy
            );
        } catch (RetryException $e) {
            $this->deadLetter->send($message, $e);
        }
    }
}
```

---

## Unit Tests

### RetryPolicyTest

**File:** `tests/Unit/Infrastructure/Resilience/Retry/RetryPolicyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\Retry;

use Infrastructure\Resilience\Retry\BackoffStrategy;
use Infrastructure\Resilience\Retry\RetryPolicy;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(RetryPolicy::class)]
final class RetryPolicyTest extends TestCase
{
    public function testShouldRetryWhenBelowMaxAttempts(): void
    {
        $policy = new RetryPolicy(maxAttempts: 3);

        self::assertTrue($policy->shouldRetry(new \RuntimeException(), 1));
        self::assertTrue($policy->shouldRetry(new \RuntimeException(), 2));
        self::assertFalse($policy->shouldRetry(new \RuntimeException(), 3));
    }

    public function testShouldNotRetryNonRetryableException(): void
    {
        $policy = new RetryPolicy(
            nonRetryableExceptions: [\InvalidArgumentException::class]
        );

        self::assertFalse($policy->shouldRetry(new \InvalidArgumentException(), 1));
        self::assertTrue($policy->shouldRetry(new \RuntimeException(), 1));
    }

    public function testExponentialBackoffCalculation(): void
    {
        $policy = new RetryPolicy(
            baseDelayMs: 100,
            multiplier: 2.0,
            useJitter: false,
            strategy: BackoffStrategy::Exponential
        );

        self::assertSame(100, $policy->calculateDelay(1));
        self::assertSame(200, $policy->calculateDelay(2));
        self::assertSame(400, $policy->calculateDelay(3));
    }

    public function testLinearBackoffCalculation(): void
    {
        $policy = new RetryPolicy(
            baseDelayMs: 100,
            useJitter: false,
            strategy: BackoffStrategy::Linear
        );

        self::assertSame(100, $policy->calculateDelay(1));
        self::assertSame(200, $policy->calculateDelay(2));
        self::assertSame(300, $policy->calculateDelay(3));
    }

    public function testMaxDelayIsCapped(): void
    {
        $policy = new RetryPolicy(
            baseDelayMs: 1000,
            maxDelayMs: 5000,
            multiplier: 10.0,
            useJitter: false,
            strategy: BackoffStrategy::Exponential
        );

        self::assertSame(5000, $policy->calculateDelay(5));
    }
}
```

---

### RetryExecutorTest

**File:** `tests/Unit/Infrastructure/Resilience/Retry/RetryExecutorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\Retry;

use Infrastructure\Resilience\Retry\RetryContext;
use Infrastructure\Resilience\Retry\RetryException;
use Infrastructure\Resilience\Retry\RetryExecutor;
use Infrastructure\Resilience\Retry\RetryPolicy;
use Infrastructure\Resilience\Retry\SleepInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(RetryExecutor::class)]
final class RetryExecutorTest extends TestCase
{
    private RetryExecutor $executor;

    protected function setUp(): void
    {
        $noOpSleep = new class implements SleepInterface {
            public function sleep(int $milliseconds): void {}
        };

        $this->executor = new RetryExecutor(
            logger: new NullLogger(),
            sleep: $noOpSleep
        );
    }

    public function testExecutesSuccessfullyOnFirstAttempt(): void
    {
        $result = $this->executor->execute(
            operation: fn() => 'success',
            policy: RetryPolicy::default()
        );

        self::assertSame('success', $result);
    }

    public function testRetriesOnFailure(): void
    {
        $attempts = 0;

        $result = $this->executor->execute(
            operation: function () use (&$attempts) {
                $attempts++;
                if ($attempts < 3) {
                    throw new \RuntimeException('fail');
                }
                return 'success';
            },
            policy: new RetryPolicy(maxAttempts: 5)
        );

        self::assertSame('success', $result);
        self::assertSame(3, $attempts);
    }

    public function testThrowsRetryExceptionAfterMaxAttempts(): void
    {
        $policy = new RetryPolicy(maxAttempts: 3);

        $this->expectException(RetryException::class);

        $this->executor->execute(
            operation: fn() => throw new \RuntimeException('always fails'),
            policy: $policy
        );
    }

    public function testCallsOnRetryCallback(): void
    {
        $retryCalls = [];

        try {
            $this->executor->execute(
                operation: fn() => throw new \RuntimeException('fail'),
                policy: new RetryPolicy(maxAttempts: 3),
                onRetry: function (\Throwable $e, RetryContext $ctx) use (&$retryCalls): void {
                    $retryCalls[] = $ctx->attempt;
                }
            );
        } catch (RetryException) {}

        self::assertSame([1, 2], $retryCalls);
    }
}
```
