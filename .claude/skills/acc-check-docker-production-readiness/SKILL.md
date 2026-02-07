---
name: acc-check-docker-production-readiness
description: Checks Docker production readiness for PHP applications. Verifies health checks, graceful shutdown, logging, monitoring, and resource limits.
---

# Docker Production Readiness Checker

Evaluate Docker configuration for production deployment of PHP applications using a scored checklist.

## Production Readiness Checklist

### 1. HEALTHCHECK Instruction (10 pts)

```dockerfile
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD php-fpm-healthcheck || exit 1
```

### 2. STOPSIGNAL for Graceful Shutdown (10 pts)

```dockerfile
# PHP-FPM needs SIGQUIT for graceful stop
STOPSIGNAL SIGQUIT
```

### 3. Logging to stdout/stderr (10 pts)

```dockerfile
# BAD: Logging to files
RUN echo "error_log = /var/log/php/error.log" >> php.ini

# GOOD: Logging to stderr for Docker log driver
RUN echo "error_log = /proc/self/fd/2" >> php.ini
```

### 4. OPcache with validate_timestamps=0 (10 pts)

```dockerfile
RUN echo "opcache.validate_timestamps=0" >> /usr/local/etc/php/conf.d/opcache.ini && \
    echo "opcache.enable=1" >> /usr/local/etc/php/conf.d/opcache.ini && \
    echo "opcache.memory_consumption=256" >> /usr/local/etc/php/conf.d/opcache.ini
```

### 5. PHP-FPM Dynamic pm Mode (10 pts)

```ini
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 20
pm.max_requests = 1000
```

### 6. Non-Root User (10 pts)

```dockerfile
RUN groupadd -r appuser && useradd -r -g appuser appuser
COPY --chown=appuser:appuser . /var/www/html
USER appuser
```

### 7. Resource Limits in Compose (10 pts)

```yaml
services:
  php-fpm:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
```

### 8. Restart Policy (5 pts)

```yaml
services:
  app:
    restart: unless-stopped
```

### 9. .dockerignore Present (5 pts)

```
.git
.env
node_modules
vendor
tests
docs
```

### 10. No Dev Dependencies (10 pts)

```dockerfile
RUN composer install --no-dev --optimize-autoloader --classmap-authoritative
```

### 11. Signal Handling Entrypoint (10 pts)

```dockerfile
COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["php-fpm"]
```

## Grep Patterns

```bash
Grep: "HEALTHCHECK" --glob "**/Dockerfile*"
Grep: "STOPSIGNAL" --glob "**/Dockerfile*"
Grep: "error_log.*=.*/var/log" --glob "**/Dockerfile*"
Grep: "validate_timestamps" --glob "**/Dockerfile*"
Grep: "^USER" --glob "**/Dockerfile*"
Grep: "composer install" --glob "**/Dockerfile*"
Grep: "^(CMD|ENTRYPOINT)" --glob "**/Dockerfile*"
Glob: "**/.dockerignore"
```

## Score Calculation

| Check | Points | Weight |
|-------|--------|--------|
| HEALTHCHECK present | 10 | Required |
| STOPSIGNAL SIGQUIT | 10 | Required |
| Logging to stdout/stderr | 10 | Required |
| OPcache validate_timestamps=0 | 10 | Required |
| PHP-FPM dynamic pm | 10 | Recommended |
| Non-root USER | 10 | Required |
| Resource limits | 10 | Recommended |
| Restart policy | 5 | Recommended |
| .dockerignore present | 5 | Recommended |
| No dev dependencies | 10 | Required |
| Signal handling entrypoint | 10 | Recommended |
| **Total** | **100** | |

**Rating:** 90-100 Production Ready | 70-89 Needs Improvement | Below 70 Not Ready

## Output Format

```markdown
## Production Readiness Report

**Score:** X/100 — [Production Ready / Needs Improvement / Not Ready]

| # | Check | Status | Points |
|---|-------|--------|--------|
| 1 | HEALTHCHECK | Pass/Fail | 10/0 |

### Findings

#### [Check Name] — FAIL
**File:** `Dockerfile:line`
**Issue:** [What is missing]
**Fix:** [How to fix it]

### Recommendations
- [Prioritized list of improvements]
```
