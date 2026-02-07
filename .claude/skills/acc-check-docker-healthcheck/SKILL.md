---
name: acc-check-docker-healthcheck
description: Checks Docker health check configuration for PHP services. Verifies PHP-FPM, Nginx, and dependent service health checks.
---

# Docker Health Check Configuration Checker

Analyze Docker health check configuration for PHP stacks and dependent services.

## Health Check Patterns by Service

### 1. PHP-FPM

```dockerfile
# Using php-fpm-healthcheck script (recommended)
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD php-fpm-healthcheck || exit 1

# Using cgi-fcgi (requires libfcgi)
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD cgi-fcgi -bind -connect 127.0.0.1:9000 /ping || exit 1
```

```ini
; Required PHP-FPM pool config
ping.path = /ping
ping.response = pong
pm.status_path = /status
```

### 2. Nginx

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Or wget for minimal images
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --spider --quiet http://localhost/health || exit 1
```

### 3. MySQL

```yaml
services:
  mysql:
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### 4. PostgreSQL

```yaml
services:
  postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
```

### 5. Redis

```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
      start_period: 5s
```

### 6. RabbitMQ

```yaml
services:
  rabbitmq:
    healthcheck:
      test: ["CMD-SHELL", "rabbitmq-diagnostics check_running && rabbitmq-diagnostics check_local_alarms"]
      interval: 15s
      timeout: 10s
      retries: 5
      start_period: 30s
```

## Recommended Parameters

| Service | interval | timeout | start_period | retries |
|---------|----------|---------|--------------|---------|
| PHP-FPM | 10s | 3s | 10s | 3 |
| Nginx | 10s | 3s | 5s | 3 |
| MySQL | 10s | 5s | 30s | 5 |
| PostgreSQL | 10s | 5s | 30s | 5 |
| Redis | 10s | 3s | 5s | 3 |
| RabbitMQ | 15s | 10s | 30s | 5 |

## Improper Health Check Detection

```dockerfile
# BAD: Too frequent (overhead)
HEALTHCHECK --interval=1s --timeout=1s --retries=1 CMD curl localhost

# BAD: No start_period (fails during init)
HEALTHCHECK --interval=5s --timeout=3s --retries=3 CMD pg_isready

# BAD: Checking external dependency
HEALTHCHECK CMD curl -f https://api.external.com/health

# BAD: Too slow detection (interval*retries > 5min)
HEALTHCHECK --interval=60s --timeout=30s --retries=10 CMD curl localhost
```

## Grep Patterns

```bash
Grep: "HEALTHCHECK" --glob "**/Dockerfile*"
Grep: "healthcheck:" --glob "**/docker-compose*.yml"
Grep: "depends_on:" --glob "**/docker-compose*.yml"
Grep: "ping\\.path|pm\\.status_path" --glob "**/*.conf"
```

## Severity Classification

| Issue | Severity | Impact |
|-------|----------|--------|
| No health check for any service | Critical | No failure detection |
| PHP-FPM without health check | Critical | Dead workers undetected |
| Database without health check | Major | App starts before DB ready |
| No start_period for databases | Major | False unhealthy during init |
| Checking external dependency | Major | External outage cascades |
| depends_on without condition | Major | Startup race condition |
| Interval too low (< 5s) | Minor | Unnecessary overhead |
| Interval too high (> 60s) | Minor | Slow failure detection |
| timeout >= interval | Minor | Overlapping checks |

## Output Format

```markdown
### Health Check Issue: [Description]

**Severity:** Critical/Major/Minor
**Service:** [service name]
**File:** `docker-compose.yml:line` or `Dockerfile:line`

**Issue:**
[Description of missing or misconfigured health check]

**Recommended:**
```yaml
healthcheck:
  test: ["CMD-SHELL", "..."]
  interval: 10s
  timeout: 3s
  start_period: 10s
  retries: 3
```

**Parameters:**
| Param | Current | Recommended | Reason |
|-------|---------|-------------|--------|
| interval | N/A | 10s | Standard frequency |
| timeout | N/A | 3s | Fast failure detection |
| start_period | N/A | 10s | Allow initialization |
| retries | N/A | 3 | Prevent flapping |
```
