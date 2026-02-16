---
description: Fix CI pipeline issues with interactive approval
allowed-tools: Task, Read, Grep, Glob, Edit, Write, Bash, AskUserQuestion
model: opus
argument-hint: <pipeline-url|log-file|description> [-- instructions]
---

# CI Fix Command

You are executing the `/acc-ci-fix` command. Your task is to diagnose CI pipeline issues and apply fixes with user approval.

## Input Received

**User Input:** $ARGUMENTS

**Meta-Instructions:** Parse any text after `--` as meta-instructions:
- `-- dry-run` — Show diagnosis and fix without applying or asking
- `-- auto-apply` — Apply fix without asking (for CI/scripts)
- `-- verbose` — Include detailed diagnosis output
- `-- skip-validation` — Don't run local syntax checks
- `-- focus on <area>` — Prioritize specific area (tests, lint, docker)

## Execution Flow

### Step 1: Parse Input

Determine the input type:

1. **Pipeline URL** (contains `github.com/` or `gitlab.com/`)
   - Extract repository and run ID
   - Use `gh` CLI to fetch logs if GitHub
   - Parse URL for context

2. **Log File Reference** (file path or starts with `@`)
   - Read the log file
   - Extract error messages and context

3. **Auto-discover CI Logs** (when `-- scan-logs` is specified or no log file provided with `-- scan-logs`)
   - Use `acc-discover-project-logs` skill via ci-debugger to find CI build logs:
     - `build/logs/*.log`, `build/logs/*.xml`
     - `build/reports/*.xml`
     - PHPUnit/PHPStan output files
   - If no logs found, use AskUserQuestion:
     ```
     Question: "CI log files not found automatically. Where are your CI logs?"
     Options:
       - "build/logs/" (PHPUnit/PHPStan output)
       - "build/reports/" (CI reports)
       - "Paste pipeline URL" (GitHub Actions / GitLab CI)
     ```

4. **Text Description**
   - Search codebase for CI configuration
   - Use description to guide diagnosis

### Step 2: Locate CI Configuration

Find CI configuration files:

```
Task → Explore agent

Find CI configuration files:
- .github/workflows/*.yml (GitHub Actions)
- .gitlab-ci.yml (GitLab CI)
- phpstan.neon, psalm.xml (static analysis)
- phpunit.xml (testing)
- Dockerfile, docker-compose.yml (Docker)
```

### Step 3: Diagnose Issue

Invoke `acc-ci-debugger` agent to diagnose:

```
Task → acc-ci-debugger

Analyze this CI issue:
[log content or description]

CI Configuration:
[relevant config files]

Provide:
1. Failure category (dependency/test/lint/infrastructure/docker/timeout)
2. Error pattern matched
3. Root cause
4. Specific error location
5. Fix recommendations
```

### Step 4: Generate Fix Preview

Invoke `acc-ci-fixer` agent to generate fix (but NOT apply yet):

```
Task → acc-ci-fixer

Diagnosis from acc-ci-debugger:
[diagnosis]

CI Configuration:
[relevant config]

Generate fix preview:
1. Show what changes will be made
2. Show diff preview
3. Provide rollback instructions
4. DO NOT apply changes yet
```

### Step 5: Show Proposed Fix and Ask Approval

**If `-- dry-run` specified:**
- Show diagnosis and proposed fix
- Do NOT ask for approval
- End with: "Dry run complete. Use without `-- dry-run` to apply."

**If `-- auto-apply` specified:**
- Skip to Step 6 (Apply Fix)

**Otherwise (interactive mode):**

Display the proposed fix to the user, then use AskUserQuestion:

```
AskUserQuestion:
  question: "Apply this fix to your CI configuration?"
  header: "CI Fix"
  options:
    - label: "Yes, apply fix"
      description: "Apply the changes shown above to CI config files"
    - label: "No, skip"
      description: "Don't apply changes, show manual fix instructions instead"
    - label: "Show more details"
      description: "Show verbose diagnosis before deciding"
```

### Step 6: Apply or Cancel

**If user selects "Yes, apply fix" OR `-- auto-apply`:**
1. Apply fix using Edit tool
2. Run validation (unless `-- skip-validation`)
3. Show success report with rollback instructions

**If user selects "No, skip":**
1. Show manual fix instructions
2. Provide copy-paste commands
3. End without making changes

**If user selects "Show more details":**
1. Show verbose diagnosis
2. Return to Step 5 (ask again)

### Step 7: Validate Fix (Optional)

Unless `-- skip-validation` specified:

```bash
# Validate YAML syntax
yamllint .github/workflows/*.yml 2>/dev/null || echo "yamllint not installed"

# Validate PHP config
php -l phpstan.neon 2>/dev/null || true

# Check Docker syntax
docker build --check . 2>/dev/null || true
```

### Step 8: Report Results

Output a comprehensive report:

```markdown
# CI Fix Report

## Summary
| Field | Value |
|-------|-------|
| Issue | [failure type] |
| Cause | [root cause] |
| Status | ✅ Fixed / ⏭️ Skipped / 📋 Dry Run |

## Diagnosis
**Category:** [dependency/test/lint/infrastructure/docker/timeout]
**Error Pattern:** [matched pattern]

[Summary from acc-ci-debugger]

## Fix Applied (or Proposed)

**File:** `path/to/config.yml`

```diff
- [old config]
+ [new config]
```

## Verification

```bash
# Test locally:
[command]

# Re-run pipeline:
[instructions]
```

## Rollback

If fix causes issues:
```bash
git checkout HEAD~1 -- [file]
```

## Prevention
[How to prevent recurrence]

## Next Steps
[Any recommended follow-up actions]
```

## Meta-Instructions Handling

| Instruction | Effect |
|-------------|--------|
| `-- dry-run` | Show diagnosis and fix without applying or asking |
| `-- auto-apply` | Apply fix without asking (for CI/scripts) |
| `-- skip-validation` | Don't run local syntax checks |
| `-- verbose` | Include detailed diagnosis output |
| `-- focus on <area>` | Prioritize specific area (tests, lint, docker) |
| `-- scan-logs` | Auto-discover CI build logs in project (build/logs/, build/reports/) |

## Examples

```bash
/acc-ci-fix "PHPStan memory exhausted"                            # Interactive (default)
/acc-ci-fix ./ci.log -- dry-run                                   # Show diagnosis only
/acc-ci-fix ./ci.log -- auto-apply                                # Apply without asking
/acc-ci-fix https://github.com/org/repo/actions/runs/12345        # From pipeline URL
/acc-ci-fix "Tests timeout" -- focus on Docker, verbose           # Focused + verbose
/acc-ci-fix "build failed" -- scan-logs                           # Auto-discover logs
```

## Error Handling

### If diagnosis fails:
- Report what was found
- Suggest manual investigation points
- Ask for more context (logs, config)

### If fix cannot be applied:
- Report the diagnosis
- Explain why automatic fix isn't possible
- Provide manual fix instructions

### If validation fails:
- Report validation errors
- Don't apply fix
- Suggest corrections

## Supported CI Issues

| Issue Type | Auto-Fix Support |
|------------|------------------|
| Memory exhausted | ✅ Full |
| Composer conflict | ✅ Full |
| PHPStan baseline | ✅ Full |
| Service not ready | ✅ Full |
| Docker build fail | ⚠️ Partial |
| Timeout | ✅ Full |
| Permission denied | ✅ Full |
| Cache miss | ✅ Full |
| PHP extension | ✅ Full |
| Env variable | ✅ Full |

## DDD Project Awareness

When fixing CI for DDD projects, respect architecture:

- **Domain tests** should run first (fastest)
- **Application tests** after Domain
- **Infrastructure tests** last (may need services)
- Separate unit from integration tests
- PHPStan rules for layer violations
- DEPTRAC for dependency rules
