# Advanced Resilience Patterns Reference

## Backpressure Mechanisms

### What Is Backpressure

When a system component receives work faster than it can process, backpressure propagates the overload signal upstream so producers slow down.

```
Producer ──fast──▶ Buffer ──slow──▶ Consumer
                     │
              Buffer full? → Signal producer to slow down
```

### Backpressure Strategies

| Strategy | How It Works | PHP Example |
|----------|-------------|-------------|
| Drop | Discard excess requests | Rate limiter returning 429 |
| Buffer | Queue requests up to a limit | RabbitMQ with max-length |
| Throttle | Slow down the producer | Sleep between batch items |
| Reject | Refuse new work, signal overload | HTTP 503 Service Unavailable |
| Scale | Add more consumers | Auto-scaling worker pool |

### PHP Backpressure Implementation

```php
<?php

declare(strict_types=1);

namespace Resilience;

final class BackpressureQueue
{
    private int $pending = 0;

    public function __construct(
        private readonly int $maxPending,
        private readonly int $highWaterMark,
        private readonly int $lowWaterMark,
    ) {}

    public function canAccept(): bool
    {
        return $this->pending < $this->maxPending;
    }

    public function isPressured(): bool
    {
        return $this->pending >= $this->highWaterMark;
    }

    public function submit(callable $work): mixed
    {
        if (!$this->canAccept()) {
            throw new BackpressureException(
                sprintf('Queue full: %d/%d pending', $this->pending, $this->maxPending)
            );
        }

        $this->pending++;
        try {
            return $work();
        } finally {
            $this->pending--;
        }
    }
}
```

## Graceful Degradation

### Degradation Levels

```
Level 0: Full Functionality     ← Normal operation
Level 1: Non-Critical Disabled  ← Recommendations, analytics off
Level 2: Read-Only Mode         ← Writes disabled, reads from cache
Level 3: Static Fallback        ← Serve cached/static content only
Level 4: Maintenance Page       ← System unavailable
```

### PHP Degradation Manager

```php
<?php

declare(strict_types=1);

namespace Resilience;

enum DegradationLevel: int
{
    case Full = 0;
    case NonCriticalDisabled = 1;
    case ReadOnly = 2;
    case StaticFallback = 3;
    case Maintenance = 4;
}

final class GracefulDegradationManager
{
    private DegradationLevel $level = DegradationLevel::Full;

    public function __construct(
        private readonly \Redis $redis,
        private readonly string $key = 'system:degradation_level',
    ) {}

    public function currentLevel(): DegradationLevel
    {
        $stored = $this->redis->get($this->key);
        if ($stored !== false) {
            $this->level = DegradationLevel::from((int) $stored);
        }
        return $this->level;
    }

    public function isFeatureAvailable(string $feature): bool
    {
        $level = $this->currentLevel();

        return match ($feature) {
            'recommendations', 'analytics' => $level === DegradationLevel::Full,
            'search', 'notifications' => $level->value <= DegradationLevel::NonCriticalDisabled->value,
            'read' => $level->value <= DegradationLevel::ReadOnly->value,
            'static' => $level->value <= DegradationLevel::StaticFallback->value,
            default => $level === DegradationLevel::Full,
        };
    }

    public function setLevel(DegradationLevel $level): void
    {
        $this->level = $level;
        $this->redis->set($this->key, (string) $level->value);
    }
}
```

## Adaptive Retry (Exponential Backoff + Jitter)

### Full Jitter vs Decorrelated Jitter

| Algorithm | Formula | Spread | Best For |
|-----------|---------|--------|----------|
| No Jitter | `base * 2^attempt` | None (thundering herd) | Never use alone |
| Full Jitter | `random(0, base * 2^attempt)` | Maximum | High concurrency |
| Equal Jitter | `base * 2^attempt / 2 + random(0, base * 2^attempt / 2)` | Medium | Balanced |
| Decorrelated | `random(base, prev_delay * 3)` | Adaptive | Sequential retries |

### Adaptive Retry with Circuit Integration

```php
<?php

declare(strict_types=1);

namespace Resilience;

final readonly class AdaptiveRetry
{
    public function __construct(
        private int $baseDelayMs = 100,
        private int $maxDelayMs = 30_000,
        private int $maxAttempts = 5,
        private float $jitterFactor = 0.5,
    ) {}

    public function execute(callable $operation, ?callable $isRetriable = null): mixed
    {
        $lastException = null;

        for ($attempt = 1; $attempt <= $this->maxAttempts; $attempt++) {
            try {
                return $operation();
            } catch (\Throwable $e) {
                $lastException = $e;

                if ($isRetriable !== null && !$isRetriable($e)) {
                    throw $e;
                }

                if ($attempt < $this->maxAttempts) {
                    $delay = $this->calculateDelay($attempt);
                    usleep($delay * 1000);
                }
            }
        }

        throw $lastException;
    }

    private function calculateDelay(int $attempt): int
    {
        $exponential = (int) min(
            $this->maxDelayMs,
            $this->baseDelayMs * (2 ** ($attempt - 1))
        );

        $jitter = (int) ($exponential * $this->jitterFactor);
        return $exponential - $jitter + random_int(0, 2 * $jitter);
    }
}
```

## Chaos Engineering Principles

### Core Practices

| Practice | Description | PHP Tool |
|----------|-------------|----------|
| Steady state hypothesis | Define normal metrics | Prometheus assertions |
| Vary real-world events | Inject failures | Custom middleware |
| Run in production | Test real behavior | Canary deployments |
| Minimize blast radius | Limit failure scope | Feature flags per-user |
| Automate experiments | Continuous chaos | CI/CD integration |

### PHP Fault Injection Middleware

```php
<?php

declare(strict_types=1);

namespace Chaos;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class ChaosMiddleware implements MiddlewareInterface
{
    public function __construct(
        private ChaosConfig $config,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        if (!$this->config->isEnabled()) {
            return $handler->handle($request);
        }

        if ($this->shouldInjectLatency()) {
            usleep($this->config->latencyMs() * 1000);
        }

        if ($this->shouldInjectError()) {
            throw new \RuntimeException('Chaos: injected failure');
        }

        return $handler->handle($request);
    }

    private function shouldInjectLatency(): bool
    {
        return random_int(1, 100) <= $this->config->latencyPercentage();
    }

    private function shouldInjectError(): bool
    {
        return random_int(1, 100) <= $this->config->errorPercentage();
    }
}
```

## Health-Based Routing

### Health Check Types

| Check | Endpoint | Purpose |
|-------|----------|---------|
| Liveness | `/health/live` | Process is running (restart if fails) |
| Readiness | `/health/ready` | Can accept traffic (remove from LB if fails) |
| Startup | `/health/startup` | Has initialized (don't check liveness until ready) |

### Composite Health Checker

```php
<?php

declare(strict_types=1);

namespace Health;

final readonly class CompositeHealthChecker
{
    /** @param array<string, HealthCheckInterface> $checks */
    public function __construct(
        private array $checks,
    ) {}

    public function isLive(): HealthResult
    {
        return new HealthResult(status: 'UP', checks: []);
    }

    public function isReady(): HealthResult
    {
        $results = [];
        $healthy = true;

        foreach ($this->checks as $name => $check) {
            try {
                $check->check();
                $results[$name] = ['status' => 'UP'];
            } catch (\Throwable $e) {
                $results[$name] = ['status' => 'DOWN', 'error' => $e->getMessage()];
                $healthy = false;
            }
        }

        return new HealthResult(
            status: $healthy ? 'UP' : 'DOWN',
            checks: $results,
        );
    }
}
```

## Fallback Strategies

| Strategy | When to Use | Example |
|----------|-------------|---------|
| Cache fallback | External service down | Serve last cached response |
| Default value | Non-critical data | Empty recommendations list |
| Degraded response | Partial data available | Show order without reviews |
| Queue for later | Write operations | Queue order for processing |
| Static content | Full outage | Pre-generated static page |
