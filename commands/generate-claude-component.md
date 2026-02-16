---
description: Interactive wizard for creating Claude Code commands, agents, skills, hooks, rules, and plugins. Use when you need to extend Claude Code capabilities.
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
- /acc-generate-claude-component
- /acc-generate-claude-component command
- /acc-generate-claude-component agent -- for DDD auditing
- /acc-generate-claude-component skill -- generates Value Objects
- /acc-generate-claude-component ? -- I want to auto-format code
- /acc-generate-claude-component ? -- need a security audit
- /acc-generate-claude-component hook -- validate PHP syntax before Write tool
- /acc-generate-claude-component rule -- domain layer must be pure
- /acc-generate-claude-component plugin -- package DDD tools for distribution
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **component type** (optional: command/agent/skill/hook/rule/plugin/?)
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
   - Is it project-wide instruction (rule) or distributable package (plugin)?

2. **Recommend component type** with reasoning:

   | Goal Pattern | Recommended | Reason |
   |--------------|-------------|--------|
   | "automatically when..." / "on save" / "before commit" | Hook | Triggered by events, zero context cost |
   | "check/audit/validate/analyze" | Command + Agent | Complex analysis needs separate context |
   | "generate/create/write" | Command + Agent + Skills | Generation workflow |
   | "instructions/reference/knowledge" | Skill | Reusable knowledge |
   | "simple workflow/quick action" | Command | Single saved prompt |
   | "always follow these rules" / "project standard" | Rule | Always in system prompt |
   | "share with team" / "distribute" / "package" | Plugin | Namespaced, installable |
   | "external API/tool integration" | MCP config | Standardized protocol |

3. **Present plan**:
   ```
   Recommendation Plan

   **Your goal:** {parsed from meta-instructions}

   **Recommended approach:**
   - Component type: {type}
   - Reason: {why this type fits}

   **What will be created:**
   - {list of files}

   **Alternative approaches:**
   - {other options if applicable}

   **Context cost:** {impact on context window}

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
5. **rule** — rule file (`.claude/rules/*.md`, always loaded instruction)
6. **plugin** — plugin (distributable extension package)

Wait for selection.

### Step 2: Gather requirements

Depending on the choice, ask:

**For command:**
- Command name (becomes /name)
- What should it do?
- Are arguments needed ($ARGUMENTS)?
- Should it use agents?
- Model preference (opus for complex, sonnet default, haiku for fast)?

**For agent:**
- Name and specialization
- What tasks does it solve?
- What tools are needed? Any tools to disallow (`disallowedTools`)?
- Which model (sonnet/haiku/opus/inherit)?
- Permission mode (default/acceptEdits/plan/dontAsk/delegate)?
- Should it load specific CLAUDE.md scope (`memory` field)?
- Does it need scoped hooks (`hooks` field)?
- Is it a coordinator (orchestrates other agents)?
  - If yes: add TaskCreate, TaskUpdate to tools
  - Add acc-task-progress-knowledge to skills
  - Add "Progress Tracking" section with 3-5 phases

**For skill:**
- Skill name
- When should Claude use it?
- What instructions/resources to include?
- Are scripts or templates needed?
- Should it run in isolated context (`context: fork`)?
- Model override needed (`model` field)?
- Should it have scoped hooks (`hooks` field)?
- Which agent type should it run in (`agent` field)?
- Invocation control: user-only, Claude-only, or both?

**For hook:**
- Which event? (12 available: PreToolUse, PostToolUse, Notification, Stop, SubagentStop, PreCompact, PostCompact, ToolError, PreUserInput, PostUserInput, SessionStart, SessionEnd)
- Which hook type? (command/prompt/agent)
- Matcher pattern (tool name, regex, `|` OR)?
- What should execute?
- Async or blocking?
- Should it control decisions (allow/block/ask)?
- Hook scope: global (settings.json), agent frontmatter, or skill frontmatter?

**For rule:**
- Rule topic (coding standards, architecture, security, etc.)
- Should it be path-specific? If yes, which glob patterns?
- User-level (`~/.claude/rules/`) or project-level (`.claude/rules/`)?
- Content: specific instructions, not general advice

**For plugin:**
- Plugin name and purpose
- Which components to include (commands, agents, skills, hooks)?
- MCP server needed?
- Distribution method (GitHub, NPM, directory)?
- Namespace prefix for components

### Step 3: Create component

Use the acc-claude-code-expert agent to create a quality component.

Load the acc-claude-code-knowledge skill for access to formats and best practices.

**For coordinator agents (orchestrates multiple agents):**

1. Add `TaskCreate, TaskUpdate` to tools in frontmatter
2. Add `acc-task-progress-knowledge` to skills
3. Add "Progress Tracking" section with pattern:

```markdown
## Progress Tracking

Before executing workflow, create tasks for user visibility:

```
TaskCreate: subject="Phase 1 name", description="What happens", activeForm="Doing phase 1..."
TaskCreate: subject="Phase 2 name", description="What happens", activeForm="Doing phase 2..."
TaskCreate: subject="Phase 3 name", description="What happens", activeForm="Doing phase 3..."
```

For each phase:
1. `TaskUpdate(taskId, status: in_progress)` — before starting
2. ... execute phase work ...
3. `TaskUpdate(taskId, status: completed)` — after finishing
```

**Phase naming guidelines:**
- 3-5 major phases per coordinator
- `subject` — imperative form (e.g., "Diagnose bug")
- `activeForm` — present continuous (e.g., "Diagnosing bug...")
- `description` — brief explanation of what happens

**For plugins:**

1. Create `.claude-plugin/plugin.json` manifest
2. Create component directories (commands/, agents/, skills/)
3. Remove namespace prefixes (plugin namespace handles it)
4. Add hooks/hooks.json if hooks needed
5. Add .mcp.json if MCP server needed
6. Test with `claude --plugin-dir ./plugin-dir`

**For rules:**

1. Create `.claude/rules/name.md` (or `~/.claude/rules/` for user-level)
2. Add `paths` frontmatter if path-specific
3. Keep instructions specific and actionable
4. Verify rule doesn't conflict with existing rules

### Step 4: Validation

Check the created file:
- YAML frontmatter is valid
- All required fields are filled
- File path is correct
- Description is specific and useful
- New fields used correctly (disallowedTools, hooks, memory, context, agent, model)
- For hooks: event name is valid (12 events), type is valid (3 types)
- For rules: paths use valid glob patterns
- For plugins: manifest has required fields

### Step 5: Show result

Display:
- Created file
- How to use (example invocation)
- Context cost impact
- What can be improved
