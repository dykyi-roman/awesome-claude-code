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
├── commands/                     # 25 commands
│   ├── acc-audit-*.md            # Audit commands (10): architecture, ci, claude-components,
│   │                             #   ddd, docker, documentation, patterns, performance, psr, security, test
│   ├── acc-bug-fix.md
│   ├── acc-ci-*.md               # CI commands (3): setup, fix, optimize
│   ├── acc-code-review.md
│   ├── acc-commit.md
│   ├── acc-generate-*.md         # Generate commands (7): claude-component, ddd, docker, documentation, patterns, psr, test
│   ├── acc-refactor.md
│   └── ...
├── agents/                       # 50 agents
│   ├── acc-*-auditor.md          # Auditors (11): architecture, behavioral, creational,
│   │                             #   ddd, documentation, integration, pattern, psr,
│   │                             #   stability, structural, test
│   ├── acc-*-generator.md        # Generators (8): architecture, behavioral, creational,
│   │                             #   ddd, integration, pattern, psr, stability
│   ├── acc-*-coordinator.md      # Coordinators (5): bug-fix, ci, code-review, docker, refactor
│   ├── acc-*-reviewer.md         # Reviewers (4): performance, readability, security, testability
│   ├── acc-ci-*.md               # CI agents (9): ci-coordinator, ci-debugger, ci-fixer,
│   │                             #   ci-security-agent, deployment-agent, docker-agent,
│   │                             #   pipeline-architect, pipeline-optimizer,
│   │                             #   static-analysis-agent, test-pipeline-agent
│   ├── acc-docker-*.md           # Docker agents (8): docker-coordinator, docker-architect-agent,
│   │                             #   docker-image-builder, docker-compose-agent,
│   │                             #   docker-performance-agent, docker-security-agent,
│   │                             #   docker-debugger-agent, docker-production-agent
│   └── ...
├── skills/                       # 200 skills
│   ├── acc-*-knowledge/          # 38 knowledge skills
│   ├── acc-check-*/              # 44 analyzer skills
│   ├── acc-find-*/               # 9 bug detection skills
│   ├── acc-detect-*/             # 7 detection skills
│   ├── acc-analyze-*/            # 8 analysis skills
│   ├── acc-create-*/             # 69 generator skills
│   ├── acc-optimize-*/           # 7 optimizer skills
│   ├── acc-*-template/           # 10 template skills
│   └── acc-*/                    # 8 other skills (estimate, suggest, bug-*)
└── settings.json

docs/                             # Documentation (root level)
├── commands.md
├── agents.md
├── skills.md
├── component-flow.md
├── hooks.md
├── mcp.md
└── quick-reference.md
```

## Statistics

| Component | Count |
|-----------|-------|
| Commands | 25 |
| Agents | 50 |
| Knowledge Skills | 38 |
| Analyzer Skills | 68 |
| Generator Skills | 69 |
| Optimizer Skills | 7 |
| Template Skills | 10 |
| Other Skills | 8 |
| **Total Skills** | **200** |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md)
