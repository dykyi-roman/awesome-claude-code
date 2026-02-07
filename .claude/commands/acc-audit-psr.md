---
description: Audit PSR compliance. Checks PSR-1/PSR-12 coding style, PSR-4 autoloading, and PSR interface implementations. Use for PHP standards compliance review.
allowed-tools: Task
model: sonnet
argument-hint: <path> [-- additional instructions]
---

# PSR Compliance Audit

Invoke the `acc-psr-auditor` agent to perform a comprehensive PSR compliance audit.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-psr ./src
- /acc-audit-psr ./src -- focus on PSR-12 only
- /acc-audit-psr ./src -- skip autoloading, check interfaces
- /acc-audit-psr ./src -- check PSR-7 and PSR-15 implementations
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, additional focus/filters)

## Usage

```
/acc-audit-psr [path] [-- instructions]
```

## What It Checks

1. **PSR-1/PSR-12 Coding Style**
   - `declare(strict_types=1)` usage
   - Class naming (PascalCase)
   - Method naming (camelCase)
   - Constant naming (UPPER_CASE)
   - Line length limits (120 chars max)
   - Indentation (4 spaces, no tabs)

2. **PSR-4 Autoloading**
   - Composer autoload configuration
   - Namespace-to-path mapping
   - File naming matches class names

3. **PSR Interface Implementations**
   - Detects PSR-3, PSR-6, PSR-7, PSR-11, PSR-13, PSR-14, PSR-15, PSR-16, PSR-17, PSR-18, PSR-20
   - Recommends missing implementations

## Execution

Use the Task tool to invoke the PSR auditor agent:

```
Task tool with subagent_type="acc-psr-auditor"
prompt: "Perform PSR compliance audit for $ARGUMENTS. Check PSR-1/PSR-12 coding style, PSR-4 autoloading, and detect PSR interface implementations. Generate a detailed report with skill recommendations."
```

If no path is provided, audit the current project root.

## Output

The agent produces a structured report with:
- Compliance scores by category
- Specific violations with file:line references
- PSR interface detection results
- Skill recommendations for generating missing implementations
- Prioritized action items

## Generation Phase

After the audit, the agent will offer to generate missing PSR implementations using skills:
- `acc-create-psr3-logger` — Logger
- `acc-create-psr6-cache` — Cache Pool
- `acc-create-psr7-http-message` — HTTP Messages
- `acc-create-psr11-container` — DI Container
- `acc-create-psr13-link` — Hypermedia Links
- `acc-create-psr14-event-dispatcher` — Events
- `acc-create-psr15-middleware` — HTTP Middleware
- `acc-create-psr16-simple-cache` — Simple Cache
- `acc-create-psr17-http-factory` — HTTP Factories
- `acc-create-psr18-http-client` — HTTP Client
- `acc-create-psr20-clock` — Clock
