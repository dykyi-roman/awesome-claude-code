# GitHub Actions for PHP CI/CD

Deep dive into GitHub Actions configuration for PHP projects with DDD, testing, and deployment patterns.

## Detection Patterns

```bash
# Detect GitHub Actions workflows
Glob: ".github/workflows/*.yml"
Glob: ".github/workflows/*.yaml"

# Detect PHP setup action
Grep: "shivammathur/setup-php" --glob ".github/workflows/*.yml"

# Detect matrix strategy for PHP versions
Grep: "php.*8\.\d" --glob ".github/workflows/*.yml"

# Detect composer caching
Grep: "actions/cache" --glob ".github/workflows/*.yml"
Grep: "composer.*cache" --glob ".github/workflows/*.yml"

# Detect reusable workflows
Grep: "uses:.*\.github/workflows/" --glob ".github/workflows/*.yml"

# Detect job dependencies
Grep: "needs:" --glob ".github/workflows/*.yml"

# Detect secrets usage
Grep: "secrets\." --glob ".github/workflows/*.yml"

# Detect environment deployments
Grep: "environment:" --glob ".github/workflows/*.yml"
```

## Workflow Structure

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:  # manual trigger

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

permissions:
  contents: read
  pull-requests: write

env:
  PHP_VERSION: '8.4'
  COMPOSER_CACHE_DIR: ~/.composer/cache

jobs:
  lint:
    # ...
  test:
    needs: lint
    # ...
  build:
    needs: test
    # ...
```

### Key Sections

| Section | Purpose | Example |
|---------|---------|---------|
| `on:` | Trigger events | `push`, `pull_request`, `schedule`, `workflow_dispatch` |
| `concurrency:` | Cancel duplicate runs | Group by workflow + branch |
| `permissions:` | Token scope | `contents: read`, `packages: write` |
| `env:` | Global environment | PHP version, cache paths |
| `jobs:` | Job definitions | `lint`, `test`, `build`, `deploy` |
| `needs:` | Job dependencies | `needs: [lint, test]` |

## PHP Setup with shivammathur/setup-php

```yaml
- uses: shivammathur/setup-php@v2
  with:
    php-version: ${{ matrix.php }}
    extensions: intl, pdo_mysql, redis, amqp, opcache
    tools: composer:v2, phpstan, php-cs-fixer
    coverage: xdebug    # or pcov, none
    ini-values: memory_limit=512M, max_execution_time=60
  env:
    COMPOSER_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### Setup Options

| Parameter | Values | Notes |
|-----------|--------|-------|
| `php-version` | `8.2`, `8.3`, `8.4` | Use matrix for multi-version |
| `extensions` | Comma-separated list | `intl, pdo_mysql, redis, amqp` |
| `tools` | Composer, PHPStan, etc. | `composer:v2, phpstan, psalm` |
| `coverage` | `xdebug`, `pcov`, `none` | `none` for lint jobs (faster) |
| `ini-values` | PHP ini settings | `memory_limit=512M` |

## Matrix Strategy for PHP Versions

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        php: ['8.2', '8.3', '8.4']
        dependency-version: ['prefer-lowest', 'prefer-stable']
        include:
          - php: '8.4'
            dependency-version: 'prefer-stable'
            coverage: true
        exclude:
          - php: '8.2'
            dependency-version: 'prefer-lowest'
      fail-fast: false
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
          coverage: ${{ matrix.coverage && 'xdebug' || 'none' }}
      - run: composer update --${{ matrix.dependency-version }} --no-progress
      - run: vendor/bin/phpunit
      - if: matrix.coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
```

### Matrix Best Practices

| Practice | Reason |
|----------|--------|
| `fail-fast: false` | See all failures, not just first |
| `include:` for coverage | Run coverage once, not per combination |
| `exclude:` for unsupported | Skip PHP 8.2 + lowest deps if incompatible |
| Quote PHP versions | `'8.0'` not `8.0` (YAML parses as float) |

## Job Dependencies and Artifacts

```yaml
jobs:
  install:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: none
      - name: Cache Composer
        uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ hashFiles('composer.lock') }}
      - run: composer install --no-progress --prefer-dist

  lint:
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: none
      - name: Restore vendor
        uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ hashFiles('composer.lock') }}
      - run: vendor/bin/phpstan analyse --memory-limit=1G
      - run: vendor/bin/php-cs-fixer fix --dry-run --diff
      - run: vendor/bin/deptrac analyse --no-progress

  test:
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: xdebug
      - name: Restore vendor
        uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ hashFiles('composer.lock') }}
      - run: vendor/bin/phpunit --coverage-clover coverage.xml --log-junit junit.xml
      - name: Upload test results
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: test-results
          path: |
            coverage.xml
            junit.xml
          retention-days: 14

  build:
    needs: [lint, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: app:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

### Job Dependency Graph

```
install ──┬── lint ──┬── build ── deploy-staging ── deploy-production
          └── test ──┘
```

## Secrets Management

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
          REDIS_URL: ${{ secrets.REDIS_URL }}
          APP_SECRET: ${{ secrets.APP_SECRET }}
        run: ./deploy.sh

      - name: Docker login
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
```

### Secrets Scope

| Scope | Access | Configuration |
|-------|--------|---------------|
| Repository secrets | All workflows in repo | Settings > Secrets > Actions |
| Environment secrets | Jobs with `environment:` | Settings > Environments > Secrets |
| Organization secrets | Selected repos | Org Settings > Secrets |
| `GITHUB_TOKEN` | Auto-generated per run | Scoped by `permissions:` |

### Secrets Safety Rules

- Never echo secrets: `echo ${{ secrets.KEY }}` leaks to logs
- Use environment-scoped secrets for production values
- Rotate secrets via GitHub API or UI, not in code
- Mask custom secrets: `echo "::add-mask::$CUSTOM_VALUE"`

## Reusable Workflows and Composite Actions

### Reusable Workflow

```yaml
# .github/workflows/php-test.yml (reusable)
name: PHP Test

on:
  workflow_call:
    inputs:
      php-version:
        required: true
        type: string
      coverage:
        required: false
        type: boolean
        default: false
    secrets:
      codecov-token:
        required: false

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ inputs.php-version }}
          coverage: ${{ inputs.coverage && 'xdebug' || 'none' }}
      - run: composer install --no-progress --prefer-dist
      - run: vendor/bin/phpunit ${{ inputs.coverage && '--coverage-clover coverage.xml' || '' }}
      - if: inputs.coverage
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.codecov-token }}
```

```yaml
# .github/workflows/ci.yml (caller)
jobs:
  test-php82:
    uses: ./.github/workflows/php-test.yml
    with:
      php-version: '8.2'

  test-php84-coverage:
    uses: ./.github/workflows/php-test.yml
    with:
      php-version: '8.4'
      coverage: true
    secrets:
      codecov-token: ${{ secrets.CODECOV_TOKEN }}
```

### Composite Action

```yaml
# .github/actions/setup-php-project/action.yml
name: Setup PHP Project
description: Install PHP and Composer dependencies with caching

inputs:
  php-version:
    description: PHP version
    required: true
    default: '8.4'
  coverage:
    description: Coverage driver
    required: false
    default: 'none'

runs:
  using: composite
  steps:
    - uses: shivammathur/setup-php@v2
      with:
        php-version: ${{ inputs.php-version }}
        extensions: intl, pdo_mysql, redis, amqp
        coverage: ${{ inputs.coverage }}
    - name: Cache Composer
      uses: actions/cache@v4
      with:
        path: vendor
        key: vendor-${{ runner.os }}-php${{ inputs.php-version }}-${{ hashFiles('composer.lock') }}
        restore-keys: vendor-${{ runner.os }}-php${{ inputs.php-version }}-
    - run: composer install --no-progress --prefer-dist
      shell: bash
```

```yaml
# Usage in workflow
steps:
  - uses: actions/checkout@v4
  - uses: ./.github/actions/setup-php-project
    with:
      php-version: '8.4'
      coverage: xdebug
  - run: vendor/bin/phpunit
```

## Full PHP CI Workflow Example

```yaml
# .github/workflows/ci.yml
name: PHP CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PHP_VERSION: '8.4'

jobs:
  lint:
    name: Static Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-php-project
      - run: vendor/bin/phpstan analyse --memory-limit=1G --error-format=github
      - run: vendor/bin/php-cs-fixer fix --dry-run --diff
      - run: vendor/bin/deptrac analyse --no-progress --formatter=github-actions

  test:
    name: Tests (PHP ${{ matrix.php }})
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        php: ['8.2', '8.3', '8.4']
      fail-fast: false
    services:
      mysql:
        image: mysql:8.4
        env:
          MYSQL_DATABASE: test
          MYSQL_ROOT_PASSWORD: root
        ports: ['3306:3306']
        options: >-
          --health-cmd="mysqladmin ping -h localhost"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
      redis:
        image: redis:7-alpine
        ports: ['6379:6379']
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=5
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/setup-php-project
        with:
          php-version: ${{ matrix.php }}
          coverage: ${{ matrix.php == '8.4' && 'xdebug' || 'none' }}
      - name: Run tests
        env:
          DATABASE_URL: mysql://root:root@127.0.0.1:3306/test
          REDIS_URL: redis://127.0.0.1:6379
        run: |
          vendor/bin/phpunit \
            ${{ matrix.php == '8.4' && '--coverage-clover coverage.xml --log-junit junit.xml' || '' }}
      - if: matrix.php == '8.4'
        uses: codecov/codecov-action@v4
        with:
          token: ${{ secrets.CODECOV_TOKEN }}
          files: coverage.xml

  build:
    name: Build Docker Image
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ghcr.io/${{ github.repository }}:${{ github.sha }}
            ghcr.io/${{ github.repository }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy to Production
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        env:
          DEPLOY_TOKEN: ${{ secrets.DEPLOY_TOKEN }}
        run: |
          echo "Deploying ${{ github.sha }} to production"
          # ./deploy.sh ${{ github.sha }}
```

## Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| PHP version parsed as float | `8.0` becomes `8` | Quote versions: `'8.0'` |
| Composer timeout | `The process has been signaled with signal "9"` | Add `COMPOSER_PROCESS_TIMEOUT: 600` env |
| PHPStan out of memory | `Allowed memory size exhausted` | Add `--memory-limit=1G` or `2G` |
| MySQL not ready | `Connection refused` | Use `options: --health-cmd` with retries |
| Cache miss on PR | Different branch key | Add `restore-keys:` fallback pattern |
| Secrets not available in PR | Fork PR security | Use `pull_request_target` (carefully) |
| Slow composer install | No cache hit | Use `hashFiles('composer.lock')` as cache key |
| Duplicate CI runs | Push + PR triggers | Add `concurrency:` with `cancel-in-progress` |
| GITHUB_TOKEN scope | Permission denied | Set explicit `permissions:` block |
| Reusable workflow not found | Wrong path | Must be in `.github/workflows/`, use `uses: ./.github/workflows/file.yml` |
