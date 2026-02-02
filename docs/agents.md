# Agents

Subagents for specialized tasks. Agents are autonomous workers that handle complex, multi-step operations.

## Overview

| Agent | Purpose | Invoked By |
|-------|---------|------------|
| `acc-claude-code-expert` | Create Claude Code components | `/acc-claude-code` |
| `acc-architecture-auditor` | Multi-pattern architecture analysis | `/acc-audit-architecture` |
| `acc-architecture-generator` | Generate architecture components | `acc-architecture-auditor` (Task) |
| `acc-ddd-auditor` | DDD compliance analysis | `/acc-audit-ddd` |
| `acc-ddd-generator` | Generate DDD components | `acc-ddd-auditor` (Task) |
| `acc-pattern-auditor` | Design patterns analysis | `/acc-audit-architecture` |
| `acc-pattern-generator` | Generate design patterns | `acc-architecture-auditor` (Task) |
| `acc-psr-auditor` | PSR compliance analysis | `/acc-audit-psr` |
| `acc-psr-generator` | Generate PSR implementations | `acc-psr-auditor` (Skill) |
| `acc-documentation-writer` | Generate documentation | `/acc-write-documentation` |
| `acc-documentation-auditor` | Audit documentation quality | `/acc-audit-documentation` |
| `acc-diagram-designer` | Create Mermaid diagrams | `acc-documentation-writer` (Task) |

## How Agents Work

1. **Invocation**: Commands invoke agents via Task tool or direct reference
2. **Skills Loading**: Agent loads skills from `skills:` frontmatter
3. **Execution**: Agent performs multi-step analysis or generation
4. **Delegation**: Agent may delegate subtasks to other agents via Task tool

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

## `acc-ddd-auditor`

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

## `acc-pattern-generator`

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

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Skills →](skills.md) | [Component Flow](component-flow.md) | [Quick Reference](quick-reference.md)
