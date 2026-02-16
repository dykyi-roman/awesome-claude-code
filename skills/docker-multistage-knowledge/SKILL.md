---
name: acc-docker-multistage-knowledge
description: Docker multi-stage build knowledge base. Provides patterns for PHP dependency, extension builder, and production stages with cache optimization.
---

# Docker Multi-Stage Build Knowledge Base

Patterns and best practices for multi-stage Docker builds in PHP applications.

## Multi-Stage Build Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MULTI-STAGE BUILD PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Stage 1: deps            Stage 2: extensions       Stage 3: build         │
│   ┌──────────────┐         ┌──────────────┐         ┌──────────────┐       │
│   │  Composer     │         │  PHP Ext     │         │  App Build   │       │
│   │  Install      │         │  Compile     │         │  Assets      │       │
│   │              │         │              │         │  Optimize    │       │
│   │  vendor/     │         │  *.so files  │         │  Cache warm  │       │
│   └──────┬───────┘         └──────┬───────┘         └──────┬───────┘       │
│          │                        │                        │               │
│          │    COPY --from=deps    │  COPY --from=extensions│               │
│          └────────────┐   ┌──────┘    ┌───────────────────┘               │
│                       │   │           │                                    │
│                       ▼   ▼           ▼                                    │
│                  ┌─────────────────────────┐                               │
│                  │   Stage 4: production    │                               │
│                  │   ┌───────────────────┐ │                               │
│                  │   │  Minimal base     │ │                               │
│                  │   │  + vendor/        │ │                               │
│                  │   │  + extensions     │ │                               │
│                  │   │  + app code       │ │                               │
│                  │   │  + optimized cfg  │ │                               │
│                  │   └───────────────────┘ │                               │
│                  │   Final image: ~80MB    │                               │
│                  └─────────────────────────┘                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Stage Naming Convention

| Stage Name | Purpose | Base Image |
|------------|---------|------------|
| `deps` | Composer dependency installation | `composer:2` |
| `extensions` | PHP extension compilation | `php:8.4-fpm-alpine` |
| `build` | Asset compilation, cache warmup | `php:8.4-cli-alpine` |
| `dev` | Development with Xdebug, tools | `php:8.4-fpm-alpine` |
| `production` | Final minimal runtime image | `php:8.4-fpm-alpine` |

## Stage 1: Composer Dependencies

```dockerfile
# syntax=docker/dockerfile:1
FROM composer:2 AS deps

WORKDIR /app

# Copy only dependency manifests first for layer caching
COPY composer.json composer.lock ./

# Install production deps only (no dev)
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-interaction

# Copy source and dump optimized autoloader
COPY src/ src/
COPY config/ config/

RUN composer dump-autoload --optimize --classmap-authoritative
```

## Stage 2: PHP Extensions Builder

```dockerfile
FROM php:8.4-fpm-alpine AS extensions

RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        icu-dev \
        libpq-dev \
        libzip-dev \
        freetype-dev \
        libjpeg-turbo-dev \
        libpng-dev \
    && docker-php-ext-configure gd \
        --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        intl \
        pdo_pgsql \
        zip \
        gd \
        opcache \
    && pecl install redis apcu \
    && docker-php-ext-enable redis apcu \
    && apk del .build-deps
```

## Stage 3: Production Final

```dockerfile
FROM php:8.4-fpm-alpine AS production

# Runtime-only dependencies (no build tools)
RUN apk add --no-cache \
    icu-libs \
    libpq \
    libzip \
    freetype \
    libjpeg-turbo \
    libpng

# Copy compiled extensions from builder stage
COPY --from=extensions /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=extensions /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

# Copy vendor directory from deps stage
COPY --from=deps /app/vendor /app/vendor

# Copy application code
COPY . /app

WORKDIR /app

# PHP production configuration
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

USER www-data

EXPOSE 9000
CMD ["php-fpm"]
```

## Cache Optimization Patterns

### BuildKit Cache Mounts

```dockerfile
# Cache composer packages across builds
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-dev --optimize-autoloader

# Cache APK packages across builds
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache icu-dev libpq-dev
```

### Layer Ordering for Cache Hits

```
# Ordered from least to most frequently changed:
1. Base image + system packages     (rarely changes)
2. PHP extensions                   (changes with requirements)
3. Composer dependencies            (changes with composer.lock)
4. Application configuration        (changes occasionally)
5. Application source code          (changes frequently)
```

### Cache From Pattern (CI/CD)

```dockerfile
# Build with cache from registry
docker build \
    --cache-from=registry.io/app:deps-cache \
    --cache-from=registry.io/app:latest \
    --target production \
    -t registry.io/app:latest .
```

## ARG Scoping Across Stages

```dockerfile
# Global ARG (before first FROM) — available in FROM lines only
ARG PHP_VERSION=8.4

FROM php:${PHP_VERSION}-fpm-alpine AS base
# PHP_VERSION is NOT available here unless redeclared
ARG PHP_VERSION
RUN echo "Building with PHP ${PHP_VERSION}"

FROM php:${PHP_VERSION}-cli-alpine AS build
# Must redeclare ARG in each stage that needs it
ARG APP_ENV=prod
RUN echo "Building for ${APP_ENV}"
```

## COPY --from Patterns

```dockerfile
# Copy from named stage
COPY --from=deps /app/vendor /app/vendor

# Copy from external image
COPY --from=composer:2 /usr/bin/composer /usr/local/bin/composer

# Copy specific extension files
COPY --from=extensions /usr/local/lib/php/extensions/no-debug-non-zts-*/ \
    /usr/local/lib/php/extensions/no-debug-non-zts-*/

# Copy with ownership
COPY --from=build --chown=www-data:www-data /app /app
```

## Parallel Builds with BuildKit

```bash
# Enable BuildKit for parallel stage execution
DOCKER_BUILDKIT=1 docker build .

# Or via docker buildx
docker buildx build --target production .
```

BuildKit automatically detects independent stages and builds them in parallel:

```
deps ──────────────┐
                    ├──▶ production
extensions ────────┘
     │
build ──── (depends on deps, runs after)
```

## Target Selection

```bash
# Build only development image
docker build --target dev -t app:dev .

# Build only production image
docker build --target production -t app:prod .

# Build specific intermediate stage for debugging
docker build --target extensions -t app:ext-debug .
```

## Minimizing Final Image

| Technique | Savings | Example |
|-----------|---------|---------|
| Alpine base | ~80MB | `php:8.4-fpm-alpine` vs `php:8.4-fpm` |
| Multi-stage (no build tools) | ~200MB | Separate builder from runtime |
| `.dockerignore` | Variable | Exclude `.git`, `tests/`, `docs/` |
| No dev dependencies | ~50MB | `composer install --no-dev` |
| Optimized autoloader | ~5MB | `--classmap-authoritative` |
| Removed package cache | ~10MB | `apk add --no-cache` or `rm -rf /var/cache/apk/*` |

## References

For base image selection guidance, see `acc-docker-base-images-knowledge`.
For extension installation details, see `acc-docker-php-extensions-knowledge`.
