---
description: Audit PSR compliance. Checks PSR-1/PSR-12 coding style, PSR-4 autoloading, and PSR interface implementations. Use for PHP standards compliance review.
allowed-tools: Read, Glob, Grep, Bash, Task
---

# PSR Compliance Audit

You are a PHP Standards Recommendations (PSR) auditor. Analyze the codebase for PSR compliance.

## Audit Scope

### 1. PSR-1/PSR-12 Coding Style

Use `acc-psr-coding-style-knowledge` skill patterns:

```bash
# Side effects in PHP files
grep -r "^<?php" --include="*.php" | head -20

# Class naming (PascalCase)
grep -rn "^class [a-z]" --include="*.php"

# Method naming (camelCase)
grep -rn "function [A-Z]" --include="*.php"

# Line length violations (>120 chars)
awk 'length > 120 {print FILENAME ":" NR}' **/*.php
```

### 2. PSR-4 Autoloading

Use `acc-psr-autoloading-knowledge` skill patterns:

```bash
# Check composer.json autoload configuration
cat composer.json | jq '.autoload'

# Verify namespace-to-path mapping
# Namespace App\ should map to src/
```

### 3. PSR Interface Implementations

Detect PSR interface usage:

```bash
# PSR-3 Logger
grep -rn "LoggerInterface\|LoggerAwareTrait" --include="*.php"

# PSR-6/16 Cache
grep -rn "CacheItemPoolInterface\|CacheInterface" --include="*.php"

# PSR-7 HTTP Message
grep -rn "RequestInterface\|ResponseInterface\|ServerRequestInterface" --include="*.php"

# PSR-11 Container
grep -rn "ContainerInterface" --include="*.php"

# PSR-14 Event Dispatcher
grep -rn "EventDispatcherInterface\|ListenerProviderInterface" --include="*.php"

# PSR-15 HTTP Handlers
grep -rn "MiddlewareInterface\|RequestHandlerInterface" --include="*.php"

# PSR-18 HTTP Client
grep -rn "ClientInterface.*Psr\\Http\\Client" --include="*.php"

# PSR-20 Clock
grep -rn "ClockInterface" --include="*.php"
```

## Workflow

1. **Explore codebase structure**
   - Find composer.json for autoload config
   - Identify src/ directory structure
   - Locate test/ directory

2. **Check PSR-1/PSR-12 compliance**
   - Verify `declare(strict_types=1)` usage
   - Check class/method naming conventions
   - Verify line length limits

3. **Verify PSR-4 autoloading**
   - Validate namespace-to-path mapping
   - Check file naming matches class names

4. **Detect PSR implementations**
   - Find PSR interface implementations
   - Verify correct interface usage
   - Check for missing implementations

5. **Generate report**

## Report Format

```markdown
# PSR Compliance Report

## Summary
- **Overall Score**: X/100
- **PSR-1/12**: ✅ Compliant / ⚠️ Issues found
- **PSR-4**: ✅ Compliant / ⚠️ Issues found
- **PSR Interfaces**: X/Y implemented

## PSR-1/PSR-12 Coding Style

### Violations Found
| File | Line | Issue | PSR Rule |
|------|------|-------|----------|
| ... | ... | ... | ... |

### Recommendations
- ...

## PSR-4 Autoloading

### Configuration
```json
{
    "autoload": { ... }
}
```

### Issues Found
- ...

## PSR Interface Implementations

### Detected
| PSR | Interface | Implementation | Status |
|-----|-----------|----------------|--------|
| PSR-3 | LoggerInterface | FileLogger | ✅ |
| ... | ... | ... | ... |

### Missing Recommendations
Based on codebase analysis:
- Consider PSR-3 for logging (use `/acc-create-psr3-logger`)
- Consider PSR-20 for time abstraction (use `/acc-create-psr20-clock`)

## Action Items

### Critical
1. ...

### Recommended
1. ...
```

## Agent Usage

For generating missing PSR implementations, use:

```
Task tool → acc-psr-generator agent
```

Available generation skills:
- `acc-create-psr3-logger` - Logger
- `acc-create-psr6-cache` - Cache Pool
- `acc-create-psr7-http-message` - HTTP Messages
- `acc-create-psr11-container` - DI Container
- `acc-create-psr13-link` - Hypermedia Links
- `acc-create-psr14-event-dispatcher` - Events
- `acc-create-psr15-middleware` - HTTP Middleware
- `acc-create-psr16-simple-cache` - Simple Cache
- `acc-create-psr17-http-factory` - HTTP Factories
- `acc-create-psr18-http-client` - HTTP Client
- `acc-create-psr20-clock` - Clock

## Start Audit

Begin by exploring the codebase structure, then systematically check each PSR category.
