---
name: acc-analyze-docker-runtime-errors
description: Analyzes Docker runtime errors for PHP containers. Identifies 502 Bad Gateway, OOM kills, connection refused, and permission issues.
---

# Docker Runtime Error Analysis

Analyze running PHP containers for runtime failures and provide targeted diagnosis and fixes.

## Runtime Error Categories

| Error | Symptom | Root Cause |
|-------|---------|------------|
| 502 Bad Gateway | Nginx returns 502 | PHP-FPM not running or crashed |
| OOM Killed | Container restarts | memory_limit or container limit exceeded |
| Connection refused | Service unreachable | Container not ready or wrong network |
| Permission denied | File operation fails | UID/GID mismatch or read-only fs |
| Segmentation fault | Process crashes | Extension bug or memory corruption |
| Slow requests | Timeouts, 504 errors | PHP-FPM pool exhaustion |

## Detection Patterns

### 1. 502 Bad Gateway (PHP-FPM Not Running)

```yaml
# FIX: Add healthcheck and proper depends_on
services:
  php-fpm:
    healthcheck:
      test: ["CMD-SHELL", "php-fpm-healthcheck || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
  nginx:
    depends_on:
      php-fpm:
        condition: service_healthy
```

### 2. OOM Killed

```ini
; php.ini -- match memory_limit to container limit
; Container limit 256MB -> PHP memory_limit should be lower
memory_limit = 128M
```

```yaml
# docker-compose.yml memory constraints
services:
  php-fpm:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 3. Connection Refused

```yaml
# FIX: Proper service dependencies and networking
services:
  php-fpm:
    depends_on:
      redis: { condition: service_healthy }
      database: { condition: service_healthy }
    networks: [app-network]
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
    networks: [app-network]
  database:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
    networks: [app-network]
networks:
  app-network:
    driver: bridge
```

### 4. Permission Denied (File Ownership)

```dockerfile
# FIX: Set correct ownership in Dockerfile
RUN mkdir -p /var/www/var/cache /var/www/var/log \
    && chown -R www-data:www-data /var/www/var
COPY --chown=www-data:www-data . /var/www
USER www-data
```

### 5. PHP-FPM Pool Exhaustion

```ini
; Sizing formula: max_children = (available_memory - overhead) / avg_process_memory
; Example: (512MB - 64MB) / 32MB = ~14
[www]
pm = dynamic
pm.max_children = 14
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 6
pm.max_requests = 500
```

### 6. Segmentation Fault

```ini
; Mitigation: disable problematic extensions one by one
; Common cause: OPcache + Xdebug conflict
opcache.enable=0  ; Test if OPcache causes segfault
opcache.fast_shutdown=0
```

## Grep Patterns

```bash
# Find PHP-FPM configuration
Grep: "pm\.(max_children|start_servers|max_requests)" --glob "**/www.conf" --glob "**/php-fpm*.conf"

# Find memory_limit settings
Grep: "memory_limit" --glob "**/php.ini" --glob "**/*.ini"

# Find healthcheck definitions
Grep: "healthcheck" --glob "**/docker-compose*.yml"

# Find depends_on without condition
Grep: "depends_on:" --glob "**/docker-compose*.yml"

# Find error logging configuration
Grep: "error_log|log_errors" --glob "**/php.ini" --glob "**/*.ini"
```

## PHP-FPM Specific Diagnostics

| Log Pattern | Diagnosis | Fix |
|-------------|-----------|-----|
| `server reached pm.max_children` | Pool exhaustion | Increase max_children or optimize code |
| `child exited on signal 11` | Segmentation fault | Check extensions, disable OPcache |
| `child exited with code 255` | Fatal PHP error | Check error log for details |
| `execution timed out` | Slow script | Profile code, check DB queries |
| `unable to open primary script` | Wrong document root | Fix Nginx fastcgi_param SCRIPT_FILENAME |

## Severity Classification

| Pattern | Severity | Impact |
|---------|----------|--------|
| OOM Killed (recurring) | Critical | Service unavailable, data loss risk |
| PHP-FPM pool exhaustion | Critical | All requests blocked |
| Segmentation fault | Critical | Process crash, intermittent failures |
| 502 Bad Gateway | Major | Service unavailable |
| Connection refused | Major | Dependent service failures |
| Permission denied (runtime) | Major | Feature degradation |
| Slow requests (< threshold) | Minor | User experience impact |

## Output Format

```markdown
### Runtime Error: [Category]

**Severity:** Critical/Major/Minor
**Container:** `<service_name>`
**Log Pattern:** `<error message from logs>`

**Diagnosis:**
[Root cause analysis with evidence from logs]

**Steps to Verify:**
1. [Command to confirm the issue]
2. [Command to check related state]

**Fix:**
```yaml
# docker-compose.yml or config change
```

**Monitoring:**
[How to detect this issue early in production]
```
