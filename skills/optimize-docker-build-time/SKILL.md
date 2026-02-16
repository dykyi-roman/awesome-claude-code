---
name: acc-optimize-docker-build-time
description: Optimizes Docker build time for PHP projects. Analyzes layer caching, BuildKit features, parallel builds, and dependency installation.
---

# Docker Build Time Optimization

Analyzes Dockerfiles and CI pipelines to minimize build time for PHP projects.

## Build Time Breakdown

```
┌─────────────────────────────────────────────────────────────────┐
│                 TYPICAL PHP BUILD TIMELINE                       │
├─────────────────────────────────────────────────────────────────┤
│  Context upload:    ████░░░░░░░░░░░░░░░░░░░░░░  10s (5%)       │
│  Base image pull:   ████████░░░░░░░░░░░░░░░░░░  30s (15%)      │
│  System packages:   ██████░░░░░░░░░░░░░░░░░░░░  20s (10%)      │
│  PHP extensions:    ████████████░░░░░░░░░░░░░░  60s (30%)      │
│  Composer install:  ██████████░░░░░░░░░░░░░░░░  45s (22%)      │
│  Source code copy:  ██░░░░░░░░░░░░░░░░░░░░░░░░   5s (3%)       │
│  Post-build steps:  ██████░░░░░░░░░░░░░░░░░░░░  30s (15%)      │
│  Total:             ████████████████████████████ ~200s           │
│  Target optimized:                              ~60s (-70%)     │
└─────────────────────────────────────────────────────────────────┘
```

## Layer Ordering by Change Frequency

| Order | Layer | Change Frequency | Cache Strategy |
|-------|-------|-----------------|----------------|
| 1 | Base image (FROM) | Quarterly | Pin version tag |
| 2 | System packages (apk/apt) | Monthly | Combine in one RUN |
| 3 | PHP extensions | Monthly | Separate from packages |
| 4 | Composer dependencies | Weekly | Copy lock file first |
| 5 | NPM dependencies | Weekly | Copy package-lock first |
| 6 | Application source | Every commit | COPY . last |

## BuildKit Cache Mounts

```dockerfile
# syntax=docker/dockerfile:1.6

# Composer cache mount (saves 20-40s)
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --prefer-dist --no-progress --no-scripts

# APK cache mount (Alpine)
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --cache-dir=/var/cache/apk libzip icu-libs

# APT cache mount (Debian)
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y --no-install-recommends libzip-dev

# NPM cache mount
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit
```

## Parallel Multi-Stage Builds

```dockerfile
# syntax=docker/dockerfile:1.6

# Stage 1: PHP deps (parallel with Stage 2)
FROM composer:2 AS php-deps
COPY composer.json composer.lock ./
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-dev --prefer-dist --no-progress --no-scripts

# Stage 2: JS deps (parallel with Stage 1)
FROM node:20-alpine AS js-deps
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --production --no-audit

# Stage 3: Final (waits for both)
FROM php:8.4-fpm-alpine
COPY --from=php-deps /app/vendor ./vendor
COPY --from=js-deps /app/node_modules ./node_modules
COPY . .
```

**Impact:** Parallel stages reduce total build time by 30-50%.

## .dockerignore to Reduce Context

```
.git
vendor
node_modules
tests
docs
var/cache
var/log
*.md
docker-compose*.yml
.env*
.phpunit*
phpstan*
```

**Impact:** Reduces context transfer from 500MB to 10MB (-98%).

## Pre-Built Base Images

```dockerfile
# ❌ BAD: Install extensions every build (~60s)
FROM php:8.4-fpm-alpine
RUN docker-php-ext-install pdo_mysql intl zip opcache

# ✅ GOOD: Pre-built base with extensions (~0s)
FROM registry.example.com/php-base:8.4-fpm-alpine
```

## Registry Cache and Buildx

```bash
# Pull previous build as cache source
docker build --cache-from registry.example.com/app:latest \
    --build-arg BUILDKIT_INLINE_CACHE=1 -t app:latest .

# Buildx with registry cache
docker buildx build \
    --cache-from type=registry,ref=registry.example.com/app:cache \
    --cache-to type=registry,ref=registry.example.com/app:cache,mode=max .
```

## Composer Install Optimization

```dockerfile
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --prefer-dist --no-progress --no-interaction \
        --no-scripts --no-dev --optimize-autoloader
```

| Flag | Effect | Time Saved |
|------|--------|-----------|
| --prefer-dist | Downloads zip instead of git clone | 10-20s |
| --no-progress | Reduces output overhead | 2-5s |
| --no-scripts | Skips post-install scripts | 5-15s |
| --no-dev | Skips dev dependencies | 10-30s |
| Cache mount | Reuses downloaded packages | 20-40s |

## PHP Extensions: Virtual Build Deps

```dockerfile
RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS libzip-dev icu-dev libpng-dev libjpeg-turbo-dev \
    && docker-php-ext-configure gd --with-jpeg \
    && docker-php-ext-install -j$(nproc) pdo_mysql intl zip gd opcache \
    && apk del .build-deps \
    && apk add --no-cache libzip icu-libs libpng libjpeg-turbo
```

## APT-GET Combined Pattern

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends libzip-dev libicu-dev libpng-dev \
    && docker-php-ext-install pdo_mysql intl zip gd \
    && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
    && rm -rf /var/lib/apt/lists/*
```

## Before/After Comparison

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Build context size | 500MB | 10MB | -98% |
| Cold build time | 5m 30s | 2m 00s | -64% |
| Warm build (deps unchanged) | 3m 00s | 30s | -83% |
| Warm build (code only) | 2m 00s | 15s | -87% |
| Extension install time | 60s | 0s (pre-built) | -100% |
| Composer install (cached) | 45s | 5s | -89% |

## Estimation Formulas

```
Cold Build Time = context_upload + base_pull + extensions + deps + source + post_build
Warm Build Time = context_upload + source + post_build (if cache hits)
Extension Time  = num_extensions * 15s (compile) or 0s (pre-built)
Composer Time   = num_packages * 0.5s (no cache) or num_packages * 0.05s (cached)
```

## Generation Instructions

1. **Analyze current build:** Parse Dockerfile, measure layer times
2. **Identify bottlenecks:** Extensions, dependencies, context size
3. **Apply optimizations:** Cache mounts, parallel stages, pre-built base
4. **Measure improvement:** Compare cold and warm build times
5. **Configure CI cache:** Set up registry or platform cache
