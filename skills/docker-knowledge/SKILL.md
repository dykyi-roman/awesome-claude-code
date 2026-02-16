---
name: acc-docker-knowledge
description: Docker knowledge base for PHP projects. Provides patterns, best practices, and guidelines for Dockerfile, Compose, security, and production readiness.
---

# Docker Knowledge Base

Quick reference for Docker patterns and PHP-specific guidelines.

## Core Concepts

```
┌─────────────────────────────────────────────────────────────────┐
│                    DOCKER FOR PHP                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Dockerfile         → Build image instructions                  │
│   docker-compose.yml → Multi-container orchestration             │
│   .dockerignore      → Build context exclusions                  │
│   entrypoint.sh      → Container startup logic                   │
│   nginx.conf         → Reverse proxy for PHP-FPM                 │
│   php.ini            → PHP runtime configuration                 │
│   supervisord.conf   → Process management                        │
│                                                                  │
│   Multi-Stage Build:                                             │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│   │ composer  │  │ php-ext  │  │production│                     │
│   │  deps     │──│ builder  │──│  final   │                     │
│   └──────────┘  └──────────┘  └──────────┘                     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## PHP Docker Image Types

| Image | Use Case | Size |
|-------|----------|------|
| `php:8.4-fpm-alpine` | Production (FPM) | ~50MB |
| `php:8.4-cli-alpine` | CI/workers | ~45MB |
| `php:8.4-fpm` | Production (Debian) | ~150MB |
| `php:8.4-cli` | CI/workers (Debian) | ~140MB |
| `php:8.4-apache` | Simple deployments | ~160MB |

## Quick Checklists

### Dockerfile Checklist

- [ ] Multi-stage build (deps → build → production)
- [ ] Alpine base image when possible
- [ ] Pinned version tags (not `latest`)
- [ ] BuildKit syntax header
- [ ] Non-root user
- [ ] Health check defined
- [ ] `.dockerignore` present
- [ ] Composer deps installed before source copy
- [ ] Production PHP config (`php.ini-production`)
- [ ] OPcache enabled and configured
- [ ] No secrets in build args or layers

### Docker Compose Checklist

- [ ] Health checks for all services
- [ ] Named volumes for persistent data
- [ ] Environment variables via `.env` file
- [ ] Dependency ordering with `depends_on` + `condition`
- [ ] Resource limits defined
- [ ] Networks segmented (frontend/backend)
- [ ] No hardcoded passwords

### Security Checklist

- [ ] Non-root user (`USER app`)
- [ ] Read-only root filesystem where possible
- [ ] No secrets in Dockerfile or image
- [ ] Minimal base image
- [ ] No unnecessary packages
- [ ] Capabilities dropped
- [ ] No privileged mode

## Common Violations Quick Reference

| Violation | Where | Severity |
|-----------|-------|----------|
| `FROM php:latest` | Dockerfile | High |
| `COPY . .` before deps install | Dockerfile | High |
| Running as root | Dockerfile | High |
| Secrets in ENV/ARG | Dockerfile | Critical |
| No health check | Dockerfile/Compose | Medium |
| No `.dockerignore` | Project root | Medium |
| `privileged: true` | docker-compose.yml | Critical |
| Hardcoded passwords | docker-compose.yml | Critical |
| No resource limits | docker-compose.yml | Medium |
| Missing `depends_on` conditions | docker-compose.yml | Medium |

## PHP-Specific Best Practices

### Extensions Installation

```dockerfile
# Alpine: use apk + docker-php-ext-install
RUN apk add --no-cache libzip-dev icu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache

# Debian: use apt-get + docker-php-ext-install
RUN apt-get update && apt-get install -y \
    libzip-dev libicu-dev \
    && docker-php-ext-install zip intl pdo_mysql opcache \
    && rm -rf /var/lib/apt/lists/*
```

### OPcache Configuration (Production)

```ini
opcache.enable=1
opcache.enable_cli=1
opcache.memory_consumption=256
opcache.interned_strings_buffer=16
opcache.max_accelerated_files=20000
opcache.validate_timestamps=0
opcache.jit=1255
opcache.jit_buffer_size=256M
```

### PHP-FPM Tuning

```ini
pm = dynamic
pm.max_children = 50
pm.start_servers = 5
pm.min_spare_servers = 5
pm.max_spare_servers = 35
pm.max_requests = 1000
```

## References

For detailed information, load these reference files:

- `references/image-selection.md` — Base image comparison and selection guide
- `references/multistage-patterns.md` — Multi-stage build patterns for PHP
- `references/security-hardening.md` — Security best practices and hardening
- `references/compose-patterns.md` — Docker Compose patterns for PHP stacks
- `references/production-checklist.md` — Production readiness checklist
