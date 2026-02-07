---
description: Audit test quality. Checks coverage gaps, test smells, naming, isolation. Recommends improvements and can generate fixes.
allowed-tools: Task
model: sonnet
argument-hint: <path> [-- additional instructions]
---

# Test Quality Audit

Invoke the `acc-test-auditor` agent to analyze test suite quality.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-test tests/
- /acc-audit-test tests/ -- focus on Domain layer only
- /acc-audit-test ./ -- skip integration tests, check unit only
- /acc-audit-test tests/ -- особое внимание на test smells
- /acc-audit-test tests/ -- check Order module coverage
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, additional focus/filters)

## Usage

```
/acc-audit-test <path> [-- instructions]
```

## Examples

```bash
# Audit entire test suite
/acc-audit-test tests/

# Audit specific module tests
/acc-audit-test tests/Unit/Domain/Order/

# Audit with focus instructions
/acc-audit-test tests/ -- focus on coverage gaps, skip smell detection

# Audit project (compares src/ with tests/)
/acc-audit-test ./
```

## What It Checks

### Coverage Analysis

- **Untested classes** — classes in src/ without tests
- **Untested methods** — public methods without test coverage
- **Uncovered branches** — if/else/switch without all paths tested
- **Exception paths** — throw statements without tests
- **Edge cases** — null, empty, boundary values

### Test Smells (15 antipatterns)

| Category | Smells |
|----------|--------|
| Logic | if/for/while in tests |
| Mocking | >3 mocks, mocking VOs/final |
| Isolation | shared state, test interdependence |
| Structure | eager tests, assertion roulette |
| Data | mystery guest, hard-coded values |
| Access | testing private methods |

### Quality Metrics

- Naming convention compliance
- AAA pattern usage
- Test isolation
- Execution speed indicators

## Execution

Use the Task tool to invoke the test auditor agent:

```
Task tool with subagent_type="acc-test-auditor"
prompt: "Perform test quality audit for $ARGUMENTS. Analyze coverage gaps, detect test smells, check naming conventions and isolation. Generate detailed report with skill recommendations for fixing issues."
```

## Output

The agent produces a structured report:

```markdown
# Test Quality Audit Report

## Summary
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Class Coverage | 75% | 90% | ⚠️ |
| Test Smell Count | 15 | 0 | ❌ |

## Coverage Analysis
- Untested classes
- Untested methods
- Uncovered branches

## Test Smells
- Critical issues (must fix)
- Warnings (should fix)

## Skill Recommendations
| Gap | Skill | Action |
|-----|-------|--------|
| Missing tests | acc-create-unit-test | Generate |
| Mock overuse | acc-create-mock-repository | Use Fakes |
```

## Generation Phase

After the audit, the agent offers to fix issues using:

- `/acc-generate-test` — for missing tests
- `acc-create-test-builder` — for test data
- `acc-create-mock-repository` — for Fakes
- `acc-create-test-double` — for appropriate doubles

## Severity Levels

| Level | Coverage | Action |
|-------|----------|--------|
| ❌ Critical | <50% or blocking smells | Immediate fix |
| ⚠️ Warning | 50-70% | Prioritize |
| ✅ Good | 70-90% | Monitor |
| 🌟 Excellent | >90% | Maintain |
