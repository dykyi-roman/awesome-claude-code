# Plugins Reference

Complete guide to Claude Code plugin system — packaging, distribution, and marketplace.

## Plugin Structure

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json       # Manifest (required)
├── commands/             # Slash commands
│   └── my-command.md
├── agents/               # Custom agents
│   └── my-agent.md
├── skills/               # Skills
│   └── my-skill/
│       ├── SKILL.md
│       └── references/
├── hooks/
│   └── hooks.json        # Plugin-scoped hooks
├── .mcp.json             # MCP server configuration
├── .lsp.json             # LSP server configuration
└── README.md             # Plugin documentation
```

## Manifest Schema

`.claude-plugin/plugin.json`:

```json
{
  "name": "awesome-php-tools",
  "description": "PHP development tools for DDD and Clean Architecture",
  "version": "2.0.0",
  "author": "Your Name",
  "homepage": "https://github.com/user/awesome-php-tools",
  "repository": "https://github.com/user/awesome-php-tools",
  "license": "MIT",
  "claude": {
    "minVersion": "1.0.0"
  }
}
```

**Required fields:**
- `name` — unique plugin identifier (lowercase, hyphens)
- `description` — what the plugin provides
- `version` — semver version string

**Optional fields:**
- `author` — plugin author name
- `homepage` — documentation URL
- `repository` — source code URL
- `license` — SPDX license identifier
- `claude.minVersion` — minimum Claude Code version required

## Component Directories

### Commands

```
commands/
└── analyze.md            # Available as /plugin-name:analyze
```

Plugin commands are namespaced: `/plugin-name:command-name`.

### Agents

```
agents/
└── php-auditor.md        # Available as subagent_type
```

Plugin agents are available in the Task tool's `subagent_type` parameter.

### Skills

```
skills/
└── php-patterns/
    ├── SKILL.md          # Available as /plugin-name:php-patterns
    └── references/
        └── patterns.md
```

Plugin skills are namespaced: `/plugin-name:skill-name`.

### Hooks

```
hooks/
└── hooks.json            # Plugin-scoped hooks
```

`hooks.json` format (same as settings.json hooks section):

```json
{
  "PreToolUse": [
    {
      "matcher": "Write",
      "hooks": [
        {"type": "command", "command": "php -l $CLAUDE_FILE_PATH"}
      ]
    }
  ]
}
```

Plugin hooks are merged with user/project hooks.

### MCP Servers

`.mcp.json` at plugin root:

```json
{
  "mcpServers": {
    "plugin-server": {
      "command": "node",
      "args": ["./mcp-server/index.js"],
      "env": {}
    }
  }
}
```

### LSP Servers

`.lsp.json` at plugin root — Language Server Protocol configuration for IDE features.

## Namespaced Invocation

All plugin components use namespace prefix:

| Component | Invocation |
|-----------|------------|
| Command | `/plugin-name:command-name` |
| Skill (user) | `/plugin-name:skill-name` |
| Agent | `Task(subagent_type="plugin-agent-name")` |
| Hook | Automatic (merged with settings) |
| MCP | `mcp__server__tool` (standard naming) |

## Installation Sources

### GitHub

```json
{
  "enabledPlugins": {
    "awesome-php": {
      "source": "github",
      "repository": "user/awesome-php-claude"
    }
  }
}
```

### Git URL

```json
{
  "enabledPlugins": {
    "my-plugin": {
      "source": "git",
      "url": "https://git.example.com/plugins/my-plugin.git"
    }
  }
}
```

### NPM

```json
{
  "enabledPlugins": {
    "my-plugin": {
      "source": "npm",
      "package": "@scope/my-claude-plugin"
    }
  }
}
```

### Local Directory

```json
{
  "enabledPlugins": {
    "dev-plugin": {
      "source": "directory",
      "path": "/path/to/local/plugin"
    }
  }
}
```

### Local File (Archive)

```json
{
  "enabledPlugins": {
    "my-plugin": {
      "source": "file",
      "path": "/path/to/plugin.tar.gz"
    }
  }
}
```

## Local Development & Testing

### --plugin-dir Flag

```bash
claude --plugin-dir /path/to/my-plugin
```

**What it does:**
- Loads plugin from local directory
- Components available immediately
- Changes reflected on reload
- No need to install/publish

### Testing Workflow

1. Create plugin structure locally
2. Run `claude --plugin-dir ./my-plugin`
3. Test commands: `/my-plugin:command-name`
4. Verify agents work via Task tool
5. Check hooks trigger correctly
6. Publish when ready

## Migration: Standalone to Plugin

### Before (Standalone)

```
.claude/
├── commands/acc-my-tool.md
├── agents/acc-my-agent.md
└── skills/acc-my-skill/SKILL.md
```

### After (Plugin)

```
my-tool-plugin/
├── .claude-plugin/
│   └── plugin.json
├── commands/my-tool.md          # Remove acc- prefix (namespace handles it)
├── agents/my-agent.md
└── skills/my-skill/SKILL.md
```

### Migration Steps

1. Create `.claude-plugin/plugin.json` with manifest
2. Move components to plugin directory structure
3. Remove namespace prefixes from component names (plugin namespace replaces them)
4. Update internal references (agent names, skill names)
5. Add hooks.json if using project hooks
6. Test with `--plugin-dir`
7. Publish to GitHub/NPM

## Plugin vs Standalone Decision

| Criterion | Standalone | Plugin |
|-----------|-----------|--------|
| Scope | Single project | Distributed |
| Installation | Copy files | `enabledPlugins` config |
| Namespacing | Manual (prefix) | Automatic |
| Updates | Manual | Via source (git pull, npm update) |
| Sharing | Copy/paste | Install from source |
| Hooks | In settings.json | In hooks/hooks.json |
| MCP | In .mcp.json | In plugin .mcp.json |

**Use standalone when:**
- Components are project-specific
- No distribution needed
- Quick prototyping

**Use plugin when:**
- Components useful across projects
- Want to share with team/community
- Need versioning and updates
- Want namespace isolation

## enabledPlugins in Settings

Add to `~/.claude/settings.json` or `.claude/settings.json`:

```json
{
  "enabledPlugins": {
    "plugin-name": {
      "source": "github",
      "repository": "user/repo"
    }
  }
}
```

Multiple plugins can be enabled simultaneously. Plugin components are merged with local components.

## Best Practices

1. **Clear naming** — plugin name should describe its purpose
2. **Minimal manifest** — include only required fields + repository
3. **README.md** — document all commands, agents, skills
4. **Version semantically** — follow semver for updates
5. **Test locally first** — use `--plugin-dir` before publishing
6. **Namespace awareness** — remember commands become `/plugin:command`
7. **Self-contained** — avoid dependencies on specific project structure
8. **Hook safety** — plugin hooks should not break user workflows
