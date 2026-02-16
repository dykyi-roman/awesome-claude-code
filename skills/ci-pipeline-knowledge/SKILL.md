---
name: acc-ci-pipeline-knowledge
description: CI/CD pipeline knowledge base. Provides platforms overview (GitHub Actions, GitLab CI), pipeline stages, caching strategies, parallelization, artifact management, and environment management.
---

# CI/CD Pipeline Knowledge Base

Quick reference for CI/CD pipeline patterns, platforms, and best practices.

## Pipeline Stages

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Install   │───▶│    Lint     │───▶│    Test     │───▶│    Build    │───▶│   Deploy    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
     Deps            Code Style         PHPUnit           Docker            Production
     Cache           PHPStan            Coverage          Artifacts         Environments
```

**Standard PHP Pipeline:**
1. **Install** — Composer dependencies, cache restore
2. **Lint** — PHPStan, Psalm, PHP-CS-Fixer, DEPTRAC
3. **Test** — PHPUnit, code coverage, mutation testing
4. **Build** — Docker image, version tagging
5. **Deploy** — Environment deployment, health checks

## Platform Comparison

| Feature | GitHub Actions | GitLab CI |
|---------|----------------|-----------|
| Config file | `.github/workflows/*.yml` | `.gitlab-ci.yml` |
| Runners | GitHub-hosted / self-hosted | GitLab-hosted / self-hosted |
| Caching | `actions/cache` | Built-in `cache:` |
| Artifacts | `actions/upload-artifact` | Built-in `artifacts:` |
| Secrets | Repository/Environment secrets | CI/CD Variables |
| Matrix builds | `strategy.matrix` | `parallel:matrix` |
| Reusable | Composite actions, workflows | `include:`, `extends:` |
| Container | `container:` | `image:` |

## GitHub Actions Structure

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  PHP_VERSION: '8.4'
  COMPOSER_CACHE_DIR: ~/.composer/cache

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: none
      - name: Cache Composer
        uses: actions/cache@v4
        with:
          path: ${{ env.COMPOSER_CACHE_DIR }}
          key: composer-${{ hashFiles('composer.lock') }}
      - run: composer install --no-progress --prefer-dist
      - run: vendor/bin/phpstan analyse

  test:
    needs: lint
    runs-on: ubuntu-latest
    services:
      mysql:
        image: mysql:8.0
        env:
          MYSQL_DATABASE: test
          MYSQL_ROOT_PASSWORD: root
        ports:
          - 3306:3306
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: xdebug
      - run: composer install --no-progress --prefer-dist
      - run: vendor/bin/phpunit --coverage-clover coverage.xml
      - uses: codecov/codecov-action@v4
```

## GitLab CI Structure

```yaml
stages:
  - install
  - lint
  - test
  - build
  - deploy

variables:
  PHP_VERSION: "8.4"
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"

.php_template: &php_template
  image: php:${PHP_VERSION}-cli
  cache:
    key: composer-$CI_COMMIT_REF_SLUG
    paths:
      - .composer-cache/
      - vendor/
    policy: pull

install:
  <<: *php_template
  stage: install
  cache:
    policy: pull-push
  script:
    - composer install --no-progress --prefer-dist

lint:phpstan:
  <<: *php_template
  stage: lint
  needs: [install]
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G

test:unit:
  <<: *php_template
  stage: test
  needs: [lint:phpstan]
  services:
    - mysql:8.0
  variables:
    MYSQL_DATABASE: test
    MYSQL_ROOT_PASSWORD: root
  script:
    - vendor/bin/phpunit --coverage-cobertura coverage.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
```

## Caching Strategies

### Composer Cache

**GitHub Actions:**
```yaml
- name: Cache Composer dependencies
  uses: actions/cache@v4
  with:
    path: |
      ~/.composer/cache
      vendor
    key: php-${{ hashFiles('composer.lock') }}
    restore-keys: |
      php-
```

**GitLab CI:**
```yaml
cache:
  key:
    files:
      - composer.lock
  paths:
    - .composer-cache/
    - vendor/
  policy: pull-push  # pull on jobs, push on install
```

### Docker Layer Cache

**GitHub Actions:**
```yaml
- name: Set up Docker Buildx
  uses: docker/setup-buildx-action@v3

- name: Build and push
  uses: docker/build-push-action@v5
  with:
    context: .
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**GitLab CI:**
```yaml
build:
  script:
    - docker build --cache-from $CI_REGISTRY_IMAGE:latest -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
```

## Parallelization Patterns

### Matrix Strategy (GitHub Actions)

```yaml
test:
  strategy:
    matrix:
      php: ['8.2', '8.3', '8.4']
      database: ['mysql', 'postgres']
      exclude:
        - php: '8.2'
          database: 'postgres'
    fail-fast: false
  runs-on: ubuntu-latest
  steps:
    - run: echo "Testing PHP ${{ matrix.php }} with ${{ matrix.database }}"
```

### Parallel Jobs (GitLab CI)

```yaml
test:
  parallel:
    matrix:
      - PHP_VERSION: ['8.2', '8.3', '8.4']
        DATABASE: ['mysql', 'postgres']
  script:
    - echo "Testing PHP $PHP_VERSION with $DATABASE"
```

### Test Splitting

```yaml
# Split PHPUnit tests across runners
test:
  parallel: 4
  script:
    - vendor/bin/phpunit --testsuite unit --filter "Test$((($CI_NODE_INDEX - 1) * 25 + 1))-$(($CI_NODE_INDEX * 25))"
```

## Environment Management

### GitHub Environments

```yaml
deploy-production:
  runs-on: ubuntu-latest
  environment:
    name: production
    url: https://example.com
  steps:
    - name: Deploy
      env:
        DATABASE_URL: ${{ secrets.DATABASE_URL }}
      run: ./deploy.sh
```

### GitLab Environments

```yaml
deploy:production:
  stage: deploy
  environment:
    name: production
    url: https://example.com
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
  script:
    - ./deploy.sh
```

## Artifact Management

### Test Reports

**GitHub Actions:**
```yaml
- name: Upload test results
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: test-results
    path: |
      coverage.xml
      junit.xml
    retention-days: 30
```

**GitLab CI:**
```yaml
test:
  artifacts:
    when: always
    paths:
      - coverage.xml
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 30 days
```

## Pipeline Optimization Checklist

| Optimization | Impact | Implementation |
|-------------|--------|----------------|
| Dependency caching | ⬇️ 2-5 min | Cache composer, npm |
| Docker layer caching | ⬇️ 3-10 min | BuildKit cache |
| Parallel jobs | ⬇️ 50-80% | Matrix, split tests |
| Skip unchanged | ⬇️ Variable | Path filters, needs |
| Smaller images | ⬇️ 1-3 min | Alpine, multi-stage |
| Fail fast | ⬇️ Variable | Early exit on errors |

## Common Pipeline Patterns

### 1. Monorepo Pipeline

```yaml
# Only run when specific paths change
on:
  push:
    paths:
      - 'services/api/**'
      - 'shared/**'
```

### 2. Pull Request vs Push

```yaml
on:
  pull_request:
    # Run tests, skip deploy
  push:
    branches: [main]
    # Run full pipeline with deploy
```

### 3. Scheduled Security Scans

```yaml
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly Monday
  workflow_dispatch:  # Manual trigger
```

### 4. Release Workflow

```yaml
on:
  release:
    types: [published]

jobs:
  publish:
    steps:
      - name: Get version
        run: echo "VERSION=${GITHUB_REF#refs/tags/v}" >> $GITHUB_ENV
```

## Best Practices

### DO

- ✅ Cache dependencies aggressively
- ✅ Use specific action versions (`@v4`, not `@latest`)
- ✅ Fail fast in PR pipelines
- ✅ Run security scans on schedule
- ✅ Use environments for deployment gates
- ✅ Store secrets in vault, not code

### DON'T

- ❌ Run full pipeline on every commit
- ❌ Install dependencies in every job
- ❌ Use mutable tags for Docker images
- ❌ Expose secrets in logs
- ❌ Skip tests for "quick fixes"
- ❌ Deploy without health checks

## References

For detailed information, load these reference files:

- `references/github-actions.md` — GitHub Actions deep dive
- `references/gitlab-ci.md` — GitLab CI configuration
- `references/caching.md` — Caching strategies and patterns
