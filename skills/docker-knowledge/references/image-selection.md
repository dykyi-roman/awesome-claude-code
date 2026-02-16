# PHP Docker Base Image Selection

Comprehensive guide for choosing the right PHP Docker base image per environment and use case.

## Alpine vs Debian Comparison

| Criteria | Alpine (`-alpine`) | Debian (`-bookworm`) |
|----------|-------------------|---------------------|
| Base size | ~5MB | ~120MB |
| PHP image size | ~50MB | ~150MB |
| C library | musl libc | glibc |
| Package manager | apk | apt-get |
| Shell | ash (BusyBox) | bash |
| Package availability | Limited | Extensive |
| Security updates | Fast, minimal | Regular, comprehensive |
| DNS resolution | Different behavior (musl) | Standard behavior |
| Compilation compat | May need patches | Broadly compatible |
| Debug tools | Minimal | Rich out of box |

### musl vs glibc Implications for PHP

```
Known musl issues:
- DNS resolution: musl uses different resolver (may cause DNS issues in Kubernetes)
- iconv: Alpine uses gnu-libiconv replacement (some encoding edge cases)
- Locale: musl has limited locale support (LC_COLLATE differences)
- Memory allocator: Different allocation strategy (can affect long-running FPM)
- PCRE JIT: Works but performance characteristics differ
```

**Recommendation:** Use Alpine for production (smaller attack surface). Use Debian if you encounter musl-specific issues or need specific native extensions.

## Image Variants

### php:X.X-fpm

```
Purpose: PHP-FPM process manager for serving web requests behind Nginx/Caddy
Includes: PHP-FPM, php.ini, php-fpm.conf
Exposes: Port 9000 (FastCGI)
Best for: Production web applications
```

### php:X.X-cli

```
Purpose: PHP CLI for scripts, workers, cron jobs, CI pipelines
Includes: PHP CLI binary, php.ini
No daemon: Exits after script completes
Best for: Queue workers, cron containers, CLI tools, CI/CD
```

### php:X.X-apache

```
Purpose: PHP with Apache mod_php built in
Includes: Apache httpd, mod_php, php.ini
Exposes: Port 80
Best for: Simple deployments, legacy apps, quick prototyping
```

### Comparison Table

| Variant | Web Serving | Workers | CI | Production | Simplicity |
|---------|------------|---------|-----|------------|------------|
| fpm | Best | No | No | Best | Medium |
| cli | No | Best | Best | Workers | Simple |
| apache | Good | No | No | Acceptable | Simplest |

## Version Pinning Strategies

### Full Pin (Most Reproducible)

```dockerfile
# Pins PHP version + patch + Alpine version
FROM php:8.4.2-fpm-alpine3.19
```

- Pros: Fully reproducible builds, no surprise changes
- Cons: Must manually update for security patches
- Use: Production images with controlled update pipeline

### Minor Pin (Recommended)

```dockerfile
# Pins PHP minor version, receives patch updates
FROM php:8.4-fpm-alpine
```

- Pros: Receives security patches automatically on rebuild
- Cons: Patch version may change between builds
- Use: Most projects with regular rebuild schedule

### Major Pin (Avoid)

```dockerfile
# Pins major only — dangerous
FROM php:8-fpm-alpine
```

- Pros: Always latest PHP 8.x
- Cons: Minor version jumps may break code
- Use: Never in production

### Latest Tag (Never Use)

```dockerfile
# NEVER do this
FROM php:latest
```

- Pros: None
- Cons: Completely unpredictable, may change PHP major version
- Use: Never

## Recommended Images per Environment

### Development

```dockerfile
# Debian-based for better debugging tools and compatibility
FROM php:8.4-fpm

# Install dev dependencies and Xdebug
RUN apt-get update && apt-get install -y \
    git unzip libzip-dev libicu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && pecl install xdebug \
    && docker-php-ext-enable xdebug \
    && rm -rf /var/lib/apt/lists/*
```

### CI/CD Pipeline

```dockerfile
# CLI-based Alpine for speed
FROM php:8.4-cli-alpine

RUN apk add --no-cache git unzip libzip-dev icu-dev linux-headers \
    && docker-php-ext-install zip intl pdo_mysql \
    && pecl install pcov \
    && docker-php-ext-enable pcov

COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
```

### Production Web

```dockerfile
# FPM Alpine — minimal and secure
FROM php:8.4-fpm-alpine

RUN apk add --no-cache libzip-dev icu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && apk del --no-cache $PHPIZE_DEPS
```

### Queue Workers

```dockerfile
# CLI Alpine — no FPM overhead
FROM php:8.4-cli-alpine

RUN apk add --no-cache libzip-dev icu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache pcntl
```

## Official vs Custom Base Images

### Official Images (Recommended)

```
Source: hub.docker.com/_/php
Maintained by: Docker Official Images team
Updates: Regular security patches
Trust: Verified, signed, scanned
```

| Pros | Cons |
|------|------|
| Well-maintained | Generic — no project-specific extensions |
| Security patches | Larger build time if many extensions needed |
| Community-tested | May not have latest PHP immediately |
| Docker Hub verified | No custom configuration baked in |

### Custom Base Images

```dockerfile
# Example: Organization base image
FROM php:8.4-fpm-alpine AS company-php-base

RUN apk add --no-cache libzip-dev icu-dev libpq-dev \
    && docker-php-ext-install zip intl pdo_pgsql opcache \
    && apk del --no-cache $PHPIZE_DEPS

COPY php.ini /usr/local/etc/php/php.ini
COPY php-fpm.conf /usr/local/etc/php-fpm.d/www.conf

RUN addgroup -g 1000 app && adduser -u 1000 -G app -D app
```

| Pros | Cons |
|------|------|
| Pre-configured extensions | Must maintain and update |
| Consistent across projects | Single point of failure |
| Faster project builds | Requires private registry |
| Company standards enforced | Team must understand the base |

### Decision Matrix

| Factor | Use Official | Use Custom |
|--------|-------------|------------|
| Team size | Small (<5) | Large (5+) |
| Projects | Few (1-3) | Many (5+) |
| Extensions | Minimal | Same set everywhere |
| Compliance | Standard | Strict requirements |
| Registry | Docker Hub | Private (ECR, GCR, ACR) |

## Extension Installation Reference

### Common Extensions by Category

| Category | Extensions | Alpine Dependencies |
|----------|-----------|-------------------|
| Database | pdo_mysql, pdo_pgsql | libpq-dev |
| Cache | redis (PECL) | — |
| Internationalization | intl | icu-dev |
| Compression | zip | libzip-dev |
| Images | gd | libpng-dev, libjpeg-turbo-dev |
| Process | pcntl | — |
| Sockets | sockets | — |
| Performance | opcache | — (built-in) |
| Debugging | xdebug (PECL) | linux-headers |
| Coverage | pcov (PECL) | linux-headers |

### Install Pattern

```dockerfile
# 1. Install system dependencies
# 2. Install PHP extensions
# 3. Clean up build dependencies
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS libzip-dev icu-dev \
    && apk add --no-cache libzip icu-libs \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && apk del .build-deps
```

The `--virtual .build-deps` pattern groups temporary build packages for clean removal, keeping the final image small.
