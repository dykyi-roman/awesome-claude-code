---
description: Interactive wizard for creating Claude Code commands, agents, and skills. Use when you need to extend Claude Code capabilities.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: opus
argument-hint: [component-type] [-- additional instructions]
---

# Claude Code Creator

You are a master of creating Claude Code components.

## Input Parsing

Parse `$ARGUMENTS` to extract component type and optional meta-instructions:

```
Format: [component-type] [-- <meta-instructions>]

Examples:
- /acc-write-claude-component
- /acc-write-claude-component command
- /acc-write-claude-component agent -- for DDD auditing
- /acc-write-claude-component skill -- generates Value Objects
- /acc-write-claude-component ? -- я хочу автоматически форматировать код
- /acc-write-claude-component ? -- нужен аудит безопасности проекта
- /acc-write-claude-component hook -- validate PHP syntax before Write tool
- /acc-write-claude-component hook -- run prettier after file save
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **component type** (optional: command/agent/skill/hook/?)
3. Second part = **meta-instructions** (optional, hints about purpose)

**Discovery mode (`?`):**
If first part is `?`, enter discovery mode:
- Analyze meta-instructions to understand user's goal
- Recommend best component type with reasoning
- Show plan before proceeding

If component type provided (not `?`), skip Step 0-1 and go directly to Step 2.
If meta-instructions provided, use them to guide questions in Step 2.

## Process

### Step 0: Discovery Mode (if `?` provided)

If user passed `?` as component type:

1. **Analyze the goal** from meta-instructions:
   - What problem needs solving?
   - Is it automation, audit, generation, or workflow?
   - Does it need separate context (agent) or just instructions (skill)?
   - Should it trigger automatically (hook) or manually (command)?

2. **Recommend component type** with reasoning:

   | Goal Pattern | Recommended | Reason |
   |--------------|-------------|--------|
   | "автоматически при..." / "on save" / "before commit" | Hook | Triggered by events |
   | "проверять/аудит/валидация/analyze" | Command + Agent | Complex analysis needs separate context |
   | "генерировать/создавать/generate/create" | Command + Agent + Skills | Generation workflow |
   | "инструкции/справочник/knowledge/reference" | Skill | Reusable knowledge |
   | "простой workflow/quick action" | Command | Single saved prompt |

3. **Present plan**:
   ```
   📋 Recommendation Plan

   **Your goal:** {parsed from meta-instructions}

   **Recommended approach:**
   - Component type: {type}
   - Reason: {why this type fits}

   **What will be created:**
   - {list of files}

   **Alternative approaches:**
   - {other options if applicable}

   Proceed with this plan? [Yes/No/Modify]
   ```

4. If user confirms, proceed to Step 2 (Gather requirements) with component type pre-selected.
   If no meta-instructions provided, ask user to describe their goal first.

### Step 1: Ask user what to create

Offer options:
1. **command** — slash command (saved prompt/workflow)
2. **agent** — subagent (specialized assistant with separate context)
3. **skill** — skill (reusable instructions + resources)
4. **hook** — hook (automatic action on event)

Wait for selection.

### Step 2: Gather requirements

Depending on the choice, ask:

**For command:**
- Command name (becomes /name)
- What should it do?
- Are arguments needed ($ARGUMENTS)?
- Should it use agents?

**For agent:**
- Name and specialization
- What tasks does it solve?
- What tools are needed?
- Which model (sonnet/haiku/opus/inherit)?

**For skill:**
- Skill name
- When should Claude use it?
- What instructions/resources to include?
- Are scripts or templates needed?

**For hook:**
- Which event (PreToolUse/PostToolUse/etc)?
- Which tool to monitor?
- What to execute?

### Step 3: Create component

Use the acc-claude-code-expert agent to create a quality component.

Load the acc-claude-code-knowledge skill for access to formats and best practices.

### Step 4: Validation

Check the created file:
- YAML frontmatter is valid
- All required fields are filled
- File path is correct
- Description is specific and useful

### Step 5: Show result

Display:
- Created file
- How to use (example invocation)
- What can be improved
