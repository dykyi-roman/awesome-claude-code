---
name: acc-analyze-docker-image-size
description: Analyzes Docker image size for PHP projects. Identifies bloated layers, unnecessary packages, and provides size reduction strategies.
---

# Docker Image Size Analysis

Analyze Docker images for PHP projects to identify bloat sources and provide size reduction strategies.

## Expected Size Ranges

| Base Image | Minimal | Typical | Bloated |
|-----------|---------|---------|---------|
| php:8.4-fpm-alpine | 30-50 MB | 80-120 MB | 200+ MB |
| php:8.4-fpm (Debian) | 150-200 MB | 250-350 MB | 500+ MB |
| php:8.4-cli-alpine | 25-40 MB | 60-100 MB | 180+ MB |

## Common Bloat Sources

### 1. Build Dependencies Not Cleaned

```dockerfile
# BLOATED: Dev packages remain in final image
RUN apk add --no-cache $PHPIZE_DEPS icu-dev libzip-dev \
    && docker-php-ext-install intl zip

# OPTIMIZED: Remove build deps after compilation
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS icu-dev libzip-dev \
    && docker-php-ext-install intl zip \
    && apk del .build-deps \
    && apk add --no-cache icu-libs libzip
```

### 2. Vendor with Dev Dependencies

```dockerfile
# BLOATED: Includes dev dependencies (+30-80MB)
RUN composer install

# OPTIMIZED: No dev dependencies, optimized autoloader
RUN composer install --no-dev --no-scripts --prefer-dist --optimize-autoloader
```

### 3. Full Debian Instead of Alpine

```dockerfile
# BLOATED: Full Debian base (~150MB base)
FROM php:8.4-fpm

# OPTIMIZED: Alpine base (~30MB base)
FROM php:8.4-fpm-alpine
```

### 4. Package Manager Cache

```dockerfile
# BLOATED: apt cache retained (~30-50MB)
RUN apt-get update && apt-get install -y libicu-dev

# OPTIMIZED: Clean apt cache in same layer
RUN apt-get update && apt-get install -y --no-install-recommends libicu-dev \
    && rm -rf /var/lib/apt/lists/*
```

### 5. Missing .dockerignore

```dockerignore
.git
node_modules
vendor
tests
docs
var/cache
var/log
docker-compose*.yml
.env.local
*.md
Makefile
```

## Size Estimation by Component

| Component | Typical Size | Notes |
|-----------|-------------|-------|
| Alpine base | 5-8 MB | Minimal Linux |
| Debian slim base | 70-90 MB | More packages available |
| PHP runtime | 25-40 MB | Core PHP binaries |
| PHP extensions (5-8) | 10-30 MB | Depends on extensions |
| Composer vendor (no-dev) | 20-60 MB | Depends on packages |
| Composer vendor (with-dev) | 50-150 MB | PHPUnit, etc. |
| Application code | 1-10 MB | Source files only |
| Build dependencies | 50-200 MB | Must be cleaned |

## Multi-Stage Build (Best Practice)

```dockerfile
FROM php:8.4-fpm-alpine AS builder
RUN apk add --no-cache --virtual .build-deps $PHPIZE_DEPS icu-dev libzip-dev \
    && docker-php-ext-install intl zip opcache \
    && apk del .build-deps
COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist --optimize-autoloader

FROM php:8.4-fpm-alpine AS runtime
RUN apk add --no-cache icu-libs libzip
COPY --from=builder /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=builder /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
COPY --from=builder /var/www/vendor /var/www/vendor
COPY . /var/www/
```

## Grep Patterns

```bash
# Find base images used
Grep: "^FROM " --glob "**/Dockerfile*"

# Find missing cache cleanup
Grep: "apt-get install" --glob "**/Dockerfile*"
Grep: "apk add(?!.*--no-cache)" --glob "**/Dockerfile*"

# Find composer install without --no-dev
Grep: "composer install(?!.*--no-dev)" --glob "**/Dockerfile*"

# Find COPY . (copies everything)
Grep: "^COPY \. " --glob "**/Dockerfile*"

# Check for .dockerignore
Glob: "**/.dockerignore"

# Find multi-stage builds
Grep: "^FROM.*AS " --glob "**/Dockerfile*"
```

## Reduction Impact

| Strategy | Size Reduction | Effort |
|----------|---------------|--------|
| Alpine instead of Debian | 100-150 MB | Low |
| Multi-stage build | 50-200 MB | Medium |
| Remove build deps | 50-200 MB | Low |
| --no-dev Composer | 30-80 MB | Low |
| Clean apt/apk cache | 20-50 MB | Low |
| .dockerignore | 10-500 MB | Low |

## Severity Classification

| Pattern | Severity | Typical Waste |
|---------|----------|---------------|
| No multi-stage, build deps remain | Critical | 100-300 MB |
| No .dockerignore, .git copied | Critical | 50-500 MB |
| Debian instead of Alpine (no reason) | Major | 100-150 MB |
| Composer with dev dependencies | Major | 30-80 MB |
| APT/APK cache not cleaned | Minor | 20-50 MB |

## Output Format

```markdown
### Image Size Issue: [Category]

**Severity:** Critical/Major/Minor
**Current Size:** X MB
**Estimated Savings:** Y MB
**Layer:** Dockerfile:line

**Issue:**
[Description of the bloat source]

**Current:**
```dockerfile
// Current Dockerfile instruction
```

**Optimized:**
```dockerfile
// Optimized Dockerfile instruction
```

**Expected Size After Fix:**
Before: X MB -> After: Z MB (saved Y MB)
```
