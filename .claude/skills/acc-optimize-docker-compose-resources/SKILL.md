---
name: acc-optimize-docker-compose-resources
description: Optimizes Docker Compose resource allocation for PHP stacks. Configures memory limits, CPU constraints, and service scaling.
---

# Docker Compose Resource Optimization

Configures resource allocation, constraints, and scaling for PHP application stacks.

## Resource Allocation Overview

```
┌─────────────────────────────────────────────────────────────────┐
│            PHP STACK RESOURCE DISTRIBUTION (4GB Host)            │
├─────────────────────────────────────────────────────────────────┤
│  PHP-FPM:   ████████████████████░░░░░░░░░░  1024MB  (25%)     │
│  MySQL:     ████████████████████████░░░░░░  1536MB  (38%)     │
│  Redis:     ████████░░░░░░░░░░░░░░░░░░░░░░   512MB  (13%)    │
│  Nginx:     ████░░░░░░░░░░░░░░░░░░░░░░░░░░   256MB   (6%)    │
│  RabbitMQ:  ████████░░░░░░░░░░░░░░░░░░░░░░   512MB  (13%)    │
│  System:    ████░░░░░░░░░░░░░░░░░░░░░░░░░░   256MB   (6%)    │
└─────────────────────────────────────────────────────────────────┘
```

## Recommended Resource Limits

| Service | Memory Limit | Memory Reservation | CPU Limit | CPU Reservation |
|---------|-------------|-------------------|-----------|----------------|
| PHP-FPM | 512MB-1GB | 256MB | 1.0 | 0.25 |
| Nginx | 128MB-256MB | 64MB | 0.5 | 0.1 |
| MySQL | 1GB-2GB | 512MB | 1.5 | 0.5 |
| PostgreSQL | 1GB-2GB | 512MB | 1.5 | 0.5 |
| Redis | 256MB-512MB | 128MB | 0.5 | 0.1 |
| RabbitMQ | 512MB-1GB | 256MB | 1.0 | 0.25 |

## Service Configurations

### PHP-FPM

```yaml
  php-fpm:
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 1024M }
        reservations: { cpus: "0.25", memory: 256M }
      replicas: 2
    tmpfs: ["/tmp:size=64M"]
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 30s
      timeout: 5s
      start_period: 10s
```

### MySQL

```yaml
  mysql:
    deploy:
      resources:
        limits: { cpus: "1.5", memory: 2048M }
        reservations: { cpus: "0.5", memory: 512M }
    shm_size: "256m"
    command: >
      --innodb-buffer-pool-size=1G --innodb-log-file-size=256M
      --max-connections=200 --tmp-table-size=64M
    ulimits:
      nofile: { soft: 65536, hard: 65536 }
```

### Redis

```yaml
  redis:
    deploy:
      resources:
        limits: { cpus: "0.5", memory: 512M }
        reservations: { cpus: "0.1", memory: 128M }
    command: redis-server --maxmemory 384mb --maxmemory-policy allkeys-lru --save "" --appendonly no
    tmpfs: ["/data:size=384M"]
```

### RabbitMQ

```yaml
  rabbitmq:
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 1024M }
        reservations: { cpus: "0.25", memory: 256M }
    environment:
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.6
      RABBITMQ_DISK_FREE_LIMIT: 128MB
```

## Logging Configuration

```yaml
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

| Service | max-size | max-file | Total Disk |
|---------|----------|----------|-----------|
| PHP-FPM | 10m | 3 | 30MB |
| Nginx | 20m | 5 | 100MB |
| MySQL | 10m | 3 | 30MB |
| Redis | 5m | 2 | 10MB |

## tmpfs for Ephemeral Data

```yaml
    tmpfs:
      - /tmp:size=64M,mode=1777
      - /app/var/cache:size=128M
      - /app/var/log:size=32M
```

Benefits: faster I/O, no disk writes, auto-cleaned on restart.

## shm_size for Databases

```yaml
  postgres:
    shm_size: "256m"   # shared_buffers, WAL buffers, lock tables
  mysql:
    shm_size: "256m"   # InnoDB buffer pool, temp tables
```

## ulimits Configuration

| ulimit | Default | Recommended | Purpose |
|--------|---------|-------------|---------|
| nofile | 1024 | 65536 | Max open files/sockets |
| nproc | 1024 | 4096 | Max processes |
| memlock | 64KB | unlimited | Memory locking (Redis) |

## Scaling with Replicas

```yaml
  php-fpm:
    deploy:
      replicas: 3
      endpoint_mode: dnsrr
      resources:
        limits: { cpus: "0.5", memory: 512M }
    # Total: 1.5 CPU, 1536M memory across 3 replicas
    # Nginx resolves php-fpm to all replicas via DNS round-robin
```

## Before/After Comparison

| Metric | No Limits | With Limits | Improvement |
|--------|-----------|-------------|-------------|
| OOM kills | Frequent | Rare | Predictable |
| Noisy neighbor | Common | Prevented | Isolated |
| Memory waste | 30-50% | < 10% | -80% waste |
| Log disk usage | Unbounded | < 200MB | Controlled |
| Recovery time | Minutes | Seconds | Faster restarts |

## Generation Instructions

1. **Inventory services:** List all containers in the stack
2. **Assess host resources:** Total CPU and memory available
3. **Allocate proportionally:** Database > App > Cache > Proxy
4. **Set limits and reservations:** Limits cap usage, reservations guarantee minimum
5. **Configure logging:** Prevent unbounded disk growth
6. **Add health checks:** Enable automatic recovery
7. **Test under load:** Verify no OOM kills or throttling
