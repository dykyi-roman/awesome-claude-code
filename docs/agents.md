# Agents

Subagents for specialized tasks. Agents are autonomous workers that handle complex, multi-step operations.

## Overview

### Coordinators (0-3 skills, delegate via Task tool)

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `acc-architecture-auditor` | Architecture audit coordinator | `/acc-audit-architecture` |
| `acc-pattern-auditor` | Design patterns audit coordinator | `/acc-audit-patterns`, `acc-architecture-auditor` (Task) |
| `acc-pattern-generator` | Design patterns generation coordinator | `/acc-generate-patterns`, `acc-architecture-auditor` (Task) |
| `acc-code-review-coordinator` | Code review coordinator (3 levels) | `/acc-code-review` |
| `acc-bug-fix-coordinator` | Bug fix coordinator (diagnose → fix → test) | `/acc-bug-fix` |
| `acc-refactor-coordinator` | Refactoring coordinator (analyze → prioritize → fix) | `/acc-refactor` |
| `acc-ci-coordinator` | CI/CD coordinator (setup, debug, optimize, audit) | `/acc-ci-*`, `/acc-audit-ci` |
| `acc-docker-coordinator` | Docker expert system coordinator (audit, generate) | `/acc-audit-docker`, `/acc-generate-docker` |
| `acc-explain-coordinator` | Code explanation coordinator (5 modes) | `/acc-explain` |

### Auditors (3-12 skills)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-structural-auditor` | Structural patterns analysis | 13 | `acc-architecture-auditor` (Task) |
| `acc-behavioral-auditor` | GoF Behavioral patterns analysis | 11 | `acc-pattern-auditor` (Task) |
| `acc-cqrs-auditor` | CQRS/ES/EDA patterns analysis | 8 | `acc-architecture-auditor`, `acc-pattern-auditor` (Task) |
| `acc-gof-structural-auditor` | GoF Structural patterns analysis | 7 | `acc-pattern-auditor` (Task) |
| `acc-integration-auditor` | Integration patterns analysis | 13 | `acc-architecture-auditor`, `acc-pattern-auditor` (Task) |
| `acc-stability-auditor` | Stability patterns analysis | 9 | `acc-pattern-auditor` (Task) |
| `acc-creational-auditor` | Creational patterns analysis | 7 | `acc-pattern-auditor` (Task) |
| `acc-ddd-auditor` | DDD compliance analysis | 8 | `/acc-audit-ddd` |
| `acc-psr-auditor` | PSR compliance analysis | 3 | `/acc-audit-psr` |
| `acc-documentation-auditor` | Audit documentation quality | 6 | `/acc-audit-documentation` |
| `acc-test-auditor` | Test quality analysis | 3 | `/acc-audit-test` |

### Reviewers (7-20 skills, code review specialists)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-bug-hunter` | Bug detection specialist | 9 | `acc-code-review-coordinator`, `acc-bug-fix-coordinator` (Task) |
| `acc-security-reviewer` | Security review specialist | 21 | `/acc-audit-security`, `acc-code-review-coordinator` (Task) |
| `acc-performance-reviewer` | Performance review specialist | 13 | `/acc-audit-performance`, `acc-code-review-coordinator` (Task) |
| `acc-readability-reviewer` | Readability review specialist | 9 | `acc-code-review-coordinator`, `acc-refactor-coordinator` (Task) |
| `acc-testability-reviewer` | Testability review specialist | 7 | `acc-code-review-coordinator`, `acc-refactor-coordinator` (Task) |

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
| `acc-behavioral-generator` | Generate behavioral patterns | 10 | `acc-pattern-generator` (Task) |
| `acc-gof-structural-generator` | Generate GoF structural patterns | 6 | `acc-pattern-generator` (Task) |
| `acc-creational-generator` | Generate creational patterns | 3 | `acc-pattern-generator` (Task) |
| `acc-integration-generator` | Generate integration patterns | 7 | `acc-pattern-generator` (Task) |
| `acc-psr-generator` | Generate PSR implementations | 14 | `/acc-generate-psr`, `acc-psr-auditor` (Skill) |
| `acc-documentation-writer` | Generate documentation | 9 | `/acc-generate-documentation` |
| `acc-diagram-designer` | Create Mermaid diagrams | 2 | `acc-documentation-writer` (Task) |
| `acc-test-generator` | Generate PHP tests | 6 | `/acc-generate-test` |

### CI/CD Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-pipeline-architect` | Pipeline design and structure | 4 | `acc-ci-coordinator` (Task) |
| `acc-static-analysis-agent` | PHPStan/Psalm/DEPTRAC config | 9 | `acc-ci-coordinator` (Task) |
| `acc-test-pipeline-agent` | PHPUnit/coverage setup | 5 | `acc-ci-coordinator` (Task) |
| `acc-ci-debugger` | Log analysis and diagnosis | 3 | `acc-ci-coordinator` (Task) |
| `acc-ci-fixer` | Fix generation and application | 6 | `acc-ci-coordinator`, `/acc-ci-fix` (Task) |
| `acc-pipeline-optimizer` | Caching and parallelization | 7 | `acc-ci-coordinator` (Task) |
| `acc-ci-security-agent` | Secrets and deps scanning | 4 | `acc-ci-coordinator` (Task) |
| `acc-docker-agent` | Dockerfile and layer optimization | 3 | `acc-ci-coordinator` (Task) |
| `acc-deployment-agent` | Deploy config, blue-green, canary | 6 | `acc-ci-coordinator` (Task) |

### Docker Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-docker-architect-agent` | Dockerfile architecture, multi-stage builds | 5 | `acc-docker-coordinator` (Task) |
| `acc-docker-image-builder` | Base images, PHP extensions | 5 | `acc-docker-coordinator` (Task) |
| `acc-docker-compose-agent` | Compose configuration, services | 6 | `acc-docker-coordinator` (Task) |
| `acc-docker-performance-agent` | Build/runtime optimization | 6 | `acc-docker-coordinator` (Task) |
| `acc-docker-security-agent` | Security audit, hardening | 6 | `acc-docker-coordinator` (Task) |
| `acc-docker-debugger-agent` | Error diagnosis, troubleshooting | 4 | `acc-docker-coordinator` (Task) |
| `acc-docker-production-agent` | Production readiness, health checks | 6 | `acc-docker-coordinator` (Task) |

### Code Explainer Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `acc-codebase-navigator` | Codebase structure scanning and pattern detection | 3 | `acc-explain-coordinator` (Task) |
| `acc-business-logic-analyst` | Business rules, processes, domain concepts extraction | 4 | `acc-explain-coordinator` (Task) |
| `acc-data-flow-analyst` | Request lifecycle, data transformation, async flow tracing | 3 | `acc-explain-coordinator` (Task) |

### Experts

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `acc-claude-code-expert` | Create Claude Code components | `/acc-generate-claude-component` |

## How Agents Work

1. **Invocation**: Commands invoke agents via Task tool or direct reference
2. **Skills Loading**: Agent loads skills from `skills:` frontmatter
3. **Execution**: Agent performs multi-step analysis or generation
4. **Delegation**: Agent may delegate subtasks to other agents via Task tool

## Progress Tracking (Coordinators)

Coordinator agents use TaskCreate/TaskUpdate for user visibility:

```
1. TaskCreate (all phases upfront)
   ├── Phase 1: "Analyze changes" — Analyzing changes...
   ├── Phase 2: "Run reviewers" — Running reviewers...
   └── Phase 3: "Generate report" — Generating report...

2. Execute with status updates:
   ├── TaskUpdate(taskId, status: in_progress)
   ├── ... execute phase ...
   └── TaskUpdate(taskId, status: completed)
```

**Coordinators with progress tracking:**
- `acc-code-review-coordinator` — 3 phases
- `acc-bug-fix-coordinator` — 3 phases
- `acc-refactor-coordinator` — 3 phases
- `acc-architecture-auditor` — 4 phases
- `acc-ci-coordinator` — 3 phases
- `acc-ddd-auditor` — 3 phases
- `acc-pattern-auditor` — 4 phases
- `acc-explain-coordinator` — 4 phases
- `acc-docker-coordinator` — 3 phases

**Specialist auditors with progress tracking:**
- `acc-security-reviewer` — 3 phases (Scan → Analyze → Report)
- `acc-performance-reviewer` — 3 phases (Scan → Analyze → Report)
- `acc-psr-auditor` — 3 phases (Scan → Analyze → Report)
- `acc-test-auditor` — 3 phases (Scan → Analyze → Report)
- `acc-documentation-auditor` — 3 phases (Scan → Analyze → Report)

See `acc-task-progress-knowledge` skill for guidelines.

---

## `acc-claude-code-expert`

**Path:** `agents/acc-claude-code-expert.md`

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

Behavioral patterns auditor for CQRS, Event Sourcing, EDA, and GoF behavioral patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento).

**Configuration:**
```yaml
name: acc-behavioral-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-cqrs-knowledge, acc-event-sourcing-knowledge, acc-eda-knowledge,
        acc-create-command, acc-create-query, acc-create-domain-event,
        acc-create-read-model, acc-create-strategy, acc-create-state,
        acc-create-chain-of-responsibility, acc-create-decorator,
        acc-create-null-object, acc-check-immutability,
        acc-create-template-method, acc-create-visitor,
        acc-create-iterator, acc-create-memento
```

**Skills:** 17 (3 knowledge + 14 generators/analyzers)

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

## `acc-gof-structural-auditor`

**Path:** `agents/acc-gof-structural-auditor.md`

GoF Structural patterns auditor for Adapter, Facade, Proxy, Composite, Bridge, and Flyweight.

**Configuration:**
```yaml
name: acc-gof-structural-auditor
tools: Read, Grep, Glob
model: sonnet
skills: acc-create-adapter, acc-create-facade, acc-create-proxy,
        acc-create-composite, acc-create-bridge, acc-create-flyweight
```

**Skills:** 6 (generators)

---

## `acc-gof-structural-generator`

**Path:** `agents/acc-gof-structural-generator.md`

Generates GoF structural patterns (Adapter, Facade, Proxy, Composite, Bridge, Flyweight).

**Configuration:**
```yaml
name: acc-gof-structural-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-create-adapter, acc-create-facade, acc-create-proxy,
        acc-create-composite, acc-create-bridge, acc-create-flyweight
```

**Skills:** 6

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

**Skills:** 2 (knowledge only, delegates to 5 specialized auditors via Task)

**Delegation:**
- `acc-stability-auditor` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc-behavioral-auditor` — Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento
- `acc-gof-structural-auditor` — Adapter, Facade, Proxy, Composite, Bridge, Flyweight
- `acc-creational-auditor` — Builder, Object Pool, Factory
- `acc-integration-auditor` — Outbox, Saga, ADR

---

## `acc-pattern-generator`

**Path:** `agents/acc-pattern-generator.md`

Design patterns generation coordinator. Orchestrates stability, behavioral, GoF structural, creational, and integration generators.

**Configuration:**
```yaml
name: acc-pattern-generator
tools: Read, Write, Glob, Grep, Edit, Task
model: opus
skills: acc-adr-knowledge
```

**Skills:** 1 (delegates to 5 specialized generators via Task)

**Delegation:**
- `acc-stability-generator` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc-behavioral-generator` — Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento
- `acc-gof-structural-generator` — Adapter, Facade, Proxy, Composite, Bridge, Flyweight
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

Generates behavioral patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento).

**Configuration:**
```yaml
name: acc-behavioral-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: acc-create-strategy, acc-create-state, acc-create-chain-of-responsibility,
        acc-create-decorator, acc-create-null-object, acc-create-policy,
        acc-create-template-method, acc-create-visitor,
        acc-create-iterator, acc-create-memento
```

**Skills:** 10

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
        acc-find-type-issues, acc-check-sql-injection, acc-find-infinite-loops
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
skills: acc-bug-fix-knowledge, acc-bug-root-cause-finder, acc-bug-impact-analyzer,
        acc-generate-bug-fix, acc-bug-regression-preventer,
        acc-detect-code-smells, acc-detect-memory-issues, acc-analyze-solid-violations,
        acc-check-encapsulation, acc-check-side-effects, acc-check-immutability
```

**Skills:** 11 (5 new + 6 existing)

**Capabilities:**
- Root cause analysis (5 Whys, fault tree)
- Impact/blast radius analysis
- Fix templates for 9 bug categories
- Quality verification (SOLID, code smells, encapsulation)
- Regression prevention checklist

---

## `acc-ci-coordinator`

**Path:** `agents/acc-ci-coordinator.md`

CI/CD coordinator orchestrating pipeline setup, fixing, optimization, and auditing.

**Configuration:**
```yaml
name: acc-ci-coordinator
tools: Read, Write, Edit, Grep, Glob, Bash, Task
model: opus
skills: acc-ci-pipeline-knowledge
```

**Operations:**
- **SETUP**: Create new CI pipeline from scratch
- **FIX**: Diagnose and fix pipeline failures with interactive approval
- **OPTIMIZE**: Improve pipeline performance
- **AUDIT**: Comprehensive CI/CD audit

**Delegation:**
- `acc-pipeline-architect` — Workflow structure
- `acc-static-analysis-agent` — PHPStan, Psalm, DEPTRAC configs
- `acc-test-pipeline-agent` — PHPUnit, coverage setup
- `acc-ci-debugger` — Log analysis, failure diagnosis
- `acc-pipeline-optimizer` — Caching, parallelization
- `acc-ci-security-agent` — Secrets, permissions, deps
- `acc-docker-agent` — Dockerfile optimization
- `acc-deployment-agent` — Deployment strategies

---

## `acc-pipeline-architect`

**Path:** `agents/acc-pipeline-architect.md`

Pipeline design specialist for GitHub Actions and GitLab CI.

**Configuration:**
```yaml
name: acc-pipeline-architect
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-ci-pipeline-knowledge, acc-create-github-actions, acc-create-gitlab-ci, acc-detect-ci-antipatterns
```

**Skills:** 4

---

## `acc-static-analysis-agent`

**Path:** `agents/acc-static-analysis-agent.md`

Static analysis configuration specialist.

**Configuration:**
```yaml
name: acc-static-analysis-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-ci-tools-knowledge, acc-create-phpstan-config, acc-create-psalm-config,
        acc-create-deptrac-config, acc-create-rector-config, acc-psr-coding-style-knowledge,
        acc-check-code-style, acc-analyze-solid-violations, acc-detect-code-smells
```

**Skills:** 9 (4 new + 5 reused)

---

## `acc-test-pipeline-agent`

**Path:** `agents/acc-test-pipeline-agent.md`

Test pipeline configuration specialist.

**Configuration:**
```yaml
name: acc-test-pipeline-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-testing-knowledge, acc-analyze-test-coverage, acc-detect-test-smells,
        acc-check-test-quality, acc-ci-pipeline-knowledge
```

**Skills:** 5 (4 reused + 1 new)

---

## `acc-ci-debugger`

**Path:** `agents/acc-ci-debugger.md`

CI/CD log analysis and failure diagnosis specialist.

**Configuration:**
```yaml
name: acc-ci-debugger
tools: Read, Grep, Glob, Bash
model: sonnet
skills: acc-analyze-ci-logs, acc-ci-pipeline-knowledge, acc-ci-tools-knowledge
```

**Skills:** 3

---

## `acc-ci-fixer`

**Path:** `agents/acc-ci-fixer.md`

CI fix generation and application specialist. Generates minimal, safe fixes for CI configuration issues.

**Configuration:**
```yaml
name: acc-ci-fixer
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-generate-ci-fix, acc-ci-pipeline-knowledge, acc-ci-tools-knowledge,
        acc-create-github-actions, acc-create-gitlab-ci, acc-detect-ci-antipatterns
```

**Skills:** 6 (1 new + 5 reused)

**Capabilities:**
- Receives diagnosis from `acc-ci-debugger`
- Selects appropriate fix pattern
- Generates minimal, safe changes
- Applies fixes to CI config files
- Provides rollback instructions
- Supports 10+ issue types (memory, composer, timeout, etc.)

---

## `acc-pipeline-optimizer`

**Path:** `agents/acc-pipeline-optimizer.md`

Pipeline performance optimization specialist.

**Configuration:**
```yaml
name: acc-pipeline-optimizer
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-ci-pipeline-knowledge, acc-estimate-pipeline-time, acc-detect-ci-antipatterns,
        acc-optimize-docker-layers, acc-analyze-ci-config, acc-detect-memory-issues,
        acc-check-caching-strategy
```

**Skills:** 7 (2 reused + 5 new)

---

## `acc-ci-security-agent`

**Path:** `agents/acc-ci-security-agent.md`

CI/CD security specialist for secrets, permissions, and dependency scanning.

**Configuration:**
```yaml
name: acc-ci-security-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: acc-ci-pipeline-knowledge, acc-check-sensitive-data, acc-check-dependency-vulnerabilities,
        acc-check-crypto-usage
```

**Skills:** 4 (3 reused + 1 new)

---

## `acc-docker-agent`

**Path:** `agents/acc-docker-agent.md`

Docker configuration and optimization specialist.

**Configuration:**
```yaml
name: acc-docker-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-create-dockerfile-ci, acc-optimize-docker-layers, acc-ci-pipeline-knowledge
```

**Skills:** 3

---

## `acc-deployment-agent`

**Path:** `agents/acc-deployment-agent.md`

Deployment configuration specialist for blue-green, canary, and rolling strategies.

**Configuration:**
```yaml
name: acc-deployment-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-deployment-knowledge, acc-create-deploy-strategy, acc-create-feature-flags,
        acc-ci-pipeline-knowledge, acc-create-github-actions, acc-create-gitlab-ci
```

**Skills:** 6

---

## `acc-docker-coordinator`

**Path:** `agents/acc-docker-coordinator.md`

Docker expert system coordinator. Orchestrates auditing, generation, and optimization.

**Configuration:**
```yaml
name: acc-docker-coordinator
tools: Read, Grep, Glob, Bash, Task, TaskCreate, TaskUpdate
model: opus
skills: acc-docker-knowledge, acc-task-progress-knowledge
```

**Operations:**
- **AUDIT**: Comprehensive Docker configuration audit
- **GENERATE**: Generate Docker components

**Delegation:**
- `acc-docker-architect-agent` — Dockerfile architecture
- `acc-docker-image-builder` — Base images, extensions
- `acc-docker-compose-agent` — Compose configuration
- `acc-docker-performance-agent` — Performance optimization
- `acc-docker-security-agent` — Security audit
- `acc-docker-debugger-agent` — Error diagnosis
- `acc-docker-production-agent` — Production readiness

---

## `acc-docker-architect-agent`

**Path:** `agents/acc-docker-architect-agent.md`

Dockerfile architecture specialist for multi-stage builds, layer optimization, and BuildKit features.

**Configuration:**
```yaml
name: acc-docker-architect-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-docker-knowledge, acc-docker-multistage-knowledge, acc-docker-buildkit-knowledge,
        acc-create-dockerfile-production, acc-create-dockerfile-dev
```

**Skills:** 5

---

## `acc-docker-image-builder`

**Path:** `agents/acc-docker-image-builder.md`

Base image selection and PHP extension installation specialist.

**Configuration:**
```yaml
name: acc-docker-image-builder
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-docker-base-images-knowledge, acc-docker-php-extensions-knowledge,
        acc-create-dockerfile-production, acc-create-dockerfile-dev, acc-create-dockerignore
```

**Skills:** 5

---

## `acc-docker-compose-agent`

**Path:** `agents/acc-docker-compose-agent.md`

Docker Compose configuration specialist for PHP stacks.

**Configuration:**
```yaml
name: acc-docker-compose-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-docker-compose-knowledge, acc-docker-networking-knowledge,
        acc-create-docker-compose-dev, acc-create-docker-compose-production,
        acc-check-docker-compose-config, acc-create-docker-env-template
```

**Skills:** 6

---

## `acc-docker-performance-agent`

**Path:** `agents/acc-docker-performance-agent.md`

Docker build and runtime performance optimization specialist.

**Configuration:**
```yaml
name: acc-docker-performance-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-optimize-docker-layers, acc-optimize-docker-build-time, acc-optimize-docker-image-size,
        acc-optimize-docker-php-fpm, acc-optimize-docker-opcache, acc-optimize-docker-startup
```

**Skills:** 6

---

## `acc-docker-security-agent`

**Path:** `agents/acc-docker-security-agent.md`

Docker security audit and hardening specialist.

**Configuration:**
```yaml
name: acc-docker-security-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: acc-docker-security-knowledge, acc-docker-scanning-knowledge,
        acc-check-docker-security, acc-check-docker-secrets,
        acc-check-docker-user-permissions, acc-detect-docker-antipatterns
```

**Skills:** 6

---

## `acc-docker-debugger-agent`

**Path:** `agents/acc-docker-debugger-agent.md`

Docker error diagnosis and troubleshooting specialist.

**Configuration:**
```yaml
name: acc-docker-debugger-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: acc-docker-troubleshooting-knowledge, acc-analyze-docker-build-errors,
        acc-analyze-docker-runtime-errors, acc-analyze-docker-image-size
```

**Skills:** 4

---

## `acc-docker-production-agent`

**Path:** `agents/acc-docker-production-agent.md`

Docker production readiness specialist for health checks, graceful shutdown, and logging.

**Configuration:**
```yaml
name: acc-docker-production-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: acc-docker-production-knowledge, acc-docker-orchestration-knowledge,
        acc-check-docker-production-readiness, acc-check-docker-healthcheck,
        acc-create-docker-healthcheck, acc-create-docker-entrypoint
```

**Skills:** 6

---

## `acc-explain-coordinator`

**Path:** `agents/acc-explain-coordinator.md`

Code explanation coordinator. Orchestrates codebase navigation, business logic extraction, data flow tracing, visualization, and documentation suggestion. Supports 5 modes.

**Configuration:**
```yaml
name: acc-explain-coordinator
tools: Read, Grep, Glob, Bash, Task, TaskCreate, TaskUpdate
model: opus
skills: acc-explain-output-template, acc-task-progress-knowledge
```

**Workflow (4 phases):**
1. **Navigate** — Task → `acc-codebase-navigator` (scan structure, entry points, patterns)
2. **Analyze** — Task → `acc-business-logic-analyst` + `acc-data-flow-analyst` (+ auditors for deep/onboarding)
3. **Visualize** — Task → `acc-diagram-designer` + `acc-documentation-writer` (deep/onboarding/business)
4. **Present** — Aggregate results, format output, suggest documentation

**Modes:** quick (file), deep (module), onboarding (project), business (non-technical), qa (interactive)

---

## `acc-codebase-navigator`

**Path:** `agents/acc-codebase-navigator.md`

Codebase navigation specialist. Scans directory structure, identifies architectural layers, detects framework and patterns, finds entry points.

**Configuration:**
```yaml
name: acc-codebase-navigator
tools: Read, Grep, Glob
model: sonnet
skills: acc-scan-codebase-structure, acc-identify-entry-points, acc-detect-architecture-pattern
```

**Skills:** 3 (analyzers)

---

## `acc-business-logic-analyst`

**Path:** `agents/acc-business-logic-analyst.md`

Business logic analysis specialist. Extracts business rules, explains business processes in natural language, maps domain concepts and ubiquitous language, detects state machines.

**Configuration:**
```yaml
name: acc-business-logic-analyst
tools: Read, Grep, Glob
model: sonnet
skills: acc-extract-business-rules, acc-explain-business-process, acc-extract-domain-concepts, acc-extract-state-machine
```

**Skills:** 4 (analyzers)

---

## `acc-data-flow-analyst`

**Path:** `agents/acc-data-flow-analyst.md`

Data flow analysis specialist. Traces request lifecycles through all layers, maps data transformations between DTOs/Commands/Entities/Responses, identifies async communication flows.

**Configuration:**
```yaml
name: acc-data-flow-analyst
tools: Read, Grep, Glob
model: sonnet
skills: acc-trace-request-lifecycle, acc-trace-data-transformation, acc-map-async-flows
```

**Skills:** 3 (analyzers)

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Skills →](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
