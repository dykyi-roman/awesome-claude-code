---
description: Audit test quality. Checks coverage gaps, test smells, naming, isolation. Recommends improvements and can generate fixes.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# Test Quality Audit

Perform a comprehensive test quality audit with actionable improvement recommendations.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-test tests/
- /acc-audit-test tests/ -- focus on Domain layer only
- /acc-audit-test ./ -- skip integration tests, check unit only
- /acc-audit-test tests/ -- level:deep
- /acc-audit-test tests/ -- check Order module coverage
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, additional focus/filters)

## Pre-flight Check

1. **Verify the path exists:**
   - If `$ARGUMENTS` is empty, audit current directory
   - If path doesn't exist, report error and stop

2. **Verify test infrastructure:**
   - Check for `phpunit.xml` or `phpunit.xml.dist`
   - Check for `tests/` directory
   - Check for PHPUnit in `composer.json` (require-dev)
   - If no test infrastructure found, report and suggest `/acc-generate-test`

3. **Check test tooling:**
   - Look for coverage configuration (Xdebug/PCOV)
   - Note Pest, Codeception, or other frameworks if present

## Audit Levels

Extract audit level from meta-instructions: `level:quick`, `level:standard`, `level:deep`. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Coverage count | Class/method coverage percentage, critical untested paths |
| `standard` | Full analysis | Coverage gaps, test smells (15 antipatterns), naming, isolation, quality metrics |
| `deep` | Standard + cross-analysis | Standard + cross-test dependencies, test execution order sensitivity, fixture analysis |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Coverage <50%, tests with side effects, broken test isolation |
| High | 🟠 | Coverage 50-70%, >3 mocks per test, logic in tests |
| Medium | 🟡 | Naming violations, missing AAA pattern, hard-coded values |
| Low | 🟢 | Style suggestions, minor improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on coverage` | Deep coverage gap analysis |
| `focus on smells` | Prioritize test smell detection |
| `unit only` | Only analyze unit tests |
| `skip integration` | Exclude integration tests |
| `check [Module]` | Focus on specific module tests |
| `level:quick` | Fast audit (coverage counts only) |
| `level:deep` | Deep audit (+ cross-test dependencies) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

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

## Instructions

Use the `acc-test-auditor` agent to perform quality assessment:

```
Task tool with subagent_type="acc-test-auditor"
prompt: "Perform test quality audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Use TaskCreate/TaskUpdate for progress visibility. Create tasks for each audit phase.

Analyze:
1. Coverage gaps — untested classes, methods, branches, exception paths
2. Test smells — 15 antipatterns (logic in tests, mock overuse, shared state, etc.)
3. Naming conventions — test method naming, class naming
4. Test isolation — shared state, test interdependence
5. Quality metrics — AAA pattern, assertion quality

For each issue provide:
- Severity (🔴/🟠/🟡/🟢)
- File:line location
- What's wrong and how to fix it

Generate detailed report with skill recommendations for fixing issues."
```

## Expected Output

```markdown
# Test Quality Audit Report

**Project:** [NAME] | **Date:** [DATE] | **Level:** [quick|standard|deep]

## 1. Executive Summary

| Category | Score | 🔴 | 🟠 | 🟡 | 🟢 |
|----------|-------|-----|-----|-----|-----|
| Coverage | X/100 | N | N | N | N |
| Test Smells | X/100 | N | N | N | N |
| Naming | X/100 | N | N | N | N |
| Isolation | X/100 | N | N | N | N |

**Overall Score:** X/100 | **Risk Level:** LOW/MEDIUM/HIGH/CRITICAL

## 2. Coverage Analysis

| Layer | Classes | Tested | Coverage | Status |
|-------|---------|--------|----------|--------|
| Domain | 15 | 14 | 93% | 🟢 |
| Application | 10 | 7 | 70% | 🟠 |
| Infrastructure | 8 | 3 | 38% | 🔴 |

### Untested Classes
- 🔴 `src/Application/UseCase/CreateOrder.php` — No test found
- 🟠 `src/Infrastructure/Repository/UserRepository.php` — Partial coverage

## 3. Test Smells by Severity

### 🔴 Critical
- **Location:** `tests/Unit/OrderTest.php:45` — Shared mutable state between tests

### 🟠 High Priority
- **Location:** `tests/Unit/UserTest.php:23` — 5 mocks in single test (max: 3)

### 🟡 Medium
- **Location:** `tests/Unit/PaymentTest.php:67` — Hard-coded test values (magic numbers)

## 4. Quality Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Class Coverage | 75% | 90% | 🟠 |
| Method Coverage | 68% | 85% | 🟠 |
| Test Smell Count | 12 | 0 | 🟠 |
| AAA Compliance | 85% | 95% | 🟡 |
| Naming Compliance | 90% | 95% | 🟢 |

## 5. Skill Recommendations

| Gap | Skill | Command |
|-----|-------|---------|
| Missing unit tests | `acc-create-unit-test` | `/acc-generate-test unit` |
| Mock overuse | `acc-create-mock-repository` | `/acc-generate-test mock` |
| Missing test data | `acc-create-test-builder` | `/acc-generate-test builder` |
| Integration tests | `acc-create-integration-test` | `/acc-generate-test integration` |

## 6. Action Items

1. 🔴 Fix shared state in OrderTest.php
2. 🔴 Add tests for 3 untested critical classes
3. 🟠 Reduce mock count in UserTest.php
4. 🟡 Replace magic numbers with named constants
5. 🟢 Align test naming to `test_should_X_when_Y` pattern
```

## Usage Examples

```bash
# Audit entire test suite
/acc-audit-test tests/

# Quick coverage check
/acc-audit-test ./ -- level:quick

# Deep analysis with cross-dependencies
/acc-audit-test tests/ -- level:deep

# Focus on specific module
/acc-audit-test tests/Unit/Domain/Order/

# Focus on coverage gaps
/acc-audit-test tests/ -- focus on coverage gaps, skip smell detection
```
