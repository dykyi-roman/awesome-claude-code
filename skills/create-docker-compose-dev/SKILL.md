---
name: acc-create-docker-compose-dev
description: Generates Docker Compose development configurations for PHP projects. Creates full development stacks with database, cache, queue, and debugging tools.
---

# Docker Compose Development Generator

Generates complete Docker Compose development configurations for PHP projects with database, cache, queue, mail, and debugging services.

## Generated Files

```
docker-compose.yml        # Full development stack
.env.docker               # Environment variables for Docker
```

## Generation Instructions

1. **Analyze project:** Read `composer.json` for database drivers, Redis, RabbitMQ, Elasticsearch; detect framework
2. **Select services:** PHP-FPM + Nginx (always), DB (MySQL/PostgreSQL), Redis, RabbitMQ (profiles), Mailhog (profiles)
3. **Generate:** All services with health checks, networking, env vars, profiles for optional services

## Docker Compose Development Stack

```yaml
# docker-compose.yml
services:
  php:
    build:
      context: .
      dockerfile: Dockerfile.dev
      args:
        HOST_UID: ${HOST_UID:-1000}
        HOST_GID: ${HOST_GID:-1000}
    volumes:
      - .:/app:cached
      - vendor:/app/vendor
      - composer-cache:/home/dev/.composer
    environment:
      APP_ENV: ${APP_ENV:-dev}
      APP_DEBUG: ${APP_DEBUG:-1}
      DATABASE_URL: "postgresql://${DB_USER:-app}:${DB_PASSWORD:-secret}@database:5432/${DB_NAME:-app_dev}?serverVersion=17"
      REDIS_URL: "redis://redis:6379"
      RABBITMQ_URL: "amqp://${RABBITMQ_USER:-guest}:${RABBITMQ_PASS:-guest}@rabbitmq:5672"
      MAILER_DSN: "smtp://mailhog:1025"
      PHP_IDE_CONFIG: "serverName=docker"
      XDEBUG_MODE: ${XDEBUG_MODE:-debug,coverage}
      XDEBUG_CONFIG: "client_host=host.docker.internal"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      database:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "php-fpm-healthcheck || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - app-network

  nginx:
    image: nginx:1.27-alpine
    ports:
      - "${NGINX_PORT:-8080}:80"
    volumes:
      - .:/app:cached
      - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      php:
        condition: service_healthy
    networks:
      - app-network

  database:
    image: postgres:17-alpine
    ports:
      - "${DB_PORT:-5432}:5432"
    environment:
      POSTGRES_DB: ${DB_NAME:-app_dev}
      POSTGRES_USER: ${DB_USER:-app}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-secret}
    volumes:
      - db-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-app} -d ${DB_NAME:-app_dev}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - app-network

  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    command: redis-server --appendonly yes --maxmemory 128mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app-network

  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    profiles: ["queue"]
    ports:
      - "${RABBITMQ_PORT:-5672}:5672"
      - "${RABBITMQ_MGMT_PORT:-15672}:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-guest}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-guest}
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5
    networks:
      - app-network

  mailhog:
    image: mailhog/mailhog:latest
    profiles: ["mail"]
    ports:
      - "${MAILHOG_SMTP_PORT:-1025}:1025"
      - "${MAILHOG_UI_PORT:-8025}:8025"
    networks:
      - app-network

volumes:
  db-data:
  redis-data:
  rabbitmq-data:
  vendor:
  composer-cache:

networks:
  app-network:
    driver: bridge
```

## Nginx Configuration

```nginx
# docker/nginx/default.conf
server {
    listen 80;
    server_name localhost;
    root /app/public;
    index index.php;
    client_max_body_size 20M;

    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ ^/index\.php(/|$) {
        fastcgi_pass php:9000;
        fastcgi_split_path_info ^(.+\.php)(/.*)$;
        include fastcgi_params;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT $realpath_root;
        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_read_timeout 300;
        internal;
    }

    location ~ \.php$ { return 404; }
    location = /ping { access_log off; return 200 "pong"; add_header Content-Type text/plain; }
    location ~ /\. { deny all; access_log off; log_not_found off; }
}
```

## Profile Usage

```bash
# Core services only (PHP, Nginx, DB, Redis)
docker compose up -d

# With RabbitMQ
docker compose --profile queue up -d

# With Mailhog
docker compose --profile mail up -d

# All services
docker compose --profile queue --profile mail up -d
```

## Common Development Commands

```bash
# First-time setup
docker compose up -d --build
docker compose exec php composer install
docker compose exec php php bin/console doctrine:migrations:migrate

# Daily workflow
docker compose up -d
docker compose exec php vendor/bin/phpunit
docker compose exec php vendor/bin/phpstan analyse

# Cleanup
docker compose down
docker compose down -v  # Also remove volumes
```

## Additional Services

See `references/service-templates.md` for composable service blocks: MySQL, Elasticsearch, MinIO, phpMyAdmin, Adminer, Traefik.

## Usage

Provide:
- Database type (PostgreSQL/MySQL)
- Required services (Redis, RabbitMQ, Mail)
- Framework (Symfony/Laravel)
- Custom ports (optional)

The generator will:
1. Create docker-compose.yml with selected services
2. Generate Nginx configuration
3. Create .env.docker with all variables
4. Add health checks and configure networking
