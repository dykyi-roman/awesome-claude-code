# MCP (Model Context Protocol)

MCP servers extend Claude Code capabilities with custom tools, resources, and prompts.

## Overview

Model Context Protocol allows Claude Code to connect to external servers that provide:

- **Tools** — Custom actions Claude can perform
- **Resources** — Data sources Claude can read
- **Prompts** — Pre-defined prompt templates

## Configuration

> **`.claude/settings.json` is not read for MCP.** Putting an `mcpServers` key there is ignored
> silently — no error, no server, nothing to debug. Use one of the files below.

| Scope | File | Applies to |
|-------|------|-----------|
| Project (committed) | `.mcp.json` in the repo root | everyone working on this project |
| User | `~/.claude.json` | all your projects |
| Shipped with a plugin | `mcpServers` in `.claude-plugin/plugin.json`, or a `.mcp.json` at the plugin root | whoever enables the plugin |

Inside a plugin, paths must go through `${CLAUDE_PLUGIN_ROOT}` — the plugin's install directory is
not the user's working directory:

```json
{
  "mcpServers": {
    "db-tools": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"]
    }
  }
}
```

Verify with `claude plugin validate <path> --strict`, which accepts `mcpServers` in `plugin.json`
and warns on any misspelled field (`Unknown field '...'. Claude Code ignores it at load time.`).

The examples below all use the `.mcp.json` schema:

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

| Server                                | Description                             | Use Case                                         |
|---------------------------------------|-----------------------------------------|--------------------------------------------------|
| [Database](#database-postgresqlmysql) | Query databases directly                | Entity/table validation, migrations              |
| [Redis](#redis)                       | Cache, sessions, pub/sub, vector search | Caching, rate limiting, session management       |
| [RabbitMQ](#rabbitmq)                 | Message broker management               | Queue monitoring, message publishing             |
| [Elasticsearch](#elasticsearch)       | Search & analytics engine               | Full-text search, log analysis, index management |
| [Kafka](#kafka)                       | Event streaming platform                | Topic management, event sourcing                 |
| [GitHub](#github)                     | Repository, PRs, issues, actions        | Code review, project management, CI/CD           |
| [GitLab](#gitlab)                     | Repository, MRs, issues, pipelines      | Code review, project management, CI/CD           |
| [Docker Hub](#docker-hub)             | Image registry management               | Image discovery, tag management                  |

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

## Redis

Natural language interface for managing and searching data in Redis. Supports strings, hashes, JSON, lists, sets, sorted sets, streams, pub/sub, and vector embeddings.

```json
{
  "mcpServers": {
    "redis": {
      "command": "uvx",
      "args": ["--from", "redis-mcp-server@latest", "redis-mcp-server"],
      "env": {
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "REDIS_PWD": "secret"
      }
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `REDIS_HOST` | Redis hostname | `127.0.0.1` |
| `REDIS_PORT` | Redis port | `6379` |
| `REDIS_DB` | Database number | `0` |
| `REDIS_USERNAME` | Username | `default` |
| `REDIS_PWD` | Password | — |
| `REDIS_SSL` | Enable SSL | `false` |
| `REDIS_CLUSTER_MODE` | Cluster mode | `false` |

### Available Tools

| Tool | Description |
|------|-------------|
| `set/get` | String operations with TTL |
| `hset/hget` | Hash field-value pairs |
| `lpush/rpush/lpop` | List operations |
| `sadd/smembers` | Set operations |
| `zadd/zrange` | Sorted set with scores |
| `json.set/json.get` | JSON document operations |
| `publish/subscribe` | Pub/sub messaging |
| `xadd/xread` | Stream operations |
| `ft.search` | Full-text and vector search |

### Use Cases for DDD

**1. Cache read models**
```
Cache the OrderSummary read model in Redis with 5-minute TTL
```

**2. Session management**
```
Store user session data as a Redis hash with authentication tokens
```

**3. Rate limiting**
```
Check current rate limit counters for the API gateway
```

**4. Event stream inspection**
```
Read the last 10 domain events from the order-events stream
```

### Docker Example

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --requirepass secret
```

---

## RabbitMQ

MCP server for interacting with RabbitMQ brokers. Supports multi-broker connections, queue/exchange management, and admin API operations.

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "uvx",
      "args": ["amq-mcp-server-rabbitmq@latest", "--allow-mutative-tools"]
    }
  }
}
```

### Command Line Arguments

| Argument | Purpose | Default |
|----------|---------|---------|
| `--allow-mutative-tools` | Enable write operations | `false` |
| `--http` | Use Streamable HTTP transport | disabled |
| `--server-port` | MCP server port | `8888` |

### Available Tools

| Tool | Description |
|------|-------------|
| Queue management | List, create, purge, delete queues |
| Exchange management | List, create, bind exchanges |
| Message operations | Publish and consume messages |
| Connection info | List connections and channels |
| Broker health | Check node status and cluster info |

### Use Cases for DDD

**1. Monitor async command processing**
```
Show me pending messages in the order-processing queue
```

**2. Inspect dead letter queues**
```
List messages in the DLQ for failed payment events
```

**3. Verify event routing**
```
Check bindings for the domain-events exchange
```

### Security Notes

- Remove `--allow-mutative-tools` in production to prevent accidental queue modifications
- Use dedicated read-only RabbitMQ user when possible

### Docker Example

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: guest
      RABBITMQ_DEFAULT_PASS: guest
```

---

## Elasticsearch

Query and manage Elasticsearch indices, documents, and clusters. Supports full-text search, analytics, and index lifecycle management.

```json
{
  "mcpServers": {
    "elasticsearch": {
      "command": "uvx",
      "args": ["elasticsearch-mcp-server"],
      "env": {
        "ELASTICSEARCH_HOSTS": "https://localhost:9200",
        "ELASTICSEARCH_API_KEY": "your-api-key"
      }
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `ELASTICSEARCH_HOSTS` | Elasticsearch endpoint | `https://localhost:9200` |
| `ELASTICSEARCH_API_KEY` | API key (recommended) | — |
| `ELASTICSEARCH_USERNAME` | Basic auth username | — |
| `ELASTICSEARCH_PASSWORD` | Basic auth password | — |
| `VERIFY_CERTS` | Verify SSL certificates | `false` |
| `DISABLE_HIGH_RISK_OPERATIONS` | Disable write operations | `false` |

### Available Tools

| Tool | Description |
|------|-------------|
| `search_documents` | Full-text and filtered search |
| `index_document` | Index a document |
| `get_document` | Retrieve document by ID |
| `delete_document` | Delete document by ID |
| `list_indices` | List all indices |
| `create_index` | Create index with mappings |
| `delete_index` | Delete an index |
| `get_cluster_health` | Cluster health status |
| `get_cluster_stats` | Cluster statistics |
| `list_aliases` | List index aliases |
| `analyze_text` | Analyze text with custom analyzers |

### Use Cases for DDD

**1. Validate read model indices**
```
Show me the mapping for the product-catalog index
```

**2. Search domain events**
```
Search for all OrderPlaced events in the last 24 hours
```

**3. Monitor cluster health**
```
Check Elasticsearch cluster health and shard allocation
```

**4. Debug search queries**
```
Analyze how "running shoes" is tokenized with the product analyzer
```

### Security Notes

- Use API keys instead of username/password when possible
- Set `DISABLE_HIGH_RISK_OPERATIONS=true` for read-only access
- Never expose production cluster credentials

### Docker Example

```yaml
services:
  elasticsearch:
    image: elasticsearch:8.15.0
    ports:
      - "9200:9200"
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms512m -Xmx512m"
```

---

## Kafka

MCP server for Apache Kafka cluster management. Manage topics, inspect partitions, and monitor cluster configurations.

```json
{
  "mcpServers": {
    "kafka": {
      "command": "python",
      "args": ["/path/to/kafka-mcp-server/server.py"]
    }
  }
}
```

> **Note**: Requires a `kafka.properties` file for connection configuration.

### Configuration File

Create `kafka.properties`:

```ini
bootstrap.servers=localhost:9092
client.id=kafka-mcp-client
# security.protocol=SASL_SSL
# sasl.mechanism=PLAIN
```

### Available Tools

| Tool | Description |
|------|-------------|
| `kafka_initialize_connection` | Connect using properties file |
| `kafka_list_topics` | List all cluster topics |
| `kafka_create_topic` | Create topic with partitions |
| `kafka_delete_topic` | Remove a topic |
| `kafka_get_topic_info` | Partition, replica, ISR details |

### Use Cases for DDD

**1. Verify event sourcing topics**
```
List all topics and check partition count for domain-events
```

**2. Create bounded context topics**
```
Create a topic order-events with 6 partitions and replication factor 3
```

**3. Inspect topic configuration**
```
Show partition details and ISR status for the payment-events topic
```

### Docker Example

```yaml
services:
  kafka:
    image: confluentinc/cp-kafka:7.7.0
    ports:
      - "9092:9092"
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_CONTROLLER_QUORUM_VOTERS: 1@kafka:29093
      KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:29093
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
      KAFKA_CONTROLLER_LISTENER_NAMES: CONTROLLER
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: CONTROLLER:PLAINTEXT,PLAINTEXT:PLAINTEXT
      CLUSTER_ID: MkU3OEVBNTcwNTJENDM2Qk
```

---

## GitHub

GitHub's official MCP server. Manage repositories, issues, pull requests, actions, and code security directly from Claude Code.

```json
{
  "mcpServers": {
    "github": {
      "command": "docker",
      "args": [
        "run", "-i", "--rm",
        "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
        "ghcr.io/github/github-mcp-server"
      ],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "<your-token>"
      }
    }
  }
}
```

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GITHUB_PERSONAL_ACCESS_TOKEN` | Personal access token (required) | — |
| `GITHUB_HOST` | GitHub Enterprise host | `github.com` |
| `GITHUB_TOOLSETS` | Comma-separated enabled toolsets | all |

### Available Toolsets

| Toolset | Capabilities |
|---------|-------------|
| `repos` | Repository CRUD, file operations, branch management |
| `issues` | Create, update, search, comment on issues |
| `pull_requests` | Create, review, merge PRs, manage reviews |
| `actions` | Workflow runs, logs, artifacts |
| `code_security` | Security alerts, Dependabot, code scanning |

### Use Cases for DDD

**1. Review PR changes**
```
Show me the diff for PR #42 and check if domain layer has external dependencies
```

**2. Track architecture decisions**
```
Create an issue for ADR-005: Switch to Event Sourcing for Order aggregate
```

**3. Monitor CI/CD**
```
Check the latest workflow run status for the main branch
```

### Security Notes

- Use fine-grained PAT with minimal required scopes
- Recommended scopes: `repo`, `read:org`, `read:packages`
- For read-only access, use `GITHUB_TOOLSETS=repos,issues` to limit capabilities

---

## GitLab

GitLab's official MCP server. Manage projects, merge requests, issues, pipelines, and search code directly from Claude Code. Uses OAuth 2.0 for secure authorization.

### HTTP Transport (Recommended)

Direct connection without additional dependencies:

```json
{
  "mcpServers": {
    "gitlab": {
      "type": "http",
      "url": "https://gitlab.example.com/api/v4/mcp"
    }
  }
}
```

### Stdio Transport

Requires Node.js 20+:

```json
{
  "mcpServers": {
    "gitlab": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://gitlab.example.com/api/v4/mcp"
      ]
    }
  }
}
```

### Claude Code CLI Setup

```bash
claude mcp add --transport http GitLab https://gitlab.example.com/api/v4/mcp
```

### Available Tools

| Tool | Description |
|------|-------------|
| `create_issue` | Create a new issue in a project |
| `get_issue` | Retrieve issue details |
| `create_merge_request` | Create a merge request |
| `get_merge_request` | Retrieve MR details |
| `get_merge_request_diffs` | Retrieve MR diffs |
| `get_merge_request_commits` | List MR commits |
| `get_merge_request_pipelines` | List MR pipelines |
| `get_pipeline_jobs` | Retrieve CI/CD pipeline jobs |
| `create_workitem_note` | Add comment to a work item |
| `get_workitem_notes` | List work item comments |
| `search` | Search across the GitLab instance |
| `search_labels` | Search project/group labels |
| `semantic_code_search` | Semantic code search in a project |

### Use Cases for DDD

**1. Review MR changes**
```
Show me the diff for MR !42 and check if domain layer has external dependencies
```

**2. Track architecture decisions**
```
Create an issue for ADR-005: Switch to Event Sourcing for Order aggregate
```

**3. Monitor CI/CD pipelines**
```
Check pipeline jobs status for the latest MR pipeline
```

**4. Search domain code**
```
Search for all Aggregate implementations across the project
```

### Security Notes

- Uses OAuth 2.0 Dynamic Client Registration — no PAT tokens needed
- Requires GitLab Duo Core with beta/experimental features enabled
- For self-hosted GitLab, replace `gitlab.example.com` with your instance URL
- GitLab.com users can use `https://gitlab.com/api/v4/mcp`

---

## Docker Hub

Access Docker Hub APIs for image discovery, repository management, and tag inspection.

```json
{
  "mcpServers": {
    "docker-hub": {
      "command": "npx",
      "args": ["-y", "docker/hub-mcp", "--transport=stdio"],
      "env": {
        "HUB_PAT_TOKEN": "<your-hub-token>"
      }
    }
  }
}
```

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `HUB_PAT_TOKEN` | Docker Hub Personal Access Token |

### Available Tools

| Tool | Description |
|------|-------------|
| `search` | Search repositories with filters (arch, OS, category) |
| `get_namespaces` | List user's namespace memberships |
| `list_repositories_by_namespace` | List repos with sorting/filtering |
| `get_repository_info` | Detailed repository info |
| `check_repository` | Verify repository existence |
| `check_repository_tag` | Confirm tag existence |
| `list_repository_tags` | All tags with arch/OS filters |
| `docker_hardened_images` | Query Docker Hardened Images |

### Use Cases for DDD

**1. Find base images**
```
Search for PHP 8.4 FPM Alpine images with the official badge
```

**2. Check image tags**
```
List available tags for the postgres image filtered by linux/arm64
```

**3. Verify deployment images**
```
Check if our app image myorg/order-service:v2.3.0 tag exists
```

---

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