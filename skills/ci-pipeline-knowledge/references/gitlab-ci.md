# GitLab CI for PHP CI/CD

Deep dive into GitLab CI configuration for PHP projects with DDD, testing, and deployment patterns.

## Detection Patterns

```bash
# Detect GitLab CI configuration
Glob: ".gitlab-ci.yml"
Glob: ".gitlab/**/*.yml"

# Detect PHP image usage
Grep: "image.*php:" --glob ".gitlab-ci.yml"

# Detect stages definition
Grep: "^stages:" --glob ".gitlab-ci.yml"

# Detect cache configuration
Grep: "cache:" --glob ".gitlab-ci.yml"

# Detect CI/CD variables
Grep: "variables:" --glob ".gitlab-ci.yml"
Grep: "\$CI_" --glob ".gitlab-ci.yml"

# Detect rules and conditions
Grep: "rules:" --glob ".gitlab-ci.yml"
Grep: "only:|except:" --glob ".gitlab-ci.yml"

# Detect include directives
Grep: "include:" --glob ".gitlab-ci.yml"

# Detect environment deployments
Grep: "environment:" --glob ".gitlab-ci.yml"

# Detect services (database, redis)
Grep: "services:" --glob ".gitlab-ci.yml"
```

## .gitlab-ci.yml Structure

```yaml
# .gitlab-ci.yml
stages:
  - install
  - lint
  - test
  - build
  - deploy

variables:
  PHP_VERSION: "8.4"
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"
  MYSQL_DATABASE: test
  MYSQL_ROOT_PASSWORD: root

default:
  image: php:${PHP_VERSION}-cli
  before_script:
    - apt-get update -qq && apt-get install -yqq git unzip libicu-dev libzip-dev
    - docker-php-ext-install intl pdo_mysql zip opcache
    - curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

# Job definitions follow...
```

### Top-Level Keywords

| Keyword | Purpose | Example |
|---------|---------|---------|
| `stages:` | Pipeline stage order | `[install, lint, test, build, deploy]` |
| `variables:` | Global environment vars | `PHP_VERSION: "8.4"` |
| `default:` | Default job settings | `image:`, `before_script:` |
| `include:` | Import external configs | `local:`, `template:`, `remote:` |
| `workflow:` | Pipeline-level rules | Control when pipeline runs |

## PHP-Specific Configuration

### Custom Docker Image (Recommended)

```dockerfile
# .gitlab/ci/Dockerfile
FROM php:8.4-cli

RUN apt-get update && apt-get install -y \
    git unzip libicu-dev libzip-dev libpq-dev \
    && docker-php-ext-install intl pdo_mysql pdo_pgsql zip opcache \
    && pecl install redis amqp xdebug \
    && docker-php-ext-enable redis amqp \
    && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer \
    && apt-get clean && rm -rf /var/lib/apt/lists/*
```

```yaml
# Use pre-built CI image instead of installing extensions each run
default:
  image: registry.example.com/php-ci:8.4
```

### PHP Template with YAML Anchors

```yaml
.php_base: &php_base
  image: php:${PHP_VERSION}-cli
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull
  before_script:
    - composer config cache-dir $COMPOSER_CACHE_DIR

.php_with_services: &php_with_services
  <<: *php_base
  services:
    - name: mysql:8.4
      alias: mysql
    - name: redis:7-alpine
      alias: redis
  variables:
    MYSQL_DATABASE: test
    MYSQL_ROOT_PASSWORD: root
    DATABASE_URL: "mysql://root:root@mysql:3306/test"
    REDIS_URL: "redis://redis:6379"
```

## Pipeline Stages

### Install Stage

```yaml
install:
  <<: *php_base
  stage: install
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull-push    # this job populates the cache
  script:
    - composer install --no-progress --prefer-dist --optimize-autoloader
  artifacts:
    paths:
      - vendor/
    expire_in: 1 hour
```

### Lint Stage

```yaml
lint:phpstan:
  <<: *php_base
  stage: lint
  needs: [install]
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G --error-format=gitlab
  artifacts:
    reports:
      codequality: phpstan-report.json
    when: always

lint:cs-fixer:
  <<: *php_base
  stage: lint
  needs: [install]
  script:
    - vendor/bin/php-cs-fixer fix --dry-run --diff --format=gitlab
  artifacts:
    reports:
      codequality: cs-fixer-report.json
    when: always

lint:deptrac:
  <<: *php_base
  stage: lint
  needs: [install]
  script:
    - vendor/bin/deptrac analyse --no-progress --formatter=gitlab
  artifacts:
    reports:
      codequality: deptrac-report.json
    when: always
```

### Test Stage

```yaml
test:unit:
  <<: *php_with_services
  stage: test
  needs: [install]
  script:
    - vendor/bin/phpunit --testsuite unit --coverage-cobertura coverage.xml --log-junit junit.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'
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

test:integration:
  <<: *php_with_services
  stage: test
  needs: [install]
  script:
    - vendor/bin/phpunit --testsuite integration
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
```

### Build Stage

```yaml
build:docker:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  needs: [test:unit]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
    IMAGE_TAG: $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    IMAGE_LATEST: $CI_REGISTRY_IMAGE:latest
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build --cache-from $IMAGE_LATEST -t $IMAGE_TAG -t $IMAGE_LATEST .
    - docker push $IMAGE_TAG
    - docker push $IMAGE_LATEST
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

### Deploy Stage

```yaml
deploy:staging:
  stage: deploy
  image: alpine:latest
  needs: [build:docker]
  environment:
    name: staging
    url: https://staging.example.com
    on_stop: stop:staging
  before_script:
    - apk add --no-cache curl
  script:
    - echo "Deploying $CI_COMMIT_SHA to staging"
    # - kubectl set image deployment/app app=$CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  rules:
    - if: $CI_COMMIT_BRANCH == "main"

deploy:production:
  stage: deploy
  image: alpine:latest
  needs: [deploy:staging]
  environment:
    name: production
    url: https://example.com
  script:
    - echo "Deploying $CI_COMMIT_SHA to production"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual    # require manual approval
  allow_failure: false
```

## Cache Configuration

```yaml
# Global cache (used by all jobs unless overridden)
cache:
  key:
    files:
      - composer.lock
  paths:
    - .composer-cache/
    - vendor/
  policy: pull

# Install job: populate cache
install:
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull-push
```

### Cache Policies

| Policy | Behavior | Use In |
|--------|----------|--------|
| `pull-push` | Download before, upload after | Install job only |
| `pull` | Download before, no upload | All other jobs |
| `push` | No download, upload after | Rare: cache rebuild only |

### Cache Key Strategies

| Strategy | Key | Use Case |
|----------|-----|----------|
| Lock file hash | `files: [composer.lock]` | Best for dependency cache |
| Branch-scoped | `$CI_COMMIT_REF_SLUG` | Branch-specific cache |
| Combined | `prefix-$CI_COMMIT_REF_SLUG` | Prefix + branch scope |
| Global | Fixed string | Shared across all branches |

## Variables and Secrets

### Built-in CI Variables

| Variable | Value | Example |
|----------|-------|---------|
| `$CI_COMMIT_SHA` | Full commit hash | `abc123def456...` |
| `$CI_COMMIT_SHORT_SHA` | Short hash (8 chars) | `abc123de` |
| `$CI_COMMIT_BRANCH` | Branch name | `main`, `feature/login` |
| `$CI_COMMIT_REF_SLUG` | URL-safe branch | `main`, `feature-login` |
| `$CI_PIPELINE_SOURCE` | Trigger source | `push`, `merge_request_event` |
| `$CI_MERGE_REQUEST_IID` | MR number | `42` |
| `$CI_REGISTRY` | Container registry | `registry.gitlab.com` |
| `$CI_REGISTRY_IMAGE` | Project image path | `registry.gitlab.com/group/project` |
| `$CI_PROJECT_DIR` | Checkout directory | `/builds/group/project` |

### Custom Variables

```yaml
variables:
  # Global variables
  PHP_VERSION: "8.4"
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"

# Job-level variables (override global)
test:unit:
  variables:
    DATABASE_URL: "mysql://root:root@mysql:3306/test"
    APP_ENV: "test"
```

### Protected and Masked Variables

Configure in Settings > CI/CD > Variables:

| Setting | Purpose |
|---------|---------|
| Protected | Only available on protected branches/tags |
| Masked | Hidden in job logs (`****`) |
| Environment scope | Limit to specific environment (`production`, `staging`) |
| File | Injected as file path, not value |

## Rules and Conditions

### Modern Rules Syntax (Preferred)

```yaml
test:unit:
  script: vendor/bin/phpunit
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

deploy:production:
  script: ./deploy.sh
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
      allow_failure: false

security:scan:
  script: ./security-check.sh
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - composer.lock
        - Dockerfile
```

### Rules Evaluation

| Condition | Description |
|-----------|-------------|
| `if:` | CI variable expression |
| `changes:` | File path patterns that changed |
| `exists:` | File exists in repository |
| `when: manual` | Require manual trigger |
| `when: delayed` | Delay execution (`start_in: 30 minutes`) |
| `allow_failure: true` | Pipeline continues on job failure |

### Path-Based Rules (Monorepo)

```yaml
test:api:
  script: vendor/bin/phpunit --testsuite api
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - src/Api/**/*
        - src/Domain/**/*
        - tests/Api/**/*

test:worker:
  script: vendor/bin/phpunit --testsuite worker
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      changes:
        - src/Worker/**/*
        - src/Domain/**/*
        - tests/Worker/**/*
```

## Include and Extends

### Include External Files

```yaml
# .gitlab-ci.yml
include:
  - local: .gitlab/ci/lint.yml
  - local: .gitlab/ci/test.yml
  - local: .gitlab/ci/build.yml
  - local: .gitlab/ci/deploy.yml
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Dependency-Scanning.gitlab-ci.yml
```

### Extends for DRY Jobs

```yaml
.test_template:
  stage: test
  needs: [install]
  services:
    - name: mysql:8.4
      alias: mysql
  variables:
    MYSQL_DATABASE: test
    MYSQL_ROOT_PASSWORD: root

test:unit:
  extends: .test_template
  script:
    - vendor/bin/phpunit --testsuite unit

test:integration:
  extends: .test_template
  script:
    - vendor/bin/phpunit --testsuite integration
```

## Full PHP CI Pipeline Example

```yaml
# .gitlab-ci.yml
stages:
  - install
  - lint
  - test
  - build
  - deploy

variables:
  PHP_VERSION: "8.4"
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"

default:
  image: registry.example.com/php-ci:${PHP_VERSION}

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

install:
  stage: install
  cache:
    key:
      files: [composer.lock]
    paths: [.composer-cache/, vendor/]
    policy: pull-push
  script:
    - composer install --no-progress --prefer-dist --optimize-autoloader
  artifacts:
    paths: [vendor/]
    expire_in: 1 hour

lint:phpstan:
  stage: lint
  needs: [install]
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G

lint:cs-fixer:
  stage: lint
  needs: [install]
  script:
    - vendor/bin/php-cs-fixer fix --dry-run --diff

lint:deptrac:
  stage: lint
  needs: [install]
  script:
    - vendor/bin/deptrac analyse --no-progress

test:unit:
  stage: test
  needs: [install]
  services:
    - name: mysql:8.4
      alias: mysql
    - name: redis:7-alpine
      alias: redis
  variables:
    MYSQL_DATABASE: test
    MYSQL_ROOT_PASSWORD: root
    DATABASE_URL: "mysql://root:root@mysql:3306/test"
    REDIS_URL: "redis://redis:6379"
  script:
    - vendor/bin/phpunit --testsuite unit --coverage-cobertura coverage.xml --log-junit junit.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'
  artifacts:
    when: always
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

test:mutation:
  stage: test
  needs: [install]
  script:
    - vendor/bin/infection --min-msi=80 --min-covered-msi=90 --threads=4
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

build:docker:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  needs: [test:unit, lint:phpstan, lint:cs-fixer]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build --cache-from $CI_REGISTRY_IMAGE:latest -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - |
      if [ "$CI_COMMIT_BRANCH" = "main" ]; then
        docker tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA $CI_REGISTRY_IMAGE:latest
        docker push $CI_REGISTRY_IMAGE:latest
      fi
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
    - if: $CI_COMMIT_BRANCH == "develop"

deploy:staging:
  stage: deploy
  needs: [build:docker]
  environment:
    name: staging
    url: https://staging.example.com
  script:
    - echo "Deploying $CI_COMMIT_SHA to staging"
  rules:
    - if: $CI_COMMIT_BRANCH == "develop"

deploy:production:
  stage: deploy
  needs: [build:docker]
  environment:
    name: production
    url: https://example.com
  script:
    - echo "Deploying $CI_COMMIT_SHA to production"
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
  allow_failure: false
```

## Common Issues and Fixes

| Issue | Symptom | Fix |
|-------|---------|-----|
| PHP extensions missing | `Class not found` or `function undefined` | Use custom CI Docker image with pre-installed extensions |
| Composer timeout | `Process timed out` | Set `COMPOSER_PROCESS_TIMEOUT: 600` variable |
| Cache not restoring | Jobs always install from scratch | Check `key:` matches, ensure `policy: pull-push` on install |
| MySQL connection refused | `SQLSTATE[HY000] [2002]` | Use service `alias:` as hostname, wait for healthcheck |
| Redis connection refused | `Connection refused on port 6379` | Use `redis` alias, ensure service is listed |
| `only/except` vs `rules` | Pipeline not triggered | Do not mix `only/except` with `rules`; prefer `rules:` |
| Job stuck pending | No available runner | Check runner tags, ensure shared runners are enabled |
| Artifact too large | Upload fails | Use `expire_in:` and limit `paths:` to necessary files |
| `needs:` job not found | YAML error on pipeline creation | Ensure referenced job exists and is not excluded by `rules:` |
| Coverage not displayed | No percentage in MR | Set `coverage:` regex matching PHPUnit output format |
