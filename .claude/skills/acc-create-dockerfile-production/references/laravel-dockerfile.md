# Laravel Production Dockerfile

Complete Laravel-specific production Dockerfile template.

## Laravel Multi-Stage Dockerfile

```dockerfile
# syntax=docker/dockerfile:1.6

#############################################
# Stage 1: Composer Dependencies
#############################################
FROM composer:2.8 AS composer-deps

WORKDIR /app

COPY composer.json composer.lock ./

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

#############################################
# Stage 2: PHP Extensions Builder
#############################################
FROM php:8.4-fpm-alpine AS extensions-builder

RUN apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS linux-headers \
    libzip-dev icu-dev postgresql-dev \
    libpng-dev libjpeg-turbo-dev freetype-dev libwebp-dev \
    oniguruma-dev

RUN docker-php-ext-configure gd --with-freetype --with-jpeg --with-webp \
    && docker-php-ext-install -j$(nproc) \
        pdo_pgsql pdo_mysql intl zip opcache gd pcntl bcmath mbstring exif

RUN pecl install redis-6.1.0 \
    && docker-php-ext-enable redis

#############################################
# Stage 3: Laravel Production
#############################################
FROM php:8.4-fpm-alpine AS production

RUN apk add --no-cache \
    libzip icu-libs libpq libpng libjpeg-turbo \
    freetype libwebp oniguruma fcgi \
    && rm -rf /var/cache/apk/*

COPY --from=extensions-builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=extensions-builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# OPcache production config
COPY <<'EOF' /usr/local/etc/php/conf.d/opcache-laravel.ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=32
opcache.max_accelerated_files=30000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.jit=1255
opcache.jit_buffer_size=256M
EOF

RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -s /bin/sh -D app

WORKDIR /app

# Copy vendor first (better caching)
COPY --from=composer-deps --chown=app:app /app/vendor /app/vendor
COPY --chown=app:app . /app

# Laravel environment
ENV APP_ENV=production
ENV APP_DEBUG=false
ENV LOG_CHANNEL=stderr

# Create required Laravel directories
RUN mkdir -p \
    storage/app/public \
    storage/framework/cache/data \
    storage/framework/sessions \
    storage/framework/testing \
    storage/framework/views \
    storage/logs \
    bootstrap/cache

# Create storage symlink
RUN php artisan storage:link 2>/dev/null || true

# Cache Laravel configuration, routes, views, and events
RUN php artisan config:cache \
    && php artisan route:cache \
    && php artisan view:cache \
    && php artisan event:cache

# Set ownership
RUN chown -R app:app storage bootstrap/cache

# Clear unnecessary files
RUN rm -rf \
    .env.example \
    tests/ phpunit.xml* \
    storage/logs/*.log

USER app

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
    CMD SCRIPT_NAME=/ping SCRIPT_FILENAME=/ping REQUEST_METHOD=GET \
        cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

## Laravel Queue Worker Variant

```dockerfile
# Build on top of the production stage
FROM production AS queue-worker

USER app

# Queue worker with graceful shutdown
HEALTHCHECK --interval=60s --timeout=10s --start-period=5s --retries=3 \
    CMD php artisan queue:monitor redis:default --max=100 2>/dev/null || exit 1

CMD ["php", "artisan", "queue:work", \
    "redis", \
    "--sleep=3", \
    "--tries=3", \
    "--max-time=3600", \
    "--memory=256", \
    "--queue=default,notifications"]
```

## Key Laravel Optimizations

- **Config cache:** `config:cache` merges all config into single cached file
- **Route cache:** `route:cache` serializes route definitions for faster matching
- **View cache:** `view:cache` precompiles all Blade templates
- **Event cache:** `event:cache` discovers and caches event listeners
- **Storage link:** `storage:link` creates public/storage symlink for file serving
- **LOG_CHANNEL=stderr:** Sends logs to Docker log collector instead of files
- **Queue worker variant:** Separate stage for long-running queue processes with memory limits
