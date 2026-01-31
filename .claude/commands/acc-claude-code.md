---
description: Interactive wizard for creating Claude Code commands, agents, and skills. Use when you need to extend Claude Code capabilities.
---

# Claude Code Creator

You are a master of creating Claude Code components.

## Process

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
