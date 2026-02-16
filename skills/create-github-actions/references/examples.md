# GitHub Actions Workflow Examples

Concrete workflow configurations and usage examples for PHP projects.

## Project Analysis Example

Before generating workflows, analyze the project:

```bash
# Check available tools
cat composer.json | jq '.require-dev'

# Check existing workflows
ls -la .github/workflows/

# Identify testing framework
grep -l "phpunit\|pest" composer.json

# Check for Docker
ls Dockerfile docker-compose.yml 2>/dev/null
```

## Minimal CI Workflow

For projects with only PHPUnit:

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: pcov

      - run: composer install --no-progress --prefer-dist

      - run: vendor/bin/phpunit --coverage-clover=coverage.xml
```

## Multi-Service Integration Test

Example with MySQL, Redis, and RabbitMQ:

```yaml
jobs:
  integration:
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: test
        ports: ['3306:3306']
        options: --health-cmd="mysqladmin ping" --health-interval=10s --health-timeout=5s --health-retries=3

      redis:
        image: redis:7
        ports: ['6379:6379']
        options: --health-cmd="redis-cli ping" --health-interval=10s --health-timeout=5s --health-retries=3

      rabbitmq:
        image: rabbitmq:3-management
        ports: ['5672:5672', '15672:15672']
        options: --health-cmd="rabbitmq-diagnostics -q check_running" --health-interval=10s --health-timeout=5s --health-retries=3

    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          extensions: pdo_mysql, redis, amqp

      - run: composer install --no-progress --prefer-dist

      - name: Run integration tests
        env:
          DATABASE_URL: mysql://root:root@127.0.0.1:3306/test
          REDIS_URL: redis://127.0.0.1:6379
          AMQP_URL: amqp://guest:guest@127.0.0.1:5672
        run: vendor/bin/phpunit --testsuite=integration
```

## Composer Cache Optimization

Reusable cache step for all workflows:

```yaml
steps:
  - name: Get Composer cache directory
    id: composer-cache
    run: echo "dir=$(composer config cache-files-dir)" >> $GITHUB_OUTPUT

  - name: Cache Composer dependencies
    uses: actions/cache@v4
    with:
      path: |
        ${{ steps.composer-cache.outputs.dir }}
        vendor
      key: composer-${{ hashFiles('composer.lock') }}
      restore-keys: composer-
```

## Artifact Sharing Between Jobs

Upload vendor in install job, download in dependent jobs:

```yaml
# Upload step (in install job)
- name: Upload vendor
  uses: actions/upload-artifact@v4
  with:
    name: vendor
    path: vendor
    retention-days: 1

# Download step (in dependent jobs)
- name: Download vendor
  uses: actions/download-artifact@v4
  with:
    name: vendor
    path: vendor
```

## Conditional Deployment Example

Deploy staging on every push to main, production only on tags:

```yaml
jobs:
  deploy-staging:
    if: github.ref == 'refs/heads/main'
    environment:
      name: staging
      url: https://staging.example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh staging

  deploy-production:
    needs: deploy-staging
    if: startsWith(github.ref, 'refs/tags/v')
    environment:
      name: production
      url: https://example.com
    steps:
      - uses: actions/checkout@v4
      - run: ./deploy.sh production
```

## Scheduled Security Scan Example

Weekly security scanning with multiple tools:

```yaml
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly Monday
  workflow_dispatch:       # Manual trigger

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'

      - run: composer install --no-progress --prefer-dist

      - name: Dependency audit
        run: composer audit

      - name: Taint analysis
        run: vendor/bin/psalm --taint-analysis
```

## Concurrency Control Example

Cancel in-progress runs for the same branch:

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

## Notification Example

Slack notification on failure:

```yaml
- name: Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: ${{ job.status }}
    text: 'CI failed on ${{ github.ref }}'
  env:
    SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK }}
```

## Coverage Badge Example

Generate and upload coverage badge:

```yaml
- name: Upload coverage
  uses: codecov/codecov-action@v4
  with:
    files: coverage.xml
    flags: unit
    token: ${{ secrets.CODECOV_TOKEN }}
    fail_ci_if_error: true
```
