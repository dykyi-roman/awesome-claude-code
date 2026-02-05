# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Composer plugin providing Claude Code extensions for PHP development with DDD, CQRS, and Clean Architecture patterns.

## Build & Validate

```bash
make help              # Show all available commands
make validate-claude   # Validate .claude structure (run before commits)
make list-commands     # List slash commands
make list-agents       # List agents
make list-skills       # List skills
make test              # Install in Docker test environment
make test-clear        # Clean up test environment
./bin/acc upgrade      # Force upgrade components (creates backup)
```

## Architecture

```
.claude/
├── commands/     # Slash commands (user-invocable)
├── agents/       # Subagents (Task tool targets)
├── skills/       # Skills (knowledge, generators, analyzers, templates)
└── settings.json # Hooks and permissions
```

`src/ComposerPlugin.php` subscribes to Composer's `POST_PACKAGE_INSTALL` and `POST_PACKAGE_UPDATE` events. On install/update, it copies commands, agents, skills directories to the target project's `.claude/` folder. Existing files are never overwritten — use `./bin/acc upgrade` to force update.

### Component Flow

```
COMMANDS                      AGENTS                        SKILLS
────────                      ──────                        ──────
/acc-commit ──────────────→ (direct Bash)

/acc-write-claude-component ─────────→ acc-claude-code-expert ─────→ acc-claude-code-knowledge

/acc-audit-ddd ───────────→ acc-ddd-auditor ────────────→ 4 knowledge skills
                                  │
                                  └──→ (Task) acc-ddd-generator

/acc-audit-architecture ──→ acc-architecture-auditor (coordinator)
                                  │
                                  ├──→ (Task) acc-structural-auditor ──→ 12 skills
                                  │           └── DDD, Clean, Hexagonal, Layered, SOLID, GRASP (6 knowledge)
                                  │           └── solid-violations, code-smells, bounded-contexts, immutability, leaky-abstractions, encapsulation (6 analyzers)
                                  │
                                  ├──→ (Task) acc-behavioral-auditor ──→ 13 skills
                                  │           └── CQRS, Event Sourcing, EDA, Strategy, State, etc.
                                  │
                                  ├──→ (Task) acc-integration-auditor ─→ 12 skills
                                  │           └── Outbox, Saga, Stability, ADR
                                  │
                                  ├──→ (Task) acc-ddd-generator
                                  └──→ (Task) acc-pattern-generator (coordinator)
                                                     │
                                                     ├──→ (Task) acc-stability-generator ──→ 5 skills
                                                     ├──→ (Task) acc-behavioral-generator ─→ 5 skills
                                                     ├──→ (Task) acc-creational-generator ─→ 3 skills
                                                     └──→ (Task) acc-integration-generator → 7 skills

/acc-audit-claude-components → (direct Read/Glob/Grep) ───→ audits .claude/ folder

/acc-audit-psr ───────────→ acc-psr-auditor ────────────→ PSR knowledge skills
                                  │
                                  └──→ PSR create-* skills

/acc-write-documentation ─→ acc-documentation-writer ───→ template skills
                                  │
                                  └──→ (Task) acc-diagram-designer

/acc-audit-documentation ─→ acc-documentation-auditor ──→ QA knowledge skills

/acc-write-test ──────────→ acc-test-generator ─────────→ acc-testing-knowledge
                                                          test create-* skills

/acc-audit-test ──────────→ acc-test-auditor ───────────→ acc-testing-knowledge
                                  │                       test analyze skills
                                  └──→ (Task) acc-test-generator

/acc-code-review ────────→ acc-code-review-coordinator ─→ 3 skills (direct)
                                  │
                                  ├──→ LOW: acc-psr-auditor, acc-test-auditor
                                  ├──→ MEDIUM: acc-bug-hunter, acc-readability-reviewer
                                  └──→ HIGH: acc-security-reviewer, acc-performance-reviewer,
                                             acc-testability-reviewer, acc-ddd-auditor,
                                             acc-architecture-auditor
```

## Key Conventions

- **`acc-` prefix** — all components use this to avoid conflicts
- **`--` separator** — pass meta-instructions to any command:
  - `/acc-audit-ddd ./src -- focus on aggregates`
  - `/acc-code-review feature/auth high -- implement OAuth2`
  - `/acc-commit -- use Russian for commit message`
- **Skills < 500 lines** — extract details to `references/` folder
- **Max 15 skills per agent** — exceeding indicates God-Agent antipattern

### YAML Frontmatter (required at file start)

**Command** (`.claude/commands/name.md`):
```yaml
---
description: Required
allowed-tools: Optional
model: Optional (sonnet/haiku/opus)
---
```

**Agent** (`.claude/agents/name.md`):
```yaml
---
name: Required
description: Required
tools: Optional
skills: Optional (list skill names)
---
```

**Skill** (`.claude/skills/name/SKILL.md`):
```yaml
---
name: Required (lowercase, hyphens)
description: Required (max 1024 chars)
---
```

## Adding Components

Integration chain: **Skill → Agent (skills: frontmatter) → Command (Task tool)**

When adding components:
1. Create component with correct YAML frontmatter
2. Wire to parent (skill→agent, agent→command)
3. Update docs: `README.md`, `docs/*.md`, `CHANGELOG.md`
4. Run `make validate-claude`

## Troubleshooting

| Issue              | Solution                                                    |
|--------------------|-------------------------------------------------------------|
| Skill not loading  | Check `skills:` in agent frontmatter                        |
| Agent not invoked  | Check command uses `Task` tool with correct `subagent_type` |
| Validation fails   | Ensure frontmatter starts with `---`                        |
