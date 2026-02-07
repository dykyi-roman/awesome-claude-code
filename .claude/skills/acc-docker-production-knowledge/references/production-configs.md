# Production Configuration Reference

Production-ready configuration snippets for PHP Docker deployments.

## php.ini (Production)

```ini
[PHP]
; Error handling
display_errors = Off
display_startup_errors = Off
error_reporting = E_ALL
log_errors = On
error_log = /dev/stderr
log_errors_max_len = 4096

; Security
expose_php = Off
allow_url_fopen = Off
allow_url_include = Off
session.cookie_secure = 1
session.cookie_httponly = 1
session.cookie_samesite = Lax
session.use_strict_mode = 1

; Performance
memory_limit = 256M
max_execution_time = 30
max_input_time = 60
post_max_size = 50M
upload_max_filesize = 50M
max_file_uploads = 20

; Timezone
date.timezone = UTC

; Realpath cache
realpath_cache_size = 4096K
realpath_cache_ttl = 600

; Disable dangerous functions
disable_functions = exec,passthru,shell_exec,system,proc_open,popen,parse_ini_file,show_source

; Open basedir restriction
open_basedir = /var/www/html:/tmp:/var/lib/php/sessions
```

## OPcache Configuration (opcache.ini)

```ini
[opcache]
opcache.enable = 1
opcache.enable_cli = 1
opcache.memory_consumption = 256
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 20000
opcache.validate_timestamps = 0
opcache.save_comments = 1
opcache.fast_shutdown = 1

; JIT (PHP 8.x)
opcache.jit = 1255
opcache.jit_buffer_size = 256M

; Preloading
opcache.preload = /var/www/html/config/preload.php
opcache.preload_user = app

; File cache (backup cache on disk)
opcache.file_cache = /tmp/opcache
opcache.file_cache_only = 0
opcache.file_cache_consistency_checks = 1
```

## PHP-FPM Pool Configuration (www.conf)

```ini
[www]
; Process manager
user = app
group = app
listen = 0.0.0.0:9000
listen.owner = app
listen.group = app

; Dynamic pool management
pm = dynamic
pm.max_children = 50
pm.start_servers = 10
pm.min_spare_servers = 5
pm.max_spare_servers = 20
pm.max_requests = 1000
pm.process_idle_timeout = 10s

; Status and health
pm.status_path = /fpm-status
ping.path = /ping
ping.response = pong

; Logging
access.log = /dev/stdout
access.format = '{"time":"%{%Y-%m-%dT%H:%M:%S%z}T","method":"%m","uri":"%r","status":"%s","duration_ms":"%{mili}d","memory_mb":"%{mega}M","cpu":"%C%%"}'

; Slow request logging
request_slowlog_timeout = 5s
slowlog = /dev/stderr

; Timeouts
request_terminate_timeout = 60s

; Security
security.limit_extensions = .php
php_admin_flag[log_errors] = on
php_admin_value[error_log] = /dev/stderr
```

## Nginx Configuration (PHP-FPM Upstream)

```nginx
upstream php-fpm {
    server php:9000;
    keepalive 16;
}

server {
    listen 80;
    server_name _;
    root /var/www/html/public;
    index index.php;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'" always;

    # Hide server version
    server_tokens off;

    # Request size limits
    client_max_body_size 50M;
    client_body_buffer_size 128k;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
    fastcgi_read_timeout 60s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;

    # Health check endpoint
    location /health {
        access_log off;
        return 200 '{"status":"healthy"}';
        add_header Content-Type application/json;
    }

    # PHP-FPM status (restrict access)
    location ~ ^/(fpm-status|ping)$ {
        allow 127.0.0.1;
        allow 10.0.0.0/8;
        allow 172.16.0.0/12;
        deny all;
        fastcgi_pass php-fpm;
        fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        include fastcgi_params;
    }

    # Static files with cache
    location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg|woff2?)$ {
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
        try_files $uri =404;
    }

    # PHP handling
    location / {
        try_files $uri /index.php$is_args$args;
    }

    location ~ \.php$ {
        fastcgi_pass php-fpm;
        fastcgi_split_path_info ^(.+\.php)(/.*)$;
        fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
        fastcgi_param DOCUMENT_ROOT $realpath_root;
        include fastcgi_params;

        # Buffer settings
        fastcgi_buffer_size 128k;
        fastcgi_buffers 4 256k;
        fastcgi_busy_buffers_size 256k;

        # Prevent access to dotfiles
        internal;
    }

    # Deny access to hidden files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    # Deny access to sensitive files
    location ~* \.(env|log|yml|yaml|ini|conf|bak|sql)$ {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```
