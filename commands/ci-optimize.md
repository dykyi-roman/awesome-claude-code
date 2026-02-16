---
description: Optimize CI pipeline performance. Analyzes execution time, improves caching, parallelization, and identifies bottlenecks.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task
model: opus
argument-hint: [path] [-- focus areas]
---

# Optimize CI Pipeline

Improve CI/CD pipeline performance by analyzing and optimizing caching, parallelization, and job structure.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional focus areas:

```
Format: [path] [-- <focus-areas>]

Examples:
- /acc-ci-optimize
- /acc-ci-optimize ./
- /acc-ci-optimize -- focus on caching
- /acc-ci-optimize ./ -- reduce Docker build time
- /acc-ci-optimize -- parallelize tests, optimize lint
```

**Parsing rules:**
1. First argument = **path** (optional, defaults to `./`)
2. After `--` = **focus areas** (optional optimization targets)

## Pre-flight Check

1. **Find CI configuration:**
   ```bash
   ls .github/workflows/*.yml 2>/dev/null
   ls .gitlab-ci.yml 2>/dev/null
   ```

2. **If no CI found:**
   - Suggest running `/acc-ci-setup` first

3. **Check for optimization targets:**
   ```bash
   # Check for caching
   grep -r "cache" .github/workflows/ .gitlab-ci.yml 2>/dev/null

   # Check job dependencies
   grep -rE "(needs:|depends_on:)" .github/workflows/ .gitlab-ci.yml 2>/dev/null

   # Check for Docker
   ls Dockerfile* 2>/dev/null
   ```

## Instructions

Use the `acc-ci-coordinator` agent to optimize:

```
Task tool with subagent_type="acc-ci-coordinator"
prompt: "Optimize CI pipeline at [PATH].

Operation: OPTIMIZE

[FOCUS_AREAS if provided]

Analysis targets:
1. Caching efficiency
2. Job parallelization
3. Dependency structure
4. Docker build optimization
5. Resource usage

Provide:
- Current vs optimized comparison
- Specific changes to make
- Estimated time savings"
```

## Expected Output

The coordinator will:

1. **Analyze current pipeline:**
   - Total execution time
   - Critical path
   - Parallelism percentage
   - Cache hit rates

2. **Identify bottlenecks:**
   - Slowest jobs
   - Sequential when parallel possible
   - Cache misses
   - Unnecessary waits

3. **Generate optimizations:**
   - Updated CI configuration
   - Before/after comparison
   - Estimated improvements

4. **Provide metrics:**
   ```
   | Metric | Before | After | Improvement |
   |--------|--------|-------|-------------|
   | Total time | 25 min | 10 min | -60% |
   | Parallelism | 12% | 68% | +56% |
   | Cache hit | 20% | 85% | +65% |
   ```

## Optimization Categories

### Caching
- Composer dependencies
- Docker layers
- Build artifacts
- Test fixtures

### Parallelization
- Independent lint jobs
- Test suite splitting
- Matrix builds
- Conditional execution

### Docker
- Multi-stage builds
- Layer ordering
- BuildKit cache
- Smaller base images

### Structure
- Job dependencies
- Fail fast
- Timeouts
- Resource allocation

## Usage Examples

```bash
# General optimization
/acc-ci-optimize

# Focus on caching
/acc-ci-optimize -- focus on caching, reduce cache misses

# Docker optimization
/acc-ci-optimize -- optimize Docker build time

# Test parallelization
/acc-ci-optimize -- split tests into parallel jobs

# Full optimization with path
/acc-ci-optimize ./my-project -- optimize everything, target 10 min total
```

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on caching` | Prioritize cache optimization |
| `parallelize tests` | Split test suites for parallel execution |
| `optimize Docker` | Focus on Docker build optimization |
| `reduce time by X%` | Set specific improvement target |
| `target X min total` | Set absolute time target |
| `minimize resources` | Optimize for cost, not just speed |
