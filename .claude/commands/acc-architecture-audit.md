---
description: Comprehensive architecture audit for PHP projects. Detects and validates DDD, CQRS, Clean Architecture, Event Sourcing patterns. Returns detailed compliance report.
allowed-tools: Read, Grep, Glob, Bash, Task
model: sonnet
argument-hint: <path-to-php-project>
---

# Architecture Audit Command

Perform a comprehensive architecture audit analyzing multiple architectural patterns.

## Target

Analyze the project at: `$ARGUMENTS`

If no path provided, analyze the current working directory.

## Instructions

Use the `acc-architecture-auditor` agent to perform a comprehensive architecture audit.

The audit should:

1. **Detect patterns** used in the project (DDD, CQRS, Clean Architecture, Event Sourcing)
2. **Analyze compliance** for each detected pattern
3. **Identify cross-pattern issues** and conflicts
4. **Generate a detailed report** with:
   - Compliance scores
   - Critical issues requiring immediate attention
   - Warnings for improvement
   - Actionable recommendations

## Expected Output

A structured markdown report containing:

- Executive summary
- Pattern detection results
- Compliance matrix with scores
- Critical issues with file locations and fixes
- Warnings with recommendations
- Cross-pattern conflict analysis
- Prioritized action items

## Usage Examples

```
/acc-architecture-audit
/acc-architecture-audit src/
/acc-architecture-audit /path/to/project
```
