---
name: acc-analyze-docker-build-errors
description: Analyzes Docker build errors for PHP projects. Identifies extension compilation failures, dependency issues, memory limits, and provides fixes.
---

# Docker Build Error Analysis

Analyze Dockerfile and build logs for PHP project build failures and provide targeted fixes.

## Common Build Error Patterns

| Error Category | Symptom | Root Cause |
|----------------|---------|------------|
| Extension compilation | `configure: error: ...` | Missing dev packages |
| Package not found | `E: Unable to locate package` | Wrong package name for base image |
| Permission denied | `COPY failed: permission denied` | File ownership or Docker socket |
| Memory exhausted | `Allowed memory size exhausted` | Composer or PHP memory limit |
| Context too large | `sending build context... 2GB` | Missing .dockerignore |
| Multi-stage failure | `COPY --from=builder ... not found` | Wrong stage name or path |

## Detection Patterns

### 1. Extension Compilation Failure

```dockerfile
# ERROR: gd extension on Alpine
RUN docker-php-ext-install gd
# configure: error: png.h not found

# FIX (Alpine):
RUN apk add --no-cache libpng-dev libjpeg-turbo-dev freetype-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) gd

# FIX (Debian):
RUN apt-get update && apt-get install -y libpng-dev libjpeg62-turbo-dev libfreetype6-dev \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) gd
```

### 2. Extension Dependencies by Base Image

| Extension | Alpine Packages | Debian Packages |
|-----------|----------------|-----------------|
| gd | `libpng-dev libjpeg-turbo-dev freetype-dev` | `libpng-dev libjpeg62-turbo-dev libfreetype6-dev` |
| intl | `icu-dev` | `libicu-dev` |
| zip | `libzip-dev` | `libzip-dev` |
| pdo_pgsql | `postgresql-dev` | `libpq-dev` |
| soap | `libxml2-dev` | `libxml2-dev` |
| xsl | `libxslt-dev` | `libxslt1-dev` |
| imagick | `imagemagick-dev` (PECL) | `libmagickwand-dev` (PECL) |

### 3. Memory Exhausted During Build

```dockerfile
# ERROR: Composer runs out of memory
RUN composer install
# PHP Fatal error: Allowed memory size of 134217728 bytes exhausted

# FIX: Increase memory limit for Composer
RUN php -d memory_limit=-1 /usr/bin/composer install --no-dev --optimize-autoloader
```

### 4. Context Too Large

```dockerignore
# Required .dockerignore entries
.git
node_modules
vendor
var/cache
var/log
docker-compose*.yml
.env.local
tests
docs
```

### 5. Alpine Build Essentials

```dockerfile
RUN apk add --no-cache --virtual .build-deps \
    $PHPIZE_DEPS build-base autoconf \
    && pecl install redis \
    && docker-php-ext-enable redis \
    && apk del .build-deps
```

## Grep Patterns

```bash
# Find Dockerfiles with extension installs
Grep: "docker-php-ext-install" --glob "**/Dockerfile*"

# Find missing dev package installs before ext-install
Grep: "ext-install.*(gd|intl|zip|pdo_pgsql|imagick)" --glob "**/Dockerfile*"

# Find unrestricted memory Composer runs
Grep: "composer install|composer update" --glob "**/Dockerfile*"

# Find large base images
Grep: "FROM php:[0-9.]+-apache|FROM php:[0-9.]+-cli$" --glob "**/Dockerfile*"

# Check for .dockerignore existence
Glob: "**/.dockerignore"
```

## Root Cause Analysis

### Build Fails on CI but Works Locally

1. **Different Docker version** -- check `docker version` output
2. **No BuildKit** -- CI may not have `DOCKER_BUILDKIT=1`
3. **Cache differences** -- CI has cold cache, local has warm
4. **Platform mismatch** -- local ARM (M1/M2), CI AMD64

### Extension Fails Only on Alpine

1. **musl vs glibc** -- some extensions require glibc patches
2. **Package naming** -- Alpine uses different package names
3. **Missing build tools** -- add `build-base` for compilation

## Fix Templates

### Alpine

```dockerfile
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS <DEV_PACKAGES> \
    && docker-php-ext-configure <EXT> <OPTIONS> \
    && docker-php-ext-install -j$(nproc) <EXT> \
    && apk del .build-deps \
    && apk add --no-cache <RUNTIME_PACKAGES>
```

### Debian

```dockerfile
RUN apt-get update \
    && apt-get install -y --no-install-recommends <DEV_PACKAGES> \
    && docker-php-ext-configure <EXT> <OPTIONS> \
    && docker-php-ext-install -j$(nproc) <EXT> \
    && apt-get purge -y --auto-remove <DEV_ONLY_PACKAGES> \
    && rm -rf /var/lib/apt/lists/*
```

## Severity Classification

| Pattern | Severity | Impact |
|---------|----------|--------|
| Extension compile failure | Critical | Build completely blocked |
| Memory exhausted | Critical | Build cannot complete |
| Package not found | Major | Build blocked, easy fix |
| Context too large | Major | Slow builds, wasted bandwidth |
| COPY path error | Minor | Build blocked, trivial fix |

## Output Format

```markdown
### Build Error: [Category]

**Severity:** Critical/Major/Minor
**Stage:** `FROM ... AS <stage>`
**Line:** Dockerfile:line

**Error Message:**
<exact error from build log>

**Root Cause:**
[Explanation of why the build fails]

**Fix:**
```dockerfile
// Corrected Dockerfile instruction
```

**Prevention:**
[How to avoid this error in future builds]
```
