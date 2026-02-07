# Docker Compose Patterns for PHP

Production-ready Docker Compose patterns for PHP applications with common service stacks.

## PHP-FPM + Nginx Pattern

### Minimal Setup

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./public:/var/www/html/public:ro
    depends_on:
      php-fpm:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  php-fpm:
    build:
      context: .
      target: production
    volumes:
      - ./public:/var/www/html/public:ro
    healthcheck:
      test: ["CMD-SHELL", "cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3
```

### Nginx Configuration for PHP-FPM

```nginx
# docker/nginx/conf.d/default.conf
server {
    listen 80;
    server_name _;
    root /var/www/html/public;
    index index.php;

    location / {
        try_files $uri $uri/ /index.php$is_args$args;
    }

    location ~ \.php$ {
        fastcgi_pass php-fpm:9000;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
        fastcgi_hide_header X-Powered-By;
    }

    location ~ /\.(ht|git|env) {
        deny all;
    }

    location /health {
        access_log off;
        return 200 "OK";
    }
}
```

## Full Stack: PHP-FPM + MySQL + Redis

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "80:80"
    volumes:
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - app-public:/var/www/html/public:ro
    depends_on:
      php-fpm:
        condition: service_healthy
    networks:
      - frontend
      - backend
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3

  php-fpm:
    build:
      context: .
      target: production
    environment:
      DATABASE_URL: "mysql://app:${DB_PASSWORD}@mysql:3306/app?charset=utf8mb4"
      REDIS_URL: "redis://redis:6379"
      APP_ENV: production
    depends_on:
      mysql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - backend
      - database
    healthcheck:
      test: ["CMD-SHELL", "cgi-fcgi -bind -connect 127.0.0.1:9000 || exit 1"]
      interval: 30s
      timeout: 5s
      retries: 3

  mysql:
    image: mysql:8.4
    environment:
      MYSQL_DATABASE: app
      MYSQL_USER: app
      MYSQL_PASSWORD: ${DB_PASSWORD}
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mysql-data:/var/lib/mysql
      - ./docker/mysql/my.cnf:/etc/mysql/conf.d/custom.cnf:ro
    networks:
      - database
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${DB_ROOT_PASSWORD}"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis-data:/data
    networks:
      - database
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  mysql-data:
  redis-data:
  app-public:

networks:
  frontend:
  backend:
    internal: true
  database:
    internal: true
```

## Development vs Production Compose Files

### Base File (docker-compose.yml)

```yaml
services:
  php-fpm:
    build:
      context: .
    environment:
      APP_ENV: ${APP_ENV:-production}

  mysql:
    image: mysql:8.4
    volumes:
      - mysql-data:/var/lib/mysql

volumes:
  mysql-data:
```

### Development Override (docker-compose.override.yml)

```yaml
services:
  php-fpm:
    build:
      target: development
    volumes:
      - .:/var/www/html
      - vendor:/var/www/html/vendor
    environment:
      APP_ENV: development
      XDEBUG_MODE: debug
      XDEBUG_CONFIG: "client_host=host.docker.internal client_port=9003"
    extra_hosts:
      - "host.docker.internal:host-gateway"

  mysql:
    ports:
      - "3306:3306"

  mailpit:
    image: axllent/mailpit
    ports:
      - "8025:8025"
      - "1025:1025"

volumes:
  vendor:
```

### Production Override (docker-compose.prod.yml)

```yaml
services:
  php-fpm:
    build:
      target: production
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=64M
    cap_drop:
      - ALL
    cap_add:
      - SETUID
      - SETGID
    security_opt:
      - no-new-privileges:true
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 512M
        reservations:
          cpus: "0.5"
          memory: 256M

  mysql:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
```

### Compose File Usage

```bash
# Development (uses docker-compose.yml + docker-compose.override.yml automatically)
docker compose up -d

# Production (explicit files, skips override)
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# CI/Testing
docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d
```

## Health Checks per Service

| Service | Check Method | Interval | Start Period |
|---------|-------------|----------|-------------|
| Nginx | `curl -f http://localhost/health` | 30s | 5s |
| PHP-FPM | `cgi-fcgi -bind -connect 127.0.0.1:9000` | 30s | 10s |
| MySQL | `mysqladmin ping -h localhost` | 10s | 30s |
| PostgreSQL | `pg_isready -U user -d dbname` | 10s | 30s |
| Redis | `redis-cli ping` | 10s | 5s |
| RabbitMQ | `rabbitmq-diagnostics -q ping` | 30s | 60s |
| Elasticsearch | `curl -f http://localhost:9200/_cluster/health` | 30s | 60s |

## Volume Strategies

### Named Volumes (Persistent Data)

```yaml
volumes:
  mysql-data:
    driver: local
  redis-data:
    driver: local
  upload-storage:
    driver: local
```

| Use Case | Volume Type | Example |
|----------|------------|---------|
| Database files | Named volume | `mysql-data:/var/lib/mysql` |
| Cache data | Named volume | `redis-data:/data` |
| File uploads | Named volume | `uploads:/var/www/html/storage` |

### Bind Mounts (Development)

```yaml
volumes:
  - ./src:/var/www/html/src          # Source code (hot reload)
  - ./docker/php/php.ini:/usr/local/etc/php/php.ini:ro  # Config
```

| Use Case | Volume Type | Example |
|----------|------------|---------|
| Source code (dev) | Bind mount | `./src:/var/www/html/src` |
| Config files | Bind mount (ro) | `./conf:/etc/nginx/conf.d:ro` |
| SSL certificates | Bind mount (ro) | `./certs:/etc/ssl/certs:ro` |

### tmpfs (Ephemeral)

```yaml
tmpfs:
  - /tmp:noexec,nosuid,size=64M
  - /var/www/html/var/cache:noexec,nosuid,size=128M
```

| Use Case | Volume Type | Example |
|----------|------------|---------|
| Temp files | tmpfs | `/tmp` |
| Framework cache | tmpfs | `var/cache` |
| Session files | tmpfs | `var/sessions` |

## Network Segmentation

```
┌─────────────────────────────────────────────────┐
│                  frontend network                  │
│  ┌─────────┐                                      │
│  │  Nginx  │ ← port 80/443 exposed                │
│  └────┬────┘                                      │
├───────┼─────────────────────────────────────────┤
│       │         backend network (internal)          │
│  ┌────┴────┐  ┌─────────┐  ┌─────────┐          │
│  │ PHP-FPM │  │ Worker  │  │  Cron   │          │
│  └────┬────┘  └────┬────┘  └────┬────┘          │
├───────┼─────────────┼───────────┼────────────────┤
│       │             │           │                   │
│       │    database network (internal)              │
│  ┌────┴────┐  ┌────┴────┐  ┌──┴──────┐          │
│  │  MySQL  │  │  Redis  │  │RabbitMQ │          │
│  └─────────┘  └─────────┘  └─────────┘          │
└─────────────────────────────────────────────────┘
```

## Environment Variable Management

### .env File (Local Defaults)

```bash
# .env (committed — safe defaults only)
APP_ENV=development
APP_DEBUG=true
DB_HOST=mysql
DB_PORT=3306
DB_NAME=app
REDIS_HOST=redis
```

### .env.local (Secrets — Never Commit)

```bash
# .env.local (git-ignored)
DB_PASSWORD=secret_password
DB_ROOT_PASSWORD=root_secret
APP_SECRET=hex_random_string
```

### Variable Interpolation

```yaml
services:
  php-fpm:
    environment:
      DATABASE_URL: "mysql://${DB_USER:-app}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
```

## Service Profiles

```yaml
services:
  php-fpm:
    build:
      context: .

  mysql:
    image: mysql:8.4

  redis:
    image: redis:7-alpine

  # Development-only services
  mailpit:
    image: axllent/mailpit
    profiles: ["dev"]
    ports:
      - "8025:8025"

  phpmyadmin:
    image: phpmyadmin:latest
    profiles: ["dev"]
    ports:
      - "8080:80"

  # Testing-only services
  selenium:
    image: selenium/standalone-chrome
    profiles: ["test"]

  # Worker services
  queue-worker:
    build:
      context: .
      target: worker
    profiles: ["worker", "prod"]
    command: php bin/console messenger:consume async --time-limit=3600

  scheduler:
    build:
      context: .
      target: worker
    profiles: ["worker", "prod"]
    command: php bin/console schedule:run --no-interaction
```

```bash
# Development with dev tools
docker compose --profile dev up -d

# Production with workers
docker compose --profile prod --profile worker up -d

# CI testing
docker compose --profile test up -d
```

## Detection Patterns

```bash
# Check for health checks
Grep: "healthcheck" --glob "docker-compose*.yml"

# Check for network segmentation
Grep: "internal.*true" --glob "docker-compose*.yml"

# Check for resource limits
Grep: "limits:|memory:|cpus:" --glob "docker-compose*.yml"

# Warning: Hardcoded passwords
Grep: "PASSWORD.*=.*[^$]" --glob "docker-compose*.yml" | grep -v "\${"

# Warning: Exposed database ports
Grep: "3306:|5432:|6379:" --glob "docker-compose*.yml" --glob "!*override*"

# Check for depends_on with conditions
Grep: "condition.*service_healthy" --glob "docker-compose*.yml"
```
