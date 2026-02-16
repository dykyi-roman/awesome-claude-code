# Redis Patterns Reference

## Eviction Policies

| Policy | Description | Use Case |
|--------|-------------|----------|
| `noeviction` | Return error when memory full | Critical data, no data loss |
| `allkeys-lru` | Evict least recently used key | General caching (recommended default) |
| `allkeys-lfu` | Evict least frequently used key | Frequency-based access patterns |
| `volatile-lru` | Evict LRU among keys with TTL | Mixed persistent + cache |
| `volatile-lfu` | Evict LFU among keys with TTL | Frequency-based with persistent keys |
| `allkeys-random` | Evict random key | When all keys equally likely accessed |
| `volatile-random` | Evict random key with TTL | Random eviction with persistent keys |
| `volatile-ttl` | Evict keys with shortest TTL | Time-sensitive data prioritization |

### Policy Selection

```
Q: Do you have persistent (non-TTL) keys?
├── No → allkeys-lru (default recommendation)
│       or allkeys-lfu (if access frequency matters)
└── Yes → volatile-lru (cache keys have TTL, persistent don't)
         or noeviction (if data loss is unacceptable)
```

### Configuration

```
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
maxmemory-samples 10  # LRU approximation accuracy (higher = more accurate, slower)
```

## Data Structure Selection Guide

### String vs Hash

| Scenario | Use String | Use Hash |
|----------|-----------|----------|
| Store serialized object | `SET user:123 '{"name":"John","email":"..."}'` | `HSET user:123 name John email john@...` |
| Read whole object | `GET user:123` ✓ Fast | `HGETALL user:123` ✓ Fast |
| Read single field | ✗ Must deserialize all | `HGET user:123 email` ✓ Efficient |
| Update single field | ✗ Must rewrite all | `HSET user:123 email new@...` ✓ Efficient |
| Memory (small objects) | Higher (per-key overhead) | Lower (ziplist encoding) |
| Memory (large objects) | Lower (one value) | Higher (field overhead) |
| TTL per field | ✗ Whole key only | ✗ Whole key only |

**Recommendation:** Use Hash when you need partial reads/writes. Use String for serialized blobs or when TTL per field isn't needed.

### Sorted Set for Leaderboards/Rankings

```php
// Add score
$redis->zAdd('leaderboard:daily', $score, $userId);

// Top 10
$redis->zRevRange('leaderboard:daily', 0, 9, withscores: true);

// User rank
$redis->zRevRank('leaderboard:daily', $userId);

// Score range
$redis->zRangeByScore('leaderboard:daily', 100, 500, withscores: true);
```

### Sorted Set for Time-Series Cache

```php
// Store recent activity (sorted by timestamp)
$redis->zAdd('activity:user:123', time(), json_encode($event));

// Get last 20 activities
$redis->zRevRange('activity:user:123', 0, 19);

// Remove older than 24 hours
$redis->zRemRangeByScore('activity:user:123', '-inf', time() - 86400);
```

### Set for Unique Collections

```php
// Track online users
$redis->sAdd('online:users', $userId);
$redis->sRem('online:users', $userId);
$redis->sIsMember('online:users', $userId);
$redis->sCard('online:users'); // count

// User permissions
$redis->sAdd('permissions:user:123', 'read', 'write', 'admin');
$redis->sIsMember('permissions:user:123', 'admin');

// Intersection: users with both roles
$redis->sInter('role:admin', 'role:active');
```

### HyperLogLog for Cardinality

```php
// Count unique visitors (memory: ~12KB regardless of count)
$redis->pfAdd('visitors:2025-01-15', $visitorId);
$redis->pfCount('visitors:2025-01-15'); // approximate count

// Merge multiple days
$redis->pfMerge('visitors:week', 'visitors:2025-01-13', 'visitors:2025-01-14', 'visitors:2025-01-15');
```

## Redis Cluster

### Architecture

```
┌────────────────────────────────────────────────┐
│              Redis Cluster (16384 slots)         │
│                                                  │
│  Node A          Node B          Node C          │
│  Slots 0-5460    Slots 5461-10922 Slots 10923-16383│
│  ┌──────────┐   ┌──────────┐   ┌──────────┐    │
│  │ Primary A │   │ Primary B │   │ Primary C │    │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘    │
│       │              │              │            │
│  ┌────▼─────┐   ┌────▼─────┐   ┌────▼─────┐    │
│  │ Replica A │   │ Replica B │   │ Replica C │    │
│  └──────────┘   └──────────┘   └──────────┘    │
└────────────────────────────────────────────────┘
```

### Key Distribution

```
slot = CRC16(key) % 16384

# Hash tags for co-location
{user:123}:profile → slot = CRC16("user:123") → same slot
{user:123}:orders  → slot = CRC16("user:123") → same slot
```

### Cluster Limitations

| Feature | Cluster Support |
|---------|----------------|
| Multi-key operations | Only if keys in same slot (use hash tags) |
| Lua scripts | Only for keys in same slot |
| Transactions | Only for keys in same slot |
| Pub/Sub | Supported (broadcast to all nodes) |
| SELECT (database) | Only database 0 |

## Redis Sentinel (High Availability)

### Architecture

```
┌────────────────────────────────────────┐
│            Redis Sentinel (3+)          │
│                                          │
│  Sentinel 1    Sentinel 2    Sentinel 3  │
│      │              │              │     │
│      └──────────────┼──────────────┘     │
│                     │                    │
│              ┌──────▼──────┐             │
│              │   Primary    │             │
│              └──────┬──────┘             │
│                     │                    │
│          ┌──────────┼──────────┐         │
│          │                     │         │
│    ┌─────▼─────┐        ┌─────▼─────┐   │
│    │  Replica 1 │        │  Replica 2 │   │
│    └───────────┘        └───────────┘   │
└────────────────────────────────────────┘
```

### Sentinel vs Cluster

| Aspect | Sentinel | Cluster |
|--------|----------|---------|
| Purpose | HA only (failover) | HA + sharding |
| Data distribution | All data on primary | Sharded across nodes |
| Max data size | Single node memory | Sum of all nodes |
| Complexity | Lower | Higher |
| Multi-key ops | Full support | Same-slot only |
| Use case | < 25GB, HA needed | > 25GB or high throughput |

## Lua Scripting for Atomic Operations

### Rate Limiter (Sliding Window)

```lua
-- KEYS[1] = rate limit key
-- ARGV[1] = window size (seconds)
-- ARGV[2] = max requests
-- ARGV[3] = current timestamp

local key = KEYS[1]
local window = tonumber(ARGV[1])
local limit = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- Remove expired entries
redis.call('ZREMRANGEBYSCORE', key, 0, now - window)

-- Count current requests
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
    redis.call('EXPIRE', key, window)
    return 1  -- allowed
else
    return 0  -- denied
end
```

### PHP Execution

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class RedisLuaExecutor
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function executeSlidingWindowRateLimit(
        string $key,
        int $windowSeconds,
        int $maxRequests,
    ): bool {
        $script = <<<'LUA'
            local key = KEYS[1]
            local window = tonumber(ARGV[1])
            local limit = tonumber(ARGV[2])
            local now = tonumber(ARGV[3])
            redis.call('ZREMRANGEBYSCORE', key, 0, now - window)
            local count = redis.call('ZCARD', key)
            if count < limit then
                redis.call('ZADD', key, now, now .. ':' .. math.random(1000000))
                redis.call('EXPIRE', key, window)
                return 1
            else
                return 0
            end
        LUA;

        return (bool) $this->redis->eval(
            $script,
            [$key, $windowSeconds, $maxRequests, time()],
            1, // number of KEYS
        );
    }
}
```

## Cache Monitoring

### Key Metrics

| Metric | Formula | Target | Alert |
|--------|---------|--------|-------|
| Hit Rate | hits / (hits + misses) | > 90% | < 80% |
| Miss Rate | misses / (hits + misses) | < 10% | > 20% |
| Memory Usage | used_memory / maxmemory | < 80% | > 90% |
| Eviction Rate | evicted_keys/sec | Low | Sudden spike |
| Connection Count | connected_clients | Stable | > 80% max |
| Latency | per-command latency | < 1ms | > 5ms |

### Redis INFO Monitoring

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Monitoring;

final readonly class RedisCacheMetrics
{
    public function __construct(
        private \Redis $redis,
    ) {}

    public function getMetrics(): array
    {
        $info = $this->redis->info();

        $hits = (int) ($info['keyspace_hits'] ?? 0);
        $misses = (int) ($info['keyspace_misses'] ?? 0);
        $total = $hits + $misses;

        return [
            'hit_rate' => $total > 0 ? round($hits / $total * 100, 2) : 0,
            'miss_rate' => $total > 0 ? round($misses / $total * 100, 2) : 0,
            'used_memory_mb' => round(((int) $info['used_memory']) / 1024 / 1024, 2),
            'max_memory_mb' => round(((int) ($info['maxmemory'] ?? 0)) / 1024 / 1024, 2),
            'connected_clients' => (int) $info['connected_clients'],
            'evicted_keys' => (int) ($info['evicted_keys'] ?? 0),
            'total_commands' => (int) $info['total_commands_processed'],
        ];
    }
}
```

## PHP Connection Patterns

### Predis Connection Pooling

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Cache;

final readonly class RedisConnectionFactory
{
    public static function createSentinel(
        array $sentinels,
        string $service,
    ): \Predis\Client {
        return new \Predis\Client(
            $sentinels,
            [
                'replication' => 'sentinel',
                'service' => $service,
                'parameters' => [
                    'timeout' => 2.0,
                    'read_write_timeout' => 2.0,
                ],
            ],
        );
    }

    public static function createCluster(
        array $nodes,
    ): \Predis\Client {
        return new \Predis\Client(
            $nodes,
            [
                'cluster' => 'redis',
                'parameters' => [
                    'timeout' => 2.0,
                ],
            ],
        );
    }
}
```

### PhpRedis Persistent Connection

```php
// Persistent connection (reused across requests in PHP-FPM)
$redis = new \Redis();
$redis->pconnect(
    host: $host,
    port: $port,
    timeout: 2.0,
    persistent_id: 'cache_pool', // connection pool identifier
);
$redis->setOption(\Redis::OPT_SERIALIZER, \Redis::SERIALIZER_JSON);
$redis->setOption(\Redis::OPT_PREFIX, 'app:');
```
