---
name: acc-check-docker-secrets
description: Detects secrets and credentials in Docker configuration. Scans Dockerfile, Compose, and .env files for exposed passwords, tokens, and keys.
---

# Docker Secrets Detection

Scan Docker configuration files for exposed secrets, credentials, and sensitive data.

## File Scanning Targets

| File | Risk Level | Common Secrets |
|------|-----------|----------------|
| `Dockerfile` | High | ARG/ENV with passwords, inline credentials |
| `docker-compose*.yml` | High | Environment variables, volume-mounted secrets |
| `.env`, `.env.*` | Critical | Database passwords, API keys, tokens |
| `entrypoint.sh` | Medium | Hardcoded credentials in scripts |

## Detection Patterns

### 1. Hardcoded Passwords

```dockerfile
# CRITICAL: Password in Dockerfile (persists in image layers)
ENV MYSQL_ROOT_PASSWORD=SuperSecret123
ARG ADMIN_PASSWORD=admin123
```

```yaml
# CRITICAL: Password in docker-compose.yml
services:
  database:
    environment:
      POSTGRES_PASSWORD: my_secret_password
```

### 2. API Keys and Tokens

```dockerfile
# CRITICAL: API keys in build args
ARG GITHUB_TOKEN=ghp_ABCDEFghijklmnop1234567890
ENV STRIPE_SECRET_KEY=sk_live_xxxxxxxxxxxxxxxxxxxx
ENV AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
```

### 3. Private Keys and Certificates

```dockerfile
# CRITICAL: Private key copied into image
COPY id_rsa /root/.ssh/id_rsa
COPY server.key /etc/ssl/private/server.key
ENV PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----\nMIIE..."
```

### 4. Database Connection Strings

```dockerfile
# CRITICAL: Full connection string with credentials
ENV DATABASE_URL="postgresql://admin:secret@db:5432/myapp"
ENV REDIS_URL="redis://:password@redis:6379/0"
```

### 5. Default and Weak Passwords

```yaml
# HIGH: Default/weak passwords in compose
services:
  database:
    environment:
      POSTGRES_PASSWORD: postgres
      MYSQL_ROOT_PASSWORD: root
```

## Grep Patterns

```bash
# Passwords in Docker files
Grep: "(PASSWORD|PASSWD|PASS)\s*[:=]\s*['\"]?[a-zA-Z0-9!@#$%^&*()_+]{4,}" --glob "**/Dockerfile*" --glob "**/docker-compose*.yml" --glob "**/.env*"

# API keys and tokens
Grep: "(API_KEY|API_SECRET|ACCESS_KEY|SECRET_KEY|AUTH_TOKEN)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{10,}" --glob "**/Dockerfile*" --glob "**/.env*"

# GitHub token pattern
Grep: "ghp_[a-zA-Z0-9]{36}" --glob "**/Dockerfile*" --glob "**/.env*"

# AWS key pattern
Grep: "AKIA[0-9A-Z]{16}" --glob "**/Dockerfile*" --glob "**/.env*"

# Private keys
Grep: "PRIVATE.KEY|BEGIN RSA|BEGIN EC|BEGIN OPENSSH" --glob "**/Dockerfile*"
Grep: "COPY.*(\.pem|\.key|id_rsa|id_ed25519)" --glob "**/Dockerfile*"

# Connection strings with credentials
Grep: "(mysql|postgres|postgresql|mongodb|redis)://[^:]+:[^@]+@" --glob "**/Dockerfile*" --glob "**/.env*"

# Default passwords
Grep: "(PASSWORD|PASSWD)\s*[:=]\s*['\"]?(password|root|admin|secret|123456)['\"]?" -i --glob "**/docker-compose*.yml" --glob "**/.env*"

# Credentials in entrypoint scripts
Grep: "(-p['\"][^'\"]+['\"]|--password[= ]['\"]?[a-zA-Z0-9])" --glob "**/entrypoint*.sh"
```

## False Positive Handling

| Pattern | Why It's False Positive | How to Handle |
|---------|----------------------|---------------|
| `PASSWORD=${DB_PASSWORD}` | Variable reference, not value | Skip if value is `${}` or `$()` |
| `password: ""` | Empty placeholder | Skip empty values |
| `# ENV PASSWORD=xxx` | Commented out | Skip lines starting with `#` |
| `PASSWORD_FILE=/run/secrets/db` | Docker secret file reference | Skip `*_FILE` suffixes |
| `.env.example` | Template file | Skip `.example` suffix |

## Remediation Patterns

### Docker Compose Secrets

```yaml
services:
  php-fpm:
    secrets: [db_password, api_key]
    environment:
      DB_PASSWORD_FILE: /run/secrets/db_password
secrets:
  db_password:
    file: ./secrets/db_password.txt
  api_key:
    external: true
```

### BuildKit Build Secrets

```dockerfile
RUN --mount=type=secret,id=composer_auth,target=/root/.composer/auth.json \
    composer install --no-dev
# Usage: docker build --secret id=composer_auth,src=auth.json .
```

## Severity Classification

| Pattern | Severity | Risk |
|---------|----------|------|
| Hardcoded password in Dockerfile | Critical | Persists in all image layers |
| Private key copied to image | Critical | Full authentication compromise |
| API key in environment variable | Critical | Service access compromise |
| Connection string with credentials | Critical | Database access compromise |
| Default/weak password | High | Easily guessable credentials |
| Password in docker-compose.yml | High | Exposed in version control |
| Credential in entrypoint script | Medium | Visible in container filesystem |

## Output Format

```markdown
### Secret Detected: [Type]

**Severity:** Critical/High/Medium
**File:** `<file_path>:<line>`
**Type:** Password / API Key / Token / Private Key / Connection String

**Detection:**
```
// Matched pattern (redacted)
```

**Risk:**
[What could be compromised with this secret]

**Remediation:**
```yaml
// Secure alternative using Docker secrets or env_file
```

**Verification Checklist:**
- [ ] Secret removed from file
- [ ] File added to .gitignore if needed
- [ ] Git history cleaned if secret was committed
- [ ] Secret rotated (old value is compromised)
```
