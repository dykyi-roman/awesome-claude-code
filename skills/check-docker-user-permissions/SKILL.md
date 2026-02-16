---
name: acc-check-docker-user-permissions
description: Checks Docker user and permission configuration. Detects root execution, improper file ownership, and missing security constraints.
---

# Docker User and Permission Check

Analyze Docker configurations for user, ownership, and permission issues in PHP containers.

## Permission Check Patterns

| Check | Risk | Detection |
|-------|------|-----------|
| No USER instruction | Root execution | Missing `USER` in Dockerfile |
| Wrong UID/GID | Permission conflicts | Non-standard user IDs |
| COPY without --chown | Root-owned files | `COPY` without ownership |
| chmod 777 | World-writable files | Overly permissive mode |
| Volume permission mismatch | Read/write failures | Host vs container UID |
| Read-only FS incompatibility | Runtime crashes | Missing tmpfs for writable dirs |

## Detection Patterns

### 1. USER Instruction Present

```dockerfile
# INSECURE: No USER instruction (runs as root PID 1)
FROM php:8.4-fpm-alpine
COPY . /var/www/
CMD ["php-fpm"]

# SECURE: Non-root user defined
FROM php:8.4-fpm-alpine
RUN addgroup -g 1000 -S appgroup \
    && adduser -u 1000 -S appuser -G appgroup
USER appuser
CMD ["php-fpm"]
```

### 2. Correct UID/GID Convention

```dockerfile
# Alpine: addgroup / adduser (BusyBox)
RUN addgroup -g 1000 -S appgroup \
    && adduser -u 1000 -S appuser -G appgroup -h /var/www -s /sbin/nologin

# Debian: groupadd / useradd (shadow)
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -d /var/www -s /usr/sbin/nologin -M appuser
```

### 3. File Ownership After COPY

```dockerfile
# INSECURE: Files owned by root after COPY
COPY . /var/www/

# SECURE: Set ownership during COPY
COPY --chown=appuser:appgroup . /var/www/

# SECURE: Set ownership in multi-stage
COPY --from=builder --chown=appuser:appgroup /app/vendor /var/www/vendor
```

### 4. No chmod 777

```dockerfile
# INSECURE: World-writable permissions
RUN chmod -R 777 /var/www/var

# SECURE: Minimal permissions
RUN mkdir -p /var/www/var/cache /var/www/var/log \
    && chown -R appuser:appgroup /var/www/var \
    && chmod -R 755 /var/www/var
```

### 5. Volume Permissions

```yaml
# PROBLEM: Host UID doesn't match container UID
services:
  php-fpm:
    volumes:
      - ./src:/var/www/src          # May cause permission issues

# SOLUTION: Read-only bind mounts + named volumes
services:
  php-fpm:
    user: "1000:1000"
    volumes:
      - ./src:/var/www/src:ro       # Read-only (no permission issues)
      - cache:/var/www/var/cache    # Named volume
      - logs:/var/www/var/log       # Named volume
```

### 6. Read-Only Filesystem Compatibility

```yaml
services:
  php-fpm:
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=64m
      - /var/run:noexec,nosuid,size=1m
    volumes:
      - cache:/var/www/var/cache
      - logs:/var/www/var/log
```

## User Creation: Alpine vs Debian

```dockerfile
# Alpine (BusyBox): -g GID -S system -u UID -G group -h home -s shell
RUN addgroup -g 1000 -S appgroup \
    && adduser -u 1000 -S appuser -G appgroup -h /var/www -s /sbin/nologin

# Debian (shadow): -g GID/group -u UID -d home -s shell -M no home dir
RUN groupadd -g 1000 appgroup \
    && useradd -u 1000 -g appgroup -d /var/www -s /usr/sbin/nologin -M appuser

# Using existing www-data (UID 82 on Alpine, 33 on Debian)
USER www-data
```

## Grep Patterns

```bash
# USER instruction
Grep: "^USER " --glob "**/Dockerfile*"

# User creation commands
Grep: "adduser|useradd|addgroup|groupadd" --glob "**/Dockerfile*"

# COPY without --chown
Grep: "^COPY(?!.*--chown)" --glob "**/Dockerfile*"

# Overly permissive chmod
Grep: "chmod.*(777|666|a\+[rw])" --glob "**/Dockerfile*"

# chown commands
Grep: "chown" --glob "**/Dockerfile*"

# Read-only filesystem
Grep: "read_only:" --glob "**/docker-compose*.yml"

# tmpfs mounts
Grep: "tmpfs:" --glob "**/docker-compose*.yml"
```

## Severity Classification

| Pattern | Severity | Impact |
|---------|----------|--------|
| No USER instruction (production) | Critical | Container runs as root |
| chmod 777 on application dirs | High | Any process can modify files |
| COPY without --chown (with USER) | High | Files inaccessible to app user |
| System UID (< 1000) for app user | Medium | Potential privilege confusion |
| Volume mount without :ro | Medium | Unnecessary write access |
| No read-only rootfs | Medium | Filesystem can be modified |
| Missing tmpfs for /tmp | Low | Temp files on persistent storage |

## Output Format

```markdown
### Permission Issue: [Check Name]

**Severity:** Critical/High/Medium/Low
**File:** `<file_path>:<line>`
**Check:** USER / Ownership / chmod / Volume / Read-only FS

**Detection:**
[How the issue was identified]

**Risk:**
[Security or operational impact]

**Current:**
```dockerfile
// Current configuration
```

**Remediation:**
```dockerfile
// Secure configuration
```

**Platform Notes:**
- Alpine: [Alpine-specific instructions]
- Debian: [Debian-specific instructions]
```
