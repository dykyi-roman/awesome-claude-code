---
name: acc-generate-ci-fix
description: Generates minimal, safe fixes for CI configuration issues. Provides fix templates for dependency, test, lint, infrastructure, Docker, and timeout failures.
---

# CI Fix Generator

Templates and patterns for generating minimal, safe CI configuration fixes.

## Fix Generation Principles

### 1. Minimal Change
- Fix only what's broken
- Don't restructure entire pipeline
- Don't add unrelated improvements
- Preserve existing job structure

### 2. Safe Change
- Preserve existing behavior
- Maintain security settings
- Keep backward compatibility
- Don't expose secrets

### 3. Validated Change
- Provide local verification command
- Include rollback instructions
- Test fix before committing

## Fix Templates by Category

### 1. Memory Exhausted

**Pattern:** `Allowed memory size of X bytes exhausted`

**GitHub Actions Fix:**
```yaml
# .github/workflows/ci.yml
jobs:
  phpstan:
    steps:
      - name: Run PHPStan
        run: php -d memory_limit=-1 vendor/bin/phpstan analyse
        # Alternative: set in phpstan.neon
```

**GitLab CI Fix:**
```yaml
# .gitlab-ci.yml
phpstan:
  variables:
    PHP_MEMORY_LIMIT: "-1"
  script:
    - php -d memory_limit=-1 vendor/bin/phpstan analyse
```

**phpstan.neon Fix:**
```neon
parameters:
    parallel:
        maximumNumberOfProcesses: 1
        processTimeout: 300.0
```

### 2. Composer Conflicts

**Pattern:** `Your requirements could not be resolved`

**Fix Strategy:**
```bash
# Diagnose
composer why-not package/name version

# Option 1: Update constraint
composer require package/name:^2.0 --no-update
composer update package/name

# Option 2: Add platform config
# composer.json
{
    "config": {
        "platform": {
            "php": "8.2"
        }
    }
}

# Option 3: Allow specific plugin
{
    "config": {
        "allow-plugins": {
            "plugin/name": true
        }
    }
}
```

**GitHub Actions Fix:**
```yaml
- name: Install dependencies
  run: |
    composer config platform.php 8.2
    composer install --prefer-dist --no-progress
  env:
    COMPOSER_MEMORY_LIMIT: -1
```

### 3. PHPStan Baseline

**Pattern:** `PHPStan found X new errors` or `Baseline outdated`

**Fix:**
```yaml
# GitHub Actions
- name: Generate PHPStan baseline
  run: |
    vendor/bin/phpstan analyse --generate-baseline
    git add phpstan-baseline.neon
```

**phpstan.neon Fix:**
```neon
includes:
    - phpstan-baseline.neon

parameters:
    reportUnmatchedIgnoredErrors: false
```

### 4. Service Not Ready

**Pattern:** `Connection refused` to database/redis/etc.

**GitHub Actions Fix:**
```yaml
services:
  mysql:
    image: mysql:8.0
    env:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test
    ports:
      - 3306:3306
    options: >-
      --health-cmd="mysqladmin ping"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=5

steps:
  - name: Wait for MySQL
    run: |
      until mysqladmin ping -h 127.0.0.1 --silent; do
        echo 'Waiting for MySQL...'
        sleep 2
      done
```

**GitLab CI Fix:**
```yaml
services:
  - name: mysql:8.0
    alias: mysql
    variables:
      MYSQL_ROOT_PASSWORD: root
      MYSQL_DATABASE: test

variables:
  DB_HOST: mysql
  DB_PORT: 3306

.wait-for-db: &wait-for-db
  before_script:
    - |
      until mysqladmin ping -h mysql --silent; do
        echo 'Waiting for MySQL...'
        sleep 2
      done
```

### 5. Docker Build Failure

**Pattern:** `COPY failed: file not found` or `no space left`

**Dockerfile Fix:**
```dockerfile
# Check .dockerignore doesn't exclude needed files
# Ensure COPY paths are correct relative to context

# Before:
COPY ./src /app/src

# After (if issue is path):
COPY src/ /app/src/

# For multi-stage builds:
FROM composer:2 AS deps
COPY composer.json composer.lock ./
RUN composer install --no-scripts

FROM php:8.2-fpm
COPY --from=deps /app/vendor /app/vendor
```

**GitHub Actions Fix (space issue):**
```yaml
- name: Free disk space
  run: |
    sudo rm -rf /usr/share/dotnet
    sudo rm -rf /opt/ghc
    docker system prune -af

- name: Build Docker image
  run: docker build -t app .
```

### 6. Timeout Issues

**Pattern:** `Job exceeded maximum execution time`

**GitHub Actions Fix:**
```yaml
jobs:
  test:
    timeout-minutes: 30  # Increase from default 6 hours
    steps:
      - name: Run tests
        timeout-minutes: 20  # Step-level timeout
        run: vendor/bin/phpunit
```

**GitLab CI Fix:**
```yaml
test:
  timeout: 30 minutes
  script:
    - vendor/bin/phpunit --stop-on-failure
```

**PHPUnit Fix:**
```xml
<!-- phpunit.xml -->
<phpunit
    executionOrder="depends,defects"
    stopOnFailure="true"
    timeoutForSmallTests="1"
    timeoutForMediumTests="10"
    timeoutForLargeTests="60">
```

### 7. Permission Denied

**Pattern:** `Permission denied` on file operations

**GitHub Actions Fix:**
```yaml
- name: Fix permissions
  run: chmod +x ./scripts/*.sh

- name: Run script
  run: ./scripts/deploy.sh
```

**GitLab CI Fix:**
```yaml
before_script:
  - chmod +x ./scripts/*.sh

# Or in Dockerfile:
RUN chmod +x /app/scripts/*.sh
```

### 8. Cache Miss

**Pattern:** Cache not being used, slow installs

**GitHub Actions Fix:**
```yaml
- name: Cache Composer dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.composer/cache
      vendor
    key: ${{ runner.os }}-composer-${{ hashFiles('**/composer.lock') }}
    restore-keys: |
      ${{ runner.os }}-composer-

- name: Install dependencies
  run: composer install --prefer-dist --no-progress
```

**GitLab CI Fix:**
```yaml
cache:
  key:
    files:
      - composer.lock
  paths:
    - vendor/
  policy: pull-push

variables:
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"
```

### 9. PHP Extension Missing

**Pattern:** `PHP Fatal error: Uncaught Error: Call to undefined function`

**GitHub Actions Fix:**
```yaml
- name: Setup PHP
  uses: shivammathur/setup-php@v2
  with:
    php-version: '8.2'
    extensions: mbstring, xml, ctype, iconv, intl, pdo_mysql, redis
    coverage: xdebug
```

**Dockerfile Fix:**
```dockerfile
RUN docker-php-ext-install pdo pdo_mysql
RUN pecl install redis && docker-php-ext-enable redis
```

### 10. Environment Variable Missing

**Pattern:** `Undefined environment variable`

**GitHub Actions Fix:**
```yaml
env:
  APP_ENV: testing
  APP_DEBUG: true
  DB_CONNECTION: mysql

jobs:
  test:
    steps:
      - name: Create .env
        run: cp .env.ci .env
```

**GitLab CI Fix:**
```yaml
variables:
  APP_ENV: testing
  DB_HOST: mysql

# Or use CI/CD variables for secrets
# Settings > CI/CD > Variables
```

## Fix Composition Rules

### Order of Operations
1. Identify failure category
2. Match error pattern
3. Select minimal fix
4. Verify fix doesn't break other jobs
5. Provide rollback instructions

### What NOT to Change
- Security settings (unless fixing vulnerability)
- Secret management approach
- Existing job names (may break branch protection)
- Trigger conditions (unless causing issue)

### Commit Message Format
```
fix(ci): <short description>

<detailed description of what was wrong and how it's fixed>

Issue: <link if applicable>
```

## Verification Commands

### Local Testing
```bash
# GitHub Actions - act
act -j <job-name>

# GitLab CI - gitlab-runner
gitlab-runner exec docker <job-name>

# Docker build
docker build -t test-image .

# Composer
composer install --dry-run

# PHPStan
vendor/bin/phpstan analyse --debug
```

## Rollback Instructions

For any CI fix, provide rollback:

```bash
# If fix causes issues, revert with:
git revert HEAD
# Or restore previous version:
git checkout HEAD~1 -- .github/workflows/ci.yml
```
