---
name: acc-optimize-docker-startup
description: Optimizes Docker container startup time for PHP applications. Reduces initialization overhead through preloading, caching, and entrypoint optimization.
---

# Docker Container Startup Optimization

Reduces cold start and initialization time for PHP applications in Docker containers.

## Startup Time Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│              TYPICAL PHP CONTAINER STARTUP TIMELINE              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Container create:  ██░░░░░░░░░░░░░░░░░░░░░░░░  0.5s  (3%)    │
│  Entrypoint script: ████████░░░░░░░░░░░░░░░░░░  3.0s  (20%)   │
│  Migrations check:  ██████░░░░░░░░░░░░░░░░░░░░  2.0s  (13%)   │
│  Cache warmup:      ████████████░░░░░░░░░░░░░░  4.0s  (27%)   │
│  OPcache preload:   ██████░░░░░░░░░░░░░░░░░░░░  2.0s  (13%)   │
│  PHP-FPM start:     ████░░░░░░░░░░░░░░░░░░░░░░  1.0s  (7%)    │
│  Health check pass: ██████░░░░░░░░░░░░░░░░░░░░  2.5s  (17%)   │
│                                                                 │
│  Total unoptimized: ████████████████████████████ ~15s           │
│  Target optimized:  ██████████░░░░░░░░░░░░░░░░  ~5s  (-67%)   │
└─────────────────────────────────────────────────────────────────┘
```

## OPcache Preloading for Startup

```ini
; Preload critical classes at PHP-FPM startup (not per-request)
opcache.preload = /app/config/preload.php
opcache.preload_user = www-data
```

### Preload Strategy

```php
<?php
// config/preload.php
// Preload hot-path classes to eliminate first-request compilation

$directories = [
    '/app/src/Domain/',
    '/app/src/Application/',
    '/app/vendor/symfony/http-kernel/',
    '/app/vendor/symfony/routing/',
    '/app/vendor/symfony/dependency-injection/',
    '/app/vendor/doctrine/orm/src/',
];

foreach ($directories as $dir) {
    if (!is_dir($dir)) continue;
    $iterator = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($iterator as $file) {
        if ($file->getExtension() === 'php') {
            opcache_compile_file($file->getRealPath());
        }
    }
}
```

**Impact:** Eliminates 200-500ms first-request compilation latency.

## Composer Autoloader Optimization

```dockerfile
# ❌ SLOW: PSR-4 autoloading (filesystem lookups per class)
RUN composer dump-autoload

# ✅ FAST: Classmap authoritative (single array lookup)
RUN composer dump-autoload --optimize --classmap-authoritative
```

| Mode | Startup | Runtime | Use Case |
|------|---------|---------|----------|
| Default (PSR-4) | Fast | Slow (file scan) | Development |
| --optimize | Medium | Fast (classmap + PSR-4 fallback) | Staging |
| --classmap-authoritative | Slow (once) | Fastest (classmap only) | Production |

**Impact:** Reduces autoload time by 60-80% on each request.

## Framework Cache Warmup

### Symfony

```dockerfile
# Warm up cache at build time (not at startup)
RUN php bin/console cache:warmup --env=prod --no-debug

# Pre-compile DI container, routes, templates
RUN php bin/console cache:clear --env=prod --no-debug \
    && php bin/console cache:warmup --env=prod --no-debug
```

### Laravel

```dockerfile
# Cache configuration, routes, and views at build time
RUN php artisan config:cache \
    && php artisan route:cache \
    && php artisan view:cache \
    && php artisan event:cache
```

| Command | What It Caches | Time Saved |
|---------|---------------|-----------|
| config:cache | All config files into single file | 50-100ms |
| route:cache | Route registrations | 100-300ms |
| view:cache | Blade template compilation | 50-200ms |
| event:cache | Event-listener mappings | 20-50ms |

**Impact:** Eliminates 300-600ms of startup/first-request overhead.

## Entrypoint Optimization

### Anti-Pattern: Sequential Blocking Entrypoint

```bash
#!/bin/bash
# ❌ SLOW: Everything runs sequentially, blocks startup

# Wait for database (blocks for 5-10s)
until mysql -h db -u root -p$PASS -e "SELECT 1" > /dev/null 2>&1; do
    sleep 1
done

# Run migrations (blocks for 2-5s)
php bin/console doctrine:migrations:migrate --no-interaction

# Clear and warm cache (blocks for 3-5s)
php bin/console cache:clear --env=prod
php bin/console cache:warmup --env=prod

# Start PHP-FPM
php-fpm
```

### Optimized: Parallel and Background Tasks

```bash
#!/bin/sh
# ✅ FAST: Parallel init, non-blocking tasks in background

set -e

# Run non-critical tasks in background
{
    # Wait for DB and run migrations (non-blocking)
    /app/bin/wait-for-it.sh db:3306 --timeout=30
    php bin/console doctrine:migrations:migrate --no-interaction 2>&1 | logger -t migrations
} &

# Cache should be warmed at build time, but verify
if [ ! -d "/app/var/cache/prod" ]; then
    php bin/console cache:warmup --env=prod --no-debug
fi

# Start PHP-FPM immediately
exec php-fpm
```

**Impact:** Reduces startup from 15s to 3-5s by parallelizing non-critical init.

### Wait-for-It Pattern

```bash
#!/bin/sh
# /app/bin/wait-for-it.sh - lightweight dependency check
HOST=$(echo "$1" | cut -d: -f1)
PORT=$(echo "$1" | cut -d: -f2)
TIMEOUT=${3:-30}

for i in $(seq 1 "$TIMEOUT"); do
    nc -z "$HOST" "$PORT" 2>/dev/null && exit 0
    sleep 1
done
echo "Timeout waiting for $HOST:$PORT" >&2
exit 1
```

## Health Check Configuration

### start_period Tuning

```yaml
services:
  php-fpm:
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 5s
      start_period: 15s
      retries: 3
```

| Parameter | Purpose | Recommendation |
|-----------|---------|---------------|
| start_period | Grace period before health checks count | Set to expected startup time |
| interval | Time between checks | 10-30s (lower = faster detection) |
| timeout | Max wait for check response | 3-5s |
| retries | Failures before unhealthy | 2-3 |

### Lightweight Health Check

```bash
#!/bin/sh
# /usr/local/bin/php-fpm-healthcheck
# Fast check: just verify PHP-FPM responds

# Option 1: TCP check (fastest, ~1ms)
nc -z 127.0.0.1 9000 2>/dev/null || exit 1

# Option 2: FPM ping (verifies PHP works, ~5ms)
SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect 127.0.0.1:9000 2>/dev/null | grep -q pong || exit 1
```

## Lazy Service Initialization

### Symfony Lazy Services

```yaml
# config/services.yaml
services:
    App\Infrastructure\Database\HeavyConnection:
        lazy: true  # Proxy created instantly, real init on first use

    App\Infrastructure\Cache\RedisAdapter:
        lazy: true  # Don't connect to Redis until actually needed
```

### Laravel Deferred Providers

```php
// Defer provider registration until service is actually needed
class HeavyServiceProvider extends ServiceProvider
{
    protected $defer = true;

    public function provides(): array
    {
        return [HeavyService::class];
    }
}
```

**Impact:** Reduces container bootstrap by 100-500ms per heavy service.

## Build-Time vs Runtime Init

| Task | Build Time | Runtime | Recommendation |
|------|-----------|---------|----------------|
| Composer install | Yes | No | Build only |
| Autoloader optimize | Yes | No | Build only |
| Config cache | Yes | No | Build only |
| Route cache | Yes | No | Build only |
| View cache | Yes | No | Build only |
| Migrations | No | Yes (background) | Background at startup |
| DB connection check | No | Yes (background) | Background at startup |
| Cache warmup | Yes | Verify only | Build, verify at startup |
| OPcache preload | No | Yes (automatic) | PHP-FPM handles it |

## Optimized Dockerfile Pattern

```dockerfile
FROM php:8.4-fpm-alpine AS production

# Install extensions and runtime deps
RUN apk add --no-cache libzip icu-libs

COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

WORKDIR /app

# Copy vendor (pre-built)
COPY --from=deps /app/vendor ./vendor

# Copy source
COPY . .

# BUILD-TIME: All cacheable operations
RUN composer dump-autoload --optimize --classmap-authoritative \
    && php bin/console cache:warmup --env=prod --no-debug

# Copy optimized entrypoint
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Health check
COPY docker/php-fpm-healthcheck /usr/local/bin/php-fpm-healthcheck
RUN chmod +x /usr/local/bin/php-fpm-healthcheck

HEALTHCHECK --interval=10s --timeout=5s --start_period=10s --retries=3 \
    CMD php-fpm-healthcheck

ENTRYPOINT ["entrypoint.sh"]
CMD ["php-fpm"]
```

## Before/After Startup Time Comparison

| Phase | Before | After | Technique |
|-------|--------|-------|-----------|
| Entrypoint script | 3.0s | 0.5s | Parallel, background tasks |
| Migration check | 2.0s | 0s (background) | Non-blocking |
| Cache warmup | 4.0s | 0.2s (verify only) | Build-time warmup |
| OPcache preload | 2.0s | 2.0s | Unavoidable, but worth it |
| PHP-FPM start | 1.0s | 1.0s | Minimal improvement |
| Health check pass | 2.5s | 1.0s | Lightweight check + start_period |
| **Total** | **~15s** | **~5s** | **-67%** |

## Generation Instructions

1. **Audit current startup:** Measure time from container start to first healthy response
2. **Move to build time:** Config cache, route cache, autoloader optimization
3. **Optimize entrypoint:** Parallelize, background non-critical tasks
4. **Configure preloading:** Preload domain and framework hot-path classes
5. **Tune health checks:** Set appropriate start_period and use lightweight checks
6. **Defer heavy services:** Use lazy proxies for services not needed immediately
7. **Measure improvement:** Compare container ready time before and after
