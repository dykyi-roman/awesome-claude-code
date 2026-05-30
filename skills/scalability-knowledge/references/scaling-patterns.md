# Scaling Patterns Reference

## Horizontal Scaling Strategies

### Stateless Services

Every application instance must be interchangeable. No local state between requests.

```
┌─────────────────────────────────────────────────────────────────────┐
│                  HORIZONTAL SCALING FLOW                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Traffic spike detected                                            │
│       │                                                              │
│       ▼                                                              │
│   Auto-scaler adds instances                                        │
│       │                                                              │
│       ├──▶ Instance 3 starts (stateless → ready immediately)        │
│       ├──▶ Instance 4 starts (no warm-up needed*)                   │
│       └──▶ Instance 5 starts (serves traffic in seconds)            │
│       │                                                              │
│       ▼                                                              │
│   Load balancer distributes evenly                                  │
│       │                                                              │
│       ▼                                                              │
│   Traffic subsides → auto-scaler removes instances                  │
│                                                                      │
│   * OPcache preloading eliminates class-loading warm-up             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Sticky Sessions Avoidance

| Pattern | Problem | Solution |
|---------|---------|----------|
| Sticky sessions | Server affinity defeats load balancing | Externalize session to Redis |
| Local file cache | Different files per server | Shared Redis cache |
| Local upload storage | Files on one server only | Object storage (S3/MinIO) |
| In-memory state | Lost on process restart | External state store |

### Load Balancer Health Checks

```php
<?php

declare(strict_types=1);

namespace Health;

final readonly class HealthCheckAction
{
    public function __construct(
        private \PDO $pdo,
        private \Redis $redis,
    ) {}

    public function __invoke(): array
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'opcache' => $this->checkOpcache(),
        ];

        $healthy = !in_array(false, array_column($checks, 'ok'), true);

        return [
            'status' => $healthy ? 'healthy' : 'degraded',
            'checks' => $checks,
            'timestamp' => (new \DateTimeImmutable())->format('c'),
        ];
    }

    private function checkDatabase(): array
    {
        try {
            $this->pdo->query('SELECT 1');
            return ['ok' => true, 'latency_ms' => 0];
        } catch (\Throwable $e) {
            return ['ok' => false, 'error' => $e->getMessage()];
        }
    }

    private function checkRedis(): array
    {
        try {
            $this->redis->ping();
            return ['ok' => true];
        } catch (\Throwable $e) {
            return ['ok' => false, 'error' => $e->getMessage()];
        }
    }

    private function checkOpcache(): array
    {
        $status = opcache_get_status(false);
        return [
            'ok' => $status !== false && $status['opcache_enabled'],
            'memory_usage_pct' => $status
                ? round($status['memory_usage']['used_memory'] / ($status['memory_usage']['used_memory'] + $status['memory_usage']['free_memory']) * 100, 1)
                : 0,
        ];
    }
}
```

## Vertical Scaling Limits

| Resource | Practical Limit | Bottleneck |
|----------|----------------|------------|
| CPU cores | 128-256 cores | Single-threaded PHP (per-request) |
| RAM | 2-4 TB | Diminishing returns past needed working set |
| Disk I/O | NVMe ceiling | Move to distributed storage |
| Network | 100 Gbps | Rarely the bottleneck for PHP |
| Database connections | ~5000 per instance | Connection pooler needed |

### When Vertical Hits the Wall

```
Cost vs Capacity:
  2 vCPU / 4GB  →  $30/mo  →  ~200 req/s
  4 vCPU / 8GB  →  $60/mo  →  ~400 req/s    (linear)
  8 vCPU / 16GB →  $120/mo →  ~750 req/s    (sub-linear)
  16 vCPU / 32GB → $250/mo →  ~1200 req/s   (diminishing returns)
  64 vCPU / 128GB → $1200/mo → ~3000 req/s  (expensive per-req)

Horizontal at $60/mo per instance:
  5 instances  → $300/mo  → ~2000 req/s  (linear scaling)
  10 instances → $600/mo  → ~4000 req/s  (still linear)
  20 instances → $1200/mo → ~8000 req/s  (still linear)
```

## Auto-Scaling Triggers

### Metrics-Based Auto-Scaling

| Metric | Threshold (Scale Up) | Threshold (Scale Down) | Cooldown |
|--------|---------------------|----------------------|----------|
| CPU utilization | > 70% for 3 min | < 30% for 10 min | 5 min |
| Memory utilization | > 80% for 3 min | < 40% for 10 min | 5 min |
| Request queue depth | > 10 pending | = 0 for 5 min | 3 min |
| Response time (p95) | > 500ms for 2 min | < 100ms for 10 min | 5 min |
| PHP-FPM active processes | > 80% of max_children | < 20% of max_children | 3 min |

### Predictive Scaling

```
┌────────────────────────────────────────────────────────┐
│              SCALING TIMELINE                           │
├────────────────────────────────────────────────────────┤
│                                                         │
│   06:00  Low traffic       → 2 instances (min)         │
│   08:00  Morning ramp-up   → 5 instances (predictive)  │
│   12:00  Peak lunch traffic → 10 instances (reactive)   │
│   14:00  Afternoon steady  → 7 instances               │
│   18:00  Evening decline   → 4 instances               │
│   22:00  Night low         → 2 instances (min)         │
│                                                         │
│   Predictive: pre-scale before known peaks             │
│   Reactive: respond to unexpected spikes               │
│                                                         │
└────────────────────────────────────────────────────────┘
```

## Read Replicas for Read-Heavy Workloads

### Read Replica Architecture

```
┌─────────────────────────────────────────────────────────┐
│              READ REPLICA PATTERN                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Application                                           │
│       │                                                  │
│       ├── INSERT/UPDATE/DELETE ──▶ Primary (Master)      │
│       │                              │                   │
│       │                    Replication Stream             │
│       │                    (async / semi-sync)           │
│       │                              │                   │
│       │                   ┌──────────┼──────────┐       │
│       │                   │          │          │       │
│       │                   ▼          ▼          ▼       │
│       └── SELECT ──▶  Replica 1  Replica 2  Replica 3  │
│                                                          │
│   Read:Write ratio 80:20 → 3 replicas handle 3x reads  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Replica Lag Handling

| Strategy | When to Use | Trade-off |
|----------|------------|-----------|
| Read from master | Critical reads (after write) | More master load |
| Lag-aware routing | General reads | Complexity |
| Causal consistency token | Read-your-writes guarantee | Extra metadata |
| Synchronous replication | Zero-lag requirement | Write latency increase |

## Write Scaling

### Sharding Strategies

| Strategy | How It Works | Use Case |
|----------|-------------|----------|
| Range-based | Rows split by key range (e.g., user ID 1-1M, 1M-2M) | Sequential access patterns |
| Hash-based | Hash function distributes rows (e.g., `user_id % N`) | Uniform distribution |
| Directory-based | Lookup table maps keys to shards | Flexible, supports rebalancing |
| Geographic | Data stored by user region | Compliance, latency reduction |

### Partitioning

```php
<?php

declare(strict_types=1);

namespace Database;

final readonly class ShardRouter
{
    /**
     * @param array<int, \PDO> $shards
     */
    public function __construct(
        private array $shards,
        private int $shardCount,
    ) {}

    public function getShardForKey(string $key): \PDO
    {
        $hash = crc32($key);
        $shardIndex = abs($hash) % $this->shardCount;

        return $this->shards[$shardIndex]
            ?? throw new \RuntimeException(sprintf('Shard %d not configured', $shardIndex));
    }
}
```

## Caching as a Scaling Tool

### Cache Hit Ratio Impact

| Hit Ratio | DB Queries (1000 req/s) | DB Load Reduction |
|-----------|------------------------|-------------------|
| 0% (no cache) | 1000 queries/s | — |
| 50% | 500 queries/s | 50% |
| 80% | 200 queries/s | 80% |
| 95% | 50 queries/s | 95% |
| 99% | 10 queries/s | 99% |

### Caching Layers for Scaling

| Layer | Technology | Latency | Scales |
|-------|-----------|---------|--------|
| CDN | Cloudflare, CloudFront | ~10ms | Globally |
| Application cache | Redis, Memcached | ~1-5ms | With replicas |
| OPcache | PHP OPcache | ~0μs | Per-process |
| Query result cache | Redis | ~1-5ms | With replicas |
| Full-page cache | Varnish, Nginx | ~1ms | Per-server |
