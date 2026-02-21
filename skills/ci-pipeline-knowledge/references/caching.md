# CI/CD Caching Strategies for PHP

Deep dive into caching strategies for PHP CI/CD pipelines across GitHub Actions and GitLab CI.

## Detection Patterns

```bash
# Detect GitHub Actions cache usage
Grep: "actions/cache@" --glob ".github/workflows/*.yml"
Grep: "cache-from.*type=gha" --glob ".github/workflows/*.yml"

# Detect GitLab CI cache configuration
Grep: "cache:" --glob ".gitlab-ci.yml"
Grep: "policy:" --glob ".gitlab-ci.yml"

# Detect Composer cache directory configuration
Grep: "COMPOSER_CACHE_DIR" --glob ".github/workflows/*.yml"
Grep: "COMPOSER_CACHE_DIR" --glob ".gitlab-ci.yml"

# Detect Docker layer caching
Grep: "setup-buildx-action" --glob ".github/workflows/*.yml"
Grep: "cache-from" --glob ".github/workflows/*.yml"
Grep: "cache-from" --glob ".gitlab-ci.yml"

# Detect PHPStan result cache
Grep: "tmpDir\|resultCachePath" --glob "phpstan.neon*"
Grep: "phpstan.*cache\|\.phpstan-cache" --glob ".github/workflows/*.yml" --glob ".gitlab-ci.yml"

# Detect missing cache configuration (potential issue)
Grep: "composer install" --glob ".github/workflows/*.yml" --glob ".gitlab-ci.yml"
# Then verify actions/cache or cache: is present in same file
```

## Composer Vendor Caching

### GitHub Actions: Composer Cache

```yaml
# Strategy 1: Cache vendor directory (fastest restore)
- name: Cache vendor
  uses: actions/cache@v4
  with:
    path: vendor
    key: vendor-${{ runner.os }}-php${{ matrix.php }}-${{ hashFiles('composer.lock') }}
    restore-keys: |
      vendor-${{ runner.os }}-php${{ matrix.php }}-

# Strategy 2: Cache Composer download cache (smaller, cross-project reuse)
- name: Cache Composer downloads
  uses: actions/cache@v4
  with:
    path: ~/.composer/cache
    key: composer-${{ runner.os }}-${{ hashFiles('composer.lock') }}
    restore-keys: |
      composer-${{ runner.os }}-

# Strategy 3: Cache both (recommended for full pipeline)
- name: Cache Composer
  uses: actions/cache@v4
  with:
    path: |
      ~/.composer/cache
      vendor
    key: php-${{ runner.os }}-${{ matrix.php }}-${{ hashFiles('composer.lock') }}
    restore-keys: |
      php-${{ runner.os }}-${{ matrix.php }}-
```

### GitLab CI: Composer Cache

```yaml
# Strategy 1: Lock file hash key (recommended)
cache:
  key:
    files:
      - composer.lock
  paths:
    - .composer-cache/
    - vendor/
  policy: pull

# Strategy 2: Branch-scoped cache
cache:
  key: composer-$CI_COMMIT_REF_SLUG
  paths:
    - .composer-cache/
    - vendor/
  policy: pull

# Strategy 3: Combined prefix + lock file
cache:
  key:
    prefix: php-${PHP_VERSION}
    files:
      - composer.lock
  paths:
    - .composer-cache/
    - vendor/
  policy: pull
```

### Composer Cache Variables

```yaml
# GitHub Actions
env:
  COMPOSER_CACHE_DIR: ~/.composer/cache
  COMPOSER_NO_INTERACTION: 1
  COMPOSER_PROCESS_TIMEOUT: 600

# GitLab CI
variables:
  COMPOSER_CACHE_DIR: "$CI_PROJECT_DIR/.composer-cache"
  COMPOSER_NO_INTERACTION: "1"
  COMPOSER_PROCESS_TIMEOUT: "600"
```

### Bad vs Good: Composer Caching

**Bad: No cache, install in every job**

```yaml
# BAD: 60-90 seconds per job, repeated network calls
jobs:
  lint:
    steps:
      - run: composer install --no-progress
  test:
    steps:
      - run: composer install --no-progress
  build:
    steps:
      - run: composer install --no-progress
```

**Good: Shared cache with proper key**

```yaml
# GOOD: Cache restored in ~5 seconds, install is a no-op
jobs:
  install:
    steps:
      - uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ hashFiles('composer.lock') }}
      - run: composer install --no-progress --prefer-dist
  lint:
    needs: install
    steps:
      - uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ hashFiles('composer.lock') }}
      - run: vendor/bin/phpstan analyse
```

## Docker Layer Caching

### GitHub Actions: BuildKit GHA Cache

```yaml
- uses: docker/setup-buildx-action@v3

- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

### GitHub Actions: Registry Cache

```yaml
- uses: docker/build-push-action@v5
  with:
    context: .
    push: true
    tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
    cache-from: type=registry,ref=ghcr.io/${{ github.repository }}:cache
    cache-to: type=registry,ref=ghcr.io/${{ github.repository }}:cache,mode=max
```

### GitLab CI: Registry Cache

```yaml
build:docker:
  image: docker:24
  services:
    - docker:24-dind
  variables:
    DOCKER_BUILDKIT: 1
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - >
      docker build
      --cache-from $CI_REGISTRY_IMAGE:latest
      --build-arg BUILDKIT_INLINE_CACHE=1
      -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      -t $CI_REGISTRY_IMAGE:latest
      .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE:latest
```

### GitLab CI: Kaniko (No Docker-in-Docker)

```yaml
build:docker:
  image:
    name: gcr.io/kaniko-project/executor:debug
    entrypoint: [""]
  script:
    - >
      /kaniko/executor
      --context $CI_PROJECT_DIR
      --dockerfile $CI_PROJECT_DIR/Dockerfile
      --destination $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      --cache=true
      --cache-repo=$CI_REGISTRY_IMAGE/cache
```

### Docker Layer Cache Comparison

| Method | Platform | Speed | Storage | Setup |
|--------|----------|-------|---------|-------|
| GHA cache (`type=gha`) | GitHub | Fast | GitHub cache (10GB limit) | Simple |
| Registry cache | Both | Medium | Container registry | Medium |
| Inline cache | Both | Medium | Image layers | Simple |
| Kaniko | GitLab | Medium | Container registry | No DinD needed |
| Local volume | Self-hosted | Fastest | Runner disk | Runner config |

### Bad vs Good: Docker Layer Caching

**Bad: No layer caching**

```yaml
# BAD: Full build every time (5-15 minutes)
build:
  script:
    - docker build -t myapp:latest .
```

**Good: Multi-layer cache with BuildKit**

```yaml
# GOOD: Cached layers restored, only changed layers rebuilt (30-60 seconds)
build:
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - >
      docker build
      --cache-from $CI_REGISTRY_IMAGE:latest
      --build-arg BUILDKIT_INLINE_CACHE=1
      -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
      .
```

## Static Analysis Result Caching

### PHPStan Result Cache

```neon
# phpstan.neon
parameters:
    tmpDir: .phpstan-cache
    resultCachePath: .phpstan-cache/resultCache.php
```

```yaml
# GitHub Actions
- name: Cache PHPStan results
  uses: actions/cache@v4
  with:
    path: .phpstan-cache
    key: phpstan-${{ github.sha }}
    restore-keys: |
      phpstan-

# GitLab CI
lint:phpstan:
  cache:
    - key:
        files: [composer.lock]
      paths: [vendor/]
      policy: pull
    - key: phpstan-$CI_COMMIT_REF_SLUG
      paths: [.phpstan-cache/]
      policy: pull-push
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G
```

### Psalm Result Cache

```xml
<!-- psalm.xml -->
<psalm cacheDirectory=".psalm-cache">
    <!-- ... -->
</psalm>
```

```yaml
# GitHub Actions
- name: Cache Psalm results
  uses: actions/cache@v4
  with:
    path: .psalm-cache
    key: psalm-${{ github.sha }}
    restore-keys: |
      psalm-

# GitLab CI
lint:psalm:
  cache:
    - key: psalm-$CI_COMMIT_REF_SLUG
      paths: [.psalm-cache/]
      policy: pull-push
  script:
    - vendor/bin/psalm --no-progress
```

### PHP-CS-Fixer Cache

```yaml
# .php-cs-fixer.dist.php
return (new PhpCsFixer\Config())
    ->setCacheFile('.php-cs-fixer.cache')
    // ...
;
```

```yaml
# GitHub Actions
- name: Cache PHP-CS-Fixer
  uses: actions/cache@v4
  with:
    path: .php-cs-fixer.cache
    key: cs-fixer-${{ github.sha }}
    restore-keys: |
      cs-fixer-

# GitLab CI
lint:cs-fixer:
  cache:
    - key: cs-fixer-$CI_COMMIT_REF_SLUG
      paths: [.php-cs-fixer.cache]
      policy: pull-push
  script:
    - vendor/bin/php-cs-fixer fix --dry-run --diff
```

## Cache Invalidation Strategies

### Hash-Based Invalidation (Recommended)

```yaml
# GitHub Actions: hashFiles() function
key: vendor-${{ hashFiles('composer.lock') }}
key: npm-${{ hashFiles('package-lock.json') }}
key: docker-${{ hashFiles('Dockerfile', 'docker/**') }}

# GitLab CI: files-based key
cache:
  key:
    files:
      - composer.lock
```

### Time-Based Invalidation

```yaml
# GitHub Actions: weekly cache refresh
key: vendor-week${{ github.run_number / 7 }}-${{ hashFiles('composer.lock') }}

# GitLab CI: date prefix (manual invalidation by changing variable)
variables:
  CACHE_VERSION: "2025-01"
cache:
  key: $CACHE_VERSION-$CI_COMMIT_REF_SLUG
```

### Manual Invalidation

```yaml
# GitHub Actions: increment version to bust cache
env:
  CACHE_VERSION: v2   # change to v3 to invalidate
# ...
key: ${{ env.CACHE_VERSION }}-vendor-${{ hashFiles('composer.lock') }}

# GitLab CI: CI/CD variable
variables:
  CACHE_VERSION: "v2"  # change in Settings > CI/CD > Variables
cache:
  key: ${CACHE_VERSION}-$CI_COMMIT_REF_SLUG
```

### Bad vs Good: Cache Invalidation

**Bad: Branch-only key (stale dependencies)**

```yaml
# BAD: Cache never updates when composer.lock changes
cache:
  key: $CI_COMMIT_REF_SLUG
  paths:
    - vendor/
```

**Good: Lock file hash (precise invalidation)**

```yaml
# GOOD: Cache invalidates exactly when dependencies change
cache:
  key:
    files:
      - composer.lock
  paths:
    - vendor/
```

## Cache Scope

### GitHub Actions Cache Scope

```
Repository cache (10GB limit)
├── Branch: main
│   └── key: vendor-abc123 (available to all branches as fallback)
├── Branch: feature/login
│   └── key: vendor-def456 (branch-specific)
└── PR #42
    └── key: vendor-def456 (inherits from source branch + main)
```

Cache scope rules:
- A workflow run can restore caches created in the current branch or the default branch
- A PR can access caches from the base branch
- Caches are scoped to the repository, not the workflow

### GitLab CI Cache Scope

```
Runner cache
├── Protected branches
│   └── key: composer-main (only accessible by protected branch jobs)
├── Unprotected branches
│   └── key: composer-feature-login (accessible by all unprotected jobs)
└── Shared runners
    └── Distributed cache (S3/GCS) recommended
```

### Scope Best Practices

| Platform | Strategy | Configuration |
|----------|----------|---------------|
| GitHub Actions | Fallback keys | `restore-keys:` with progressively shorter prefix |
| GitLab CI | Branch-scoped | `key: prefix-$CI_COMMIT_REF_SLUG` |
| GitLab CI | Protected | Separate cache for protected branches |
| Both | Version prefix | `key: v2-vendor-...` for manual invalidation |

## Complete Caching Configuration

### GitHub Actions: Full Cache Setup

```yaml
jobs:
  ci:
    steps:
      - uses: actions/checkout@v4
      - uses: shivammathur/setup-php@v2
        with:
          php-version: '8.4'
          coverage: xdebug

      # Composer vendor cache
      - name: Cache Composer vendor
        uses: actions/cache@v4
        with:
          path: vendor
          key: vendor-${{ runner.os }}-php8.4-${{ hashFiles('composer.lock') }}
          restore-keys: |
            vendor-${{ runner.os }}-php8.4-

      # PHPStan result cache
      - name: Cache PHPStan
        uses: actions/cache@v4
        with:
          path: .phpstan-cache
          key: phpstan-${{ github.sha }}
          restore-keys: phpstan-

      # PHP-CS-Fixer cache
      - name: Cache CS-Fixer
        uses: actions/cache@v4
        with:
          path: .php-cs-fixer.cache
          key: cs-fixer-${{ github.sha }}
          restore-keys: cs-fixer-

      - run: composer install --no-progress --prefer-dist
      - run: vendor/bin/phpstan analyse
      - run: vendor/bin/php-cs-fixer fix --dry-run
      - run: vendor/bin/phpunit --coverage-clover coverage.xml
```

### GitLab CI: Full Cache Setup

```yaml
test:
  stage: test
  cache:
    # Cache 1: Composer dependencies (lock-file keyed)
    - key:
        files: [composer.lock]
      paths:
        - .composer-cache/
        - vendor/
      policy: pull
    # Cache 2: PHPStan results (branch-scoped)
    - key: phpstan-$CI_COMMIT_REF_SLUG
      paths:
        - .phpstan-cache/
      policy: pull-push
    # Cache 3: PHP-CS-Fixer results (branch-scoped)
    - key: cs-fixer-$CI_COMMIT_REF_SLUG
      paths:
        - .php-cs-fixer.cache
      policy: pull-push
  script:
    - composer install --no-progress --prefer-dist
    - vendor/bin/phpstan analyse
    - vendor/bin/php-cs-fixer fix --dry-run
    - vendor/bin/phpunit
```

## Summary Table

| Cache Target | Key Pattern | Paths | Invalidation | Time Saved |
|-------------|-------------|-------|--------------|------------|
| Composer vendor | `hashFiles('composer.lock')` | `vendor/` | Lock file changes | 30-90s |
| Composer downloads | `hashFiles('composer.lock')` | `~/.composer/cache` | Lock file changes | 20-60s |
| PHPStan results | `${{ github.sha }}` with fallback | `.phpstan-cache/` | Every commit (incremental) | 10-60s |
| Psalm results | `${{ github.sha }}` with fallback | `.psalm-cache/` | Every commit (incremental) | 10-60s |
| PHP-CS-Fixer | `${{ github.sha }}` with fallback | `.php-cs-fixer.cache` | Every commit (incremental) | 5-20s |
| Docker layers (GHA) | Automatic | GitHub cache storage | Dockerfile/context changes | 2-10min |
| Docker layers (Registry) | Image tag | Container registry | Dockerfile/context changes | 2-10min |
| Node modules | `hashFiles('package-lock.json')` | `node_modules/` | Lock file changes | 20-60s |

## Cache Size Optimization

| Technique | Before | After | How |
|-----------|--------|-------|-----|
| `--prefer-dist` | Source archives | Zip archives | Composer flag |
| `--no-dev` in build | All packages | Production only | Composer flag |
| `.composer-cache` only | vendor + cache | Download cache | Cache path selection |
| Exclude test fixtures | Full vendor | Trimmed vendor | `.gitattributes` export-ignore |
| GHA cache pruning | 10GB limit hit | Under limit | Automatic LRU eviction |
| GitLab `expire_in` | Unlimited | Time-limited | `artifacts: expire_in: 7 days` |
