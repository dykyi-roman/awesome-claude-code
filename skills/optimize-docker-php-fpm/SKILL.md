---
name: acc-optimize-docker-php-fpm
description: Optimizes PHP-FPM configuration in Docker containers. Tunes process manager, request handling, and resource allocation for production workloads.
---

# PHP-FPM Configuration Optimization

Provides production-ready PHP-FPM tuning for Docker containers based on workload type and available resources.

## Process Manager Modes

```
┌─────────────────────────────────────────────────────────────────┐
│                  PHP-FPM PROCESS MANAGERS                        │
├─────────────────────────────────────────────────────────────────┤
│  STATIC:    [W][W][W][W][W][W][W][W]   Fixed pool              │
│             Best for: dedicated containers, predictable load    │
│  DYNAMIC:   [W][W][W][W][ ][ ][ ][ ]   Scales up/down         │
│             Best for: variable load, shared resources           │
│  ONDEMAND:  [ ][ ][ ][ ][ ][ ][ ][ ]   Starts on request      │
│             Best for: low-traffic, dev environments             │
└─────────────────────────────────────────────────────────────────┘
```

## Memory Calculation Formula

```
max_children = (available_memory - system_overhead) / avg_worker_memory

Where:
  available_memory = container_memory_limit
  system_overhead  = ~50MB (OS + PHP-FPM master + nginx)
  avg_worker_memory = 30-60MB (depends on application)
```

| Container Memory | System Overhead | Worker Memory | max_children |
|-----------------|-----------------|---------------|-------------|
| 256MB | 50MB | 40MB | 5 |
| 512MB | 50MB | 40MB | 11 |
| 1024MB | 50MB | 40MB | 24 |
| 2048MB | 50MB | 50MB | 39 |

Measure actual worker memory:

```bash
ps aux | grep "php-fpm: pool" | awk '{sum+=$6; n++} END {print sum/n/1024 " MB"}'
```

## Configuration by Workload

### API Workload (Many Fast Requests)

```ini
[www]
pm = static
pm.max_children = 20
request_terminate_timeout = 30s
request_slowlog_timeout = 5s
pm.max_requests = 1000
slowlog = /proc/self/fd/2
```

### Worker Workload (Few Long Requests)

```ini
[www]
pm = dynamic
pm.max_children = 8
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 4
request_terminate_timeout = 300s
request_slowlog_timeout = 30s
pm.max_requests = 200
```

### Mixed Workload

```ini
[www]
pm = dynamic
pm.max_children = 15
pm.start_servers = 5
pm.min_spare_servers = 3
pm.max_spare_servers = 8
request_terminate_timeout = 60s
request_slowlog_timeout = 10s
pm.max_requests = 500
```

## Dynamic Mode Formulas

```
pm.start_servers     = (min_spare + max_spare) / 2
pm.min_spare_servers = max_children * 0.25
pm.max_spare_servers = max_children * 0.75
```

## pm.max_requests by Application Type

| Application Type | Recommended Value |
|-----------------|-------------------|
| Stateless API | 1000-5000 |
| Framework with ORM | 500-1000 |
| Legacy application | 100-500 |
| Memory-intensive processing | 50-200 |

## Health Check and Monitoring

```ini
pm.status_path = /status
ping.path = /ping
ping.response = pong
```

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD php-fpm-healthcheck || exit 1
```

Key status metrics to monitor:
- **active processes:** current load
- **listen queue:** requests waiting (should be 0)
- **max children reached:** need more workers
- **slow requests:** performance issues

## Docker-Specific Settings

```ini
; Logging to stdout/stderr
error_log = /proc/self/fd/2
access.log = /proc/self/fd/2
clear_env = yes
catch_workers_output = yes
decorate_workers_output = no
```

## Before/After Comparison

| Metric | Default | Optimized (static) | Improvement |
|--------|---------|---------------------|-------------|
| max_children | 5 | 20 | +300% capacity |
| Idle memory (512MB) | 200MB wasted | ~50MB overhead | -75% waste |
| Request latency (p99) | 500ms | 150ms | -70% |
| Throughput (req/s) | 50 | 200 | +300% |
| Memory leak recovery | Never | Every 1000 req | Predictable |

## Complete Production Configuration

```ini
[global]
error_log = /proc/self/fd/2
log_level = warning
daemonize = no

[www]
user = www-data
group = www-data
listen = 0.0.0.0:9000
pm = static
pm.max_children = 20
pm.max_requests = 1000
request_terminate_timeout = 30s
request_slowlog_timeout = 5s
slowlog = /proc/self/fd/2
pm.status_path = /status
ping.path = /ping
ping.response = pong
clear_env = yes
catch_workers_output = yes
decorate_workers_output = no
access.log = /proc/self/fd/2
access.format = "%R - %u %t \"%m %r\" %s %{mili}dms %{mega}MMB %C%%"
```

## Generation Instructions

1. **Determine workload type:** API, Worker, or Mixed
2. **Calculate max_children:** Based on container memory and worker memory
3. **Select PM mode:** Static for production, dynamic for variable load
4. **Configure timeouts:** Based on expected request duration
5. **Set max_requests:** Based on application memory behavior
6. **Enable monitoring:** Status page, health check, slow log
