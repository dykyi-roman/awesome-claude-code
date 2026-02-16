# Settings and Permissions Reference

Complete guide to Claude Code settings schema, permissions, sandbox, and environment variables.

## Settings Hierarchy

Files are loaded with higher priority overriding lower:

| Priority | Level | Location | Versioned |
|----------|-------|----------|-----------|
| 1 (highest) | Managed | Enterprise system dirs | Admin-controlled |
| 2 | CLI args | `--model`, `--agents`, etc. | N/A |
| 3 | Local | `.claude/settings.local.json` | No (gitignored) |
| 4 | Project | `.claude/settings.json` | Yes |
| 5 (lowest) | User | `~/.claude/settings.json` | No |

### File Locations

| Level | Path |
|-------|------|
| User | `~/.claude/settings.json` |
| Project | `.claude/settings.json` (project root) |
| Local | `.claude/settings.local.json` (project root) |
| Managed (macOS) | `/Library/Application Support/Claude/managed-settings.json` |
| Managed (Linux) | `/etc/claude/managed-settings.json` |

## Full Settings Schema

```json
{
  "permissions": {
    "allow": [],
    "deny": [],
    "ask": []
  },
  "hooks": {},
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "network": "allow",
    "allowedDomains": []
  },
  "mcpServers": {},
  "enableAllProjectMcpServers": false,
  "allowedMcpServers": [],
  "deniedMcpServers": [],
  "enabledPlugins": {},
  "model": "claude-sonnet-4-5-20250929",
  "modelAliases": {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001"
  },
  "contextManagement": {
    "autoCompactEnabled": true,
    "autoCompactThreshold": 80
  },
  "attribution": {
    "enabled": true,
    "format": "Co-Authored-By: Claude <noreply@anthropic.com>"
  }
}
```

## Permission Rules

### Rule Syntax

```
Tool                    # Match all uses of Tool
Tool(specifier)         # Match specific uses
```

### Tool-Specific Specifiers

#### Bash

```json
{
  "allow": [
    "Bash(npm test)",
    "Bash(make *)",
    "Bash(php -l *)",
    "Bash(composer *)"
  ],
  "deny": [
    "Bash(rm -rf *)",
    "Bash(sudo *)",
    "Bash(chmod 777 *)"
  ]
}
```

**Matching:** glob-style on full command string.

#### Read / Edit / Write

```json
{
  "allow": [
    "Read(src/**)",
    "Edit(src/**)",
    "Write(src/**)"
  ],
  "deny": [
    "Read(.env*)",
    "Edit(vendor/**)",
    "Write(vendor/**)"
  ]
}
```

**Matching:** gitignore-style path patterns relative to project root.

#### WebFetch

```json
{
  "allow": [
    "WebFetch(domain:api.example.com)",
    "WebFetch(domain:docs.php.net)"
  ],
  "deny": [
    "WebFetch(domain:evil.com)"
  ]
}
```

**Matching:** `domain:` prefix filters by hostname.

#### MCP Tools

```json
{
  "allow": [
    "mcp__github__create_issue",
    "mcp__github__list_repos"
  ],
  "deny": [
    "mcp__github__delete_repo"
  ]
}
```

**Matching:** exact tool name in `mcp__server__tool` format.

#### Task (Subagents)

```json
{
  "allow": [
    "Task(acc-ddd-auditor)",
    "Task(acc-test-generator)"
  ],
  "deny": [
    "Task(dangerous-agent)"
  ]
}
```

**Matching:** exact agent name.

### Evaluation Order

1. **Deny rules checked first** — if any deny matches, tool is blocked
2. **Ask rules checked second** — if any ask matches, user is prompted
3. **Allow rules checked last** — if any allow matches, tool proceeds
4. **No match** — default behavior (usually ask)

**Deny always wins.** Even if a tool is in both `allow` and `deny`, it will be denied.

### Wildcard Patterns

| Pattern | Meaning |
|---------|---------|
| `*` | Match any single path segment |
| `**` | Match any number of path segments |
| `?` | Match any single character |
| `[abc]` | Match character set |

Examples:
```json
{
  "allow": [
    "Read(src/**/*.php)",
    "Bash(make *)",
    "Edit(src/Domain/**/Entity/*.php)"
  ]
}
```

## Sandbox Configuration

```json
{
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "network": "allow",
    "allowedDomains": ["api.example.com", "packagist.org"]
  }
}
```

**Fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | false | Enable sandbox mode |
| `autoAllowBashIfSandboxed` | boolean | false | Auto-allow Bash if sandbox is on |
| `network` | string | "allow" | "allow", "deny", or "restrict" |
| `allowedDomains` | string[] | [] | Domains allowed when network is "restrict" |

**Sandbox provides:**
- File system restrictions (project directory only)
- Network restrictions (configurable)
- Process isolation
- Enables `autoAllowBashIfSandboxed` for hands-free operation

## MCP Server Configuration

### Project-level (.mcp.json)

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "--root", "."]
    }
  }
}
```

### Settings-level

```json
{
  "enableAllProjectMcpServers": false,
  "allowedMcpServers": ["github", "filesystem"],
  "deniedMcpServers": ["dangerous-server"]
}
```

**MCP permission flow:**
1. Server defined in `.mcp.json` or settings
2. Check `deniedMcpServers` — if listed, blocked
3. Check `allowedMcpServers` — if listed, allowed
4. Check `enableAllProjectMcpServers` — if true, all project servers allowed
5. Otherwise, ask user

## Model Configuration

### ANTHROPIC_MODEL Environment Variable

```bash
export ANTHROPIC_MODEL=claude-opus-4-6
```

Overrides the default model for all sessions.

### Model Aliases in Settings

```json
{
  "modelAliases": {
    "opus": "claude-opus-4-6",
    "sonnet": "claude-sonnet-4-5-20250929",
    "haiku": "claude-haiku-4-5-20251001"
  }
}
```

Aliases used in agent/skill/command `model:` field resolve to full model IDs.

### CLI Model Override

```bash
claude --model opus
```

Overrides model for the current session.

## Key Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_MODEL` | (settings) | Override default model |
| `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` | 80 | Context compaction threshold (%) |
| `SLASH_COMMAND_TOOL_CHAR_BUDGET` | 15000 | Max chars loaded from skill/command |
| `CLAUDE_PROJECT_DIR` | (auto) | Project root directory |
| `CLAUDE_SESSION_ID` | (auto) | Current session identifier |
| `CLAUDE_CODE_ADDITIONAL_DIRECTORIES_CLAUDE_MD` | (none) | Extra CLAUDE.md directories |
| `CLAUDE_FILE_PATH` | (auto) | File path in hook context |
| `CLAUDE_TOOL_NAME` | (auto) | Tool name in hook context |

## Context Management

```json
{
  "contextManagement": {
    "autoCompactEnabled": true,
    "autoCompactThreshold": 80
  }
}
```

**Auto-compaction:**
- Triggers when context usage exceeds threshold (default 80%)
- Summarizes older messages to free space
- Preserves recent context and key information
- Fires `PreCompact` and `PostCompact` hooks

## Attribution Settings

```json
{
  "attribution": {
    "enabled": true,
    "format": "Co-Authored-By: Claude <noreply@anthropic.com>"
  }
}
```

Controls whether and how Claude attributes its contributions in commits.

## Managed Settings (Enterprise)

Managed settings are admin-controlled and cannot be overridden:

| Setting | Description |
|---------|-------------|
| `permissions.deny` | Organization-wide denied tools |
| `sandbox.enabled` | Force sandbox mode |
| `deniedMcpServers` | Blocked MCP servers |

**Managed-only fields** (only valid in managed settings):
- Organization-wide deny rules
- Force sandbox configuration
- Approved plugin lists

## Common Settings Patterns

### Development (Permissive)

```json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit", "Glob", "Grep", "Bash(make *)", "Bash(composer *)", "Bash(php *)"]
  },
  "sandbox": {"enabled": false}
}
```

### Production Review (Restrictive)

```json
{
  "permissions": {
    "allow": ["Read", "Glob", "Grep"],
    "deny": ["Write", "Edit", "Bash"]
  }
}
```

### Automated Pipeline (Sandboxed)

```json
{
  "permissions": {
    "allow": ["Read", "Write", "Edit", "Glob", "Grep", "Bash"]
  },
  "sandbox": {
    "enabled": true,
    "autoAllowBashIfSandboxed": true,
    "network": "restrict",
    "allowedDomains": ["packagist.org", "getcomposer.org"]
  }
}
```

### Team Shared (Balanced)

```json
{
  "permissions": {
    "allow": ["Read", "Glob", "Grep", "Bash(make *)", "Bash(composer *)"],
    "ask": ["Write", "Edit"],
    "deny": ["Bash(rm *)", "Bash(sudo *)"]
  },
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [{"type": "command", "command": "php -l $CLAUDE_FILE_PATH"}]
      }
    ]
  }
}
```
