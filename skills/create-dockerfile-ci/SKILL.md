---
name: acc-create-dockerfile-ci
description: Generates optimized Dockerfiles for PHP CI pipelines. Creates multi-stage builds with separate stages for dependencies, testing, and production with minimal image sizes.
---

# Dockerfile CI Generator

Generates optimized Dockerfiles for PHP projects with multi-stage builds.

## Generated Files

```
Dockerfile                # Production multi-stage build
Dockerfile.ci             # CI-optimized build (optional)
.dockerignore             # Exclude unnecessary files
```

## Multi-Stage Production Dockerfile

```dockerfile
# Dockerfile
# syntax=docker/dockerfile:1.6

#############################################
# Stage 1: Composer Dependencies
#############################################
FROM composer:2.7 AS composer

WORKDIR /app

# Copy only composer files for better caching
COPY composer.json composer.lock ./

# Install dependencies without dev packages
RUN composer install \
    --no-dev \
    --no-scripts \
    --no-autoloader \
    --prefer-dist \
    --no-progress \
    --ignore-platform-reqs

# Copy source code
COPY . .

# Generate optimized autoloader
RUN composer dump-autoload \
    --no-dev \
    --optimize \
    --classmap-authoritative

#############################################
# Stage 2: PHP Extensions Builder
#############################################
FROM php:8.4-fpm-alpine AS php-builder

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS \
    linux-headers \
    libzip-dev \
    icu-dev \
    postgresql-dev \
    libpng-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    libwebp-dev

# Install PHP extensions
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
        bcmath

# Install Redis extension
RUN pecl install redis-6.0.2 \
    && docker-php-ext-enable redis

#############################################
# Stage 3: Production Image
#############################################
FROM php:8.4-fpm-alpine AS production

# Install runtime dependencies only
RUN apk add --no-cache \
    libzip \
    icu-libs \
    libpq \
    libpng \
    libjpeg-turbo \
    freetype \
    libwebp

# Copy PHP extensions from builder
COPY --from=php-builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=php-builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

# Production PHP configuration
RUN mv "$PHP_INI_DIR/php.ini-production" "$PHP_INI_DIR/php.ini"

# Opcache configuration for production
RUN echo "opcache.enable=1" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.enable_cli=1" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.memory_consumption=256" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.interned_strings_buffer=16" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.max_accelerated_files=20000" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.validate_timestamps=0" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.jit=1255" >> /usr/local/etc/php/conf.d/opcache.ini \
    && echo "opcache.jit_buffer_size=256M" >> /usr/local/etc/php/conf.d/opcache.ini

# PHP-FPM configuration
RUN echo "pm = dynamic" >> /usr/local/etc/php-fpm.d/zz-docker.conf \
    && echo "pm.max_children = 50" >> /usr/local/etc/php-fpm.d/zz-docker.conf \
    && echo "pm.start_servers = 5" >> /usr/local/etc/php-fpm.d/zz-docker.conf \
    && echo "pm.min_spare_servers = 5" >> /usr/local/etc/php-fpm.d/zz-docker.conf \
    && echo "pm.max_spare_servers = 35" >> /usr/local/etc/php-fpm.d/zz-docker.conf

# Create non-root user
RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -s /bin/sh -D app

WORKDIR /app

# Copy application from composer stage
COPY --from=composer --chown=app:app /app /app

# Set permissions
RUN chown -R app:app /app

USER app

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD php-fpm-healthcheck || exit 1

EXPOSE 9000

CMD ["php-fpm"]
```

## CI-Optimized Dockerfile

```dockerfile
# Dockerfile.ci
# Optimized for CI: fast builds, includes dev dependencies

FROM php:8.4-cli-alpine AS ci

# Install system dependencies
RUN apk add --no-cache \
    git \
    unzip \
    libzip-dev \
    icu-dev \
    linux-headers \
    $PHPIZE_DEPS

# Install PHP extensions
RUN docker-php-ext-install \
    pdo_mysql \
    intl \
    zip \
    pcntl \
    bcmath

# Install Xdebug/PCOV for coverage
ARG COVERAGE_DRIVER=pcov
RUN if [ "$COVERAGE_DRIVER" = "pcov" ]; then \
        pecl install pcov && docker-php-ext-enable pcov; \
    elif [ "$COVERAGE_DRIVER" = "xdebug" ]; then \
        pecl install xdebug && docker-php-ext-enable xdebug; \
    fi

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

# Configure PHP for CI
RUN echo "memory_limit=1G" >> /usr/local/etc/php/conf.d/ci.ini \
    && echo "max_execution_time=0" >> /usr/local/etc/php/conf.d/ci.ini

WORKDIR /app

# Copy composer files first for caching
COPY composer.json composer.lock ./

# Install all dependencies including dev
RUN composer install \
    --prefer-dist \
    --no-progress \
    --no-interaction

# Copy source code
COPY . .

# Generate autoloader
RUN composer dump-autoload

# Default command
CMD ["vendor/bin/phpunit"]
```

## Development Dockerfile

```dockerfile
# Dockerfile.dev
# For local development with hot reload

FROM php:8.4-cli-alpine

# Install dependencies
RUN apk add --no-cache \
    git \
    unzip \
    libzip-dev \
    icu-dev \
    linux-headers \
    $PHPIZE_DEPS

# Install PHP extensions
RUN docker-php-ext-install \
    pdo_mysql \
    intl \
    zip \
    pcntl

# Install Xdebug for debugging
RUN pecl install xdebug \
    && docker-php-ext-enable xdebug

# Xdebug configuration
RUN echo "xdebug.mode=debug,coverage" >> /usr/local/etc/php/conf.d/xdebug.ini \
    && echo "xdebug.client_host=host.docker.internal" >> /usr/local/etc/php/conf.d/xdebug.ini \
    && echo "xdebug.start_with_request=yes" >> /usr/local/etc/php/conf.d/xdebug.ini

# Install Composer
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer

WORKDIR /app

# Don't copy files - mount volume instead
# COPY . .

CMD ["php", "-S", "0.0.0.0:8000", "-t", "public"]
```

## Docker Compose for CI

```yaml
# docker-compose.ci.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.ci
      args:
        COVERAGE_DRIVER: pcov
    volumes:
      - ./coverage:/app/coverage
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      DATABASE_URL: mysql://root:root@mysql:3306/test
      REDIS_URL: redis://redis:6379

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
```

## .dockerignore Template

```
# .dockerignore
# Git
.git
.gitignore
.gitattributes

# CI/CD
.github
.gitlab-ci.yml
Jenkinsfile

# IDE
.idea
.vscode
*.sublime-*

# Dependencies (will be installed in container)
vendor

# Tests (for production image)
tests
phpunit.xml*
.phpunit.result.cache

# Development files
docker-compose*.yml
Dockerfile*
.docker

# Documentation
docs
*.md
!README.md

# Cache and logs
var/cache
var/log
*.log

# Local configuration
.env.local
.env.*.local
*.local.php

# Static analysis
phpstan.neon
psalm.xml
.php-cs-fixer.php
deptrac.yaml

# Build artifacts
coverage
build
```

## Build Arguments

### PHP Version

```dockerfile
ARG PHP_VERSION=8.4
FROM php:${PHP_VERSION}-fpm-alpine
```

### Coverage Driver

```dockerfile
ARG COVERAGE_DRIVER=none
RUN if [ "$COVERAGE_DRIVER" = "pcov" ]; then \
        pecl install pcov && docker-php-ext-enable pcov; \
    fi
```

### Build Mode

```dockerfile
ARG APP_ENV=prod
RUN if [ "$APP_ENV" = "prod" ]; then \
        composer install --no-dev --optimize-autoloader; \
    else \
        composer install; \
    fi
```

## CI Build Commands

### GitHub Actions

```yaml
- name: Build CI image
  run: |
    docker build \
      --file Dockerfile.ci \
      --build-arg COVERAGE_DRIVER=pcov \
      --tag app:ci \
      .

- name: Run tests
  run: |
    docker run --rm \
      -v ${{ github.workspace }}/coverage:/app/coverage \
      app:ci \
      vendor/bin/phpunit --coverage-clover=/app/coverage/coverage.xml
```

### GitLab CI

```yaml
build:
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build
        --file Dockerfile.ci
        --build-arg COVERAGE_DRIVER=pcov
        --cache-from $CI_REGISTRY_IMAGE:ci
        --tag $CI_REGISTRY_IMAGE:ci
        .
    - docker push $CI_REGISTRY_IMAGE:ci
```

## Generation Instructions

1. **Analyze project:**
   - Check PHP version in composer.json
   - Identify required extensions
   - Check for framework (Symfony, Laravel)
   - Identify services (MySQL, Redis, etc.)

2. **Generate Dockerfiles:**
   - Production: Multi-stage, optimized
   - CI: Fast builds, dev dependencies
   - Development: Hot reload, debugging

3. **Optimize for caching:**
   - Copy composer files first
   - Install dependencies before source
   - Use multi-stage builds

4. **Security:**
   - Non-root user
   - Minimal base image
   - No secrets in image

## Usage

Provide:
- PHP version
- Required extensions
- Framework (optional)
- Services (MySQL, Redis, etc.)
- Target (production/ci/dev)

The generator will:
1. Create appropriate Dockerfile(s)
2. Generate .dockerignore
3. Create docker-compose.ci.yml if needed
4. Optimize for the target environment
