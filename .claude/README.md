# Claude Code Components

Detailed documentation for commands, agents, and skills.

## Table of Contents

- [Commands](#commands)
- [Agents](#agents)
- [Skills](#skills)
  - [Knowledge Skills](#knowledge-skills)
  - [Generator Skills](#generator-skills)
- [File Structure](#file-structure)
- [Quick Reference](#quick-reference)

---

## Component Flow

This section describes how commands, agents, and skills interact.

### Dependency Graph

```
COMMANDS                    AGENTS                      SKILLS
────────                    ──────                      ──────
/acc-commit ────────────→ (direct Bash)

/acc-claude-code ───────→ acc-claude-code-expert ───→ acc-claude-code-knowledge

/acc-claude-code-audit ─→ (direct analysis)

/acc-ddd-audit ─────────→ acc-ddd-auditor ──────────→ acc-ddd-knowledge
                                │
                                └──→ (Task) acc-ddd-generator ──→ 13 create-* skills

/acc-architecture-audit ─→ acc-architecture-auditor ─→ 11 knowledge skills
                                │
                                ├──→ (Task) acc-ddd-generator ──→ 13 create-* skills
                                └──→ (Task) acc-pattern-generator → 15 create-* skills
```

### Audit → Generate Workflow

```
User: /acc-architecture-audit ./src
       ↓
Command loads acc-architecture-auditor agent
       ↓
Auditor analyzes project using knowledge skills
       ↓
Auditor generates report with recommendations
       ↓
Auditor asks "Generate code?"
       ↓
If yes → Task tool invokes generator agent
       ↓
Generator selects appropriate create-* skill
       ↓
Skill generates PHP code with tests
```

### Generator Mapping

| Issue Type | Generator Agent | Skills Used |
|------------|-----------------|-------------|
| DDD components | `acc-ddd-generator` | 13 acc-create-* skills |
| Design patterns | `acc-pattern-generator` | 15 acc-create-* skills |
| Architecture | `acc-architecture-generator` | Coordinator (delegates) |

### Generator Skills by Category

**DDD (13 skills):**
- `acc-create-value-object` — Value Objects
- `acc-create-entity` — Entities
- `acc-create-aggregate` — Aggregates
- `acc-create-domain-event` — Domain Events
- `acc-create-repository` — Repository interfaces
- `acc-create-command` — CQRS Commands
- `acc-create-query` — CQRS Queries
- `acc-create-use-case` — Application Use Cases
- `acc-create-domain-service` — Domain Services
- `acc-create-factory` — Factories
- `acc-create-specification` — Specifications
- `acc-create-dto` — DTOs
- `acc-create-anti-corruption-layer` — Anti-Corruption Layer

**Stability Patterns (4 skills):**
- `acc-create-circuit-breaker` — Circuit Breaker
- `acc-create-retry-pattern` — Retry with backoff
- `acc-create-rate-limiter` — Rate limiting
- `acc-create-bulkhead` — Bulkhead isolation

**Integration Patterns (2 skills):**
- `acc-create-outbox-pattern` — Transactional Outbox
- `acc-create-saga-pattern` — Saga orchestration

**Behavioral Patterns (5 skills):**
- `acc-create-strategy` — Strategy pattern
- `acc-create-state` — State machine
- `acc-create-chain-of-responsibility` — Handler chains
- `acc-create-decorator` — Decorator pattern
- `acc-create-null-object` — Null Object pattern

**Creational Patterns (2 skills):**
- `acc-create-builder` — Builder pattern
- `acc-create-object-pool` — Object Pool

**Enterprise Patterns (2 skills):**
- `acc-create-read-model` — CQRS Read Models
- `acc-create-policy` — Policy pattern

---

## Commands

### `/acc-claude-code`

**Path:** `commands/acc-claude-code.md`

Interactive wizard for creating Claude Code components.

**Usage:**
```
/acc-claude-code
```

**Process:**
1. Asks what to create (command/agent/skill/hook)
2. Gathers requirements through questions
3. Uses `acc-claude-code-expert` agent with `acc-claude-code-knowledge` skill
4. Creates component with proper structure
5. Validates and shows result

---

### `/acc-claude-code-audit`

**Path:** `commands/acc-claude-code-audit.md`

Audit `.claude/` folder structure and configuration quality.

**Usage:**
```
/acc-claude-code-audit
```

**Analyzes:**
- Commands (YAML frontmatter, descriptions, tool restrictions)
- Agents (naming, skills references, tool permissions)
- Skills (structure, size, references)
- Settings (hooks, permissions, secrets)
- Cross-references integrity

**Output:**
- File tree with status indicators
- Detailed issues analysis
- Prioritized recommendations
- Ready-to-apply quick fixes

---

### `/acc-commit`

**Path:** `commands/acc-commit.md`

Auto-generate commit message from diff and push to current branch.

**Usage:**
```
/acc-commit
```

---

### `/acc-architecture-audit`

**Path:** `commands/acc-architecture-audit.md`

Comprehensive multi-pattern architecture audit for PHP projects.

**Usage:**
```
/acc-architecture-audit <path-to-project>
```

**Analyzes:**
- DDD compliance
- CQRS patterns
- Clean Architecture
- Hexagonal Architecture
- Layered Architecture
- Event Sourcing
- Event-Driven Architecture
- Outbox Pattern
- Saga Pattern
- Stability Patterns

---

### `/acc-ddd-audit`

**Path:** `commands/acc-ddd-audit.md`

DDD compliance analysis for PHP projects.

**Usage:**
```
/acc-ddd-audit <path-to-project>
```

---

## Agents

### `acc-claude-code-expert`

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

### `acc-architecture-auditor`

**Path:** `agents/acc-architecture-auditor.md`

Multi-pattern architecture auditor.

**Configuration:**
```yaml
name: acc-architecture-auditor
tools: Read, Grep, Glob, Bash
model: opus
skills: acc-ddd-knowledge, acc-cqrs-knowledge, acc-clean-arch-knowledge,
        acc-hexagonal-knowledge, acc-layer-arch-knowledge,
        acc-event-sourcing-knowledge, acc-eda-knowledge,
        acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge,
        acc-stability-patterns-knowledge
```

---

### `acc-ddd-auditor`

**Path:** `agents/acc-ddd-auditor.md`

Specialized DDD compliance auditor.

**Configuration:**
```yaml
name: acc-ddd-auditor
tools: Read, Grep, Glob, Bash
model: opus
skills: acc-ddd-knowledge
```

---

### `acc-ddd-generator`

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

### `acc-pattern-auditor`

**Path:** `agents/acc-pattern-auditor.md`

Design patterns auditor (Integration, Stability, Behavioral, Creational, Enterprise).

**Configuration:**
```yaml
name: acc-pattern-auditor
tools: Read, Grep, Glob, Bash
model: opus
skills: acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge,
        acc-stability-patterns-knowledge, acc-eda-knowledge
```

---

### `acc-pattern-generator`

**Path:** `agents/acc-pattern-generator.md`

Creates integration and design pattern components.

**Configuration:**
```yaml
name: acc-pattern-generator
tools: Read, Write, Glob, Grep, Edit
model: opus
skills: acc-outbox-pattern-knowledge, acc-saga-pattern-knowledge,
        acc-stability-patterns-knowledge, acc-create-outbox-pattern,
        acc-create-saga-pattern, acc-create-circuit-breaker,
        acc-create-retry-pattern, acc-create-rate-limiter,
        acc-create-bulkhead, acc-create-strategy, acc-create-state,
        acc-create-decorator, acc-create-chain-of-responsibility,
        acc-create-null-object, acc-create-builder, acc-create-object-pool,
        acc-create-read-model, acc-create-policy
```

---

### `acc-architecture-generator`

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

## Skills

### Knowledge Skills

Knowledge bases for architecture audits and best practices.

| Skill | Path | Description |
|-------|------|-------------|
| `acc-claude-code-knowledge` | `skills/acc-claude-code-knowledge/` | Claude Code formats and patterns |
| `acc-ddd-knowledge` | `skills/acc-ddd-knowledge/` | DDD patterns, antipatterns |
| `acc-cqrs-knowledge` | `skills/acc-cqrs-knowledge/` | CQRS command/query patterns |
| `acc-clean-arch-knowledge` | `skills/acc-clean-arch-knowledge/` | Clean Architecture patterns |
| `acc-hexagonal-knowledge` | `skills/acc-hexagonal-knowledge/` | Hexagonal/Ports & Adapters |
| `acc-layer-arch-knowledge` | `skills/acc-layer-arch-knowledge/` | Layered Architecture patterns |
| `acc-event-sourcing-knowledge` | `skills/acc-event-sourcing-knowledge/` | Event Sourcing patterns |
| `acc-eda-knowledge` | `skills/acc-eda-knowledge/` | Event-Driven Architecture |
| `acc-outbox-pattern-knowledge` | `skills/acc-outbox-pattern-knowledge/` | Transactional Outbox pattern |
| `acc-saga-pattern-knowledge` | `skills/acc-saga-pattern-knowledge/` | Saga/distributed transactions |
| `acc-stability-patterns-knowledge` | `skills/acc-stability-patterns-knowledge/` | Circuit Breaker, Retry, Rate Limiter, Bulkhead |

### Generator Skills

Code generators for DDD and architecture components (PHP 8.5).

#### DDD Components

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-value-object` | `skills/acc-create-value-object/` | DDD Value Objects |
| `acc-create-entity` | `skills/acc-create-entity/` | DDD Entities |
| `acc-create-aggregate` | `skills/acc-create-aggregate/` | DDD Aggregates |
| `acc-create-domain-event` | `skills/acc-create-domain-event/` | Domain Events |
| `acc-create-repository` | `skills/acc-create-repository/` | Repository interfaces |
| `acc-create-domain-service` | `skills/acc-create-domain-service/` | DDD Domain Services |
| `acc-create-factory` | `skills/acc-create-factory/` | DDD Factories |
| `acc-create-specification` | `skills/acc-create-specification/` | DDD Specifications |
| `acc-create-dto` | `skills/acc-create-dto/` | DTOs for layer boundaries |
| `acc-create-anti-corruption-layer` | `skills/acc-create-anti-corruption-layer/` | Anti-Corruption Layer (ACL) |

#### CQRS Components

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-command` | `skills/acc-create-command/` | CQRS Commands |
| `acc-create-query` | `skills/acc-create-query/` | CQRS Queries |
| `acc-create-use-case` | `skills/acc-create-use-case/` | Application Use Cases |
| `acc-create-read-model` | `skills/acc-create-read-model/` | CQRS Read Models/Projections |

#### Stability Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-circuit-breaker` | `skills/acc-create-circuit-breaker/` | Circuit Breaker pattern |
| `acc-create-retry-pattern` | `skills/acc-create-retry-pattern/` | Retry with exponential backoff |
| `acc-create-rate-limiter` | `skills/acc-create-rate-limiter/` | Rate limiting (Token Bucket, Sliding Window) |
| `acc-create-bulkhead` | `skills/acc-create-bulkhead/` | Bulkhead isolation pattern |

#### Integration Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-outbox-pattern` | `skills/acc-create-outbox-pattern/` | Transactional Outbox |
| `acc-create-saga-pattern` | `skills/acc-create-saga-pattern/` | Saga orchestration |

#### Behavioral Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-strategy` | `skills/acc-create-strategy/` | Strategy pattern |
| `acc-create-state` | `skills/acc-create-state/` | State machine pattern |
| `acc-create-chain-of-responsibility` | `skills/acc-create-chain-of-responsibility/` | Handler chains |
| `acc-create-decorator` | `skills/acc-create-decorator/` | Decorator pattern |
| `acc-create-null-object` | `skills/acc-create-null-object/` | Null Object pattern |
| `acc-create-policy` | `skills/acc-create-policy/` | Policy pattern |

#### Creational Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-builder` | `skills/acc-create-builder/` | Builder pattern |
| `acc-create-object-pool` | `skills/acc-create-object-pool/` | Object Pool pattern |

---

## File Structure

```
.claude/
├── commands/
│   ├── acc-architecture-audit.md
│   ├── acc-claude-code.md
│   ├── acc-claude-code-audit.md
│   ├── acc-commit.md
│   └── acc-ddd-audit.md
├── agents/
│   ├── acc-architecture-auditor.md
│   ├── acc-architecture-generator.md
│   ├── acc-claude-code-expert.md
│   ├── acc-ddd-auditor.md
│   ├── acc-ddd-generator.md
│   ├── acc-pattern-auditor.md
│   └── acc-pattern-generator.md
├── skills/
│   ├── acc-clean-arch-knowledge/
│   ├── acc-claude-code-knowledge/
│   ├── acc-cqrs-knowledge/
│   ├── acc-ddd-knowledge/
│   ├── acc-eda-knowledge/
│   ├── acc-event-sourcing-knowledge/
│   ├── acc-hexagonal-knowledge/
│   ├── acc-layer-arch-knowledge/
│   ├── acc-outbox-pattern-knowledge/
│   ├── acc-saga-pattern-knowledge/
│   ├── acc-stability-patterns-knowledge/
│   ├── acc-create-aggregate/
│   ├── acc-create-anti-corruption-layer/
│   ├── acc-create-builder/
│   ├── acc-create-bulkhead/
│   ├── acc-create-chain-of-responsibility/
│   ├── acc-create-circuit-breaker/
│   ├── acc-create-command/
│   ├── acc-create-decorator/
│   ├── acc-create-domain-event/
│   ├── acc-create-domain-service/
│   ├── acc-create-dto/
│   ├── acc-create-entity/
│   ├── acc-create-factory/
│   ├── acc-create-null-object/
│   ├── acc-create-object-pool/
│   ├── acc-create-outbox-pattern/
│   ├── acc-create-policy/
│   ├── acc-create-query/
│   ├── acc-create-rate-limiter/
│   ├── acc-create-read-model/
│   ├── acc-create-repository/
│   ├── acc-create-retry-pattern/
│   ├── acc-create-saga-pattern/
│   ├── acc-create-specification/
│   ├── acc-create-state/
│   ├── acc-create-strategy/
│   ├── acc-create-use-case/
│   └── acc-create-value-object/
└── README.md
```

---

## Quick Reference

### Component Paths

| Type    | Path                           | Invocation       |
|---------|--------------------------------|------------------|
| Command | `.claude/commands/name.md`     | `/name`          |
| Agent   | `.claude/agents/name.md`       | Auto or explicit |
| Skill   | `.claude/skills/name/SKILL.md` | `/name` or auto  |
| Hook    | `.claude/settings.json`        | On event         |

### YAML Frontmatter

**Command:**
```yaml
---
description: Required
allowed-tools: Optional
model: Optional (sonnet/haiku/opus)
argument-hint: Optional
---
```

**Agent:**
```yaml
---
name: Required
description: Required
tools: Optional (default: all)
model: Optional (default: sonnet)
permissionMode: Optional
skills: Optional
---
```

**Skill:**
```yaml
---
name: Required (lowercase, hyphens)
description: Required (max 1024 chars)
allowed-tools: Optional
---
```

### Best Practices

1. **Specific descriptions** — not "helps with code" but "analyzes Python for vulnerabilities"
2. **PROACTIVELY keyword** — triggers automatic agent invocation
3. **Minimal tools** — only what's needed
4. **Skills < 500 lines** — use references/ for details
5. **Test in isolation** — verify before integration

### Statistics

| Component | Count |
|-----------|-------|
| Commands | 5 |
| Agents | 7 |
| Knowledge Skills | 11 |
| Generator Skills | 28 |
| **Total Skills** | **39** |