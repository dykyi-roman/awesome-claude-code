---
name: acc-create-docker-entrypoint
description: Generates Docker entrypoint scripts for PHP containers. Creates startup scripts with signal handling, migrations, and cache warmup.
---

# Docker Entrypoint Generator

Generates entrypoint scripts for PHP Docker containers with signal handling, service readiness, and application bootstrap.

## Generated Files

```
docker/
  entrypoint.sh             # Main web container entrypoint
  entrypoint-worker.sh      # Queue worker entrypoint
  entrypoint-scheduler.sh   # Cron scheduler entrypoint
  wait-for-it.sh            # Service readiness checker
```

## Web Container Entrypoint (PHP-FPM)

```bash
#!/bin/bash
# entrypoint.sh — Web container entrypoint for PHP-FPM
set -eo pipefail

# ─── Signal Handling ────────────────────────────────────────
cleanup() {
    echo "[entrypoint] Received shutdown signal, stopping gracefully..."
    if [ -n "${FPM_PID}" ]; then
        kill -SIGQUIT "${FPM_PID}" 2>/dev/null || true
        wait "${FPM_PID}" 2>/dev/null || true
    fi
    echo "[entrypoint] Shutdown complete"
    exit 0
}

trap cleanup SIGTERM SIGQUIT SIGINT

# ─── Environment Validation ────────────────────────────────
validate_env() {
    local required_vars=("APP_ENV" "DATABASE_URL")
    local missing=()

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing+=("${var}")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        echo "[entrypoint] ERROR: Missing required environment variables: ${missing[*]}"
        exit 1
    fi

    echo "[entrypoint] Environment: ${APP_ENV}"
}

# ─── Wait for Dependencies ─────────────────────────────────
wait_for_services() {
    if [ -n "${DB_HOST}" ] && [ -n "${DB_PORT}" ]; then
        echo "[entrypoint] Waiting for database at ${DB_HOST}:${DB_PORT}..."
        /usr/local/bin/wait-for-it.sh "${DB_HOST}:${DB_PORT}" --timeout=60 --strict
    fi

    if [ -n "${REDIS_HOST}" ] && [ -n "${REDIS_PORT}" ]; then
        echo "[entrypoint] Waiting for Redis at ${REDIS_HOST}:${REDIS_PORT}..."
        /usr/local/bin/wait-for-it.sh "${REDIS_HOST}:${REDIS_PORT}" --timeout=30 --strict
    fi

    if [ -n "${RABBITMQ_HOST}" ] && [ -n "${RABBITMQ_PORT}" ]; then
        echo "[entrypoint] Waiting for RabbitMQ at ${RABBITMQ_HOST}:${RABBITMQ_PORT}..."
        /usr/local/bin/wait-for-it.sh "${RABBITMQ_HOST}:${RABBITMQ_PORT}" --timeout=60 --strict
    fi
}

# ─── Database Migrations ───────────────────────────────────
run_migrations() {
    if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
        echo "[entrypoint] Running database migrations..."
        # Framework-specific command (see references/entrypoint-patterns.md)
        php bin/console doctrine:migrations:migrate --no-interaction --allow-no-migration 2>&1 || {
            echo "[entrypoint] ERROR: Migration failed"
            exit 1
        }
        echo "[entrypoint] Migrations complete"
    fi
}

# ─── Cache Warmup ──────────────────────────────────────────
warmup_cache() {
    if [ "${APP_ENV}" = "prod" ]; then
        echo "[entrypoint] Warming up cache..."
        # Framework-specific command (see references/entrypoint-patterns.md)
        php bin/console cache:warmup --env=prod --no-debug 2>&1 || {
            echo "[entrypoint] WARNING: Cache warmup failed, continuing..."
        }
        echo "[entrypoint] Cache warmup complete"
    fi
}

# ─── Fix Permissions ───────────────────────────────────────
fix_permissions() {
    if [ -d "var" ]; then
        chown -R www-data:www-data var/ 2>/dev/null || true
    fi
    if [ -d "storage" ]; then
        chown -R www-data:www-data storage/ 2>/dev/null || true
    fi
}

# ─── Main Execution ────────────────────────────────────────
echo "[entrypoint] Starting PHP-FPM container..."

validate_env
wait_for_services
fix_permissions
run_migrations
warmup_cache

echo "[entrypoint] Launching PHP-FPM..."
exec php-fpm --nodaemonize &
FPM_PID=$!
wait "${FPM_PID}"
```

## Worker Container Entrypoint (Queue Consumer)

```bash
#!/bin/bash
# entrypoint-worker.sh — Queue worker entrypoint
set -eo pipefail

WORKER_PID=""

cleanup() {
    echo "[worker] Received shutdown signal, draining worker..."
    if [ -n "${WORKER_PID}" ]; then
        kill -SIGTERM "${WORKER_PID}" 2>/dev/null || true
        wait "${WORKER_PID}" 2>/dev/null || true
    fi
    echo "[worker] Worker stopped gracefully"
    exit 0
}

trap cleanup SIGTERM SIGQUIT SIGINT

# Wait for dependencies
if [ -n "${DB_HOST}" ] && [ -n "${DB_PORT}" ]; then
    /usr/local/bin/wait-for-it.sh "${DB_HOST}:${DB_PORT}" --timeout=60 --strict
fi
if [ -n "${RABBITMQ_HOST}" ] && [ -n "${RABBITMQ_PORT}" ]; then
    /usr/local/bin/wait-for-it.sh "${RABBITMQ_HOST}:${RABBITMQ_PORT}" --timeout=60 --strict
fi

echo "[worker] Starting queue worker..."

WORKER_MEMORY_LIMIT="${WORKER_MEMORY_LIMIT:-128}"
WORKER_TIMEOUT="${WORKER_TIMEOUT:-60}"
WORKER_TRIES="${WORKER_TRIES:-3}"
WORKER_SLEEP="${WORKER_SLEEP:-3}"

# Framework-specific command (see references/entrypoint-patterns.md)
exec php bin/console messenger:consume async \
    --memory-limit="${WORKER_MEMORY_LIMIT}M" \
    --time-limit=3600 \
    --limit=1000 \
    -vv &
WORKER_PID=$!
wait "${WORKER_PID}"
```

## Scheduler Container Entrypoint (Cron)

```bash
#!/bin/bash
# entrypoint-scheduler.sh — Cron scheduler entrypoint
set -eo pipefail

cleanup() {
    echo "[scheduler] Shutting down cron..."
    if [ -n "${CRON_PID}" ]; then
        kill -SIGTERM "${CRON_PID}" 2>/dev/null || true
    fi
    exit 0
}

trap cleanup SIGTERM SIGQUIT SIGINT

# Wait for dependencies
if [ -n "${DB_HOST}" ] && [ -n "${DB_PORT}" ]; then
    /usr/local/bin/wait-for-it.sh "${DB_HOST}:${DB_PORT}" --timeout=60 --strict
fi

# Install crontab
echo "[scheduler] Installing crontab..."
CRON_SCHEDULE="${CRON_SCHEDULE:-* * * * *}"

# Framework-specific (see references/entrypoint-patterns.md)
echo "${CRON_SCHEDULE} cd /app && php bin/console app:scheduler:run >> /var/log/cron.log 2>&1" \
    | crontab -

# Start cron in foreground
echo "[scheduler] Starting cron daemon..."
exec crond -f -l 2 &
CRON_PID=$!
wait "${CRON_PID}"
```

## Wait-for-it Script

```bash
#!/bin/bash
# wait-for-it.sh — Waits for a TCP host:port to become available
set -eo pipefail

TIMEOUT=30
STRICT=0
HOST=""
PORT=""

usage() {
    echo "Usage: wait-for-it.sh host:port [--timeout=N] [--strict]"
    exit 1
}

for arg in "$@"; do
    case "${arg}" in
        *:*)
            HOST="${arg%%:*}"
            PORT="${arg##*:}"
            ;;
        --timeout=*)
            TIMEOUT="${arg#*=}"
            ;;
        --strict)
            STRICT=1
            ;;
    esac
done

[ -z "${HOST}" ] || [ -z "${PORT}" ] && usage

echo "Waiting for ${HOST}:${PORT} (timeout: ${TIMEOUT}s)..."

START_TIME=$(date +%s)
while ! nc -z "${HOST}" "${PORT}" 2>/dev/null; do
    ELAPSED=$(( $(date +%s) - START_TIME ))
    if [ "${ELAPSED}" -ge "${TIMEOUT}" ]; then
        echo "ERROR: Timeout waiting for ${HOST}:${PORT} after ${TIMEOUT}s"
        [ "${STRICT}" -eq 1 ] && exit 1
        break
    fi
    sleep 1
done

echo "${HOST}:${PORT} is available"
exit 0
```

## Dockerfile Integration

```dockerfile
# Copy entrypoint scripts
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY docker/entrypoint-worker.sh /usr/local/bin/entrypoint-worker.sh
COPY docker/entrypoint-scheduler.sh /usr/local/bin/entrypoint-scheduler.sh
COPY docker/wait-for-it.sh /usr/local/bin/wait-for-it.sh

RUN chmod +x /usr/local/bin/entrypoint.sh \
    /usr/local/bin/entrypoint-worker.sh \
    /usr/local/bin/entrypoint-scheduler.sh \
    /usr/local/bin/wait-for-it.sh

# Install netcat for wait-for-it
RUN apk add --no-cache netcat-openbsd

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["php-fpm"]
```

## Docker Compose Service Definitions

```yaml
services:
  web:
    build: .
    entrypoint: /usr/local/bin/entrypoint.sh
    environment:
      RUN_MIGRATIONS: "true"

  worker:
    build: .
    entrypoint: /usr/local/bin/entrypoint-worker.sh
    deploy:
      replicas: 2

  scheduler:
    build: .
    entrypoint: /usr/local/bin/entrypoint-scheduler.sh
```

## Generation Instructions

1. **Identify container roles:** web (PHP-FPM), worker (queue), scheduler (cron)
2. **Detect framework:** Symfony or Laravel for correct CLI commands
3. **List dependencies:** database, cache, message broker
4. **Generate entrypoint scripts** with signal handling and readiness checks
5. **Add Dockerfile COPY/RUN** for entrypoint installation

See `references/entrypoint-patterns.md` for Symfony and Laravel specifics.
