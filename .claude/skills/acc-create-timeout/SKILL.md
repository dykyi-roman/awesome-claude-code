---
name: acc-create-timeout
description: Generates Timeout pattern components for PHP 8.4. Creates execution time limit infrastructure with configurable timeouts, fallback support, stream timeouts, and unit tests.
---

# Timeout Pattern Generator

Creates Timeout pattern infrastructure for execution time limits with fallback support.

## When to Use

| Scenario | Example |
|----------|---------|
| External API calls | HTTP requests to third-party services |
| Database queries | Long-running or unoptimized queries |
| Queue consumers | Message processing time limits |
| File operations | Large file uploads/downloads |
| Distributed calls | gRPC, SOAP, or REST inter-service calls |
| Batch processing | Individual item timeout within batch |

## Component Characteristics

### TimeoutConfig
- Immutable value object
- Duration in seconds (float for sub-second precision)
- Optional fallback callable
- Optional shouldRetry flag
- Named presets (fast, standard, slow)

### TimeoutInterface
- Domain layer contract
- execute(callable operation, TimeoutConfig config): mixed
- Single responsibility: enforce time limit

### TimeoutExecutor
- pcntl_alarm + async signal based for CLI
- Catches SIGALRM to throw TimeoutException
- Restores previous signal handler after execution
- Thread-safe via execution context

### StreamTimeoutExecutor
- stream_set_timeout for I/O operations
- Works in both CLI and FPM
- Socket and stream resource support

### TimeoutException
- Extends RuntimeException
- Contains elapsed time and operation context
- Machine-readable properties for monitoring

### TimeoutMiddleware
- PSR-15 compatible for HTTP clients
- Adds timeout to outgoing requests
- Configurable per-route timeouts

---

## Generation Process

### Step 1: Analyze Request

Determine:
- Target use case (API calls, DB queries, queue consumers)
- Timeout strategy (signal-based, stream-based, or both)
- Fallback behavior (exception, default value, cached result)

### Step 2: Generate Core Components

1. **Domain Layer** (`src/Domain/Shared/Timeout/`)
   - `TimeoutConfig.php` — Configuration value object
   - `TimeoutInterface.php` — Execution contract
   - `TimeoutException.php` — Timeout exceeded exception

2. **Infrastructure Layer** (`src/Infrastructure/Resilience/Timeout/`)
   - `SignalTimeoutExecutor.php` — pcntl_alarm based implementation
   - `StreamTimeoutExecutor.php` — stream_set_timeout based
   - `NullTimeoutExecutor.php` — No-op for testing
   - `TimeoutExecutorFactory.php` — Environment-aware factory

3. **Presentation Layer** (`src/Presentation/Middleware/`)
   - `TimeoutMiddleware.php` — PSR-15 HTTP middleware

4. **Tests**
   - `TimeoutConfigTest.php`
   - `SignalTimeoutExecutorTest.php`
   - `TimeoutExceptionTest.php`

---

## File Placement

| Layer | Path |
|-------|------|
| Domain Types | `src/Domain/Shared/Timeout/` |
| Infrastructure | `src/Infrastructure/Resilience/Timeout/` |
| Middleware | `src/Presentation/Middleware/` |
| Unit Tests | `tests/Unit/{Layer}/{Path}/` |

---

## Key Principles

### Signal-Based Timeout (CLI)
1. Register SIGALRM handler
2. Set pcntl_alarm with timeout duration
3. Execute operation
4. Cancel alarm on completion
5. Restore previous handler
6. If alarm fires → throw TimeoutException

### Stream-Based Timeout (FPM/CLI)
1. Set stream_set_timeout on resource
2. Check stream_get_meta_data for timed_out flag
3. Works for network I/O operations

### Fallback Strategy
1. On timeout, check if fallback provided
2. Execute fallback within separate timeout (prevent cascading)
3. If no fallback, throw TimeoutException
4. Log timeout event with context

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Config VO | `TimeoutConfig` | `TimeoutConfig` |
| Interface | `TimeoutInterface` | `TimeoutInterface` |
| Signal Impl | `SignalTimeoutExecutor` | `SignalTimeoutExecutor` |
| Stream Impl | `StreamTimeoutExecutor` | `StreamTimeoutExecutor` |
| Null Impl | `NullTimeoutExecutor` | `NullTimeoutExecutor` |
| Exception | `TimeoutException` | `TimeoutException` |
| Factory | `TimeoutExecutorFactory` | `TimeoutExecutorFactory` |
| Middleware | `TimeoutMiddleware` | `TimeoutMiddleware` |
| Test | `{ClassName}Test` | `SignalTimeoutExecutorTest` |

---

## Quick Template Reference

### TimeoutConfig

```php
final readonly class TimeoutConfig
{
    public function __construct(
        public float $durationSeconds,
        public ?callable $fallback = null,
        public bool $shouldRetry = false,
        public string $operationName = 'unknown',
    ) {}

    public static function fast(): self; // 3 seconds
    public static function standard(): self; // 10 seconds
    public static function slow(): self; // 30 seconds
    public static function of(float $seconds): self;
}
```

### TimeoutInterface

```php
interface TimeoutInterface
{
    /**
     * @template T
     * @param callable(): T $operation
     * @return T
     * @throws TimeoutException
     */
    public function execute(callable $operation, TimeoutConfig $config): mixed;
}
```

### TimeoutException

```php
final class TimeoutException extends \RuntimeException
{
    public function __construct(
        public readonly float $elapsedSeconds,
        public readonly float $timeoutSeconds,
        public readonly string $operationName,
        ?\Throwable $previous = null,
    ) {
        parent::__construct(
            sprintf('Operation "%s" timed out after %.2fs (limit: %.2fs)', $operationName, $elapsedSeconds, $timeoutSeconds),
            0,
            $previous,
        );
    }
}
```

---

## Usage Example

```php
$timeout = $timeoutFactory->create();

try {
    $result = $timeout->execute(
        operation: fn() => $httpClient->request('GET', $url),
        config: TimeoutConfig::of(5.0),
    );
} catch (TimeoutException $e) {
    $logger->warning('API call timed out', [
        'operation' => $e->operationName,
        'elapsed' => $e->elapsedSeconds,
        'timeout' => $e->timeoutSeconds,
    ]);
    return $cachedResult;
}
```

---

## Composition with Circuit Breaker

```php
$result = $circuitBreaker->execute(
    operation: fn() => $timeout->execute(
        operation: fn() => $api->call($request),
        config: TimeoutConfig::of(5.0),
    ),
    fallback: fn() => $cache->get($cacheKey),
);
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No timeout | Indefinite blocking | Always set explicit timeout |
| Too aggressive | Fail on normal slow responses | Tune per-operation |
| Global timeout | One size doesn't fit all | Per-operation config |
| No fallback | Hard failure on timeout | Provide degraded response |
| Ignoring context | Can't debug timeouts | Include operation name |
| Nested timeouts | Outer timeout kills inner | Coordinate timeout budgets |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — API call, DB query examples and tests
