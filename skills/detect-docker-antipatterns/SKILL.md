---
name: acc-detect-docker-antipatterns
description: Detects Docker antipatterns in PHP projects. Identifies layer ordering issues, cache invalidation, bloated images, and configuration smells.
---

# Docker Antipattern Detection

Analyze Dockerfiles for antipatterns causing bloated images, poor caching, and unreliable builds.

## Antipattern Catalog

### 1. COPY Before Dependency Install

```dockerfile
# BAD: Cache busted on every code change
COPY . /var/www/html
RUN composer install --no-dev

# GOOD: Dependencies first, source second
COPY composer.json composer.lock /var/www/html/
RUN composer install --no-dev --no-scripts --no-autoloader
COPY . /var/www/html
RUN composer dump-autoload --optimize
```

### 2. apt-get update in Separate Layer

```dockerfile
# BAD: Stale package index
RUN apt-get update
RUN apt-get install -y libpng-dev

# GOOD: Combined in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpng-dev && rm -rf /var/lib/apt/lists/*
```

### 3. Using latest Tag

```dockerfile
# BAD: Non-deterministic builds
FROM php:latest

# GOOD: Pinned version
FROM php:8.4.3-fpm-bookworm
```

### 4. apt-get Without Cleanup

```dockerfile
# BAD: Package cache bloats image
RUN apt-get update && apt-get install -y libzip-dev

# GOOD: Cleanup in same layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzip-dev && rm -rf /var/lib/apt/lists/*
```

### 5. Multiple FROM Without Multi-Stage Purpose

```dockerfile
# BAD: Build artifacts never copied
FROM node:20
RUN npm ci && npm run build
FROM php:8.4-fpm
COPY . /var/www/html

# GOOD: Artifact copy from named stage
FROM node:20 AS frontend
RUN npm ci && npm run build
FROM php:8.4-fpm
COPY --from=frontend /app/dist /var/www/html/public
```

### 6. Unrelated Commands in Single RUN

```dockerfile
# BAD: Mixed concerns, poor cache utilization
RUN apt-get update && pecl install redis && composer install

# GOOD: Logically grouped
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzip-dev && rm -rf /var/lib/apt/lists/*
RUN docker-php-ext-install zip opcache
RUN pecl install redis && docker-php-ext-enable redis
```

### 7. No .dockerignore

```
# Required .dockerignore to exclude:
.git
.env
vendor
node_modules
tests
docs
docker-compose*.yml
```

### 8. Installing Editors in Production

```dockerfile
# BAD: Dev tools in production
RUN apt-get install -y vim nano htop strace

# GOOD: Only runtime dependencies
RUN apt-get install -y --no-install-recommends libzip-dev
```

### 9. ADD Instead of COPY

```dockerfile
# BAD: ADD has implicit tar extraction and URL fetching
ADD app.tar.gz /var/www/html/

# GOOD: Explicit COPY for local files
COPY . /var/www/html/
```

### 10. CMD with Shell Form

```dockerfile
# BAD: Shell form (no signal forwarding)
CMD php-fpm -F

# GOOD: Exec form (PID 1 receives signals)
CMD ["php-fpm", "-F"]
```

### 11. ENTRYPOINT Not Handling Signals

```dockerfile
# GOOD: Entrypoint with exec for signal forwarding
COPY docker-entrypoint.sh /usr/local/bin/
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["php-fpm"]
```

## Grep Patterns

```bash
Grep: "^COPY \\." --glob "**/Dockerfile*"
Grep: "^RUN apt-get update$" --glob "**/Dockerfile*"
Grep: "^FROM.*:latest" --glob "**/Dockerfile*"
Grep: "apt-get install" --glob "**/Dockerfile*"
Grep: "^ADD " --glob "**/Dockerfile*"
Grep: "^(CMD|ENTRYPOINT) [^\\[]" --glob "**/Dockerfile*"
Grep: "install.*-y.*(vim|nano|htop|strace)" --glob "**/Dockerfile*"
Glob: "**/.dockerignore"
```

## Severity Classification

| Antipattern | Severity | Impact |
|-------------|----------|--------|
| COPY before deps install | Critical | Cache invalidation every build |
| Using latest tag | Critical | Non-reproducible builds |
| Installing editors | Major | Image bloat, attack surface |
| apt-get without cleanup | Major | +50-200MB image size |
| Shell form CMD | Major | No signal forwarding |
| ADD instead of COPY | Major | Unexpected behavior |
| Separate apt-get update | Major | Stale packages |
| No .dockerignore | Major | Large build context |
| Unrelated RUN commands | Minor | Poor cache utilization |
| Multiple FROM unused | Minor | Confusion, dead stages |
| No signal handling | Minor | Ungraceful shutdown |

## Output Format

```markdown
### Docker Antipattern: [Name]

**Severity:** Critical/Major/Minor
**File:** `Dockerfile:line`
**Category:** Cache / Size / Security / Reliability
**Issue:** [Description and why it is problematic]
**Fix:** [Corrected instruction snippet]
**Impact:** Build time / Image size / Reliability changes
```
