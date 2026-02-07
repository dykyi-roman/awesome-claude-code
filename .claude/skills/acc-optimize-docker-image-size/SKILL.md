---
name: acc-optimize-docker-image-size
description: Optimizes Docker image size for PHP projects. Reduces image footprint through Alpine, multi-stage builds, layer cleanup, and dependency minimization.
---

# Docker Image Size Optimization

Analyzes Docker images and provides actionable recommendations to reduce footprint for PHP projects.

## Image Size Anatomy

```
┌─────────────────────────────────────────────────────────────────┐
│              TYPICAL PHP IMAGE SIZE BREAKDOWN                    │
├─────────────────────────────────────────────────────────────────┤
│  Base OS (Debian):   ████████████████████░░░░░  150MB (33%)    │
│  PHP runtime:        ████████░░░░░░░░░░░░░░░░░   50MB (11%)   │
│  PHP extensions:     ██████░░░░░░░░░░░░░░░░░░░   40MB  (9%)   │
│  Build dependencies: ████████████░░░░░░░░░░░░░   80MB (18%)   │
│  Composer vendor:    ████████████░░░░░░░░░░░░░   80MB (18%)   │
│  Application source: ████░░░░░░░░░░░░░░░░░░░░░   20MB  (4%)   │
│  Misc (logs, cache): ████░░░░░░░░░░░░░░░░░░░░░   30MB  (7%)   │
│  Total unoptimized:  █████████████████████████  ~450MB          │
│  Target optimized:   ████████████░░░░░░░░░░░░░  ~120MB (-73%) │
└─────────────────────────────────────────────────────────────────┘
```

## Size Estimation by Component

| Component | Debian | Alpine | Savings |
|-----------|--------|--------|---------|
| Base OS | 150MB | 8MB | -142MB |
| PHP runtime | 50MB | 35MB | -15MB |
| PHP extensions (5 typical) | 40MB | 25MB | -15MB |
| Build dependencies | 80MB | 0MB (multi-stage) | -80MB |
| Vendor (with dev) | 80MB | 30MB (--no-dev) | -50MB |
| Application source | 20MB | 10MB (.dockerignore) | -10MB |
| **Total** | **~450MB** | **~108MB** | **-342MB** |

## Alpine vs Debian

```dockerfile
# ❌ Debian-based: ~150MB base → Final: 400-500MB
FROM php:8.4-fpm

# ✅ Alpine-based: ~8MB base → Final: 80-150MB
FROM php:8.4-fpm-alpine
```

| Concern | Solution |
|---------|----------|
| musl vs glibc | Most PHP extensions work fine with musl |
| Missing packages | Use `apk search` to find Alpine equivalents |
| DNS resolution | Add `gnu-libc-compat` if needed |

## Multi-Stage Builds: Production-Only Artifacts

```dockerfile
# Stage 1: Build with all tools
FROM php:8.4-cli-alpine AS builder
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS libzip-dev icu-dev \
    && docker-php-ext-install pdo_mysql intl zip
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist --optimize-autoloader
COPY . .

# Stage 2: Minimal production image
FROM php:8.4-fpm-alpine AS production
RUN apk add --no-cache libzip icu-libs
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /app/vendor /app/vendor
COPY --from=builder /app/src /app/src
COPY --from=builder /app/public /app/public
COPY --from=builder /app/config /app/config
```

## Build Dependencies Cleanup

```dockerfile
# ❌ BAD: Build deps remain in image (+80MB)
RUN apk add $PHPIZE_DEPS libzip-dev icu-dev \
    && docker-php-ext-install pdo_mysql intl zip

# ✅ GOOD: Virtual package for clean removal
RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS libzip-dev icu-dev libpng-dev \
    && docker-php-ext-install pdo_mysql intl zip gd \
    && apk del .build-deps \
    && apk add --no-cache libzip icu-libs libpng
```

Debian equivalent:

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends libzip-dev libicu-dev \
    && docker-php-ext-install pdo_mysql intl zip \
    && apt-get purge -y --auto-remove libzip-dev libicu-dev \
    && rm -rf /var/lib/apt/lists/*
```

## Composer Dependency Minimization

```dockerfile
# ❌ BAD: Includes dev deps (+50MB: phpunit, phpstan, faker)
RUN composer install

# ✅ GOOD: Production only
RUN composer install --no-dev --prefer-dist --optimize-autoloader \
    --classmap-authoritative --no-scripts
```

## Image Analysis Tools

```bash
# Dive: interactive layer analysis
dive app:latest

# CI mode: fail if wasted space > 10%
CI=true dive app:latest --highestWastedBytes 10MB

# Docker history: show layer sizes
docker history --human --no-trunc app:latest
```

## Specific Savings Per Technique

| Technique | Typical Savings | Effort |
|-----------|----------------|--------|
| Switch to Alpine | 120-200MB | Low |
| Multi-stage build | 50-150MB | Medium |
| Remove build deps (.build-deps) | 40-80MB | Low |
| Composer --no-dev | 30-60MB | Low |
| .dockerignore | 10-50MB | Low |
| Remove unused system packages | 10-30MB | Low |
| Optimize COPY (specific paths) | 5-20MB | Low |
| Strip debug symbols | 5-15MB | Low |

## Before/After Comparison

| Metric | Unoptimized | Optimized | Improvement |
|--------|-------------|-----------|-------------|
| Base image | php:8.4-fpm (150MB) | php:8.4-fpm-alpine (8MB) | -142MB |
| Build deps | Included (80MB) | Multi-stage removed | -80MB |
| Vendor | With dev (80MB) | --no-dev (30MB) | -50MB |
| Source | Full repo (20MB) | .dockerignore (10MB) | -10MB |
| **Total** | **~450MB** | **~108MB** | **-76%** |

## Generation Instructions

1. **Analyze current image:** Run `docker history` and `dive` to identify large layers
2. **Identify waste:** Build deps, dev packages, unnecessary files
3. **Apply techniques:** Alpine base, multi-stage, cleanup, --no-dev
4. **Measure result:** Compare before/after with `docker images`
5. **Validate runtime:** Ensure application works correctly with minimal image
