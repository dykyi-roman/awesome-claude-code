---
description: Comprehensive CI/CD audit. Analyzes pipeline structure, security, performance, and best practices compliance.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: [path] [level] [-- meta-instructions]
---

# CI/CD Audit

Perform a comprehensive audit of CI/CD configuration, including security, performance, and best practices.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: [path] [level] [-- <meta-instructions>]

Arguments:
- path: Target directory (optional, default: ./)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-ci
- /acc-audit-ci ./
- /acc-audit-ci deep
- /acc-audit-ci ./ deep
- /acc-audit-ci -- focus on security
- /acc-audit-ci deep -- focus on security
- /acc-audit-ci -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if any word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path (or default `./`)
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)

## Pre-flight Check

1. **Find CI artifacts:**
   ```bash
   # CI configurations
   find . -name "*.yml" -path "*/.github/*" 2>/dev/null
   ls .gitlab-ci.yml 2>/dev/null

   # Docker files
   ls Dockerfile* 2>/dev/null

   # Static analysis configs
   ls phpstan.neon* psalm.xml* .php-cs-fixer* deptrac.yaml* 2>/dev/null

   # Test config
   ls phpunit.xml* 2>/dev/null
   ```

2. **If no CI found:**
   - Report "No CI configuration found"
   - Suggest `/acc-ci-setup`

## Instructions

Use the `acc-ci-coordinator` agent to perform the audit:

```
Task tool with subagent_type="acc-ci-coordinator"
prompt: "Perform comprehensive CI/CD audit at [PATH]. Audit level: [LEVEL].

Operation: AUDIT

[FOCUS_AREAS if provided]

Use TaskCreate/TaskUpdate for progress visibility. Create tasks for each audit phase.

Audit areas:
1. Pipeline structure and stages
2. Static analysis configuration
3. Test configuration and coverage
4. Security (secrets, permissions, dependencies)
5. Performance (caching, parallelization)
6. Docker configuration
7. Deployment configuration

Generate a full audit report with:
- Summary by category
- Issues by severity
- Specific recommendations
- Action items"
```

## Expected Output

The coordinator will delegate to specialized agents and aggregate results:

### Audit Report Structure

```markdown
# CI/CD Audit Report

**Project:** [NAME]
**Date:** [DATE]

## Executive Summary

| Category | Status | Critical | High | Medium | Low |
|----------|--------|----------|------|--------|-----|
| Pipeline | ✅ | 0 | 0 | 1 | 2 |
| Static Analysis | ⚠️ | 0 | 2 | 3 | 1 |
| Testing | ⚠️ | 0 | 1 | 2 | 0 |
| Security | 🔴 | 1 | 2 | 1 | 0 |
| Performance | ⚠️ | 0 | 1 | 3 | 2 |
| Docker | ✅ | 0 | 0 | 1 | 1 |
| Deployment | ⚠️ | 0 | 1 | 1 | 0 |

**Overall Score:** 72/100
**Risk Level:** MEDIUM

## Critical Issues

[Detailed critical issues...]

## Recommendations

### Immediate (This Week)
1. Fix security issue...
2. ...

### Short-term (This Month)
1. ...

### Long-term
1. ...
```

## Audit Categories

### Pipeline Structure
- Stage organization
- Job dependencies
- Triggers configuration
- Error handling

### Static Analysis
- PHPStan level
- Psalm configuration
- DEPTRAC rules
- Baseline management

### Testing
- Coverage thresholds
- Test organization
- Integration tests
- CI test configuration

### Security
- Secrets handling
- Permissions
- Dependency vulnerabilities
- Container security

### Performance
- Caching efficiency
- Parallelization
- Build times
- Resource usage

### Docker
- Image size
- Layer optimization
- Security best practices
- Multi-stage builds

### Deployment
- Zero-downtime
- Health checks
- Rollback procedures
- Feature flags

## Usage Examples

```bash
# Standard audit (default)
/acc-audit-ci

# Quick check
/acc-audit-ci quick

# Deep analysis
/acc-audit-ci deep

# With path and level
/acc-audit-ci ./ deep

# Deep + focus
/acc-audit-ci deep -- focus on security

# Backward compatible
/acc-audit-ci -- level:deep
```

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on security` | Deep security analysis |
| `performance only` | Only performance audit |
| `skip deployment` | Exclude deployment audit |
| `include dependency scan` | Full dependency vulnerability scan |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Structure check | Pipeline structure, basic config validation |
| `standard` | Full 7-category | All 7 audit areas with detailed findings |
| `deep` | Standard + dependencies | Standard + dependency vulnerability scan, cross-job optimization |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Security vulnerabilities, data exposure |
| High | 🟠 | Significant issues, missing best practices |
| Medium | 🟡 | Improvements recommended |
| Low | 🟢 | Minor suggestions |
