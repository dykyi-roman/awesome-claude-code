---
name: acc-create-dockerfile-dev
description: Generates development Dockerfiles for PHP projects. Creates images with Xdebug, hot reload, and development tools.
---

# Development Dockerfile Generator

Generates development-optimized Dockerfiles for PHP projects with Xdebug integration, hot reload, and developer tools.

## Generated Files

```
Dockerfile.dev            # Development image with debugging tools
docker-compose.dev.yml    # Development stack with volume mounts
```

## Generation Instructions

1. **Analyze project:**
   - Read `composer.json` for PHP version and extensions
   - Detect framework (Symfony/Laravel) for specific dev tools
   - Check for existing Docker configuration

2. **Generate Dockerfile.dev:**
   - Single-stage (no multi-stage needed for dev)
   - Include Xdebug with full configuration
   - Include development tools (git, unzip, vim, curl)
   - Do NOT COPY source code (use volume mounts)
   - Use development PHP config (display_errors=On)

3. **Generate docker-compose.dev.yml:**
   - Volume mount source code
   - Expose debug ports
   - Configure environment for IDE integration

## Development Dockerfile

```dockerfile
# Dockerfile.dev
# Development image with Xdebug and dev tools
# Do NOT use in production

FROM php:8.4-fpm-alpine

# Install system dependencies and dev tools
RUN apk add --no-cache \
    git \
    unzip \
    vim \
    curl \
    wget \
    bash \
    make \
    libzip-dev \
    icu-dev \
    linux-headers \
    postgresql-dev \
    libpng-dev \
    libjpeg-turbo-dev \
    freetype-dev \
    libwebp-dev \
    libxml2-dev \
    oniguruma-dev \
    rabbitmq-c-dev \
    $PHPIZE_DEPS

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
        bcmath \
        sockets \
        mbstring

# Install PECL extensions
RUN pecl install redis-6.1.0 \
    && pecl install amqp-2.1.2 \
    && docker-php-ext-enable redis amqp

# Install Xdebug
RUN pecl install xdebug-3.4.0 \
    && docker-php-ext-enable xdebug

# Install Composer
COPY --from=composer:2.8 /usr/bin/composer /usr/bin/composer

# Development PHP configuration
COPY <<'EOF' /usr/local/etc/php/conf.d/dev-php.ini
display_errors=On
display_startup_errors=On
error_reporting=E_ALL
log_errors=On
error_log=/proc/self/fd/2
memory_limit=512M
max_execution_time=0
max_input_time=-1
post_max_size=100M
upload_max_filesize=100M
realpath_cache_size=4096K
realpath_cache_ttl=600
session.use_strict_mode=1
EOF

# OPcache development configuration (validate on every request)
COPY <<'EOF' /usr/local/etc/php/conf.d/dev-opcache.ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=1
opcache.revalidate_freq=0
opcache.jit=disable
EOF

# Xdebug configuration
COPY <<'EOF' /usr/local/etc/php/conf.d/dev-xdebug.ini
[xdebug]
xdebug.mode=debug,coverage,develop
xdebug.client_host=host.docker.internal
xdebug.client_port=9003
xdebug.start_with_request=trigger
xdebug.discover_client_host=false
xdebug.idekey=PHPSTORM
xdebug.max_nesting_level=512
xdebug.var_display_max_depth=5
xdebug.var_display_max_data=512
xdebug.log=/tmp/xdebug.log
xdebug.log_level=3
EOF

# PHP-FPM development configuration
COPY <<'EOF' /usr/local/etc/php-fpm.d/zz-dev.conf
[www]
pm = dynamic
pm.max_children = 10
pm.start_servers = 2
pm.min_spare_servers = 1
pm.max_spare_servers = 5
pm.max_requests = 500
pm.status_path = /status
ping.path = /ping
access.log = /proc/self/fd/2
catch_workers_output = yes
decorate_workers_output = no
EOF

# Create development user matching host UID
ARG HOST_UID=1000
ARG HOST_GID=1000

RUN addgroup -g ${HOST_GID} dev \
    && adduser -u ${HOST_UID} -G dev -s /bin/bash -D dev \
    && mkdir -p /home/dev/.composer \
    && chown -R dev:dev /home/dev

WORKDIR /app

# Do NOT copy source code — use volume mounts instead
# Source is mounted via docker-compose.dev.yml

# Set ownership for working directory
RUN chown -R dev:dev /app

USER dev

# Composer cache in named volume
ENV COMPOSER_HOME=/home/dev/.composer

EXPOSE 9000

CMD ["php-fpm"]
```

## Xdebug IDE Configuration

### PhpStorm Setup

1. **Settings > PHP > Debug:**
   - Debug port: `9003`
   - Accept external connections: checked

2. **Settings > PHP > Servers:**
   - Name: `docker`
   - Host: `localhost`
   - Port: `80`
   - Debugger: Xdebug
   - Path mappings: `/path/to/project` -> `/app`

3. **Trigger debugging:**
   - Use browser extension (Xdebug Helper)
   - Or set cookie: `XDEBUG_TRIGGER=PHPSTORM`

### VS Code Setup

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Listen for Xdebug",
            "type": "php",
            "request": "launch",
            "port": 9003,
            "pathMappings": {
                "/app": "${workspaceFolder}"
            },
            "hostname": "0.0.0.0"
        }
    ]
}
```

## Docker Compose Development Stack

```yaml
# docker-compose.dev.yml
services:
  php:
    build:
      context: .
      dockerfile: Dockerfile.dev
      args:
        HOST_UID: ${HOST_UID:-1000}
        HOST_GID: ${HOST_GID:-1000}
    volumes:
      # Mount source code
      - .:/app:cached
      # Exclude vendor (use container's vendor)
      - vendor:/app/vendor
      # Composer cache
      - composer-cache:/home/dev/.composer
    environment:
      PHP_IDE_CONFIG: "serverName=docker"
      XDEBUG_MODE: "debug,coverage"
      XDEBUG_CONFIG: "client_host=host.docker.internal"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    ports:
      - "9003:9003"
    depends_on:
      - nginx

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "8080:80"
    volumes:
      - .:/app:cached
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - php

volumes:
  vendor:
  composer-cache:
```

## Useful Development Commands

```bash
# Build development image
docker compose -f docker-compose.dev.yml build

# Start development stack
docker compose -f docker-compose.dev.yml up -d

# Install dependencies inside container
docker compose -f docker-compose.dev.yml exec php composer install

# Run tests with coverage
docker compose -f docker-compose.dev.yml exec php vendor/bin/phpunit --coverage-html coverage

# Enable/disable Xdebug on-the-fly
docker compose -f docker-compose.dev.yml exec php bash -c \
    "echo 'xdebug.mode=off' > /usr/local/etc/php/conf.d/99-xdebug-toggle.ini && kill -USR2 1"

# PHP shell inside container
docker compose -f docker-compose.dev.yml exec php php -a

# Watch logs
docker compose -f docker-compose.dev.yml logs -f php
```

## Hot Reload Notes

- Source code is volume-mounted; changes reflect immediately
- OPcache `validate_timestamps=1` with `revalidate_freq=0` detects file changes on every request
- Xdebug `start_with_request=trigger` avoids debug overhead unless explicitly triggered
- Vendor directory uses a named volume to avoid slow host filesystem I/O on macOS

## Usage

Provide:
- PHP version (default: 8.4)
- Required extensions (from composer.json)
- IDE (PhpStorm/VS Code) for Xdebug config
- Host UID/GID for permission mapping

The generator will:
1. Create Dockerfile.dev with all dev tools
2. Configure Xdebug for your IDE
3. Generate docker-compose.dev.yml with volume mounts
4. Include helpful development commands
