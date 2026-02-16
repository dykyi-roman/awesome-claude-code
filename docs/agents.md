# Agents

Subagents for specialized tasks. Agents are autonomous workers that handle complex, multi-step operations.

## Overview

### Coordinators (0-3 skills, delegate via Task tool)

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `architecture-auditor` | Architecture audit coordinator | `/acc:audit-architecture` |
| `pattern-auditor` | Design patterns audit coordinator | `/acc:audit-patterns`, `acc:architecture-auditor` (Task) |
| `pattern-generator` | Design patterns generation coordinator | `/acc:generate-patterns`, `acc:architecture-auditor` (Task) |
| `code-review-coordinator` | Code review coordinator (3 levels) | `/acc:code-review` |
| `bug-fix-coordinator` | Bug fix coordinator (diagnose → fix → test) | `/acc:bug-fix` |
| `refactor-coordinator` | Refactoring coordinator (analyze → prioritize → fix) | `/acc:refactor` |
| `ci-coordinator` | CI/CD coordinator (setup, debug, optimize, audit) | `/acc:ci-*`, `/acc:audit-ci` |
| `docker-coordinator` | Docker expert system coordinator (audit, generate) | `/acc:audit-docker`, `/acc:generate-docker` |
| `explain-coordinator` | Code explanation coordinator (5 modes) | `/acc:explain` |

### Auditors (3-12 skills)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `structural-auditor` | Structural patterns analysis | 13 | `acc:architecture-auditor` (Task) |
| `behavioral-auditor` | GoF Behavioral patterns analysis | 11 | `acc:pattern-auditor` (Task) |
| `cqrs-auditor` | CQRS/ES/EDA patterns analysis | 8 | `acc:architecture-auditor`, `acc:pattern-auditor` (Task) |
| `gof-structural-auditor` | GoF Structural patterns analysis | 7 | `acc:pattern-auditor` (Task) |
| `integration-auditor` | Integration patterns analysis | 13 | `acc:architecture-auditor`, `acc:pattern-auditor` (Task) |
| `stability-auditor` | Stability patterns analysis | 9 | `acc:pattern-auditor` (Task) |
| `creational-auditor` | Creational patterns analysis | 7 | `acc:pattern-auditor` (Task) |
| `ddd-auditor` | DDD compliance analysis | 8 | `/acc:audit-ddd` |
| `psr-auditor` | PSR compliance analysis | 3 | `/acc:audit-psr` |
| `documentation-auditor` | Audit documentation quality | 7 | `/acc:audit-documentation` |
| `test-auditor` | Test quality analysis | 3 | `/acc:audit-test` |

### Reviewers (5-15 skills, code review specialists)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `bug-hunter` | Bug detection specialist | 11 | `acc:code-review-coordinator`, `acc:bug-fix-coordinator` (Task) |
| `security-reviewer` | Security review coordinator | 1 | `/acc:audit-security`, `acc:code-review-coordinator` (Task) |
| `injection-reviewer` | Injection vulnerability specialist | 7 | `acc:security-reviewer` (Task) |
| `auth-reviewer` | Auth & access control specialist | 6 | `acc:security-reviewer` (Task) |
| `data-security-reviewer` | Data & crypto security specialist | 6 | `acc:security-reviewer` (Task) |
| `design-security-reviewer` | Design & component security specialist | 5 | `acc:security-reviewer` (Task) |
| `performance-reviewer` | Performance review specialist | 15 | `/acc:audit-performance`, `acc:code-review-coordinator` (Task) |
| `readability-reviewer` | Readability review specialist | 9 | `acc:code-review-coordinator`, `acc:refactor-coordinator` (Task) |
| `testability-reviewer` | Testability review specialist | 7 | `acc:code-review-coordinator`, `acc:refactor-coordinator` (Task) |

### Bug Fix Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `bug-fixer` | Bug fix generator | 12 | `acc:bug-fix-coordinator` (Task) |

### Generators (3-14 skills)

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `architecture-generator` | Generate architecture components | 7 | `acc:architecture-auditor` (Task) |
| `ddd-generator` | Generate DDD building blocks | 12 | `acc:ddd-auditor` (Task) |
| `cqrs-generator` | Generate CQRS/ES components | 8 | `/acc:generate-ddd`, `acc:architecture-generator` (Task) |
| `stability-generator` | Generate stability patterns | 5 | `acc:pattern-generator` (Task) |
| `behavioral-generator` | Generate behavioral patterns | 10 | `acc:pattern-generator` (Task) |
| `gof-structural-generator` | Generate GoF structural patterns | 6 | `acc:pattern-generator` (Task) |
| `creational-generator` | Generate creational patterns | 3 | `acc:pattern-generator` (Task) |
| `integration-generator` | Generate integration patterns | 8 | `acc:pattern-generator` (Task) |
| `psr-generator` | Generate PSR implementations | 14 | `/acc:generate-psr`, `acc:psr-auditor` (Skill) |
| `documentation-writer` | Generate documentation | 9 | `/acc:generate-documentation` |
| `diagram-designer` | Create Mermaid diagrams | 2 | `acc:documentation-writer` (Task) |
| `test-generator` | Generate PHP tests | 6 | `/acc:generate-test` |

### CI/CD Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `pipeline-architect` | Pipeline design and structure | 4 | `acc:ci-coordinator` (Task) |
| `static-analysis-agent` | PHPStan/Psalm/DEPTRAC config | 9 | `acc:ci-coordinator` (Task) |
| `test-pipeline-agent` | PHPUnit/coverage setup | 5 | `acc:ci-coordinator` (Task) |
| `ci-debugger` | Log analysis and diagnosis | 4 | `acc:ci-coordinator` (Task) |
| `ci-fixer` | Fix generation and application | 6 | `acc:ci-coordinator`, `/acc:ci-fix` (Task) |
| `pipeline-optimizer` | Caching and parallelization | 7 | `acc:ci-coordinator` (Task) |
| `ci-security-agent` | Secrets and deps scanning | 4 | `acc:ci-coordinator` (Task) |
| `docker-agent` | Dockerfile and layer optimization | 3 | `acc:ci-coordinator` (Task) |
| `deployment-agent` | Deploy config, blue-green, canary | 6 | `acc:ci-coordinator` (Task) |

### Docker Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `docker-architect-agent` | Dockerfile architecture, multi-stage builds | 5 | `acc:docker-coordinator` (Task) |
| `docker-image-builder` | Base images, PHP extensions | 5 | `acc:docker-coordinator` (Task) |
| `docker-compose-agent` | Compose configuration, services | 6 | `acc:docker-coordinator` (Task) |
| `docker-performance-agent` | Build/runtime optimization | 6 | `acc:docker-coordinator` (Task) |
| `docker-security-agent` | Security audit, hardening | 6 | `acc:docker-coordinator` (Task) |
| `docker-debugger-agent` | Error diagnosis, troubleshooting | 6 | `acc:docker-coordinator` (Task) |
| `docker-production-agent` | Production readiness, health checks | 6 | `acc:docker-coordinator` (Task) |

### Code Explainer Specialists

| Agent | Purpose | Skills | Invoked By |
|-------|---------|--------|------------|
| `codebase-navigator` | Codebase structure scanning and pattern detection | 3 | `acc:explain-coordinator` (Task) |
| `business-logic-analyst` | Business rules, processes, domain concepts extraction | 4 | `acc:explain-coordinator` (Task) |
| `data-flow-analyst` | Request lifecycle, data transformation, async flow tracing | 4 | `acc:explain-coordinator` (Task) |

### Experts

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `claude-code-expert` | Create Claude Code components | `/acc:generate-claude-component` |

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
- `code-review-coordinator` — 3 phases
- `bug-fix-coordinator` — 3 phases
- `refactor-coordinator` — 3 phases
- `architecture-auditor` — 4 phases
- `ci-coordinator` — 3 phases
- `ddd-auditor` — 3 phases
- `pattern-auditor` — 4 phases
- `explain-coordinator` — 4 phases
- `docker-coordinator` — 3 phases

**Specialist auditors with progress tracking:**
- `security-reviewer` — 3 phases (Scan → Analyze → Report)
- `performance-reviewer` — 3 phases (Scan → Analyze → Report)
- `psr-auditor` — 3 phases (Scan → Analyze → Report)
- `test-auditor` — 3 phases (Scan → Analyze → Report)
- `documentation-auditor` — 3 phases (Scan → Analyze → Report)

See `task-progress-knowledge` skill for guidelines.

---

## `claude-code-expert`

**Path:** `agents/claude-code-expert.md`

Expert in creating Claude Code commands, agents, and skills.

**Configuration:**
```yaml
name: claude-code-expert
tools: Read, Write, Edit, Bash, Grep, Glob
model: opus
skills: claude-code-knowledge
```

---

## `architecture-auditor`

**Path:** `agents/architecture-auditor.md`

Architecture audit coordinator. Orchestrates three specialized auditors for comprehensive reviews.

**Configuration:**
```yaml
name: architecture-auditor
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

## `structural-auditor`

**Path:** `agents/structural-auditor.md`

Structural architecture auditor for DDD, Clean Architecture, Hexagonal, Layered, SOLID, GRASP.

**Configuration:**
```yaml
name: structural-auditor
tools: Read, Grep, Glob
model: sonnet
skills: ddd-knowledge, clean-arch-knowledge, hexagonal-knowledge,
        layer-arch-knowledge, solid-knowledge, grasp-knowledge,
        analyze-solid-violations, detect-code-smells, check-bounded-contexts,
        check-immutability, check-leaky-abstractions, check-encapsulation
```

**Skills:** 12 (6 knowledge + 6 analyzer)

---

## `behavioral-auditor`

**Path:** `agents/behavioral-auditor.md`

GoF Behavioral patterns auditor for Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, and Memento patterns.

**Configuration:**
```yaml
name: behavioral-auditor
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: opus
skills: create-strategy, create-state, create-chain-of-responsibility,
        create-decorator, create-null-object, check-immutability,
        create-template-method, create-visitor,
        create-iterator, create-memento, task-progress-knowledge
```

**Skills:** 11 (9 generators + 1 analyzer + 1 progress)

---

## `integration-auditor`

**Path:** `agents/integration-auditor.md`

Integration patterns auditor for Outbox, Saga, Stability, and ADR.

**Configuration:**
```yaml
name: integration-auditor
tools: Read, Grep, Glob
model: sonnet
skills: outbox-pattern-knowledge, saga-pattern-knowledge,
        stability-patterns-knowledge, adr-knowledge,
        create-outbox-pattern, create-saga-pattern,
        create-circuit-breaker, create-retry-pattern,
        create-rate-limiter, create-bulkhead,
        create-action, create-responder
```

**Skills:** 12 (4 knowledge + 8 generators)

---

## `stability-auditor`

**Path:** `agents/stability-auditor.md`

Stability patterns auditor for Circuit Breaker, Retry, Rate Limiter, and Bulkhead.

**Configuration:**
```yaml
name: stability-auditor
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: sonnet
skills: stability-patterns-knowledge, create-circuit-breaker,
        create-retry-pattern, create-rate-limiter, create-bulkhead,
        check-timeout-strategy, check-cascading-failures,
        check-fallback-strategy, task-progress-knowledge
```

**Skills:** 9 (1 knowledge + 4 generators + 3 analyzers + 1 progress)

---

## `gof-structural-auditor`

**Path:** `agents/gof-structural-auditor.md`

GoF Structural patterns auditor for Adapter, Facade, Proxy, Composite, Bridge, and Flyweight.

**Configuration:**
```yaml
name: gof-structural-auditor
tools: Read, Grep, Glob
model: sonnet
skills: create-adapter, create-facade, create-proxy,
        create-composite, create-bridge, create-flyweight
```

**Skills:** 6 (generators)

---

## `gof-structural-generator`

**Path:** `agents/gof-structural-generator.md`

Generates GoF structural patterns (Adapter, Facade, Proxy, Composite, Bridge, Flyweight).

**Configuration:**
```yaml
name: gof-structural-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: create-adapter, create-facade, create-proxy,
        create-composite, create-bridge, create-flyweight
```

**Skills:** 6

---

## `creational-auditor`

**Path:** `agents/creational-auditor.md`

Creational patterns auditor for Builder, Object Pool, and Factory patterns.

**Configuration:**
```yaml
name: creational-auditor
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: opus
skills: create-builder, create-object-pool, create-factory,
        check-singleton-antipattern, check-abstract-factory,
        create-prototype, task-progress-knowledge
```

**Skills:** 7 (4 generators + 2 analyzers + 1 progress)

---

## `ddd-auditor`

**Path:** `agents/ddd-auditor.md`

Specialized DDD compliance auditor.

**Configuration:**
```yaml
name: ddd-auditor
tools: Read, Bash, Grep, Glob, Task, TaskCreate, TaskUpdate
model: opus
skills: ddd-knowledge, solid-knowledge, grasp-knowledge,
        check-bounded-contexts, task-progress-knowledge,
        check-aggregate-consistency, check-cqrs-alignment,
        check-context-communication
```

**Skills:** 8 (3 knowledge + 4 analyzers + 1 progress, generation delegated to `acc:ddd-generator` via Task)

---

## `ddd-generator`

**Path:** `agents/ddd-generator.md`

Creates DDD building blocks (Domain + Application layers).

**Configuration:**
```yaml
name: ddd-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: ddd-knowledge, create-value-object, create-entity,
        create-aggregate, create-domain-event, create-repository,
        create-domain-service, create-factory, create-specification,
        create-dto, create-anti-corruption-layer, create-use-case
```

**Skills:** 12 (1 knowledge + 11 generators)

---

## `cqrs-generator`

**Path:** `agents/cqrs-generator.md`

Creates CQRS/ES components (Commands, Queries, Use Cases, Event Stores, Snapshots, Read Models).

**Configuration:**
```yaml
name: cqrs-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: cqrs-knowledge, event-sourcing-knowledge,
        create-command, create-query, create-use-case,
        create-event-store, create-snapshot, create-read-model
```

**Skills:** 8 (2 knowledge + 6 generators)

---

## `pattern-auditor`

**Path:** `agents/pattern-auditor.md`

Design patterns audit coordinator. Orchestrates stability, behavioral, creational, and integration auditors.

**Configuration:**
```yaml
name: pattern-auditor
tools: Read, Grep, Glob, Task
model: opus
skills: solid-knowledge, grasp-knowledge
```

**Skills:** 2 (knowledge only, delegates to 5 specialized auditors via Task)

**Delegation:**
- `acc:stability-auditor` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc:behavioral-auditor` — Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento
- `acc:gof-structural-auditor` — Adapter, Facade, Proxy, Composite, Bridge, Flyweight
- `acc:creational-auditor` — Builder, Object Pool, Factory
- `acc:integration-auditor` — Outbox, Saga, ADR

---

## `pattern-generator`

**Path:** `agents/pattern-generator.md`

Design patterns generation coordinator. Orchestrates stability, behavioral, GoF structural, creational, and integration generators.

**Configuration:**
```yaml
name: pattern-generator
tools: Read, Write, Glob, Grep, Edit, Task
model: opus
skills: adr-knowledge
```

**Skills:** 1 (delegates to 5 specialized generators via Task)

**Delegation:**
- `acc:stability-generator` — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- `acc:behavioral-generator` — Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento
- `acc:gof-structural-generator` — Adapter, Facade, Proxy, Composite, Bridge, Flyweight
- `acc:creational-generator` — Builder, Object Pool, Factory
- `acc:integration-generator` — Outbox, Saga, Action, Responder, Correlation Context

---

## `stability-generator`

**Path:** `agents/stability-generator.md`

Generates stability patterns (Circuit Breaker, Retry, Rate Limiter, Bulkhead).

**Configuration:**
```yaml
name: stability-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: stability-patterns-knowledge, create-circuit-breaker,
        create-retry-pattern, create-rate-limiter, create-bulkhead
```

**Skills:** 5

---

## `behavioral-generator`

**Path:** `agents/behavioral-generator.md`

Generates behavioral patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento).

**Configuration:**
```yaml
name: behavioral-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: create-strategy, create-state, create-chain-of-responsibility,
        create-decorator, create-null-object, create-policy,
        create-template-method, create-visitor,
        create-iterator, create-memento
```

**Skills:** 10

---

## `creational-generator`

**Path:** `agents/creational-generator.md`

Generates creational patterns (Builder, Object Pool, Factory).

**Configuration:**
```yaml
name: creational-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: create-builder, create-object-pool, create-factory
```

**Skills:** 3

---

## `integration-generator`

**Path:** `agents/integration-generator.md`

Generates integration patterns (Outbox, Saga, Action, Responder, Correlation Context).

**Configuration:**
```yaml
name: integration-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: outbox-pattern-knowledge, saga-pattern-knowledge, adr-knowledge,
        create-outbox-pattern, create-saga-pattern,
        create-action, create-responder, create-correlation-context
```

**Skills:** 8

---

## `architecture-generator`

**Path:** `agents/architecture-generator.md`

Meta-generator coordinating DDD and integration pattern generation for bounded contexts and complex structures.

**Configuration:**
```yaml
name: architecture-generator
tools: Read, Write, Glob, Grep, Edit, Task
model: opus
skills: ddd-knowledge, cqrs-knowledge, clean-arch-knowledge,
        eda-knowledge, outbox-pattern-knowledge, saga-pattern-knowledge,
        stability-patterns-knowledge
```

**Capabilities:**
- Direct generation: Value Objects, Entities, Aggregates, Commands, Queries, DTOs
- Delegated generation: Complex DDD structures via `acc:ddd-generator`, CQRS/ES via `acc:cqrs-generator`, Outbox/Saga via `acc:pattern-generator`
- Bounded context scaffolding
- CQRS + Event Sourcing setup
- Full feature vertical slices

---

## `psr-auditor`

**Path:** `agents/psr-auditor.md`

PSR compliance auditor for PHP projects. Analyzes coding standards and interface implementations.

**Configuration:**
```yaml
name: psr-auditor
tools: Read, Bash, Grep, Glob
model: opus
skills: psr-coding-style-knowledge, psr-autoloading-knowledge, psr-overview-knowledge
```

**Analysis Phases:**
1. Project structure discovery
2. PSR-1/PSR-12 coding style analysis
3. PSR-4 autoloading verification
4. PSR interface detection
5. Report generation with skill recommendations

---

## `psr-generator`

**Path:** `agents/psr-generator.md`

Creates PSR-compliant PHP components.

**Configuration:**
```yaml
name: psr-generator
tools: Read, Write, Glob, Grep, Edit
model: sonnet
skills: psr-overview-knowledge, psr-coding-style-knowledge, psr-autoloading-knowledge,
        create-psr3-logger, create-psr6-cache, create-psr7-http-message,
        create-psr11-container, create-psr13-link, create-psr14-event-dispatcher,
        create-psr15-middleware, create-psr16-simple-cache, create-psr17-http-factory,
        create-psr18-http-client, create-psr20-clock
```

---

## `documentation-writer`

**Path:** `agents/documentation-writer.md`

Technical documentation writer for PHP projects.

**Configuration:**
```yaml
name: documentation-writer
tools: Read, Write, Edit, Glob, Grep
model: opus
skills: documentation-knowledge, readme-template, architecture-doc-template,
        adr-template, api-doc-template, getting-started-template,
        troubleshooting-template, code-examples-template, changelog-template
```

---

## `documentation-auditor`

**Path:** `agents/documentation-auditor.md`

Documentation quality auditor.

**Configuration:**
```yaml
name: documentation-auditor
tools: Read, Glob, Grep, Bash, TaskCreate, TaskUpdate
model: opus
skills: documentation-qa-knowledge, documentation-knowledge, claude-code-knowledge,
        check-doc-links, check-doc-examples, check-version-consistency,
        task-progress-knowledge
```

---

## `diagram-designer`

**Path:** `agents/diagram-designer.md`

Diagram designer for technical documentation.

**Configuration:**
```yaml
name: diagram-designer
tools: Read, Write, Edit, Glob, Grep
model: opus
skills: diagram-knowledge, mermaid-template
```

---

## `test-auditor`

**Path:** `agents/test-auditor.md`

Test quality auditor for PHP projects.

**Configuration:**
```yaml
name: test-auditor
tools: Read, Bash, Grep, Glob
model: opus
skills: testing-knowledge, analyze-test-coverage, detect-test-smells
```

**Analysis Phases:**
1. Project discovery (framework, PHPUnit/Pest)
2. Coverage analysis (untested classes, methods, branches)
3. Test smell detection (15 antipatterns)
4. Quality metrics (naming, isolation)
5. Report generation with skill recommendations

---

## `test-generator`

**Path:** `agents/test-generator.md`

Test generator for DDD/CQRS PHP projects.

**Configuration:**
```yaml
name: test-generator
tools: Read, Write, Glob, Grep
model: opus
skills: testing-knowledge, create-unit-test, create-integration-test,
        create-test-builder, create-mock-repository, create-test-double
```

**Generation Process:**
1. Analyze source code (class type, dependencies)
2. Classify test type (unit/integration)
3. Prepare infrastructure (builders, fakes)
4. Generate tests using appropriate skill
5. Verify quality rules compliance

---

---

## `code-review-coordinator`

**Path:** `agents/code-review-coordinator.md`

Code review coordinator orchestrating multi-level reviews (low/medium/high) with git diff analysis.

**Configuration:**
```yaml
name: code-review-coordinator
tools: Read, Grep, Glob, Bash, Task
model: opus
skills: analyze-solid-violations, detect-code-smells, check-encapsulation
```

**Review Levels:**
- **LOW**: PSR + Tests + Encapsulation + Code Smells
- **MEDIUM**: LOW + Bugs + Readability + SOLID
- **HIGH**: MEDIUM + Security + Performance + Testability + DDD + Architecture

---

## `bug-hunter`

**Path:** `agents/bug-hunter.md`

Bug detection specialist for code review.

**Configuration:**
```yaml
name: bug-hunter
tools: Read, Grep, Glob
model: sonnet
skills: find-logic-errors, find-null-pointer-issues, find-boundary-issues,
        find-race-conditions, find-resource-leaks, find-exception-issues,
        find-type-issues, check-sql-injection, find-infinite-loops,
        discover-project-logs, analyze-php-logs
```

**Skills:** 11 (bug detection + log analysis)

---

## `security-reviewer`

**Path:** `agents/security-reviewer.md`

Security review coordinator. Orchestrates 4 specialized security reviewers covering OWASP Top 10.

**Configuration:**
```yaml
name: security-reviewer
tools: Read, Grep, Glob, Task, TaskCreate, TaskUpdate
model: opus
skills: task-progress-knowledge
```

**Skills:** 1 (delegates to 4 specialized agents via Task)

**Delegation:**
- `acc:injection-reviewer` — SQL injection, command injection, SSRF, XXE, path traversal, deserialization (A03, A10, A08)
- `acc:auth-reviewer` — Authentication, authorization, CSRF, mass assignment, type juggling (A01, A07)
- `acc:data-security-reviewer` — Sensitive data, crypto, logging failures, secure headers, CORS (A02, A09, A05)
- `acc:design-security-reviewer` — Input validation, output encoding, insecure design, dependencies (A04, A06)

---

## `injection-reviewer`

**Path:** `agents/injection-reviewer.md`

Injection vulnerability specialist for SQL injection, command injection, SSRF, XXE, path traversal, deserialization.

**Configuration:**
```yaml
name: injection-reviewer
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: sonnet
skills: check-sql-injection, check-command-injection, check-ssrf,
        check-xxe, check-path-traversal, check-deserialization,
        task-progress-knowledge
```

**Skills:** 7 (6 security + 1 progress)

---

## `auth-reviewer`

**Path:** `agents/auth-reviewer.md`

Authentication and authorization security specialist for auth, access control, CSRF, mass assignment, type juggling.

**Configuration:**
```yaml
name: auth-reviewer
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: sonnet
skills: check-authentication, check-authorization, check-csrf-protection,
        check-mass-assignment, check-type-juggling, task-progress-knowledge
```

**Skills:** 6 (5 security + 1 progress)

---

## `data-security-reviewer`

**Path:** `agents/data-security-reviewer.md`

Data security specialist for sensitive data, cryptography, logging, headers, CORS.

**Configuration:**
```yaml
name: data-security-reviewer
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: sonnet
skills: check-sensitive-data, check-crypto-usage, check-logging-failures,
        check-secure-headers, check-cors-security, task-progress-knowledge
```

**Skills:** 6 (5 security + 1 progress)

---

## `design-security-reviewer`

**Path:** `agents/design-security-reviewer.md`

Design security specialist for input validation, output encoding, insecure design, dependency vulnerabilities.

**Configuration:**
```yaml
name: design-security-reviewer
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: sonnet
skills: check-input-validation, check-output-encoding, check-insecure-design,
        check-dependency-vulnerabilities, task-progress-knowledge
```

**Skills:** 5 (4 security + 1 progress)

---

## `performance-reviewer`

**Path:** `agents/performance-reviewer.md`

Performance review specialist for efficiency issues.

**Configuration:**
```yaml
name: performance-reviewer
tools: Read, Grep, Glob, TaskCreate, TaskUpdate
model: opus
skills: detect-n-plus-one, check-query-efficiency, detect-memory-issues,
        check-caching-strategy, detect-unnecessary-loops, check-lazy-loading,
        check-batch-processing, estimate-complexity, check-connection-pool,
        check-serialization, check-index-usage, check-async-patterns,
        check-file-io, task-progress-knowledge, discover-project-logs
```

**Skills:** 15 (performance checks + log discovery)

---

## `readability-reviewer`

**Path:** `agents/readability-reviewer.md`

Readability review specialist for code quality.

**Configuration:**
```yaml
name: readability-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: check-naming, check-code-style, check-method-length,
        check-class-length, check-nesting-depth, check-comments,
        check-magic-values, check-consistency, suggest-simplification
```

**Skills:** 9 (readability checks)

---

## `testability-reviewer`

**Path:** `agents/testability-reviewer.md`

Testability review specialist for test quality.

**Configuration:**
```yaml
name: testability-reviewer
tools: Read, Grep, Glob
model: sonnet
skills: check-dependency-injection, check-pure-functions, check-side-effects,
        check-test-quality, suggest-testability-improvements,
        analyze-test-coverage, detect-test-smells
```

**Skills:** 7 (testability checks)

---

## `bug-fix-coordinator`

**Path:** `agents/bug-fix-coordinator.md`

Bug fix coordinator orchestrating diagnosis, fix generation, and regression testing.

**Configuration:**
```yaml
name: bug-fix-coordinator
tools: Task, Read, Grep, Glob, Edit, Write, Bash
model: opus
# No skills - delegates to specialized agents
```

**Workflow:**
1. Parse input (text, file:line, stack trace, log file)
2. Task → `acc:bug-hunter` (diagnose bug category)
3. Task → `acc:bug-fixer` (generate minimal fix)
4. Task → `acc:test-generator` (create regression test)
5. Apply changes and run tests

**Meta-Instructions:**
- `-- focus on <area>` — Prioritize specific area
- `-- skip tests` — Don't generate regression test
- `-- dry-run` — Show fix without applying
- `-- verbose` — Detailed analysis output

---

## `bug-fixer`

**Path:** `agents/bug-fixer.md`

Bug fix specialist generating safe, minimal fixes using diagnosis from bug-hunter.

**Configuration:**
```yaml
name: bug-fixer
tools: Read, Edit, Write, Grep, Glob
model: sonnet
skills: bug-fix-knowledge, bug-root-cause-finder, bug-impact-analyzer,
        generate-bug-fix, bug-regression-preventer,
        detect-code-smells, detect-memory-issues, analyze-solid-violations,
        check-encapsulation, check-side-effects, check-immutability,
        analyze-php-logs
```

**Skills:** 12 (5 new + 6 existing + 1 log analysis)

**Capabilities:**
- Root cause analysis (5 Whys, fault tree)
- Impact/blast radius analysis
- Fix templates for 9 bug categories
- Quality verification (SOLID, code smells, encapsulation)
- Regression prevention checklist

---

## `ci-coordinator`

**Path:** `agents/ci-coordinator.md`

CI/CD coordinator orchestrating pipeline setup, fixing, optimization, and auditing.

**Configuration:**
```yaml
name: ci-coordinator
tools: Read, Write, Edit, Grep, Glob, Bash, Task
model: opus
skills: ci-pipeline-knowledge
```

**Operations:**
- **SETUP**: Create new CI pipeline from scratch
- **FIX**: Diagnose and fix pipeline failures with interactive approval
- **OPTIMIZE**: Improve pipeline performance
- **AUDIT**: Comprehensive CI/CD audit

**Delegation:**
- `acc:pipeline-architect` — Workflow structure
- `acc:static-analysis-agent` — PHPStan, Psalm, DEPTRAC configs
- `acc:test-pipeline-agent` — PHPUnit, coverage setup
- `acc:ci-debugger` — Log analysis, failure diagnosis
- `acc:pipeline-optimizer` — Caching, parallelization
- `acc:ci-security-agent` — Secrets, permissions, deps
- `acc:docker-agent` — Dockerfile optimization
- `acc:deployment-agent` — Deployment strategies

---

## `pipeline-architect`

**Path:** `agents/pipeline-architect.md`

Pipeline design specialist for GitHub Actions and GitLab CI.

**Configuration:**
```yaml
name: pipeline-architect
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: ci-pipeline-knowledge, create-github-actions, create-gitlab-ci, detect-ci-antipatterns
```

**Skills:** 4

---

## `static-analysis-agent`

**Path:** `agents/static-analysis-agent.md`

Static analysis configuration specialist.

**Configuration:**
```yaml
name: static-analysis-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: ci-tools-knowledge, create-phpstan-config, create-psalm-config,
        create-deptrac-config, create-rector-config, psr-coding-style-knowledge,
        check-code-style, analyze-solid-violations, detect-code-smells
```

**Skills:** 9 (4 new + 5 reused)

---

## `test-pipeline-agent`

**Path:** `agents/test-pipeline-agent.md`

Test pipeline configuration specialist.

**Configuration:**
```yaml
name: test-pipeline-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: testing-knowledge, analyze-test-coverage, detect-test-smells,
        check-test-quality, ci-pipeline-knowledge
```

**Skills:** 5 (4 reused + 1 new)

---

## `ci-debugger`

**Path:** `agents/ci-debugger.md`

CI/CD log analysis and failure diagnosis specialist.

**Configuration:**
```yaml
name: ci-debugger
tools: Read, Grep, Glob, Bash
model: sonnet
skills: analyze-ci-logs, detect-ci-antipatterns, analyze-ci-config,
        discover-project-logs
```

**Skills:** 4

---

## `ci-fixer`

**Path:** `agents/ci-fixer.md`

CI fix generation and application specialist. Generates minimal, safe fixes for CI configuration issues.

**Configuration:**
```yaml
name: ci-fixer
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: generate-ci-fix, ci-pipeline-knowledge, ci-tools-knowledge,
        create-github-actions, create-gitlab-ci, detect-ci-antipatterns
```

**Skills:** 6 (1 new + 5 reused)

**Capabilities:**
- Receives diagnosis from `acc:ci-debugger`
- Selects appropriate fix pattern
- Generates minimal, safe changes
- Applies fixes to CI config files
- Provides rollback instructions
- Supports 10+ issue types (memory, composer, timeout, etc.)

---

## `pipeline-optimizer`

**Path:** `agents/pipeline-optimizer.md`

Pipeline performance optimization specialist.

**Configuration:**
```yaml
name: pipeline-optimizer
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: ci-pipeline-knowledge, estimate-pipeline-time, detect-ci-antipatterns,
        optimize-docker-layers, analyze-ci-config, detect-memory-issues,
        check-caching-strategy
```

**Skills:** 7 (2 reused + 5 new)

---

## `ci-security-agent`

**Path:** `agents/ci-security-agent.md`

CI/CD security specialist for secrets, permissions, and dependency scanning.

**Configuration:**
```yaml
name: ci-security-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: ci-pipeline-knowledge, check-sensitive-data, check-dependency-vulnerabilities,
        check-crypto-usage
```

**Skills:** 4 (3 reused + 1 new)

---

## `docker-agent`

**Path:** `agents/docker-agent.md`

Docker configuration and optimization specialist.

**Configuration:**
```yaml
name: docker-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: create-dockerfile-ci, optimize-docker-layers, ci-pipeline-knowledge
```

**Skills:** 3

---

## `deployment-agent`

**Path:** `agents/deployment-agent.md`

Deployment configuration specialist for blue-green, canary, and rolling strategies.

**Configuration:**
```yaml
name: deployment-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: deployment-knowledge, create-deploy-strategy, create-feature-flags,
        ci-pipeline-knowledge, create-github-actions, create-gitlab-ci
```

**Skills:** 6

---

## `docker-coordinator`

**Path:** `agents/docker-coordinator.md`

Docker expert system coordinator. Orchestrates auditing, generation, and optimization.

**Configuration:**
```yaml
name: docker-coordinator
tools: Read, Grep, Glob, Bash, Task, TaskCreate, TaskUpdate
model: opus
skills: docker-knowledge, task-progress-knowledge,
        docker-orchestration-knowledge, create-docker-makefile
```

**Operations:**
- **AUDIT**: Comprehensive Docker configuration audit
- **GENERATE**: Generate Docker components

**Delegation:**
- `acc:docker-architect-agent` — Dockerfile architecture
- `acc:docker-image-builder` — Base images, extensions
- `acc:docker-compose-agent` — Compose configuration
- `acc:docker-performance-agent` — Performance optimization
- `acc:docker-security-agent` — Security audit
- `acc:docker-debugger-agent` — Error diagnosis
- `acc:docker-production-agent` — Production readiness

---

## `docker-architect-agent`

**Path:** `agents/docker-architect-agent.md`

Dockerfile architecture specialist for multi-stage builds, layer optimization, and BuildKit features.

**Configuration:**
```yaml
name: docker-architect-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: docker-knowledge, docker-multistage-knowledge, docker-buildkit-knowledge,
        create-dockerfile-production, create-dockerfile-dev
```

**Skills:** 5

---

## `docker-image-builder`

**Path:** `agents/docker-image-builder.md`

Base image selection and PHP extension installation specialist.

**Configuration:**
```yaml
name: docker-image-builder
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: docker-base-images-knowledge, docker-php-extensions-knowledge,
        create-dockerfile-production, create-dockerfile-dev, create-dockerignore
```

**Skills:** 5

---

## `docker-compose-agent`

**Path:** `agents/docker-compose-agent.md`

Docker Compose configuration specialist for PHP stacks.

**Configuration:**
```yaml
name: docker-compose-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: docker-compose-knowledge, docker-networking-knowledge,
        create-docker-compose-dev, create-docker-compose-production,
        check-docker-compose-config, create-docker-env-template
```

**Skills:** 6

---

## `docker-performance-agent`

**Path:** `agents/docker-performance-agent.md`

Docker build and runtime performance optimization specialist.

**Configuration:**
```yaml
name: docker-performance-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: optimize-docker-layers, optimize-docker-build-time, optimize-docker-image-size,
        optimize-docker-php-fpm, optimize-docker-opcache, optimize-docker-startup
```

**Skills:** 6

---

## `docker-security-agent`

**Path:** `agents/docker-security-agent.md`

Docker security audit and hardening specialist.

**Configuration:**
```yaml
name: docker-security-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: docker-security-knowledge, docker-scanning-knowledge,
        check-docker-security, check-docker-secrets,
        check-docker-user-permissions, detect-docker-antipatterns
```

**Skills:** 6

---

## `docker-debugger-agent`

**Path:** `agents/docker-debugger-agent.md`

Docker error diagnosis and troubleshooting specialist.

**Configuration:**
```yaml
name: docker-debugger-agent
tools: Read, Grep, Glob, Bash
model: sonnet
skills: docker-troubleshooting-knowledge, docker-knowledge,
        analyze-docker-build-errors, analyze-docker-runtime-errors,
        discover-project-logs, analyze-php-logs
```

**Skills:** 6 (2 knowledge + 2 analyzers + 2 log analysis)

---

## `docker-production-agent`

**Path:** `agents/docker-production-agent.md`

Docker production readiness specialist for health checks, graceful shutdown, and logging.

**Configuration:**
```yaml
name: docker-production-agent
tools: Read, Write, Edit, Grep, Glob
model: sonnet
skills: docker-production-knowledge, docker-orchestration-knowledge,
        check-docker-production-readiness, check-docker-healthcheck,
        create-docker-healthcheck, create-docker-entrypoint
```

**Skills:** 6

---

## `explain-coordinator`

**Path:** `agents/explain-coordinator.md`

Code explanation coordinator. Orchestrates codebase navigation, business logic extraction, data flow tracing, visualization, and documentation suggestion. Supports 5 modes.

**Configuration:**
```yaml
name: explain-coordinator
tools: Read, Grep, Glob, Bash, Task, TaskCreate, TaskUpdate
model: opus
skills: explain-output-template, task-progress-knowledge
```

**Workflow (4 phases):**
1. **Navigate** — Task → `acc:codebase-navigator` (scan structure, entry points, patterns)
2. **Analyze** — Task → `acc:business-logic-analyst` + `acc:data-flow-analyst` (+ auditors for deep/onboarding)
3. **Visualize** — Task → `acc:diagram-designer` + `acc:documentation-writer` (deep/onboarding/business)
4. **Present** — Aggregate results, format output, suggest documentation

**Modes:** quick (file), deep (module), onboarding (project), business (non-technical), qa (interactive)

---

## `codebase-navigator`

**Path:** `agents/codebase-navigator.md`

Codebase navigation specialist. Scans directory structure, identifies architectural layers, detects framework and patterns, finds entry points.

**Configuration:**
```yaml
name: codebase-navigator
tools: Read, Grep, Glob
model: sonnet
skills: scan-codebase-structure, identify-entry-points, detect-architecture-pattern
```

**Skills:** 3 (analyzers)

---

## `business-logic-analyst`

**Path:** `agents/business-logic-analyst.md`

Business logic analysis specialist. Extracts business rules, explains business processes in natural language, maps domain concepts and ubiquitous language, detects state machines.

**Configuration:**
```yaml
name: business-logic-analyst
tools: Read, Grep, Glob
model: sonnet
skills: extract-business-rules, explain-business-process, extract-domain-concepts, extract-state-machine
```

**Skills:** 4 (analyzers)

---

## `data-flow-analyst`

**Path:** `agents/data-flow-analyst.md`

Data flow analysis specialist. Traces request lifecycles through all layers, maps data transformations between DTOs/Commands/Entities/Responses, identifies async communication flows.

**Configuration:**
```yaml
name: data-flow-analyst
tools: Read, Grep, Glob
model: sonnet
skills: trace-request-lifecycle, trace-data-transformation, map-async-flows,
        discover-project-logs
```

**Skills:** 4 (analyzers + log discovery)

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Skills →](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
