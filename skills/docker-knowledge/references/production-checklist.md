# Production Readiness Checklist

Comprehensive checklist for deploying PHP Docker containers to production.

## Image Optimization

### Size Reduction Checklist

| Check | Status | Command/Notes |
|-------|--------|---------------|
| Multi-stage build | Required | Separate build and runtime stages |
| Alpine base | Recommended | `php:8.4-fpm-alpine` (~50MB vs ~150MB) |
| Build deps removed | Required | `apk del .build-deps` after ext install |
| No dev packages | Required | `composer install --no-dev` |
| No debug extensions | Required | No xdebug, phpdbg in production |
| Minimal layers | Recommended | Combine RUN instructions |
| `.dockerignore` present | Required | Exclude `.git`, `tests/`, `node_modules/` |
| No unnecessary files | Required | No docs, IDE configs, test fixtures |

### .dockerignore Template

```
.git
.github
.idea
.vscode
node_modules
tests
docs
*.md
docker-compose*.yml
Makefile
.env*
!.env.example
phpunit.xml*
phpstan.neon*
psalm.xml*
.php-cs-fixer.php
```

### Layer Optimization

```dockerfile
# Bad: 3 layers, build deps remain
RUN apk add --no-cache libzip-dev icu-dev $PHPIZE_DEPS
RUN docker-php-ext-install zip intl pdo_mysql opcache
RUN pecl install redis && docker-php-ext-enable redis

# Good: 1 layer, build deps cleaned
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS libzip-dev icu-dev \
    && apk add --no-cache libzip icu-libs \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && pecl install redis && docker-php-ext-enable redis \
    && apk del .build-deps \
    && rm -rf /tmp/pear
```

### Tag Strategy

```bash
# Production tags — always specific
myapp:1.2.3              # Semantic version
myapp:1.2.3-abc1234      # Version + commit SHA
myapp:2024-01-15-abc1234 # Date + commit SHA

# Never use in production
myapp:latest             # Unpredictable
myapp:dev                # Wrong environment
```

## Runtime Configuration

### OPcache (Production)

```ini
; docker/php/conf.d/opcache.ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.jit=1255
opcache.jit_buffer_size=256M
```

| Setting | Production | Development |
|---------|-----------|-------------|
| `validate_timestamps` | 0 (disabled) | 1 (enabled) |
| `memory_consumption` | 256 | 128 |
| `max_accelerated_files` | 20000 | 10000 |
| `jit` | 1255 | 0 (disabled) |
| `jit_buffer_size` | 256M | 0 |

### PHP-FPM Tuning

```ini
; docker/php/php-fpm.d/www.conf
[www]
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 20
pm.max_requests = 1000
pm.process_idle_timeout = 10s

; Status page for monitoring
pm.status_path = /fpm-status
ping.path = /fpm-ping
ping.response = pong

; Slow log for debugging
slowlog = /proc/self/fd/2
request_slowlog_timeout = 5s

; Request limits
request_terminate_timeout = 60s
```

### Calculating max_children

```
Formula: max_children = Available Memory / Average Process Memory

Example:
  Container memory limit: 512MB
  Average PHP-FPM worker: 40MB
  System overhead: ~50MB
  max_children = (512 - 50) / 40 = ~11

Conservative settings:
  512MB container → max_children = 10
  1GB container   → max_children = 25
  2GB container   → max_children = 50
```

### PHP Configuration (Production)

```ini
; docker/php/php.ini
display_errors = Off
display_startup_errors = Off
error_reporting = E_ALL
log_errors = On
error_log = /proc/self/fd/2

memory_limit = 256M
max_execution_time = 30
max_input_time = 60
post_max_size = 32M
upload_max_filesize = 16M
max_file_uploads = 20

expose_php = Off
session.cookie_httponly = On
session.cookie_secure = On
session.cookie_samesite = Strict
session.use_strict_mode = On

realpath_cache_size = 4096K
realpath_cache_ttl = 600
```

## Logging

### stdout/stderr Pattern

```dockerfile
# PHP-FPM logs to stderr (Docker captures automatically)
# No log files inside container — everything to stdout/stderr
```

```ini
; php-fpm.conf
[global]
error_log = /proc/self/fd/2
log_level = warning

[www]
access.log = /proc/self/fd/2
access.format = '{"time":"%{%Y-%m-%dT%H:%M:%S%z}T","method":"%m","uri":"%r","status":"%s","duration":"%d","memory":"%{mega}M"}'
```

### Structured Logging (JSON)

```php
// Application-level structured logging (PSR-3)
$logger->info('Order confirmed', [
    'order_id' => $orderId->toString(),
    'total' => $total->amount,
    'currency' => $total->currency,
    'customer_id' => $customerId->toString(),
]);
```

### Log Levels

| Level | Use In Production | Example |
|-------|------------------|---------|
| emergency | Yes | System unusable |
| alert | Yes | Immediate action required |
| critical | Yes | Component failure |
| error | Yes | Runtime errors |
| warning | Yes | Unusual conditions |
| notice | Selectively | Normal but significant |
| info | Selectively | Operational messages |
| debug | Never | Detailed debug info |

## Monitoring

### Health Check Endpoint

```php
// public/health.php or /health route
final readonly class HealthAction
{
    public function __invoke(): JsonResponse
    {
        $checks = [
            'database' => $this->checkDatabase(),
            'redis' => $this->checkRedis(),
            'disk' => $this->checkDisk(),
        ];

        $healthy = !in_array(false, $checks, true);

        return new JsonResponse(
            ['status' => $healthy ? 'healthy' : 'degraded', 'checks' => $checks],
            $healthy ? 200 : 503
        );
    }
}
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1
```

### Prometheus Metrics

```yaml
services:
  php-fpm:
    labels:
      prometheus.io/scrape: "true"
      prometheus.io/port: "9253"
      prometheus.io/path: "/metrics"

  php-fpm-exporter:
    image: hipages/php-fpm_exporter
    environment:
      PHP_FPM_SCRAPE_URI: "tcp://php-fpm:9000/fpm-status"
    ports:
      - "9253:9253"
```

## Graceful Shutdown

### SIGTERM Handling

```ini
; php-fpm.conf
[global]
; FPM will finish existing requests before stopping
process_control_timeout = 30

; Stop signal
daemonize = no
```

### Docker Stop Timeout

```yaml
services:
  php-fpm:
    stop_grace_period: 30s  # Wait for FPM to finish requests
    stop_signal: SIGQUIT    # Graceful shutdown for PHP-FPM
```

### PHP Worker Graceful Shutdown

```php
// Queue worker — handle SIGTERM
pcntl_async_signals(true);

$running = true;
pcntl_signal(SIGTERM, function () use (&$running) {
    $running = false;  // Finish current job, then exit
});

while ($running) {
    $job = $queue->pop();
    if ($job !== null) {
        $this->process($job);
    }
    usleep(100_000); // 100ms
}
```

## Resource Limits

### Docker Compose

```yaml
services:
  php-fpm:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M

  mysql:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "1.0"
          memory: 512M

  redis:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 256M
```

### Resource Guidelines

| Service | CPU Limit | Memory Limit | Notes |
|---------|----------|-------------|-------|
| PHP-FPM | 1-4 | 256M-1G | Scale by max_children |
| Nginx | 0.5-1 | 128M-256M | Lightweight |
| MySQL | 1-4 | 512M-4G | Scale with dataset |
| Redis | 0.5-1 | 128M-512M | Match maxmemory config |
| Workers | 0.5-2 | 256M-512M | Per job memory usage |

## Backup and Data Persistence

### Volume Backup Strategy

```bash
# MySQL backup (daily)
docker compose exec mysql mysqldump -u root -p${DB_ROOT_PASSWORD} app | gzip > backup_$(date +%Y%m%d).sql.gz

# Volume backup
docker run --rm \
    -v myapp_mysql-data:/source:ro \
    -v $(pwd)/backups:/backup \
    alpine tar czf /backup/mysql-data-$(date +%Y%m%d).tar.gz -C /source .
```

### Persistent Data Checklist

| Data | Strategy | Volume |
|------|----------|--------|
| Database | Named volume + daily backup | `mysql-data` |
| File uploads | Named volume + S3 sync | `uploads` |
| Redis (cache) | No backup needed | `redis-data` |
| Redis (sessions) | Optional backup | `redis-data` |
| Logs | Ship to external service | No volume |

## Rollback Strategy

### Image-Based Rollback

```bash
# Deploy new version
docker compose pull php-fpm
docker compose up -d php-fpm

# Rollback to previous version (tag pinned)
docker compose down php-fpm
# Update image tag in docker-compose.yml or .env
APP_VERSION=1.2.2  # Previous version
docker compose up -d php-fpm
```

### Blue-Green with Compose

```bash
# Blue is running
docker compose -p myapp-blue up -d

# Deploy green
docker compose -p myapp-green up -d

# Switch nginx upstream to green
# Test green

# Stop blue
docker compose -p myapp-blue down
```

### Rollback Checklist

| Step | Action | Verify |
|------|--------|--------|
| 1 | Identify failing version | Check logs, metrics |
| 2 | Pull previous image tag | `docker pull myapp:1.2.2` |
| 3 | Update service | `docker compose up -d` |
| 4 | Run migrations (if needed) | Check backward compat |
| 5 | Verify health checks | All services healthy |
| 6 | Monitor for 15 minutes | Check error rates |

## Detection Patterns

```bash
# Check for OPcache configuration
Grep: "opcache" --glob "docker/php/**/*.ini"

# Check for production PHP config
Grep: "display_errors.*Off" --glob "docker/php/**/*.ini"

# Check for health checks in Dockerfile
Grep: "HEALTHCHECK" --glob "Dockerfile*"

# Check for resource limits in compose
Grep: "limits:|memory:|cpus:" --glob "docker-compose*.yml"

# Check for graceful shutdown
Grep: "stop_grace_period|stop_signal" --glob "docker-compose*.yml"

# Check for proper logging
Grep: "/proc/self/fd" --glob "docker/php/**/*.conf" --glob "docker/php/**/*.ini"

# Warning: debug in production config
Grep: "display_errors.*On|xdebug" --glob "docker/php/prod/**"
```
