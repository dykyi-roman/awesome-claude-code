# Entrypoint Patterns for PHP Frameworks

## Symfony Patterns

### Cache Clear and Warmup

```bash
# Clear and warmup cache for production
php bin/console cache:clear --env=prod --no-debug
php bin/console cache:warmup --env=prod --no-debug
```

### Database Migrations (Doctrine)

```bash
# Run pending migrations non-interactively
php bin/console doctrine:migrations:migrate --no-interaction --allow-no-migration

# Check migration status
php bin/console doctrine:migrations:status --no-interaction

# Validate schema
php bin/console doctrine:schema:validate --skip-sync
```

### Symfony Messenger Worker

```bash
# Consume from async transport with limits
php bin/console messenger:consume async \
    --memory-limit=128M \
    --time-limit=3600 \
    --limit=1000 \
    -vv

# Consume from multiple transports
php bin/console messenger:consume async priority high_priority \
    --memory-limit=256M \
    --time-limit=3600 \
    -vv

# Failed message retry
php bin/console messenger:failed:retry --force
```

### Symfony Scheduler

```bash
# Run scheduler (Symfony 6.3+)
php bin/console messenger:consume scheduler_default

# Custom cron command
php bin/console app:scheduler:run
```

### Symfony Assets

```bash
# Install assets for production
php bin/console assets:install public --symlink --env=prod
```

## Laravel Patterns

### Configuration Cache

```bash
# Cache configuration for production
php artisan config:cache
php artisan route:cache
php artisan view:cache
php artisan event:cache

# Clear all caches
php artisan optimize:clear
```

### Database Migrations (Eloquent)

```bash
# Run pending migrations
php artisan migrate --force --no-interaction

# Check migration status
php artisan migrate:status

# Seed database (if needed)
php artisan db:seed --force --no-interaction
```

### Laravel Queue Worker

```bash
# Start queue worker with limits
php artisan queue:work redis \
    --memory=128 \
    --timeout=60 \
    --tries=3 \
    --sleep=3 \
    --max-jobs=1000 \
    --max-time=3600

# Process specific queues
php artisan queue:work redis \
    --queue=high,default,low \
    --memory=256 \
    --timeout=120
```

### Laravel Scheduler

```bash
# Run scheduler via cron
* * * * * cd /app && php artisan schedule:run >> /dev/null 2>&1

# Run scheduler as daemon (Laravel 10+)
php artisan schedule:work
```

### Laravel Storage

```bash
# Create storage symlink
php artisan storage:link
```

## Common Patterns

### Opcache Preloading

```bash
# Symfony preload file
php bin/console cache:warmup --env=prod
# Preload file generated at var/cache/prod/App_KernelProdContainer.preload.php

# Laravel preload (if configured)
# Set opcache.preload in php.ini to bootstrap/preload.php
```

### Health Check Endpoint (in entrypoint)

```bash
# Wait for application to be ready after boot
wait_for_app_ready() {
    local max_attempts=30
    local attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -sf http://localhost/health > /dev/null 2>&1; then
            echo "[entrypoint] Application is ready"
            return 0
        fi
        attempt=$((attempt + 1))
        sleep 1
    done
    echo "[entrypoint] WARNING: Application not ready after ${max_attempts}s"
    return 1
}
```

### Environment-Specific Entrypoint Logic

```bash
case "${APP_ENV}" in
    prod|production)
        run_migrations
        warmup_cache
        ;;
    staging)
        run_migrations
        warmup_cache
        seed_test_data
        ;;
    dev|development|local)
        echo "[entrypoint] Development mode: skipping migrations and cache warmup"
        ;;
    *)
        echo "[entrypoint] Unknown APP_ENV: ${APP_ENV}"
        exit 1
        ;;
esac
```

### Graceful PHP-FPM Shutdown

```bash
# SIGQUIT: Graceful shutdown (finishes current requests)
# SIGTERM: Immediate termination
# SIGUSR2: Graceful reload (re-read config)

cleanup() {
    echo "[entrypoint] Sending SIGQUIT to PHP-FPM for graceful shutdown..."
    kill -SIGQUIT "${FPM_PID}" 2>/dev/null || true

    # Wait up to 30 seconds for graceful shutdown
    local timeout=30
    while [ $timeout -gt 0 ] && kill -0 "${FPM_PID}" 2>/dev/null; do
        sleep 1
        timeout=$((timeout - 1))
    done

    # Force kill if still running
    if kill -0 "${FPM_PID}" 2>/dev/null; then
        echo "[entrypoint] Force killing PHP-FPM after timeout"
        kill -SIGKILL "${FPM_PID}" 2>/dev/null || true
    fi
}
```
