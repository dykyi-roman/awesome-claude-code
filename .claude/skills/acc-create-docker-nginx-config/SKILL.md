---
name: acc-create-docker-nginx-config
description: Generates Nginx configuration for PHP-FPM Docker containers. Creates optimized reverse proxy configs with gzip, security headers, and caching.
---

# Docker Nginx Configuration Generator

Generates production-ready Nginx configurations for PHP-FPM Docker containers.

## Generated Files

```
docker/nginx/
  nginx.conf                # Main Nginx configuration
  conf.d/default.conf       # Server block configuration
  conf.d/upstream.conf      # PHP-FPM upstream definition
```

## Main nginx.conf

```nginx
# nginx.conf
user nginx;
worker_processes auto;
worker_rlimit_nofile 65535;
pid /var/run/nginx.pid;
error_log /var/log/nginx/error.log warn;

events {
    worker_connections 4096;
    multi_accept on;
    use epoll;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # Logging
    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for" '
                    'rt=$request_time';
    access_log /var/log/nginx/access.log main;

    # Performance
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;

    # Request size limits
    client_max_body_size 64M;
    client_body_buffer_size 128k;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/javascript
        application/json
        application/xml
        application/xml+rss
        image/svg+xml
        font/woff2;

    # Security headers (applied globally)
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self';" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

    include /etc/nginx/conf.d/*.conf;
}
```

## PHP-FPM Upstream Configuration

```nginx
# conf.d/upstream.conf
upstream php-fpm {
    server php:9000;
    keepalive 32;
}
```

## Symfony Server Block

```nginx
# conf.d/default.conf — Symfony application
server {
    listen 80;
    listen [::]:80;
    server_name _;
    root /app/public;
    index index.php;

    # Static file caching
    location ~* \.(ico|css|js|gif|jpeg|jpg|png|svg|woff|woff2|ttf|eot|webp|avif)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
        try_files $uri =404;
    }

    # Deny access to hidden files and sensitive paths
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
    location ~ ^/(config|var|vendor|translations|templates)/ {
        deny all;
    }

    # Health check endpoint (no logging)
    location = /health {
        access_log off;
        try_files $uri /index.php$is_args$args;
    }

    # PHP handling — Symfony front controller
    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ ^/index\.php(/|$) {
        fastcgi_pass php-fpm;
        fastcgi_split_path_info ^(.+\.php)(/.*)$;
        include fastcgi_params;

        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT $realpath_root;

        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_busy_buffers_size 256k;
        fastcgi_read_timeout 300;
        fastcgi_connect_timeout 10;

        # Prevent URI from being passed to PHP for other .php files
        internal;
    }

    # Deny access to any other .php files
    location ~ \.php$ {
        return 404;
    }
}
```

## Laravel Server Block

```nginx
# conf.d/default.conf — Laravel application
server {
    listen 80;
    listen [::]:80;
    server_name _;
    root /app/public;
    index index.php;

    # Static file caching
    location ~* \.(ico|css|js|gif|jpeg|jpg|png|svg|woff|woff2|ttf|eot|webp|avif)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
        try_files $uri =404;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Health check endpoint
    location = /health {
        access_log off;
        try_files $uri /index.php$is_args$args;
    }

    # Laravel front controller
    location / {
        try_files $uri $uri/ /index.php?$query_string;
    }

    location ~ \.php$ {
        fastcgi_pass php-fpm;
        fastcgi_index index.php;
        include fastcgi_params;

        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT $realpath_root;

        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_busy_buffers_size 256k;
        fastcgi_read_timeout 300;
        fastcgi_connect_timeout 10;
    }
}
```

## Docker Compose Nginx Service

```yaml
services:
  nginx:
    image: nginx:1.27-alpine
    ports:
      - "${NGINX_PORT:-80}:80"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./docker/nginx/conf.d:/etc/nginx/conf.d:ro
      - ./public:/app/public:ro
    depends_on:
      php:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 5s
      retries: 3
```

## Generation Instructions

1. **Detect framework:** Symfony (public/index.php) or Laravel (public/index.php)
2. **Identify requirements:** upload size, WebSocket, SSL
3. **Generate nginx.conf** with tuned workers and gzip
4. **Generate server block** with framework-specific try_files
5. **Add security headers** and static file caching

See `references/nginx-snippets.md` for SSL, rate limiting, and advanced snippets.
