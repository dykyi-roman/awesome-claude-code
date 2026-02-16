---
name: acc-check-cascading-failures
description: Detects cascading failure risks in PHP systems. Identifies shared resources, unbounded queues, missing backpressure, thread pool exhaustion, and failure propagation paths.
---

# Cascading Failure Detection

Analyze PHP code for patterns that can cause cascading failures across services and components.

## Detection Patterns

### 1. Shared Resource Without Isolation

```php
// CRITICAL: Single connection pool shared by all services
final class DatabasePool
{
    private static array $connections = [];

    public static function getConnection(): PDO
    {
        // All services compete for same pool
        // If one service hogs connections, all others starve
        return self::$connections[array_rand(self::$connections)];
    }
}

// CORRECT: Isolated pools per service (Bulkhead pattern)
final readonly class IsolatedDatabasePool
{
    public function __construct(
        private string $serviceName,
        private int $maxConnections,
    ) {}
}
```

### 2. Unbounded Queue Growth

```php
// CRITICAL: No size limit on in-memory queue
class EventQueue
{
    private array $events = []; // Grows without bound

    public function push(Event $event): void
    {
        $this->events[] = $event; // Memory exhaustion risk
    }
}

// CRITICAL: No consumer backpressure
while (true) {
    $message = $producer->produce($data);
    // No check if consumer is keeping up
    // Queue grows → memory fills → OOM → crash
}

// CORRECT: Bounded queue with backpressure
final class BoundedEventQueue
{
    private SplQueue $events;

    public function __construct(
        private readonly int $maxSize = 10000,
    ) {
        $this->events = new SplQueue();
    }

    public function push(Event $event): void
    {
        if ($this->events->count() >= $this->maxSize) {
            throw new QueueFullException('Backpressure: queue at capacity');
        }
        $this->events->enqueue($event);
    }
}
```

### 3. Synchronous Chain Without Circuit Breaker

```php
// CRITICAL: Cascading synchronous calls
class OrderService
{
    public function createOrder(OrderData $data): Order
    {
        $inventory = $this->inventoryService->reserve($data->items());    // If this hangs...
        $payment = $this->paymentService->charge($data->total());         // ...this waits...
        $shipping = $this->shippingService->schedule($data->address());   // ...everything stops
        $notification = $this->notificationService->send($data->email()); // ...cascade!
    }
}

// CORRECT: Each call protected with circuit breaker + timeout
class OrderService
{
    public function createOrder(OrderData $data): Order
    {
        $inventory = $this->circuitBreaker->call(
            fn () => $this->inventoryService->reserve($data->items()),
            fallback: fn () => $this->reserveLater($data->items()),
        );
    }
}
```

### 4. Retry Storm (Thundering Herd)

```php
// CRITICAL: All instances retry at same time
class ApiClient
{
    public function call(string $endpoint): Response
    {
        for ($i = 0; $i < 3; $i++) {
            try {
                return $this->http->get($endpoint);
            } catch (Exception $e) {
                sleep(1); // Fixed delay — all instances retry simultaneously!
            }
        }
        throw new ApiException('Failed after 3 retries');
    }
}

// CORRECT: Exponential backoff with jitter
$delay = min($baseDelay * (2 ** $attempt) + random_int(0, 1000), $maxDelay);
```

### 5. Missing Health Checks

```php
// CRITICAL: Serving traffic while dependencies are down
class ApiController
{
    public function handle(Request $request): Response
    {
        // No check if database/cache/external services are available
        // Returns 500 errors, load balancer keeps sending traffic
        return $this->service->process($request);
    }
}

// CORRECT: Health check endpoint
class HealthController
{
    public function check(): Response
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'queue' => $this->checkQueue(),
        ];

        $healthy = !in_array(false, $checks, true);
        return new Response(
            json_encode($checks),
            $healthy ? 200 : 503,
        );
    }
}
```

### 6. Resource Leak Under Failure

```php
// CRITICAL: Connection not released on exception
class MessageProcessor
{
    public function process(): void
    {
        $connection = $this->pool->acquire();
        $this->doWork($connection); // If this throws...
        $this->pool->release($connection); // ...connection is leaked!
    }
}

// CORRECT: Always release in finally
class MessageProcessor
{
    public function process(): void
    {
        $connection = $this->pool->acquire();
        try {
            $this->doWork($connection);
        } finally {
            $this->pool->release($connection);
        }
    }
}
```

## Grep Patterns

```bash
# Shared static resources
Grep: "private static.*\$.*=.*\[\]|protected static.*pool|static.*\$connections" --glob "**/*.php"

# Unbounded collections
Grep: "\$this->.*\[\].*=|\[\].*events|array_push" --glob "**/Infrastructure/**/*.php"

# Synchronous chains (multiple service calls in one method)
Grep: "\$this->.*Service->.*\n.*\$this->.*Service->" --glob "**/Application/**/*.php"

# Fixed retry delays (no jitter)
Grep: "sleep\([0-9]+\)|usleep\([0-9]+\)" --glob "**/*.php"

# Missing finally blocks
Grep: "->acquire\(\)|->lock\(" --glob "**/*.php"
Grep: "finally" --glob "**/*.php"

# Missing health checks
Grep: "class.*HealthCheck|function.*health|/health" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Shared pool without isolation | 🔴 Critical |
| Unbounded queue in memory | 🔴 Critical |
| Synchronous chain without breaker | 🔴 Critical |
| Retry storm (no jitter) | 🟠 Major |
| Missing health checks | 🟠 Major |
| Resource leak on failure | 🟠 Major |
| No backpressure mechanism | 🟡 Minor |

## Output Format

```markdown
### Cascading Failure Risk: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Failure Path:** ServiceA → ServiceB → ServiceC

**Issue:**
[Description of the cascading failure risk]

**Blast Radius:**
- Direct: [immediately affected components]
- Indirect: [downstream components that will fail]

**Code:**
```php
// Vulnerable pattern
```

**Fix:**
```php
// With isolation/circuit breaker/backpressure
```
```
