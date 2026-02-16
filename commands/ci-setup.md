---
description: Setup CI pipeline from scratch. Creates GitHub Actions or GitLab CI configuration with lint, test, build, and deploy stages.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash, Task
model: opus
argument-hint: <platform> [path] [-- additional instructions]
---

# Setup CI Pipeline

Create a complete CI/CD pipeline for a PHP project from scratch.

## Input Parsing

Parse `$ARGUMENTS` to extract platform, path, and optional meta-instructions:

```
Format: <platform> [path] [-- <meta-instructions>]

Examples:
- /acc-ci-setup github
- /acc-ci-setup gitlab ./
- /acc-ci-setup github ./src -- include Docker, blue-green deploy
- /acc-ci-setup gitlab -- skip deploy, focus on testing
```

**Parsing rules:**
1. First argument = **platform** (`github` or `gitlab`)
2. Second argument = **path** (optional, defaults to `./`)
3. After `--` = **meta-instructions** (optional customization)

## Pre-flight Check

1. **Verify platform specified:**
   - If empty, ask user: "Which CI platform? (github/gitlab)"

2. **Check existing CI:**
   ```bash
   ls -la .github/workflows/ 2>/dev/null
   ls -la .gitlab-ci.yml 2>/dev/null
   ```
   - Warn if CI already exists
   - Ask to overwrite or extend

3. **Analyze project:**
   ```bash
   cat composer.json | jq '.require.php, ."require-dev"'
   ls phpstan.neon* psalm.xml* .php-cs-fixer* 2>/dev/null
   ls phpunit.xml* 2>/dev/null
   ls Dockerfile* 2>/dev/null
   ```

## Instructions

Use the `acc-ci-coordinator` agent to set up the CI pipeline:

```
Task tool with subagent_type="acc-ci-coordinator"
prompt: "Set up CI pipeline for [PATH].

Platform: [PLATFORM]
[META-INSTRUCTIONS if provided]

Operation: SETUP

Required components:
1. Pipeline workflow (lint, test, build)
2. Static analysis configs (PHPStan, Psalm, CS-Fixer)
3. Test configuration (PHPUnit)
4. Docker configuration (if needed)
5. Deployment configuration (if requested)

Analyze the project and generate all necessary files."
```

## Expected Output

The coordinator will:

1. **Analyze the project:**
   - PHP version
   - Dependencies and dev tools
   - Test framework
   - Existing configurations

2. **Generate CI workflow:**
   - `.github/workflows/ci.yml` or `.gitlab-ci.yml`
   - Stages: install, lint, test, build, deploy

3. **Generate tool configs (if missing):**
   - `phpstan.neon`
   - `psalm.xml`
   - `.php-cs-fixer.dist.php`
   - `deptrac.yaml`

4. **Generate Docker files (if requested):**
   - `Dockerfile`
   - `Dockerfile.ci`
   - `.dockerignore`

5. **Provide setup instructions:**
   - Required secrets
   - First run guidance
   - Customization options

## Usage Examples

```bash
# Basic GitHub Actions setup
/acc-ci-setup github

# GitLab CI with specific path
/acc-ci-setup gitlab ./my-project

# Full setup with Docker and deployment
/acc-ci-setup github -- include Docker, canary deployment

# Testing-focused setup
/acc-ci-setup gitlab -- focus on testing, high coverage requirements

# Minimal setup
/acc-ci-setup github -- only lint and unit tests, no deploy
```

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `include Docker` | Generate Dockerfile and CI Docker build |
| `blue-green deploy` | Add blue-green deployment workflow |
| `canary deployment` | Add canary release workflow |
| `skip deploy` | Only generate lint/test stages |
| `focus on testing` | Prioritize test configuration |
| `high coverage` | Set strict coverage requirements (90%+) |
| `minimal` | Basic lint and test only |
