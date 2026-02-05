---
description: Fix bug based on description, stack trace, or file reference
allowed-tools: Task, Read, Grep, Glob, Edit, Write, Bash
model: opus
argument-hint: <bug-description|file:line|stack-trace>
---

# Bug Fix Command

You are executing the `/acc-fix-bug` command. Your task is to diagnose and fix a bug using the bug fix system.

## Input Received

**User Input:** $ARGUMENTS

**Meta-Instructions:** Parse any text after `--` as meta-instructions (e.g., `-- focus on validation`, `-- skip tests`, `-- dry-run`).

## Execution Flow

### Step 1: Parse Input

Determine the input type:

1. **File:Line Reference** (e.g., `src/Domain/Order.php:45`)
   - Read the file with context (±30 lines around the line)
   - Extract any description after the reference

2. **Stack Trace** (contains `Stack trace:` or `#0`, `#1`, etc.)
   - Parse the trace to find origin file and line
   - Read the relevant files

3. **Log File Reference** (starts with `@`)
   - Read the log file
   - Extract error messages and stack traces

4. **Text Description**
   - Search codebase for relevant code
   - Use Grep to find mentioned classes/methods

### Step 2: Diagnose Bug

Invoke `acc-bug-hunter` agent to diagnose:

```
Task → acc-bug-hunter

Analyze this code for bugs:
[code context]

User description: [bug description]

Provide:
1. Bug category (logic/null/boundary/race/resource/exception/type/sql/infinite)
2. Severity (Critical/Major/Minor)
3. Exact location (file:line)
4. Root cause hypothesis
5. Fix recommendations
```

### Step 3: Generate Fix

Invoke `acc-bug-fixer` agent:

```
Task → acc-bug-fixer

Diagnosis from acc-bug-hunter:
[diagnosis]

Code context:
[relevant code]

Generate:
1. Root cause analysis (5 Whys)
2. Impact analysis (blast radius)
3. Minimal fix code
4. Quality verification
5. Regression prevention checklist
```

### Step 4: Generate Regression Test

Unless `-- skip tests` specified, invoke `acc-test-generator`:

```
Task → acc-test-generator

Bug: [description]
Fix: [the fix code]
Location: [file:line]

Create a regression test that:
1. Fails before the fix
2. Passes after the fix
3. Covers edge cases
```

### Step 5: Apply Changes

Unless `-- dry-run` specified:

1. **Apply fix** using Edit tool
2. **Create test file** using Write tool
3. **Run tests** using Bash:
   ```bash
   # Try common test commands
   make test
   # or
   ./vendor/bin/phpunit
   # or
   docker exec app php vendor/bin/phpunit
   ```

### Step 6: Report Results

Output a comprehensive report:

```markdown
# Bug Fix Report

## Summary
| Field | Value |
|-------|-------|
| Bug | [short description] |
| Category | [category from diagnosis] |
| Severity | [severity] |
| Location | [file:line] |
| Status | ✅ Fixed / ❌ Failed |

## Diagnosis
[Summary from acc-bug-hunter]

## Root Cause
[5 Whys analysis from acc-bug-fixer]

## Fix Applied

**File:** `path/to/file.php`

```diff
- [old code]
+ [new code]
```

## Regression Test

**File:** `tests/path/to/Test.php`
[Test summary or "Skipped per user request"]

## Verification
- [x] Fix applied
- [x] Test created
- [x] Tests passing
- [ ] Manual verification recommended for: [areas]

## Next Steps
[Any recommended follow-up actions]
```

## Meta-Instructions Handling

| Instruction | Effect |
|-------------|--------|
| `-- focus on <area>` | Prioritize searching/analyzing specific area |
| `-- skip tests` | Don't generate regression test |
| `-- dry-run` | Show proposed fix without applying |
| `-- verbose` | Include detailed diagnosis and analysis |

## Examples

### Example 1: Text Description
```
/acc-fix-bug "NullPointerException in OrderService::process()"
```

### Example 2: File Reference
```
/acc-fix-bug src/Domain/Order/OrderService.php:45 "off-by-one error in loop"
```

### Example 3: With Meta-Instructions
```
/acc-fix-bug "Payment validation fails for amounts > 1000" -- focus on validation
```

### Example 4: From Log File
```
/acc-fix-bug @storage/logs/laravel.log -- skip tests
```

### Example 5: Dry Run
```
/acc-fix-bug src/Application/UseCase/CreateOrder.php:78 -- dry-run
```

## Error Handling

### If diagnosis fails:
- Report what was found
- Suggest manual investigation points
- Ask for more context if needed

### If fix generation fails:
- Report the diagnosis
- Explain why automatic fix isn't possible
- Provide manual fix guidance

### If tests fail after fix:
- Report the failure
- Show test output
- Suggest refinements

## DDD Awareness

When working with DDD codebases, respect layer boundaries:

- **Domain Layer:** Preserve invariants, maintain immutability
- **Application Layer:** Keep transactions, maintain CQRS separation
- **Infrastructure Layer:** Preserve contracts, maintain idempotency
- **Presentation Layer:** Validate input, format output correctly
