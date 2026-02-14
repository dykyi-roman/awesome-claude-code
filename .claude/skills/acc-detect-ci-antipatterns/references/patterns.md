# CI Antipattern Detector — Detection Patterns & Examples

## 1. Performance Antipatterns

### Sequential When Parallel Possible

```yaml
# ANTIPATTERN: Jobs that could run in parallel are sequential
jobs:
  phpstan:
    runs-on: ubuntu-latest
    # ...

  psalm:
    needs: phpstan  # Unnecessary dependency!
    runs-on: ubuntu-latest
    # ...

  phpunit:
    needs: psalm  # Unnecessary dependency!
    runs-on: ubuntu-latest
    # ...
```

```yaml
# FIX: Run independent jobs in parallel
jobs:
  lint:
    strategy:
      matrix:
        tool: [phpstan, psalm, cs-fixer]
    runs-on: ubuntu-latest
    steps:
      - run: vendor/bin/${{ matrix.tool }}

  phpunit:
    runs-on: ubuntu-latest  # No needs, runs in parallel
    # ...
```

### Installing Dependencies in Every Job

```yaml
# ANTIPATTERN: Composer install in every job
jobs:
  phpstan:
    steps:
      - run: composer install
      - run: vendor/bin/phpstan

  phpunit:
    steps:
      - run: composer install  # Duplicate!
      - run: vendor/bin/phpunit
```

```yaml
# FIX: Install once, share via artifacts
jobs:
  install:
    steps:
      - run: composer install
      - uses: actions/upload-artifact@v4
        with:
          name: vendor
          path: vendor

  phpstan:
    needs: install
    steps:
      - uses: actions/download-artifact@v4
        with:
          name: vendor
      - run: vendor/bin/phpstan
```

### No Caching

```yaml
# ANTIPATTERN: No cache configuration
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - run: composer install  # Downloads everything every time
```

```yaml
# FIX: Cache dependencies
jobs:
  test:
    steps:
      - uses: actions/checkout@v4
      - uses: actions/cache@v4
        with:
          path: |
            ~/.composer/cache
            vendor
          key: deps-${{ hashFiles('composer.lock') }}
      - run: composer install
```

## 2. Security Antipatterns

### Secrets in Logs

```yaml
# ANTIPATTERN: Secret exposed in logs
- run: |
    echo "Deploying with key: ${{ secrets.DEPLOY_KEY }}"
    curl -H "Authorization: ${{ secrets.API_TOKEN }}" https://api.example.com
```

```yaml
# FIX: Use environment variables, mask output
- run: |
    echo "Deploying..."
    curl -H "Authorization: Bearer ${API_TOKEN}" https://api.example.com
  env:
    API_TOKEN: ${{ secrets.API_TOKEN }}
```

### Mutable Action References

```yaml
# ANTIPATTERN: Using mutable tags
- uses: actions/checkout@main
- uses: actions/setup-php@v2
```

```yaml
# FIX: Pin to SHA or specific version
- uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11  # v4.1.1
- uses: shivammathur/setup-php@6d7209f44a25a59e904b1ee9f3b0c33ab2cd888d  # v2.27.1
```

### Overly Permissive Permissions

```yaml
# ANTIPATTERN: Default permissions (write-all)
name: CI
on: push
jobs:
  build:
    runs-on: ubuntu-latest
```

```yaml
# FIX: Minimal permissions
name: CI
on: push

permissions:
  contents: read

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write  # Only if needed
```

### Unsafe pull_request_target

```yaml
# ANTIPATTERN: Running untrusted code with secrets
on:
  pull_request_target:
jobs:
  build:
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Untrusted!
      - run: ./scripts/build.sh  # Runs attacker's code with secrets
```

```yaml
# FIX: Separate trusted and untrusted workflows
# For tests (no secrets needed):
on: pull_request

# For deployments (needs secrets):
on:
  pull_request_target:
jobs:
  build:
    steps:
      - uses: actions/checkout@v4  # Uses base branch (trusted)
```

## 3. Maintenance Antipatterns

### Duplicated Configuration

```yaml
# ANTIPATTERN: Copy-pasted steps
jobs:
  test-php82:
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.2'
      - run: composer install
      - run: vendor/bin/phpunit

  test-php83:
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.3'  # Only difference!
      - run: composer install
      - run: vendor/bin/phpunit
```

```yaml
# FIX: Use matrix strategy
jobs:
  test:
    strategy:
      matrix:
        php: ['8.2', '8.3', '8.4']
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ matrix.php }}
      - run: composer install
      - run: vendor/bin/phpunit
```

### Hardcoded Values

```yaml
# ANTIPATTERN: Hardcoded versions everywhere
- uses: shivammathur/setup-php@v2
  with:
    php-version: '8.4'
# ... later ...
- run: docker build --build-arg PHP_VERSION=8.4
```

```yaml
# FIX: Centralize in env
env:
  PHP_VERSION: '8.4'

jobs:
  build:
    steps:
      - uses: shivammathur/setup-php@v2
        with:
          php-version: ${{ env.PHP_VERSION }}
      - run: docker build --build-arg PHP_VERSION=${{ env.PHP_VERSION }}
```

### No Workflow Reuse

```yaml
# ANTIPATTERN: Same steps in multiple workflows
# ci.yml, deploy.yml, release.yml all have identical test steps
```

```yaml
# FIX: Reusable workflow
# .github/workflows/test.yml
name: Test
on:
  workflow_call:
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: composer install
      - run: vendor/bin/phpunit

# .github/workflows/ci.yml
name: CI
on: push
jobs:
  test:
    uses: ./.github/workflows/test.yml
```

## 4. Reliability Antipatterns

### No Timeouts

```yaml
# ANTIPATTERN: No timeout, can hang forever
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: vendor/bin/phpunit
```

```yaml
# FIX: Set appropriate timeouts
jobs:
  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    steps:
      - run: vendor/bin/phpunit
        timeout-minutes: 20
```

### No Retry for Flaky Operations

```yaml
# ANTIPATTERN: Network operations without retry
- run: composer install
```

```yaml
# FIX: Add retry for flaky operations
jobs:
  install:
    runs-on: ubuntu-latest
    steps:
      - run: composer install
        continue-on-error: true
        id: install
      - run: composer install
        if: steps.install.outcome == 'failure'
```

### Missing Health Checks

```yaml
# ANTIPATTERN: No service health check
services:
  mysql:
    image: mysql:8.0
# Tests start immediately, may fail if MySQL not ready
```

```yaml
# FIX: Add health check
services:
  mysql:
    image: mysql:8.0
    options: >-
      --health-cmd="mysqladmin ping"
      --health-interval=10s
      --health-timeout=5s
      --health-retries=3
```
