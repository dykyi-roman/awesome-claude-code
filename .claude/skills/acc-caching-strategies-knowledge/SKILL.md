---
name: acc-caching-strategies-knowledge
description: Caching Strategies knowledge base. Provides caching patterns (Cache-Aside, Read-Through, Write-Through, Write-Behind), invalidation approaches, multi-level caching, and Redis data structures for caching audits and generation.
---

# Caching Strategies Knowledge Base

Quick reference for caching patterns, invalidation strategies, and Redis implementation guidelines. Focuses on caching theory and Redis patterns — for Cache-Aside code generation, see `acc-create-cache-aside`.

## Caching Strategies

| Strategy | How It Works | Consistency | Performance | Use Case |
|----------|-------------|-------------|-------------|----------|
| Cache-Aside | App reads cache first, fetches from DB on miss, writes to cache | Eventual | Read-heavy | General purpose, most common |
| Read-Through | Cache itself fetches from DB on miss | Eventual | Read-heavy | Transparent caching layer |
| Write-Through | App writes to cache and DB synchronously | Strong | Write-heavy (slower writes) | Consistency-critical data |
| Write-Behind | App writes to cache, cache writes to DB asynchronously | Eventual | Write-heavy (fast writes) | High write throughput |
| Write-Around | App writes directly to DB, cache populated on read | Eventual | Infrequent-read data | Write-once, read-later |

### Strategy Flow Diagrams

```
Cache-Aside (Lazy Loading):
  Read:  App → Cache (hit?) → yes → return
                             → no  → DB → write to Cache → return
  Write: App → DB → invalidate Cache

Read-Through:
  Read:  App → Cache (hit?) → yes → return
                             → no  → Cache fetches from DB → return
  Write: App → DB → invalidate Cache

Write-Through:
  Read:  App → Cache (hit?) → yes → return
                             → no  → DB → return
  Write: App → Cache → Cache writes to DB (sync)

Write-Behind (Write-Back):
  Read:  App → Cache (hit?) → yes → return
                             → no  → DB → return
  Write: App → Cache → Cache writes to DB (async, batched)
```

## Cache Invalidation Approaches

| Approach | Description | Consistency | Complexity |
|----------|-------------|-------------|------------|
| TTL (Time-To-Live) | Cache expires after fixed duration | Eventual (stale window) | Low |
| Event-Driven | Invalidate on domain event | Near real-time | Medium |
| Versioned Keys | Include version in cache key | Immediate (new key) | Medium |
| Tag-Based | Group related keys by tag, purge by tag | Immediate | High |
| Write-Through | Update cache on write | Immediate | Medium |
| Manual | Explicit invalidation in code | Depends on discipline | Low |

### TTL Selection Guide

| Data Type | TTL | Reasoning |
|-----------|-----|-----------|
| Static config | 1-24 hours | Rarely changes |
| User profile | 5-15 minutes | Moderate change frequency |
| Session data | 30 minutes | Linked to session timeout |
| Product catalog | 1-5 minutes | Moderate updates |
| Search results | 30-60 seconds | Frequent updates |
| Real-time data | 5-15 seconds | High change frequency |
| Counters/stats | No TTL (event-driven) | Update on write |

## Multi-Level Caching

```
┌─────────────────────────────────────────────────┐
│                 MULTI-LEVEL CACHE                 │
│                                                   │
│   Request → L1 (In-Process)  hit → return         │
│                              miss ↓               │
│            L2 (Redis/Memcached) hit → populate L1  │
│                              miss ↓               │
│            L3 (CDN/HTTP Cache) hit → populate L2   │
│                              miss ↓               │
│            Database → populate L2 → populate L1    │
└─────────────────────────────────────────────────┘
```

| Level | Storage | Latency | Capacity | Scope |
|-------|---------|---------|----------|-------|
| L1 | In-process (APCu, static) | < 1μs | Small (MB) | Per-process |
| L2 | Distributed (Redis) | 1-5ms | Large (GB) | Shared |
| L3 | CDN / HTTP Cache | 5-50ms | Very large | Global |
| Origin | Database | 10-100ms | Unlimited | Source of truth |

## Redis Data Structures for Caching

| Structure | When to Use | Example |
|-----------|------------|---------|
| String | Simple key-value, serialized objects | User session, JSON blob |
| Hash | Object with fields, partial reads | User profile (name, email, role) |
| Sorted Set | Ranked data, leaderboards, time-series | Top products, recent activity |
| List | Queues, recent items, feeds | Recent notifications |
| Set | Unique collections, tags | User permissions, online users |
| HyperLogLog | Cardinality estimation | Unique visitors count |

## Strategy Selection by Workload

| Workload | Strategy | Why |
|----------|----------|-----|
| Read-heavy, tolerance for stale | Cache-Aside + TTL | Simple, effective |
| Read-heavy, consistency needed | Cache-Aside + event invalidation | Fresh data |
| Write-heavy, read-after-write | Write-Through | Immediate consistency |
| Write-heavy, async OK | Write-Behind | Best write performance |
| Mixed, complex invalidation | Tag-based + event-driven | Granular control |
| API responses | HTTP Cache (CDN) + L2 | Reduce server load |

## Detection Patterns

```bash
# Cache usage
Grep: "Cache|Redis|Memcached|APCu|apc_" --glob "**/*.php"
Grep: "CacheInterface|CacheItemPoolInterface|SimpleCacheInterface" --glob "**/*.php"

# Cache-Aside pattern
Grep: "->get\(.*\).*->set\(" --glob "**/*.php"
Grep: "cache->has|cache->get|cache->set" --glob "**/*.php"

# TTL configuration
Grep: "ttl|expire|setex|SETEX|TTL" --glob "**/*.php"
Grep: "CACHE_TTL|CACHE_LIFETIME" --glob "**/.env*"

# Cache invalidation
Grep: "->delete\(|->invalidate\(|->clear\(|->flush\(" --glob "**/*.php"
Grep: "invalidateTag|invalidateTags|clearByTag" --glob "**/*.php"

# Redis patterns
Grep: "Predis|PhpRedis|Redis::|new Redis" --glob "**/*.php"
Grep: "REDIS_HOST|REDIS_URL" --glob "**/.env*"

# Multi-level caching
Grep: "ChainCache|StackedCache|MultiLevelCache" --glob "**/*.php"
Grep: "apcu_fetch|apcu_store" --glob "**/*.php"
```

## References

For detailed information, load these reference files:

- `references/strategies.md` — Detailed strategy analysis, cache warming, stampede prevention, distributed consistency
- `references/redis-patterns.md` — Eviction policies, data structure guide, cluster/sentinel, Lua scripting, PHP patterns
