---
name: acc-create-github-actions
description: Generates GitHub Actions workflows for PHP projects. Creates CI/CD pipelines with PHPStan, PHPUnit, code coverage, Docker builds, and deployment stages.
---

# GitHub Actions Workflow Generator

Generates optimized GitHub Actions workflows for PHP projects.

## When to Use

- Setting up CI/CD for a new PHP project
- Adding static analysis, testing, or deployment pipelines
- Migrating from other CI systems to GitHub Actions
- Optimizing existing workflow performance

## Generated Files

```
.github/
└── workflows/
    ├── ci.yml           # Main CI pipeline
    ├── security.yml     # Security scanning
    └── deploy.yml       # Deployment workflow
```

## Workflow Components

### CI Pipeline (`ci.yml`)

4-stage pipeline with dependency caching and parallel execution:

| Stage | Jobs | Purpose |
|-------|------|---------|
| 1. Install | `install` | Composer install, upload vendor artifact |
| 2. Analysis | `phpstan`, `psalm`, `cs-fixer`, `deptrac` | Static analysis (parallel) |
| 3. Tests | `test-unit`, `test-integration` | PHPUnit with coverage upload |
| 4. Build | `build` | Docker image build and push (main/tags only) |

Key features:
- Concurrency control (cancel in-progress runs)
- Composer cache with `actions/cache@v4`
- Vendor sharing via `actions/upload-artifact@v4`
- Service containers for MySQL and Redis
- Coverage upload to Codecov
- Docker Buildx with GHCR push

### Security Workflow (`security.yml`)

Triggers: push to main, PRs, weekly schedule (Monday).

| Job | Tool | Purpose |
|-----|------|---------|
| `dependency-audit` | `composer audit` | Known vulnerability check |
| `psalm-security` | Psalm taint analysis | Data flow security |
| `trivy` | Trivy + SARIF | Container image scanning |

### Deploy Workflow (`deploy.yml`)

Triggers: version tags (`v*`), manual `workflow_dispatch`.

| Job | Condition | Environment |
|-----|-----------|-------------|
| `deploy-staging` | Push or manual staging | `staging` |
| `deploy-production` | Tags or manual production | `production` |

Features: environment protection rules, health checks, sequential staging-then-production.

### Matrix Testing

Cross-version testing pattern for libraries:

| Dimension | Values |
|-----------|--------|
| PHP versions | 8.2, 8.3, 8.4 |
| Dependencies | lowest, highest |
| Coverage | Only on PHP 8.4 + highest |

Uses `fail-fast: false` to run all combinations.

## Generation Process

1. **Analyze project:**
   - Check `composer.json` for tools (phpstan, psalm, php-cs-fixer, deptrac)
   - Check existing `.github/workflows/` directory
   - Identify testing framework (PHPUnit, Pest)
   - Check for Docker/docker-compose

2. **Generate appropriate workflows:**
   - Basic CI if minimal tools detected
   - Full CI if all tools present
   - Security workflow if sensitive project
   - Deploy workflow if infrastructure detected

3. **Customize based on:**
   - PHP version from `composer.json` `require.php`
   - Required services (MySQL, Redis, RabbitMQ)
   - Coverage requirements and reporting
   - Deployment targets and environments

## File Placement

All workflows go in `.github/workflows/`:

| File | When Generated |
|------|---------------|
| `ci.yml` | Always |
| `security.yml` | When security tools detected or requested |
| `deploy.yml` | When deployment infrastructure detected |

## Naming Conventions

- Workflow files: lowercase, hyphenated (e.g., `ci.yml`, `security.yml`)
- Job names: lowercase, hyphenated (e.g., `test-unit`, `deploy-staging`)
- Step names: sentence case (e.g., `Run PHPStan`, `Upload coverage`)
- Environment variables: UPPER_SNAKE_CASE (e.g., `PHP_VERSION`, `COMPOSER_ARGS`)

## Quick Template Reference

| Template | Lines | Key Actions Used |
|----------|-------|-----------------|
| CI Pipeline | ~270 | `checkout@v4`, `setup-php@v2`, `cache@v4`, `upload-artifact@v4`, `codecov-action@v4`, `build-push-action@v5` |
| Security | ~70 | `checkout@v4`, `setup-php@v2`, `trivy-action`, `upload-sarif` |
| Deploy | ~70 | `checkout@v4`, environments, health checks |
| Matrix | ~30 | `setup-php@v2`, strategy matrix |

## Usage

Provide:
- Project path or `composer.json`
- Required environments (staging, production)
- Custom requirements (specific services, notification channels)

The generator will:
1. Analyze the project structure
2. Generate optimized workflows
3. Include caching and parallelization
4. Add appropriate triggers and conditions

## References

- `references/templates.md` — Full YAML workflow templates (CI, Security, Deploy, Matrix)
- `references/examples.md` — Concrete usage examples (minimal CI, multi-service, caching, artifacts, deployment)
