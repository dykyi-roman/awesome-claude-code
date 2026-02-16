---
description: Audit Docker configuration. Analyzes Dockerfile, Compose, security, performance, and production readiness for PHP projects.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: [path] [level] [-- meta-instructions]
---

# Docker Audit

Perform a comprehensive audit of Docker configuration, including architecture, security, performance, and production readiness.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: [path] [level] [-- <meta-instructions>]

Arguments:
- path: Target directory (optional, default: ./)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-docker
- /acc-audit-docker ./
- /acc-audit-docker deep
- /acc-audit-docker ./ deep
- /acc-audit-docker -- focus on security
- /acc-audit-docker deep -- focus on security
- /acc-audit-docker -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if any word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path (or default `./`)
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)

## Pre-flight Check

1. **Find Docker artifacts:**
   ```bash
   # Dockerfiles
   ls Dockerfile* 2>/dev/null
   ls docker/Dockerfile* 2>/dev/null

   # Compose files
   ls docker-compose*.yml docker-compose*.yaml 2>/dev/null

   # Docker-related configs
   ls .dockerignore 2>/dev/null
   ls docker/ 2>/dev/null
   ls nginx.conf nginx/ 2>/dev/null

   # PHP project info
   cat composer.json 2>/dev/null | head -30
   ```

2. **If no Docker files found:**
   - Report "No Docker configuration found"
   - Suggest `/acc-generate-docker full` to create complete Docker setup

## Instructions

Use the `acc-docker-coordinator` agent to perform the audit:

```
Task tool with subagent_type="acc-docker-coordinator"
prompt: "Perform comprehensive Docker audit at [PATH]. Audit level: [LEVEL].

Operation: AUDIT

[FOCUS_AREAS if provided]

Use TaskCreate/TaskUpdate for progress visibility. Create tasks for each audit phase.

Audit areas:
1. Dockerfile architecture (multi-stage, layer ordering, BuildKit)
2. Base images and PHP extensions (selection, pinning, compatibility)
3. Docker Compose (services, health checks, networking, environment)
4. Performance (build time, image size, caching, PHP-FPM, OPcache)
5. Security (user permissions, secrets, vulnerabilities, network)
6. Production readiness (health checks, graceful shutdown, logging, monitoring)

Generate a full audit report with:
- Summary table by category
- Issues by severity (Critical/High/Medium/Low)
- Specific recommendations with code examples
- Overall score and risk level"
```

## Expected Output

The coordinator will delegate to specialized agents and aggregate results:

### Audit Report Structure

```markdown
# Docker Audit Report

**Project:** [NAME]
**Date:** [DATE]

## Executive Summary

| Category | Status | Critical | High | Medium | Low |
|----------|--------|----------|------|--------|-----|
| Dockerfile Architecture | ✅ | 0 | 0 | 1 | 2 |
| Base Images & Extensions | ⚠️ | 0 | 1 | 2 | 1 |
| Docker Compose | ⚠️ | 0 | 1 | 3 | 0 |
| Performance | ⚠️ | 0 | 2 | 2 | 1 |
| Security | 🔴 | 1 | 2 | 1 | 0 |
| Production Readiness | ⚠️ | 0 | 1 | 2 | 1 |

**Overall Score:** 68/100
**Risk Level:** MEDIUM

## Critical Issues

[Detailed critical issues with remediation steps...]

## Recommendations

### Immediate (This Week)
1. Fix security issues...

### Short-term (This Month)
1. Optimize build performance...

### Long-term
1. Implement monitoring...
```

## Audit Categories

### Dockerfile Architecture
- Multi-stage build usage
- Stage organization
- Layer ordering
- BuildKit features
- .dockerignore presence

### Base Images & Extensions
- Image selection (Alpine vs Debian)
- Version pinning
- Extension installation
- Build dependency cleanup

### Docker Compose
- Service configuration
- Health checks
- Networking
- Volume strategies
- Environment management

### Performance
- Build time optimization
- Image size
- Layer caching
- OPcache configuration
- PHP-FPM tuning

### Security
- User permissions (non-root)
- Secrets management
- Network exposure
- Image vulnerabilities
- Capability management

### Production Readiness
- Health checks
- Graceful shutdown
- Logging (stdout/stderr)
- Resource limits
- Restart policies

## Usage Examples

```bash
# Standard audit (default)
/acc-audit-docker

# Quick check
/acc-audit-docker quick

# Deep analysis
/acc-audit-docker deep

# With path and level
/acc-audit-docker ./ deep

# Deep + focus
/acc-audit-docker deep -- focus on security

# Backward compatible
/acc-audit-docker -- level:deep
```

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on security` | Deep security analysis |
| `performance only` | Only performance audit |
| `skip compose` | Exclude Compose audit |
| `image size analysis` | Focus on image size reduction |
| `production readiness` | Focus on deployment readiness |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Dockerfile lint | Basic Dockerfile structure, common issues |
| `standard` | Full 6-category | All 6 audit areas with detailed findings |
| `deep` | Standard + optimization | Standard + image size optimization, layer analysis, benchmark suggestions |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Security vulnerabilities, exposed secrets |
| High | 🟠 | Running as root, no health checks, cache invalidation |
| Medium | 🟡 | Missing optimizations, no .dockerignore |
| Low | 🟢 | Minor improvements, style suggestions |
