---
name: acc-create-dockerfile-production
description: Generates production-ready Dockerfiles for PHP 8.4 projects. Creates multi-stage builds with composer deps, extensions builder, and optimized production stages.
---

# Production Dockerfile Generator

Generates production-ready, multi-stage Dockerfiles for PHP 8.4 projects with security hardening, OPcache tuning, and PHP-FPM optimization.

## Generated Files

```
Dockerfile              # Production multi-stage build (3 stages)
```

## Generation Instructions

1. **Analyze project:**
   - Read `composer.json` for PHP version and required extensions
   - Check `require` section for `ext-*` entries
   - Detect framework: Symfony (`symfony/framework-bundle`), Laravel (`laravel/framework`)
   - Identify database drivers: `pdo_pgsql`, `pdo_mysql`
   - Check for `ext-redis`, `ext-amqp`, `ext-gd`, `ext-intl`, etc.

2. **Determine base image:**
   - Default: `php:8.4-fpm-alpine` (smallest production image)
   - Use Alpine variants for minimal attack surface

3. **Generate Dockerfile:**
   - Use 3-stage build: composer deps, extensions builder, production
   - Order layers by change frequency (least changed first)
   - Include only runtime dependencies in final stage

4. **Apply security hardening:**
   - Non-root user with explicit UID/GID
   - Read-only filesystem where possible
   - No package manager cache in final image
   - HEALTHCHECK for orchestration

5. **Apply framework-specific optimizations:**
   - Symfony: warm cache, dump env, compile container
   - Laravel: config cache, route cache, view cache, storage link

## Multi-Stage Production Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.6

#############################################
# Stage 1: Composer Dependencies
#############################################
FROM composer:2.8 AS composer-deps

WORKDIR /app

# Copy only composer files for better layer caching
COPY composer.json composer.lock ./

# Install production dependencies only
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-progress \
    --ignore-platform-reqs

# Copy full source code
COPY . .

# Generate optimized autoloader with classmap
RUN composer dump-autoload \
    --no-dev \
    --optimize \
    --classmap-authoritative

#############################################
# Stage 2: PHP Extensions Builder
#############################################
FROM php:8.4-fpm-alpine AS extensions-builder

# Install build dependencies in single layer
RUN apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS \
    linux-headers \
    libzip-dev \
    icu-dev \
    postgresql-dev \
    libpng-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    libwebp-dev \
    libxml2-dev \
    oniguruma-dev \
    rabbitmq-c-dev

# Configure and install extensions in single RUN
RUN docker-php-ext-configure gd \
        --with-freetype \
        --with-jpeg \
        --with-webp \
    && docker-php-ext-install -j$(nproc) \
        pdo_pgsql \
        pdo_mysql \
        intl \
        zip \
        opcache \
        gd \
        pcntl \
        bcmath \
        sockets \
        mbstring

# Install PECL extensions
RUN pecl install redis-6.1.0 \
    && pecl install amqp-2.1.2 \
    && docker-php-ext-enable redis amqp

#############################################
# Stage 3: Production Image
#############################################
FROM php:8.4-fpm-alpine AS production

LABEL maintainer="team@example.com"
LABEL org.opencontainers.image.source="https://github.com/org/repo"

# Install runtime dependencies only (no build tools)
RUN apk add --no-cache \
    libzip \
    icu-libs \
    libpq \
    libpng \
    libjpeg-turbo \
    freetype \
    libwebp \
    libxml2 \
    oniguruma \
    rabbitmq-c \
    fcgi \
    && rm -rf /var/cache/apk/*

# Copy compiled extensions from builder
COPY --from=extensions-builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=extensions-builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

# Use production PHP configuration
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# OPcache production configuration
COPY <<'EOF' /usr/local/etc/php/conf.d/opcache-prod.ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=32
opcache.max_accelerated_files=30000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.jit=1255
opcache.jit_buffer_size=256M
opcache.preload_user=app
EOF

# PHP production settings
COPY <<'EOF' /usr/local/etc/php/conf.d/production.ini
display_errors=Off
display_startup_errors=Off
log_errors=On
error_log=/proc/self/fd/2
error_reporting=E_ALL & ~E_DEPRECATED & ~E_STRICT
expose_php=Off
memory_limit=256M
max_execution_time=30
max_input_time=60
post_max_size=20M
upload_max_filesize=10M
session.use_strict_mode=1
session.cookie_httponly=1
session.cookie_secure=1
session.cookie_samesite=Lax
realpath_cache_size=4096K
realpath_cache_ttl=600
EOF

# PHP-FPM tuning
COPY <<'EOF' /usr/local/etc/php-fpm.d/zz-production.conf
[www]
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
access.log = /proc/self/fd/2
slowlog = /proc/self/fd/2
request_slowlog_timeout = 5s
catch_workers_output = yes
decorate_workers_output = no
EOF

# Create non-root user
RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -s /bin/sh -D app \
    && mkdir -p /app/var /app/public \
    && chown -R app:app /app

WORKDIR /app

# Copy application from composer stage
COPY --from=composer-deps --chown=app:app /app/vendor /app/vendor
COPY --chown=app:app . /app

# Set proper permissions
RUN chown -R app:app /app/var 2>/dev/null || true

USER app

# Health check using php-fpm ping
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
        cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

## Framework Variations

### Symfony Production

See `references/symfony-dockerfile.md` for complete Symfony-specific template with:
- Cache warmup during build
- Compiled container
- Environment variable handling via `.env.local.php`
- Asset compilation stage

### Laravel Production

See `references/laravel-dockerfile.md` for complete Laravel-specific template with:
- Config/route/view caching
- Storage directory linking
- Artisan optimize
- Queue worker variant

## Extension Detection from composer.json

Map `require` entries to Docker extensions:

| composer.json | Docker extension | APK runtime dependency |
|---|---|---|
| `ext-pdo_pgsql` | `pdo_pgsql` | `libpq` |
| `ext-pdo_mysql` | `pdo_mysql` | (none) |
| `ext-intl` | `intl` | `icu-libs` |
| `ext-zip` | `zip` | `libzip` |
| `ext-gd` | `gd` | `libpng libjpeg-turbo freetype libwebp` |
| `ext-redis` | `redis` (PECL) | (none) |
| `ext-amqp` | `amqp` (PECL) | `rabbitmq-c` |
| `ext-bcmath` | `bcmath` | (none) |
| `ext-pcntl` | `pcntl` | (none) |
| `ext-sockets` | `sockets` | (none) |
| `ext-mbstring` | `mbstring` | `oniguruma` |

## Build Commands

```bash
# Standard production build
docker build --target production -t app:latest .

# Build with BuildKit cache
DOCKER_BUILDKIT=1 docker build \
    --target production \
    --cache-from app:latest \
    -t app:$(git rev-parse --short HEAD) \
    -t app:latest \
    .

# Multi-platform build
docker buildx build \
    --platform linux/amd64,linux/arm64 \
    --target production \
    -t registry.example.com/app:latest \
    --push \
    .
```

## Security Checklist

- Non-root user (UID 1000)
- Alpine base (minimal attack surface)
- No build tools in final image
- No package manager cache
- `expose_php=Off`
- Secure session cookies
- HEALTHCHECK for orchestration readiness
- OCI labels for image provenance
- No secrets baked into image

## Usage

Provide:
- PHP version (default: 8.4)
- Required extensions (from composer.json)
- Framework (Symfony/Laravel/none)
- OPcache preload file path (optional)

The generator will:
1. Detect extensions from composer.json
2. Create 3-stage Dockerfile
3. Apply framework-specific optimizations
4. Configure OPcache, PHP-FPM, and security settings
