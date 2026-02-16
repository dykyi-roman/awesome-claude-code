---
description: Audit PSR compliance. Checks PSR-1/PSR-12 coding style, PSR-4 autoloading, and PSR interface implementations. Use for PHP standards compliance review.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path> [level] [-- meta-instructions]
---

# PSR Compliance Audit

Perform a comprehensive PSR compliance audit with actionable improvement recommendations.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: <path> [level] [-- <meta-instructions>]

Arguments:
- path: Target directory or file (required, default: current directory)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-psr ./src
- /acc-audit-psr ./src deep
- /acc-audit-psr ./src quick
- /acc-audit-psr ./src -- focus on PSR-12 only
- /acc-audit-psr ./src deep -- focus on interfaces
- /acc-audit-psr ./src -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if last word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)
7. Default path: current directory (if empty)

## Pre-flight Check

1. **Verify the path exists:**
   - If `$ARGUMENTS` is empty, audit current directory
   - If path doesn't exist, report error and stop

2. **Verify it's a PHP project:**
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

3. **Check PSR tooling:**
   - Look for `.php-cs-fixer.php`, `phpcs.xml`, `phpstan.neon`
   - Look for PSR packages in `composer.json` (psr/log, psr/cache, psr/http-message, etc.)
   - Note available vs missing tooling in report

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Structure only | `declare(strict_types=1)`, namespace conventions, basic naming |
| `standard` | Full analysis | PSR-1/12 coding style, PSR-4 autoloading, interface detection, file:line references |
| `deep` | Standard + quality | Standard + PSR interface implementation quality, method signatures, return types, docblock compliance |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Missing `strict_types`, wrong namespace-to-path mapping, broken autoloading |
| High | 🟠 | PSR-12 violations (indentation, line length, brace placement) |
| Medium | 🟡 | Naming convention issues, missing type declarations |
| Low | 🟢 | Style suggestions, optional improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on PSR-12` | Deep PSR-12 coding style analysis |
| `focus on interfaces` | Analyze PSR interface implementations in depth |
| `skip autoloading` | Exclude PSR-4 autoloading checks |
| `PSR-12 only` | Only check PSR-12 coding style |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

## Instructions

Use the `acc-psr-auditor` agent to perform a comprehensive PSR compliance audit:

```
Task tool with subagent_type="acc-psr-auditor"
prompt: "Perform PSR compliance audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Use TaskCreate/TaskUpdate for progress visibility. Create tasks for each audit phase.

Analyze:
1. PSR-1/PSR-12 Coding Style — strict_types, naming (PascalCase classes, camelCase methods, UPPER_CASE constants), indentation, line length, brace placement
2. PSR-4 Autoloading — composer autoload config, namespace-to-path mapping, file naming
3. PSR Interface Implementations — detect PSR-3, PSR-6, PSR-7, PSR-11, PSR-13, PSR-14, PSR-15, PSR-16, PSR-17, PSR-18, PSR-20 usage and quality

For each violation provide:
- Severity (🔴/🟠/🟡/🟢)
- File:line location
- What's wrong and how to fix it

Generate a detailed report with skill recommendations."
```

If no path is provided, audit the current project root.

## What It Checks

### 1. PSR-1/PSR-12 Coding Style
- `declare(strict_types=1)` usage
- Class naming (PascalCase)
- Method naming (camelCase)
- Constant naming (UPPER_CASE)
- Property naming (camelCase)
- Line length limits (120 chars max)
- Indentation (4 spaces, no tabs)
- Brace placement (Allman for classes, K&R for control)
- Use statement ordering
- Blank line rules

### 2. PSR-4 Autoloading
- Composer autoload configuration
- Namespace-to-path mapping correctness
- File naming matches class names
- One class per file

### 3. PSR Interface Implementations
- Detects PSR-3, PSR-6, PSR-7, PSR-11, PSR-13, PSR-14, PSR-15, PSR-16, PSR-17, PSR-18, PSR-20
- Implementation completeness
- Method signature correctness
- Recommends missing implementations

## Expected Output

```markdown
# PSR Compliance Audit Report

**Project:** [NAME] | **Date:** [DATE] | **Level:** [quick|standard|deep]

## 1. Executive Summary

| Category | Score | 🔴 | 🟠 | 🟡 | 🟢 |
|----------|-------|-----|-----|-----|-----|
| PSR-1 Basic | X/100 | N | N | N | N |
| PSR-12 Style | X/100 | N | N | N | N |
| PSR-4 Autoloading | X/100 | N | N | N | N |
| PSR Interfaces | X/100 | N | N | N | N |

**Overall Score:** X/100 | **Risk Level:** LOW/MEDIUM/HIGH/CRITICAL

## 2. PSR-1/PSR-12 Compliance

### 🔴 Critical Issues
- **Location:** `file.php:line` — Missing `declare(strict_types=1)` — Add declaration

### 🟠 High Priority
- **Location:** `file.php:line` — Wrong brace placement — Move to next line

### 🟡 Medium
- **Location:** `file.php:line` — Method naming — Rename to camelCase

## 3. PSR-4 Autoloading

| Namespace | Path | Status |
|-----------|------|--------|
| App\Domain | src/Domain/ | ✅ |
| App\Infra | src/Infrastructure/ | 🟠 Mismatch |

## 4. PSR Interface Detection

| PSR | Package | Implemented | Quality |
|-----|---------|-------------|---------|
| PSR-3 | psr/log | ✅ | Good |
| PSR-7 | — | ❌ Not found | — |
| PSR-11 | psr/container | ✅ | Good |

## 5. Skill Recommendations

| Gap | Skill | Command |
|-----|-------|---------|
| No PSR-3 logger | `acc-create-psr3-logger` | `/acc-generate-psr logger` |
| No PSR-7 messages | `acc-create-psr7-http-message` | `/acc-generate-psr http-message` |
| No PSR-15 middleware | `acc-create-psr15-middleware` | `/acc-generate-psr middleware` |

## 6. Action Items

1. 🔴 Add `declare(strict_types=1)` to N files
2. 🟠 Fix PSR-12 brace placement in N files
3. 🟡 Rename N methods to camelCase
4. 🟢 Consider implementing PSR-3 logger
```

## Usage Examples

```bash
# Standard audit (default)
/acc-audit-psr ./src

# Quick check
/acc-audit-psr ./src quick

# Deep analysis with interface quality
/acc-audit-psr ./src deep

# Focus on specific PSR
/acc-audit-psr ./src -- focus on PSR-12 only

# Deep + focus
/acc-audit-psr ./src deep -- focus on interfaces

# Backward compatible
/acc-audit-psr ./src -- level:deep
```
