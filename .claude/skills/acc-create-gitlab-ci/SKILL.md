---
name: acc-create-gitlab-ci
description: Generates GitLab CI configurations for PHP projects. Creates pipelines with stages, caching, artifacts, parallel jobs, and deployment environments.
---

# GitLab CI Configuration Generator

Generates optimized GitLab CI pipelines for PHP projects.

## Generated Files

```
.gitlab-ci.yml           # Main pipeline configuration
.gitlab/
├── ci/
│   ├── templates.yml    # Reusable templates
│   ├── lint.yml         # Linting jobs
│   ├── test.yml         # Testing jobs
│   └── deploy.yml       # Deployment jobs
```

## References

- `references/templates.md` — Complete YAML templates: main pipeline, base templates, lint, test, deploy, security scanning, scheduled pipelines

## Generation Instructions

1. **Analyze project:**
   - Check `composer.json` for tools
   - Check existing `.gitlab-ci.yml`
   - Identify required services
   - Check for Dockerfile

2. **Generate configuration:**
   - Main `.gitlab-ci.yml` with includes
   - Modular files in `.gitlab/ci/`
   - Templates for reuse

3. **Customize based on:**
   - PHP version from `composer.json`
   - Required services
   - Deployment targets
   - Branch strategy

## Usage

Provide:
- Project path or composer.json
- Deployment targets (staging, production)
- Required services (MySQL, Redis, etc.)

The generator will:
1. Analyze project structure
2. Generate optimized pipeline
3. Include proper caching
4. Set up parallel jobs
5. Configure deployments
