# Reusable Nginx Snippets

## SSL/TLS Configuration

```nginx
# ssl.conf — Modern SSL configuration (Mozilla Intermediate)
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_trusted_certificate /etc/nginx/ssl/chain.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_timeout 1d;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;

    # OCSP stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    # HSTS
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

## Rate Limiting

```nginx
# Rate limiting zones (place in http block)
limit_req_zone $binary_remote_addr zone=api:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
limit_req_zone $binary_remote_addr zone=general:10m rate=100r/s;

# Apply rate limits (place in location blocks)
location /api/ {
    limit_req zone=api burst=50 nodelay;
    limit_req_status 429;
    try_files $uri /index.php$is_args$args;
}

location ~ ^/(login|register|password) {
    limit_req zone=login burst=3 nodelay;
    limit_req_status 429;
    try_files $uri /index.php$is_args$args;
}
```

## Access Control

```nginx
# IP-based access control
location /admin {
    allow 10.0.0.0/8;
    allow 172.16.0.0/12;
    allow 192.168.0.0/16;
    deny all;
    try_files $uri /index.php$is_args$args;
}

# Basic authentication
location /monitoring {
    auth_basic "Restricted";
    auth_basic_user_file /etc/nginx/.htpasswd;
    try_files $uri /index.php$is_args$args;
}
```

## WebSocket Proxy

```nginx
# WebSocket upgrade support
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}

location /ws {
    proxy_pass http://websocket_backend;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection $connection_upgrade;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_read_timeout 86400s;
    proxy_send_timeout 86400s;
}
```

## File Upload Configuration

```nginx
# Large file upload support
location /api/upload {
    client_max_body_size 256M;
    client_body_buffer_size 1M;
    client_body_temp_path /tmp/nginx-uploads;

    proxy_request_buffering off;
    proxy_read_timeout 600s;

    try_files $uri /index.php$is_args$args;
}
```

## Custom Error Pages

```nginx
# Custom error pages
error_page 404 /404.html;
error_page 500 502 503 504 /50x.html;

location = /404.html {
    root /app/public/errors;
    internal;
}

location = /50x.html {
    root /app/public/errors;
    internal;
}

# JSON error responses for API
location /api/ {
    error_page 404 = @api_404;
    error_page 500 502 503 504 = @api_50x;
    try_files $uri /index.php$is_args$args;
}

location @api_404 {
    default_type application/json;
    return 404 '{"error": "Not Found", "status": 404}';
}

location @api_50x {
    default_type application/json;
    return 500 '{"error": "Internal Server Error", "status": 500}';
}
```

## Proxy Headers (behind load balancer)

```nginx
# Real IP from trusted proxies
set_real_ip_from 10.0.0.0/8;
set_real_ip_from 172.16.0.0/12;
set_real_ip_from 192.168.0.0/16;
real_ip_header X-Forwarded-For;
real_ip_recursive on;

# Forward headers to PHP-FPM
fastcgi_param HTTP_X_REAL_IP $remote_addr;
fastcgi_param HTTP_X_FORWARDED_FOR $proxy_add_x_forwarded_for;
fastcgi_param HTTP_X_FORWARDED_PROTO $scheme;
```

## Cache Bypass for Authenticated Users

```nginx
# Skip cache for logged-in users
map $http_cookie $skip_cache {
    default 0;
    ~PHPSESSID 1;
    ~remember_token 1;
}

location / {
    proxy_cache app_cache;
    proxy_cache_bypass $skip_cache;
    proxy_no_cache $skip_cache;
    proxy_cache_valid 200 10m;
    proxy_cache_valid 404 1m;
    try_files $uri /index.php$is_args$args;
}
```
