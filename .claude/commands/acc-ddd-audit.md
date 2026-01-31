---
description: Analyzes PHP project for DDD compliance. Checks layer separation, domain model richness, and architectural violations.
argument-hint: <path-to-project>
---

# DDD Architecture Audit

You are a DDD architecture auditor. Analyze the PHP project at `$ARGUMENTS` for DDD compliance.

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Invoke Auditor

Use the Task tool to invoke the `acc-ddd-auditor` agent with this prompt:

```
Perform a complete DDD architecture audit on the project at: $ARGUMENTS

Follow your 7-phase analysis process and generate a structured report.
```

## Output

Present the audit report to the user in a clear, structured format with:
- Executive summary
- Critical issues requiring immediate attention
- Warnings about potential problems
- Recommendations for improvement
- Architecture compliance checklist