# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Composer plugin providing Claude Code extensions (commands, agents, skills) for PHP development. On `composer require dykyi-roman/awesome-claude-code`, components auto-copy to the project's `.claude/` directory without overwriting existing files.

## Commands

```bash
make help              # Show all available commands
make list-commands     # List slash commands
make list-skills       # List skills
make list-agents       # List agents
make validate-claude   # Validate .claude structure
make test              # Install in test environment (tests/)
make test-clear        # Clear test environment
make release           # Prepare release (run checks)
```

## Architecture

### Composer Plugin

`src/ComposerPlugin.php` subscribes to `POST_PACKAGE_INSTALL` and `POST_PACKAGE_UPDATE` events. Copies `.claude/{commands,agents,skills}/` to target project. Existing files are never overwritten.

### Component Structure

```
.claude/
├── commands/           # Slash commands (/name invokes name.md)
├── agents/             # Subagents with YAML frontmatter
├── skills/             # Skills in name/SKILL.md format
│   └── name/
│       ├── SKILL.md    # Skill definition
│       └── references/ # Detailed documentation
└── settings.json       # Hooks and permissions
```

### Component Flow

```
COMMANDS                    AGENTS                      SKILLS
────────                    ──────                      ──────
/acc-commit ────────────→ (direct Bash)

/acc-claude-code ───────→ acc-claude-code-expert ───→ acc-claude-code-knowledge

/acc-ddd-audit ─────────→ acc-ddd-auditor ──────────→ acc-ddd-knowledge
                                │
                                └──→ (Task) acc-ddd-generator ──→ 13 create-* skills

/acc-architecture-audit ─→ acc-architecture-auditor ─→ 10 knowledge skills
                                │
                                ├──→ (Task) acc-ddd-generator ──→ 13 create-* skills
                                └──→ (Task) acc-pattern-generator → 15 create-* skills
```

See [.claude/README.md](.claude/README.md) for detailed component documentation.

## Component Formats

### Commands (`.claude/commands/*.md`)

```yaml
---
description: Required. When to use this command.
allowed-tools: Optional. Comma-separated tool names.
model: Optional. sonnet/haiku/opus
argument-hint: Optional. Hint for arguments.
---

Instructions. Use $ARGUMENTS for user input.
```

### Agents (`.claude/agents/*.md`)

```yaml
---
name: required-name
description: Required. Include "PROACTIVELY" for auto-invocation.
tools: Optional. Default: all tools.
model: Optional. Default: sonnet.
skills: Optional. Auto-load skills.
---

Agent prompt.
```

### Skills (`.claude/skills/name/SKILL.md`)

```yaml
---
name: lowercase-with-hyphens
description: Required. Max 1024 chars.
---

Skill instructions. Keep under 500 lines.
Use references/ folder for detailed documentation.
```

## Naming Convention

All components use `acc-` prefix (Awesome Claude Code) to avoid conflicts with user components.

## Component Integration Rules

When adding new components, verify proper integration in the component chain:

### After Adding a Skill
1. **Verify agent usage** - ensure skill is listed in relevant agent's `skills:` frontmatter
2. Check if skill should be used by:
   - `acc-ddd-generator` (for DDD create-* skills)
   - `acc-pattern-generator` (for pattern create-* skills)
   - `acc-ddd-auditor` (for DDD knowledge skills)
   - `acc-architecture-auditor` (for architecture knowledge skills)
   - `acc-pattern-auditor` (for pattern knowledge skills)

### After Adding an Agent
1. **Verify command usage** - ensure agent is invoked by relevant command via `Task` tool
2. Check if agent should be called from:
   - `/acc-ddd-audit` → `acc-ddd-auditor`, `acc-ddd-generator`
   - `/acc-architecture-audit` → `acc-architecture-auditor`, `acc-ddd-generator`, `acc-pattern-generator`
   - `/acc-claude-code` → `acc-claude-code-expert`

### Integration Checklist
```
Skill → Agent (skills: frontmatter) → Command (Task tool call)
```

## Documentation Updates

When adding, removing, or modifying components, **always update documentation**:

| Change | Update |
|--------|--------|
| Add/remove command | `.claude/README.md`, `README.md` |
| Add/remove agent | `.claude/README.md`, `README.md` |
| Add/remove skill | `.claude/README.md`, `README.md` |
| Change component flow | `.claude/README.md`, `CLAUDE.md` |

**Checklist:**
1. Update component tables in both README files
2. Update statistics (counts) in `.claude/README.md`
3. Update file structure tree in `.claude/README.md`
4. Update dependency graph if flow changes
5. **Verify skill is used in correct agents**
6. **Verify agent is called from correct commands**

## Testing

```bash
# Install in test environment (uses Docker)
make test

# Check installed components
ls -la tests/.claude/

# Clean up
make test-clear
```

Test environment uses Docker with PHP-FPM. See `tests/docker-compose.yml`.
