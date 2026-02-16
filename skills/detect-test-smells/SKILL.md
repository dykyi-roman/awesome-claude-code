---
name: acc-detect-test-smells
description: Detects test antipatterns and code smells in PHP test suites. Identifies 15 smells (Logic in Test, Mock Overuse, Fragile Tests, Mystery Guest, etc.) with fix recommendations and refactoring patterns for testability.
---

# Test Smell Detection

Identifies antipatterns and code smells in PHP test suites.

## 15 Test Smells

| # | Smell | Severity | Detection Pattern |
|---|-------|----------|-------------------|
| 1 | Logic in Test | High | `if/for/while/foreach` in tests |
| 2 | Mock Overuse | High | >3 mocks in single test |
| 3 | Test Interdependence | High | `static $`, `@depends` |
| 4 | Fragile Test | High | `expects(exactly)`, `at()` |
| 5 | Mystery Guest | Medium | `file_get_contents`, `getenv` |
| 6 | Eager Test | Medium | Multiple unrelated assertions |
| 7 | Assertion Roulette | Medium | >5 assertions without context |
| 8 | Obscure Test | Low | `test_it_works`, `test_foo` |
| 9 | Test Code Duplication | Medium | Repeated setup/assertion |
| 10 | Conditional Test Logic | Medium | `if.*assert` patterns |
| 11 | Hard-Coded Test Data | Low | Magic values in tests |
| 12 | Testing Private Methods | High | `setAccessible(true)` |
| 13 | Slow Test | Medium | `sleep`, I/O in unit tests |
| 14 | Mocking Final Classes | High | Mock concrete final classes |
| 15 | Mocking Value Objects | High | Mock readonly/immutable classes |

## Quick Detection Commands

```bash
# Logic in tests
Grep: "if \(|for \(|while \(|foreach \(" --glob "tests/**/*Test.php"

# Mock overuse (manual count needed)
Grep: "createMock|createStub" --glob "tests/**/*Test.php"

# Test interdependence
Grep: "static \$|@depends" --glob "tests/**/*Test.php"

# Testing private methods
Grep: "setAccessible\(true\)|ReflectionMethod" --glob "tests/**/*Test.php"

# Mystery guest
Grep: "file_get_contents|fopen|getenv|_ENV|_SERVER" --glob "tests/**/*Test.php"

# Fragile tests
Grep: "expects\(.*exactly|expects\(.*at\(" --glob "tests/**/*Test.php"
```

## Output Format

```markdown
# Test Smell Report

## Summary

| Smell | Count | Severity |
|-------|-------|----------|
| Logic in Test | 5 | High |
| Mock Overuse | 3 | High |

## Findings

### Logic in Test (5 occurrences)

| File | Line | Code |
|------|------|------|
| OrderTest.php | 45 | `foreach ($items as $item)` |

**Recommendation:** Extract to data providers or inline values.

## Action Items

1. **High Priority** — Refactor tests with >5 mocks
2. **Medium Priority** — Inline fixture data
```

## Severity Matrix

| Severity | Smells | Impact |
|----------|--------|--------|
| **High** | Logic in Test, Mock Overuse, Test Interdependence, Fragile Test, Mocking Final/VO, Testing Private | Unreliable results, design problems |
| **Medium** | Mystery Guest, Eager Test, Slow Test, Conditional Logic, Duplication | Hard to understand/maintain |
| **Low** | Obscure Test, Hard-Coded Data | Documentation/readability |

## Related Skills

| Smell | Fix With |
|-------|----------|
| Mock Overuse | `acc-create-mock-repository` |
| Mystery Guest | `acc-create-test-builder` |
| Test Duplication | `acc-create-test-builder` |

## References

- `references/smell-catalog.md` — Full smell descriptions with code examples
- `references/refactoring-patterns.md` — Refactoring patterns for testability
