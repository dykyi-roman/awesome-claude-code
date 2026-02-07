---
name: acc-check-docker-compose-config
description: Checks Docker Compose configuration for PHP stacks. Detects missing health checks, improper dependencies, hardcoded values, and networking issues.
---

# Docker Compose Configuration Checker

Analyze Docker Compose files for configuration issues in PHP application stacks.

## Detection Patterns

### 1. Missing Health Checks

```yaml
# BAD: No healthcheck section for service
# GOOD: Health check present
services:
  php-fpm:
    healthcheck:
      test: ["CMD-SHELL", "php-fpm-healthcheck || exit 1"]
      interval: 10s
      timeout: 3s
      retries: 3
```

### 2. depends_on Without Condition

```yaml
# BAD: No health condition (race condition on startup)
services:
  app:
    depends_on:
      - mysql

# GOOD: Health condition enforced
services:
  app:
    depends_on:
      mysql:
        condition: service_healthy
```

### 3. Hardcoded Passwords

```yaml
# BAD: Credentials in plain text
services:
  mysql:
    environment:
      MYSQL_ROOT_PASSWORD: secret123

# GOOD: Using .env file reference
services:
  mysql:
    env_file: [.env]
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
```

### 4. No Resource Limits

```yaml
# GOOD: Resource limits defined
services:
  php-fpm:
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
```

### 5. No Restart Policy

```yaml
# GOOD: Restart policy defined
services:
  app:
    restart: unless-stopped
```

### 6. Deprecated version Field

```yaml
# BAD: Deprecated in Compose V2+
version: "3.8"
services:
  app:
    image: my-app
```

### 7. Missing Networks Definition

```yaml
# GOOD: Explicit network isolation
services:
  app:
    networks: [frontend, backend]
  mysql:
    networks: [backend]
networks:
  frontend:
  backend:
    internal: true
```

### 8. Volume Permission Issues

```yaml
# GOOD: User mapping to avoid permission issues
services:
  php-fpm:
    user: "${UID:-1000}:${GID:-1000}"
    volumes:
      - ./src:/var/www/html
```

### 9. Port Conflicts

```yaml
# BAD: Binding to all interfaces — ports: ["80:80"]
# GOOD: Specific host binding — ports: ["127.0.0.1:8080:80"]
```

### 10. Missing .env File Reference

```yaml
# GOOD: Explicit env_file with variable interpolation
services:
  app:
    env_file: [.env]
```

## Grep Patterns

```bash
# Hardcoded passwords
Grep: "PASSWORD.*:.*['\"]?[a-zA-Z0-9]" --glob "**/docker-compose*.yml"

# depends_on without condition
Grep: "depends_on:" --glob "**/docker-compose*.yml"

# Deprecated version field
Grep: "^version:" --glob "**/docker-compose*.yml"

# Port bindings
Grep: "ports:" --glob "**/docker-compose*.yml"
```

## Severity Classification

| Pattern | Severity | Impact |
|---------|----------|--------|
| Hardcoded credentials | Critical | Security breach risk |
| No health checks | Major | Unreliable dependencies |
| depends_on without condition | Major | Race conditions on startup |
| No resource limits | Major | OOM kills, resource exhaustion |
| Port conflicts | Major | Service startup failure |
| Missing networks | Minor | No network isolation |
| Deprecated version field | Minor | Compatibility warning |
| No restart policy | Minor | Manual recovery needed |
| Volume permissions | Minor | File access errors |
| Missing .env reference | Minor | Undefined variable risk |

## Output Format

```markdown
### Compose Issue: [Description]

**Severity:** Critical/Major/Minor
**File:** `docker-compose.yml:line`
**Issue:** [Description of the problem]
**Fix:** [Corrected configuration snippet]
**Impact:** [What could happen if not fixed]
```
