# PHP Configuration Explained

Detailed explanation of each PHP configuration setting, its impact, and recommended values.

## php.ini Settings

### Error Handling

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `display_errors` | Off | Security | Never show errors to users in production; prevents information leakage |
| `log_errors` | On | Debugging | Write errors to log for monitoring and debugging |
| `error_log` | /proc/self/fd/2 | Docker | Sends to stderr, captured by Docker log driver |
| `error_reporting` | E_ALL & ~E_DEPRECATED | Quality | Report all errors except deprecations in production |

### Resource Limits

| Setting | Web API | Worker | CLI | Explanation |
|---|---|---|---|---|
| `memory_limit` | 128M | 512M | 1G | Maximum memory per process; prevents runaway scripts |
| `max_execution_time` | 15-30 | 0 (unlimited) | 0 | Wall-clock timeout in seconds; 0 for long-running |
| `max_input_time` | 30-60 | -1 | -1 | Time to parse input data; -1 for unlimited |
| `max_input_vars` | 5000 | 1000 | 1000 | Maximum POST/GET variables; prevents hash collision DoS |

### File Uploads

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `upload_max_filesize` | 10M | Storage | Maximum single file upload size |
| `post_max_size` | 20M | Memory | Must be > upload_max_filesize; total POST body limit |
| `max_file_uploads` | 20 | Security | Maximum files in single request; prevents abuse |

### Security Settings

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `expose_php` | Off | Security | Hides PHP version from HTTP headers |
| `allow_url_include` | Off | Security | Prevents remote file inclusion attacks |
| `disable_functions` | exec,system,... | Security | Blocks dangerous functions; adjust per workload |
| `open_basedir` | /app:/tmp | Security | Restricts file access to specific directories |

### Session Security

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `session.use_strict_mode` | 1 | Security | Rejects uninitialized session IDs |
| `session.cookie_httponly` | 1 | Security | Prevents JavaScript access to session cookie |
| `session.cookie_secure` | 1 | Security | Session cookie only sent over HTTPS |
| `session.cookie_samesite` | Lax | Security | CSRF protection via SameSite attribute |
| `session.sid_length` | 48 | Security | Longer session IDs are harder to brute-force |

### Performance

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `realpath_cache_size` | 4096K | Performance | Cache for resolved file paths; reduces stat() calls |
| `realpath_cache_ttl` | 600 | Performance | Cache lifetime in seconds; 600 for production |
| `zend.detect_unicode` | Off | Performance | Skip BOM detection; saves CPU on every request |
| `zend.assertions` | -1 | Performance | Compile out assertions entirely in production |

## OPcache Settings

### Core Settings

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `opcache.enable` | 1 | Critical | Enables the bytecode cache; must be on in production |
| `opcache.enable_cli` | 1 | Performance | Enable for CLI workers consuming queues |
| `opcache.memory_consumption` | 256 | Memory | Shared memory in MB for cached scripts |
| `opcache.interned_strings_buffer` | 32 | Memory | MB for deduplicated strings across scripts |
| `opcache.max_accelerated_files` | 30000 | Coverage | Max cached files; use prime number >= number of PHP files |

### Validation

| Setting | Production | Development | Explanation |
|---|---|---|---|
| `opcache.validate_timestamps` | 0 | 1 | 0 = never check if file changed (fastest); 1 = check periodically |
| `opcache.revalidate_freq` | N/A | 0 | Seconds between checks; 0 = every request in dev |

### JIT Compiler

| Setting | Value | Impact | Explanation |
|---|---|---|---|
| `opcache.jit` | 1255 | Performance | Tracing JIT; best for most workloads |
| `opcache.jit_buffer_size` | 256M | Memory | Separate from opcache.memory_consumption |

**JIT Mode Explained (CRTO format):**
- `C` (0-1): CPU-specific optimizations. 1 = enable
- `R` (0-5): Register allocation. 2 = root trace, 5 = optimistic
- `T` (0-5): JIT trigger. 5 = use call counters and edge counters
- `O` (0-1): Optimization level. 5 = full optimization

Common values:
- `1255` — Tracing JIT, recommended for most apps
- `1205` — Function JIT, simpler, less memory
- `disable` — Turn off JIT entirely (development)

### Preloading

| Setting | Value | Explanation |
|---|---|---|
| `opcache.preload` | /app/config/preload.php | Script that loads frequently-used classes at startup |
| `opcache.preload_user` | app | Must match PHP-FPM user |

**Preload Benefits:**
- Classes loaded once at startup, shared across all requests
- Eliminates autoloader overhead for preloaded classes
- Typically 10-20% improvement for framework code

## PHP-FPM Pool Settings

### Process Manager Modes

| Mode | Best For | Behavior |
|---|---|---|
| `dynamic` | Most apps | Adjusts workers between min/max based on load |
| `static` | Predictable load | Fixed number of workers; no scaling overhead |
| `ondemand` | Low traffic | Creates workers only when requests arrive; higher latency |

### Process Sizing

| Setting | Formula | Explanation |
|---|---|---|
| `pm.max_children` | (RAM - overhead) / avg_process_size | Maximum concurrent PHP requests |
| `pm.start_servers` | max_children * 0.25 | Initial workers at startup |
| `pm.min_spare_servers` | max_children * 0.1 | Keep this many idle workers minimum |
| `pm.max_spare_servers` | max_children * 0.4 | Kill excess idle workers above this |
| `pm.max_requests` | 1000-5000 | Recycle workers to prevent memory leaks |

### Monitoring

| Setting | Value | Explanation |
|---|---|---|
| `pm.status_path` | /status | Exposes worker stats (protect with Nginx) |
| `ping.path` | /ping | Health check endpoint for orchestration |
| `request_slowlog_timeout` | 5s | Logs stack trace for slow requests |
| `slowlog` | /proc/self/fd/2 | Slow log destination |

### Access Log Format

```
access.format = "%R - %u %t \"%m %r%Q%q\" %s %f %{mili}dms %{kilo}Mkb %C%%"
```

| Token | Meaning |
|---|---|
| `%R` | Remote IP |
| `%u` | User |
| `%t` | Timestamp |
| `%m` | Method |
| `%r` | Request URI |
| `%Q%q` | Query string |
| `%s` | Status |
| `%f` | Script filename |
| `%{mili}d` | Duration in milliseconds |
| `%{kilo}M` | Peak memory in KB |
| `%C` | CPU usage percentage |

## Recommended Values by Container Size

### 256 MB Container (Minimal)

```ini
; php.ini
memory_limit = 64M

; opcache
opcache.memory_consumption = 64
opcache.interned_strings_buffer = 8
opcache.jit_buffer_size = 32M

; php-fpm
pm.max_children = 6
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 3
```

### 512 MB Container (Standard)

```ini
; php.ini
memory_limit = 128M

; opcache
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 16
opcache.jit_buffer_size = 128M

; php-fpm
pm.max_children = 12
pm.start_servers = 4
pm.min_spare_servers = 2
pm.max_spare_servers = 6
```

### 1 GB Container (Standard+)

```ini
; php.ini
memory_limit = 256M

; opcache
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 32
opcache.jit_buffer_size = 256M

; php-fpm
pm.max_children = 25
pm.start_servers = 8
pm.min_spare_servers = 4
pm.max_spare_servers = 12
```

### 2 GB Container (Large)

```ini
; php.ini
memory_limit = 256M

; opcache
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 32
opcache.jit_buffer_size = 256M

; php-fpm
pm.max_children = 50
pm.start_servers = 15
pm.min_spare_servers = 8
pm.max_spare_servers = 25
```
