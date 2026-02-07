# Docker PHP Error Solutions Reference

Common Docker PHP errors with symptoms, causes, and solutions.

## Build Errors

### 1. Extension Compilation Failure

**Symptoms:** `configure: error: ... not found` during `docker-php-ext-install`
**Cause:** Missing development libraries required for PHP extension compilation.
**Solution:**
```dockerfile
# Alpine
RUN apk add --no-cache libzip-dev icu-dev libpq-dev oniguruma-dev && \
    docker-php-ext-install zip intl pdo_pgsql mbstring

# Debian
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzip-dev libicu-dev libpq-dev libonig-dev && \
    docker-php-ext-install zip intl pdo_pgsql mbstring
```

### 2. Composer Memory Exhaustion

**Symptoms:** `Allowed memory size of ... bytes exhausted` during `composer install`
**Cause:** PHP memory limit too low for dependency resolution.
**Solution:**
```dockerfile
RUN COMPOSER_MEMORY_LIMIT=-1 composer install --no-dev --prefer-dist
```

### 3. Composer Authentication Failure

**Symptoms:** `Could not find a matching version` or `401 Unauthorized`
**Cause:** Missing authentication for private repositories.
**Solution:**
```dockerfile
RUN --mount=type=secret,id=composer_auth,target=/root/.composer/auth.json \
    composer install --no-dev --prefer-dist
```

### 4. COPY File Not Found

**Symptoms:** `COPY failed: file not found in build context`
**Cause:** File excluded by `.dockerignore` or wrong path.
**Solution:** Check `.dockerignore` does not exclude the file. Verify path is relative to build context root.

### 5. Layer Cache Invalidation

**Symptoms:** Build takes long despite no code changes.
**Cause:** `COPY . .` placed before dependency installation.
**Solution:**
```dockerfile
COPY composer.json composer.lock ./
RUN composer install --no-dev
COPY . .
```

## Runtime Errors

### 6. 502 Bad Gateway

**Symptoms:** Nginx returns 502 when accessing PHP pages.
**Cause:** PHP-FPM not running, wrong listen address, or crashed.
**Solution:**
```nginx
# Verify upstream matches FPM listen directive
upstream php-fpm {
    server php:9000;  # Must match FPM container name and port
}
```
```ini
; www.conf - ensure correct listen address
listen = 0.0.0.0:9000
```

### 7. Connection Refused on Port 9000

**Symptoms:** `connect() failed (111: Connection refused)` in nginx logs.
**Cause:** PHP-FPM not listening on expected address.
**Solution:** Verify `listen` in `www.conf` matches the address nginx expects. Check container is on same Docker network.

### 8. OOM Killed (Exit Code 137)

**Symptoms:** Container exits with code 137, `docker inspect` shows `OOMKilled: true`.
**Cause:** PHP processes exceed container memory limit.
**Solution:**
```yaml
services:
  php:
    deploy:
      resources:
        limits:
          memory: 512M
```
```ini
; Reduce FPM workers
pm.max_children = 10
```

### 9. Permission Denied on Mounted Volume

**Symptoms:** `Permission denied` when writing to mounted volume.
**Cause:** UID/GID mismatch between container user and host filesystem.
**Solution:**
```dockerfile
RUN addgroup -g 1000 -S app && adduser -u 1000 -S app -G app
USER app
```
Ensure host directory is owned by UID 1000.

### 10. File Not Found (FastCGI)

**Symptoms:** `Primary script unknown` or `File not found` in FPM logs.
**Cause:** `SCRIPT_FILENAME` parameter incorrect in nginx config.
**Solution:**
```nginx
location ~ \.php$ {
    fastcgi_param SCRIPT_FILENAME $realpath_root$fastcgi_script_name;
    fastcgi_param DOCUMENT_ROOT $realpath_root;
}
```

### 11. Slow Response Times

**Symptoms:** Requests take seconds to respond.
**Cause:** OPcache disabled, FPM pool exhausted, or database connection issues.
**Solution:**
```ini
; Enable OPcache
opcache.enable=1
opcache.validate_timestamps=0
```
Enable FPM slow log: `request_slowlog_timeout = 3s`

### 12. Session Lost Between Requests

**Symptoms:** Users logged out randomly, session data missing.
**Cause:** Session files stored locally in ephemeral container filesystem.
**Solution:**
```yaml
volumes:
  - php-sessions:/var/lib/php/sessions
```
Or use Redis for sessions:
```ini
session.save_handler = redis
session.save_path = "tcp://redis:6379"
```

### 13. DNS Resolution Failure

**Symptoms:** `php_network_getaddresses: getaddrinfo failed`
**Cause:** Container DNS not resolving service names.
**Solution:** Ensure services are on the same Docker network. Use service name (not `localhost` or IP).

### 14. Read-Only Filesystem Error

**Symptoms:** `Read-only file system` when writing temp files or logs.
**Cause:** Container has `read_only: true` without tmpfs for writable paths.
**Solution:**
```yaml
services:
  php:
    read_only: true
    tmpfs:
      - /tmp:size=64M
      - /var/run:size=1M
      - /var/log:size=32M
```

### 15. Xdebug Slowing Production

**Symptoms:** Extremely slow response times in production.
**Cause:** Xdebug or other debug extensions enabled in production image.
**Solution:** Use multi-stage build, only install Xdebug in dev target:
```dockerfile
FROM php:8.4-fpm-alpine AS base
# ... production setup ...

FROM base AS dev
RUN pecl install xdebug && docker-php-ext-enable xdebug

FROM base AS production
# No xdebug here
```

### 16. Timezone Mismatch

**Symptoms:** Log timestamps wrong, scheduled tasks run at wrong time.
**Cause:** Container uses UTC but application expects different timezone.
**Solution:**
```ini
; php.ini
date.timezone = UTC
```
Always use UTC internally, convert for display.

### 17. Upload File Size Exceeded

**Symptoms:** `413 Request Entity Too Large` or PHP upload errors.
**Cause:** Size limits in nginx and/or PHP not matching.
**Solution:**
```nginx
client_max_body_size 50M;
```
```ini
upload_max_filesize = 50M
post_max_size = 55M
```

### 18. Container Keeps Restarting

**Symptoms:** Container in restart loop, `docker ps` shows frequent restarts.
**Cause:** Application crashes on startup (config error, missing env vars).
**Solution:** Check logs with `docker logs <container>`. Verify all required environment variables are set.

### 19. Build Context Too Large

**Symptoms:** `Sending build context to Docker daemon` takes minutes.
**Cause:** Large files (vendor, node_modules, .git) in build context.
**Solution:**
```
# .dockerignore
.git
vendor
node_modules
tests
*.md
docker-compose*.yml
```

### 20. Port Already in Use

**Symptoms:** `Bind for 0.0.0.0:80: port is already allocated`
**Cause:** Another container or host process using the same port.
**Solution:**
```bash
# Find what's using the port
lsof -i :80
# Or change the host port mapping
ports:
  - "8080:80"
```

### 21. Composer Autoload Not Working

**Symptoms:** `Class not found` errors after deployment.
**Cause:** Autoloader not regenerated after copying source files.
**Solution:**
```dockerfile
COPY --from=deps /app/vendor /var/www/html/vendor
COPY . /var/www/html
RUN composer dump-autoload --optimize --classmap-authoritative
```

### 22. PHP Extensions Missing at Runtime

**Symptoms:** `Call to undefined function` or `Class not found` for extension classes.
**Cause:** Extension installed in build stage but not copied to final stage.
**Solution:**
```dockerfile
COPY --from=php-ext /usr/local/lib/php/extensions/ /usr/local/lib/php/extensions/
COPY --from=php-ext /usr/local/etc/php/conf.d/ /usr/local/etc/php/conf.d/
```
