---
description: Fix bug based on description, stack trace, or file reference
allowed-tools: Task, Read, Grep, Glob, Edit, Write, Bash
model: opus
argument-hint: <bug-description|file:line|stack-trace>
---

# Bug Fix Command

You are executing the `/acc-bug-fix` command. Your task is to diagnose and fix a bug using the bug fix system.

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

4. **Auto-discover Logs** (when `-- scan-logs` is specified or no `@logfile` provided with `-- scan-logs`)
   - Use `acc-discover-project-logs` skill via bug-hunter to find log files automatically
   - Prioritize by recency and severity
   - If no logs found, use AskUserQuestion:
     ```
     Question: "Log files not found automatically. Where are your project logs?"
     Options:
       - "storage/logs/" (Laravel)
       - "var/log/" (Symfony)
       - "writable/logs/" (CodeIgniter 4)
       - "runtime/logs/" (Yii2/Yii3)
     ```

5. **Text Description**
   - Search codebase for relevant code
   - Use Grep to find mentioned classes/methods

### Step 2: Invoke Bug Fix Coordinator

Use the `acc-bug-fix-coordinator` agent to orchestrate the full bug fix workflow:

```
Task tool with subagent_type="acc-bug-fix-coordinator"

prompt: |
  Fix the following bug:

  Input: [parsed input from Step 1]
  Code context: [relevant code]
  Meta-instructions: [any -- options]

  Execute full workflow:
  1. Diagnose with acc-bug-hunter
  2. Generate fix with acc-bug-fixer
  3. Create regression test with acc-test-generator (unless skip-tests)
  4. Apply changes (unless dry-run)
  5. Run tests and verify
```

The coordinator orchestrates:
- `acc-bug-hunter` → Diagnose bug (category, severity, location, root cause)
- `acc-bug-fixer` → Generate minimal fix (5 Whys, impact analysis, fix code)
- `acc-test-generator` → Create regression test (unless `-- skip tests`)

### Step 3: Report Results

Output the comprehensive report from coordinator:

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
| `-- scan-logs` | Auto-discover and analyze project log files for error evidence |
| `-- no-logs` | Skip automatic log discovery (use only provided input) |

## Examples

### Example 1: Text Description
```
/acc-bug-fix "NullPointerException in OrderService::process()"
```

### Example 2: File Reference
```
/acc-bug-fix src/Domain/Order/OrderService.php:45 "off-by-one error in loop"
```

### Example 3: With Meta-Instructions
```
/acc-bug-fix "Payment validation fails for amounts > 1000" -- focus on validation
```

### Example 4: From Log File
```
/acc-bug-fix @storage/logs/laravel.log -- skip tests
```

### Example 5: Auto-discover Logs
```
/acc-bug-fix "connection refused to database" -- scan-logs
```

### Example 6: Dry Run
```
/acc-bug-fix src/Application/UseCase/CreateOrder.php:78 -- dry-run
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
