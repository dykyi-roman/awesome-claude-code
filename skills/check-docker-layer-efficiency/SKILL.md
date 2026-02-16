---
name: acc-check-docker-layer-efficiency
description: Checks Docker layer efficiency for PHP builds. Analyzes layer ordering, cache utilization, and identifies optimization opportunities.
---

# Docker Layer Efficiency Checker

Analyze Dockerfile layer structure for optimal ordering, cache utilization, and build performance.

## Optimal Layer Ordering

| Order | Layer Type | Change Frequency | Example |
|-------|-----------|------------------|---------|
| 1 | Base image | Rare | `FROM php:8.4-fpm` |
| 2 | System deps | Rare | `RUN apt-get install` |
| 3 | PHP extensions | Rare | `RUN docker-php-ext-install` |
| 4 | Composer deps | Weekly | `COPY composer.* && composer install` |
| 5 | NPM deps | Weekly | `COPY package.* && npm ci` |
| 6 | Config files | Occasional | `COPY php.ini, nginx.conf` |
| 7 | App source | Every commit | `COPY . /var/www/html` |
| 8 | Build steps | Every commit | `RUN composer dump-autoload` |

## Detection Patterns

### 1. Source Copy Before Dependencies

```dockerfile
# BAD: Layer 7 before Layer 4
COPY . /var/www/html
RUN composer install --no-dev

# GOOD: Dependencies first
COPY composer.json composer.lock /var/www/html/
RUN composer install --no-dev --no-scripts --no-autoloader
COPY . /var/www/html/
RUN composer dump-autoload --optimize
```

### 2. Mergeable RUN Commands

```dockerfile
# BAD: Three layers for related ops
RUN apt-get update
RUN apt-get install -y libzip-dev
RUN rm -rf /var/lib/apt/lists/*

# GOOD: Single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzip-dev && rm -rf /var/lib/apt/lists/*
```

### 3. Cache-Busting ARG Placement

```dockerfile
# BAD: ARG before expensive layers busts cache
ARG APP_VERSION=1.0.0
FROM php:8.4-fpm
RUN apt-get update && apt-get install -y libzip-dev

# GOOD: ARG after expensive layers
FROM php:8.4-fpm
RUN apt-get update && apt-get install -y libzip-dev
ARG APP_VERSION=1.0.0
LABEL version=$APP_VERSION
```

### 4. BuildKit Cache Mount Usage

```dockerfile
# STANDARD: Re-downloads every build
RUN composer install --no-dev

# OPTIMIZED: BuildKit cache mount
RUN --mount=type=cache,target=/root/.composer/cache \
    composer install --no-dev --optimize-autoloader

# OPTIMIZED: apt cache mount
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && apt-get install -y libzip-dev
```

### 5. Config Files Placement

```dockerfile
# BAD: Config copied early
COPY docker/php.ini /usr/local/etc/php/php.ini
RUN apt-get update && apt-get install -y libzip-dev

# GOOD: Config after system deps, before source
RUN apt-get update && apt-get install -y libzip-dev
COPY docker/php.ini /usr/local/etc/php/php.ini
COPY . /var/www/html/
```

### 6. Extension Installation Order

```dockerfile
# GOOD: All extensions together before app code
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpng-dev libzip-dev libicu-dev \
    && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install -j$(nproc) gd zip intl opcache pdo_mysql
```

## Grep Patterns

```bash
Grep: "^(FROM|RUN|COPY|ADD) " --glob "**/Dockerfile*"
Grep: "^COPY \\." --glob "**/Dockerfile*"
Grep: "--mount=type=cache" --glob "**/Dockerfile*"
Grep: "^ARG " --glob "**/Dockerfile*"
Grep: "^WORKDIR " --glob "**/Dockerfile*"
```

## Scoring

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Layer ordering | 30% | Layers in optimal frequency order |
| Mergeable RUN count | 20% | Fewer mergeable pairs = better |
| Cache mount usage | 15% | BuildKit cache for package managers |
| Dependency-first | 20% | Composer/npm files before source |
| Empty layers | 15% | Fewer redundant layers = better |

**Score:** 0-100% (Excellent > 85 | Good > 70 | Needs Improvement > 50 | Poor <= 50)

## Output Format

```markdown
## Layer Efficiency Report

**Score:** X% — [Excellent / Good / Needs Improvement / Poor]
**Total Layers:** N
**Ordering Violations:** N

### Layer Map
| # | Instruction | Category | Order | Status |
|---|-------------|----------|-------|--------|
| 1 | FROM php:8.4-fpm | Base | 1 | OK |
| 2 | COPY . /var/www | Source | 7 | Out of order |

### Issues Found
1. **[Issue]** at line N — [Description and fix]

### Optimization Opportunities
- Merge RUN at lines X, Y (saves N layers)
- Add BuildKit cache for composer (saves ~30s)
- Reorder COPY instructions (improves cache hit rate)
```
