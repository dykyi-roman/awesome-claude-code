---
description: Performance audit. Detects N+1 queries, memory issues, caching gaps, inefficient loops, batch processing problems, algorithm complexity, connection pools, serialization overhead.
allowed-tools: Read, Grep, Glob, Task
model: opus
argument-hint: <path> [level] [-- meta-instructions]
---

# Performance Audit

Perform a comprehensive performance audit focusing on database queries, memory usage, caching, and algorithm efficiency.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: <path> [level] [-- <meta-instructions>]

Arguments:
- path: Target directory or file (required, default: current directory)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc:audit-performance ./src
- /acc:audit-performance ./src deep
- /acc:audit-performance ./src quick
- /acc:audit-performance ./src -- focus on memory and caching
- /acc:audit-performance ./src deep -- focus on N+1 queries
- /acc:audit-performance ./src -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if last word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)
7. Default path: current directory (if empty)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — customize audit focus

If meta-instructions provided, adjust audit to:
- Focus on specific performance categories
- Skip categories if requested
- Apply additional depth to specific areas
- Modify output verbosity

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Instructions

Use three specialized reviewers in parallel:

```
Task tool with subagent_type="acc:performance-reviewer"
prompt: "Perform performance audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Analyze for:
1. N+1 Query Problems — queries inside loops, missing eager loading
2. Query Efficiency — SELECT *, missing indexes, full table scans
3. Caching Strategy — missing cache opportunities, repeated expensive operations
4. Unnecessary Loops — nested loop inefficiency, redundant iterations
5. Lazy Loading Problems — premature loading, missing pagination
6. Batch Processing — single-item vs bulk operations, transaction overhead
7. Algorithm Complexity — O(n²) patterns, exponential growth
8. Database Index Usage — missing indexes, incorrect composite order

Provide severity classification, impact estimates, current vs optimal complexity, code examples."

Task tool with subagent_type="acc:resource-reviewer"
prompt: "Perform resource usage audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Analyze for:
1. Memory Issues — large arrays, missing generators, unbounded loading
2. Connection Pool Issues — leaks, connections in loops, missing cleanup
3. Serialization Overhead — large objects, N+1 during serialization
4. Async Patterns — blocking operations in request cycle
5. File I/O Patterns — full file reads, missing streaming

Provide severity classification, impact estimates, code examples."

Task tool with subagent_type="acc:scalability-reviewer"
prompt: "Perform scalability audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Analyze for:
1. Scalability Readiness — stateless design, session handling, hardcoded config
2. Database Scaling — read/write separation, connection pooling, replica usage

Provide severity classification, scaling impact, code examples."
```

## Analysis Scope

### Performance Categories

| Category | Impact | Common Issues |
|----------|--------|---------------|
| N+1 Queries | Database overload | Queries in foreach, lazy loading |
| Query Efficiency | Slow responses | SELECT *, missing indexes |
| Memory Issues | OOM errors | Large collections, no generators |
| Caching | Repeated work | No cache, cache stampede |
| Unnecessary Loops | CPU waste | O(n²), redundant iterations |
| Lazy Loading | Memory bloat | Load everything, no pagination |
| Batch Processing | I/O overhead | Single inserts in loops |
| Algorithm Complexity | Timeouts | Exponential algorithms |
| Connection Pool | Resource exhaustion | Leaks, no cleanup |
| Serialization | API latency | Large JSON, circular refs |

### Detection Patterns

```php
// N+1 Query (Critical)
foreach ($orders as $order) {
    $customer = $customerRepo->find($order->customerId); // Query per iteration
}

// Memory Issue (Major)
$allUsers = $userRepo->findAll(); // Loads millions into memory

// Algorithm Complexity (Major)
foreach ($items as $item) {
    if (in_array($item->id, $processedIds)) { ... } // O(n) inside O(n) = O(n²)
}

// Missing Batch (Major)
foreach ($entities as $entity) {
    $em->persist($entity);
    $em->flush(); // Should batch outside loop
}
```

## Expected Output

A structured markdown report containing:

### 1. Executive Summary
- Total issues found by severity
- Estimated performance impact
- Critical hot paths identified

### 2. Performance Dashboard

| Category | Issues | Impact | Priority |
|----------|--------|--------|----------|
| 🔴 N+1 Queries | 5 | High DB load | Critical |
| 🟠 Memory Issues | 3 | OOM risk | High |
| 🟡 Caching Gaps | 8 | Latency | Medium |

### 3. Critical Performance Issues

For each critical issue:

```markdown
### [Category]: [Brief Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**Impact:** [Estimated performance impact]

**Issue:**
[Detailed description]

**Current Complexity:** O(n²)
**Optimal Complexity:** O(n)

**Problematic Code:**
```php
// Slow code
```

**Optimized Solution:**
```php
// Fast code
```

**Expected Improvement:**
[Estimated improvement: queries, latency, memory]
```

### 4. Major Issues

[Same format as Critical]

### 5. Minor Issues / Suggestions

[Condensed list format]

### 6. Hot Path Analysis

```
Request Flow: Controller → Service → Repository → Database
                  │           │           │
                  │           │           └─ 5 queries (N+1)
                  │           └─ 200ms (caching opportunity)
                  └─ Total: 450ms (target: 100ms)
```

### 7. Optimization Roadmap

| Priority | Action | Location | Expected Gain |
|----------|--------|----------|---------------|
| 1 | Add eager loading | `OrderRepository.php:45` | -50 queries |
| 2 | Implement Redis cache | `ProductService.php:78` | -200ms |
| 3 | Use generator | `ReportGenerator.php:120` | -500MB RAM |

### 8. Performance Metrics Targets

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Queries per request | 50 | <10 | ❌ |
| Memory peak | 256MB | <64MB | ❌ |
| Response time | 450ms | <100ms | ❌ |
| Cache hit ratio | 20% | >80% | ❌ |

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Critical patterns | N+1 queries, memory issues (OOM risks) |
| `standard` | Full 10-category | All 10 performance categories with file:line references |
| `deep` | Standard + profiling | Standard + hot path analysis, profiling suggestions, optimization roadmap |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | System degradation, timeouts, OOM errors, N+1 with large datasets |
| High | 🟠 | Noticeable latency, scaling issues, missing batch processing |
| Medium | 🟡 | Suboptimal but functional, caching opportunities |
| Low | 🟢 | Minor optimizations, code style improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on N+1` | Deep N+1 query analysis |
| `focus on memory` | Memory usage and leak detection |
| `focus on caching` | Caching strategy analysis |
| `skip serialization` | Exclude serialization checks |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail with complexity analysis |
| `на русском` | Report in Russian |

## Usage Examples

```bash
/acc:audit-performance ./src
/acc:audit-performance ./src quick
/acc:audit-performance ./src deep
/acc:audit-performance ./src/Repository -- focus on N+1 and query efficiency
/acc:audit-performance ./src deep -- check memory and batch processing
/acc:audit-performance ./src -- level:deep
```
