# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code marketplace plugin providing extensions for PHP development with DDD, CQRS, and Clean Architecture patterns. Current version: **v3.3.0**. Installed via:

```bash
/plugin marketplace add dykyi-roman/awesome-claude-code
/plugin install acc@awesome-claude-code
```

## Commands

```bash
make help                   # Show all available make targets (default)
make validate-claude        # Validate plugin structure — run before every commit
make list-commands          # List all slash commands
make list-agents            # List all agents
make list-skills            # List all skills
make changelog              # Show recent git commits for changelog
make release                # Run validate-claude, then print release instructions
```

## Architecture

```
.claude-plugin/
├── marketplace.json
└── plugin.json

commands/          # 26 commands (was .claude/commands/) — user-invokable via /acc:*
agents/            # 68 agents (was .claude/agents/) — invoked via Task tool with subagent_type
skills/            # 283 skills (was .claude/skills/) — 53 knowledge, 107 analyzer, 99 generator, 7 optimizer, 10 template, 7 other

hooks/
└── hooks.json     # PHP syntax check hook (the only hook shipped; docs/hooks.md holds 21 recipes)

scripts/
└── validate.py    # the real gate — run by `make validate-claude` (NOT part of plugin)

evals/             # behavioural regression cases for `claude plugin eval` (NOT part of plugin)
.github/workflows/ # CI (NOT part of plugin)

.claude/
├── settings.json  # Project settings (NOT part of plugin)
└── rules/         # Conditional rules (NOT part of plugin)

docs/              # commands.md, agents.md, skills.md, hooks.md, component-flow.md, mcp.md, quick-reference.md
llms.txt           # LLM-readable project summary (sync counts with other docs)
```

### Validation

`make validate-claude` runs `scripts/validate.py` and then the official CLI. The two are
complementary — measured on this repo, `claude plugin validate --strict` does **not** catch an
invalid `model:`, an empty `description`, a broken `skills:` reference, or a `name` that does not
match the filename. `scripts/validate.py` does, and it fails the build, so `make release` can no
longer print "All checks passed!" over a broken component.

Grep-pattern problems (lookaround, backreferences, BRE `\|` — none of which ripgrep executes) are
currently reported as **warnings**: 123 pre-existing occurrences are scheduled for the grep audit.
Turn them into errors in `check_grep_patterns_executable` once that work lands.

### Execution Flow

```
User → /acc:command → Coordinator Agent (opus) → Specialized Agents (sonnet, parallel via Task) → Skills → Output
```

**Three component types with strict integration chain:**

1. **Skill** provides knowledge or generates code (`skills/name/SKILL.md`, optionally `references/` subfolder)
2. **Agent** references skills via `skills:` frontmatter (bare names, no `acc:` prefix), performs analysis/generation
3. **Command** delegates to agents via the `Task` tool with `subagent_type="acc:agent-name"`

### Agent Categories

- **Coordinators** (6): orchestrate multi-agent workflows via Task delegation, use `model: opus`, have `TaskCreate/TaskUpdate` for progress tracking — `bug-fix-coordinator`, `ci-coordinator`, `code-review-coordinator`, `docker-coordinator`, `explain-coordinator`, `refactor-coordinator`
- **Auditor-coordinators** (4): audit via sub-agent delegation, use `model: opus` — `architecture-auditor`, `pattern-auditor`, `ddd-auditor`, `security-reviewer`
- **Specialists** (58): perform focused tasks — 31 use `model: sonnet` (generators, CI/Docker agents), 27 use `model: opus` (sub-auditors, reviewers, analysts requiring higher quality)

## Key Rules

- **`acc:` namespace** on all plugin components to avoid naming conflicts with other extensions
- **`--` separator** in commands for meta-instructions: `/acc:audit-ddd ./src -- focus on aggregates`
- **After any change**: run `make validate-claude`, update the matching `docs/*.md` file and `CHANGELOG.md`
- **Component counts** appear in 6 places — keep all in sync: `README.md` (Documentation table), `docs/quick-reference.md` (Statistics + file tree), `.claude-plugin/marketplace.json` (plugin description), `llms.txt` (Quick Facts + Project Structure + Skills by Category), `CHANGELOG.md`, `CLAUDE.md` (Architecture section)
- **File renames**: always use `git mv` instead of delete + create to preserve git history
- **CI/CD `docker-agent`** (for CI pipelines) is separate from Docker Expert System agents (`docker-coordinator`, `docker-*-agent`) — do not merge them
- **Every skill must be referenced** by at least one agent's `skills:` frontmatter — orphaned skills cause audit failures

## Conditional Rules

`.claude/rules/` contains context-specific rules for development only, loaded when matching files are involved:

- `component-creation.md` — command/agent/skill frontmatter specs (loads for plugin component edits)
- `versioning.md` — versioning workflow and documentation files table (loads for CHANGELOG, README, docs/)
- `troubleshooting.md` — diagnostic table for common issues (loads for plugin components, Makefile)
