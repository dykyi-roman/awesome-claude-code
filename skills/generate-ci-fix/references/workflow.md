# CI Fix Workflow

## Workflow Diagram

```
/acc-ci-fix <input> [-- instructions]
         │
         ▼
  ┌──────────────┐
  │ Parse Input  │
  │ (URL/log/    │
  │  description)│
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Find CI      │
  │ Config Files │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Task →       │
  │ ci-debugger  │
  │ (diagnose)   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────┐
  │ Task →       │
  │ ci-fixer     │
  │ (generate)   │
  └──────┬───────┘
         │
         ▼
  ┌──────────────────────────────────────────┐
  │              Check Mode                   │
  │                                          │
  │  dry-run?  ──────────┐                   │
  │      │               ▼                   │
  │      │        ┌────────────┐             │
  │      │        │ Show Only  │             │
  │      │        │ (no apply) │             │
  │      │        └────────────┘             │
  │      │                                   │
  │  auto-apply? ────────┐                   │
  │      │               ▼                   │
  │      │        ┌────────────┐             │
  │      │        │ Apply Now  │             │
  │      │        │ (no ask)   │             │
  │      │        └────────────┘             │
  │      │                                   │
  │  interactive ────────┐                   │
  │                      ▼                   │
  │               ┌────────────┐             │
  │               │ Ask User   │             │
  │               │ (approve?) │             │
  │               └──────┬─────┘             │
  │                      │                   │
  │              ┌───────┴───────┐           │
  │              ▼               ▼           │
  │       [Yes/Apply]     [No/Skip]          │
  │              │               │           │
  │              ▼               ▼           │
  │       ┌──────────┐   ┌──────────┐        │
  │       │ Apply &  │   │ Show     │        │
  │       │ Validate │   │ Manual   │        │
  │       └──────────┘   └──────────┘        │
  └──────────────────────────────────────────┘
         │
         ▼
  ┌──────────────┐
  │ Report       │
  │ (with diff)  │
  └──────────────┘
```

## Usage Examples

### Example 1: Interactive Mode (default)
```
/acc-ci-fix "PHPStan memory exhausted"
```
→ Diagnoses → Shows fix → Asks approval → Applies if approved

### Example 2: Dry Run
```
/acc-ci-fix ./ci.log -- dry-run
```
→ Diagnoses → Shows fix → Ends (no changes)

### Example 3: Auto Apply
```
/acc-ci-fix ./ci.log -- auto-apply
```
→ Diagnoses → Applies fix immediately (for scripts/CI)

### Example 4: Pipeline URL
```
/acc-ci-fix https://github.com/org/repo/actions/runs/12345
```

### Example 5: With Focus
```
/acc-ci-fix "Tests timeout" -- focus on Docker, verbose
```

### Example 6: Auto-discover CI Logs
```
/acc-ci-fix "build failed" -- scan-logs
```

### Example 7: Skip Validation
```
/acc-ci-fix ./logs/ci.txt -- skip-validation
```
