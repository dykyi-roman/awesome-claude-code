---
name: acc-optimize-docker-opcache
description: Optimizes OPcache configuration for PHP Docker containers. Configures memory, file limits, JIT, and validation for production and development.
---

# OPcache Configuration Optimization

Provides production and development OPcache tuning for PHP Docker containers, including JIT and preloading.

## OPcache Impact Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                  OPCACHE PERFORMANCE IMPACT                      │
├─────────────────────────────────────────────────────────────────┤
│  Without OPcache:                                               │
│  Request → Parse → Compile → Execute → Response      ~50ms     │
│  With OPcache:                                                  │
│  Request → Execute (cached bytecode) → Response      ~15ms     │
│  With OPcache + JIT:                                            │
│  Request → Execute (native code) → Response          ~10ms     │
│  With OPcache + JIT + Preload:                                  │
│  Request → Execute (preloaded) → Response             ~5ms     │
└─────────────────────────────────────────────────────────────────┘
```

## Production vs Development Settings

| Setting | Production | Development | Purpose |
|---------|-----------|-------------|---------|
| opcache.enable | 1 | 1 | Enable OPcache |
| opcache.enable_cli | 1 | 0 | Cache for CLI scripts |
| opcache.memory_consumption | 256 | 128 | Shared memory (MB) |
| opcache.interned_strings_buffer | 32 | 16 | Interned strings (MB) |
| opcache.max_accelerated_files | 20000 | 10000 | Max cached files |
| opcache.validate_timestamps | 0 | 1 | Check file changes |
| opcache.revalidate_freq | 0 | 2 | Revalidation interval (s) |
| opcache.jit | 1255 | disable | JIT mode |
| opcache.jit_buffer_size | 128M | 0 | JIT buffer |

## Memory Consumption Calculation

```
memory_consumption = total_php_files * avg_bytecode_size (20-50 KB per file)

  Small project (500 files):    15MB  → set 64MB
  Medium project (2000 files):  60MB  → set 128MB
  Large project (5000 files):  175MB  → set 256MB
  Enterprise (10000+ files):   350MB  → set 512MB
```

## max_accelerated_files Calculation

PHP rounds up to the next prime from: 223, 463, 983, 1979, 3907, 7963, 16229, 32531, 65407, 130987

| Total PHP Files | Set To | PHP Uses |
|----------------|--------|----------|
| < 200 | 1000 | 983 |
| 200-900 | 4000 | 3907 |
| 900-3800 | 8000 | 7963 |
| 3800-8000 | 20000 | 16229 |
| 8000-16000 | 32531 | 32531 |

## JIT Configuration (PHP 8.0+)

```
opcache.jit = CRTO (4-digit mode)
  C: CPU optimization (0=off, 1=on)
  R: Register allocation (0=off, 1=local, 2=global)
  T: Trigger (0=first run, 3=hot counter, 5=tracing)
  O: Optimization (0=none, 5=full)
```

| Mode | Value | Use Case |
|------|-------|----------|
| Tracing (recommended) | 1255 | Web applications |
| Function | 1205 | Simpler, less memory |
| Disabled | disable | Development, debugging |

## Preloading (PHP 7.4+)

```php
<?php
// config/preload.php
$directories = [
    '/app/src/Domain/', '/app/src/Application/',
    '/app/vendor/symfony/http-kernel/',
];
foreach ($directories as $dir) {
    if (!is_dir($dir)) continue;
    $it = new RecursiveIteratorIterator(
        new RecursiveDirectoryIterator($dir, FilesystemIterator::SKIP_DOTS)
    );
    foreach ($it as $file) {
        if ($file->getExtension() === 'php') opcache_compile_file($file->getRealPath());
    }
}
```

| Category | Preload? | Reason |
|----------|----------|--------|
| Domain entities / Value objects | Yes | Loaded on every request |
| Framework core | Yes | Always loaded |
| Controllers | Maybe | Only relevant routes |
| Tests / Migrations | No | Not in production |

## Monitoring OPcache

| Metric | Healthy | Action Needed |
|--------|---------|--------------|
| Hit rate | > 99% | < 95%: check validate_timestamps |
| Memory free | > 20% | < 10%: increase memory_consumption |
| Wasted memory | < 5% | > 10%: restart PHP-FPM |
| Cache full | false | true: increase max_accelerated_files |

## Production OPcache INI

```ini
[opcache]
opcache.enable = 1
opcache.enable_cli = 1
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 32
opcache.max_accelerated_files = 20000
opcache.validate_timestamps = 0
opcache.revalidate_freq = 0
opcache.save_comments = 1
opcache.fast_shutdown = 1
opcache.jit = 1255
opcache.jit_buffer_size = 128M
opcache.preload = /app/config/preload.php
opcache.preload_user = www-data
opcache.log_verbosity_level = 1
opcache.error_log = /proc/self/fd/2
```

## Development OPcache INI

```ini
[opcache]
opcache.enable = 1
opcache.enable_cli = 0
opcache.memory_consumption = 128
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 10000
opcache.validate_timestamps = 1
opcache.revalidate_freq = 2
opcache.save_comments = 1
opcache.jit = disable
opcache.jit_buffer_size = 0
```

## Dockerfile Integration

```dockerfile
ARG APP_ENV=production
COPY docker/php/opcache-${APP_ENV}.ini /usr/local/etc/php/conf.d/opcache.ini
COPY config/preload.php /app/config/preload.php
```

## Before/After Comparison

| Metric | No OPcache | OPcache | OPcache+JIT+Preload |
|--------|-----------|---------|---------------------|
| First request | 200ms | 200ms | 50ms (preloaded) |
| Subsequent requests | 200ms | 15ms | 5ms |
| Memory per worker | 30MB | 35MB | 38MB |
| Throughput (req/s) | 50 | 300 | 500 |
| CPU usage | High | Medium | Low |

## Generation Instructions

1. **Count PHP files:** `find /app -name "*.php" | wc -l` (including vendor)
2. **Calculate memory:** files * 35KB, round up to nearest power of 2
3. **Set max_accelerated_files:** Next prime above file count
4. **Configure JIT:** 1255 for production, disable for development
5. **Create preload script:** Include domain, application, and framework core
6. **Set validate_timestamps:** 0 for immutable containers, 1 for development
7. **Monitor:** Check hit rate and memory usage after deployment
