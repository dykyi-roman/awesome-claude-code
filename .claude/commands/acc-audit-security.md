---
description: Security audit (OWASP Top 10, PHP-specific vulnerabilities). Analyzes input validation, injection, authentication, authorization, CSRF, XSS, XXE, SSRF, deserialization, path traversal.
allowed-tools: Read, Grep, Glob, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# Security Audit

Perform a comprehensive security audit focusing on OWASP Top 10 and PHP-specific vulnerabilities.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-security ./src
- /acc-audit-security ./src -- focus on OWASP A01-A03
- /acc-audit-security ./src/Payment -- check SQL injection and CSRF
- /acc-audit-security ./src -- skip A06 (vulnerable components)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, focus areas)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — customize audit focus

If meta-instructions provided, adjust audit to:
- Focus on specific OWASP categories mentioned
- Skip categories if requested
- Apply additional checks
- Modify output verbosity

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Instructions

Use the `acc-security-reviewer` agent to perform a comprehensive security audit:

```
Task tool with subagent_type="acc-security-reviewer"
prompt: "Perform security audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Analyze for:
1. Input Validation (A03:2021)
2. Output Encoding / XSS (A03:2021)
3. SQL Injection (A03:2021)
4. Command Injection (A03:2021)
5. Authentication Issues (A07:2021)
6. Authorization / Access Control (A01:2021)
7. CSRF Protection (A01:2021)
8. Sensitive Data Exposure (A02:2021)
9. Cryptographic Failures (A02:2021)
10. SSRF (A10:2021)
11. XXE (A05:2021)
12. Insecure Deserialization (A08:2021)
13. Path Traversal (A01:2021)
14. Dependency Vulnerabilities (A06:2021)

Provide:
- Severity classification (Critical/Major/Minor)
- CWE identifiers
- Attack vectors
- Code examples (vulnerable and fixed)
- OWASP references"
```

## Analysis Scope

### OWASP Top 10 (2021) Coverage

| OWASP ID | Category | Checks |
|----------|----------|--------|
| A01:2021 | Broken Access Control | IDOR, missing auth checks, CSRF, path traversal |
| A02:2021 | Cryptographic Failures | Weak crypto, exposed secrets, plaintext storage |
| A03:2021 | Injection | SQL, Command, XPath, LDAP, XSS |
| A04:2021 | Insecure Design | Business logic flaws, missing controls |
| A05:2021 | Security Misconfiguration | XXE, default configs, exposed endpoints |
| A06:2021 | Vulnerable Components | Outdated dependencies, known CVEs |
| A07:2021 | Auth Failures | Weak passwords, session issues, token flaws |
| A08:2021 | Software Integrity | Deserialization, unsigned updates |
| A09:2021 | Logging Failures | Missing audit, log injection |
| A10:2021 | SSRF | User-controlled URLs, internal network access |

### PHP-Specific Vulnerabilities

- `unserialize()` with user input
- `eval()` / `preg_replace()` with `e` modifier
- `shell_exec()` / `exec()` / `system()` without escaping
- `include()` / `require()` with user input
- Unsafe file operations (`file_get_contents`, `fopen`)
- Type juggling vulnerabilities
- `extract()` and variable overwriting

## Expected Output

A structured markdown report containing:

### 1. Executive Summary
- Total vulnerabilities found by severity
- Critical issues requiring immediate attention
- Overall security posture

### 2. Vulnerability Dashboard

| Severity | Count | Categories |
|----------|-------|------------|
| 🔴 Critical | N | SQL Injection, RCE |
| 🟠 Major | N | XSS, CSRF, Auth |
| 🟡 Minor | N | Best practices |

### 3. Critical Vulnerabilities

For each critical issue:

```markdown
### [OWASP Category]: [Brief Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-XXX

**Issue:**
[Detailed description]

**Attack Vector:**
[How an attacker could exploit this]

**Vulnerable Code:**
```php
// Vulnerable code
```

**Secure Fix:**
```php
// Fixed code
```

**References:**
- OWASP: [link]
- CWE: [link]
```

### 4. Major Vulnerabilities

[Same format as Critical]

### 5. Minor Issues / Best Practices

[Condensed list format]

### 6. Recommendations Summary

| Priority | Action | Location | Fix |
|----------|--------|----------|-----|
| 1 | Fix SQL injection | `UserRepository.php:45` | Use prepared statements |
| 2 | Add CSRF tokens | `LoginAction.php:23` | Implement token validation |

### 7. Compliance Checklist

| OWASP Category | Status | Issues |
|----------------|--------|--------|
| A01 Access Control | ⚠️ | 3 issues |
| A02 Crypto Failures | ✅ | 0 issues |
| A03 Injection | ❌ | 5 issues |
| ... | ... | ... |

## Audit Levels

Extract audit level from meta-instructions: `level:quick`, `level:standard`, `level:deep`. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Critical patterns only | `eval()`, `unserialize()`, SQL injection, command injection |
| `standard` | Full OWASP analysis | All 14 vulnerability categories, CWE references, fix suggestions |
| `deep` | Standard + extended | Standard + dependency vulnerability scan, attack vector mapping, CWE chains |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | RCE, SQL injection, auth bypass, data breach, deserialization |
| High | 🟠 | XSS, CSRF, information disclosure, privilege escalation |
| Medium | 🟡 | Missing best practices, theoretical attacks, low-impact issues |
| Low | 🟢 | Code hardening suggestions, defense-in-depth improvements |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on injection` | Deep injection analysis (SQL, Command, XSS) |
| `focus on A01-A03` | Analyze specific OWASP categories only |
| `skip A06` | Exclude vulnerable components check |
| `injection only` | Only check injection vulnerabilities |
| `level:quick` | Fast audit (only critical patterns) |
| `level:deep` | Deep audit (+ dependency scan + attack vectors) |
| `detailed report` | Maximum detail with CWE references |
| `на русском` | Report in Russian |

## Usage Examples

```bash
/acc-audit-security ./src
/acc-audit-security ./src/Api -- focus on input validation
/acc-audit-security ./src/Payment -- check A01-A03 only
/acc-audit-security . -- level:deep
/acc-audit-security ./src -- level:quick
```