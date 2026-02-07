---
name: acc-create-docker-env-template
description: Generates Docker environment templates for PHP projects. Creates .env.docker files with service configurations and documentation.
---

# Docker Environment Template Generator

Generates documented environment variable templates for Docker-based PHP projects.

## Generated Files

```
.env.docker                 # Docker environment template with defaults
.env.docker.example         # Committed example (no secrets)
```

## Complete .env.docker Template

```bash
# ──────────────────────────────────────────────────────────
# Docker Environment Configuration
# Copy to .env and adjust values for your environment.
# NEVER commit .env with real secrets to version control.
# ──────────────────────────────────────────────────────────

# ─── Application ──────────────────────────────────────────

# Application environment: dev, test, staging, prod
APP_ENV=dev

# Enable/disable debug mode (MUST be false in production)
APP_DEBUG=true

# Application secret key (generate unique value per environment)
# Generate: php -r "echo bin2hex(random_bytes(32));"
APP_SECRET=change_me_to_a_random_secret_value

# Application base URL
APP_URL=http://localhost

# Application port exposed on host
APP_PORT=8080

# Trusted proxies (comma-separated IPs or CIDR, use REMOTE_ADDR for single proxy)
TRUSTED_PROXIES=127.0.0.1,REMOTE_ADDR

# Trusted hosts regex pattern
TRUSTED_HOSTS=^localhost|app$

# ─── Database ─────────────────────────────────────────────

# Database driver: mysql, pgsql
DB_DRIVER=mysql

# Database host (service name in docker-compose)
DB_HOST=mysql

# Database port (internal Docker network port)
DB_PORT=3306

# Database name
DB_NAME=app

# Database user (avoid using root in production)
DB_USER=app

# Database password (use strong password in production)
# Generate: openssl rand -base64 32
DB_PASSWORD=secret

# Database root password (for initial setup only)
DB_ROOT_PASSWORD=root_secret

# Database charset and collation
DB_CHARSET=utf8mb4
DB_COLLATION=utf8mb4_unicode_ci

# Database connection URL (alternative to individual params)
# MySQL:    mysql://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME
# Postgres: postgresql://DB_USER:DB_PASSWORD@DB_HOST:DB_PORT/DB_NAME?serverVersion=16
DATABASE_URL=mysql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}?charset=${DB_CHARSET}

# Database port exposed on host (for external tools like DBeaver)
DB_EXTERNAL_PORT=33060

# ─── Redis ────────────────────────────────────────────────

# Redis host (service name in docker-compose)
REDIS_HOST=redis

# Redis port
REDIS_PORT=6379

# Redis password (empty for no auth, set in production)
REDIS_PASSWORD=

# Redis database index (0-15)
REDIS_DB=0

# Redis connection URL
REDIS_URL=redis://${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# Redis port exposed on host
REDIS_EXTERNAL_PORT=63790

# ─── RabbitMQ ─────────────────────────────────────────────

# RabbitMQ host (service name in docker-compose)
RABBITMQ_HOST=rabbitmq

# RabbitMQ AMQP port
RABBITMQ_PORT=5672

# RabbitMQ management UI port
RABBITMQ_MANAGEMENT_PORT=15672

# RabbitMQ credentials
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

# RabbitMQ virtual host
RABBITMQ_VHOST=/

# RabbitMQ connection URL
RABBITMQ_URL=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST}:${RABBITMQ_PORT}/${RABBITMQ_VHOST}

# Messenger transport DSN (Symfony)
MESSENGER_TRANSPORT_DSN=amqp://${RABBITMQ_USER}:${RABBITMQ_PASSWORD}@${RABBITMQ_HOST}:${RABBITMQ_PORT}/%2f/messages

# ─── Mail ─────────────────────────────────────────────────

# Mail driver: smtp, sendmail, log, array
MAIL_DRIVER=smtp

# SMTP host (use Mailhog/Mailpit for development)
MAIL_HOST=mailpit

# SMTP port (1025 for Mailhog/Mailpit, 587 for production)
MAIL_PORT=1025

# SMTP credentials (empty for local dev tools)
MAIL_USERNAME=
MAIL_PASSWORD=

# SMTP encryption: tls, ssl, null
MAIL_ENCRYPTION=null

# Default from address
MAIL_FROM_ADDRESS=noreply@app.local
MAIL_FROM_NAME="App Name"

# Mailer DSN (Symfony)
MAILER_DSN=smtp://${MAIL_HOST}:${MAIL_PORT}

# Mailpit web UI port exposed on host
MAIL_WEB_PORT=8025

# ─── PHP Configuration ───────────────────────────────────

# PHP memory limit
PHP_MEMORY_LIMIT=256M

# Maximum upload file size
PHP_UPLOAD_MAX_FILESIZE=64M

# Maximum POST data size (should be >= UPLOAD_MAX_FILESIZE)
PHP_POST_MAX_SIZE=64M

# Maximum execution time in seconds (0 = unlimited)
PHP_MAX_EXECUTION_TIME=30

# Maximum input time in seconds
PHP_MAX_INPUT_TIME=60

# Error reporting level
PHP_ERROR_REPORTING=E_ALL

# Display errors (MUST be Off in production)
PHP_DISPLAY_ERRORS=On

# Opcache settings
PHP_OPCACHE_ENABLE=1
PHP_OPCACHE_MEMORY=128
PHP_OPCACHE_MAX_FILES=10000
PHP_OPCACHE_VALIDATE_TIMESTAMPS=1
PHP_OPCACHE_REVALIDATE_FREQ=0

# Xdebug mode: off, debug, coverage, profile, trace
XDEBUG_MODE=off

# Xdebug client host (host.docker.internal for Docker Desktop)
XDEBUG_CLIENT_HOST=host.docker.internal

# ─── Docker Configuration ────────────────────────────────

# Docker Compose project name (prefixes container names)
COMPOSE_PROJECT_NAME=app

# PHP Docker image tag
PHP_IMAGE_TAG=8.4-fpm-alpine

# Nginx Docker image tag
NGINX_IMAGE_TAG=1.27-alpine

# User/Group IDs (match host user to avoid permission issues)
# Run: id -u and id -g to get your values
UID=1000
GID=1000

# ─── Worker Configuration ────────────────────────────────

# Queue worker memory limit in MB
WORKER_MEMORY_LIMIT=128

# Queue worker timeout per job in seconds
WORKER_TIMEOUT=60

# Maximum retry attempts per job
WORKER_TRIES=3

# Sleep seconds between empty queue polls
WORKER_SLEEP=3

# Number of worker replicas
WORKER_REPLICAS=2

# ─── Logging ──────────────────────────────────────────────

# Log channel: stderr, file, syslog
LOG_CHANNEL=stderr

# Log level: debug, info, notice, warning, error, critical
LOG_LEVEL=debug
```

## .env.docker.example (safe to commit)

```bash
# Docker Environment — Example Configuration
# Copy this file to .env and set your values.
# See .env.docker for full documentation of each variable.

APP_ENV=dev
APP_DEBUG=true
APP_SECRET=CHANGE_ME
APP_URL=http://localhost
APP_PORT=8080

DB_HOST=mysql
DB_PORT=3306
DB_NAME=app
DB_USER=app
DB_PASSWORD=CHANGE_ME
DB_ROOT_PASSWORD=CHANGE_ME

REDIS_HOST=redis
REDIS_PORT=6379

RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest

MAIL_HOST=mailpit
MAIL_PORT=1025

PHP_MEMORY_LIMIT=256M
COMPOSE_PROJECT_NAME=app
```

## .gitignore Addition

```gitignore
# Environment files with secrets
.env
.env.local
.env.*.local

# Keep example files
!.env.docker.example
```

## Generation Instructions

1. **Analyze project dependencies:**
   - Check docker-compose.yml for services
   - Check composer.json for framework
   - Identify required external services

2. **Generate .env.docker:**
   - Include only relevant service sections
   - Add documentation for each variable
   - Set sensible development defaults
   - Mark production-sensitive values

3. **Generate .env.docker.example:**
   - Strip actual secrets
   - Use CHANGE_ME placeholders
   - Keep structure matching .env.docker

4. **Security:**
   - Never include real credentials
   - Add .env to .gitignore
   - Document secret generation commands

## Usage

Provide:
- Services from docker-compose.yml
- Framework (Symfony/Laravel)
- Custom environment variables needed
- Target environment (dev/staging/prod)

The generator will:
1. Create documented .env.docker template
2. Create safe-to-commit .env.docker.example
3. Add appropriate .gitignore entries
4. Include variable generation commands for secrets
