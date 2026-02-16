---
name: acc-check-docker-php-config
description: Checks PHP configuration in Docker containers. Verifies php.ini settings, OPcache, PHP-FPM pool, and extension configuration for production.
---

# Docker PHP Configuration Checker

Analyze PHP configuration within Docker environments for production readiness.

## Configuration Checks

### 1. php.ini Production vs Development

```dockerfile
# BAD: Development config
RUN cp /usr/local/etc/php/php.ini-development /usr/local/etc/php/php.ini

# GOOD: Production config
RUN cp /usr/local/etc/php/php.ini-production /usr/local/etc/php/php.ini
```

### 2. OPcache Configuration

```ini
; GOOD: OPcache optimized for production
opcache.enable=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.save_comments=1
```

### 3. OPcache JIT (PHP 8.4+)

```ini
opcache.jit=1255
opcache.jit_buffer_size=128M
```

### 4. PHP-FPM Pool Configuration

```ini
; BAD: Static pm wastes memory; ondemand has fork overhead
pm = static
pm.max_children = 100

; GOOD: Dynamic pm with tuned values
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 20
pm.max_requests = 1000
```

### 5. Memory Limit

```ini
; BAD: Unlimited memory
memory_limit = -1

; GOOD: Appropriate for workload
memory_limit = 128M   ; web
memory_limit = 256M   ; workers
memory_limit = 512M   ; batch
```

### 6. Error Reporting

```ini
; BAD: Development error display
display_errors = On

; GOOD: Production settings
display_errors = Off
display_startup_errors = Off
log_errors = On
error_log = /proc/self/fd/2
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT
```

### 7. Session Handling

```ini
; BAD: File-based sessions (not scalable)
session.save_handler = files

; GOOD: External storage
session.save_handler = redis
session.save_path = "tcp://redis:6379"
```

### 8. Upload Limits

```ini
upload_max_filesize = 20M
post_max_size = 25M
max_file_uploads = 10
```

### 9. Timezone

```ini
date.timezone = UTC
```

### 10. Realpath Cache

```ini
; GOOD: Increased for Symfony/Laravel
realpath_cache_size = 4096K
realpath_cache_ttl = 600
```

## Grep Patterns

```bash
Grep: "php.ini-(production|development)" --glob "**/Dockerfile*"
Grep: "opcache\\." --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "^pm[. =]" --glob "**/*.conf"
Grep: "memory_limit" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "display_errors" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "session\\.save_handler" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "upload_max_filesize|post_max_size" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "date\\.timezone" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "realpath_cache" --glob "**/{Dockerfile*,*.ini,*.conf}"
Grep: "opcache\\.jit" --glob "**/{Dockerfile*,*.ini,*.conf}"
```

## Detection Sources

1. **Dockerfile RUN echo** — inline php.ini directives
2. **COPY'd php.ini** — full configuration replacement
3. **COPY'd conf.d/*.ini** — modular config files
4. **PHP-FPM pool config** — www.conf or custom pools
5. **Environment variables** — PHP_INI_SCAN_DIR overrides

## Severity Classification

| Check | Severity | Impact |
|-------|----------|--------|
| Using php.ini-development | Critical | Exposes errors, no OPcache |
| OPcache disabled | Critical | 3-10x slower responses |
| display_errors = On | Critical | Information disclosure |
| memory_limit = -1 | Major | OOM risk |
| validate_timestamps=1 | Major | FS checks per request |
| File-based sessions | Major | Not scalable, data loss |
| No timezone set | Minor | Inconsistent dates |
| Default upload limits | Minor | May block uploads |
| No realpath cache tuning | Minor | Extra FS lookups |
| JIT not configured | Minor | Missing perf gains |

## Output Format

```markdown
### PHP Config Issue: [Description]

**Severity:** Critical/Major/Minor
**Setting:** `directive = value`
**Location:** `Dockerfile:line` or `config-file:line`

**Current Value:**
```ini
directive = current_value
```

**Recommended Value:**
```ini
directive = recommended_value
```

**Rationale:**
[Why this setting matters for production]
```
