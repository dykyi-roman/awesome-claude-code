# MCP (Model Context Protocol)

MCP servers extend Claude Code capabilities with custom tools, resources, and prompts.

## Overview

Model Context Protocol allows Claude Code to connect to external servers that provide:

- **Tools** — Custom actions Claude can perform
- **Resources** — Data sources Claude can read
- **Prompts** — Pre-defined prompt templates

## Configuration

MCP servers are configured in `.claude/settings.json`:

```json
{
  "mcpServers": {
    "server-name": {
      "command": "npx",
      "args": ["-y", "@example/mcp-server"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

## Available MCP Servers

| Server | Description | Use Case |
|--------|-------------|----------|
| [Database](#database-postgresqlmysql) | Query databases directly | Entity/table validation, migrations |
| GitHub | Issues, PRs, releases | Code review, project management |
| Sequential Thinking | Complex reasoning | Architecture decisions |
| Memory | Persistent storage | Cross-session context |
| Docker | Container management | DevOps automation |

## Database (PostgreSQL/MySQL)

Query databases directly from Claude Code. Essential for DDD projects.

### PostgreSQL

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://user:password@localhost:5432/database"
      }
    }
  }
}
```

### MySQL

```json
{
  "mcpServers": {
    "mysql": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-mysql"],
      "env": {
        "MYSQL_HOST": "localhost",
        "MYSQL_PORT": "3306",
        "MYSQL_USER": "root",
        "MYSQL_PASSWORD": "password",
        "MYSQL_DATABASE": "database"
      }
    }
  }
}
```

### Available Tools

| Tool          | Description                  |
|---------------|------------------------------|
| `query`       | Execute SELECT queries       |
| `execute`     | Execute INSERT/UPDATE/DELETE |
| `describe`    | Get table schema             |
| `list_tables` | List all tables              |

### Use Cases for DDD

**1. Validate Entity against table schema**
```
Check if User entity properties match users table columns
```

**2. Analyze migrations**
```
Show me the schema changes in the last 5 migrations
```

**3. Verify Repository queries**
```
Test this Repository findByEmail query against the database
```

**4. Generate Value Objects from columns**
```
Create Value Objects for users table columns (email, phone, address)
```

**5. Check data integrity**
```
Find orphaned records in order_items without parent orders
```

### Security Notes

- Use read-only database user for safety
- Never expose production credentials
- Consider using `.env` files with environment variables
- Add to `.gitignore`: any file containing connection strings

### Docker Example

For local development with Docker:

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "POSTGRES_CONNECTION_STRING": "postgresql://app:secret@localhost:5432/app_db"
      }
    }
  }
}
```

Ensure your `docker-compose.yml` exposes the port:

```yaml
services:
  postgres:
    image: postgres:16
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: app_db
```

## Creating Custom MCP Server

Basic structure for PHP MCP server:

```
mcp-server/
├── src/
│   └── Server.php
├── composer.json
└── bin/server
```

*Detailed guide coming soon*

## Resources

- [MCP Specification](https://modelcontextprotocol.io/)
- [MCP Servers Directory](https://github.com/modelcontextprotocol/servers)
- [Claude Code MCP Documentation](https://docs.anthropic.com/en/docs/claude-code/mcp)

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Hooks](hooks.md)