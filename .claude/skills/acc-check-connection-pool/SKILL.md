---
name: acc-check-connection-pool
description: Analyzes PHP code for connection pool issues. Detects connection leaks, improper pool sizing, missing connection release, timeout issues.
---

# Connection Pool Performance Analysis

Analyze PHP code for connection pool issues and database connection management problems.

## When to Use

- Reviewing database-heavy PHP applications
- Investigating connection exhaustion or memory leaks
- Auditing long-running workers (queue consumers, daemons)
- Checking Doctrine EntityManager lifecycle issues
- Reviewing HTTP client usage patterns

## Analysis Approach

1. Scan for connection creation patterns (PDO, Redis, Guzzle)
2. Check loop bodies for repeated connection instantiation
3. Verify try/finally cleanup on pool acquire/release
4. Check timeout configuration on all connection types
5. Review persistent connection usage and state reset
6. Audit worker processes for connection refresh logic

## Detection Rules

| ID | Pattern | What to Look For |
|----|---------|------------------|
| CP-01 | Connection leak | `new PDO` without cleanup in exception/early-return paths |
| CP-02 | Connection in loop | `new PDO`/`new Redis`/`new Client` inside foreach/while |
| CP-03 | Missing timeout | PDO without `ATTR_TIMEOUT`, Redis without connect timeout |
| CP-04 | Persistent misuse | `ATTR_PERSISTENT => true` without shutdown cleanup |
| CP-05 | Pool exhaustion | Multiple connections opened without reuse |
| CP-06 | Missing finally | `$pool->release()` not in finally block |
| CP-07 | State not reset | Connection returned to pool with modified session state |
| CP-08 | Doctrine issues | EntityManager not cleared, long-held transactions |
| CP-09 | Worker stale conn | Long-running worker without connection refresh |
| CP-10 | HTTP no pooling | `file_get_contents` in loop, no keep-alive headers |

## Grep Patterns

```bash
# New connection in loops
Grep: "foreach.*\{[^}]*new PDO|while.*\{[^}]*new PDO" --glob "**/*.php" --multiline

# Missing connection close
Grep: "new Redis\(\)" --glob "**/*.php"

# Persistent connections
Grep: "ATTR_PERSISTENT" --glob "**/*.php"

# Connection without timeout
Grep: "new PDO\s*\([^)]+\)\s*;" --glob "**/*.php"

# Static connection storage
Grep: "static.*PDO|static.*connection" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Connection in loop | Critical |
| Connection leak (no finally) | Critical |
| No connection timeout | Major |
| Pool exhaustion risk | Major |
| Missing connection health check | Major |
| Persistent connection misuse | Minor |
| Static connection storage | Minor |

## Output Format

```markdown
### Connection Pool: [Description]

**Severity:** Critical/Major/Minor
**Location:** `file.php:line`
**Impact:** [Database overload, connection exhaustion, memory leak]

**Issue:**
[Description of the connection management problem]

**Code:**
[Problematic code snippet]

**Fix:**
[Proper connection management code]

**Expected Improvement:**
- Connection count: 100 -> 10 (pooled)
- Memory usage: -50% (connections reused)
- DB load: -80% (connection overhead eliminated)
```

## References

- `references/patterns.md` — detailed detection patterns with code examples, secure pool implementations, health check and worker refresh patterns
