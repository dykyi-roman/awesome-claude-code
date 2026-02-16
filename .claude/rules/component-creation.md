---
paths:
  - commands/*.md
  - agents/*.md
  - skills/**/SKILL.md
---

# Adding Components

## Command (`commands/name.md`)

```yaml
---
description: Required (shown in /help)
allowed-tools: Optional (e.g. "Read, Grep, Glob, Bash, Task")
model: Optional (sonnet|haiku|opus — opus for coordinators)
argument-hint: Optional (e.g. "<path> [-- instructions]")
---
```

Commands parse `$ARGUMENTS` for input. The `--` separator passes meta-instructions. Always specify `model:` explicitly (`sonnet` for most, `opus` for coordinators).

## Agent (`agents/name.md`)

```yaml
---
name: Required (matches filename without .md)
description: Required
tools: Optional (default: all tools)
model: Optional (default: opus)
skills: skill-one, skill-two
---
```

**Important**: `skills:` is a comma-separated inline list (not a YAML array). Skill names must match the skill folder name exactly (without any prefix).

For coordinators with 3+ phases: add `TaskCreate, TaskUpdate` to tools, include `task-progress-knowledge` in skills.

## Skill (`skills/name/SKILL.md`)

```yaml
---
name: Required (lowercase, hyphens, must match folder name)
description: Required (max 1024 chars)
---
```

Max 500 lines in SKILL.md — extract large content to `references/` subfolder.
