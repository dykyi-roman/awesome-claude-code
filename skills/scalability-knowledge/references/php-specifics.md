# PHP Scalability Specifics Reference

## PHP-FPM Tuning

### Process Manager Configuration

```ini
; /etc/php/8.4/fpm/pool.d/www.conf

[www]
; Process manager mode
pm = dynamic

; Maximum number of child processes
; Formula: pm.max_children = (Total RAM - OS overhead) / Avg PHP worker memory
; Example: (4096MB - 512MB) / 40MB = 89
pm.max_children = 89

; Number of child processes created on startup (dynamic only)
; Rule of thumb: 25% of max_children
pm.start_servers = 20

; Minimum number of idle processes (dynamic only)
; Prevents slow ramp-up during traffic spikes
pm.min_spare_servers = 10

; Maximum number of idle processes (dynamic only)
; Prevents over-provisioning during low traffic
pm.max_spare_servers = 30

; Number of requests each child process executes before respawning
; Prevents memory leaks from accumulating
pm.max_requests = 500

; Timeout for idle processes to be killed (ondemand only)
pm.process_idle_timeout = 10s

; Status page for monitoring
pm.status_path = /fpm-status
pm.status_listen = 127.0.0.1:9001
```

### Worker Memory Calculation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Monitoring;

final readonly class FpmCapacityCalculator
{
    public function __construct(
        private int $totalMemoryMb,
        private int $osOverheadMb = 512,
        private int $avgWorkerMemoryMb = 40,
    ) {}

    public function calculateMaxChildren(): int
    {
        $availableMemory = $this->totalMemoryMb - $this->osOverheadMb;

        return (int) floor($availableMemory / $this->avgWorkerMemoryMb);
    }

    public function calculateThroughput(float $avgResponseTimeSeconds): float
    {
        return $this->calculateMaxChildren() / $avgResponseTimeSeconds;
    }

    public function report(): array
    {
        $maxChildren = $this->calculateMaxChildren();

        return [
            'total_memory_mb' => $this->totalMemoryMb,
            'available_memory_mb' => $this->totalMemoryMb - $this->osOverheadMb,
            'avg_worker_memory_mb' => $this->avgWorkerMemoryMb,
            'recommended_max_children' => $maxChildren,
            'estimated_throughput_100ms' => $maxChildren / 0.1,
            'estimated_throughput_200ms' => $maxChildren / 0.2,
        ];
    }
}
```

### Mode Selection Guide

| Scenario | Mode | Why |
|----------|------|-----|
| Production, stable traffic | `static` | No fork overhead, predictable memory |
| Production, variable traffic | `dynamic` | Balances memory and responsiveness |
| Development, low traffic | `ondemand` | Minimal resource usage |
| High-traffic API | `static` | Maximum throughput, no fork latency |
| Background workers container | `static` with low count | Dedicated, stable processes |

## OPcache Settings

### Production Configuration

```ini
; /etc/php/8.4/fpm/conf.d/10-opcache.ini

; Enable OPcache
opcache.enable=1
opcache.enable_cli=0

; Memory allocation
; 256MB supports ~20,000 files (typical Symfony/Laravel app)
opcache.memory_consumption=256

; Maximum number of cached scripts
; Set to number of PHP files in project + buffer
opcache.max_accelerated_files=20000

; Maximum wasted memory before restart (percentage)
opcache.max_wasted_percentage=10

; Disable timestamp validation in production
; Requires FPM restart/reload on deploy
opcache.validate_timestamps=0

; Interned strings buffer (for class names, function names)
opcache.interned_strings_buffer=32

; Optimization level (all optimizations enabled)
opcache.optimization_level=0x7FFEBFFF

; JIT configuration (PHP 8.4)
opcache.jit=1255
opcache.jit_buffer_size=128M
```

### Preloading (PHP 8.4)

```php
<?php

declare(strict_types=1);

// config/preload.php
// Specified in php.ini: opcache.preload=/app/config/preload.php

$preloadPaths = [
    __DIR__ . '/../src/Domain/Entity',
    __DIR__ . '/../src/Domain/ValueObject',
    __DIR__ . '/../src/Domain/Event',
    __DIR__ . '/../src/Application/UseCase',
    __DIR__ . '/../src/Application/DTO',
];

$count = 0;

foreach ($preloadPaths as $path) {
    if (!is_dir($path)) {
        continue;
    }

    $iterator = new \RecursiveIteratorIterator(
        new \RecursiveDirectoryIterator($path, \FilesystemIterator::SKIP_DOTS),
    );

    /** @var \SplFileInfo $file */
    foreach ($iterator as $file) {
        if ($file->getExtension() === 'php') {
            opcache_compile_file($file->getRealPath());
            $count++;
        }
    }
}

// Log preloaded count (visible in FPM startup log)
error_log(sprintf('Preloaded %d PHP files into OPcache', $count));
```

### OPcache Monitoring

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Monitoring;

final readonly class OpcacheMonitor
{
    public function getStatus(): array
    {
        $status = opcache_get_status(false);

        if ($status === false) {
            return ['enabled' => false];
        }

        $memory = $status['memory_usage'];
        $stats = $status['opcache_statistics'];
        $totalMemory = $memory['used_memory'] + $memory['free_memory'];

        return [
            'enabled' => true,
            'memory_usage_pct' => round($memory['used_memory'] / $totalMemory * 100, 1),
            'memory_used_mb' => round($memory['used_memory'] / 1024 / 1024, 1),
            'memory_free_mb' => round($memory['free_memory'] / 1024 / 1024, 1),
            'cached_scripts' => $stats['num_cached_scripts'],
            'hit_rate_pct' => round($stats['opcache_hit_rate'], 1),
            'misses' => $stats['misses'],
            'oom_restarts' => $stats['oom_restarts'],
            'jit_enabled' => $status['jit']['enabled'] ?? false,
        ];
    }
}
```

## Shared-Nothing Architecture in PHP

### Why PHP Is Naturally Shared-Nothing

| Aspect | PHP Behavior | Scaling Benefit |
|--------|-------------|-----------------|
| Request lifecycle | Process starts clean, dies after response | No stale state between requests |
| Global variables | Reset per request | No shared memory corruption |
| Database connections | Opened per request (default) | No connection state leaks |
| File handles | Closed per request | No resource leaks |
| Memory | Released per request | No memory leaks (long-term) |

### Shared-Nothing Violations to Avoid

```php
<?php

declare(strict_types=1);

namespace App\Examples;

// VIOLATION: Writing to local filesystem (not shared across instances)
file_put_contents('/tmp/cache/data.json', $jsonData);

// FIX: Use shared storage
$redis->set('cache:data', $jsonData);

// VIOLATION: Using APCu for shared state (per-process only)
apcu_store('user:count', $count);

// FIX: Use Redis for shared counters
$redis->incr('user:count');

// VIOLATION: Storing uploads locally
move_uploaded_file($tmpFile, '/var/www/uploads/' . $filename);

// FIX: Use object storage
$s3Client->putObject([
    'Bucket' => 'uploads',
    'Key' => $filename,
    'Body' => fopen($tmpFile, 'r'),
]);
```

## Persistent Connections

### PDO Persistent Connections

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final readonly class PersistentConnectionFactory
{
    public function __construct(
        private string $dsn,
        private string $username,
        private string $password,
    ) {}

    public function create(): \PDO
    {
        return new \PDO(
            $this->dsn,
            $this->username,
            $this->password,
            [
                // Reuse connections across requests within same FPM worker
                \PDO::ATTR_PERSISTENT => true,
                \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
                \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
                \PDO::ATTR_EMULATE_PREPARES => false,
            ],
        );
    }
}
```

### Persistent Connection Caveats

| Issue | Description | Mitigation |
|-------|-------------|------------|
| Connection state | Transaction/lock state persists | Reset state after each request |
| Connection limit | Each worker holds one connection | Use external pooler |
| Error recovery | Broken connection stays in pool | Implement reconnect logic |
| Memory | Connections consume server RAM | Monitor with `SHOW PROCESSLIST` |

## External Connection Poolers

### pgbouncer Configuration

```ini
; /etc/pgbouncer/pgbouncer.ini

[databases]
myapp = host=postgres port=5432 dbname=myapp

[pgbouncer]
; Transaction pooling: connection returned after each transaction
pool_mode = transaction

; Maximum client connections
max_client_conn = 1000

; Connections per database-user pair
default_pool_size = 25

; Extra connections for SHOW commands
reserve_pool_size = 5

; Timeout for unused server connections
server_idle_timeout = 300

; Authentication
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
```

### ProxySQL Configuration (MySQL)

```sql
-- Add MySQL backend servers
INSERT INTO mysql_servers (hostgroup_id, hostname, port, max_connections)
VALUES (1, 'mysql-primary', 3306, 50),
       (2, 'mysql-replica1', 3306, 50),
       (2, 'mysql-replica2', 3306, 50);

-- Route reads to replicas, writes to primary
INSERT INTO mysql_query_rules (rule_id, match_pattern, destination_hostgroup)
VALUES (1, '^SELECT.*FOR UPDATE', 1),
       (2, '^SELECT', 2),
       (3, '.*', 1);

-- Connection pool settings
UPDATE global_variables SET variable_value='1000' WHERE variable_name='mysql-max_connections';
UPDATE global_variables SET variable_value='50' WHERE variable_name='mysql-default_max_latency_ms';
```

## Real-Time Alternatives

### Swoole / OpenSwoole

```php
<?php

declare(strict_types=1);

// Swoole HTTP Server — keeps processes alive between requests
// Shared memory via Swoole\Table, connection pools built-in

use Swoole\Http\Server;
use Swoole\Http\Request;
use Swoole\Http\Response;

$server = new Server('0.0.0.0', 8080);
$server->set([
    'worker_num' => swoole_cpu_num() * 2,
    'max_request' => 10000,
    'enable_coroutine' => true,
]);

$server->on('request', function (Request $request, Response $response): void {
    $response->header('Content-Type', 'application/json');
    $response->end(json_encode(['status' => 'ok'], JSON_THROW_ON_ERROR));
});

$server->start();
```

### RoadRunner

```yaml
# .rr.yaml — RoadRunner configuration
version: "3"

server:
  command: "php worker.php"
  relay: pipes

http:
  address: "0.0.0.0:8080"
  pool:
    num_workers: 16
    max_jobs: 500
    supervisor:
      max_worker_memory: 128
```

### FrankenPHP

```dockerfile
# Dockerfile — FrankenPHP with worker mode
FROM dunglas/frankenphp:php8.4

COPY . /app

# Worker mode: PHP script stays in memory, handles multiple requests
ENV FRANKENPHP_CONFIG="worker ./public/index.php"

EXPOSE 8080
```

### Comparison

| Runtime | Model | Persistent State | Connection Pool | Use Case |
|---------|-------|-----------------|-----------------|----------|
| PHP-FPM | Process-per-request | No (shared-nothing) | External only | Traditional web apps |
| Swoole | Event-loop, coroutines | Yes (in-memory) | Built-in | High-performance APIs |
| RoadRunner | Long-lived workers | Yes (worker memory) | Via plugins | Balanced performance |
| FrankenPHP | Worker mode + Caddy | Yes (worker memory) | Via Caddy | Modern PHP, HTTP/3 |
