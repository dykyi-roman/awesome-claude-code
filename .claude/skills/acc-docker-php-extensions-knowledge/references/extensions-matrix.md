# PHP Extensions Installation Matrix

Comprehensive reference for installing PHP extensions in Docker containers across Alpine and Debian bases.

## Core Extensions (docker-php-ext-install)

| Extension | Alpine Build Deps | Debian Build Deps | Install Command | Runtime Deps (Alpine) | Runtime Deps (Debian) |
|-----------|------------------|-------------------|-----------------|----------------------|----------------------|
| opcache | (none) | (none) | `docker-php-ext-install opcache` | (none) | (none) |
| intl | `icu-dev` | `libicu-dev` | `docker-php-ext-install intl` | `icu-libs` | `libicu72` |
| pdo_pgsql | `libpq-dev` | `libpq-dev` | `docker-php-ext-install pdo_pgsql` | `libpq` | `libpq5` |
| pdo_mysql | (none) | (none) | `docker-php-ext-install pdo_mysql` | (none) | (none) |
| pgsql | `libpq-dev` | `libpq-dev` | `docker-php-ext-install pgsql` | `libpq` | `libpq5` |
| mysqli | (none) | (none) | `docker-php-ext-install mysqli` | (none) | (none) |
| zip | `libzip-dev` | `libzip-dev` | `docker-php-ext-install zip` | `libzip` | `libzip4` |
| bcmath | (none) | (none) | `docker-php-ext-install bcmath` | (none) | (none) |
| pcntl | (none) | (none) | `docker-php-ext-install pcntl` | (none) | (none) |
| sockets | (none) | (none) | `docker-php-ext-install sockets` | (none) | (none) |
| exif | (none) | (none) | `docker-php-ext-install exif` | (none) | (none) |
| calendar | (none) | (none) | `docker-php-ext-install calendar` | (none) | (none) |
| gettext | `gettext-dev` | `gettext` | `docker-php-ext-install gettext` | `libintl` | `gettext` |
| soap | `libxml2-dev` | `libxml2-dev` | `docker-php-ext-install soap` | `libxml2` | `libxml2` |
| xsl | `libxslt-dev` | `libxslt1-dev` | `docker-php-ext-install xsl` | `libxslt` | `libxslt1.1` |
| bz2 | `bzip2-dev` | `libbz2-dev` | `docker-php-ext-install bz2` | `libbz2` | `libbz2-1.0` |
| gmp | `gmp-dev` | `libgmp-dev` | `docker-php-ext-install gmp` | `gmp` | `libgmp10` |
| ldap | `openldap-dev` | `libldap2-dev` | `docker-php-ext-install ldap` | `libldap` | `libldap-2.5-0` |
| imap | `imap-dev krb5-dev` | `libc-client-dev libkrb5-dev` | `docker-php-ext-configure imap --with-kerberos --with-imap-ssl && docker-php-ext-install imap` | `c-client krb5-libs` | `libc-client2007e libkrb5-3` |
| tidy | `tidyhtml-dev` | `libtidy-dev` | `docker-php-ext-install tidy` | `tidyhtml-libs` | `libtidy5deb1` |
| sodium | `libsodium-dev` | `libsodium-dev` | `docker-php-ext-install sodium` | `libsodium` | `libsodium23` |

## Extensions Requiring Configuration

| Extension | Configure Flags | Alpine Build Deps | Debian Build Deps |
|-----------|----------------|-------------------|-------------------|
| gd | `--with-freetype --with-jpeg --with-webp` | `freetype-dev libjpeg-turbo-dev libpng-dev libwebp-dev` | `libfreetype6-dev libjpeg62-turbo-dev libpng-dev libwebp-dev` |
| gd (minimal) | `--with-jpeg` | `libjpeg-turbo-dev libpng-dev` | `libjpeg62-turbo-dev libpng-dev` |
| imap | `--with-kerberos --with-imap-ssl` | `imap-dev krb5-dev openssl-dev` | `libc-client-dev libkrb5-dev` |
| ldap | `--with-libdir=lib/x86_64-linux-gnu` (Debian only) | `openldap-dev` | `libldap2-dev` |

## PECL Extensions

| Extension | PECL Package | Install Command | Alpine Deps | Debian Deps | Purpose |
|-----------|-------------|-----------------|-------------|-------------|---------|
| redis | `redis` | `pecl install redis` | (none) | (none) | Redis client |
| apcu | `apcu` | `pecl install apcu` | (none) | (none) | Userland cache |
| xdebug | `xdebug` | `pecl install xdebug` | `linux-headers` | (none) | Debug/profiling |
| pcov | `pcov` | `pecl install pcov` | (none) | (none) | Code coverage |
| imagick | `imagick` | `pecl install imagick` | `imagemagick-dev` | `libmagickwand-dev` | ImageMagick |
| amqp | `amqp` | `pecl install amqp` | `rabbitmq-c-dev` | `librabbitmq-dev` | RabbitMQ |
| igbinary | `igbinary` | `pecl install igbinary` | (none) | (none) | Fast serialization |
| msgpack | `msgpack` | `pecl install msgpack` | (none) | (none) | MessagePack |
| memcached | `memcached` | `pecl install memcached` | `libmemcached-dev zlib-dev` | `libmemcached-dev zlib1g-dev` | Memcached client |
| mongodb | `mongodb` | `pecl install mongodb` | `openssl-dev` | `libssl-dev` | MongoDB driver |
| protobuf | `protobuf` | `pecl install protobuf` | (none) | (none) | Protocol Buffers |
| grpc | `grpc` | `pecl install grpc` | `linux-headers zlib-dev` | `zlib1g-dev` | gRPC client |
| swoole | `swoole` | `pecl install swoole` | `openssl-dev curl-dev` | `libssl-dev libcurl4-openssl-dev` | Async server |
| uuid | `uuid` | `pecl install uuid` | `util-linux-dev` | `uuid-dev` | UUID generation |
| ds | `ds` | `pecl install ds` | (none) | (none) | Data structures |
| decimal | `decimal` | `pecl install decimal` | `mpdecimal-dev` | `libmpdec-dev` | Arbitrary precision |

## Version Pinning for PECL

```dockerfile
# Pin specific versions for reproducibility
RUN pecl install \
    redis-6.1.0 \
    apcu-5.1.24 \
    igbinary-3.2.16 \
    amqp-2.1.2 \
    && docker-php-ext-enable redis apcu igbinary amqp
```

## Enabling Extensions

```dockerfile
# After pecl install, always enable
RUN docker-php-ext-enable redis apcu igbinary

# Verify extensions are loaded
RUN php -m | grep -i redis
```

## Quick Copy-Paste Blocks

### Minimal Web App (Alpine)

```dockerfile
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS icu-dev libpq-dev libzip-dev \
    && docker-php-ext-install -j$(nproc) intl pdo_pgsql zip opcache bcmath \
    && pecl install redis apcu && docker-php-ext-enable redis apcu \
    && apk del .build-deps \
    && apk add --no-cache icu-libs libpq libzip
```

### Full Stack (Alpine)

```dockerfile
RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS icu-dev libpq-dev libzip-dev freetype-dev \
        libjpeg-turbo-dev libpng-dev rabbitmq-c-dev imagemagick-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) intl pdo_pgsql zip gd opcache bcmath pcntl sockets \
    && pecl install redis apcu amqp igbinary imagick \
    && docker-php-ext-enable redis apcu amqp igbinary imagick \
    && apk del .build-deps \
    && apk add --no-cache icu-libs libpq libzip freetype libjpeg-turbo libpng rabbitmq-c imagemagick
```
