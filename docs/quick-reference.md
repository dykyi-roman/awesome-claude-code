# Quick Reference

> Version: **v3.2.0**

Component paths, formats, and best practices. Use this as a cheat sheet when creating or modifying components.

## When to Use This Document

- Creating new commands, agents, or skills
- Checking correct YAML frontmatter format
- Finding component paths
- Following best practices

---

## Component Paths

| Type    | Path                       | Invocation          |
|---------|----------------------------|---------------------|
| Command | `commands/name.md`         | `/acc:name`         |
| Agent   | `agents/name.md`           | Auto or explicit    |
| Skill   | `skills/name/SKILL.md`     | `/acc:name` or auto |
| Rule    | `.claude/rules/name.md`    | Conditional         |
| Hook    | `hooks/hooks.json`         | On event            |

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
awesome-claude-code/
├── .claude-plugin/
│   ├── marketplace.json            # Marketplace catalog
│   └── plugin.json                 # Plugin manifest
├── commands/                       # 26 commands
│   ├── audit-*.md                  # Audit commands (11): architecture, ci, claude-components,
│   │                               #   ddd, docker, documentation, patterns, performance, psr, security, test
│   ├── bug-fix.md
│   ├── ci-*.md                     # CI commands (3): setup, fix, optimize
│   ├── code-review.md
│   ├── commit.md
│   ├── explain.md                  # Code explanation (5 modes)
│   ├── generate-*.md               # Generate commands (7): claude-component, ddd, docker, documentation, patterns, psr, test
│   ├── refactor.md
│   └── ...
├── agents/                         # 68 agents
│   ├── *-auditor.md                # Auditors (15): architecture, behavioral, cqrs, creational,
│   │                               #   ddd, documentation, gof-structural, integration,
│   │                               #   observability, pattern, principles, psr, stability, structural, test
│   ├── *-generator.md              # Generators (11): api-infrastructure, architecture, behavioral, creational,
│   │                               #   cqrs, ddd, gof-structural, messaging, pattern, psr, stability
│   ├── *-coordinator.md            # Coordinators (6): bug-fix, ci, code-review, docker, explain, refactor
│   │                               #   + security-reviewer (coordinator via Task delegation)
│   ├── *-reviewer.md               # Reviewers (10): auth, data-security, design-security, injection,
│   │                               #   performance, readability, resource, scalability, security (coordinator), testability
│   ├── *-analyst.md                # Analysts (2): business-logic, data-flow
│   ├── codebase-navigator.md       # Codebase navigation specialist
│   ├── ci-*.md                     # CI agents (9): ci-coordinator, ci-debugger, ci-fixer,
│   │                               #   ci-security-agent, deployment-agent, docker-agent,
│   │                               #   pipeline-architect, pipeline-optimizer,
│   │                               #   static-analysis-agent, test-pipeline-agent
│   ├── docker-*.md                 # Docker agents (8): docker-coordinator, docker-architect-agent,
│   │                               #   docker-image-builder, docker-compose-agent,
│   │                               #   docker-performance-agent, docker-security-agent,
│   │                               #   docker-debugger-agent, docker-production-agent
│   └── ...
├── skills/                         # 283 skills
│   ├── *-knowledge/                # 53 knowledge skills
│   ├── check-*/                    # 71 analyzer skills
│   ├── find-*/                     # 8 bug detection skills
│   ├── detect-*/                   # 8 detection skills
│   ├── analyze-*/                  # 9 analysis skills
│   ├── scan-*/                     # 1 scanner skill
│   ├── identify-*/                 # 1 identifier skill
│   ├── resolve-*/                  # 1 resolver skill
│   ├── extract-*/                  # 3 extractor skills
│   ├── explain-*/                  # 1 explainer skill (business-process)
│   ├── trace-*/                    # 2 tracer skills
│   ├── map-*/                      # 1 mapper skill
│   ├── discover-*/                 # 1 discovery skill
│   ├── create-*/                   # 97 generator skills
│   ├── generate-*/                 # 2 generator skills
│   ├── optimize-*/                 # 7 optimizer skills
│   ├── *-template/                 # 10 template skills
│   └── */                          # 7 other skills (estimate, suggest, bug-*)
├── hooks/
│   └── hooks.json                  # PHP syntax check hook
├── .claude/
│   ├── settings.json               # Project settings (dev only, NOT part of plugin)
│   └── rules/                      # Conditional rules (dev only, NOT part of plugin)
│       ├── component-creation.md
│       ├── versioning.md
│       └── troubleshooting.md
├── docs/                           # Documentation
│   ├── commands.md
│   ├── agents.md
│   ├── skills.md
│   ├── component-flow.md
│   ├── hooks.md
│   ├── mcp.md
│   └── quick-reference.md
├── README.md
├── CLAUDE.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Makefile
├── llms.txt
└── LICENSE
```

## Statistics

| Component | Count |
|-----------|-------|
| Commands | 26 |
| Agents | 68 |
| Knowledge Skills | 53 |
| Analyzer Skills | 107 |
| Generator Skills | 99 |
| Optimizer Skills | 7 |
| Template Skills | 10 |
| Other Skills | 7 |
| **Total Skills** | **283** |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md)
