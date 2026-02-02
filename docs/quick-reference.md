# Quick Reference

Component paths, formats, and best practices. Use this as a cheat sheet when creating or modifying components.

## When to Use This Document

- Creating new commands, agents, or skills
- Checking correct YAML frontmatter format
- Finding component paths
- Following best practices

---

## Component Paths

| Type    | Path                           | Invocation       |
|---------|--------------------------------|------------------|
| Command | `.claude/commands/name.md`     | `/name`          |
| Agent   | `.claude/agents/name.md`       | Auto or explicit |
| Skill   | `.claude/skills/name/SKILL.md` | `/name` or auto  |
| Hook    | `.claude/settings.json`        | On event         |

## YAML Frontmatter

### Command

```yaml
---
description: Required
allowed-tools: Optional
model: Optional (sonnet/haiku/opus)
argument-hint: Optional
---
```

### Agent

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

### Skill

```yaml
---
name: Required (lowercase, hyphens)
description: Required (max 1024 chars)
allowed-tools: Optional
---
```

## Best Practices

1. **Specific descriptions** — not "helps with code" but "analyzes Python for vulnerabilities"
2. **PROACTIVELY keyword** — triggers automatic agent invocation
3. **Minimal tools** — only what's needed
4. **Skills < 500 lines** — use references/ for details
5. **Test in isolation** — verify before integration

## File Structure

```
.claude/
├── commands/
│   ├── acc-audit-architecture.md
│   ├── acc-audit-claude-code.md
│   ├── acc-audit-ddd.md
│   ├── acc-audit-documentation.md
│   ├── acc-audit-psr.md
│   ├── acc-claude-code.md
│   ├── acc-commit.md
│   └── acc-write-documentation.md
├── agents/
│   ├── acc-architecture-auditor.md
│   ├── acc-architecture-generator.md
│   ├── acc-claude-code-expert.md
│   ├── acc-ddd-auditor.md
│   ├── acc-ddd-generator.md
│   ├── acc-documentation-auditor.md
│   ├── acc-documentation-writer.md
│   ├── acc-diagram-designer.md
│   ├── acc-pattern-auditor.md
│   ├── acc-pattern-generator.md
│   ├── acc-psr-auditor.md
│   └── acc-psr-generator.md
├── skills/
│   ├── acc-*-knowledge/          # 20 knowledge skills
│   ├── acc-analyze-*/            # 1 analyzer skill
│   ├── acc-create-*/             # 43 generator skills
│   └── acc-*-template/           # 9 template skills
└── settings.json

docs/                       # Documentation (root level)
├── commands.md
├── agents.md
├── skills.md
├── component-flow.md
└── quick-reference.md
```

## Statistics

| Component | Count |
|-----------|-------|
| Commands | 8 |
| Agents | 11 |
| Knowledge Skills | 20 |
| Analyzer Skills | 1 |
| Generator Skills | 43 |
| Template Skills | 9 |
| **Total Skills** | **73** |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md)
