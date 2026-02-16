---
description: Generate Docker components. Creates Dockerfiles, Compose configs, Nginx, entrypoint, Makefile, and environment templates for PHP projects.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: opus
argument-hint: <component-type> [name] [-- additional instructions]
---

# Generate Docker Components

Generate Docker configuration components for PHP projects with production-ready defaults.

## Input Parsing

Parse `$ARGUMENTS` to extract component type, optional name, and meta-instructions:

```
Format: <component-type> [name] [-- <meta-instructions>]

Examples:
- /acc-generate-docker dockerfile
- /acc-generate-docker compose
- /acc-generate-docker full
- /acc-generate-docker dockerfile production -- with Symfony
- /acc-generate-docker compose myapp -- with PostgreSQL and Redis
- /acc-generate-docker nginx -- with SSL termination
- /acc-generate-docker entrypoint -- with migrations
```

**Parsing rules:**
1. First part = **component type** (required, see list below)
2. Second part = **name** (optional project/service name)
3. After ` -- ` = **meta-instructions** (optional customizations)

## Supported Components

| Component | Aliases | Description |
|-----------|---------|-------------|
| `dockerfile` | `df` | Production multi-stage Dockerfile |
| `compose` | `dc`, `docker-compose` | Docker Compose configuration |
| `nginx` | `web` | Nginx reverse proxy config |
| `entrypoint` | `ep`, `entry` | Container entrypoint script |
| `makefile` | `mk`, `make` | Docker Makefile commands |
| `env` | `environment` | Environment variable template |
| `healthcheck` | `hc`, `health` | Health check script |
| `full` | `all`, `stack` | Complete Docker setup |

## Pre-flight Check

1. **Verify valid component type:**
   - If not provided, ask user which component to generate
   - If invalid, show list of supported components

2. **Check project structure:**
   ```bash
   # PHP project info
   cat composer.json 2>/dev/null

   # Detect framework
   grep -E "(symfony|laravel)" composer.json 2>/dev/null

   # Check existing Docker files
   ls Dockerfile* docker-compose* .dockerignore 2>/dev/null

   # Check project directories
   ls -d src/ app/ public/ config/ 2>/dev/null
   ```

3. **Detect framework and services:**
   - Symfony: `symfony/framework-bundle` in composer.json
   - Laravel: `laravel/framework` in composer.json
   - MySQL: `doctrine/dbal` or `ext-pdo_mysql`
   - PostgreSQL: `ext-pdo_pgsql`
   - Redis: `predis/predis` or `ext-redis`
   - RabbitMQ: `php-amqplib/php-amqplib` or `ext-amqp`

## Instructions

Use the `acc-docker-coordinator` agent to generate components:

```
Task tool with subagent_type="acc-docker-coordinator"
prompt: "Generate Docker component: [COMPONENT_TYPE]

Operation: GENERATE
Component: [COMPONENT_TYPE]
Name: [NAME if provided]

Project info:
- PHP version: [from composer.json]
- Framework: [detected framework]
- Extensions: [from composer.json require]
- Services: [detected services]

[META-INSTRUCTIONS if provided]

Requirements:
1. PHP 8.4 with Alpine base
2. Multi-stage builds for Dockerfile
3. Health checks for all services
4. Non-root user
5. BuildKit optimizations
6. Production-ready defaults
7. Follow existing project patterns"
```

## Generation Examples

### Dockerfile
```bash
/acc-generate-docker dockerfile
/acc-generate-docker df -- with Symfony and PostgreSQL
```

Generates:
```
Dockerfile              # Production multi-stage build
Dockerfile.dev          # Development with Xdebug
.dockerignore           # Build context exclusions
```

### Docker Compose
```bash
/acc-generate-docker compose
/acc-generate-docker dc -- with MySQL, Redis, RabbitMQ
```

Generates:
```
docker-compose.yml      # Development stack
docker-compose.prod.yml # Production overrides
.env.docker             # Environment template
```

### Nginx
```bash
/acc-generate-docker nginx
/acc-generate-docker web -- with SSL and rate limiting
```

Generates:
```
docker/nginx/nginx.conf    # Main config
docker/nginx/default.conf  # Server block
```

### Entrypoint
```bash
/acc-generate-docker entrypoint
/acc-generate-docker ep -- with migrations and cache warmup
```

Generates:
```
docker/entrypoint.sh    # Startup script with signal handling
```

### Makefile
```bash
/acc-generate-docker makefile
/acc-generate-docker mk -- with deploy targets
```

Generates:
```
Makefile.docker         # Docker commands (or appends to existing Makefile)
```

### Environment
```bash
/acc-generate-docker env
/acc-generate-docker environment -- with all services
```

Generates:
```
.env.docker             # Environment template with documentation
```

### Health Check
```bash
/acc-generate-docker healthcheck
/acc-generate-docker hc -- for PHP-FPM and custom endpoint
```

Generates:
```
docker/healthcheck.sh   # Health check script
```

### Full Stack
```bash
/acc-generate-docker full
/acc-generate-docker all -- Symfony with PostgreSQL, Redis, RabbitMQ
```

Generates:
```
Dockerfile              # Production multi-stage
Dockerfile.dev          # Development with Xdebug
.dockerignore           # Context exclusions
docker-compose.yml      # Development stack
docker-compose.prod.yml # Production overrides
.env.docker             # Environment template
docker/
├── nginx/
│   ├── nginx.conf
│   └── default.conf
├── php/
│   ├── php.ini
│   ├── opcache.ini
│   └── php-fpm.d/www.conf
├── entrypoint.sh
├── healthcheck.sh
└── Makefile.docker
```

## Expected Output

### Generated Files Summary

```
Generated Docker Stack for: my-project

Files created:
├── Dockerfile (production, multi-stage, ~180MB)
├── Dockerfile.dev (development, Xdebug)
├── .dockerignore
├── docker-compose.yml (PHP-FPM, Nginx, MySQL, Redis)
├── docker-compose.prod.yml
├── .env.docker
└── docker/
    ├── nginx/default.conf
    ├── php/php.ini
    ├── entrypoint.sh
    └── healthcheck.sh

Quick start:
  cp .env.docker .env
  docker compose up -d
  docker compose exec php composer install
  open http://localhost:8080
```

## Usage Examples

```bash
# Generate full Docker setup
/acc-generate-docker full

# Just a Dockerfile
/acc-generate-docker dockerfile

# Compose with specific services
/acc-generate-docker compose -- with PostgreSQL and Redis

# Nginx for Symfony
/acc-generate-docker nginx -- Symfony public directory

# Everything for Laravel
/acc-generate-docker full -- Laravel with MySQL, Redis, queue workers

# Just the Makefile
/acc-generate-docker makefile -- with deploy and CI targets
```

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `with Symfony` | Symfony-specific configuration |
| `with Laravel` | Laravel-specific configuration |
| `with MySQL` | Include MySQL service |
| `with PostgreSQL` | Include PostgreSQL service |
| `with Redis` | Include Redis service |
| `with RabbitMQ` | Include RabbitMQ service |
| `with SSL` | Include SSL/TLS configuration |
| `with workers` | Include queue worker config |
| `minimal` | Minimal configuration |
| `with monitoring` | Include monitoring setup |
