---
name: acc-check-dependency-vulnerabilities
description: Analyzes PHP dependencies for security vulnerabilities. Detects outdated packages, known CVEs, unsupported versions, vulnerable transitive dependencies.
---

# Dependency Vulnerability Check

Analyze PHP project dependencies for security vulnerabilities.

## Analysis Process

### 1. Check composer.json/composer.lock

```bash
# Read composer.lock to get exact versions
cat composer.lock | jq '.packages[] | {name, version}'

# Check for outdated packages
composer outdated --direct

# Security audit
composer audit
```

### 2. Common Vulnerable Packages

| Package | Vulnerable Versions | Issue | CVE |
|---------|---------------------|-------|-----|
| symfony/http-kernel | < 4.4.50 | Request smuggling | CVE-2022-24894 |
| guzzlehttp/guzzle | < 7.4.5 | Header injection | CVE-2022-31090 |
| doctrine/dbal | < 2.13.9 | SQL injection | CVE-2021-43608 |
| laravel/framework | < 8.83.27 | SQL injection | CVE-2022-44268 |
| phpseclib | < 3.0.14 | RCE | CVE-2023-27560 |
| twig/twig | < 2.15.3 | SSTI | CVE-2022-39261 |
| phpmailer/phpmailer | < 6.5.0 | XSS | CVE-2021-34551 |
| monolog/monolog | < 2.7.0 | RCE via SMTP | CVE-2022-29244 |

### 3. End-of-Life Versions

```php
// CRITICAL: EOL PHP versions
// PHP 7.4 - EOL November 2022
// PHP 8.0 - EOL November 2023

// Check supported versions:
// PHP 8.1 - Security fixes until December 2025
// PHP 8.2 - Security fixes until December 2026
// PHP 8.3 - Security fixes until December 2027
```

### 4. Detection Patterns

```json
// composer.json - Risky version constraints
{
    "require": {
        "vendor/package": "*",        // CRITICAL: Any version
        "vendor/package": ">=1.0",    // VULNERABLE: Too permissive
        "vendor/package": "^1.0",     // OK: Semver constraint
        "vendor/package": "1.2.3",    // Best: Exact version
        "vendor/package": "dev-main"  // CRITICAL: Unstable
    }
}
```

### 5. Abandoned Packages

```bash
# Check for abandoned packages
composer show --abandoned

# Common abandoned packages to replace:
# phpunit/dbunit → Use fixtures
# zendframework/* → laminas/*
# swiftmailer/swiftmailer → symfony/mailer
# paragonie/random_compat → Use random_bytes() (PHP 7+)
```

### 6. Transitive Dependencies

```bash
# Check dependency tree
composer depends vendor/package

# Find why a vulnerable package is included
composer why vendor/vulnerable-package
```

## Grep Patterns

```bash
# composer.json with wildcard versions
Grep: '"\\*"|"dev-|">=|">' --glob "**/composer.json"

# Known vulnerable package names
Grep: "guzzlehttp/guzzle|symfony/http-kernel|doctrine/dbal" --glob "**/composer.lock"

# EOL PHP version
Grep: '"php":\s*"[^"]*7\.[0-4]|"php":\s*"[^"]*8\.0' --glob "**/composer.json"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Known CVE with exploit | 🔴 Critical |
| EOL PHP version | 🔴 Critical |
| Abandoned package with issues | 🟠 Major |
| Outdated with security fixes | 🟠 Major |
| Wildcard version constraint | 🟡 Minor |

## Vulnerability Resources

- **PHP Security Advisories Database**: https://github.com/FriendsOfPHP/security-advisories
- **Snyk Vulnerability DB**: https://snyk.io/vuln
- **NVD**: https://nvd.nist.gov/
- **Packagist Advisories**: https://packagist.org/advisories

## Remediation

### Upgrade Process

```bash
# Check what will be upgraded
composer update --dry-run

# Update specific package
composer update vendor/package --with-dependencies

# Update all packages
composer update

# After update, run tests
./vendor/bin/phpunit
```

### Version Constraints

```json
{
    "require": {
        // Good: Specific minor version
        "vendor/package": "^2.5",

        // Best: Lock to patch version in production
        "vendor/package": "2.5.3"
    }
}
```

### Lock File Management

```bash
# Always commit composer.lock
git add composer.lock

# Use consistent platform
composer config platform.php 8.2

# Audit before deploy
composer audit --locked
```

## Output Format

```markdown
### Vulnerable Dependency: [package-name]

**Severity:** 🔴/🟠/🟡
**Current Version:** 1.2.3
**Fixed Version:** 1.2.4
**CVE:** CVE-2024-XXXX

**Issue:**
[Description of the vulnerability]

**Risk:**
[What an attacker can do]

**Location:**
- `composer.lock:line` (direct dependency)
- Required by: `other/package`

**Fix:**
```bash
composer update vendor/package
```

**Workaround (if upgrade not possible):**
[Temporary mitigation]
```

## Automated Scanning

### GitHub Dependabot

```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "composer"
    directory: "/"
    schedule:
      interval: "weekly"
    open-pull-requests-limit: 10
```

### CI/CD Integration

```yaml
# In CI pipeline
- name: Security Audit
  run: composer audit --format=json > audit.json

- name: Check for vulnerabilities
  run: |
    if [ -s audit.json ]; then
      cat audit.json
      exit 1
    fi
```

## Important Notes

1. **Always check composer.lock** — Not just composer.json
2. **Transitive dependencies matter** — Your dependencies have dependencies
3. **Regular audits** — Run `composer audit` in CI/CD
4. **Test after updates** — Security updates can break things
5. **Monitor advisories** — Subscribe to security mailing lists
