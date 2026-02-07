---
name: acc-docker-security-knowledge
description: Docker security knowledge base for PHP. Provides hardening patterns, vulnerability scanning, secrets management, and OWASP container guidelines.
---

# Docker Security Knowledge Base

Quick reference for Docker security hardening patterns in PHP applications.

## Security Layers

```
+---------------------------------------------------------------------------+
|                     DOCKER SECURITY LAYERS                                 |
+---------------------------------------------------------------------------+
|                                                                            |
|   Layer 1: Build Security                                                  |
|   +--------------------------------------------------------------------+  |
|   | Minimal base image | Pinned versions | No secrets in layers        |  |
|   | Multi-stage builds | .dockerignore   | Verified base images        |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Layer 2: Image Security                                                  |
|   +--------------------------------------------------------------------+  |
|   | Vulnerability scanning | SBOM generation | Signed images            |  |
|   | No unnecessary packages | Read-only layers | Minimal attack surface |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Layer 3: Runtime Security                                                |
|   +--------------------------------------------------------------------+  |
|   | Non-root user      | Read-only filesystem | Dropped capabilities   |  |
|   | Resource limits     | No privileged mode   | Seccomp profiles       |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Layer 4: Network Security                                                |
|   +--------------------------------------------------------------------+  |
|   | Network segmentation | Encrypted traffic | Internal DNS only        |  |
|   | No host networking   | Firewall rules    | Service mesh (optional)  |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
|   Layer 5: Secrets Management                                              |
|   +--------------------------------------------------------------------+  |
|   | Docker secrets     | Build secrets      | External vault            |  |
|   | No ENV for secrets | Encrypted at rest  | Rotation policies         |  |
|   +--------------------------------------------------------------------+  |
|                                                                            |
+---------------------------------------------------------------------------+
```

## Non-Root User Patterns

### Alpine-based Image

```dockerfile
# syntax=docker/dockerfile:1
FROM php:8.4-fpm-alpine

# Create non-root user and group
RUN addgroup -g 1000 -S app && \
    adduser -u 1000 -S app -G app -h /home/app -s /bin/sh

# Set working directory with correct ownership
WORKDIR /var/www/html
RUN chown -R app:app /var/www/html

# Switch to non-root user
USER app
```

### Debian-based Image

```dockerfile
FROM php:8.4-fpm

RUN groupadd -g 1000 app && \
    useradd -u 1000 -g app -m -s /bin/bash app

WORKDIR /var/www/html
RUN chown -R app:app /var/www/html

USER app
```

## Secrets Management

### Build Secrets (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1
FROM composer:2 AS deps

# Use build secret for private repository access
RUN --mount=type=secret,id=composer_auth,target=/root/.composer/auth.json \
    composer install --no-dev --no-scripts --prefer-dist

FROM php:8.4-fpm-alpine AS production
COPY --from=deps /app/vendor /var/www/html/vendor
# Secret is NOT present in final image
```

```bash
# Build with secret
DOCKER_BUILDKIT=1 docker build \
    --secret id=composer_auth,src=auth.json \
    -t myapp:latest .
```

### Runtime Secrets (Docker Compose)

```yaml
services:
  php:
    image: myapp:latest
    secrets:
      - db_password
      - app_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  app_key:
    file: ./secrets/app_key.txt
```

```php
<?php
// Read secret at runtime
function getSecret(string $name): string
{
    $path = '/run/secrets/' . $name;
    if (!file_exists($path)) {
        throw new \RuntimeException("Secret not found: {$name}");
    }
    return trim(file_get_contents($path));
}
```

### Docker Swarm Secrets

```bash
# Create encrypted secret
echo "s3cur3p@ss" | docker secret create db_password -

# Use in service
docker service create \
    --secret db_password \
    --name php-app myapp:latest
```

## Image Scanning Tools

| Tool | Integration | License | Features |
|------|-------------|---------|----------|
| **Trivy** | CLI, CI, Kubernetes | Apache 2.0 | OS + app deps, IaC, SBOM |
| **Grype** | CLI, CI | Apache 2.0 | OS + app deps, fast |
| **Snyk** | CLI, CI, IDE | Commercial | Deep analysis, fix advice |
| **Docker Scout** | Docker Desktop, CLI | Commercial | Policy, SBOM, real-time |

### Quick Scan Commands

```bash
# Trivy - comprehensive scan
trivy image --severity HIGH,CRITICAL myapp:latest

# Grype - fast vulnerability scan
grype myapp:latest --fail-on high

# Docker Scout - built-in scanning
docker scout cves myapp:latest
docker scout recommendations myapp:latest
```

## Capability Management

```yaml
# docker-compose.yml
services:
  php:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE    # Bind to ports < 1024 (if needed)
      - CHOWN               # Change file ownership (if needed)
    security_opt:
      - no-new-privileges:true
```

### Minimal Capabilities for PHP-FPM

| Capability | Required | Reason |
|------------|----------|--------|
| `CHOWN` | Sometimes | File ownership changes |
| `SETUID` | No | Drop if non-root |
| `SETGID` | No | Drop if non-root |
| `NET_BIND_SERVICE` | Rarely | Only for ports < 1024 |
| `SYS_PTRACE` | No | Debugging only |
| `ALL` | Drop | Always drop all first |

## Read-Only Filesystem

```yaml
services:
  php:
    read_only: true
    tmpfs:
      - /tmp:size=64M
      - /var/run:size=1M
      - /var/log:size=32M
    volumes:
      - php-sessions:/var/lib/php/sessions
```

## Network Policies

```yaml
services:
  nginx:
    networks:
      - frontend
      - backend

  php:
    networks:
      - backend          # No direct external access

  postgres:
    networks:
      - backend          # Database isolated

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true       # No external access
```

## OWASP Docker Top 10

| # | Risk | Mitigation |
|---|------|------------|
| D01 | Secure user mapping | Run as non-root, USER directive |
| D02 | Patch management | Regular base image updates, scanning |
| D03 | Network segmentation | Internal networks, no host mode |
| D04 | Secure defaults | Drop capabilities, read-only FS |
| D05 | Content trust | Signed images, verified publishers |
| D06 | Vulnerability management | Automated scanning in CI/CD |
| D07 | Resource protection | CPU/memory limits, ulimits |
| D08 | Log management | Centralized logging, no sensitive data |
| D09 | Secret management | Docker secrets, external vaults |
| D10 | Integrity and authenticity | Image signing, content trust |

## Detection Patterns

```bash
# Find Dockerfiles with security issues
Grep: "FROM.*:latest" --glob "**/Dockerfile*"
Grep: "USER root" --glob "**/Dockerfile*"
Grep: "privileged.*true" --glob "**/docker-compose*.yml"
Grep: "ENV.*PASSWORD|ENV.*SECRET|ENV.*KEY" --glob "**/Dockerfile*"
Grep: "cap_add.*ALL|cap_add.*SYS_ADMIN" --glob "**/docker-compose*.yml"

# Check for proper security measures
Grep: "USER app|USER www-data|USER nobody" --glob "**/Dockerfile*"
Grep: "cap_drop.*ALL" --glob "**/docker-compose*.yml"
Grep: "read_only.*true" --glob "**/docker-compose*.yml"
Grep: "no-new-privileges" --glob "**/docker-compose*.yml"
```

## References

For detailed information, load these reference files:

- `references/security-checklist.md` -- Comprehensive security checklist with 50+ items
