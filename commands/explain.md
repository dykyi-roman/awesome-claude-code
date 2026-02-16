---
description: Explain code — structure, business logic, data flows, architecture. Accepts file/dir, HTTP route (GET /api/orders), or console command (app:process-payments). Modes: quick, deep, onboarding, business, qa.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path|route|command> [mode] [-- instructions]
---

# Code Explain Command

Explain code structure, business logic, data flows, and architecture patterns for any scope — from a single file to an entire project, HTTP route, or console command.

## Input Parsing

Parse `$ARGUMENTS` to extract input, mode, and optional meta-instructions:

```
Format: <input> [mode] [-- instructions]

Arguments:
- input: File, directory, ".", HTTP route, or console command (required)
- mode: quick|deep|onboarding|business|qa (optional, auto-detected)
- -- instructions: Focus area or specific question (optional)

Input types (auto-detected):
1. HTTP route:    GET /api/orders
2. HTTP route:    POST /api/orders/{id}/status
3. Console cmd:   app:process-payments
4. Console cmd:   import:products
5. File path:     src/Domain/Order/Order.php
6. Directory:     src/Domain/Order/
7. Project root:  .

Examples:
- /acc-explain GET /api/orders
- /acc-explain POST /api/orders/{id}/status deep
- /acc-explain app:process-payments
- /acc-explain import:products -- explain data transformation pipeline
- /acc-explain src/Domain/Order/Order.php
- /acc-explain src/Domain/Order/
- /acc-explain . onboarding
- /acc-explain src/Payment business
- /acc-explain src/Domain/Order/ deep -- focus on state transitions
- /acc-explain . qa -- how does payment processing work?
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = input + optional mode, Second part = meta-instructions
3. Check if last word of first part is a valid mode (`quick|deep|onboarding|business|qa`)
4. If valid mode found, extract it; everything else is the input
5. If no mode specified, auto-detect based on input type

## Input Type Detection

Before path validation, detect input type from the parsed input:

1. If input matches `^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/` → `input_type = "route"`
2. If input matches `^[a-z][a-z0-9_-]*:[a-z][a-z0-9:_-]*$` → `input_type = "command"`
3. If `test -f input` → `input_type = "file"`
4. If `test -d input` → `input_type = "directory"`
5. If input = "." → `input_type = "project"`
6. Otherwise → report error: "Invalid input. Provide a file/directory path, HTTP route (GET /path), or console command (namespace:name)."

**For route/command input:** skip `test -e` validation — resolution happens in the coordinator.

## Pre-flight Checks

### For file/directory/project input (existing behavior):

1. **Validate path exists:**
   ```bash
   test -e "[path]"
   ```
   If path doesn't exist, report error and stop.

2. **Auto-detect mode (if not specified):**
   | Input type | Default mode |
   |------------|-------------|
   | HTTP route | `quick` |
   | Console command | `quick` |
   | File | `quick` |
   | Directory (not root) | `deep` |
   | `.` (project root) | `onboarding` |

3. **Verify PHP files exist in path (file/directory only):**
   ```bash
   # For file: check it's a PHP file or has PHP content
   # For directory: check for *.php files
   find [path] -name "*.php" -type f | head -1
   ```
   If no PHP files found and mode is not `business`, warn but continue (may have config files).

### For route/command input:

1. Skip path existence check
2. Auto-detect mode as `quick` (unless user overrides)
3. Skip PHP file existence check — coordinator will resolve handler

## Delegation

Delegate to the `acc-explain-coordinator` agent with all parsed parameters:

```
Task: acc-explain-coordinator
prompt: |
  Explain the code for the following input:

  Input: [detected input]
  Input type: [route|command|file|directory|project]
  Mode: [detected or auto-detected mode]
  Meta-instructions: [if provided after --]

  Execute the full explanation workflow:
  0. Resolve — if route/command, resolve to handler file (Phase 0)
  1. Navigate — scan structure, find entry points, detect patterns
  2. Analyze — extract business logic, trace data flows (+ auditors for deep/onboarding)
  3. Visualize — generate diagrams (for deep/onboarding/business modes)
  4. Present — aggregate results using the appropriate output template

  End with documentation suggestion.
```

## Modes

| Mode | Auto-detect | Depth | Audience |
|------|-------------|-------|----------|
| `quick` | Single file, HTTP route, console command | 1-2 screens | Developer |
| `deep` | Directory | Full analysis + diagrams | Senior dev / Architect |
| `onboarding` | `.` (root) | Comprehensive guide | New team member |
| `business` | Explicit only | Non-technical | PM / Stakeholder |
| `qa` | Explicit only | Answer-focused | Any |

## Expected Output

The coordinator returns a structured explanation appropriate to the mode:

### Quick Mode (~50 lines)
- Purpose, business context
- Key responsibilities
- Business rules table
- Data flow summary
- Dependencies
- Important notes

### Deep Mode (full analysis)
- Architecture overview with Mermaid diagrams
- Component map per layer
- Business processes with steps
- Data flow with sequence diagrams
- Domain model and glossary
- State machines (if found)
- Quality observations
- Documentation suggestion

### Onboarding Mode (project guide)
- What is this project?
- Tech stack
- Architecture overview (C4 diagrams)
- Project structure with annotations
- Modules/bounded contexts
- Key business processes
- API endpoints
- Domain model with class diagrams
- How to navigate the code
- Glossary
- Documentation suggestion

### Business Mode (non-technical)
- What does it do? (plain language)
- Who uses it?
- Key business processes
- Business rules (no code)
- Simple flow diagrams
- Limitations

### QA Mode (interactive)
- Direct answer to question
- Supporting evidence with code references
- Related areas to explore

## Usage Examples

```bash
# HTTP route: explain API endpoint handler
/acc-explain GET /api/orders
/acc-explain POST /api/orders/{id}/status
/acc-explain DELETE /api/users/{id} -- explain cascade deletion

# HTTP route with mode override
/acc-explain POST /api/orders deep -- trace full request lifecycle with diagrams

# Console command: explain command handler
/acc-explain app:process-payments
/acc-explain import:products -- explain data transformation pipeline

# Quick: explain a single file
/acc-explain src/Domain/Order/Order.php

# Deep: explain a module
/acc-explain src/Domain/Order/

# Onboarding: project guide for new developer
/acc-explain .

# Business: explain for stakeholder
/acc-explain src/Payment business

# QA: ask specific question
/acc-explain src/Domain qa -- how are discounts calculated?

# With focus instructions
/acc-explain src/Domain/Order/ deep -- focus on state transitions and events

# Quick with context
/acc-explain src/Infrastructure/Repository/OrderRepository.php -- explain query optimization
```
