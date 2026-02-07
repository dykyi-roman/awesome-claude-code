---
name: acc-docker-networking-knowledge
description: Docker networking knowledge base. Provides network configuration patterns, DNS resolution, port mapping, and multi-service communication for PHP.
---

# Docker Networking Knowledge Base

Network configuration patterns and communication strategies for PHP Docker stacks.

## Network Types

| Type | Driver | Use Case | Isolation | Performance |
|------|--------|----------|-----------|-------------|
| **Bridge** | `bridge` | Default single-host | Container-level | Good |
| **Host** | `host` | Maximum performance | None (shares host) | Best |
| **Overlay** | `overlay` | Multi-host (Swarm/K8s) | Container-level | Moderate |
| **None** | `none` | Complete isolation | Full | N/A |
| **Macvlan** | `macvlan` | Direct LAN access | Network-level | Good |

## PHP-FPM + Nginx Communication

### TCP Socket (Default in Docker)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     TCP SOCKET COMMUNICATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Client ──▶ :80 ──▶ ┌─────────┐  TCP :9000  ┌──────────┐                 │
│                       │  Nginx  │ ──────────▶ │ PHP-FPM  │                 │
│                       └─────────┘              └──────────┘                 │
│                                                                              │
│   Nginx config: fastcgi_pass php:9000;                                      │
│   PHP-FPM config: listen = 0.0.0.0:9000                                    │
│                                                                              │
│   Pros: Works across containers, simple setup, scalable                     │
│   Cons: Slight overhead vs Unix socket                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Unix Socket (Shared Volume)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    UNIX SOCKET COMMUNICATION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Client ──▶ :80 ──▶ ┌─────────┐  /sock/fpm  ┌──────────┐                 │
│                       │  Nginx  │ ──────────▶ │ PHP-FPM  │                 │
│                       └────┬────┘              └────┬─────┘                 │
│                            │     shared volume      │                       │
│                            └────────┐  ┌────────────┘                       │
│                                     ▼  ▼                                    │
│                              ┌──────────────┐                               │
│                              │ /var/run/php/ │                               │
│                              │  php-fpm.sock │                               │
│                              └──────────────┘                               │
│                                                                              │
│   Nginx config: fastcgi_pass unix:/var/run/php/php-fpm.sock;               │
│   PHP-FPM config: listen = /var/run/php/php-fpm.sock                       │
│                                                                              │
│   Pros: ~5-10% faster, no TCP overhead                                      │
│   Cons: Requires shared volume, harder to scale                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

Compose configuration for Unix socket:

```yaml
services:
  php:
    volumes:
      - php-socket:/var/run/php

  nginx:
    volumes:
      - php-socket:/var/run/php:ro

volumes:
  php-socket:
```

## DNS Resolution in Compose

Docker Compose provides automatic DNS resolution using service names.

```
┌──────────────────────────────────────────────────────────┐
│              DNS RESOLUTION                                │
├──────────────────────────────────────────────────────────┤
│                                                           │
│   Service Name    ──▶  Container IP                       │
│   ────────────────────────────────────                    │
│   postgres        ──▶  172.20.0.2                         │
│   redis           ──▶  172.20.0.3                         │
│   rabbitmq        ──▶  172.20.0.4                         │
│   php             ──▶  172.20.0.5                         │
│   nginx           ──▶  172.20.0.6                         │
│                                                           │
│   Resolution scope: within same network only              │
│   Resolver: Docker embedded DNS (127.0.0.11)             │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

PHP connection strings using service names:

```php
// PostgreSQL
'postgresql://app:secret@postgres:5432/app'

// Redis
'redis://redis:6379'

// RabbitMQ
'amqp://guest:guest@rabbitmq:5672/%2f'

// Elasticsearch
'http://elasticsearch:9200'
```

### DNS Aliases

```yaml
services:
  postgres:
    networks:
      backend:
        aliases:
          - db
          - database
          - pg
```

## Port Mapping Strategies

| Pattern | Syntax | Visibility | Use Case |
|---------|--------|------------|----------|
| **Published** | `ports: ["8080:80"]` | Host + containers | Dev access, public services |
| **Exposed** | `expose: ["9000"]` | Containers only | Internal services (FPM) |
| **Host binding** | `ports: ["127.0.0.1:5432:5432"]` | Localhost only | Databases in dev |
| **Random host** | `ports: ["5432"]` | Random host port | CI, parallel testing |

### Recommended Port Mapping

```yaml
services:
  # Public-facing — bind to all interfaces
  nginx:
    ports:
      - "80:80"
      - "443:443"

  # Internal service — expose only (no host port)
  php:
    expose:
      - "9000"

  # Database — localhost only (dev security)
  postgres:
    ports:
      - "127.0.0.1:${POSTGRES_PORT:-5432}:5432"

  # Management UI — localhost only
  rabbitmq:
    ports:
      - "127.0.0.1:${RABBITMQ_MGMT_PORT:-15672}:15672"
```

## Network Segmentation

```yaml
networks:
  frontend:
    driver: bridge
    # Public-facing services (Nginx, Mailhog UI)

  backend:
    driver: bridge
    internal: true
    # Database, cache, queue — no external access

  monitoring:
    driver: bridge
    # Prometheus, Grafana, Jaeger
```

### Segmentation Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│   Service         │ frontend │ backend │ monitoring │ internet  │
│   ────────────────┼──────────┼─────────┼────────────┼────────── │
│   Nginx           │    ✓     │         │            │    ✓      │
│   PHP-FPM         │    ✓     │    ✓    │            │           │
│   Worker          │          │    ✓    │            │           │
│   Cron            │          │    ✓    │            │           │
│   PostgreSQL      │          │    ✓    │            │           │
│   Redis           │          │    ✓    │            │           │
│   RabbitMQ        │          │    ✓    │            │           │
│   Elasticsearch   │          │    ✓    │            │           │
│   Prometheus      │          │    ✓    │     ✓      │           │
│   Grafana         │          │         │     ✓      │    ✓      │
│   Jaeger          │          │    ✓    │     ✓      │           │
└─────────────────────────────────────────────────────────────────┘
```

The `internal: true` flag on the backend network prevents containers from reaching the internet, ensuring databases and caches are not exposed.

## Inter-Container Communication

### Same Network (Direct)

```php
// Containers on the same network communicate directly via service name
$redis = new \Redis();
$redis->connect('redis', 6379);
```

### Cross-Network (Shared Service)

```yaml
services:
  php:
    networks:
      - frontend
      - backend    # PHP needs both to talk to Nginx AND database

  postgres:
    networks:
      - backend    # Only backend — no direct external access
```

### Service Discovery Pattern

```php
// Use environment variables for service endpoints
$dbHost = getenv('DATABASE_HOST') ?: 'postgres';
$redisHost = getenv('REDIS_HOST') ?: 'redis';
$amqpHost = getenv('AMQP_HOST') ?: 'rabbitmq';
```

## host.docker.internal for Local Development

Access host machine services from within containers:

```yaml
services:
  php:
    extra_hosts:
      - "host.docker.internal:host-gateway"
    environment:
      # Connect to services running on host machine
      XDEBUG_CONFIG: "client_host=host.docker.internal"
```

| Platform | host.docker.internal | Notes |
|----------|---------------------|-------|
| Docker Desktop (Mac) | Built-in | Works automatically |
| Docker Desktop (Windows) | Built-in | Works automatically |
| Linux | Requires `extra_hosts` | Use `host-gateway` mapping |

## Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| Container cannot resolve service name | Wrong network | Ensure both services share a network |
| Connection refused between containers | Port not exposed | Add `expose` or check service is listening |
| Intermittent DNS failures (Alpine) | musl resolver | Add `options ndots:0` to resolv.conf |
| Cannot reach host machine | Missing extra_hosts | Add `host.docker.internal:host-gateway` |
| External access to internal service | Missing `internal: true` | Mark backend network as internal |
| Port conflict on host | Port already in use | Use variable port mapping `${PORT:-5432}:5432` |

## References

For service configuration examples, see `acc-docker-compose-knowledge`.
For base image networking considerations, see `acc-docker-base-images-knowledge`.
