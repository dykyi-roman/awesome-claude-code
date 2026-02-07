# Docker Compose Service Templates

Composable service blocks for Docker Compose development configurations.

## MySQL 8.4

```yaml
  mysql:
    image: mysql:8.4
    ports:
      - "${MYSQL_PORT:-3306}:3306"
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      MYSQL_DATABASE: ${MYSQL_DATABASE:-app_dev}
      MYSQL_USER: ${MYSQL_USER:-app}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD:-secret}
    volumes:
      - mysql-data:/var/lib/mysql
      - ./docker/mysql/my.cnf:/etc/mysql/conf.d/custom.cnf:ro
    command: >
      --default-authentication-plugin=caching_sha2_password
      --character-set-server=utf8mb4
      --collation-server=utf8mb4_unicode_ci
      --innodb-buffer-pool-size=256M
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - app-network
```

## PostgreSQL 17

```yaml
  postgres:
    image: postgres:17-alpine
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-app_dev}
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
      interval: 5s
      timeout: 5s
      retries: 10
    networks:
      - app-network
```

## Redis 7

```yaml
  redis:
    image: redis:7-alpine
    ports:
      - "${REDIS_PORT:-6379}:6379"
    command: >
      redis-server
      --appendonly yes
      --maxmemory 128mb
      --maxmemory-policy allkeys-lru
      --save 60 1000
    volumes:
      - redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - app-network
```

## RabbitMQ 3.13

```yaml
  rabbitmq:
    image: rabbitmq:3.13-management-alpine
    ports:
      - "${RABBITMQ_PORT:-5672}:5672"
      - "${RABBITMQ_MGMT_PORT:-15672}:15672"
    environment:
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-guest}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASS:-guest}
      RABBITMQ_DEFAULT_VHOST: /
    volumes:
      - rabbitmq-data:/var/lib/rabbitmq
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_running"]
      interval: 10s
      timeout: 10s
      retries: 5
    networks:
      - app-network
```

## Elasticsearch 8

```yaml
  elasticsearch:
    image: elasticsearch:8.15.0
    ports:
      - "${ES_PORT:-9200}:9200"
    environment:
      discovery.type: single-node
      xpack.security.enabled: "false"
      ES_JAVA_OPTS: "-Xms512m -Xmx512m"
    volumes:
      - es-data:/usr/share/elasticsearch/data
    healthcheck:
      test: ["CMD-SHELL", "curl -fsSL http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\\|yellow\"'"]
      interval: 10s
      timeout: 10s
      retries: 10
    networks:
      - app-network
```

## Nginx 1.27

```yaml
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
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost/ping"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - app-network
```

## Mailhog (Email Testing)

```yaml
  mailhog:
    image: mailhog/mailhog:latest
    ports:
      - "${MAILHOG_SMTP:-1025}:1025"
      - "${MAILHOG_UI:-8025}:8025"
    healthcheck:
      test: ["CMD", "wget", "-qO-", "http://localhost:8025"]
      interval: 10s
      timeout: 5s
      retries: 3
    networks:
      - app-network
```

## MinIO (S3-Compatible Storage)

```yaml
  minio:
    image: minio/minio:latest
    ports:
      - "${MINIO_PORT:-9000}:9000"
      - "${MINIO_CONSOLE:-9001}:9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD:-minioadmin}
    volumes:
      - minio-data:/data
    command: server /data --console-address ":9001"
    healthcheck:
      test: ["CMD", "mc", "ready", "local"]
      interval: 10s
      timeout: 5s
      retries: 5
    networks:
      - app-network
```

## phpMyAdmin

```yaml
  phpmyadmin:
    image: phpmyadmin:5
    ports:
      - "${PMA_PORT:-8081}:80"
    environment:
      PMA_HOST: mysql
      PMA_PORT: 3306
      PMA_USER: root
      PMA_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
      UPLOAD_LIMIT: 100M
    depends_on:
      mysql:
        condition: service_healthy
    networks:
      - app-network
```

## Adminer (Multi-DB Admin)

```yaml
  adminer:
    image: adminer:latest
    ports:
      - "${ADMINER_PORT:-8082}:8080"
    environment:
      ADMINER_DEFAULT_SERVER: database
      ADMINER_DESIGN: dracula
    depends_on:
      database:
        condition: service_healthy
    networks:
      - app-network
```

## Traefik (Reverse Proxy)

```yaml
  traefik:
    image: traefik:v3.1
    ports:
      - "80:80"
      - "443:443"
      - "${TRAEFIK_DASHBOARD:-8090}:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./docker/traefik/traefik.yml:/etc/traefik/traefik.yml:ro
    command:
      - "--api.dashboard=true"
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    networks:
      - app-network
```

## Volumes Reference

```yaml
volumes:
  mysql-data:
    driver: local
  postgres-data:
    driver: local
  redis-data:
    driver: local
  rabbitmq-data:
    driver: local
  es-data:
    driver: local
  minio-data:
    driver: local
  vendor:
    driver: local
  composer-cache:
    driver: local
```
