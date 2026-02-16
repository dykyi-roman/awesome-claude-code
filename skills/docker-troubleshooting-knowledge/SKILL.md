---
name: acc-docker-troubleshooting-knowledge
description: Docker troubleshooting knowledge base. Provides debugging patterns, common error solutions, and diagnostic commands for PHP containers.
---

# Docker Troubleshooting Knowledge Base

Quick reference for debugging Docker containers in PHP projects.

## Common Build Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `failed to compute cache key` | File not in build context | Check `.dockerignore`, verify file path |
| `returned a non-zero code: 137` | OOM during build | Increase Docker memory or reduce parallel ops |
| `Could not find package` | Composer can't resolve deps | Check `composer.lock`, mount auth secrets |
| `E: Unable to locate package` | Missing apt repository | Add required repo or use correct base image |
| `configure: error: ... not found` | Missing dev library | Install `-dev` package before ext install |
| `Permission denied` | Wrong user/permissions | Fix `chown`/`chmod` or adjust USER directive |
| `COPY failed: file not found` | File not in context | Check path relative to Dockerfile, check `.dockerignore` |
| `max depth exceeded` | Too many layers | Combine RUN commands, use multi-stage build |

## Common Runtime Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `502 Bad Gateway` | PHP-FPM not running or crashed | Check FPM logs, verify listen address |
| `Connection refused (port 9000)` | FPM not listening | Check `listen` directive, container networking |
| `OOM Killed` | Memory limit exceeded | Increase limits, tune `pm.max_children` |
| `No space left on device` | Disk/overlay full | Prune images/volumes, increase disk |
| `exec format error` | Wrong platform image | Build for correct arch (`linux/amd64`) |
| `name resolution failure` | DNS issue | Check network config, service names |
| `read-only file system` | Read-only FS enabled | Mount tmpfs for writable dirs |
| `file not found (FastCGI)` | Wrong SCRIPT_FILENAME | Check nginx root and fastcgi params |

## Diagnostic Commands

### Container Inspection

```bash
# View container logs (last 100 lines, follow)
docker logs --tail 100 -f <container>

# Execute command inside running container
docker exec -it <container> sh

# Inspect container configuration
docker inspect <container>

# Container resource usage (live)
docker stats <container>

# List processes inside container
docker top <container>

# View container events
docker events --filter container=<container>

# Check container health status
docker inspect --format='{{json .State.Health}}' <container> | jq
```

### Image Inspection

```bash
# View image layers and sizes
docker history <image>

# Inspect image metadata
docker inspect <image>

# Check image size
docker images <image> --format '{{.Size}}'

# Export image filesystem for inspection
docker save <image> | tar -tvf -
```

### Resource Diagnostics

```bash
# Disk usage summary
docker system df

# Detailed disk usage
docker system df -v

# Prune unused resources
docker system prune -a --volumes

# List dangling images
docker images -f "dangling=true"
```

## PHP-FPM Debugging

### Enable Slow Log

```ini
; www.conf
request_slowlog_timeout = 3s
slowlog = /dev/stderr
```

### Enable Access Log with Timing

```ini
access.log = /dev/stdout
access.format = '{"time":"%T","method":"%m","uri":"%r","status":"%s","duration":"%d","memory":"%{mega}M"}'
```

### Check FPM Status

```bash
# Enable status page in www.conf
# pm.status_path = /fpm-status

# Query FPM status
docker exec <container> sh -c \
    'SCRIPT_NAME=/fpm-status SCRIPT_FILENAME=/fpm-status REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect 127.0.0.1:9000'

# Full status (per-process details)
docker exec <container> sh -c \
    'SCRIPT_NAME=/fpm-status SCRIPT_FILENAME=/fpm-status QUERY_STRING=full REQUEST_METHOD=GET \
    cgi-fcgi -bind -connect 127.0.0.1:9000'
```

### Check PHP Configuration

```bash
# View loaded PHP modules
docker exec <container> php -m

# View PHP configuration
docker exec <container> php -i | grep -i opcache

# Check for configuration errors
docker exec <container> php -r "phpinfo();" | grep -i error

# Validate PHP syntax
docker exec <container> php -l /var/www/html/public/index.php
```

## Network Debugging

### DNS Resolution

```bash
# Check DNS from inside container
docker exec <container> nslookup postgres
docker exec <container> getent hosts postgres

# Check network connectivity
docker exec <container> ping -c 3 postgres

# Check port connectivity
docker exec <container> nc -zv postgres 5432

# List container networks
docker inspect <container> --format='{{json .NetworkSettings.Networks}}' | jq
```

### Port Mapping

```bash
# Check port bindings
docker port <container>

# Check listening ports inside container
docker exec <container> netstat -tlnp
# or with ss
docker exec <container> ss -tlnp
```

### Network Inspection

```bash
# List all networks
docker network ls

# Inspect network
docker network inspect <network>

# Check connected containers
docker network inspect <network> --format='{{json .Containers}}' | jq
```

## Volume and Permission Debugging

### Permission Issues

```bash
# Check file ownership inside container
docker exec <container> ls -la /var/www/html

# Check running user
docker exec <container> whoami
docker exec <container> id

# Fix permissions (temporary)
docker exec -u root <container> chown -R app:app /var/www/html
```

### Volume Issues

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect <volume>

# Check volume mount points
docker inspect <container> --format='{{json .Mounts}}' | jq

# Verify volume contents
docker run --rm -v <volume>:/data alpine ls -la /data
```

## Compose-Specific Debugging

```bash
# View all service statuses
docker compose ps

# View service logs (all services)
docker compose logs -f

# View specific service logs
docker compose logs -f php

# Validate compose file
docker compose config

# Recreate specific service
docker compose up -d --force-recreate php

# View service events
docker compose events
```

## Quick Diagnosis Flowchart

```
Container not starting?
  |
  +-- Check: docker logs <container>
  |     |
  |     +-- Permission error --> Fix chown/chmod or USER
  |     +-- Config error --> Validate config files
  |     +-- OOM killed --> Increase memory limits
  |
  +-- Check: docker inspect <container> | grep State
        |
        +-- Restarting --> Check restart policy + logs
        +-- Exited --> Check exit code (137=OOM, 1=error)

502 Bad Gateway?
  |
  +-- Check: docker exec php ps aux (is FPM running?)
  |     |
  |     +-- Not running --> Check FPM config + logs
  |     +-- Running --> Check nginx upstream config
  |
  +-- Check: docker exec nginx curl http://php:9000/ping
        |
        +-- Connection refused --> Wrong listen address
        +-- Timeout --> FPM overloaded, check pm settings
```

## References

For detailed information, load these reference files:

- `references/error-solutions.md` -- 20+ common Docker PHP errors with solutions
