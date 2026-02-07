# Symfony Production Dockerfile

Complete Symfony-specific production Dockerfile template.

## Symfony Multi-Stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.6

#############################################
# Stage 1: Composer Dependencies
#############################################
FROM composer:2.8 AS composer-deps

WORKDIR /app

COPY composer.json composer.lock symfony.lock ./

RUN --mount=type=cache,target=/root/.composer/cache \
    composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-progress \
    --ignore-platform-reqs

COPY . .

RUN composer dump-autoload --no-dev --optimize --classmap-authoritative
RUN composer run-script post-install-cmd --no-dev 2>/dev/null || true

#############################################
# Stage 2: PHP Extensions Builder
#############################################
FROM php:8.4-fpm-alpine AS extensions-builder

RUN apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS linux-headers \
    libzip-dev icu-dev postgresql-dev \
    libpng-dev libjpeg-turbo-dev freetype-dev libwebp-dev \
    libxml2-dev oniguruma-dev rabbitmq-c-dev

RUN docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j$(nproc) \
        pdo_pgsql intl zip opcache gd pcntl bcmath sockets mbstring

RUN pecl install redis-6.1.0 apcu-5.1.24 \
    && docker-php-ext-enable redis apcu

#############################################
# Stage 3: Symfony Production
#############################################
FROM php:8.4-fpm-alpine AS production

RUN apk add --no-cache \
    libzip icu-libs libpq libpng libjpeg-turbo \
    freetype libwebp libxml2 oniguruma rabbitmq-c fcgi \
    && rm -rf /var/cache/apk/*

COPY --from=extensions-builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=extensions-builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# OPcache with Symfony preloading
COPY <<'EOF' /usr/local/etc/php/conf.d/opcache-symfony.ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=32
opcache.max_accelerated_files=30000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.jit=1255
opcache.jit_buffer_size=256M
opcache.preload=/app/config/preload.php
opcache.preload_user=app
EOF

# APCu for Symfony cache adapter
COPY <<'EOF' /usr/local/etc/php/conf.d/apcu.ini
apc.enabled=1
apc.shm_size=64M
apc.enable_cli=0
EOF

RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -s /bin/sh -D app

WORKDIR /app

# Copy vendor first (changes less frequently)
COPY --from=composer-deps --chown=app:app /app/vendor /app/vendor
COPY --chown=app:app . /app

# Symfony environment setup
ENV APP_ENV=prod
ENV APP_DEBUG=0

# Compile .env files to .env.local.php for production
RUN composer dump-env prod 2>/dev/null || true

# Create var directories
RUN mkdir -p var/cache var/log \
    && chown -R app:app var

# Warm up Symfony cache (compiles container, routes, templates)
RUN php bin/console cache:warmup --env=prod --no-debug \
    && chown -R app:app var/cache

# Clear unnecessary files
RUN rm -rf \
    .env.local .env.*.local \
    tests/ phpunit.xml* \
    var/log/*.log

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
        cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

## Key Symfony Optimizations

- **Preloading:** `opcache.preload=/app/config/preload.php` loads framework classes into shared memory
- **APCu:** Used by Symfony cache adapter for system cache in production
- **Cache warmup:** Compiles DI container, routes, and Twig templates during build
- **Env compilation:** `composer dump-env prod` creates `.env.local.php` avoiding `.env` parsing at runtime
- **APP_ENV=prod:** Ensures production kernel and compiled container are used
