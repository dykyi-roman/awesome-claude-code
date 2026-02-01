# Circuit Breaker Pattern Examples

## HTTP Client with Circuit Breaker

**File:** `src/Infrastructure/Http/ResilientHttpClient.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Resilience\CircuitBreaker\CircuitBreakerRegistry;

final readonly class ResilientHttpClient
{
    public function __construct(
        private HttpClientInterface $client,
        private CircuitBreakerRegistry $circuitBreakers
    ) {}

    public function get(string $serviceName, string $url): Response
    {
        $breaker = $this->circuitBreakers->get($serviceName);

        return $breaker->execute(
            operation: fn() => $this->client->get($url),
            fallback: fn() => Response::empty()
        );
    }
}
```

---

## Payment Gateway with Circuit Breaker

**File:** `src/Infrastructure/Payment/PaymentGatewayAdapter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Payment;

use Infrastructure\Resilience\CircuitBreaker\CircuitBreaker;
use Infrastructure\Resilience\CircuitBreaker\CircuitBreakerException;

final readonly class PaymentGatewayAdapter
{
    public function __construct(
        private PaymentApiClient $client,
        private CircuitBreaker $circuitBreaker
    ) {}

    public function charge(PaymentRequest $request): PaymentResult
    {
        try {
            return $this->circuitBreaker->execute(
                operation: fn() => $this->client->charge($request),
                fallback: fn() => PaymentResult::deferred($request->id)
            );
        } catch (CircuitBreakerException $e) {
            return PaymentResult::serviceUnavailable($request->id);
        }
    }
}
```

---

## Unit Tests

### CircuitStateTest

**File:** `tests/Unit/Infrastructure/Resilience/CircuitBreaker/CircuitStateTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\CircuitBreaker;

use Infrastructure\Resilience\CircuitBreaker\CircuitState;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CircuitState::class)]
final class CircuitStateTest extends TestCase
{
    public function testClosedAllowsRequests(): void
    {
        self::assertTrue(CircuitState::Closed->allowsRequest());
    }

    public function testOpenBlocksRequests(): void
    {
        self::assertFalse(CircuitState::Open->allowsRequest());
    }

    public function testHalfOpenAllowsRequests(): void
    {
        self::assertTrue(CircuitState::HalfOpen->allowsRequest());
    }

    public function testClosedCanTransitionToOpen(): void
    {
        self::assertTrue(CircuitState::Closed->canTransitionTo(CircuitState::Open));
        self::assertFalse(CircuitState::Closed->canTransitionTo(CircuitState::HalfOpen));
    }

    public function testOpenCanTransitionToHalfOpen(): void
    {
        self::assertTrue(CircuitState::Open->canTransitionTo(CircuitState::HalfOpen));
        self::assertFalse(CircuitState::Open->canTransitionTo(CircuitState::Closed));
    }

    public function testHalfOpenCanTransitionToClosedOrOpen(): void
    {
        self::assertTrue(CircuitState::HalfOpen->canTransitionTo(CircuitState::Closed));
        self::assertTrue(CircuitState::HalfOpen->canTransitionTo(CircuitState::Open));
    }
}
```

---

### CircuitBreakerTest

**File:** `tests/Unit/Infrastructure/Resilience/CircuitBreaker/CircuitBreakerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Resilience\CircuitBreaker;

use Infrastructure\Resilience\CircuitBreaker\CircuitBreaker;
use Infrastructure\Resilience\CircuitBreaker\CircuitBreakerConfig;
use Infrastructure\Resilience\CircuitBreaker\CircuitBreakerException;
use Infrastructure\Resilience\CircuitBreaker\CircuitState;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Clock\ClockInterface;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(CircuitBreaker::class)]
final class CircuitBreakerTest extends TestCase
{
    private ClockInterface $clock;

    protected function setUp(): void
    {
        $this->clock = new class implements ClockInterface {
            public \DateTimeImmutable $now;
            public function __construct()
            {
                $this->now = new \DateTimeImmutable();
            }
            public function now(): \DateTimeImmutable
            {
                return $this->now;
            }
        };
    }

    public function testStartsInClosedState(): void
    {
        $breaker = $this->createBreaker();

        self::assertSame(CircuitState::Closed, $breaker->getState());
    }

    public function testExecutesOperationWhenClosed(): void
    {
        $breaker = $this->createBreaker();

        $result = $breaker->execute(fn() => 'success');

        self::assertSame('success', $result);
    }

    public function testOpensAfterFailureThreshold(): void
    {
        $config = new CircuitBreakerConfig(failureThreshold: 3);
        $breaker = $this->createBreaker($config);

        for ($i = 0; $i < 3; $i++) {
            try {
                $breaker->execute(fn() => throw new \RuntimeException('fail'));
            } catch (\RuntimeException) {}
        }

        self::assertSame(CircuitState::Open, $breaker->getState());
    }

    public function testThrowsWhenOpenWithoutFallback(): void
    {
        $breaker = $this->createBreaker();
        $breaker->forceOpen();

        $this->expectException(CircuitBreakerException::class);

        $breaker->execute(fn() => 'should not execute');
    }

    public function testExecutesFallbackWhenOpen(): void
    {
        $breaker = $this->createBreaker();
        $breaker->forceOpen();

        $result = $breaker->execute(
            fn() => 'should not execute',
            fn() => 'fallback'
        );

        self::assertSame('fallback', $result);
    }

    public function testTransitionsToHalfOpenAfterTimeout(): void
    {
        $config = new CircuitBreakerConfig(openTimeoutSeconds: 30);
        $breaker = $this->createBreaker($config);
        $breaker->forceOpen();

        $this->clock->now = $this->clock->now->modify('+31 seconds');

        $breaker->execute(fn() => 'test');

        self::assertSame(CircuitState::HalfOpen, $breaker->getState());
    }

    public function testClosesAfterSuccessThresholdInHalfOpen(): void
    {
        $config = new CircuitBreakerConfig(successThreshold: 2, openTimeoutSeconds: 1);
        $breaker = $this->createBreaker($config);
        $breaker->forceOpen();

        $this->clock->now = $this->clock->now->modify('+2 seconds');

        $breaker->execute(fn() => 'success');
        $breaker->execute(fn() => 'success');

        self::assertSame(CircuitState::Closed, $breaker->getState());
    }

    public function testReopensOnFailureInHalfOpen(): void
    {
        $config = new CircuitBreakerConfig(openTimeoutSeconds: 1);
        $breaker = $this->createBreaker($config);
        $breaker->forceOpen();

        $this->clock->now = $this->clock->now->modify('+2 seconds');
        $breaker->canExecute();

        try {
            $breaker->execute(fn() => throw new \RuntimeException('fail'));
        } catch (\RuntimeException) {}

        self::assertSame(CircuitState::Open, $breaker->getState());
    }

    private function createBreaker(?CircuitBreakerConfig $config = null): CircuitBreaker
    {
        return new CircuitBreaker(
            name: 'test-service',
            config: $config ?? new CircuitBreakerConfig(),
            clock: $this->clock,
            logger: new NullLogger()
        );
    }
}
```
