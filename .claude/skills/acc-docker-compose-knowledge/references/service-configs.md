# Docker Compose Service Configurations

Complete YAML configurations for common services in a PHP stack.

## PostgreSQL

```yaml
postgres:
  image: postgres:16-alpine
  ports:
    - "${POSTGRES_PORT:-5432}:5432"
  environment:
    POSTGRES_USER: ${POSTGRES_USER:-app}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-secret}
    POSTGRES_DB: ${POSTGRES_DB:-app}
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app} -d ${POSTGRES_DB:-app}"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 10s
  networks:
    - backend
  restart: unless-stopped
```

## MySQL

```yaml
mysql:
  image: mysql:8.4
  ports:
    - "${MYSQL_PORT:-3306}:3306"
  environment:
    MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD:-root}
    MYSQL_DATABASE: ${MYSQL_DATABASE:-app}
    MYSQL_USER: ${MYSQL_USER:-app}
    MYSQL_PASSWORD: ${MYSQL_PASSWORD:-secret}
  volumes:
    - mysql-data:/var/lib/mysql
    - ./docker/mysql/my.cnf:/etc/mysql/conf.d/custom.cnf:ro
  healthcheck:
    test: ["CMD", "mysqladmin", "ping", "-h", "localhost", "-u", "root", "-p${MYSQL_ROOT_PASSWORD:-root}"]
    interval: 5s
    timeout: 5s
    retries: 5
    start_period: 20s
  networks:
    - backend
  restart: unless-stopped
```

## Redis

```yaml
redis:
  image: redis:7-alpine
  ports:
    - "${REDIS_PORT:-6379}:6379"
  command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis-data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 3
  networks:
    - backend
  restart: unless-stopped
```

## RabbitMQ

```yaml
rabbitmq:
  image: rabbitmq:3.13-management-alpine
  ports:
    - "${RABBITMQ_PORT:-5672}:5672"
    - "${RABBITMQ_MGMT_PORT:-15672}:15672"
  environment:
    RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER:-guest}
    RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD:-guest}
    RABBITMQ_DEFAULT_VHOST: ${RABBITMQ_VHOST:-/}
  volumes:
    - rabbitmq-data:/var/lib/rabbitmq
    - ./docker/rabbitmq/definitions.json:/etc/rabbitmq/definitions.json:ro
    - ./docker/rabbitmq/rabbitmq.conf:/etc/rabbitmq/rabbitmq.conf:ro
  healthcheck:
    test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
    interval: 10s
    timeout: 10s
    retries: 5
    start_period: 30s
  networks:
    - backend
  restart: unless-stopped
```

## Elasticsearch

```yaml
elasticsearch:
  image: elasticsearch:8.15.0
  ports:
    - "${ELASTICSEARCH_PORT:-9200}:9200"
  environment:
    discovery.type: single-node
    xpack.security.enabled: "false"
    ES_JAVA_OPTS: "-Xms512m -Xmx512m"
    cluster.name: app-cluster
  volumes:
    - elasticsearch-data:/usr/share/elasticsearch/data
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:9200/_cluster/health || exit 1"]
    interval: 10s
    timeout: 10s
    retries: 5
    start_period: 30s
  networks:
    - backend
  restart: unless-stopped
  deploy:
    resources:
      limits:
        memory: 1G
```

## Nginx

```yaml
nginx:
  image: nginx:1.27-alpine
  ports:
    - "${NGINX_PORT:-80}:80"
    - "${NGINX_SSL_PORT:-443}:443"
  volumes:
    - ./docker/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro
    - ./docker/nginx/ssl:/etc/nginx/ssl:ro
    - ./public:/app/public:ro
  depends_on:
    php:
      condition: service_healthy
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost/health"]
    interval: 10s
    timeout: 5s
    retries: 3
  networks:
    - frontend
  restart: unless-stopped
```

### Nginx Default Config (referenced above)

```nginx
# docker/nginx/default.conf
server {
    listen 80;
    server_name _;
    root /app/public;
    index index.php;

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
        internal;
    }

    location ~ \.php$ {
        return 404;
    }

    location /health {
        access_log off;
        return 200 "OK";
    }
}
```

## Mailhog

```yaml
mailhog:
  image: mailhog/mailhog:latest
  ports:
    - "${MAILHOG_SMTP_PORT:-1025}:1025"
    - "${MAILHOG_UI_PORT:-8025}:8025"
  networks:
    - frontend
    - backend
  profiles:
    - dev
```

## MinIO (S3-Compatible Storage)

```yaml
minio:
  image: minio/minio:latest
  ports:
    - "${MINIO_PORT:-9000}:9000"
    - "${MINIO_CONSOLE_PORT:-9001}:9001"
  command: server /data --console-address ":9001"
  environment:
    MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
    MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
  volumes:
    - minio-data:/data
  healthcheck:
    test: ["CMD", "mc", "ready", "local"]
    interval: 10s
    timeout: 5s
    retries: 3
  networks:
    - backend
  restart: unless-stopped
```

## Complete Volumes Section

```yaml
volumes:
  postgres-data:
    driver: local
  mysql-data:
    driver: local
  redis-data:
    driver: local
  rabbitmq-data:
    driver: local
  elasticsearch-data:
    driver: local
  minio-data:
    driver: local
```
