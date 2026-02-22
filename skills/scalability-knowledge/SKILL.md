---
name: scalability-knowledge
description: Scalability knowledge base. Provides vertical vs horizontal scaling, stateless design, session management, connection pooling, capacity planning, and PHP-FPM tuning for scalability audits.
---

# Scalability Knowledge Base

Quick reference for scalability patterns, stateless design, PHP-FPM tuning, and capacity planning in PHP applications.

## Vertical vs Horizontal Scaling

| Aspect | Vertical (Scale Up) | Horizontal (Scale Out) |
|--------|---------------------|------------------------|
| Approach | Bigger server (CPU, RAM) | More servers |
| Cost curve | Exponential (diminishing returns) | Linear (commodity hardware) |
| Downtime | Often required for upgrade | Zero-downtime rolling deploys |
| Limit | Hardware ceiling | Theoretically unlimited |
| Complexity | Low (single server) | High (distributed system) |
| Data consistency | Simple (single node) | Requires distributed coordination |
| Failure blast radius | Entire application | Single instance |
| PHP suitability | Quick win, limited ceiling | Natural fit (shared-nothing) |

### When to Use Each

| Scenario | Strategy | Why |
|----------|----------|-----|
| Early stage, simple app | Vertical | Cheapest, simplest |
| Read-heavy workload | Horizontal + read replicas | Distribute read load |
| Write-heavy workload | Horizontal + sharding | Distribute write load |
| Unpredictable traffic | Horizontal + auto-scaling | Elastic capacity |
| Legacy monolith | Vertical first, then decompose | Buys time for refactoring |

## Stateless vs Stateful: PHP Shared-Nothing Architecture

PHP is **shared-nothing by design** — each request starts with a clean process, no shared memory between requests. This is a natural advantage for horizontal scaling.

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    SHARED-NOTHING ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Load Balancer                                                         │
│       │                                                                 │
│   ┌───┼───────────────────┬─────────────────────┐                      │
│   │   │                   │                     │                      │
│   ▼   ▼                   ▼                     ▼                      │
│ ┌──────────┐        ┌──────────┐          ┌──────────┐                 │
│ │ PHP-FPM  │        │ PHP-FPM  │          │ PHP-FPM  │                 │
│ │ Worker 1 │        │ Worker 2 │          │ Worker N │                 │
│ │          │        │          │          │          │                 │
│ │ No shared│        │ No shared│          │ No shared│                 │
│ │ state    │        │ state    │          │ state    │                 │
│ └────┬─────┘        └────┬─────┘          └────┬─────┘                 │
│      │                   │                     │                       │
│      └───────────────────┼─────────────────────┘                       │
│                          │                                              │
│                          ▼                                              │
│                 ┌─────────────────┐                                     │
│                 │  External State  │                                    │
│                 │  Redis / DB      │                                    │
│                 └─────────────────┘                                     │
│                                                                         │
│   Key Principle: ANY request can be served by ANY worker.               │
│   State lives in external stores (Redis, DB), NOT in process memory.   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Stateless Checklist

| Requirement | Stateless | Stateful (Problem) |
|-------------|-----------|-------------------|
| Session data | Redis / JWT | `$_SESSION` with file storage |
| File uploads | Object storage (S3) | Local filesystem |
| Cache | Redis / Memcached | APCu (per-process) |
| Configuration | Env vars / config service | Local config files that vary per server |
| Scheduled jobs | Centralized scheduler | Local cron per server |
| WebSocket state | Redis pub/sub | In-memory connections |

## Session Management

### File-Based Sessions (Problem)

```
Server A: session file → /tmp/sess_abc123
Server B: no session file → user logged out!

Sticky sessions (workaround) → couples user to server → defeats horizontal scaling
```

### Redis Sessions (Solution)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Session;

final readonly class RedisSessionConfig
{
    public function __construct(
        private string $redisHost,
        private int $redisPort = 6379,
        private string $redisPrefix = 'sess:',
        private int $ttlSeconds = 1800,
    ) {}

    public function configure(): void
    {
        ini_set('session.save_handler', 'redis');
        ini_set('session.save_path', sprintf(
            'tcp://%s:%d?prefix=%s&timeout=2',
            $this->redisHost,
            $this->redisPort,
            $this->redisPrefix,
        ));
        ini_set('session.gc_maxlifetime', (string) $this->ttlSeconds);
    }
}
```

### JWT Stateless Alternative

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Auth;

final readonly class JwtTokenFactory
{
    public function __construct(
        private string $secretKey,
        private string $algorithm = 'HS256',
        private int $ttlSeconds = 3600,
    ) {}

    /**
     * @param array<string, mixed> $claims
     */
    public function create(string $userId, array $claims = []): string
    {
        $header = base64_encode(json_encode([
            'alg' => $this->algorithm,
            'typ' => 'JWT',
        ], JSON_THROW_ON_ERROR));

        $payload = base64_encode(json_encode(array_merge($claims, [
            'sub' => $userId,
            'iat' => time(),
            'exp' => time() + $this->ttlSeconds,
        ]), JSON_THROW_ON_ERROR));

        $signature = base64_encode(hash_hmac(
            'sha256',
            sprintf('%s.%s', $header, $payload),
            $this->secretKey,
            true,
        ));

        return sprintf('%s.%s.%s', $header, $payload, $signature);
    }
}
```

## Connection Pooling

PHP creates a new database connection per request (shared-nothing). Without pooling, high-concurrency scenarios exhaust database connections.

### Why PHP Needs External Poolers

| Problem | Cause | Solution |
|---------|-------|----------|
| Connection exhaustion | Each PHP-FPM worker opens own connection | pgbouncer / ProxySQL |
| Connection overhead | TCP handshake + auth per request | Persistent connections |
| Idle connections | Workers hold connections while waiting for I/O | External pooler reclaims idle |
| Max connections limit | PostgreSQL default 100, MySQL 151 | Pooler multiplexes |

### Connection Pool Wrapper

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final readonly class ConnectionPoolConfig
{
    public function __construct(
        private string $host,
        private int $port,
        private string $database,
        private string $user,
        private string $password,
        private bool $persistent = true,
        private int $connectTimeoutSeconds = 5,
        private int $statementTimeoutMs = 30000,
    ) {}

    public function createPdo(): \PDO
    {
        $dsn = sprintf(
            'pgsql:host=%s;port=%d;dbname=%s',
            $this->host,
            $this->port,
            $this->database,
        );

        $options = [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            \PDO::ATTR_EMULATE_PREPARES => false,
            \PDO::ATTR_PERSISTENT => $this->persistent,
            \PDO::ATTR_TIMEOUT => $this->connectTimeoutSeconds,
        ];

        $pdo = new \PDO($dsn, $this->user, $this->password, $options);
        $pdo->exec(sprintf(
            'SET statement_timeout = %d',
            $this->statementTimeoutMs,
        ));

        return $pdo;
    }
}
```

### External Pooler Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                   CONNECTION POOLING                              │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   PHP-FPM Workers (200+)                                         │
│   ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐                 │
│   │  W1  │ │  W2  │ │  W3  │ │ ...  │ │ W200 │                 │
│   └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘                 │
│      │        │        │        │        │                       │
│      └────────┴────────┴────┬───┴────────┘                       │
│                             │                                    │
│                             ▼                                    │
│                    ┌─────────────────┐                           │
│                    │   pgbouncer /   │  Pool: 20-50 connections  │
│                    │   ProxySQL      │  Mode: transaction        │
│                    └────────┬────────┘                           │
│                             │                                    │
│                             ▼                                    │
│                    ┌─────────────────┐                           │
│                    │   PostgreSQL /  │  max_connections: 100     │
│                    │   MySQL         │                           │
│                    └─────────────────┘                           │
│                                                                   │
│   200 PHP workers share 20-50 DB connections via pooler          │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Capacity Planning

### Amdahl's Law

```
Speedup = 1 / ((1 - P) + P/N)

P = parallelizable fraction of workload
N = number of processors/instances

Example: If 90% of work is parallelizable (P=0.9), 10 servers:
  Speedup = 1 / ((1 - 0.9) + 0.9/10) = 1 / (0.1 + 0.09) = 5.26x

Lesson: Serial bottlenecks (DB writes, locks) limit scaling.
```

### Little's Law

```
L = λ × W

L = average number of concurrent requests
λ = arrival rate (requests/second)
W = average response time (seconds)

Example: 500 req/s, 200ms avg response time:
  L = 500 × 0.2 = 100 concurrent requests needed

Lesson: To handle 500 req/s at 200ms, you need capacity for 100 concurrent requests.
```

### Throughput Formula

```
Throughput = Workers / Avg_Response_Time

Example: 50 PHP-FPM workers, 100ms avg:
  Throughput = 50 / 0.1 = 500 req/s

To increase throughput:
  1. Add more workers (horizontal scaling)
  2. Reduce response time (optimization)
  3. Both
```

## PHP-FPM Scaling

### Worker Calculation Formula

```
pm.max_children = Available_Memory / Avg_Worker_Memory

Example:
  Server RAM: 4 GB
  OS + overhead: 512 MB
  Available: 3584 MB
  Avg PHP worker: 40 MB

  pm.max_children = 3584 / 40 = 89 workers
```

### Process Manager Modes

| Mode | pm.max_children | Workers | Use Case |
|------|-----------------|---------|----------|
| `static` | Fixed pool size | Always running | Stable, predictable traffic |
| `dynamic` | Max pool size | Scale between min/max | General purpose, variable traffic |
| `ondemand` | Max pool size | Created per request, killed after idle | Low-traffic, memory-constrained |

### Recommended Settings

| Setting | Static Mode | Dynamic Mode | Ondemand Mode |
|---------|------------|--------------|---------------|
| `pm` | `static` | `dynamic` | `ondemand` |
| `pm.max_children` | 89 | 89 | 89 |
| `pm.start_servers` | — | 20 | — |
| `pm.min_spare_servers` | — | 10 | — |
| `pm.max_spare_servers` | — | 30 | — |
| `pm.max_requests` | 500 | 500 | 500 |
| `pm.process_idle_timeout` | — | — | `10s` |

## OPcache Preloading (PHP 8.4)

```ini
; php.ini — OPcache settings for production
opcache.enable=1
opcache.memory_consumption=256
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.preload=/app/config/preload.php
opcache.preload_user=www-data
opcache.jit=1255
opcache.jit_buffer_size=128M
```

```php
<?php

declare(strict_types=1);

namespace App\Config;

// preload.php — Preload hot classes into OPcache at FPM startup
// All preloaded classes are available without autoloading overhead

$classMap = [
    __DIR__ . '/../src/Domain/Entity/',
    __DIR__ . '/../src/Domain/ValueObject/',
    __DIR__ . '/../src/Application/UseCase/',
];

foreach ($classMap as $directory) {
    $iterator = new \RecursiveIteratorIterator(
        new \RecursiveDirectoryIterator($directory),
    );

    /** @var \SplFileInfo $file */
    foreach ($iterator as $file) {
        if ($file->isFile() && $file->getExtension() === 'php') {
            opcache_compile_file($file->getRealPath());
        }
    }
}
```

## Quick Reference Tables

### Scaling Decision Matrix

| Signal | Action | Implementation |
|--------|--------|----------------|
| CPU > 80% sustained | Add instances or upgrade CPU | Horizontal + auto-scaling |
| Memory > 85% | Reduce worker count or add RAM | pm.max_children tuning |
| Response time > SLA | Profile + optimize or add capacity | APM + horizontal scaling |
| Connection pool exhausted | Add pooler or increase pool | pgbouncer / ProxySQL |
| Disk I/O bottleneck | Move to SSD, offload to object storage | Infrastructure change |
| Request queue growing | Add PHP-FPM workers | pm.max_children increase |

### Common Bottlenecks

| Bottleneck | Symptom | Fix |
|------------|---------|-----|
| Database queries | Slow response, high DB CPU | Query optimization, caching, read replicas |
| Session storage | Inconsistent sessions across servers | Redis sessions |
| File uploads | Disk I/O, storage limits | Object storage (S3) |
| External API calls | Timeout, high latency | Circuit breaker, async processing |
| PHP-FPM workers | 502/504 errors, request queue | Increase pm.max_children |
| OPcache | Slow first requests after deploy | Preloading, warm-up scripts |

## Detection Patterns

```bash
# PHP-FPM configuration
Grep: "pm\.max_children|pm\.start_servers|pm\.min_spare|pm\.max_spare" --glob "**/php-fpm*.conf"
Grep: "pm\.max_children|pm\.start_servers" --glob "**/www.conf"
Grep: "pm\.max_requests|pm\.process_idle_timeout" --glob "**/php-fpm*.conf"

# OPcache settings
Grep: "opcache\." --glob "**/php.ini"
Grep: "opcache_compile_file|opcache_reset" --glob "**/*.php"
Grep: "opcache\.preload" --glob "**/php.ini"

# Session configuration
Grep: "session\.save_handler|session\.save_path" --glob "**/php.ini"
Grep: "session_start|SESSION" --glob "**/*.php"
Grep: "Redis.*session|session.*redis" --glob "**/*.php"

# Connection pooling
Grep: "PDO::ATTR_PERSISTENT|ATTR_PERSISTENT" --glob "**/*.php"
Grep: "pgbouncer|proxysql" --glob "**/docker-compose*.yml"

# Stateless violations
Grep: "file_put_contents|fwrite.*tmp" --glob "**/src/**/*.php"
Grep: "\\\$_SESSION" --glob "**/src/**/*.php"
Grep: "apc_store|apcu_store" --glob "**/src/**/*.php"

# Scaling indicators
Grep: "HORIZONTAL_SCALE|AUTO_SCALE|REPLICAS" --glob "**/.env*"
Grep: "replicas:|scale:" --glob "**/docker-compose*.yml"
```

## References

For detailed information, load these reference files:

- `references/scaling-patterns.md` — Horizontal scaling strategies, auto-scaling triggers, read replicas, write scaling, caching as scaling tool
- `references/php-specifics.md` — PHP-FPM tuning, OPcache settings, shared-nothing architecture, persistent connections, external poolers, real-time alternatives
