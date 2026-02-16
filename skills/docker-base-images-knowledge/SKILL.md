---
name: acc-docker-base-images-knowledge
description: Docker base images knowledge base for PHP. Provides image selection guidelines, Alpine vs Debian comparison, and version pinning strategies.
---

# Docker Base Images Knowledge Base for PHP

Guidelines for selecting and managing PHP Docker base images.

## PHP Official Images Overview

| Image Tag Pattern | Base OS | Size | Use Case |
|-------------------|---------|------|----------|
| `php:8.4-fpm` | Debian Bookworm | ~480MB | Production FPM (full compatibility) |
| `php:8.4-fpm-alpine` | Alpine 3.20 | ~80MB | Production FPM (minimal size) |
| `php:8.4-cli` | Debian Bookworm | ~450MB | CLI scripts, cron jobs, workers |
| `php:8.4-cli-alpine` | Alpine 3.20 | ~50MB | Lightweight CLI tasks |
| `php:8.4-apache` | Debian Bookworm | ~500MB | All-in-one Apache+PHP |
| `php:8.4-zts` | Debian Bookworm | ~460MB | Thread-safe (parallel ext) |
| `php:8.4-zts-alpine` | Alpine 3.20 | ~85MB | Thread-safe minimal |

## Alpine vs Debian Comparison

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ALPINE vs DEBIAN FOR PHP CONTAINERS                             │
├────────────────────┬────────────────────────┬───────────────────────────────┤
│   Criterion        │   Alpine (musl)        │   Debian (glibc)              │
├────────────────────┼────────────────────────┼───────────────────────────────┤
│   Image Size       │   ~80MB (FPM)          │   ~480MB (FPM)                │
│   C Library        │   musl libc            │   glibc                       │
│   Package Manager  │   apk                  │   apt                         │
│   Security Updates │   Fast, frequent       │   Regular, well-tested        │
│   DNS Resolver     │   musl (simpler)       │   glibc (full-featured)       │
│   Locale Support   │   Limited              │   Full                        │
│   iconv            │   GNU libiconv needed  │   Works out of the box        │
│   Compatibility    │   Most PHP apps OK     │   All PHP apps                │
│   Build Speed      │   Faster (smaller dl)  │   Slower (larger packages)    │
│   Debug Tools      │   Limited              │   Comprehensive               │
│   gRPC / Protobuf  │   May need workarounds │   Works natively              │
│   Image Scanning   │   Fewer CVEs reported  │   More CVEs (more packages)   │
└────────────────────┴────────────────────────┴───────────────────────────────┘
```

## Image Selection Decision Tree

```
Start
  │
  ├── Need Apache built-in?
  │     └── YES ──▶ php:8.4-apache
  │
  ├── Need PHP-FPM (web)?
  │     ├── Need full glibc compatibility?
  │     │     ├── YES ──▶ php:8.4-fpm (Debian)
  │     │     └── NO ──▶ php:8.4-fpm-alpine
  │     │
  │     ├── Using gRPC/protobuf?
  │     │     └── YES ──▶ php:8.4-fpm (Debian)
  │     │
  │     ├── Need locale/intl precision?
  │     │     └── YES ──▶ php:8.4-fpm (Debian)
  │     │
  │     └── Default ──▶ php:8.4-fpm-alpine
  │
  ├── CLI workers / cron / queue consumers?
  │     └── php:8.4-cli-alpine (or cli for glibc)
  │
  └── Need parallel extension (ZTS)?
        └── php:8.4-zts-alpine (or zts for glibc)
```

## Version Pinning Strategies

| Strategy | Example | Stability | Updates |
|----------|---------|-----------|---------|
| **Full pin** | `php:8.4.2-fpm-alpine3.20` | Highest | Manual only |
| **Minor pin** | `php:8.4-fpm-alpine` | High | Patch auto |
| **Major pin** | `php:8-fpm-alpine` | Medium | Minor auto |
| **Latest** | `php:latest` | Lowest | All auto |

**Recommended for production:** Full pin or minor pin with CI rebuild schedule.

```dockerfile
# Full pin (most reproducible)
FROM php:8.4.2-fpm-alpine3.20

# Minor pin (recommended balance)
FROM php:8.4-fpm-alpine

# AVOID in production
FROM php:latest
FROM php:fpm
```

## Common Alpine Issues and Solutions

### DNS Resolution

musl DNS resolver behaves differently from glibc. May cause issues with service discovery.

```dockerfile
# Fix: Add DNS options
RUN echo "options ndots:0" >> /etc/resolv.conf
```

### iconv Issues

Alpine uses musl iconv which has limited charset support.

```dockerfile
# Fix: Install GNU libiconv
RUN apk add --no-cache gnu-libiconv
ENV LD_PRELOAD=/usr/lib/preloadable_libiconv.so
```

### Locale Support

Alpine has minimal locale support by default.

```dockerfile
# Fix: Install locale data for intl
RUN apk add --no-cache icu-data-full
```

### Missing Shared Libraries

Some PECL extensions expect glibc-specific libraries.

```dockerfile
# Fix: Install compatibility layer (use sparingly)
RUN apk add --no-cache gcompat
```

## Image Lifecycle Best Practices

| Practice | Description |
|----------|-------------|
| Pin digest in CI | Use `php:8.4-fpm-alpine@sha256:abc...` for fully reproducible builds |
| Rebuild weekly | Scheduled CI rebuild picks up security patches |
| Scan images | Use `trivy image app:latest` or `docker scout` |
| Track upstream | Monitor `docker-library/php` for breaking changes |
| Test Alpine compat | Run full test suite against Alpine image before adopting |

## References

For detailed image variant comparison, see `references/image-comparison.md`.
For extension installation on different bases, see `acc-docker-php-extensions-knowledge`.
