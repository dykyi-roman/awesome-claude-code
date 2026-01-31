# Claude Code Components

Detailed documentation for commands, agents, and skills.

## Table of Contents

- [Commands](#commands)
- [Agents](#agents)
- [Skills](#skills)
- [File Structure](#file-structure)
- [Quick Reference](#quick-reference)

---

## Commands

### `/acc-claude-code`

**Path:** `commands/acc-claude-code.md`

Interactive wizard for creating Claude Code components.

**Usage:**
```
/acc-claude-code
```

**Process:**
1. Asks what to create (command/agent/skill/hook)
2. Gathers requirements through questions
3. Uses `acc-claude-code-expert` agent with `acc-claude-code-knowledge` skill
4. Creates component with proper structure
5. Validates and shows result

**Example:**
```
> /acc-claude-code

What would you like to create?
1. command — slash command
2. agent — subagent
3. skill — skill
4. hook — hook

> 1

Command name?
> review

What should it do?
> Code review for file

Created: .claude/commands/review.md
```

---

## Agents

### `acc-claude-code-expert`

**Path:** `agents/acc-claude-code-expert.md`

Expert in creating Claude Code commands, agents, and skills.

**Configuration:**
```yaml
name: acc-claude-code-expert
tools: Read, Write, Edit, Bash, Grep, Glob
model: sonnet
skills: acc-claude-code-knowledge
```

**Capabilities:**
- Knows Claude Code file structure and formats
- Follows best practices for component creation
- Auto-loads knowledge base skill

**Invocation:**
- Automatic: "PROACTIVELY" in description
- Manual: "Use acc-claude-code-expert agent for..."

---

## Skills

### `acc-claude-code-knowledge`

**Path:** `skills/acc-claude-code-knowledge/SKILL.md`

Knowledge base for Claude Code formats and patterns.

**Contents:**

1. **Format Reference**
   - Commands format
   - Agents format
   - Skills format
   - Hooks format

2. **Examples**
   - Good command examples
   - Good agent examples
   - Skill with resources

3. **Patterns**
   - Parallel Agents
   - Progressive Disclosure
   - Chained Agents

4. **Validation Checklists**
   - Commands checklist
   - Agents checklist
   - Skills checklist
   - Hooks checklist

---

## File Structure

```
.claude/
├── commands/
│   └── acc-claude-code.md          # /acc-claude-code wizard
├── agents/
│   └── acc-claude-code-expert.md       # Expert agent
├── skills/
│   └── acc-claude-code-knowledge/
│       └── SKILL.md                # Knowledge base
└── README.md                       # This file
```

---

## Quick Reference

### Component Paths

| Type    | Path                           | Invocation       |
|---------|--------------------------------|------------------|
| Command | `.claude/commands/name.md`     | `/name`          |
| Agent   | `.claude/agents/name.md`       | Auto or explicit |
| Skill   | `.claude/skills/name/SKILL.md` | `/name` or auto  |
| Hook    | `.claude/settings.json`        | On event         |

### YAML Frontmatter

**Command:**
```yaml
---
description: Required
allowed-tools: Optional
model: Optional (sonnet/haiku/opus)
argument-hint: Optional
---
```

**Agent:**
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

**Skill:**
```yaml
---
name: Required (lowercase, hyphens)
description: Required (max 1024 chars)
allowed-tools: Optional
---
```

### Best Practices

1. **Specific descriptions** — not "helps with code" but "analyzes Python for vulnerabilities"
2. **PROACTIVELY keyword** — triggers automatic agent invocation
3. **Minimal tools** — only what's needed
4. **Skills < 500 lines** — use references/ for details
5. **Test in isolation** — verify before integration
