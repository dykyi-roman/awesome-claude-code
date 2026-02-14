# GitHub Actions Workflow Templates

Complete YAML workflow templates for PHP projects.

## Main CI Workflow

```yaml
# .github/workflows/ci.yml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

env:
  PHP_VERSION: '8.4'
  COMPOSER_ARGS: '--no-progress --prefer-dist --optimize-autoloader'

jobs:
  #############################################
  # Stage 1: Install Dependencies
  #############################################
  install:
    name: Install Dependencies
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          extensions: mbstring, xml, ctype, json, pdo, pdo_mysql, redis
          coverage: none
          tools: composer:v2

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

      - name: Install dependencies
        run: composer install ${{ env.COMPOSER_ARGS }}

      - name: Upload vendor
        uses: actions/upload-artifact@v4
        with:
          name: vendor
          path: vendor
          retention-days: 1

  #############################################
  # Stage 2: Static Analysis (Parallel)
  #############################################
  phpstan:
    name: PHPStan
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: none

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Run PHPStan
        run: vendor/bin/phpstan analyse --memory-limit=1G --error-format=github

  psalm:
    name: Psalm
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: none

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Run Psalm
        run: vendor/bin/psalm --output-format=github

  cs-fixer:
    name: PHP-CS-Fixer
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: none

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Check code style
        run: vendor/bin/php-cs-fixer fix --dry-run --diff

  deptrac:
    name: Deptrac
    needs: install
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: none

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Check architecture
        run: vendor/bin/deptrac analyse --fail-on-uncovered

  #############################################
  # Stage 3: Tests
  #############################################
  test-unit:
    name: Unit Tests
    needs: [phpstan, psalm, cs-fixer]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: pcov

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Run unit tests
        run: vendor/bin/phpunit --testsuite=unit --coverage-clover=coverage-unit.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage-unit.xml
          flags: unit
          token: ${{ secrets.CODECOV_TOKEN }}

  test-integration:
    name: Integration Tests
    needs: [phpstan, psalm, cs-fixer]
    runs-on: ubuntu-latest
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
          --health-retries=3

      redis:
        image: redis:7
        ports:
          - 6379:6379
        options: >-
          --health-cmd="redis-cli ping"
          --health-interval=10s
          --health-timeout=5s
          --health-retries=3

    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
          coverage: pcov

      - uses: actions/download-artifact@v4
        with:
          name: vendor
          path: vendor

      - name: Run integration tests
        env:
          DATABASE_URL: mysql://root:root@127.0.0.1:3306/test
          REDIS_URL: redis://127.0.0.1:6379
        run: vendor/bin/phpunit --testsuite=integration --coverage-clover=coverage-integration.xml

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: coverage-integration.xml
          flags: integration
          token: ${{ secrets.CODECOV_TOKEN }}

  #############################################
  # Stage 4: Build (only on main/tags)
  #############################################
  build:
    name: Build Docker Image
    needs: [test-unit, test-integration]
    if: github.ref == 'refs/heads/main' || startsWith(github.ref, 'refs/tags/')
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ghcr.io/${{ github.repository }}
          tags: |
            type=ref,event=branch
            type=semver,pattern={{version}}
            type=sha,prefix=

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## Security Workflow

```yaml
# .github/workflows/security.yml
name: Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 1'  # Weekly Monday

jobs:
  dependency-audit:
    name: Dependency Audit
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          tools: composer:v2

      - name: Install dependencies
        run: composer install --no-progress --prefer-dist

      - name: Check for vulnerabilities
        run: composer audit

  psalm-security:
    name: Psalm Taint Analysis
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'

      - name: Install dependencies
        run: composer install --no-progress --prefer-dist

      - name: Run taint analysis
        run: vendor/bin/psalm --taint-analysis

  trivy:
    name: Trivy Container Scan
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Build image
        run: docker build -t app:scan .

      - name: Run Trivy
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: app:scan
          format: sarif
          output: trivy-results.sarif

      - name: Upload results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: trivy-results.sarif
```

## Deploy Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy-staging:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    environment:
      name: staging
      url: https://staging.example.com
    if: github.event_name == 'push' || github.event.inputs.environment == 'staging'
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          echo "Deploying to staging..."
          # Add deployment commands

      - name: Health check
        run: |
          curl --fail https://staging.example.com/health || exit 1

  deploy-production:
    name: Deploy to Production
    runs-on: ubuntu-latest
    needs: deploy-staging
    environment:
      name: production
      url: https://example.com
    if: startsWith(github.ref, 'refs/tags/v') || github.event.inputs.environment == 'production'
    steps:
      - uses: actions/checkout@v4

      - name: Deploy to production
        env:
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY_PROD }}
        run: |
          echo "Deploying to production..."
          # Add deployment commands

      - name: Health check
        run: |
          curl --fail https://example.com/health || exit 1

      - name: Notify success
        if: success()
        run: |
          echo "Deployment successful!"
```

## Matrix Testing

```yaml
# For testing across PHP versions
test:
  strategy:
    fail-fast: false
    matrix:
      php: ['8.2', '8.3', '8.4']
      dependencies: ['lowest', 'highest']
      include:
        - php: '8.4'
          dependencies: 'highest'
          coverage: true
  runs-on: ubuntu-latest
  steps:
    - uses: shivammathur/setup-php@v2
      with:
        php-version: ${{ matrix.php }}
        coverage: ${{ matrix.coverage && 'pcov' || 'none' }}

    - name: Install dependencies
      run: |
        if [ "${{ matrix.dependencies }}" = "lowest" ]; then
          composer update --prefer-lowest --prefer-stable
        else
          composer install
        fi

    - name: Run tests
      run: vendor/bin/phpunit
```
