---
name: acc-optimize-docker-layers
description: Analyzes and optimizes Docker layer caching for PHP projects. Identifies layer ordering issues, cache invalidation problems, and provides recommendations for faster builds.
---

# Docker Layer Optimization

Analyzes Dockerfiles and provides optimization recommendations for faster CI builds.

## Layer Caching Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER LAYER CACHE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Layer 1: FROM php:8.4-alpine          ✓ Cached (base image)   │
│      ↓                                                          │
│  Layer 2: RUN apk add ...              ✓ Cached (system deps)  │
│      ↓                                                          │
│  Layer 3: COPY composer.json ...       ✓ Cached (if unchanged) │
│      ↓                                                          │
│  Layer 4: RUN composer install         ✓ Cached (if lock same) │
│      ↓                                                          │
│  Layer 5: COPY . .                     ✗ INVALIDATED (source)  │
│      ↓                                                          │
│  Layer 6: RUN build commands           ✗ Must rebuild          │
│                                                                 │
│  Rule: When a layer changes, all subsequent layers rebuild     │
└─────────────────────────────────────────────────────────────────┘
```

## Anti-Patterns and Fixes

### 1. Copying All Files Too Early

```dockerfile
# ❌ BAD: Invalidates cache on ANY file change
FROM php:8.4-cli
COPY . /app
RUN composer install
```

```dockerfile
# ✅ GOOD: Only invalidates on composer changes
FROM php:8.4-cli
COPY composer.json composer.lock /app/
RUN composer install
COPY . /app
```

### 2. Installing Dev Dependencies in Production

```dockerfile
# ❌ BAD: Includes dev dependencies in production
FROM php:8.4-fpm
COPY . /app
RUN composer install
```

```dockerfile
# ✅ GOOD: Multi-stage with production deps
FROM composer:2 AS deps
COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist

FROM php:8.4-fpm
COPY --from=deps /app/vendor /app/vendor
COPY . /app
```

### 3. Combining Unrelated Commands

```dockerfile
# ❌ BAD: One change invalidates entire layer
RUN apt-get update && \
    apt-get install -y git && \
    composer install && \
    npm install && \
    npm run build
```

```dockerfile
# ✅ GOOD: Separate concerns into layers
RUN apt-get update && apt-get install -y git

COPY composer.json composer.lock ./
RUN composer install

COPY package.json package-lock.json ./
RUN npm ci && npm run build
```

### 4. Not Using .dockerignore

```dockerfile
# ❌ BAD: Copies unnecessary files
COPY . .
# Includes: vendor, node_modules, .git, tests, etc.
```

```
# ✅ GOOD: .dockerignore
.git
vendor
node_modules
tests
docs
*.md
```

### 5. Running apt-get update Separately

```dockerfile
# ❌ BAD: Stale package cache
RUN apt-get update
RUN apt-get install -y git curl
```

```dockerfile
# ✅ GOOD: Combined update and install
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

## Optimization Checklist

### Layer Ordering

| Order | Content | Frequency of Change |
|-------|---------|---------------------|
| 1 | Base image | Rarely |
| 2 | System packages | Monthly |
| 3 | PHP extensions | Monthly |
| 4 | Composer dependencies | Weekly |
| 5 | NPM dependencies | Weekly |
| 6 | Application code | Every commit |
| 7 | Build artifacts | Every commit |

### Cache Optimization

```dockerfile
# Optimal layer ordering example
FROM php:8.4-fpm-alpine

# Layer 1-2: System dependencies (changes rarely)
RUN apk add --no-cache libzip icu-libs

# Layer 3: PHP extensions (changes monthly)
RUN docker-php-ext-install pdo_mysql intl zip

# Layer 4: Composer deps (changes weekly)
COPY composer.json composer.lock ./
RUN composer install --no-dev --prefer-dist

# Layer 5: NPM deps if needed (changes weekly)
COPY package*.json ./
RUN npm ci --production

# Layer 6: Source code (changes every commit)
COPY . .

# Layer 7: Build step (depends on source)
RUN composer dump-autoload --optimize
```

## BuildKit Cache Mounts

### Composer Cache Mount

```dockerfile
# syntax=docker/dockerfile:1.6

FROM php:8.4-cli

# Cache composer packages between builds
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --prefer-dist
```

### APK Cache Mount

```dockerfile
# syntax=docker/dockerfile:1.6

FROM php:8.4-alpine

# Cache apk packages
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --cache-dir=/var/cache/apk git unzip
```

### NPM Cache Mount

```dockerfile
# syntax=docker/dockerfile:1.6

FROM node:20-alpine

RUN --mount=type=cache,target=/root/.npm \
    npm ci
```

## Multi-Stage Build Patterns

### Minimal Production Image

```dockerfile
# Stage 1: Build with all tools
FROM php:8.4-cli AS builder
RUN apt-get update && apt-get install -y git unzip
COPY --from=composer:2 /usr/bin/composer /usr/bin/composer
COPY . .
RUN composer install --no-dev --optimize-autoloader

# Stage 2: Production with only runtime
FROM php:8.4-fpm-alpine AS production
COPY --from=builder /app/vendor /app/vendor
COPY --from=builder /app/src /app/src
COPY --from=builder /app/public /app/public
```

### Parallel Builds

```dockerfile
# syntax=docker/dockerfile:1.6

# Build PHP deps in parallel with JS deps
FROM composer:2 AS php-deps
COPY composer.* ./
RUN composer install --no-dev

FROM node:20 AS js-deps
COPY package*.json ./
RUN npm ci

FROM php:8.4-fpm
COPY --from=php-deps /app/vendor ./vendor
COPY --from=js-deps /app/node_modules ./node_modules
```

## CI Platform Caching

### GitHub Actions

```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build with cache
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### GitLab CI

```yaml
build:
  script:
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
```

### Docker Layer Cache with Registry

```yaml
# Pull previous image for cache
- docker pull $REGISTRY/app:latest || true

# Build with cache from pulled image
- docker build
    --cache-from $REGISTRY/app:latest
    --tag $REGISTRY/app:$VERSION
    .
```

## Image Size Optimization

### Alpine vs Debian

```dockerfile
# Debian: ~150MB base
FROM php:8.4-fpm
# Final: ~400-500MB

# Alpine: ~50MB base
FROM php:8.4-fpm-alpine
# Final: ~100-200MB
```

### Remove Build Dependencies

```dockerfile
FROM php:8.4-fpm-alpine

# Install and clean in one layer
RUN apk add --no-cache --virtual .build-deps \
        $PHPIZE_DEPS \
        libzip-dev \
    && docker-php-ext-install zip \
    && apk del .build-deps \
    && apk add --no-cache libzip
```

### Use Specific Tags

```dockerfile
# ❌ BAD: Unpredictable
FROM php:latest

# ✅ GOOD: Deterministic
FROM php:8.4.2-fpm-alpine3.19
```

## Analysis Output Format

```markdown
## Docker Layer Analysis

### Image: app:latest
**Size:** 450MB
**Layers:** 12

### Issues Found

| Severity | Issue | Location | Impact |
|----------|-------|----------|--------|
| 🔴 High | COPY before deps | Line 5 | Cache invalidation |
| 🟠 Medium | No .dockerignore | - | 50MB+ extra |
| 🟡 Low | Combined commands | Line 12 | Poor caching |

### Recommendations

1. **Move COPY . . after dependency install**
   ```dockerfile
   # Before
   COPY . .
   RUN composer install

   # After
   COPY composer.* ./
   RUN composer install
   COPY . .
   ```
   **Impact:** -2-5 minutes per build

2. **Add .dockerignore**
   ```
   .git
   vendor
   node_modules
   ```
   **Impact:** -50MB image size

### Estimated Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Build time | 8m | 3m | -62% |
| Image size | 450MB | 180MB | -60% |
| Cache hit rate | 20% | 80% | +60% |
```

## Generation Instructions

1. **Analyze Dockerfile:**
   - Parse layer order
   - Identify COPY commands
   - Check RUN command grouping
   - Verify .dockerignore exists

2. **Check for anti-patterns:**
   - Early COPY of all files
   - Combined unrelated commands
   - Missing cache mounts
   - No multi-stage build

3. **Generate recommendations:**
   - Reorder layers
   - Split/combine commands
   - Add cache mounts
   - Optimize for CI platform

## Usage

Provide:
- Path to Dockerfile
- CI platform (GitHub Actions, GitLab CI)
- Current build time (optional)

The analyzer will:
1. Parse Dockerfile layers
2. Identify optimization opportunities
3. Calculate potential improvements
4. Generate optimized Dockerfile
