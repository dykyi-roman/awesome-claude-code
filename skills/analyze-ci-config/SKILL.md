---
name: analyze-ci-config
description: Analyzes existing CI/CD configurations. Detects issues in GitHub Actions and GitLab CI files, checks for best practices, caching efficiency, and security concerns.
---

# CI Configuration Analyzer

Analyzes CI/CD configurations for issues, optimizations, and best practices.

## Analysis Categories

### 1. Structure Analysis

```
┌─────────────────────────────────────────────────────────────────┐
│                    CI CONFIG ANALYSIS                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✓ Stages defined: install → lint → test → build → deploy      │
│  ✓ Jobs properly ordered                                        │
│  ✗ Missing concurrency control                                  │
│  ✗ No timeout configuration                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Caching Analysis

| Issue | Severity | Location | Recommendation |
|-------|----------|----------|----------------|
| No Composer cache | 🟠 Major | `lint` job | Add `actions/cache` for `~/.composer/cache` |
| Invalid cache key | 🟡 Minor | Line 23 | Use `hashFiles('composer.lock')` |
| Missing vendor cache | 🟠 Major | All jobs | Share vendor between jobs with artifacts |

### 3. Security Analysis

| Issue | Severity | Location | Risk |
|-------|----------|----------|------|
| `pull_request_target` misuse | 🔴 Critical | Line 5 | Code injection from forks |
| Secrets in logs | 🔴 Critical | Line 45 | `echo ${{ secrets.API_KEY }}` exposed |
| Outdated actions | 🟠 Major | Lines 12, 18 | Using `@v1` instead of `@v4` |
| No permissions defined | 🟡 Minor | - | Uses default (write-all) |

## GitHub Actions Analysis

### Checklist

```markdown
## GitHub Actions Analysis Report

### Configuration: `.github/workflows/ci.yml`

#### Structure ✓
- [x] Valid YAML syntax
- [x] Proper job dependencies (needs)
- [ ] Concurrency configuration
- [ ] Timeout defined for jobs
- [x] Workflow triggers appropriate

#### Caching ⚠️
- [ ] Composer dependencies cached
- [ ] Node modules cached (if applicable)
- [x] Docker layer caching
- [ ] Cache keys use file hashes

#### Security 🔴
- [ ] Permissions explicitly defined
- [ ] No secrets echoed
- [x] Actions pinned to SHA
- [ ] pull_request_target safe usage

#### Performance ⚠️
- [ ] Jobs run in parallel where possible
- [x] Matrix strategy for PHP versions
- [ ] Fail-fast disabled for matrix
- [ ] Artifacts shared between jobs

#### Best Practices ✓
- [x] Uses specific action versions
- [x] Environment variables centralized
- [ ] Reusable workflows
- [x] Clear job names
```

### Common Issues

#### 1. Missing Concurrency

```yaml
# ❌ BAD: No concurrency control
name: CI
on: [push, pull_request]

# ✅ GOOD: Cancel redundant runs
name: CI
on: [push, pull_request]

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true
```

#### 2. Inefficient Caching

```yaml
# ❌ BAD: Cache key doesn't include lock file
- uses: actions/cache@v4
  with:
    path: vendor
    key: vendor-${{ github.sha }}

# ✅ GOOD: Cache key based on lock file
- uses: actions/cache@v4
  with:
    path: |
      ~/.composer/cache
      vendor
    key: composer-${{ hashFiles('composer.lock') }}
    restore-keys: composer-
```

#### 3. Security Issues

```yaml
# ❌ BAD: Dangerous with forks
on:
  pull_request_target:
    types: [opened]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          ref: ${{ github.event.pull_request.head.sha }}  # Runs untrusted code

# ✅ GOOD: Separate trusted/untrusted
on:
  pull_request:  # Safe: runs in context of base
```

## GitLab CI Analysis

### Checklist

```markdown
## GitLab CI Analysis Report

### Configuration: `.gitlab-ci.yml`

#### Structure ✓
- [x] Valid YAML syntax
- [x] Stages defined
- [x] Jobs assigned to stages
- [ ] Global variables defined
- [x] Default image set

#### Caching ⚠️
- [ ] Cache key uses files hash
- [ ] Cache policy appropriate (pull/push)
- [x] Cache paths correct
- [ ] Artifacts used for job sharing

#### Security ⚠️
- [x] Secrets in CI/CD variables (not code)
- [ ] Protected branches configured
- [ ] No sensitive data in artifacts
- [x] Image from trusted registry

#### Performance ⚠️
- [ ] Jobs run in parallel
- [x] Needs keyword for dependencies
- [ ] Rules/only properly configured
- [ ] DAG mode enabled

#### Best Practices ✓
- [x] Uses extends for reuse
- [x] Clear job names
- [ ] Include for modular config
- [x] Appropriate timeouts
```

### Common Issues

#### 1. Cache Key Without Hash

```yaml
# ❌ BAD: Cache never invalidates properly
cache:
  key: composer-cache
  paths:
    - vendor/

# ✅ GOOD: Cache invalidates on lock change
cache:
  key:
    files:
      - composer.lock
  paths:
    - vendor/
```

#### 2. Missing Needs

```yaml
# ❌ BAD: Sequential stages, no parallelism
stages:
  - lint
  - test

phpstan:
  stage: lint
  script: vendor/bin/phpstan

phpunit:
  stage: test  # Waits for ALL lint jobs

# ✅ GOOD: DAG with needs
phpunit:
  stage: test
  needs: [composer-install]  # Only waits for install
```

## Analysis Output Format

```markdown
# CI/CD Configuration Analysis

**File:** `.github/workflows/ci.yml`
**Platform:** GitHub Actions
**Date:** 2024-01-15

## Summary

| Category | Status | Issues |
|----------|--------|--------|
| Structure | ✅ Good | 0 |
| Caching | ⚠️ Warning | 3 |
| Security | 🔴 Critical | 2 |
| Performance | ⚠️ Warning | 4 |
| Best Practices | ✅ Good | 1 |

**Total Issues:** 10 (2 Critical, 4 Major, 4 Minor)

## Critical Issues

### SEC-001: Exposed Secret in Logs
**Location:** Line 45
**Code:**
```yaml
- run: echo "Deploying with ${{ secrets.DEPLOY_KEY }}"
```
**Risk:** Secret visible in workflow logs
**Fix:**
```yaml
- run: echo "Deploying..."
  env:
    DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
```

### SEC-002: pull_request_target with Checkout
**Location:** Lines 3, 15
**Risk:** Arbitrary code execution from forks
**Fix:** Use `pull_request` event instead, or don't checkout PR code

## Major Issues

### CACHE-001: Missing Composer Cache
**Location:** `lint` job
**Impact:** +2-3 minutes per run
**Fix:**
```yaml
- uses: actions/cache@v4
  with:
    path: ~/.composer/cache
    key: composer-${{ hashFiles('composer.lock') }}
```

### PERF-001: Sequential Jobs Could Run Parallel
**Location:** `test-unit`, `test-integration`
**Impact:** +5 minutes total
**Fix:** Remove `needs` dependency between test jobs

## Minor Issues

### BP-001: Using Outdated Action Version
**Location:** Line 12
**Current:** `actions/checkout@v2`
**Recommended:** `actions/checkout@v4`

## Recommendations

1. **Immediate:** Fix security issues SEC-001 and SEC-002
2. **Short-term:** Implement caching improvements
3. **Long-term:** Restructure for parallel execution

## Optimized Configuration

See [Appendix A](#appendix-a) for complete optimized configuration.
```

## Analysis Instructions

1. **Parse configuration:**
   - Validate YAML syntax
   - Identify platform (GitHub/GitLab)
   - Extract jobs, stages, triggers

2. **Check structure:**
   - Proper job ordering
   - Dependencies (needs/stages)
   - Concurrency settings
   - Timeouts

3. **Analyze caching:**
   - Cache keys use file hashes
   - Appropriate cache paths
   - Cache policy (pull/push)
   - Artifacts for job sharing

4. **Security review:**
   - Secret exposure
   - Permissions
   - Unsafe triggers
   - Action versions

5. **Performance audit:**
   - Parallel execution opportunities
   - Unnecessary sequential jobs
   - Matrix optimization
   - Fail-fast settings

## Usage

Provide:
- Path to CI configuration file(s)
- Specific areas to focus on (optional)

The analyzer will:
1. Parse and validate configuration
2. Check against best practices
3. Identify issues by severity
4. Provide specific fixes
5. Generate optimized configuration
