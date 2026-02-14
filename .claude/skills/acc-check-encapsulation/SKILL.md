---
name: acc-check-encapsulation
description: Analyzes PHP code for encapsulation violations. Detects public mutable state, exposed internals, Tell Don't Ask violations, getter/setter abuse, and information hiding breaches.
---

# Encapsulation Analyzer

## Overview

This skill analyzes PHP codebases for encapsulation violations — situations where internal state is exposed, getters/setters replace behavior, or the "Tell, Don't Ask" principle is violated.

## When to Use

- Reviewing Domain layer entities and aggregates
- Detecting anemic domain models
- Checking for Law of Demeter violations
- Auditing collection exposure patterns
- Evaluating getter/behavior ratio in entities

## Encapsulation Principles

| Principle | Description | Violation Indicator |
|-----------|-------------|---------------------|
| Information Hiding | Internal state not exposed | Public properties, many getters |
| Tell Don't Ask | Objects perform actions, not expose data | Getter chains, external decisions |
| Behavioral Richness | Objects have behavior, not just data | Anemic domain model |
| Invariant Protection | State changes validate constraints | Public setters without validation |

## Analysis Approach

1. **Phase 1 — Public Mutable State:** Scan Domain entities for non-readonly public properties
2. **Phase 2 — Getter/Setter Abuse:** Count getters vs behavior methods, flag anemic entities
3. **Phase 3 — Tell Don't Ask:** Detect getter chains and external conditionals on object state
4. **Phase 4 — Collection Exposure:** Find methods returning internal arrays/collections directly
5. **Phase 5 — Exposed Internals:** Check for reflection usage, debug methods, mutable object returns
6. **Phase 6 — Constructor Issues:** Flag too many dependencies, complex construction without factories

## Detection Rules

| ID | Pattern | Grep Target |
|----|---------|-------------|
| ENC-01 | Public mutable props | `public string\|public int\|public array` in Domain (exclude readonly) |
| ENC-02 | Setter methods | `public function set[A-Z]` in Entity/Aggregate |
| ENC-03 | Getter chains | `->get[A-Z].*->get[A-Z].*->get[A-Z]` |
| ENC-04 | External conditionals | `if \(\$.*->get[A-Z].*===` |
| ENC-05 | Switch on state | `switch \(\$.*->get[A-Z]\|match \(\$.*->get[A-Z]` |
| ENC-06 | Collection return | `public function get.*\(\): array` in Entity |
| ENC-07 | Doctrine exposure | `public function get.*\(\): Collection` in Domain |
| ENC-08 | Reflection access | `ReflectionClass\|ReflectionProperty\|setAccessible` |
| ENC-09 | Debug exposure | `public function toArray\(\)\|dump\(\)\|debug\(\)` in Domain |
| ENC-10 | Complex construction | `new [A-Z].*Entity\(\|new [A-Z].*Aggregate\(` in Application |

## Severity Classification

| Issue | Severity |
|-------|----------|
| Public mutable state in Entity | Critical |
| Collection mutated externally | Critical |
| Anemic entity (ratio > 5.0) | Critical |
| Tell Don't Ask violation | Major |
| Getter chain (3+ levels) | Major |
| Internal array returned | Major |
| Setter in Aggregate | Minor |
| Reflection in non-test code | Minor |

## Report Format

```markdown
# Encapsulation Analysis Report

## Summary

| Issue Type | Critical | Warning | Info |
|------------|----------|---------|------|
| Public Mutable State | N | N | - |
| Getter/Setter Abuse | N | N | N |
| Tell Don't Ask | N | N | - |
| Collection Exposure | N | N | - |
| Exposed Internals | N | N | N |

**Encapsulation Score: X%**

## Findings

### [ID]: [Title]
- **File:** `path:line`
- **Issue:** [Description]
- **Code:** [Problematic snippet]
- **Expected:** [Correct pattern]
- **Skills:** [Related generator skills]

## Getter/Behavior Ratio

| Entity | Getters | Setters | Behavior | Ratio | Status |
|--------|---------|---------|----------|-------|--------|

**Target:** Ratio < 2.0

## Refactoring Recommendations

### Immediate
1. Make all entity properties private
2. Replace setters with behavior methods
3. Return collection copies, not references

### Short-term
4. Extract Value Objects for validated data
5. Add factory methods for complex construction
6. Remove getter chains (add shortcut methods)

### Long-term
7. Review anemic entities for missing behavior
8. Consider CQRS to separate read/write models
```

## Integration

Works with:
- `acc-detect-code-smells` — Feature Envy, Anemic Model
- `acc-structural-auditor` — DDD compliance
- `acc-create-entity` — Generate rich entities
- `acc-create-value-object` — Encapsulated value types

## References

- `references/patterns.md` — detailed detection patterns with code examples, report format samples, metrics examples, and rich entity template
- "Tell, Don't Ask" — Martin Fowler
- "Anemic Domain Model" — Martin Fowler
- "Object-Oriented Software Construction" (Bertrand Meyer)
- "Elegant Objects" (Yegor Bugayenko)
