# GitLab CI Templates

## Main Pipeline Template

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
  COMPOSER_ARGS: "--no-progress --prefer-dist --optimize-autoloader"
  MYSQL_DATABASE: test
  MYSQL_ROOT_PASSWORD: root

# Include modular configurations
include:
  - local: '.gitlab/ci/templates.yml'
  - local: '.gitlab/ci/lint.yml'
  - local: '.gitlab/ci/test.yml'
  - local: '.gitlab/ci/deploy.yml'

# Default settings
default:
  image: php:${PHP_VERSION}-cli
  interruptible: true
  retry:
    max: 2
    when:
      - runner_system_failure
      - stuck_or_timeout_failure

# Workflow rules
workflow:
  rules:
    - if: $CI_COMMIT_TAG
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_PIPELINE_SOURCE == "web"
```

## Templates Configuration

```yaml
# .gitlab/ci/templates.yml

.php_template:
  image: php:${PHP_VERSION}-cli
  before_script:
    - apt-get update && apt-get install -y git unzip libzip-dev
    - docker-php-ext-install zip pdo pdo_mysql
    - curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull

.with_services:
  services:
    - name: mysql:8.0
      alias: mysql
    - name: redis:7
      alias: redis
  variables:
    MYSQL_DATABASE: test
    MYSQL_ROOT_PASSWORD: root
    DATABASE_URL: "mysql://root:root@mysql:3306/test"
    REDIS_URL: "redis://redis:6379"

.composer_cache:
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull

.composer_cache_push:
  extends: .composer_cache
  cache:
    policy: pull-push

.test_artifacts:
  artifacts:
    when: always
    paths:
      - coverage/
    reports:
      junit: junit.xml
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 7 days

.build_artifacts:
  artifacts:
    paths:
      - build/
    expire_in: 30 days
```

## Linting Configuration

```yaml
# .gitlab/ci/lint.yml

install:
  stage: install
  extends: .php_template
  cache:
    key:
      files:
        - composer.lock
    paths:
      - .composer-cache/
      - vendor/
    policy: pull-push
  script:
    - composer install ${COMPOSER_ARGS}
  artifacts:
    paths:
      - vendor/
    expire_in: 1 hour

phpstan:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G --error-format=gitlab > phpstan.json
  artifacts:
    reports:
      codequality: phpstan.json
    expire_in: 7 days
  rules:
    - exists:
        - phpstan.neon
        - phpstan.neon.dist

psalm:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - vendor/bin/psalm --output-format=checkstyle > psalm-report.xml || true
  artifacts:
    paths:
      - psalm-report.xml
    expire_in: 7 days
  rules:
    - exists:
        - psalm.xml
        - psalm.xml.dist

cs-fixer:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - vendor/bin/php-cs-fixer fix --dry-run --diff --format=gitlab > cs-report.json
  artifacts:
    reports:
      codequality: cs-report.json
    expire_in: 7 days
  rules:
    - exists:
        - .php-cs-fixer.php
        - .php-cs-fixer.dist.php

deptrac:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - vendor/bin/deptrac analyse --formatter=junit --output=deptrac-report.xml
  artifacts:
    reports:
      junit: deptrac-report.xml
    expire_in: 7 days
  rules:
    - exists:
        - deptrac.yaml
        - deptrac.yml
```

## Testing Configuration

```yaml
# .gitlab/ci/test.yml

test:unit:
  stage: test
  extends:
    - .php_template
    - .test_artifacts
  needs: [install, phpstan, psalm, cs-fixer]
  script:
    - vendor/bin/phpunit --testsuite=unit --coverage-cobertura=coverage.xml --log-junit=junit.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'

test:integration:
  stage: test
  extends:
    - .php_template
    - .with_services
    - .test_artifacts
  needs: [install, phpstan, psalm, cs-fixer]
  script:
    - vendor/bin/phpunit --testsuite=integration --coverage-cobertura=coverage.xml --log-junit=junit.xml
  coverage: '/^\s*Lines:\s*\d+.\d+\%/'

test:e2e:
  stage: test
  extends:
    - .php_template
    - .with_services
  needs: [test:unit, test:integration]
  script:
    - vendor/bin/phpunit --testsuite=e2e
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

.test_matrix:
  parallel:
    matrix:
      - PHP_VERSION: ["8.2", "8.3", "8.4"]
        DEPENDENCIES: ["lowest", "highest"]
  script:
    - |
      if [ "$DEPENDENCIES" = "lowest" ]; then
        composer update --prefer-lowest --prefer-stable
      fi
    - vendor/bin/phpunit

test:matrix:
  stage: test
  extends:
    - .php_template
    - .test_matrix
  needs: [install]
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
    - if: $CI_COMMIT_TAG
```

## Deployment Configuration

```yaml
# .gitlab/ci/deploy.yml

build:docker:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  needs: [test:unit, test:integration]
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build
        --cache-from $CI_REGISTRY_IMAGE:latest
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_REF_SLUG
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
    - if: $CI_COMMIT_TAG

build:docker:tagged:
  extends: build:docker
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build
        --tag $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
        --tag $CI_REGISTRY_IMAGE:latest
        .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
    - docker push $CI_REGISTRY_IMAGE:latest
  rules:
    - if: $CI_COMMIT_TAG

deploy:staging:
  stage: deploy
  image: alpine:latest
  needs: [build:docker]
  environment:
    name: staging
    url: https://staging.example.com
    on_stop: stop:staging
  before_script:
    - apk add --no-cache curl openssh-client
  script:
    - echo "Deploying to staging..."
    - |
      ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$STAGING_HOST << EOF
        docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
        docker-compose -f docker-compose.staging.yml up -d
      EOF
    - curl --fail https://staging.example.com/health
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

stop:staging:
  stage: deploy
  image: alpine:latest
  environment:
    name: staging
    action: stop
  script:
    - echo "Stopping staging environment"
  when: manual
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
      when: manual

deploy:production:
  stage: deploy
  image: alpine:latest
  needs: [deploy:staging]
  environment:
    name: production
    url: https://example.com
  before_script:
    - apk add --no-cache curl openssh-client
  script:
    - echo "Deploying to production..."
    - |
      ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$PROD_HOST << EOF
        docker pull $CI_REGISTRY_IMAGE:$CI_COMMIT_TAG
        docker-compose -f docker-compose.prod.yml up -d
      EOF
    - curl --fail https://example.com/health
  rules:
    - if: $CI_COMMIT_TAG
      when: manual
```

## Security Scanning Configuration

```yaml
include:
  - template: Security/Dependency-Scanning.gitlab-ci.yml
  - template: Security/SAST.gitlab-ci.yml
  - template: Security/Secret-Detection.gitlab-ci.yml
  - template: Security/Container-Scanning.gitlab-ci.yml

security:composer-audit:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - composer audit --format=json > composer-audit.json
  artifacts:
    paths:
      - composer-audit.json
    expire_in: 30 days
  allow_failure: true

security:psalm-taint:
  stage: lint
  extends: .php_template
  needs: [install]
  script:
    - vendor/bin/psalm --taint-analysis
  allow_failure: true
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
```

## Scheduled Pipeline Configuration

```yaml
test:weekly:
  stage: test
  extends: .php_template
  rules:
    - if: $CI_PIPELINE_SOURCE == "schedule"
  script:
    - composer update
    - vendor/bin/phpunit --coverage-text

# Security scan schedule (configure in GitLab UI)
# Schedule: 0 0 * * 1 (Every Monday at midnight)
```
