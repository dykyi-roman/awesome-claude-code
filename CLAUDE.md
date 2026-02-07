# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Composer plugin (`composer-plugin` type) providing Claude Code extensions for PHP development with DDD, CQRS, and Clean Architecture patterns. Installed via `composer require dykyi-roman/awesome-claude-code`. The plugin auto-copies `.claude/` components (commands, agents, skills) to the target project on install/update, never overwriting existing files.

## Commands

```bash
make help                   # Show all available make targets (default)
make validate-claude        # Validate .claude/ structure — run before every commit
make list-commands          # List all slash commands
make list-agents            # List all agents
make list-skills            # List all skills
make test                   # Install in Docker test environment (tests/)
make test-clear             # Clear test environment
make changelog              # Show recent git commits for changelog
make release                # Run validate-claude, then print release instructions
./bin/acc upgrade                        # Force upgrade components (creates backup)
./bin/acc upgrade --no-backup            # Upgrade without backup
./bin/acc upgrade --component=commands   # Upgrade only commands|agents|skills
```

**Testing**: `make test` runs `docker compose run --rm php composer install` in `tests/` directory, which triggers the Composer plugin and copies components to `tests/.claude/`. Use `make test-clear` to reset.

## Architecture

```
.claude/
├── commands/     # Slash commands (25) — user-invokable via /acc-*
├── agents/       # Subagents (50) — invoked via Task tool with subagent_type
├── skills/       # Skills (200) — knowledge bases, generators, analyzers
└── settings.json # Hooks and permission allowlist (NOT copied by plugin)

src/
└── ComposerPlugin.php  # Single PHP file — subscribes to POST_PACKAGE_INSTALL/UPDATE

bin/acc                 # CLI tool for force-upgrading components
docs/                   # commands.md, agents.md, skills.md, hooks.md, component-flow.md, mcp.md, quick-reference.md
tests/                  # Docker-based test environment (Dockerfile + docker-compose.yml + composer.json)
```

### Execution Flow

```
User → /acc-command → Coordinator Agent (opus) → Specialized Agents (sonnet, parallel via Task) → Skills → Output
```

**Three component types with strict integration chain:**

1. **Skill** provides knowledge or generates code (`.claude/skills/name/SKILL.md`, optionally `references/` subfolder)
2. **Agent** references skills via `skills:` frontmatter, performs analysis/generation
3. **Command** delegates to agents via the `Task` tool with `subagent_type="agent-name"`

### Agent Categories

- **Coordinators** (5): orchestrate multi-agent workflows via Task delegation, use `model: opus`, have `TaskCreate/TaskUpdate` for progress tracking — `bug-fix-coordinator`, `ci-coordinator`, `code-review-coordinator`, `docker-coordinator`, `refactor-coordinator`
- **Auditor-coordinators** (3): audit via sub-agent delegation, use `model: opus` — `architecture-auditor`, `pattern-auditor`, `ddd-auditor`
- **Specialists** (42): perform focused tasks, use `model: sonnet` — auditors, generators, reviewers, CI/Docker agents

### Composer Plugin

`src/ComposerPlugin.php` — the only PHP source file. Copies `.claude/{commands,agents,skills}` from vendor to project root. Skips existing files (prints "Skipping (exists)"). Files NOT copied: `settings.json`, `settings.local.json` — these are project-specific.

## Adding Components

### Command (`.claude/commands/acc-name.md`)

```yaml
---
description: Required (shown in /help)
allowed-tools: Optional (e.g. "Read, Grep, Glob, Bash, Task")
model: Optional (sonnet|haiku|opus — opus for coordinators)
argument-hint: Optional (e.g. "<path> [-- instructions]")
---
```

Commands parse `$ARGUMENTS` for input. The `--` separator passes meta-instructions. Always specify `model:` explicitly (`sonnet` for most, `opus` for coordinators).

### Agent (`.claude/agents/acc-name.md`)

```yaml
---
name: Required (matches filename without .md)
description: Required
tools: Optional (default: all tools)
model: Optional (default: sonnet)
skills: acc-skill-one, acc-skill-two
---
```

**Important**: `skills:` is a comma-separated inline list (not a YAML array). Skill names must match the skill folder name exactly.

For coordinators with 3+ phases: add `TaskCreate, TaskUpdate` to tools, include `acc-task-progress-knowledge` in skills.

### Skill (`.claude/skills/acc-name/SKILL.md`)

```yaml
---
name: Required (lowercase, hyphens, must match folder name)
description: Required (max 1024 chars)
---
```

Max 500 lines in SKILL.md — extract large content to `references/` subfolder.

## Key Rules

- **`acc-` prefix** on all components to avoid naming conflicts with other extensions
- **`--` separator** in commands for meta-instructions: `/acc-audit-ddd ./src -- focus on aggregates`
- **After any change**: run `make validate-claude`, update the matching `docs/*.md` file and `CHANGELOG.md`
- **Component counts** appear in 5 places — keep all in sync: `README.md` (Documentation table), `docs/quick-reference.md` (Statistics + file tree), `composer.json` (description), `llms.txt` (Quick Facts), `CHANGELOG.md`
- **File renames**: always use `git mv` instead of delete + create to preserve git history
- **CI/CD `acc-docker-agent`** (for CI pipelines) is separate from Docker Expert System agents (`acc-docker-coordinator`, `acc-docker-*-agent`) — do not merge them
- **`settings.json`** is project-specific (NOT copied by plugin). Contains: PostToolUse hook (`php -l` on `.php` files after Write), permissions allowlist (make, git read-only, composer validate, WebSearch)
- **Every skill must be referenced** by at least one agent's `skills:` frontmatter — orphaned skills cause audit failures

## Versioning

1. Update `CHANGELOG.md` with new section (format: `[X.Y.Z] - YYYY-MM-DD`)
2. Run `make validate-claude`
3. Update component counts in `README.md`, `docs/quick-reference.md`, `composer.json` if changed
4. Add comparison link at bottom of `CHANGELOG.md`
5. Run `make release` (validates + prints git tag instructions)

## Documentation Files

| File | What to Update |
|------|---------------|
| `docs/commands.md` | New/changed slash commands — overview table + detailed section |
| `docs/agents.md` | New/changed agents — category table + description section |
| `docs/skills.md` | New/changed skills — categorized by type (knowledge/analyzer/generator) |
| `docs/hooks.md` | New hooks for `settings.json` |
| `docs/component-flow.md` | Dependency graph when adding command→agent→skill chains |
| `docs/quick-reference.md` | Component counts, file structure diagram, statistics table |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Skill not loading | Missing from agent's `skills:` frontmatter | Add skill name to agent's comma-separated `skills:` list |
| Agent not invoked | Command uses wrong `subagent_type` | Match `subagent_type` to agent filename (without `.md`) |
| Validation fails | Frontmatter missing or malformed | Ensure file starts with `---` and has required fields |
| Plugin doesn't copy files | Plugin not allowed in Composer | Run `composer config allow-plugins.dykyi-roman/awesome-claude-code true` |
| Orphaned skill in audit | Skill folder exists but no agent references it | Add skill to appropriate agent's `skills:` frontmatter |
