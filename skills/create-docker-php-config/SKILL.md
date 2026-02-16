---
name: acc-create-docker-php-config
description: Generates PHP configuration files for Docker containers. Creates optimized php.ini, OPcache, and PHP-FPM pool configurations.
---

# Docker PHP Configuration Generator

Generates optimized PHP configuration files for Docker containers: `php.ini`, OPcache with JIT, and PHP-FPM pool configuration.

## Generated Files

```
docker/php/php.ini              # Production PHP configuration
docker/php/opcache.ini          # OPcache with JIT configuration
docker/php/php-fpm.d/www.conf   # PHP-FPM pool configuration
```

## Generation Instructions

1. **Determine workload type:** Web API (low memory, short execution), Background worker (higher memory, longer execution), CLI tools (max memory, no limit)
2. **Analyze needs:** File uploads, session handling, serialization, timezone
3. **Generate:** php.ini tuned for workload, OPcache with JIT, PHP-FPM pool matched to resources

## Production php.ini

```ini
; php.ini — Production Configuration for Docker
display_errors = Off
display_startup_errors = Off
error_reporting = E_ALL & ~E_DEPRECATED & ~E_STRICT
log_errors = On
error_log = /proc/self/fd/2

memory_limit = 256M
max_execution_time = 30
max_input_time = 60
max_input_vars = 5000

file_uploads = On
upload_max_filesize = 10M
post_max_size = 20M
upload_tmp_dir = /tmp

expose_php = Off
allow_url_fopen = On
allow_url_include = Off
disable_functions = exec,passthru,shell_exec,system,proc_open,popen
open_basedir = /app:/tmp:/proc/self/fd

session.use_strict_mode = 1
session.use_only_cookies = 1
session.cookie_httponly = 1
session.cookie_secure = 1
session.cookie_samesite = Lax
session.sid_length = 48

date.timezone = UTC
default_charset = UTF-8
realpath_cache_size = 4096K
realpath_cache_ttl = 600
output_buffering = 4096
serialize_precision = -1
zend.detect_unicode = Off
zend.assertions = -1
```

## OPcache Production Configuration

```ini
; opcache.ini — Production OPcache + JIT for PHP 8.4
opcache.enable = 1
opcache.enable_cli = 1
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 32
opcache.max_accelerated_files = 30000
opcache.validate_timestamps = 0
opcache.fast_shutdown = 1
opcache.save_comments = 1

; JIT: 1255 = tracing JIT (CRTO format)
; C(0-1): CPU optimizations, R(0-5): registers, T(0-5): trigger, O(0-1): optimization
opcache.jit = 1255
opcache.jit_buffer_size = 256M
opcache.jit_debug = 0

; Preloading — uncomment and configure
; opcache.preload = /app/config/preload.php
; opcache.preload_user = app

opcache.log_verbosity_level = 1
opcache.error_log = /proc/self/fd/2
```

## PHP-FPM Pool Configuration

```ini
; www.conf — PHP-FPM Pool for Docker
[www]
user = app
group = app
listen = 0.0.0.0:9000
listen.backlog = 511

; pm.max_children = (Container RAM - overhead) / avg process size (~35MB)
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 20
pm.max_requests = 1000
pm.process_idle_timeout = 10s

pm.status_path = /status
ping.path = /ping
ping.response = pong

request_terminate_timeout = 60s
request_slowlog_timeout = 5s
slowlog = /proc/self/fd/2

access.log = /proc/self/fd/2
access.format = "%R - %u %t \"%m %r%Q%q\" %s %f %{mili}dms %{kilo}Mkb %C%%"
catch_workers_output = yes
decorate_workers_output = no

security.limit_extensions = .php
clear_env = yes
```

## Workload-Specific Overrides

### Web API (High Concurrency)

```ini
memory_limit = 128M
max_execution_time = 15
pm = dynamic
pm.max_children = 80
pm.start_servers = 20
pm.max_requests = 2000
request_terminate_timeout = 15s
```

### Background Worker (Long-Running)

```ini
memory_limit = 512M
max_execution_time = 0
opcache.validate_timestamps = 1
opcache.revalidate_freq = 60
pm = static
pm.max_children = 4
pm.max_requests = 500
request_terminate_timeout = 3600s
```

### CLI Tools (Batch Processing)

```ini
memory_limit = 1G
max_execution_time = 0
opcache.enable_cli = 1
opcache.validate_timestamps = 1
opcache.jit_buffer_size = 512M
```

## Docker Integration

```dockerfile
COPY docker/php/php.ini /usr/local/etc/php/php.ini
COPY docker/php/opcache.ini /usr/local/etc/php/conf.d/opcache.ini
COPY docker/php/php-fpm.d/www.conf /usr/local/etc/php-fpm.d/www.conf
```

## PHP-FPM Children Calculator

```
pm.max_children = (Container RAM - overhead) / Average Process Size

256 MB container → max_children = (256-64)/35  = ~5
512 MB container → max_children = (512-64)/35  = ~12
1 GB container   → max_children = (1024-128)/40 = ~22
2 GB container   → max_children = (2048-128)/40 = ~48
```

## Verification Commands

```bash
docker exec php php -i | grep "Loaded Configuration"
docker exec php php -r "var_dump(opcache_get_status()['jit']);"
docker exec php php-fpm -t
curl http://localhost/status?json
```

## Configuration Details

See `references/php-config-explained.md` for detailed explanation of each setting with impact and recommended values.

## Usage

Provide:
- Workload type (web API / background worker / CLI)
- Container memory limit
- Expected concurrent requests
- Framework (Symfony/Laravel/none)
- Preload file path (optional)

The generator will:
1. Create php.ini optimized for workload
2. Configure OPcache with JIT
3. Generate PHP-FPM pool with calculated children
4. Tune all settings for container environment
