---
name: acc-docker-production-knowledge
description: Docker production knowledge base for PHP. Provides deployment patterns, health checks, graceful shutdown, logging, and monitoring.
---

# Docker Production Knowledge Base

Quick reference for production-ready Docker patterns in PHP applications.

## Production Image Requirements

```
+---------------------------------------------------------------------------+
|                   PRODUCTION IMAGE CHECKLIST                                |
+---------------------------------------------------------------------------+
|                                                                            |
|   Build                                                                    |
|   +--------------------------------------------------------------------+  |
|   | Multi-stage build       | Pinned versions      | BuildKit enabled  |  |
|   | .dockerignore present   | No dev dependencies  | Minimal layers    |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Runtime                                                                  |
|   +--------------------------------------------------------------------+  |
|   | Non-root user           | Health check defined | OPcache enabled   |  |
|   | Read-only filesystem    | Resource limits      | Graceful shutdown |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Observability                                                            |
|   +--------------------------------------------------------------------+  |
|   | Structured logging      | Metrics endpoint     | Tracing headers   |  |
|   | Health/readiness probes | Error tracking       | Performance APM   |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
+---------------------------------------------------------------------------+
```

## Health Check Patterns

### PHP-FPM Health Check Script

```dockerfile
# Install health check utility
COPY --from=renatomefi/php-fpm-healthcheck:latest \
    /usr/local/bin/php-fpm-healthcheck /usr/local/bin/php-fpm-healthcheck

HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=3 \
    CMD php-fpm-healthcheck || exit 1
```

### Custom Health Check Script

```bash
#!/bin/sh
# healthcheck.sh

# Check PHP-FPM is running
if ! kill -0 $(cat /var/run/php-fpm.pid 2>/dev/null) 2>/dev/null; then
    echo "PHP-FPM not running"
    exit 1
fi

# Check PHP-FPM responds
SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect 127.0.0.1:9000 > /dev/null 2>&1

if [ $? -ne 0 ]; then
    echo "PHP-FPM not responding"
    exit 1
fi

exit 0
```

### Docker Compose Health Checks

```yaml
services:
  php:
    healthcheck:
      test: ["CMD", "php-fpm-healthcheck"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 30s

  nginx:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 15s
      timeout: 5s
      retries: 3
    depends_on:
      php:
        condition: service_healthy

  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
```

## Graceful Shutdown

### PHP-FPM STOPSIGNAL

```dockerfile
# PHP-FPM graceful shutdown
STOPSIGNAL SIGQUIT
```

### Entrypoint with Trap

```bash
#!/bin/sh
# entrypoint.sh

# Trap SIGTERM/SIGQUIT for graceful shutdown
trap 'kill -SIGQUIT $PID; wait $PID' SIGTERM SIGQUIT

# Start PHP-FPM in background
php-fpm &
PID=$!

# Wait for PHP-FPM to finish
wait $PID
EXIT_STATUS=$?

exit $EXIT_STATUS
```

### Docker Compose Stop Configuration

```yaml
services:
  php:
    stop_signal: SIGQUIT
    stop_grace_period: 30s
```

## Logging Strategy

### Stdout/Stderr Pattern

```dockerfile
# Redirect PHP-FPM logs to stdout/stderr
RUN ln -sf /dev/stderr /var/log/php-fpm/error.log && \
    ln -sf /dev/stdout /var/log/php-fpm/access.log
```

### PHP Logging Configuration

```ini
; php.ini production logging
error_reporting = E_ALL
display_errors = Off
display_startup_errors = Off
log_errors = On
error_log = /dev/stderr
log_errors_max_len = 4096
```

### Structured Logging in Application

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Psr\Log\LoggerInterface;

final readonly class StructuredLogger
{
    public function __construct(
        private LoggerInterface $logger,
        private string $serviceName,
        private string $environment,
    ) {}

    public function log(string $level, string $message, array $context = []): void
    {
        $this->logger->log($level, $message, array_merge([
            'service' => $this->serviceName,
            'environment' => $this->environment,
            'timestamp' => (new \DateTimeImmutable())->format('c'),
            'trace_id' => $context['trace_id'] ?? null,
        ], $context));
    }
}
```

## OPcache Production Configuration

```ini
; opcache.ini - Production settings
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.fast_shutdown=1
opcache.jit=1255
opcache.jit_buffer_size=256M
opcache.preload=/var/www/html/config/preload.php
opcache.preload_user=app
```

### Preload Configuration

```php
<?php
// config/preload.php

declare(strict_types=1);

require __DIR__ . '/../vendor/autoload.php';

// Preload frequently used classes
$classesToPreload = [
    // Framework core
    '/var/www/html/vendor/symfony/http-kernel/HttpKernel.php',
    '/var/www/html/vendor/symfony/routing/Router.php',
    // Domain classes
    '/var/www/html/src/Domain/ValueObject/*.php',
    '/var/www/html/src/Domain/Entity/*.php',
];
```

## PHP-FPM Tuning

### Dynamic Pool (Recommended for Production)

```ini
; php-fpm.d/www.conf
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
ping.path = /ping
ping.response = pong

; Slow request logging
request_slowlog_timeout = 5s
slowlog = /dev/stderr

; Access log format
access.log = /dev/stdout
access.format = '{"time":"%{%Y-%m-%dT%H:%M:%S%z}T","method":"%m","uri":"%r","status":"%s","duration":"%d","memory":"%{mega}M","cpu":"%C%%"}'
```

### Calculating max_children

```
max_children = (Available RAM - OS/other services) / Average PHP process memory

Example:
  Container limit: 512MB
  OS overhead: ~50MB
  Average PHP process: ~30MB
  max_children = (512 - 50) / 30 = ~15
```

## Resource Limits

```yaml
services:
  php:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
      replicas: 3
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
```

## Update Strategies

| Strategy | Downtime | Risk | Use Case |
|----------|----------|------|----------|
| **Rolling** | None | Medium | Default choice |
| **Blue-Green** | None | Low | Critical services |
| **Canary** | None | Low | High-traffic services |
| **Recreate** | Yes | Low | Stateful services |

### Rolling Update Configuration

```yaml
services:
  php:
    deploy:
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
        monitor: 30s
        max_failure_ratio: 0.1
        order: start-first
      rollback_config:
        parallelism: 1
        delay: 5s
        order: stop-first
```

## Detection Patterns

```bash
# Check for production readiness
Grep: "HEALTHCHECK" --glob "**/Dockerfile*"
Grep: "STOPSIGNAL|stop_signal|stop_grace_period" --glob "**/Dockerfile*" --glob "**/docker-compose*.yml"
Grep: "validate_timestamps=0" --glob "**/opcache*.ini" --glob "**/php.ini"
Grep: "display_errors.*Off" --glob "**/php.ini"
Grep: "memory.*limit|cpus" --glob "**/docker-compose*.yml"

# Find missing production configurations
Grep: "display_errors.*On" --glob "**/php*.ini"
Grep: "xdebug" --glob "**/Dockerfile*" --glob "**/php*.ini"
```

## References

For detailed information, load these reference files:

- `references/production-configs.md` -- Production-ready configuration snippets
