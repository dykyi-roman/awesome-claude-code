---
name: acc-create-health-check
description: Generates Health Check pattern for PHP 8.4. Creates application-level health endpoints with component checkers (Database, Redis, RabbitMQ), status aggregation, and RFC-compliant JSON response. Includes unit tests.
---

# Health Check Generator

Creates Health Check infrastructure for monitoring application and dependency health.

## When to Use

| Scenario | Example |
|----------|---------|
| Load balancer routing | Kubernetes liveness/readiness probes |
| Monitoring | Prometheus health scraping |
| Deployment readiness | Verify all dependencies before serving traffic |
| Dependency status | Check Database, Redis, RabbitMQ availability |

## Component Characteristics

### HealthCheckInterface
- `name(): string` — unique identifier for the check
- `check(): HealthCheckResult` — execute the health check

### HealthStatus Enum
- **Healthy**: All systems operational
- **Degraded**: Partially operational, non-critical issues
- **Unhealthy**: System is down or critical failure

### HealthCheckResult
- Immutable value object
- Properties: `name`, `status` (HealthStatus), `durationMs` (float), `details` (array)
- Static factory methods: `healthy()`, `unhealthy()`, `degraded()`

### HealthCheckRunner
- Accepts iterable of HealthCheckInterface implementations
- Runs all checks with configurable timeout
- Aggregates overall status (worst status wins)
- Catches exceptions as unhealthy results

---

## Generation Process

### Step 1: Generate Domain Components

**Path:** `src/Domain/Shared/Health/`

1. `HealthCheckInterface.php` — Interface for health checks
2. `HealthStatus.php` — Enum with Healthy/Degraded/Unhealthy states
3. `HealthCheckResult.php` — Immutable result value object

### Step 2: Generate Infrastructure Checkers

**Path:** `src/Infrastructure/Health/`

1. `DatabaseHealthCheck.php` — PDO connectivity check
2. `RedisHealthCheck.php` — Redis connectivity check
3. `RabbitMqHealthCheck.php` — RabbitMQ connectivity check
4. `HealthCheckRunner.php` — Runs all checks and aggregates status

### Step 3: Generate Presentation Endpoint

**Path:** `src/Presentation/Api/Action/`

1. `HealthCheckAction.php` — PSR-15 handler returning JSON response

### Step 4: Generate Tests

1. `HealthCheckResultTest.php` — Result construction and serialization
2. `HealthCheckRunnerTest.php` — Aggregation and error handling
3. `HealthCheckActionTest.php` — HTTP response codes and format

---

## File Placement

| Component | Path |
|-----------|------|
| Domain Interfaces & VOs | `src/Domain/Shared/Health/` |
| Infrastructure Checkers | `src/Infrastructure/Health/` |
| Presentation Action | `src/Presentation/Api/Action/` |
| Unit Tests (Domain) | `tests/Unit/Domain/Shared/Health/` |
| Unit Tests (Infra) | `tests/Unit/Infrastructure/Health/` |
| Unit Tests (Presentation) | `tests/Unit/Presentation/Api/Action/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `HealthCheckInterface` | `HealthCheckInterface` |
| Status Enum | `HealthStatus` | `HealthStatus` |
| Result VO | `HealthCheckResult` | `HealthCheckResult` |
| Checker | `{Service}HealthCheck` | `DatabaseHealthCheck` |
| Runner | `HealthCheckRunner` | `HealthCheckRunner` |
| Action | `HealthCheckAction` | `HealthCheckAction` |
| Test | `{ClassName}Test` | `HealthCheckResultTest` |

---

## Quick Template Reference

### HealthCheckInterface

```php
interface HealthCheckInterface
{
    public function name(): string;
    public function check(): HealthCheckResult;
}
```

### HealthStatus

```php
enum HealthStatus: string
{
    case Healthy = 'healthy';
    case Degraded = 'degraded';
    case Unhealthy = 'unhealthy';

    public function isOperational(): bool;
    public function merge(self $other): self;
}
```

### HealthCheckResult

```php
final readonly class HealthCheckResult
{
    public function __construct(
        public string $name,
        public HealthStatus $status,
        public float $durationMs,
        public array $details = []
    ) {}

    public static function healthy(string $name, float $durationMs): self;
    public static function unhealthy(string $name, float $durationMs, string $error): self;
    public static function degraded(string $name, float $durationMs, string $reason): self;
    public function toArray(): array;
}
```

---

## Usage Example

```php
// GET /health
$runner = new HealthCheckRunner($checkers, timeoutSeconds: 5);
$result = $runner->run();
// $result['status'] is HealthStatus, $result['checks'] is array<string, HealthCheckResult>
```

---

## Response Format (RFC Health Check JSON)

```json
{
    "status": "healthy",
    "checks": {
        "database": {
            "name": "database",
            "status": "healthy",
            "duration_ms": 1.23,
            "details": {}
        },
        "redis": {
            "name": "redis",
            "status": "healthy",
            "duration_ms": 0.45,
            "details": {}
        },
        "rabbitmq": {
            "name": "rabbitmq",
            "status": "degraded",
            "duration_ms": 15.7,
            "details": {
                "reason": "High latency detected"
            }
        }
    }
}
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Slow checks | Health endpoint times out | Set per-check timeouts |
| No timeouts | Single check blocks entire response | Use configurable timeout per runner |
| Exposing internals | Leaking credentials or internal IPs | Return only status, duration, generic details |
| Missing checks | Silent dependency failures | Register checkers for all critical dependencies |
| Synchronous only | Sequential checks increase latency | Consider parallel execution for many checks |
| No degraded state | Binary healthy/unhealthy is too rigid | Use three-state model with Degraded |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — HealthCheckInterface, HealthStatus, HealthCheckResult, checkers, runner, action templates
- `references/examples.md` — DI wiring, custom checker, and unit tests
