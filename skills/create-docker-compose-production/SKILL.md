---
name: acc-create-docker-compose-production
description: Generates Docker Compose production configurations for PHP projects. Creates hardened stacks with resource limits, restart policies, and monitoring.
---

# Docker Compose Production Generator

Generates hardened Docker Compose production configurations with resource limits, restart policies, network segmentation, and logging.

## Generated Files

```
docker-compose.prod.yml   # Production stack configuration
```

## Generation Instructions

1. **Analyze:** Identify services, determine resource needs, plan network segmentation, define persistence
2. **Harden:** Resource limits, restart policies, read-only root, network segmentation, log rotation, health checks
3. **Configure:** Service dependencies with health conditions, graceful shutdown, persistent volumes

## Docker Compose Production Stack

```yaml
# docker-compose.prod.yml
services:
  php:
    image: ${REGISTRY:-registry.example.com}/app:${APP_VERSION:-latest}
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=64M
      - /var/run:size=1M
    environment:
      APP_ENV: prod
      APP_DEBUG: "0"
      DATABASE_URL: "postgresql://${DB_USER}:${DB_PASSWORD}@database:5432/${DB_NAME}?serverVersion=17"
      REDIS_URL: "redis://redis:6379"
      RABBITMQ_URL: "amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@rabbitmq:5672"
    depends_on:
      database: { condition: service_healthy }
      redis: { condition: service_healthy }
    healthcheck:
      test: ["CMD-SHELL", "SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1"]
      interval: 30s
      timeout: 5s
      start_period: 15s
      retries: 3
    deploy:
      resources:
        limits: { cpus: "2.0", memory: 512M }
        reservations: { cpus: "0.5", memory: 256M }
      replicas: 2
    logging: { driver: json-file, options: { max-size: "10m", max-file: "5" } }
    stop_grace_period: 30s
    networks: [backend]

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    read_only: true
    tmpfs:
      - /tmp:size=32M
      - /var/cache/nginx:size=64M
      - /var/run:size=1M
    ports:
      - "${HTTP_PORT:-80}:80"
      - "${HTTPS_PORT:-443}:443"
    volumes:
      - ./docker/nginx/production.conf:/etc/nginx/conf.d/default.conf:ro
      - ssl-certs:/etc/nginx/ssl:ro
      - static-files:/app/public:ro
    depends_on:
      php: { condition: service_healthy }
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 256M }
        reservations: { cpus: "0.25", memory: 64M }
    logging: { driver: json-file, options: { max-size: "10m", max-file: "10" } }
    stop_grace_period: 15s
    networks: [frontend, backend]

  database:
    image: postgres:17-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${DB_NAME}
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_INITDB_ARGS: "--data-checksums"
    volumes:
      - db-data:/var/lib/postgresql/data
      - db-backups:/backups
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER} -d ${DB_NAME}"]
      interval: 10s
      timeout: 5s
      start_period: 30s
      retries: 5
    deploy:
      resources:
        limits: { cpus: "2.0", memory: 1G }
        reservations: { cpus: "0.5", memory: 512M }
    command: >
      postgres
      -c shared_buffers=256MB
      -c effective_cache_size=768MB
      -c max_connections=100
      -c log_min_duration_statement=1000
    shm_size: 256M
    stop_grace_period: 60s
    networks: [backend]

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    read_only: true
    tmpfs: [/tmp:size=16M]
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru --loglevel warning
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 320M }
        reservations: { cpus: "0.25", memory: 128M }
    stop_grace_period: 15s
    networks: [backend]

  rabbitmq:
    image: rabbitmq:3.13-alpine
    restart: unless-stopped
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS}
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 0.4
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 30s
      timeout: 10s
      start_period: 30s
      retries: 5
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 512M }
        reservations: { cpus: "0.25", memory: 256M }
    stop_grace_period: 30s
    networks: [backend]

  worker:
    image: ${REGISTRY:-registry.example.com}/app:${APP_VERSION:-latest}
    restart: unless-stopped
    read_only: true
    tmpfs: [/tmp:size=64M]
    environment:
      APP_ENV: prod
      APP_DEBUG: "0"
      DATABASE_URL: "postgresql://${DB_USER}:${DB_PASSWORD}@database:5432/${DB_NAME}?serverVersion=17"
      REDIS_URL: "redis://redis:6379"
      RABBITMQ_URL: "amqp://${RABBITMQ_USER}:${RABBITMQ_PASS}@rabbitmq:5672"
    command: ["php", "bin/console", "messenger:consume", "async", "--time-limit=3600", "--memory-limit=256M"]
    depends_on:
      database: { condition: service_healthy }
      rabbitmq: { condition: service_healthy }
    deploy:
      resources:
        limits: { cpus: "1.0", memory: 384M }
      replicas: 2
    logging: { driver: json-file, options: { max-size: "10m", max-file: "5" } }
    stop_grace_period: 60s
    networks: [backend]

volumes:
  db-data:
  db-backups:
  redis-data:
  rabbitmq-data:
  ssl-certs:
  static-files:

networks:
  frontend:
    driver: bridge
    name: app-frontend
  backend:
    driver: bridge
    internal: true
    name: app-backend
```

## Network Segmentation

```
Internet → [frontend] → nginx:80/443 → [backend (internal)] → php, database, redis, rabbitmq, worker
```

- **frontend:** Only Nginx exposed to internet
- **backend:** Internal network; database, Redis, RabbitMQ not accessible from outside

## Production Deployment Commands

```bash
# Deploy with specific version
APP_VERSION=v1.2.3 docker compose -f docker-compose.prod.yml up -d

# Rolling update (zero-downtime)
APP_VERSION=v1.2.4 docker compose -f docker-compose.prod.yml up -d --no-deps php worker

# Scale workers
docker compose -f docker-compose.prod.yml up -d --scale worker=4

# Database backup
docker compose -f docker-compose.prod.yml exec database \
    pg_dump -U app -d app --format=custom > backup.dump
```

## Security Checklist

- Read-only root filesystem on stateless services
- tmpfs for temporary file needs
- Network segmentation (frontend/backend)
- No management ports exposed (RabbitMQ management disabled)
- Resource limits prevent runaway processes
- Restart policies for fault tolerance
- Log rotation prevents disk exhaustion
- Graceful shutdown timeouts configured
- Database data checksums enabled

## Usage

Provide:
- Services required (database, cache, queue)
- Database type (PostgreSQL/MySQL)
- Resource constraints per service
- SSL certificate strategy

The generator will:
1. Create docker-compose.prod.yml with hardened services
2. Configure network segmentation
3. Set resource limits and restart policies
4. Include health checks, logging, and backup config
