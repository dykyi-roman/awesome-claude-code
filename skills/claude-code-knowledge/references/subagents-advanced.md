# Subagents Advanced Reference

Advanced subagent features: memory, hooks, permissions, background execution, resume.

## Built-in Subagent Types

| Type | Purpose | Tools | Model |
|------|---------|-------|-------|
| `Explore` | Fast codebase exploration | Glob, Grep, Read (no Write/Edit) | haiku |
| `Plan` | Design implementation plans | Read-only tools (no Write/Edit) | sonnet |
| `general-purpose` | Full-capability research | All tools except Task | sonnet |
| `Bash` | Command execution | Bash only | haiku |
| `statusline-setup` | Configure status line | Read, Edit | haiku |
| `claude-code-guide` | Claude Code documentation | Glob, Grep, Read, WebFetch, WebSearch | haiku |

**Custom agents:** `.claude/agents/name.md` — available as `subagent_type="name"`

## DisallowedTools Field

```yaml
---
name: safe-analyzer
description: Analyzer that cannot modify files
tools: Read, Grep, Glob, Bash, WebSearch, WebFetch
disallowedTools: Write, Edit, Task
---
```

**What `disallowedTools` does:**
- Denylist complement to `tools`
- If `tools` specifies an allowlist, `disallowedTools` is typically not needed
- Useful when you want "all tools except X"
- `disallowedTools` takes precedence if a tool appears in both lists

**When to use:**
- Agent needs most tools but must not write files → `disallowedTools: Write, Edit`
- Agent should not spawn sub-subagents → `disallowedTools: Task`

## Hooks Field

```yaml
---
name: validated-generator
description: Generator with validation hooks
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

**Agent-scoped hooks:**
- Only active when this agent is running
- Same format as settings.json hooks
- Support all 12 hook events
- Merged with global hooks (both run)

## Memory Field

```yaml
---
name: context-aware-agent
description: Agent with specific CLAUDE.md context
memory: project
---
```

**Memory scope options:**

| Value | Loads |
|-------|-------|
| `user` | `~/.claude/CLAUDE.md` only |
| `project` | Project `CLAUDE.md` + `.claude/rules/*.md` |
| `local` | `CLAUDE.local.md` + project + rules |
| (omitted) | All applicable CLAUDE.md files (default) |

**When to use:**
- `user` — agent should follow user preferences but ignore project rules
- `project` — agent should follow project standards only
- `local` — agent needs local overrides (machine-specific paths, etc.)

## Permission Modes

### Full Permission Mode List

| Mode | Behavior | Use Case |
|------|----------|----------|
| `default` | Ask user for each tool use | Interactive, careful work |
| `acceptEdits` | Auto-allow Read/Write/Edit, ask for Bash/Web | Trusted file operations |
| `plan` | Read-only, no file modifications | Analysis, exploration |
| `dontAsk` | Run without asking (within sandbox) | Automated pipelines |
| `delegate` | Inherit parent agent's permissions | Sub-subagent delegation |
| `bypassPermissions` | Skip all checks | **Dangerous** — only for trusted agents |

### Permission Mode Selection Guide

```
Need to modify files?
├── No → plan (read-only exploration)
├── Yes, carefully → default (ask each time)
├── Yes, trusted edits → acceptEdits (auto-allow files)
├── Yes, automated → dontAsk (sandbox required)
├── Yes, from parent → delegate (inherit parent)
└── Yes, everything → bypassPermissions (dangerous)
```

## Background Execution

### Foreground (Default)

```python
# Parent blocks until agent completes
Task(subagent_type="analyzer", prompt="Analyze code")
# Result available immediately
```

### Background

```python
# Parent continues while agent runs
Task(subagent_type="analyzer", prompt="Analyze code", run_in_background=True)
# Returns output_file path
# Check later with Read tool or TaskOutput
```

**Keyboard shortcut:** `Ctrl+B` — toggle background mode for running agent.

**Background agent behavior:**
- Runs independently of parent conversation
- Output stored in file (path returned in tool result)
- Check progress with `Read` tool on output file
- Multiple background agents can run concurrently

## Resume Capability

```python
# First invocation
result = Task(subagent_type="researcher", prompt="Research authentication patterns")
# result includes agent_id

# Later, resume with full context preserved
result = Task(subagent_type="researcher", resume="agent-id-from-before", prompt="Now focus on JWT specifically")
```

**Resume behavior:**
- Agent continues with full previous transcript preserved
- No need to repeat context or instructions
- New prompt is appended to existing conversation
- Same agent type must be used

## Auto-Compaction

Subagents have their own context windows. When context fills up:
1. Auto-compaction triggers (like main conversation)
2. Earlier messages are summarized
3. Recent context preserved
4. `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` controls threshold

## Agent Management

### /agents Command

- List all available custom agents
- Shows agent descriptions and tools
- Helps discover agents for Task tool

### CLI --agents Flag

```bash
claude --agents '{"my-agent": {"tools": ["Read", "Grep"], "model": "haiku"}}'
```

**CLI agent definitions override project/user agents with same name.**

## Scope Priority

Agent resolution order (first match wins):

1. **CLI `--agents` flag** — runtime overrides
2. **Project `.claude/agents/`** — project-specific
3. **User `~/.claude/agents/`** — user-wide
4. **Plugin agents** — from enabled plugins

## Permission Rules for Agents

In settings.json permissions:

```json
{
  "permissions": {
    "allow": ["Task(acc-ddd-auditor)", "Task(acc-test-generator)"],
    "deny": ["Task(acc-dangerous-agent)"]
  }
}
```

**`Task(agent-name)`** — controls which agents can be spawned.

## Subagent Transcript Storage

- Subagent conversations are stored in `.claude/` directory
- Transcripts include full tool call history
- Useful for debugging agent behavior
- Auto-cleaned based on session management settings

## Best Practices

1. **Choose the right built-in type** — Explore for search, Plan for design, general-purpose for complex tasks
2. **Minimize tools** — agents with fewer tools are faster and safer
3. **Use `plan` mode for auditors** — prevents accidental modifications
4. **Background for slow agents** — don't block parent conversation
5. **Resume for iterative work** — avoids re-explaining context
6. **Scope hooks to agents** — keeps global settings clean
7. **Test agents in isolation** — verify behavior before integration
8. **Use `delegate` for sub-subagents** — consistent permission inheritance
