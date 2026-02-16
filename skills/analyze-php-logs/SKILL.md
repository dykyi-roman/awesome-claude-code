---
name: acc-analyze-php-logs
description: Parses and analyzes PHP application logs in PSR-3/Monolog, Laravel, Symfony, and plain error_log formats. Extracts exceptions, stack traces, request context, error frequency, and correlates related errors.
---

# PHP Log Analyzer

Parses PHP application logs across multiple formats, extracts structured data, identifies error patterns, and correlates related issues.

## Supported Log Formats

### 1. PSR-3 / Monolog (JSON)

```json
{"message":"Connection refused","context":{"exception":"PDOException","file":"/app/src/Infrastructure/Repository/OrderRepository.php","line":45,"trace":"..."},"level":500,"level_name":"CRITICAL","channel":"app","datetime":"2025-01-15T14:30:00+00:00","extra":{"url":"/api/orders","method":"POST","ip":"10.0.0.1"}}
```

**Detection:** Line starts with `{` and contains `"level_name"` or `"channel"`

**Extraction pattern:**
```
JSON decode each line
Fields: message, context.exception, context.file, context.line, level_name, datetime, extra.*
Stack trace: context.trace (string or array)
```

### 2. PSR-3 / Monolog (Line Format)

```
[2025-01-15T14:30:00+00:00] app.CRITICAL: Connection refused {"exception":"PDOException","file":"/app/src/Infrastructure/Repository/OrderRepository.php","line":45} {"url":"/api/orders"}
```

**Detection:** Line matches `\[\d{4}-\d{2}-\d{2}T.+\] \w+\.\w+:`

**Extraction pattern:**
```
Regex: /^\[(.+?)\] (\w+)\.(\w+): (.+?)(\s+\{.+\})?\s*(\{.+\})?$/
Groups: datetime, channel, level, message, context_json, extra_json
```

### 3. Laravel Log Format

```
[2025-01-15 14:30:00] production.ERROR: SQLSTATE[HY000] [2002] Connection refused {"exception":"[object] (PDOException(code: 2002): SQLSTATE[HY000] [2002] Connection refused at /app/vendor/laravel/framework/src/Illuminate/Database/Connectors/Connector.php:70)
[stacktrace]
#0 /app/vendor/laravel/framework/src/Illuminate/Database/Connectors/Connector.php(70): PDO->__construct()
#1 /app/src/Infrastructure/Repository/OrderRepository.php(45): Illuminate\\Database\\Connectors\\Connector->createPdoConnection()
"}
```

**Detection:** Line matches `\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\] \w+\.(ERROR|CRITICAL|WARNING|INFO|DEBUG):`

**Extraction pattern:**
```
Regex: /^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] (\w+)\.(\w+): (.+)/
Groups: datetime, environment, level, message+context
Stack trace: Lines starting with #N after [stacktrace]
Exception: object class and message from context JSON
```

### 4. Symfony Log Format

```
[2025-01-15T14:30:00+00:00] request.CRITICAL: Uncaught PHP Exception PDOException: "Connection refused" at /app/src/Infrastructure/Repository/OrderRepository.php line 45 {"exception":"[object] (PDOException(code: 2002): Connection refused at /app/src/Infrastructure/Repository/OrderRepository.php:45)"}
```

**Detection:** Same as Monolog line format, channel often `request`, `doctrine`, `security`

**Extraction pattern:** Same as Monolog line format.

### 5. Plain PHP error_log

```
[15-Jan-2025 14:30:00 UTC] PHP Fatal error:  Uncaught PDOException: Connection refused in /app/src/Infrastructure/Repository/OrderRepository.php:45
Stack trace:
#0 /app/src/Infrastructure/Repository/OrderRepository.php(45): PDO->__construct()
#1 /app/src/Application/UseCase/CreateOrder.php(32): App\Infrastructure\Repository\OrderRepository->save()
#2 {main}
  thrown in /app/src/Infrastructure/Repository/OrderRepository.php on line 45
```

**Detection:** Line matches `\[\d{2}-\w{3}-\d{4}.*\] PHP (Fatal error|Warning|Notice|Deprecated):`

**Extraction pattern:**
```
Regex: /^\[(.+?)\] PHP (\w[\w ]+):\s+(.+) in (.+):(\d+)$/
Groups: datetime, severity, message, file, line
Stack trace: Lines starting with #N until blank line
```

### 6. PHP-FPM Slow Log

```
[15-Jan-2025 14:30:00]  [pool www] pid 1234
script_filename = /app/public/index.php
[0x00007f...] sleep() /app/src/Infrastructure/ExternalApi/PaymentGateway.php:89
[0x00007f...] App\Infrastructure\ExternalApi\PaymentGateway->charge() /app/src/Application/UseCase/ProcessPayment.php:34
[0x00007f...] App\Application\UseCase\ProcessPayment->execute() /app/src/Presentation/Api/Action/PaymentAction.php:28
```

**Detection:** Contains `[pool ` and `script_filename`

**Extraction pattern:**
```
Entry starts with: /^\[\d{2}-\w{3}-\d{4}.*\]\s+\[pool/
Script: line after "script_filename = "
Stack frames: [address] function_call file:line
Top of stack = slowest function (bottleneck)
```

## Analysis Capabilities

### Exception Extraction

For each exception found:

```markdown
| Field | Value |
|-------|-------|
| Exception | PDOException |
| Message | Connection refused |
| File | src/Infrastructure/Repository/OrderRepository.php |
| Line | 45 |
| Level | CRITICAL |
| Time | 2025-01-15 14:30:00 |
```

### Stack Trace Analysis

**Separate application frames from vendor frames:**

```markdown
### Application Frames (actionable)
#1 src/Infrastructure/Repository/OrderRepository.php:45 → PDO->__construct()
#2 src/Application/UseCase/CreateOrder.php:32 → OrderRepository->save()
#3 src/Presentation/Api/Action/CreateOrderAction.php:28 → CreateOrder->execute()

### Vendor Frames (context only)
#0 vendor/laravel/framework/src/Illuminate/Database/Connectors/Connector.php:70
```

**Heuristic:** Frame is "application" if path does NOT contain `vendor/`, `var/cache/`, or framework internals.

### Request Context Extraction

Look for these fields in log context/extra:

```
URL: extra.url, context.request_uri, context.path
Method: extra.method, context.request_method
User: extra.user_id, context.user, extra.username
Correlation ID: extra.correlation_id, extra.request_id, extra.trace_id, context.X-Request-Id
IP: extra.ip, extra.client_ip, context.ip
Session: extra.session_id
```

### Error Frequency Analysis

Group errors by exception class + message pattern:

```markdown
## Error Frequency (last 24h)

| Exception | Message Pattern | Count | First | Last | Trend |
|-----------|----------------|-------|-------|------|-------|
| PDOException | Connection refused | 47 | 14:00 | 14:30 | ↑ spike |
| InvalidArgumentException | Invalid order status * | 12 | 08:15 | 14:28 | → steady |
| TimeoutException | Gateway timeout * | 3 | 14:25 | 14:30 | ↑ new |
```

**Spike detection:** If error count in last hour > 3x average hourly rate → flag as spike.

### Error Correlation

Group related errors by:

1. **Time proximity** — errors within 1-second window likely from same request
2. **Correlation ID** — same request_id/trace_id across log entries
3. **Causal chain** — Exception A causes Exception B (e.g., PDOException → QueryException → HttpException)
4. **File proximity** — errors in same class/namespace within short timeframe

```markdown
## Correlated Error Group

**Trigger:** PDOException: Connection refused (14:30:00)
**Cascade:**
  → QueryException: Could not execute query (14:30:00)
  → HttpException: 500 Internal Server Error (14:30:01)

**Root Cause:** Database connection failure
**Affected Endpoint:** POST /api/orders
**Impact:** 47 failed requests in 30 minutes
```

## Reading Strategy

### For Large Log Files

```
File size < 10KB   → Read entire file
File size 10KB-1MB → Read last 500 lines (most recent errors)
File size > 1MB    → Read last 1000 lines
                     + Grep for specific exception class or timestamp range
```

### Targeted Extraction

When looking for specific errors:

```
# By exception class
Grep: /PDOException|QueryException/ in log file

# By severity
Grep: /\.(CRITICAL|ERROR|EMERGENCY):/ in log file

# By time range (last hour)
Grep: /\[2025-01-15 14:/ in log file

# By file reference
Grep: /OrderRepository\.php/ in log file
```

### Multi-File Analysis

When multiple log files exist (e.g., daily rotation):

```
1. Start with most recent file (highest score from discovery)
2. If error pattern needs historical context → check previous day's file
3. Cross-reference application log with PHP-FPM slow log for performance
4. Cross-reference application log with web server error log for HTTP errors
```

## Output Format

```markdown
# Log Analysis Report

**Log File:** storage/logs/laravel.log
**Period:** 2025-01-15 14:00 — 14:30
**Lines Analyzed:** 1,247

## Summary

| Metric | Value |
|--------|-------|
| Total Errors | 62 |
| Unique Exceptions | 3 |
| Critical | 47 |
| Error | 12 |
| Warning | 3 |

## Top Exceptions

### 1. PDOException: Connection refused (47 occurrences)

**Severity:** 🔴 Critical
**First:** 14:00:12 | **Last:** 14:30:01 | **Trend:** ↑ Spike
**File:** `src/Infrastructure/Repository/OrderRepository.php:45`

**Application Stack:**
```
#1 OrderRepository.php:45 → PDO->__construct()
#2 CreateOrder.php:32 → OrderRepository->save()
#3 CreateOrderAction.php:28 → CreateOrder->execute()
```

**Request Context:**
- URL: POST /api/orders
- Correlation IDs: [req-abc123, req-def456, ...]

**Likely Cause:** Database server unreachable or connection pool exhausted

### 2. [Next exception...]

## Correlated Groups

[Correlation analysis...]

## Recommendations

1. **Immediate:** Check database connectivity and connection pool settings
2. **Investigation:** Review `OrderRepository` database configuration
3. **Prevention:** Add circuit breaker pattern for database connections
```

## Integration Notes

- This skill is **read-only** — it analyzes and reports, never modifies files
- Works with `Read`, `Grep` tools available to all agents
- Use `acc-discover-project-logs` first to find log file locations
- For bug diagnosis: focus on exception extraction and stack trace analysis
- For performance review: focus on PHP-FPM slow log and error frequency
- For Docker debugging: focus on PHP-FPM logs and error correlation
