---
name: acc-check-docker-security
description: Checks Docker security for PHP projects. Detects root user, exposed secrets, privileged mode, and missing security configurations.
---

# Docker Security Check

Analyze Docker configurations for PHP projects to detect security vulnerabilities and missing hardening.

## Security Check Patterns

| Check | Risk | Detection |
|-------|------|-----------|
| Running as root | Container escape | No USER instruction |
| Secrets in Dockerfile | Credential leak | ENV/ARG with passwords |
| Privileged mode | Full host access | `privileged: true` |
| No capability dropping | Excessive permissions | Missing `cap_drop` |
| Exposed unnecessary ports | Attack surface | Extra port mappings |
| No read-only rootfs | Filesystem tampering | Missing `read_only` |
| Latest tag | Unpredictable builds | `FROM image:latest` |

## Detection Patterns

### 1. Running as Root

```dockerfile
# INSECURE: No USER instruction, runs as root
FROM php:8.4-fpm-alpine
COPY . /var/www/
CMD ["php-fpm"]

# SECURE: Explicit non-root user
FROM php:8.4-fpm-alpine
RUN addgroup -g 1000 -S appgroup \
    && adduser -u 1000 -S appuser -G appgroup
COPY --chown=appuser:appgroup . /var/www/
USER appuser
CMD ["php-fpm"]
```

### 2. Secrets in Dockerfile

```dockerfile
# INSECURE: Hardcoded credentials
ENV DB_PASSWORD=secret123
ARG GITHUB_TOKEN=ghp_xxxxxxxxxxxx

# SECURE: Use build secrets (BuildKit)
RUN --mount=type=secret,id=composer_auth \
    COMPOSER_AUTH=$(cat /run/secrets/composer_auth) \
    composer install --no-dev
```

### 3. Privileged Mode and Capabilities

```yaml
# INSECURE: Full host access
services:
  php-fpm:
    privileged: true

# SECURE: Minimal capabilities
services:
  php-fpm:
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
```

### 4. Exposed Unnecessary Ports

```yaml
# INSECURE: Database port exposed to host
services:
  database:
    ports:
      - "5432:5432"

# SECURE: Only expose through internal network
services:
  database:
    expose:
      - "5432"
    networks:
      - internal
networks:
  internal:
    internal: true
```

### 5. Latest Tag and Read-Only FS

```dockerfile
# INSECURE: Unpredictable, not reproducible
FROM php:latest

# SECURE: Pinned version
FROM php:8.4.3-fpm-alpine3.21
```

```yaml
# SECURE: Read-only with explicit writable dirs
services:
  php-fpm:
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=64m
      - /var/run:noexec,nosuid,size=1m
    volumes:
      - cache:/var/www/var/cache
```

## Grep Patterns

```bash
# Root user detection
Grep: "^USER " --glob "**/Dockerfile*"

# Secrets in build files
Grep: "(PASSWORD|SECRET|TOKEN|API_KEY|PRIVATE_KEY)\s*=" --glob "**/Dockerfile*"

# Privileged containers
Grep: "privileged:\s*true" --glob "**/docker-compose*.yml"

# Missing security options
Grep: "security_opt:|cap_drop:|no-new-privileges" --glob "**/docker-compose*.yml"

# Latest tags
Grep: ":latest" --glob "**/Dockerfile*" --glob "**/docker-compose*.yml"

# Read-only rootfs
Grep: "read_only:\s*true" --glob "**/docker-compose*.yml"

# Port exposure
Grep: "ports:" --glob "**/docker-compose*.yml"

# ADD instead of COPY
Grep: "^ADD " --glob "**/Dockerfile*"
```

## Severity Classification

| Pattern | Severity | OWASP Category |
|---------|----------|----------------|
| Hardcoded secrets in Dockerfile | Critical | A07 - Security Misconfiguration |
| Privileged mode enabled | Critical | A01 - Broken Access Control |
| Running as root (production) | High | A01 - Broken Access Control |
| No capability dropping | High | A05 - Security Misconfiguration |
| Database ports exposed to host | High | A01 - Broken Access Control |
| Using :latest tag | Medium | A08 - Software Integrity |
| No read-only rootfs | Medium | A05 - Security Misconfiguration |
| Missing --no-new-privileges | Medium | A01 - Broken Access Control |
| ADD instead of COPY | Low | A08 - Software Integrity |

## Output Format

```markdown
### Security Issue: [Check Name]

**Severity:** Critical/High/Medium/Low
**File:** `<file_path>:<line>`
**OWASP:** A0X - Category

**Detection:**
[How the issue was found]

**Risk:**
[What an attacker could exploit]

**Current:**
```dockerfile
// Insecure configuration
```

**Remediation:**
```dockerfile
// Secure configuration
```

**Verification:**
[Command to verify the fix is applied]
```
