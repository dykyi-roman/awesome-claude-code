# Multi-Stage Build Patterns for PHP

Patterns for efficient, cacheable, secure multi-stage Docker builds.

## BuildKit Syntax Header

Always include BuildKit syntax at the top of multi-stage Dockerfiles:

```dockerfile
# syntax=docker/dockerfile:1
```

This enables cache mounts, secret mounts, and parallel stage building.

## Stage 1: Composer Dependencies

```dockerfile
# syntax=docker/dockerfile:1

FROM composer:2 AS composer-deps

WORKDIR /app

# Copy only dependency files first for caching
COPY composer.json composer.lock ./

# Install without dev dependencies, no autoloader (source not yet available)
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
        --no-dev \
        --no-scripts \
        --no-autoloader \
        --prefer-dist \
        --no-progress
```

### With Dev Dependencies (for CI/testing)

```dockerfile
FROM composer:2 AS composer-deps-dev

WORKDIR /app

COPY composer.json composer.lock ./

RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
        --no-scripts \
        --no-autoloader \
        --prefer-dist \
        --no-progress
```

## Stage 2: PHP Extensions Builder

```dockerfile
FROM php:8.4-fpm-alpine AS php-extensions

RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        libzip-dev \
        icu-dev \
        libpq-dev \
        linux-headers \
    && docker-php-ext-install \
        zip \
        intl \
        pdo_mysql \
        pdo_pgsql \
        opcache \
        pcntl \
        sockets \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apk del .build-deps
```

### Why Separate Extension Stage

```
Benefits:
- Extensions are cached independently of source code
- Rebuild only when extension list changes
- Can be shared across multiple project images
- Reduces production stage complexity
```

## Stage 3: Frontend Assets (Node)

```dockerfile
FROM node:22-alpine AS frontend

WORKDIR /app

COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline

COPY resources/ ./resources/
COPY vite.config.js tailwind.config.js postcss.config.js ./

RUN npm run build
```

### Output Files

```
Only the build output is needed in the production stage:
- public/build/          (Vite/Webpack output)
- public/build/manifest.json
No node_modules, no source JS/CSS
```

## Stage 4: Production (Final)

```dockerfile
FROM php:8.4-fpm-alpine AS production

# Copy pre-built extensions
COPY --from=php-extensions /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=php-extensions /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

# Copy runtime dependencies only
RUN apk add --no-cache libzip icu-libs libpq

# Create non-root user
RUN addgroup -g 1000 app && adduser -u 1000 -G app -D app

WORKDIR /var/www/html

# Copy composer dependencies
COPY --from=composer-deps /app/vendor/ ./vendor/

# Copy application source
COPY --chown=app:app . .

# Copy frontend assets
COPY --from=frontend /app/public/build/ ./public/build/

# Generate optimized autoloader with source present
RUN composer dump-autoload --optimize --classmap-authoritative --no-dev

# Production PHP config
COPY docker/php/php.ini /usr/local/etc/php/php.ini
COPY docker/php/php-fpm.conf /usr/local/etc/php-fpm.d/www.conf

USER app

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD php-fpm-healthcheck || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

## Complete Multi-Stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1

# === Stage 1: Composer Dependencies ===
FROM composer:2 AS composer-deps

WORKDIR /app
COPY composer.json composer.lock ./

RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-dev --no-scripts --no-autoloader --prefer-dist --no-progress

# === Stage 2: PHP Extensions ===
FROM php:8.4-fpm-alpine AS php-extensions

RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS libzip-dev icu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && pecl install redis && docker-php-ext-enable redis \
    && apk del .build-deps

# === Stage 3: Frontend ===
FROM node:22-alpine AS frontend

WORKDIR /app
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --prefer-offline
COPY resources/ ./resources/
COPY vite.config.js tailwind.config.js postcss.config.js ./
RUN npm run build

# === Stage 4: Production ===
FROM php:8.4-fpm-alpine AS production

COPY --from=php-extensions /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=php-extensions /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

RUN apk add --no-cache libzip icu-libs fcgi \
    && addgroup -g 1000 app && adduser -u 1000 -G app -D app

WORKDIR /var/www/html

COPY --from=composer-deps /app/vendor/ ./vendor/
COPY --chown=app:app . .
COPY --from=frontend /app/public/build/ ./public/build/

RUN composer dump-autoload --optimize --classmap-authoritative --no-dev

COPY docker/php/php.ini /usr/local/etc/php/php.ini
COPY docker/php/php-fpm.conf /usr/local/etc/php-fpm.d/www.conf

USER app

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1

EXPOSE 9000
CMD ["php-fpm"]
```

## Parallel Builds with BuildKit

BuildKit automatically parallelizes independent stages:

```
Build Graph:
                    ┌──────────────┐
              ┌────→│ composer-deps │
              │     └──────────────┘
              │     ┌──────────────┐
Dockerfile ───┼────→│ php-extensions│    (parallel)
              │     └──────────────┘
              │     ┌──────────────┐
              └────→│   frontend   │
                    └──────────────┘
                           │
                    ┌──────┴───────┐
                    │  production  │    (waits for all above)
                    └──────────────┘
```

Enable BuildKit:

```bash
# Environment variable
DOCKER_BUILDKIT=1 docker build .

# Docker buildx (recommended)
docker buildx build .
```

## Target-Specific Builds

Use `--target` to build specific stages:

```dockerfile
# === Testing stage ===
FROM composer-deps AS testing

COPY --from=php-extensions /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=php-extensions /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

RUN apk add --no-cache libzip icu-libs

WORKDIR /var/www/html
COPY . .

# Install dev dependencies for testing
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-progress

RUN ./vendor/bin/phpunit
```

```bash
# Build only production
docker build --target production -t myapp:prod .

# Build and run tests
docker build --target testing -t myapp:test .

# Build for development (with xdebug)
docker build --target development -t myapp:dev .
```

## Cache Mount Patterns

### Composer Cache

```dockerfile
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-dev --prefer-dist
```

### APK Cache (Alpine)

```dockerfile
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache libzip-dev icu-dev
```

### APT Cache (Debian)

```dockerfile
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt/lists \
    apt-get update && apt-get install -y libzip-dev libicu-dev
```

### NPM Cache

```dockerfile
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline
```

### Multiple Caches in One RUN

```dockerfile
RUN --mount=type=cache,target=/root/.composer/cache \
    --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache libzip-dev \
    && docker-php-ext-install zip \
    && composer install --no-dev --prefer-dist
```

## Layer Optimization

### Order of COPY Instructions

```dockerfile
# Least frequently changed → most frequently changed

COPY docker/php/php.ini /usr/local/etc/php/php.ini      # 1. Config (rarely changes)
COPY --from=composer-deps /app/vendor/ ./vendor/          # 2. Dependencies (weekly)
COPY --from=frontend /app/public/build/ ./public/build/   # 3. Assets (with releases)
COPY --chown=app:app . .                                  # 4. Source code (every commit)
```

### Reducing Layer Count

```dockerfile
# Bad: Multiple RUN layers
RUN apk add --no-cache libzip-dev
RUN docker-php-ext-install zip
RUN apk del libzip-dev

# Good: Single RUN layer
RUN apk add --no-cache --virtual .build-deps libzip-dev \
    && apk add --no-cache libzip \
    && docker-php-ext-install zip \
    && apk del .build-deps
```

## Detection Patterns

```bash
# Check for multi-stage builds
Grep: "^FROM .* AS " --glob "Dockerfile*"

# Check for BuildKit syntax
Grep: "^# syntax=" --glob "Dockerfile*"

# Check for cache mounts
Grep: "--mount=type=cache" --glob "Dockerfile*"

# Warning: No multi-stage (single FROM)
Grep: "^FROM " --glob "Dockerfile*" | wc -l  # Should be > 1

# Warning: Missing cache mounts for composer
Grep: "composer install" --glob "Dockerfile*" | grep -v "mount=type=cache"
```
