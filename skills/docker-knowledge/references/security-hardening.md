# Docker Security Hardening for PHP

Security best practices for building and running PHP Docker containers.

## Non-Root User Setup

### Alpine (addgroup/adduser)

```dockerfile
# Create application user and group
RUN addgroup -g 1000 app \
    && adduser -u 1000 -G app -D -h /var/www/html app

# Set ownership
COPY --chown=app:app . /var/www/html

# Switch to non-root user
USER app
```

### Debian (groupadd/useradd)

```dockerfile
RUN groupadd -g 1000 app \
    && useradd -u 1000 -g app -m -d /var/www/html app

COPY --chown=app:app . /var/www/html

USER app
```

### PHP-FPM User Configuration

```ini
; php-fpm.d/www.conf
[www]
user = app
group = app
listen.owner = app
listen.group = app
listen.mode = 0660
```

### Writable Directories

```dockerfile
# Create writable dirs before switching user
RUN mkdir -p /var/www/html/var/cache \
             /var/www/html/var/log \
             /var/www/html/var/sessions \
    && chown -R app:app /var/www/html/var

USER app
```

## Read-Only Filesystem

### Docker Compose Configuration

```yaml
services:
  php-fpm:
    image: myapp:prod
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=64M
      - /var/www/html/var/cache:noexec,nosuid,size=128M
      - /var/www/html/var/log:noexec,nosuid,size=64M
    volumes:
      - sessions:/var/www/html/var/sessions
```

### Required Writable Paths for PHP

| Path | Purpose | Strategy |
|------|---------|----------|
| `/tmp` | PHP temp files, uploads | tmpfs |
| `var/cache` | Framework cache | tmpfs (warm on boot) |
| `var/log` | Application logs | tmpfs or volume |
| `var/sessions` | Session files | tmpfs or Redis |
| `/var/run/php` | FPM socket/pid | tmpfs |

## Secrets Management

### Build-Time Secrets (BuildKit)

```dockerfile
# syntax=docker/dockerfile:1

# Mount secret during build only — never stored in image layers
RUN --mount=type=secret,id=composer_auth,target=/root/.composer/auth.json \
    composer install --no-dev --prefer-dist
```

```bash
# Pass secret at build time
docker build --secret id=composer_auth,src=auth.json .
```

### Runtime Secrets (Docker Swarm)

```yaml
services:
  php-fpm:
    image: myapp:prod
    secrets:
      - db_password
      - app_key

secrets:
  db_password:
    external: true
  app_key:
    file: ./secrets/app_key.txt
```

```php
// Read secret in PHP
$dbPassword = trim(file_get_contents('/run/secrets/db_password'));
```

### Environment Variables (Less Secure)

```yaml
# Acceptable for non-sensitive config
services:
  php-fpm:
    environment:
      APP_ENV: production
      LOG_LEVEL: info
    env_file:
      - .env.production  # Never commit this file
```

### What NOT to Do

```dockerfile
# NEVER: Secrets in ENV instruction (visible in image history)
ENV DB_PASSWORD=secret123

# NEVER: Secrets in ARG (visible in build history)
ARG PRIVATE_TOKEN=abc123

# NEVER: Copy secret files into image
COPY .env /var/www/html/.env

# NEVER: Inline secrets in RUN
RUN curl -H "Authorization: Bearer s3cr3t" https://api.example.com
```

## Capability Dropping

### Docker Compose

```yaml
services:
  php-fpm:
    image: myapp:prod
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETUID
      - SETGID
    security_opt:
      - no-new-privileges:true
```

### Docker Run

```bash
docker run \
    --cap-drop=ALL \
    --cap-add=CHOWN \
    --cap-add=SETUID \
    --cap-add=SETGID \
    --security-opt=no-new-privileges:true \
    --read-only \
    myapp:prod
```

### Capabilities Reference for PHP-FPM

| Capability | Needed | Reason |
|-----------|--------|--------|
| CHOWN | Maybe | File ownership changes |
| SETUID | Yes | FPM master switches to worker user |
| SETGID | Yes | FPM master switches to worker group |
| NET_BIND_SERVICE | No | FPM uses port 9000 (>1024) |
| SYS_PTRACE | No | Only for debugging |
| ALL others | No | Drop everything else |

## Network Security

### Network Segmentation

```yaml
services:
  nginx:
    networks:
      - frontend
      - backend

  php-fpm:
    networks:
      - backend
      - database

  mysql:
    networks:
      - database  # Not accessible from frontend

  redis:
    networks:
      - database

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
  database:
    driver: bridge
    internal: true  # No external access
```

### Network Isolation Rules

```
Internet → Nginx (frontend)
              ↓
           PHP-FPM (backend, internal)
              ↓
           MySQL/Redis (database, internal)

Only Nginx is reachable from outside.
PHP-FPM, MySQL, Redis have no internet access.
```

## Image Scanning

### Trivy (Recommended)

```bash
# Scan image for vulnerabilities
trivy image myapp:prod

# Fail CI on HIGH/CRITICAL
trivy image --exit-code 1 --severity HIGH,CRITICAL myapp:prod

# Generate SBOM
trivy image --format spdx-json --output sbom.json myapp:prod
```

### Grype

```bash
# Scan image
grype myapp:prod

# Fail on high severity
grype myapp:prod --fail-on high
```

### GitHub Actions Integration

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:prod
    format: sarif
    output: trivy-results.sarif
    severity: CRITICAL,HIGH

- name: Upload scan results
  uses: github/codeql-action/upload-sarif@v3
  with:
    sarif_file: trivy-results.sarif
```

## Supply Chain Security

### Image Signing with Cosign

```bash
# Sign image
cosign sign --key cosign.key myregistry/myapp:prod

# Verify image
cosign verify --key cosign.pub myregistry/myapp:prod
```

### SBOM Generation

```bash
# Generate SBOM with Syft
syft myapp:prod -o spdx-json > sbom.json

# Attach SBOM to image with Cosign
cosign attach sbom --sbom sbom.json myregistry/myapp:prod
```

### Dockerfile Best Practices

```dockerfile
# Pin base image by digest for reproducibility
FROM php:8.4-fpm-alpine@sha256:abc123... AS production

# Verify downloaded files
RUN curl -o file.tar.gz https://example.com/file.tar.gz \
    && echo "expected_sha256  file.tar.gz" | sha256sum -c -
```

## Common CVE Patterns in PHP Images

| Pattern | Risk | Mitigation |
|---------|------|------------|
| Outdated base image | Known CVEs in OS packages | Regular rebuilds with latest base |
| Unused system packages | Wider attack surface | Minimal installs, remove build deps |
| Old PHP version | PHP security bugs | Pin to latest patch, rebuild weekly |
| Bundled curl/openssl | TLS vulnerabilities | Update Alpine/Debian packages |
| Writable document root | Web shell upload | Read-only filesystem, separate upload dir |
| PHP-FPM exposed to network | Direct FastCGI access | Internal network, Nginx in front |
| Debug extensions in prod | Information disclosure | No xdebug/phpinfo in production |
| Default PHP error display | Information disclosure | `display_errors=Off` in production |

## Detection Patterns

```bash
# Check for root user (missing USER instruction)
Grep: "^USER " --glob "Dockerfile*"  # Should exist

# Check for secrets in Dockerfile
Grep: "ENV.*PASSWORD|ENV.*SECRET|ENV.*KEY|ENV.*TOKEN" --glob "Dockerfile*"

# Check for privileged mode
Grep: "privileged.*true" --glob "docker-compose*.yml"

# Check for capability dropping
Grep: "cap_drop|no-new-privileges" --glob "docker-compose*.yml"

# Check for read-only filesystem
Grep: "read_only.*true" --glob "docker-compose*.yml"

# Check for network segmentation
Grep: "internal.*true" --glob "docker-compose*.yml"
```
