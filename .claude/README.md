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
model: sonnet
skills: acc-ddd-knowledge, acc-cqrs-knowledge, acc-clean-arch-knowledge,
        acc-hexagonal-knowledge, acc-layer-arch-knowledge,
        acc-event-sourcing-knowledge, acc-eda-knowledge
```

---

### `acc-ddd-auditor`

**Path:** `agents/acc-ddd-auditor.md`

Specialized DDD compliance auditor.

**Configuration:**
```yaml
name: acc-ddd-auditor
tools: Read, Grep, Glob, Bash
model: sonnet
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
model: sonnet
skills: acc-ddd-knowledge, acc-create-value-object, acc-create-entity,
        acc-create-aggregate, acc-create-domain-event, acc-create-repository,
        acc-create-command, acc-create-query, acc-create-use-case
```

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

### Generator Skills

Code generators for DDD and architecture components (PHP 8.4).

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-value-object` | `skills/acc-create-value-object/` | DDD Value Objects |
| `acc-create-entity` | `skills/acc-create-entity/` | DDD Entities |
| `acc-create-aggregate` | `skills/acc-create-aggregate/` | DDD Aggregates |
| `acc-create-domain-event` | `skills/acc-create-domain-event/` | Domain Events |
| `acc-create-repository` | `skills/acc-create-repository/` | Repository interfaces |
| `acc-create-command` | `skills/acc-create-command/` | CQRS Commands |
| `acc-create-query` | `skills/acc-create-query/` | CQRS Queries |
| `acc-create-use-case` | `skills/acc-create-use-case/` | Application Use Cases |

---

## File Structure

```
.claude/
├── commands/
│   ├── acc-claude-code.md
│   ├── acc-commit.md
│   ├── acc-architecture-audit.md
│   └── acc-ddd-audit.md
├── agents/
│   ├── acc-claude-code-expert.md
│   ├── acc-architecture-auditor.md
│   ├── acc-ddd-auditor.md
│   └── acc-ddd-generator.md
├── skills/
│   ├── acc-claude-code-knowledge/
│   ├── acc-ddd-knowledge/
│   ├── acc-cqrs-knowledge/
│   ├── acc-clean-arch-knowledge/
│   ├── acc-hexagonal-knowledge/
│   ├── acc-layer-arch-knowledge/
│   ├── acc-event-sourcing-knowledge/
│   ├── acc-eda-knowledge/
│   ├── acc-create-value-object/
│   ├── acc-create-entity/
│   ├── acc-create-aggregate/
│   ├── acc-create-domain-event/
│   ├── acc-create-repository/
│   ├── acc-create-command/
│   ├── acc-create-query/
│   └── acc-create-use-case/
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
