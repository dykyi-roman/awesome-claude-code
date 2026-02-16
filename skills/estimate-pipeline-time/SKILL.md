---
name: acc-estimate-pipeline-time
description: Estimates and optimizes CI/CD pipeline execution time. Analyzes job dependencies, identifies bottlenecks, and suggests parallelization strategies.
---

# Pipeline Time Estimator

Estimates pipeline execution time and identifies optimization opportunities.

## Pipeline Analysis

### Execution Flow Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    PIPELINE EXECUTION FLOW                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Time  0    2    4    6    8    10   12   14   16   18   20    │
│        │    │    │    │    │    │    │    │    │    │    │     │
│        ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼    ▼     │
│                                                                 │
│  install ████████                                               │
│              │                                                  │
│              ├──▶ phpstan ████████                              │
│              │                                                  │
│              ├──▶ psalm ██████████                              │
│              │                                                  │
│              ├──▶ cs-fixer ██████                               │
│              │                                                  │
│              └──▶ deptrac ████                                  │
│                            │                                    │
│                            └──▶ test-unit ████████████████      │
│                                                         │       │
│                                                         └──▶ build ████│
│                                                                 │
│  Critical Path: install → psalm → test-unit → build = 20 min   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Time Estimation Model

### Job Time Components

```
Job Time = Setup Time + Execution Time + Teardown Time

Where:
- Setup Time = Runner startup + Checkout + Cache restore
- Execution Time = Actual command execution
- Teardown Time = Artifact upload + Cache save + Cleanup
```

### Typical Job Times (PHP Project)

| Job | Cold (no cache) | Warm (cached) | Components |
|-----|-----------------|---------------|------------|
| **checkout** | 10s | 10s | git clone |
| **composer install** | 180s | 30s | Download + autoload |
| **phpstan** | 120s | 120s | Analysis |
| **psalm** | 180s | 180s | Analysis + taint |
| **cs-fixer** | 60s | 60s | Style check |
| **deptrac** | 30s | 30s | Architecture |
| **phpunit (unit)** | 120s | 120s | Tests |
| **phpunit (integration)** | 300s | 300s | Tests + DB |
| **docker build** | 600s | 120s | Build + push |

### Critical Path Analysis

```python
# Pseudo-algorithm for critical path
def find_critical_path(jobs):
    # Build dependency graph
    graph = build_dependency_graph(jobs)

    # Calculate earliest start time for each job
    for job in topological_sort(graph):
        job.earliest_start = max(
            dep.earliest_finish for dep in job.dependencies
        ) if job.dependencies else 0
        job.earliest_finish = job.earliest_start + job.duration

    # Total pipeline time = max(earliest_finish)
    total_time = max(job.earliest_finish for job in jobs)

    # Critical path = jobs where slack = 0
    critical_path = [job for job in jobs if job.slack == 0]

    return critical_path, total_time
```

## Optimization Strategies

### 1. Parallelize Independent Jobs

```yaml
# BEFORE: Sequential (20 min)
#   install → phpstan → psalm → cs-fixer → deptrac → test → build

# AFTER: Parallel lint (12 min)
#   install ─┬─► phpstan ─────┐
#            ├─► psalm ───────┼─► test → build
#            ├─► cs-fixer ────┤
#            └─► deptrac ─────┘

# Savings: 8 minutes (40%)
```

### 2. Split Long Jobs

```yaml
# BEFORE: Single test job (10 min)
test:
  script: vendor/bin/phpunit

# AFTER: Parallel test suites (4 min)
test-unit:
  script: vendor/bin/phpunit --testsuite=unit
test-integration:
  script: vendor/bin/phpunit --testsuite=integration
test-e2e:
  script: vendor/bin/phpunit --testsuite=e2e

# Savings: 6 minutes (60%)
```

### 3. Optimize Cache Usage

```yaml
# BEFORE: No caching (composer install: 3 min)
- run: composer install

# AFTER: With caching (composer install: 30 sec)
- uses: actions/cache@v4
  with:
    path: |
      ~/.composer/cache
      vendor
    key: composer-${{ hashFiles('composer.lock') }}
- run: composer install

# Savings: 2.5 minutes per job
```

### 4. Use Smaller Images

```yaml
# BEFORE: Full PHP image (pull: 45 sec)
image: php:8.4-cli

# AFTER: Alpine image (pull: 15 sec)
image: php:8.4-cli-alpine

# Savings: 30 seconds per job
```

### 5. Matrix Optimization

```yaml
# BEFORE: Matrix of 9 combinations, all run
strategy:
  matrix:
    php: ['8.2', '8.3', '8.4']
    deps: ['lowest', 'locked', 'highest']

# AFTER: Strategic subset (3 combinations)
strategy:
  matrix:
    include:
      - php: '8.2'
        deps: 'lowest'   # Min requirements
      - php: '8.4'
        deps: 'locked'   # Primary target
      - php: '8.4'
        deps: 'highest'  # Future compat

# Savings: 66% reduction in matrix jobs
```

## Analysis Output Format

```markdown
# Pipeline Time Analysis

**Pipeline:** CI
**Current Duration:** 25 min 30 sec
**Optimized Estimate:** 10 min 15 sec
**Potential Savings:** 15 min 15 sec (60%)

## Current Execution Timeline

```
Job                  Start    Duration    End      Status
──────────────────────────────────────────────────────────
install              0:00     3:00        3:00     ✓
phpstan              3:00     2:00        5:00     ✓ (waits 3:00)
psalm                5:00     3:00        8:00     ✓ (waits 5:00)
cs-fixer             8:00     1:00        9:00     ✓ (waits 8:00)
deptrac              9:00     0:30        9:30     ✓ (waits 9:00)
test-unit            9:30     6:00        15:30    ✓ (waits 9:30)
test-integration     15:30    8:00        23:30    ✓ (waits 15:30)
build                23:30    2:00        25:30    ✓ (waits 23:30)
```

## Critical Path

```
install (3:00) → psalm (3:00) → test-unit (6:00) → test-integration (8:00) → build (2:00)
Total: 22:00 (critical path determines minimum possible time)
```

## Bottleneck Analysis

| Job | Duration | Wait Time | Utilization | Bottleneck? |
|-----|----------|-----------|-------------|-------------|
| install | 3:00 | 0:00 | 100% | No |
| phpstan | 2:00 | 3:00 | 40% | **Wait** |
| psalm | 3:00 | 5:00 | 37% | **Wait** |
| cs-fixer | 1:00 | 8:00 | 11% | **Wait** |
| test-integration | 8:00 | 15:30 | 34% | **Duration** |

## Optimization Recommendations

### 1. Parallelize Lint Jobs
**Impact:** -6:30 (25%)
```yaml
# Current: Sequential
# Proposed: All lint jobs run in parallel after install
```

### 2. Split Integration Tests
**Impact:** -4:00 (16%)
```yaml
# Current: Single 8-minute job
# Proposed: Split into 3 parallel jobs of ~3 min each
```

### 3. Add Caching
**Impact:** -2:30 (10%)
```yaml
# Current: Cold composer install (3:00)
# Proposed: Cached install (0:30)
```

### 4. Move Build Earlier
**Impact:** -0:30 (2%)
```yaml
# Build can start after unit tests, doesn't need integration
```

## Optimized Pipeline

```
Time  0    2    4    6    8    10
      │    │    │    │    │    │
      ▼    ▼    ▼    ▼    ▼    ▼

install (0:30) ─┬─► phpstan (2:00) ──────────┐
                ├─► psalm (3:00) ────────────┼─► test-unit (4:00) ─┬─► build (2:00)
                ├─► cs-fixer (1:00) ─────────┤                     │
                └─► deptrac (0:30) ──────────┘                     │
                                                                   │
                              test-int-1 (3:00) ───────────────────┤
                              test-int-2 (3:00) ───────────────────┤
                              test-int-3 (3:00) ───────────────────┘

Total: 10:15 (was 25:30)
```

## Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Total Duration | 25:30 | 10:15 | -60% |
| Critical Path | 22:00 | 10:15 | -53% |
| Parallelism | 12% | 68% | +56% |
| Wait Time | 41:30 | 8:00 | -81% |
```

## Estimation Formulas

### Total Pipeline Time

```
T_total = max(T_critical_path, T_resource_constrained)

Where:
T_critical_path = sum of job times on longest dependency chain
T_resource_constrained = total_job_time / max_parallel_runners
```

### Cache Benefit

```
T_cached = T_uncached * cache_hit_rate * cache_speedup + T_uncached * (1 - cache_hit_rate)

Example:
- Uncached composer: 180s
- Cache hit rate: 90%
- Cache speedup: 85%
T_cached = 180 * 0.90 * 0.15 + 180 * 0.10 = 24.3 + 18 = 42s
```

## Usage

Provide:
- CI configuration file
- Historical run data (optional)
- Runner constraints (optional)

The estimator will:
1. Parse job dependencies
2. Estimate job durations
3. Calculate critical path
4. Identify bottlenecks
5. Suggest optimizations
6. Estimate savings
