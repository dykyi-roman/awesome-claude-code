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
| Rule    | `.claude/rules/name.md`        | Conditional      |
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
├── commands/                     # 26 commands
│   ├── acc-audit-*.md            # Audit commands (10): architecture, ci, claude-components,
│   │                             #   ddd, docker, documentation, patterns, performance, psr, security, test
│   ├── acc-bug-fix.md
│   ├── acc-ci-*.md               # CI commands (3): setup, fix, optimize
│   ├── acc-code-review.md
│   ├── acc-commit.md
│   ├── acc-explain.md            # Code explanation (5 modes)
│   ├── acc-generate-*.md         # Generate commands (7): claude-component, ddd, docker, documentation, patterns, psr, test
│   ├── acc-refactor.md
│   └── ...
├── agents/                       # 62 agents
│   ├── acc-*-auditor.md          # Auditors (13): architecture, behavioral, cqrs, creational,
│   │                             #   ddd, documentation, gof-structural, integration,
│   │                             #   pattern, psr, stability, structural, test
│   ├── acc-*-generator.md        # Generators (10): architecture, behavioral, creational,
│   │                             #   cqrs, ddd, gof-structural, integration, pattern, psr, stability
│   ├── acc-*-coordinator.md      # Coordinators (6): bug-fix, ci, code-review, docker, explain, refactor
│   │                             #   + security-reviewer (coordinator via Task delegation)
│   ├── acc-*-reviewer.md         # Reviewers (8): auth, data-security, design-security, injection,
│   │                             #   performance, readability, security (coordinator), testability
│   ├── acc-*-analyst.md          # Analysts (2): business-logic, data-flow
│   ├── acc-codebase-navigator.md # Codebase navigation specialist
│   ├── acc-ci-*.md               # CI agents (9): ci-coordinator, ci-debugger, ci-fixer,
│   │                             #   ci-security-agent, deployment-agent, docker-agent,
│   │                             #   pipeline-architect, pipeline-optimizer,
│   │                             #   static-analysis-agent, test-pipeline-agent
│   ├── acc-docker-*.md           # Docker agents (8): docker-coordinator, docker-architect-agent,
│   │                             #   docker-image-builder, docker-compose-agent,
│   │                             #   docker-performance-agent, docker-security-agent,
│   │                             #   docker-debugger-agent, docker-production-agent
│   └── ...
├── skills/                       # 259 skills
│   ├── acc-*-knowledge/          # 42 knowledge skills
│   ├── acc-check-*/              # 64 analyzer skills
│   ├── acc-find-*/               # 8 bug detection skills
│   ├── acc-detect-*/             # 8 detection skills
│   ├── acc-analyze-*/            # 9 analysis skills
│   ├── acc-scan-*/               # 1 scanner skill
│   ├── acc-identify-*/           # 1 identifier skill
│   ├── acc-resolve-*/            # 1 resolver skill
│   ├── acc-extract-*/            # 3 extractor skills
│   ├── acc-explain-*/            # 2 explainer skills (business-process, output-template)
│   ├── acc-trace-*/              # 2 tracer skills
│   ├── acc-map-*/                # 1 mapper skill
│   ├── acc-discover-*/           # 1 discovery skill
│   ├── acc-create-*/             # 86 generator skills
│   ├── acc-generate-*/           # 2 generator skills
│   ├── acc-optimize-*/           # 7 optimizer skills
│   ├── acc-*-template/           # 10 template skills
│   └── acc-*/                    # 7 other skills (estimate, suggest, bug-*)
├── rules/                       # 3 conditional rules
│   ├── component-creation.md    # Loads for .claude/ edits
│   ├── versioning.md            # Loads for CHANGELOG, README, docs/
│   └── troubleshooting.md       # Loads for .claude/, src/, Makefile
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
| Commands | 26 |
| Agents | 62 |
| Knowledge Skills | 42 |
| Analyzer Skills | 100 |
| Generator Skills | 88 |
| Optimizer Skills | 7 |
| Template Skills | 10 |
| Other Skills | 7 |
| **Total Skills** | **259** |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Component Flow](component-flow.md)
