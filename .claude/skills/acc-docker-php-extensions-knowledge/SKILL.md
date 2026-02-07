---
name: acc-docker-php-extensions-knowledge
description: Docker PHP extensions knowledge base. Provides installation patterns for common extensions, build dependency management, and PECL usage.
---

# Docker PHP Extensions Knowledge Base

Patterns for installing, building, and managing PHP extensions in Docker containers.

## Extension Categories

| Category | Extensions | Purpose |
|----------|-----------|---------|
| **Core** | opcache, intl, mbstring, bcmath | Performance, i18n, math |
| **Database** | pdo_pgsql, pdo_mysql, pgsql, mysqli | Database connectivity |
| **Cache** | redis, apcu, memcached | Caching layers |
| **Crypto** | sodium, openssl | Encryption, hashing |
| **Image** | gd, imagick | Image processing |
| **Archive** | zip, zlib, bz2 | Compression |
| **Message** | amqp, pcntl | Queues, process control |
| **Debug** | xdebug, pcov | Debugging, coverage |
| **Serialization** | igbinary, msgpack | Fast serialization |

## Installation Methods

### Method 1: docker-php-ext-install (Built-in Extensions)

```dockerfile
# Extensions bundled with PHP source
RUN docker-php-ext-install -j$(nproc) \
    opcache \
    intl \
    pdo_pgsql \
    pdo_mysql \
    zip \
    bcmath \
    pcntl \
    sockets
```

### Method 2: docker-php-ext-configure + install

```dockerfile
# Extensions requiring configuration
RUN docker-php-ext-configure gd \
        --with-freetype \
        --with-jpeg \
        --with-webp \
    && docker-php-ext-install -j$(nproc) gd
```

### Method 3: PECL Install

```dockerfile
# Extensions from PECL repository
RUN pecl install redis-6.1.0 apcu-5.1.24 igbinary-3.2.16 \
    && docker-php-ext-enable redis apcu igbinary
```

### Method 4: Manual Compilation

```dockerfile
# For extensions not in PECL or needing custom patches
RUN curl -fsSL https://github.com/example/ext/archive/v1.0.tar.gz | tar xz \
    && cd ext-1.0 \
    && phpize \
    && ./configure \
    && make -j$(nproc) \
    && make install \
    && docker-php-ext-enable ext
```

## Alpine vs Debian Build Dependencies

| Extension | Alpine Packages | Debian Packages |
|-----------|----------------|-----------------|
| intl | `icu-dev` | `libicu-dev` |
| pdo_pgsql | `libpq-dev` | `libpq-dev` |
| pdo_mysql | (none) | (none) |
| gd | `freetype-dev libjpeg-turbo-dev libpng-dev libwebp-dev` | `libfreetype6-dev libjpeg62-turbo-dev libpng-dev libwebp-dev` |
| zip | `libzip-dev` | `libzip-dev` |
| imagick | `imagemagick-dev` | `libmagickwand-dev` |
| amqp | `rabbitmq-c-dev` | `librabbitmq-dev` |
| memcached | `libmemcached-dev zlib-dev` | `libmemcached-dev zlib1g-dev` |
| sodium | `libsodium-dev` | `libsodium-dev` |
| bz2 | `bzip2-dev` | `libbz2-dev` |
| xsl | `libxslt-dev` | `libxslt1-dev` |
| ldap | `openldap-dev` | `libldap2-dev` |
| gmp | `gmp-dev` | `libgmp-dev` |
| imap | `imap-dev krb5-dev` | `libc-client-dev libkrb5-dev` |

## Runtime vs Build Dependencies Pattern

```dockerfile
FROM php:8.4-fpm-alpine AS production

# 1. Install build dependencies (virtual package for easy removal)
RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        icu-dev \
        libpq-dev \
        libzip-dev \
        freetype-dev \
        libjpeg-turbo-dev \
        libpng-dev \
        rabbitmq-c-dev \
    \
# 2. Install and configure extensions
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        intl \
        pdo_pgsql \
        zip \
        gd \
        opcache \
        bcmath \
        pcntl \
        sockets \
    \
# 3. Install PECL extensions
    && pecl install redis apcu amqp igbinary \
    && docker-php-ext-enable redis apcu amqp igbinary \
    \
# 4. Remove build dependencies (keep runtime libs)
    && apk del .build-deps

# 5. Install runtime-only libraries
RUN apk add --no-cache \
    icu-libs \
    libpq \
    libzip \
    freetype \
    libjpeg-turbo \
    libpng \
    rabbitmq-c
```

## Extension Builder Stage Pattern

```dockerfile
# Dedicated stage for compiling extensions (reusable across images)
FROM php:8.4-fpm-alpine AS ext-builder

RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        icu-dev \
        libpq-dev \
        libzip-dev \
    && docker-php-ext-install -j$(nproc) intl pdo_pgsql zip opcache bcmath \
    && pecl install redis apcu \
    && docker-php-ext-enable redis apcu \
    && apk del .build-deps

# Production stage copies only compiled artifacts
FROM php:8.4-fpm-alpine AS production

COPY --from=ext-builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=ext-builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/

RUN apk add --no-cache icu-libs libpq libzip
```

## Framework Extension Combinations

### Symfony Stack

```dockerfile
RUN docker-php-ext-install -j$(nproc) \
    intl \           # Translation, validation, routing
    pdo_pgsql \      # Doctrine DBAL (PostgreSQL)
    opcache \        # Performance
    zip \            # Composer, file handling
    bcmath \         # Precise math (money)
    pcntl \          # Messenger async workers
    sockets          # Messenger AMQP transport

RUN pecl install redis apcu amqp \
    && docker-php-ext-enable redis apcu amqp
```

### Laravel Stack

```dockerfile
RUN docker-php-ext-install -j$(nproc) \
    pdo_mysql \      # Eloquent (MySQL)
    opcache \        # Performance
    zip \            # File handling
    bcmath \         # Precise math
    pcntl \          # Horizon workers
    exif             # Image metadata

RUN pecl install redis igbinary \
    && docker-php-ext-enable redis igbinary
```

### API Platform / High-Load

```dockerfile
RUN docker-php-ext-install -j$(nproc) \
    intl \
    pdo_pgsql \
    opcache \
    bcmath \
    pcntl \
    sockets

RUN pecl install redis apcu amqp igbinary msgpack \
    && docker-php-ext-enable redis apcu amqp igbinary msgpack
```

## OPcache Configuration for Production

```ini
; /usr/local/etc/php/conf.d/opcache.ini
opcache.enable=1
opcache.enable_cli=0
opcache.memory_consumption=256
opcache.interned_strings_buffer=32
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.save_comments=1
opcache.jit=tracing
opcache.jit_buffer_size=128M
```

```dockerfile
COPY docker/php/opcache.ini /usr/local/etc/php/conf.d/opcache.ini
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| `cannot find -licu` | Missing icu-dev | `apk add icu-dev` or `apt install libicu-dev` |
| `pecl install fails` | Missing $PHPIZE_DEPS | `apk add $PHPIZE_DEPS` |
| Extension loads but segfaults | Alpine musl incompatibility | Switch to Debian base |
| `Class 'Redis' not found` | Extension not enabled | `docker-php-ext-enable redis` |
| `iconv(): Wrong encoding` | Alpine musl iconv | Install `gnu-libiconv` |
| Slow builds | Sequential compilation | Use `-j$(nproc)` and BuildKit cache |

## References

For the full extensions matrix with all dependencies, see `references/extensions-matrix.md`.
For base image selection, see `acc-docker-base-images-knowledge`.
