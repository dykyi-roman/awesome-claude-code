---
description: Audit .claude folder structure, commands, agents, skills, and settings. Evaluates quality, identifies issues, and provides improvement recommendations.
allowed-tools: Read, Glob, Grep, Bash
model: opus
---

# Claude Code Configuration Audit

Perform a comprehensive audit of the `.claude/` folder in the current project.

## Pre-flight Check

1. Check if `.claude/` folder exists in the current working directory
2. If missing, skip to **Missing Configuration** section

## Audit Process

### Step 1: Scan Structure

Discover all components:

```
.claude/
├── commands/           # Slash commands (*.md)
├── agents/             # Custom agents (*.md)
├── skills/             # Skills (name/SKILL.md)
├── plans/              # Plan files
├── settings.json       # Project settings
├── settings.local.json # Local settings (gitignored)
├── CLAUDE.md           # Project instructions
└── README.md           # Documentation
```

Use Glob to find:
- `.claude/commands/*.md`
- `.claude/agents/*.md`
- `.claude/skills/*/SKILL.md`
- `.claude/settings.json`
- `.claude/settings.local.json`
- `.claude/CLAUDE.md`

### Step 2: Analyze Each Component

For each file found, evaluate against quality criteria:

#### Commands Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| YAML frontmatter | Valid, all fields | Missing optional fields | Invalid/missing |
| Description | Clear, specific | Too generic | Missing |
| Instructions | Step-by-step, clear | Vague steps | No instructions |
| $ARGUMENTS handling | Documented, validated | Used but not documented | Ignored |
| Tool restrictions | Appropriate for task | Too permissive | Missing when needed |

#### Agents Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| YAML frontmatter | name, description, tools | Missing optional | Invalid/missing |
| Name | Lowercase, hyphenated | Inconsistent casing | Invalid characters |
| Description | Specific purpose | Too generic | Missing |
| Tool restrictions | Minimal needed set | Missing restrictions | Overly broad |
| Skills reference | Links to skills | No skill usage | Broken references |

#### Skills Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| Location | name/SKILL.md structure | Flat file | Wrong location |
| YAML frontmatter | name, description | Missing fields | Invalid |
| Size | Under 500 lines | 500-1000 lines | Over 1000 lines |
| References | Large content in references/ | Everything in SKILL.md | Missing needed refs |
| Trigger conditions | Clear "when to use" | Vague triggers | No triggers |

#### Settings Quality Criteria

| Criterion | ✅ Good | ⚠️ Improve | ❌ Problem |
|-----------|---------|------------|------------|
| JSON validity | Valid JSON | - | Parse errors |
| Hooks | Defined and documented | Undocumented | Invalid format |
| Permissions | Explicit allow/deny | Implicit defaults | Overly permissive |
| Local settings | Gitignored properly | Not gitignored | Secrets exposed |

### Step 3: Check Cross-References

Verify integrity:
- Commands referencing agents → agents exist
- Agents referencing skills → skills exist
- Skills referencing other files → files exist

### Step 4: Detect Antipatterns

Common issues to flag:

1. **Duplicate functionality** — Multiple commands doing similar things
2. **Missing descriptions** — Components without clear purpose
3. **Hardcoded paths** — Paths that won't work in other projects
4. **Overly long files** — Skills over 500 lines, commands over 200 lines
5. **No tool restrictions** — Commands/agents with unlimited tool access
6. **Inconsistent naming** — Mixed naming conventions
7. **Missing error handling** — Commands without pre-flight checks
8. **Secrets in settings** — API keys or sensitive data in versioned files

## Output Format

Generate a structured markdown report:

### 1. Overview

```
📁 .claude/ Audit Report
========================

📊 Summary
├── Commands:  X found (Y issues)
├── Agents:    X found (Y issues)
├── Skills:    X found (Y issues)
├── Settings:  X files (Y issues)
└── Total issues: X critical, Y warnings, Z suggestions
```

### 2. File Tree

Show discovered structure with status indicators:
```
.claude/
├── commands/
│   ├── ✅ acc-commit.md
│   ├── ⚠️ my-command.md (missing description)
│   └── ❌ broken.md (invalid YAML)
├── agents/
│   └── ✅ my-agent.md
├── skills/
│   └── ⚠️ my-skill/SKILL.md (too long: 800 lines)
└── ✅ settings.json
```

### 3. Detailed Analysis

For each file with issues:

```markdown
#### ⚠️ commands/my-command.md

**Issues:**
- Missing `description` in frontmatter
- No $ARGUMENTS validation
- Uses Bash without restriction

**Current:**
```yaml
---
allowed-tools: Bash
---
```

**Recommended:**
```yaml
---
description: Brief description of what this command does
allowed-tools: Bash, Read
argument-hint: <required-argument>
---

## Pre-flight Check
Validate $ARGUMENTS before proceeding...
```
```

### 4. Recommendations

Prioritized action items:

| Priority | File | Issue | Fix |
|----------|------|-------|-----|
| ❌ Critical | broken.md | Invalid YAML | Fix frontmatter syntax |
| ⚠️ High | my-command.md | No description | Add description field |
| 💡 Suggestion | settings.json | No hooks | Consider adding pre-commit hook |

### 5. Quick Fixes

Ready-to-apply fixes for common issues:

```markdown
**Fix: Add missing description to my-command.md**
Add this to the YAML frontmatter:
description: [Describe what this command does and when to use it]
```

## Missing Configuration

If `.claude/` folder is missing or empty, provide starter template:

```markdown
## Recommended Structure

Your project is missing Claude Code configuration. Here's a starter setup:

### 1. Create basic structure

```bash
mkdir -p .claude/commands .claude/agents .claude/skills
```

### 2. Create CLAUDE.md

```markdown
# CLAUDE.md

## Project Overview
[Describe your project]

## Architecture
[Key patterns and structures]

## Commands
- `make test` — run tests
- `make lint` — check code style
```

### 3. Create settings.json

```json
{
  "hooks": {
    "PreToolUse": []
  },
  "permissions": {
    "allow": [],
    "deny": []
  }
}
```

### 4. Add to .gitignore

```
.claude/settings.local.json
```
```

## Usage

```bash
/acc-claude-code-audit
```
