# Skills Advanced Reference

Advanced skill features beyond basic SKILL.md format.

## Context Fork

```yaml
---
name: isolated-analyzer
description: Runs analysis in isolated context
context: fork
---
```

**What `context: fork` does:**
- Skill executes in a fresh subagent context
- Parent context is not polluted with skill's intermediate work
- Only the final result is returned to parent
- Useful for skills that read many files or produce large intermediate output

**When to use:**
- Large codebase analysis that would fill parent context
- Skills that generate verbose intermediate steps
- Isolation from parent conversation state

## Agent Field

```yaml
---
name: deep-researcher
description: Deep research using Explore agent
agent: Explore
---
```

**What `agent` field does:**
- Skill runs inside the specified subagent type
- Inherits that agent type's tools and capabilities
- Useful for leveraging built-in agent specializations

**Available agent types:**
- `Explore` — fast codebase exploration (Glob, Grep, Read)
- `Plan` — planning mode (read-only, no writes)
- `general-purpose` — full capabilities
- Custom agent name from `.claude/agents/`

## Model Override

```yaml
---
name: quick-check
description: Fast validation check
model: haiku
---
```

**What `model` field does:**
- Overrides the model when this skill is active
- Applies to the skill's execution context
- Useful for cost/speed optimization

**Model choices:**
- `haiku` — fastest, cheapest, good for simple checks
- `sonnet` — balanced, good for most tasks
- `opus` — most capable, for complex reasoning

## Hooks Field

```yaml
---
name: guarded-generator
description: Generator with pre/post hooks
hooks:
  PreToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "php -l $CLAUDE_FILE_PATH"
  PostToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "php-cs-fixer fix $CLAUDE_FILE_PATH --quiet"
          async: true
---
```

**What `hooks` field does:**
- Defines lifecycle hooks scoped to this skill only
- Hooks activate when skill is loaded, deactivate when skill completes
- Same format as settings.json hooks

## Dynamic Context Injection

```markdown
Current PHP version: !`php -v | head -1`

Project dependencies:
!`composer show --direct 2>/dev/null | head -20`
```

**What `!`command`` does:**
- Executes shell command at skill load time
- Inserts stdout into skill content
- Enables dynamic, project-aware instructions

**Use cases:**
- Detect runtime environment (PHP version, OS)
- List project dependencies
- Check git status
- Read dynamic configuration

**Limitations:**
- Runs synchronously during skill loading
- Output is inserted as plain text
- Failed commands insert error output
- Keep commands fast (< 1 second)

## Argument Patterns

### Positional Arguments

```markdown
# File Analyzer

Analyze file: $ARGUMENTS[0]
Focus on: $ARGUMENTS[1]

Shorthand equivalents:
- $1 = $ARGUMENTS[0]
- $2 = $ARGUMENTS[1]
```

### Full Argument String

```markdown
# Code Review

Review the following: $ARGUMENTS
```

### Session Variable

```markdown
# Session Logger

Session: ${CLAUDE_SESSION_ID}
Log to: /tmp/claude-${CLAUDE_SESSION_ID}.log
```

## Invocation Control

### Invocation Control Matrix

| `disable-model-invocation` | `user-invocable` | Result |
|---------------------------|------------------|--------|
| `false` (default) | `true` (default) | **Both** — user via `/name`, Claude auto-loads |
| `true` | `true` | **User only** — `/name` invocation, Claude cannot auto-load |
| `false` | `false` | **Claude only** — auto-loaded by agents, not in `/` menu |
| `true` | `false` | **Disabled** — nobody can invoke |

### When to Use Each Mode

- **Both (default):** General knowledge skills, most skills
- **User only:** Dangerous operations, cost-heavy skills, one-time wizards
- **Claude only:** Internal knowledge bases, agent-specific helpers
- **Disabled:** Deprecated skills awaiting removal

## Skill Character Budget

The `SLASH_COMMAND_TOOL_CHAR_BUDGET` environment variable controls max characters loaded from a skill.

- **Default:** 15000 characters
- **Override:** Set in environment or settings
- Skills exceeding budget are truncated
- Use `references/` to keep SKILL.md under budget

## Supporting Files

### References Directory

```
skill-name/
├── SKILL.md              # Main instructions (< 500 lines)
└── references/
    ├── patterns.md       # Detailed patterns
    ├── examples.md       # Code examples
    └── checklist.md      # Validation checklist
```

**Loading behavior:**
- SKILL.md is loaded automatically
- Reference files are loaded when Claude reads them (via links in SKILL.md)
- Progressive disclosure — keeps initial context small

### Scripts Directory

```
skill-name/
├── SKILL.md
└── scripts/
    ├── analyze.sh        # Analysis script
    └── generate.py       # Code generator
```

**Scripts are executed via Bash tool**, not loaded into context. Ideal for:
- Code generation templates
- Analysis tools
- Validation scripts

### Assets Directory

```
skill-name/
├── SKILL.md
└── assets/
    ├── template.php      # PHP template
    └── config.json       # Default config
```

**Assets are read or copied**, not executed. Ideal for:
- File templates
- Default configurations
- Static resources

## Skill vs Command Equivalence

Skills and commands are interchangeable:

| Feature | Command | Skill |
|---------|---------|-------|
| Path | `.claude/commands/name.md` | `.claude/skills/name/SKILL.md` |
| User invocation | `/name` | `/name` (if `user-invocable: true`) |
| Auto-load by Claude | No | Yes (by description match) |
| Folder structure | Single file | Folder with references/scripts/assets |
| Argument access | `$ARGUMENTS` | `$ARGUMENTS` |

**When to use command:** Simple saved prompts, user-facing workflows.
**When to use skill:** Knowledge bases, reusable across agents, needs supporting files.
