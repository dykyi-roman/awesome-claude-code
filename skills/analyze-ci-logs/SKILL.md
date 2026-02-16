---
name: acc-analyze-ci-logs
description: Analyzes CI/CD pipeline logs to identify failure causes. Parses error messages, detects common failure patterns, and provides fix recommendations.
---

# CI Log Analyzer

Analyzes CI/CD pipeline logs to diagnose failures and suggest fixes.

## Failure Categories

### 1. Dependency Failures

```
┌─────────────────────────────────────────────────────────────────┐
│  DEPENDENCY FAILURE PATTERNS                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  composer install:                                              │
│  • "Your requirements could not be resolved"                   │
│  • "Package not found"                                          │
│  • "Allowed memory exhausted"                                   │
│                                                                 │
│  npm/yarn:                                                      │
│  • "ERESOLVE unable to resolve dependency tree"                │
│  • "npm ERR! 404 Not Found"                                    │
│  • "ENOMEM: not enough memory"                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2. Test Failures

```
PHPUnit Test Failures:
• "Failed asserting that..."
• "Error: Call to undefined method..."
• "Exception: ..."
• "PHPUnit\Framework\MockObject\RuntimeException"

Common Causes:
• Missing test fixtures
• Database connection issues
• Timing-dependent tests
• Mock configuration errors
```

### 3. Static Analysis Failures

```
PHPStan Errors:
• "Parameter $x has no type specified"
• "Method .+::.+ has no return type specified"
• "Call to an undefined method"
• "Access to an undefined property"

Psalm Errors:
• "MixedAssignment"
• "UndefinedClass"
• "InvalidReturnType"
```

### 4. Infrastructure Failures

```
Docker Errors:
• "Cannot connect to the Docker daemon"
• "pull access denied"
• "no space left on device"

Service Errors:
• "Connection refused" (database/redis)
• "ECONNRESET"
• "Timeout exceeded"
```

## Log Pattern Matching

### PHPUnit Failure Parser

```
Pattern: /FAILURES!\nTests: (\d+), Assertions: (\d+), Failures: (\d+)/
Pattern: /1\) (.+)::(.+)\n(.+)\nFailed asserting that (.+)/
Pattern: /Error: (.+)\n(.+):(\d+)/

Example:
FAILURES!
Tests: 45, Assertions: 120, Failures: 2, Errors: 1

1) App\Tests\Unit\OrderTest::test_calculate_total
Failed asserting that 100 matches expected 99.

/app/tests/Unit/OrderTest.php:45

Parsed:
{
  "type": "test_failure",
  "test_class": "App\\Tests\\Unit\\OrderTest",
  "test_method": "test_calculate_total",
  "assertion": "Failed asserting that 100 matches expected 99",
  "file": "/app/tests/Unit/OrderTest.php",
  "line": 45
}
```

### PHPStan Error Parser

```
Pattern: /------ (.+) ------\n\s*Line\s+(.+\.php)\n\s+(\d+)\s+(.+)/
Pattern: /\[ERROR\] Found (\d+) errors/

Example:
 ------ ----------------------------------------
  Line   src/Domain/Order/Order.php
 ------ ----------------------------------------
  45     Method Order::getTotal() has no return type specified.
  67     Parameter $discount has no type specified.
 ------ ----------------------------------------

 [ERROR] Found 2 errors

Parsed:
{
  "type": "phpstan_errors",
  "count": 2,
  "errors": [
    {"file": "src/Domain/Order/Order.php", "line": 45, "message": "Method Order::getTotal() has no return type specified."},
    {"file": "src/Domain/Order/Order.php", "line": 67, "message": "Parameter $discount has no type specified."}
  ]
}
```

### Composer Error Parser

```
Pattern: /Your requirements could not be resolved to an installable set of packages./
Pattern: /Problem (\d+)\n\s+- (.+)/
Pattern: /- (.+) requires (.+) -> (.+)/

Example:
Your requirements could not be resolved to an installable set of packages.

  Problem 1
    - symfony/framework-bundle v6.0.0 requires php >=8.0.2 -> your php version (7.4.33) does not satisfy that requirement.

Parsed:
{
  "type": "dependency_conflict",
  "problems": [
    {
      "package": "symfony/framework-bundle",
      "requires": "php >=8.0.2",
      "actual": "7.4.33",
      "message": "PHP version mismatch"
    }
  ]
}
```

## Analysis Output Format

```markdown
# CI Pipeline Failure Analysis

**Pipeline:** #12345
**Branch:** feature/new-checkout
**Commit:** abc1234
**Failed Job:** test-unit
**Duration:** 5m 32s

## Failure Summary

| Category | Count | Severity |
|----------|-------|----------|
| Test Failures | 3 | 🔴 Critical |
| PHPStan Errors | 0 | - |
| Infrastructure | 0 | - |

## Root Cause Analysis

### Primary Failure: Test Assertion Error

**Test:** `OrderTest::test_calculate_total_with_discount`
**File:** `tests/Unit/Domain/OrderTest.php:45`

**Error:**
```
Failed asserting that 90.0 matches expected 90.
```

**Analysis:**
The test expects an integer `90` but receives a float `90.0`. This is likely due to:
1. Changed calculation in `Order::calculateTotal()` now returns float
2. Test assertion uses strict comparison

**Suggested Fix:**
```php
// Option 1: Update test to expect float
self::assertSame(90.0, $order->calculateTotal());

// Option 2: Use assertEquals for loose comparison
self::assertEquals(90, $order->calculateTotal());

// Option 3: Use Money value object (recommended)
self::assertTrue($order->calculateTotal()->equals(Money::EUR(90)));
```

### Secondary Failure: Mock Configuration

**Test:** `PaymentServiceTest::test_process_payment`
**File:** `tests/Unit/Application/PaymentServiceTest.php:78`

**Error:**
```
Expectation failed for method name is "charge" when invoked 1 time(s).
Method was expected to be called 1 times, actually called 0 times.
```

**Analysis:**
Mock expectation not met. The `charge` method was never called, indicating:
1. Conditional logic preventing the call
2. Early return before reaching the charge
3. Exception thrown before charge

**Suggested Fix:**
Review the test setup and ensure conditions are met for `charge` to be called.

## Timeline

```
00:00 - Job started
00:15 - Composer install (cached)
00:45 - PHPStan passed
01:30 - PHPUnit started
04:45 - Test failure: OrderTest::test_calculate_total_with_discount
05:00 - Test failure: PaymentServiceTest::test_process_payment
05:32 - Job failed
```

## Recommendations

1. **Immediate:** Fix type mismatch in OrderTest
2. **Short-term:** Add type declarations to prevent float/int confusion
3. **Long-term:** Use Money value object for financial calculations

## Related Changes

Recent commits that may have caused this failure:
- `abc1234` - Refactor calculateTotal to return float
- `def5678` - Update discount calculation logic
```

## Common Fixes Database

### Dependency Issues

| Error Pattern | Cause | Fix |
|---------------|-------|-----|
| `memory exhausted during composer` | Low memory limit | Add `COMPOSER_MEMORY_LIMIT=-1` |
| `package not found` | Private repo or typo | Check package name and auth |
| `requirements not resolved` | Version conflict | Run `composer why-not package` |

### Test Issues

| Error Pattern | Cause | Fix |
|---------------|-------|-----|
| `Connection refused 127.0.0.1:3306` | MySQL not ready | Add service health check |
| `Mock expectation failed` | Mock not configured | Review mock setup |
| `Class not found` | Autoloader issue | Run `composer dump-autoload` |

### Infrastructure Issues

| Error Pattern | Cause | Fix |
|---------------|-------|-----|
| `no space left on device` | Disk full | Clear Docker cache |
| `Cannot connect to Docker daemon` | DinD not running | Check Docker service |
| `pull access denied` | Auth issue | Add registry credentials |

## Analysis Instructions

1. **Extract log content:**
   - Identify job that failed
   - Get full log output
   - Note timestamps

2. **Identify failure type:**
   - Parse error messages
   - Categorize (test/lint/infra)
   - Determine severity

3. **Root cause analysis:**
   - Trace error to source
   - Check recent changes
   - Identify patterns

4. **Generate recommendations:**
   - Specific fixes
   - Prevention strategies
   - Related improvements

## Usage

Provide:
- CI log output (full or relevant section)
- Pipeline context (branch, commit)
- Recent changes (optional)

The analyzer will:
1. Parse log for errors
2. Categorize failures
3. Identify root cause
4. Suggest specific fixes
5. Provide prevention tips
