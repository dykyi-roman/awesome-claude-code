---
name: acc-create-dockerignore
description: Generates optimized .dockerignore files for PHP projects. Excludes tests, docs, IDE files, and development artifacts to minimize build context.
---

# .dockerignore Generator

Generates optimized `.dockerignore` files for PHP projects, reducing build context size and improving build performance.

## Generated Files

```
.dockerignore             # Optimized exclusion rules
```

## Generation Instructions

1. **Detect project type:** Check for `symfony.lock` (Symfony), `artisan` (Laravel), or generic PHP
2. **Analyze existing files:** Read `.gitignore`, check CI/CD config, identify test/doc directories
3. **Generate .dockerignore:** Universal exclusions + framework-specific + proper `!` negations

## Universal PHP .dockerignore

```
# ===========================================
# .dockerignore — PHP Project
# ===========================================

# Version Control
.git
.gitignore
.gitattributes
.gitmodules

# CI/CD
.github
.gitlab
.gitlab-ci.yml
.circleci
Jenkinsfile
bitbucket-pipelines.yml

# IDE
.idea
.vscode
*.sublime-project
*.sublime-workspace
*.swp
*.swo
*~

# Dependencies (installed in container)
vendor/
node_modules/

# Testing
tests/
test/
spec/
phpunit.xml
phpunit.xml.dist
.phpunit.result.cache
.phpunit.cache/
behat.yml
behat.yml.dist
infection.json
infection.json.dist

# Documentation
docs/
doc/
*.md
!README.md
LICENSE

# Development Files
docker-compose*.yml
docker-compose*.yaml
Dockerfile*
.docker/
Makefile
Vagrantfile

# Cache and Temporary Files
var/cache/
var/log/
storage/logs/
storage/framework/cache/
storage/framework/sessions/
storage/framework/views/
*.log
tmp/
temp/

# Local Configuration
.env
.env.local
.env.*.local
.env.test
*.local.php
docker-compose.override.yml

# Static Analysis
phpstan.neon
phpstan.neon.dist
phpstan-baseline.neon
psalm.xml
psalm.xml.dist
.php-cs-fixer.php
.php-cs-fixer.dist.php
.php-cs-fixer.cache
.phpcs-cache
phpcs.xml
phpcs.xml.dist
deptrac.yaml
rector.php
ecs.php
pint.json

# Build Artifacts
coverage/
build/
report/
reports/
clover.xml
coverage.xml

# OS Files
.DS_Store
Thumbs.db

# Package Management
composer.phar
auth.json

# Claude / AI
.claude/
CLAUDE.md
```

## Symfony-Specific Additions

```
# Symfony
symfony.lock
var/
assets/
public/build/
.symfony/
.symfony.local.yaml
.phpunit/
```

## Laravel-Specific Additions

```
# Laravel
storage/
bootstrap/cache/
docker-compose.sail.yml
public/hot
public/storage
public/build/
public/mix-manifest.json
_ide_helper*.php
.phpstorm.meta.php
Homestead.json
Homestead.yaml
```

## Important Negations

```
# Required Files (do NOT exclude)
!composer.json
!composer.lock
!symfony.lock
!.env.dist
!.env.example
```

## Build Context Impact

| Pattern | Typical savings |
|---|---|
| `.git` | 50-500 MB |
| `vendor/` | 100-500 MB |
| `node_modules/` | 200-800 MB |
| `tests/` | 5-50 MB |

## Validation Rules

1. **Never exclude:** `composer.json`, `composer.lock`, source code (`src/`, `app/`, `config/`, `public/`), migrations
2. **Always exclude:** `.git`, `vendor/`, tests, IDE files, local env files with secrets
3. **Framework awareness:** Symfony: exclude `var/`, keep `config/`, `public/`, `templates/`; Laravel: exclude `storage/`, keep `config/`, `public/`, `resources/`

## Usage

Provide:
- Framework (Symfony/Laravel/generic PHP)
- Monorepo structure (yes/no)
- Custom exclusions (optional)

The generator will:
1. Create `.dockerignore` with universal exclusions
2. Add framework-specific exclusions
3. Add proper negation rules for required files
4. Optimize for minimal build context
