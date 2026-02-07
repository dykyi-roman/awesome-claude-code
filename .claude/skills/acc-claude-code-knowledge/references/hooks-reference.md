# Hooks Reference

Comprehensive guide to Claude Code hooks — automatic actions triggered by events.

## Hook Locations (6 Scopes)

| Scope | Location | Priority |
|-------|----------|----------|
| Managed | Enterprise system dirs | Highest |
| User | `~/.claude/settings.json` | |
| Project | `.claude/settings.json` | |
| Local | `.claude/settings.local.json` | |
| Agent frontmatter | `.claude/agents/*.md` `hooks:` field | |
| Skill frontmatter | `.claude/skills/*/SKILL.md` `hooks:` field | Lowest |

Hooks from all scopes are merged and all run for matching events.

## All 12 Hook Events

### PreToolUse

**When:** Before any tool execution
**Matcher:** Tool name (Bash, Write, Edit, Read, Glob, Grep, WebFetch, WebSearch, Task, mcp__server__tool)
**Can block:** Yes (exit code 2)
**JSON input (stdin):**
```json
{
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/path/to/file.php",
    "content": "..."
  },
  "session_id": "abc123"
}
```
**JSON output (stdout):** `{"decision": "allow"}`, `{"decision": "block", "reason": "..."}`, or `{"decision": "ask", "message": "..."}`

**Common uses:** syntax validation, file protection, security checks, format enforcement.

### PostToolUse

**When:** After tool execution completes
**Matcher:** Tool name
**Can block:** No
**JSON input (stdin):**
```json
{
  "tool_name": "Write",
  "tool_input": {"file_path": "/path/to/file.php", "content": "..."},
  "tool_output": {"success": true},
  "session_id": "abc123"
}
```

**Common uses:** auto-formatting, logging, notifications, test running.

### Notification

**When:** Claude sends a notification (e.g., task completion)
**Matcher:** None
**Can block:** No
**JSON input:** `{"message": "Task completed", "session_id": "abc123"}`

**Common uses:** desktop notifications, Slack/email alerts, sound alerts.

### Stop

**When:** Main agent stops (conversation ends or user interrupts)
**Matcher:** None
**Can block:** No
**JSON input:** `{"reason": "completed", "session_id": "abc123"}`

**Common uses:** cleanup, final reports, session logging.

### SubagentStop

**When:** A subagent (Task) completes
**Matcher:** Agent name
**Can block:** No
**JSON input:** `{"agent_name": "acc-ddd-auditor", "result": "...", "session_id": "abc123"}`

**Common uses:** result aggregation, progress tracking, chaining.

### PreCompact

**When:** Before context window compaction (auto-trim of long conversations)
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123", "context_usage_percent": 85}`

**Common uses:** save important context, create checkpoints.

### PostCompact

**When:** After context compaction completes
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123", "tokens_before": 180000, "tokens_after": 90000}`

**Common uses:** restore state, log compaction stats.

### ToolError

**When:** A tool execution fails with an error
**Matcher:** Tool name
**Can block:** No
**JSON input:** `{"tool_name": "Bash", "error": "Command failed with exit code 1", "session_id": "abc123"}`

**Common uses:** error reporting, auto-retry logic, alerting.

### PreUserInput

**When:** Before user message is processed
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123"}`

**Common uses:** context preparation, state loading.

### PostUserInput

**When:** After user message is processed
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123"}`

**Common uses:** logging, analytics.

### SessionStart

**When:** New session begins
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123", "project_dir": "/path/to/project"}`

**Common uses:** environment setup, welcome messages, state initialization.

### SessionEnd

**When:** Session ends
**Matcher:** None
**Can block:** No
**JSON input:** `{"session_id": "abc123"}`

**Common uses:** cleanup, reporting, state persistence.

## Hook Types

### Command Hook

Executes a shell command. Most common type.

```json
{
  "type": "command",
  "command": "php -l \"$CLAUDE_FILE_PATH\"",
  "async": false,
  "timeout": 30000
}
```

**Environment variables available:**
- `$CLAUDE_PROJECT_DIR` — project root directory
- `$CLAUDE_SESSION_ID` — current session identifier
- `$CLAUDE_FILE_PATH` — file path (for file-related tool events)
- `$CLAUDE_TOOL_NAME` — tool name that triggered the hook

**Exit codes:**
- `0` — success/allow
- `2` — block (PreToolUse only, denies the tool use)
- Other — warning logged, execution continues

### Prompt Hook

Sends a prompt to Claude for evaluation. Uses LLM context.

```json
{
  "type": "prompt",
  "prompt": "Review this file change for security issues. If unsafe, respond with BLOCK."
}
```

**When to use:** complex validation requiring LLM reasoning, content analysis, semantic checks.

**Context cost:** Uses tokens from context window. Avoid for frequent events.

### Agent Hook

Delegates to a subagent for evaluation.

```json
{
  "type": "agent",
  "agent": "security-validator"
}
```

**When to use:** complex multi-step validation, when you need tool access during validation.

**Context cost:** Runs in separate context (no parent cost), but slower.

## Async Hooks

```json
{
  "type": "command",
  "command": "./notify.sh",
  "async": true
}
```

**Async hooks:**
- Run in background, don't block execution
- Cannot return decisions (allow/block/ask)
- Ideal for logging, notifications, analytics
- Multiple async hooks run concurrently

## Matcher Patterns

| Pattern | Matches |
|---------|---------|
| `"Bash"` | Only Bash tool |
| `"Write\|Edit"` | Write OR Edit tools |
| `"Write"` (no matcher field) | All events if no matcher needed |
| `"mcp__github__.*"` | All GitHub MCP tools (regex) |
| Omitted | All tool calls for that event |

**MCP tool matching:** MCP tools use the pattern `mcp__servername__toolname`. Match with exact name or regex.

## Decision Control (PreToolUse)

Command hooks can output JSON to control behavior:

```json
{"decision": "allow"}
```
```json
{"decision": "block", "reason": "PHP syntax error on line 42"}
```
```json
{"decision": "ask", "message": "This will modify a migration file. Continue?"}
```

If no JSON output, exit code determines behavior:
- Exit 0 → allow
- Exit 2 → block
- Other → log warning, allow

## Complete Example

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "php -l \"$CLAUDE_FILE_PATH\" 2>&1 || echo '{\"decision\":\"block\",\"reason\":\"PHP syntax error\"}'",
            "async": false
          }
        ]
      },
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "echo '{\"decision\":\"block\",\"reason\":\"Dangerous command\"}' && exit 2",
            "async": false
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          {
            "type": "command",
            "command": "php-cs-fixer fix \"$CLAUDE_FILE_PATH\" --quiet",
            "async": true
          }
        ]
      }
    ],
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "terminal-notifier -title 'Claude Code' -message 'Task completed'",
            "async": true
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo \"Session started at $(date)\" >> ~/.claude/session.log",
            "async": true
          }
        ]
      }
    ]
  }
}
```

## Frontmatter Hooks

Agents and skills can define scoped hooks in frontmatter:

```yaml
---
name: my-agent
description: Agent with custom hooks
hooks:
  PreToolUse:
    - matcher: Write
      hooks:
        - type: command
          command: "./validate-output.sh"
  PostToolUse:
    - matcher: Bash
      hooks:
        - type: command
          command: "./log-commands.sh"
          async: true
---
```

These hooks only run when the agent/skill is active.

## Best Practices

1. **Use command hooks for fast validation** — shell scripts are fast, no context cost
2. **Use async for non-blocking operations** — notifications, logging, formatting
3. **Avoid prompt hooks on frequent events** — they consume context tokens
4. **Test hooks independently** — run the command manually before adding to settings
5. **Use exit code 2 sparingly** — blocking should be for real errors only
6. **Provide clear block reasons** — helps Claude understand what went wrong
7. **Keep hooks fast** — slow hooks degrade the interactive experience
8. **Use matchers to scope hooks** — avoid running on every tool call
