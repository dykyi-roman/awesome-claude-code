# Agents

Subagents for specialized tasks. Agents are autonomous workers that handle complex, multi-step operations.

## Overview

### Coordinators (0-3 skills, delegate via Task tool)

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `acc-architecture-auditor` | Architecture audit coordinator | `/acc-audit-architecture` |
| `acc-pattern-auditor` | Design patterns audit coordinator | `acc-architecture-auditor` (Task) |
| `acc-pattern-generator` | Design patterns generation coordinator | `acc-architecture-auditor` (Task) |
| `acc-code-review-coordinator` | Code review coordinator (3 levels) | `/acc-code-review` |
| `acc-bug-fix-coordinator` | Bug fix coordinator (diagnose → fix → test) | `/acc-fix-bug` |

### Auditors (3-12 skills)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-structural-auditor` | Structural patterns analysis | 12 | `acc-architecture-auditor` (Task) |
| `acc-behavioral-auditor` | Behavioral patterns analysis | 12 | `acc-architecture-auditor`, `acc-pattern-auditor` (Task) |
| `acc-integration-auditor` | Integration patterns analysis | 12 | `acc-architecture-auditor`, `acc-pattern-auditor` (Task) |
| `acc-stability-auditor` | Stability patterns analysis | 5 | `acc-pattern-auditor` (Task) |
| `acc-creational-auditor` | Creational patterns analysis | 3 | `acc-pattern-auditor` (Task) |
| `acc-ddd-auditor` | DDD compliance analysis | 3 | `/acc-audit-ddd` |
| `acc-psr-auditor` | PSR compliance analysis | 3 | `/acc-audit-psr` |
| `acc-documentation-auditor` | Audit documentation quality | 3 | `/acc-audit-documentation` |
| `acc-test-auditor` | Test quality analysis | 3 | `/acc-audit-test` |

### Reviewers (7-9 skills, code review specialists)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-bug-hunter` | Bug detection specialist | 9 | `acc-code-review-coordinator`, `acc-bug-fix-coordinator` (Task) |
| `acc-security-reviewer` | Security review specialist | 9 | `acc-code-review-coordinator` (Task) |
| `acc-performance-reviewer` | Performance review specialist | 8 | `acc-code-review-coordinator` (Task) |
| `acc-readability-reviewer` | Readability review specialist | 9 | `acc-code-review-coordinator` (Task) |
| `acc-testability-reviewer` | Testability review specialist | 7 | `acc-code-review-coordinator` (Task) |

### Bug Fix Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-bug-fixer` | Bug fix generator | 11 | `acc-bug-fix-coordinator` (Task) |

### Generators (3-14 skills)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-architecture-generator` | Generate architecture components | 7 | `acc-architecture-auditor` (Task) |
| `acc-ddd-generator` | Generate DDD components | 14 | `acc-ddd-auditor` (Task) |
| `acc-stability-generator` | Generate stability patterns | 5 | `acc-pattern-generator` (Task) |
| `acc-behavioral-generator` | Generate behavioral patterns | 5 | `acc-pattern-generator` (Task) |
| `acc-creational-generator` | Generate creational patterns | 3 | `acc-pattern-generator` (Task) |
| `acc-integration-generator` | Generate integration patterns | 7 | `acc-pattern-generator` (Task) |
| `acc-psr-generator` | Generate PSR implementations | 14 | `acc-psr-auditor` (Skill) |
| `acc-documentation-writer` | Generate documentation | 9 | `/acc-write-documentation` |
| `acc-diagram-designer` | Create Mermaid diagrams | 2 | `acc-documentation-writer` (Task) |
| `acc-test-generator` | Generate PHP tests | 6 | `/acc-write-test` |

### Experts

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `acc-claude-code-expert` | Create Claude Code components | `/acc-write-claude-component` |

## How Agents Work

1. **Invocation**: Commands invoke agents via Task tool or direct reference
2. **Skills Loading**: Agent loads skills from `skills:` frontmatter
3. **Execution**: Agent performs multi-step analysis or generation
4. **Delegation**: Agent may delegate subtasks to other agents via Task tool

---

## `acc-claude-code-expert`

**Path:** `agents/acc-write-claude-component-expert.md`

Expert in creating Claude Code commands, agents, and skills.

**Configuration:**
```yaml
name: acc-claude-code-expert
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
skills: acc-claude-code-knowledge
```

---

## `acc-architecture-auditor`

**Path:** `agents/acc-architecture-auditor.md`

Architecture audit coordinator. Orchestrates three specialized auditors for comprehensive reviews.

**Configuration:**
```yaml
name: acc-architecture-auditor
tools: Read, Grep, Glob, Task
model: opus
# No skills - delegates to specialized auditors
```

**Workflow:**
1. Pattern Detection (Glob/Grep for structural, behavioral, integration patterns)
2. Parallel Task delegation to 3 auditors
3. Cross-Pattern Analysis (detect conflicts between patterns)
4. Report Aggregation (unified markdown report)

---

## `acc-structural-auditor`

**Path:** `agents/acc-structural-auditor.md`

Structural architecture auditor for DDD, Clean Architecture, Hexagonal, Layered, SOLID, GRASP.

**Configuration:**
```yaml
name: acc-structural-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-ddd-knowledge, acc-clean-arch-knowledge, acc-hexagonal-knowledge,
        acc-layer-arch-knowledge, acc-solid-knowledge, acc-grasp-knowledge,
        acc-analyze-solid-violations, acc-detect-code-smells, acc-check-bounded-contexts,
        acc-check-immutability, acc-check-leaky-abstractions, acc-check-encapsulation
```

**Skills:** 12 (6 knowledge + 6 analyzer)

---

## `acc-behavioral-auditor`

**Path:** `agents/acc-behavioral-auditor.md`

Behavioral patterns auditor for CQRS, Event Sourcing, EDA, and GoF behavioral patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object).

**Configuration:**
```yaml
name: acc-behavioral-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-cqrs-knowledge, acc-event-sourcing-knowledge, acc-eda-knowledge,
        acc-create-command, acc-create-query, acc-create-domain-event,
        acc-create-read-model, acc-create-strategy, acc-create-state,
        acc-create-chain-of-responsibility, acc-create-decorator,
        acc-create-null-object
```

**Skills:** 12 (3 knowledge + 9 generators)

---

## `acc-integration-auditor`

**Path:** `agents/acc-integration-auditor.md`

Integration patterns auditor for Outbox, Saga, Stability, and ADR.

**Configuration:**
```yaml
name: acc-integration-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge,
        acc-stability-patterns-knowledge, acc-adr-knowledge,
        acc-create-outbox-pattern, acc-create-saga-pattern,
        acc-create-circuit-breaker, acc-create-retry-pattern,
        acc-create-rate-limiter, acc-create-bulkhead,
        acc-create-action, acc-create-responder
```

**Skills:** 12 (4 knowledge + 8 generators)

---

## `acc-stability-auditor`

**Path:** `agents/acc-stability-auditor.md`

Stability patterns auditor for Circuit Breaker, Retry, Rate Limiter, and Bulkhead.

**Configuration:**
```yaml
name: acc-stability-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-stability-patterns-knowledge, acc-create-circuit-breaker,
        acc-create-retry-pattern, acc-create-rate-limiter, acc-create-bulkhead
```

**Skills:** 5 (1 knowledge + 4 generators)

---

## `acc-creational-auditor`

**Path:** `agents/acc-creational-auditor.md`

Creational patterns auditor for Builder, Object Pool, and Factory patterns.

**Configuration:**
```yaml
name: acc-creational-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-create-builder, acc-create-object-pool, acc-create-factory
```

**Skills:** 3 (generators only)

---

## `acc-ddd-auditor`

**Path:** `agents/acc-ddd-auditor.md`

Specialized DDD compliance auditor.

**Configuration:**
```yaml
name: acc-ddd-auditor
tools: Read, Grep, Glob, Bash, Task
model: opus
skills: acc-ddd-knowledge, acc-solid-knowledge, acc-grasp-knowledge
```

**Skills:** 3 (knowledge only, generation delegated to `acc-ddd-generator` via Task)

---

## `acc-ddd-generator`

**Path:** `agents/acc-ddd-generator.md`

Creates DDD and architecture components.

**Configuration:**
```yaml
name: acc-ddd-generator
tools: Read, Write, Glob, Grep
model: opus
skills: acc-ddd-knowledge, acc-create-value-object, acc-create-entity,
        acc-create-aggregate, acc-create-domain-event, acc-create-repository,
        acc-create-command, acc-create-query, acc-create-use-case,
        acc-create-domain-service, acc-create-factory, acc-create-specification,
        acc-create-dto, acc-create-anti-corruption-layer
```

---

## `acc-pattern-auditor`

**Path:** `agents/acc-pattern-auditor.md`

Design patterns audit coordinator. Orchestrates stability, behavioral, creational, and integration auditors.

**Configuration:**
```yaml
name: acc-pattern-auditor
tools: Read, Grep, Glob, Task
model: opus
skills: acc-solid-knowledge, acc-grasp-knowledge
```

**Skills:** 2 (knowledge only, delegates to 4 specialized auditors via Task)

**Delegation:**
- `acc-stability-auditor` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc-behavioral-auditor` — Strategy, State, Chain, Decorator, Null Object
- `acc-creational-auditor` — Builder, Object Pool, Factory
- `acc-integration-auditor` — Outbox, Saga, ADR

---

## `acc-pattern-generator`

**Path:** `agents/acc-pattern-generator.md`

Design patterns generation coordinator. Orchestrates stability, behavioral, creational, and integration generators.

**Configuration:**
```yaml
name: acc-pattern-generator
tools: Read, Write, Glob, Grep, Edit, Task
model: opus
skills: acc-adr-knowledge
```

**Skills:** 1 (delegates to 4 specialized generators via Task)

**Delegation:**
- `acc-stability-generator` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc-behavioral-generator` — Strategy, State, Chain, Decorator, Null Object
- `acc-creational-generator` — Builder, Object Pool, Factory
- `acc-integration-generator` — Outbox, Saga, Action, Responder

---

## `acc-stability-generator`

**Path:** `agents/acc-stability-generator.md`

Generates stability patterns (Circuit Breaker, Retry, Rate Limiter, Bulkhead).

**Configuration:**
```yaml
name: acc-stability-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-stability-patterns-knowledge, acc-create-circuit-breaker,
        acc-create-retry-pattern, acc-create-rate-limiter, acc-create-bulkhead
```

**Skills:** 5

---

## `acc-behavioral-generator`

**Path:** `agents/acc-behavioral-generator.md`

Generates behavioral patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object).

**Configuration:**
```yaml
name: acc-behavioral-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-create-strategy, acc-create-state, acc-create-chain-of-responsibility,
        acc-create-decorator, acc-create-null-object
```

**Skills:** 5

---

## `acc-creational-generator`

**Path:** `agents/acc-creational-generator.md`

Generates creational patterns (Builder, Object Pool, Factory).

**Configuration:**
```yaml
name: acc-creational-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-create-builder, acc-create-object-pool, acc-create-factory
```

**Skills:** 3

---

## `acc-integration-generator`

**Path:** `agents/acc-integration-generator.md`

Generates integration patterns (Outbox, Saga, Action, Responder).

**Configuration:**
```yaml
name: acc-integration-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge, acc-adr-knowledge,
        acc-create-outbox-pattern, acc-create-saga-pattern,
        acc-create-action, acc-create-responder
```

**Skills:** 7

---

## `acc-architecture-generator`

**Path:** `agents/acc-architecture-generator.md`

Meta-generator coordinating DDD and integration pattern generation for bounded contexts and complex structures.

**Configuration:**
```yaml
name: acc-architecture-generator
tools: Read, Write, Glob, Grep, Edit, Task
model: opus
skills: acc-ddd-knowledge, acc-cqrs-knowledge, acc-clean-arch-knowledge,
        acc-eda-knowledge, acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge,
        acc-stability-patterns-knowledge
```

**Capabilities:**
- Direct generation: Value Objects, Entities, Aggregates, Commands, Queries, DTOs
- Delegated generation: Complex DDD structures via `acc-ddd-generator`, Outbox/Saga via `acc-pattern-generator`
- Bounded context scaffolding
- CQRS + Event Sourcing setup
- Full feature vertical slices

---

## `acc-psr-auditor`

**Path:** `agents/acc-psr-auditor.md`

PSR compliance auditor for PHP projects. Analyzes coding standards and interface implementations.

**Configuration:**
```yaml
name: acc-psr-auditor
tools: Read, Bash, Grep, Glob
model: opus
skills: acc-psr-coding-style-knowledge, acc-psr-autoloading-knowledge, acc-psr-overview-knowledge
```

**Analysis Phases:**
1. Project structure discovery
2. PSR-1/PSR-12 coding style analysis
3. PSR-4 autoloading verification
4. PSR interface detection
5. Report generation with skill recommendations

---

## `acc-psr-generator`

**Path:** `agents/acc-psr-generator.md`

Creates PSR-compliant PHP components.

**Configuration:**
```yaml
name: acc-psr-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-psr-overview-knowledge, acc-psr-coding-style-knowledge, acc-psr-autoloading-knowledge,
        acc-create-psr3-logger, acc-create-psr6-cache, acc-create-psr7-http-message,
        acc-create-psr11-container, acc-create-psr13-link, acc-create-psr14-event-dispatcher,
        acc-create-psr15-middleware, acc-create-psr16-simple-cache, acc-create-psr17-http-factory,
        acc-create-psr18-http-client, acc-create-psr20-clock
```

---

## `acc-documentation-writer`

**Path:** `agents/acc-documentation-writer.md`

Technical documentation writer for PHP projects.

**Configuration:**
```yaml
name: acc-documentation-writer
tools: Read, Write, Edit, Glob, Grep
model: opus
skills: acc-documentation-knowledge, acc-readme-template, acc-architecture-doc-template,
        acc-adr-template, acc-api-doc-template, acc-getting-started-template,
        acc-troubleshooting-template, acc-code-examples-template, acc-changelog-template
```

---

## `acc-documentation-auditor`

**Path:** `agents/acc-documentation-auditor.md`

Documentation quality auditor.

**Configuration:**
```yaml
name: acc-documentation-auditor
tools: Read, Glob, Grep, Bash
model: opus
skills: acc-documentation-qa-knowledge, acc-documentation-knowledge, acc-claude-code-knowledge
```

---

## `acc-diagram-designer`

**Path:** `agents/acc-diagram-designer.md`

Diagram designer for technical documentation.

**Configuration:**
```yaml
name: acc-diagram-designer
tools: Read, Write, Edit, Glob, Grep
model: opus
skills: acc-diagram-knowledge, acc-mermaid-template
```

---

## `acc-test-auditor`

**Path:** `agents/acc-test-auditor.md`

Test quality auditor for PHP projects.

**Configuration:**
```yaml
name: acc-test-auditor
tools: Read, Bash, Grep, Glob
model: opus
skills: acc-testing-knowledge, acc-analyze-test-coverage, acc-detect-test-smells
```

**Analysis Phases:**
1. Project discovery (framework, PHPUnit/Pest)
2. Coverage analysis (untested classes, methods, branches)
3. Test smell detection (15 antipatterns)
4. Quality metrics (naming, isolation)
5. Report generation with skill recommendations

---

## `acc-test-generator`

**Path:** `agents/acc-test-generator.md`

Test generator for DDD/CQRS PHP projects.

**Configuration:**
```yaml
name: acc-test-generator
tools: Read, Write, Glob, Grep
model: opus
skills: acc-testing-knowledge, acc-create-unit-test, acc-create-integration-test,
        acc-create-test-builder, acc-create-mock-repository, acc-create-test-double
```

**Generation Process:**
1. Analyze source code (class type, dependencies)
2. Classify test type (unit/integration)
3. Prepare infrastructure (builders, fakes)
4. Generate tests using appropriate skill
5. Verify quality rules compliance

---

---

## `acc-code-review-coordinator`

**Path:** `agents/acc-code-review-coordinator.md`

Code review coordinator orchestrating multi-level reviews (low/medium/high) with git diff analysis.

**Configuration:**
```yaml
name: acc-code-review-coordinator
tools: Read, Grep, Glob, Bash, Task
model: opus
skills: acc-analyze-solid-violations, acc-detect-code-smells, acc-check-encapsulation
```

**Review Levels:**
- **LOW**: PSR + Tests + Encapsulation + Code Smells
- **MEDIUM**: LOW + Bugs + Readability + SOLID
- **HIGH**: MEDIUM + Security + Performance + Testability + DDD + Architecture

---

## `acc-bug-hunter`

**Path:** `agents/acc-bug-hunter.md`

Bug detection specialist for code review.

**Configuration:**
```yaml
name: acc-bug-hunter
tools: Read, Grep, Glob
model: sonnet
skills: acc-find-logic-errors, acc-find-null-pointer-issues, acc-find-boundary-issues,
        acc-find-race-conditions, acc-find-resource-leaks, acc-find-exception-issues,
        acc-find-type-issues, acc-find-sql-injection, acc-find-infinite-loops
```

**Skills:** 9 (bug detection)

---

## `acc-security-reviewer`

**Path:** `agents/acc-security-reviewer.md`

Security review specialist for OWASP Top 10 vulnerabilities.

**Configuration:**
```yaml
name: acc-security-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: acc-check-input-validation, acc-check-output-encoding, acc-check-authentication,
        acc-check-authorization, acc-check-sensitive-data, acc-check-csrf-protection,
        acc-check-crypto-usage, acc-check-dependency-vulnerabilities, acc-check-sql-injection
```

**Skills:** 9 (security checks)

---

## `acc-performance-reviewer`

**Path:** `agents/acc-performance-reviewer.md`

Performance review specialist for efficiency issues.

**Configuration:**
```yaml
name: acc-performance-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: acc-detect-n-plus-one, acc-check-query-efficiency, acc-detect-memory-issues,
        acc-check-caching-strategy, acc-detect-unnecessary-loops, acc-check-lazy-loading,
        acc-check-batch-processing, acc-estimate-complexity
```

**Skills:** 8 (performance checks)

---

## `acc-readability-reviewer`

**Path:** `agents/acc-readability-reviewer.md`

Readability review specialist for code quality.

**Configuration:**
```yaml
name: acc-readability-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: acc-check-naming, acc-check-code-style, acc-check-method-length,
        acc-check-class-length, acc-check-nesting-depth, acc-check-comments,
        acc-check-magic-values, acc-check-consistency, acc-suggest-simplification
```

**Skills:** 9 (readability checks)

---

## `acc-testability-reviewer`

**Path:** `agents/acc-testability-reviewer.md`

Testability review specialist for test quality.

**Configuration:**
```yaml
name: acc-testability-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: acc-check-dependency-injection, acc-check-pure-functions, acc-check-side-effects,
        acc-check-test-quality, acc-suggest-testability-improvements,
        acc-analyze-test-coverage, acc-detect-test-smells
```

**Skills:** 7 (testability checks)

---

## `acc-bug-fix-coordinator`

**Path:** `agents/acc-bug-fix-coordinator.md`

Bug fix coordinator orchestrating diagnosis, fix generation, and regression testing.

**Configuration:**
```yaml
name: acc-bug-fix-coordinator
tools: Task, Read, Grep, Glob, Edit, Write, Bash
model: opus
# No skills - delegates to specialized agents
```

**Workflow:**
1. Parse input (text, file:line, stack trace, log file)
2. Task → `acc-bug-hunter` (diagnose bug category)
3. Task → `acc-bug-fixer` (generate minimal fix)
4. Task → `acc-test-generator` (create regression test)
5. Apply changes and run tests

**Meta-Instructions:**
- `-- focus on <area>` — Prioritize specific area
- `-- skip tests` — Don't generate regression test
- `-- dry-run` — Show fix without applying
- `-- verbose` — Detailed analysis output

---

## `acc-bug-fixer`

**Path:** `agents/acc-bug-fixer.md`

Bug fix specialist generating safe, minimal fixes using diagnosis from bug-hunter.

**Configuration:**
```yaml
name: acc-bug-fixer
tools: Read, Edit, Write, Grep, Glob
model: sonnet
skills:
  # New skills (5)
  - acc-bug-fix-knowledge
  - acc-bug-root-cause-finder
  - acc-bug-impact-analyzer
  - acc-generate-bug-fix
  - acc-bug-regression-preventer
  # Existing skills (6) - quality checks
  - acc-detect-code-smells
  - acc-detect-memory-issues
  - acc-analyze-solid-violations
  - acc-check-encapsulation
  - acc-check-side-effects
  - acc-check-immutability
```

**Skills:** 11 (5 new + 6 existing)

**Capabilities:**
- Root cause analysis (5 Whys, fault tree)
- Impact/blast radius analysis
- Fix templates for 9 bug categories
- Quality verification (SOLID, code smells, encapsulation)
- Regression prevention checklist

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Skills →](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
