---
description: Guided refactoring with analysis and pattern application. Analyzes code smells, SOLID violations, testability issues. Provides prioritized refactoring roadmap with generation commands.
allowed-tools: Read, Write, Edit, Grep, Glob, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# Guided Refactoring

Perform comprehensive code analysis and guide through safe, incremental refactoring with pattern application.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-refactor ./src/Domain/OrderService.php
- /acc-refactor ./src/Application -- focus on SOLID violations
- /acc-refactor ./src -- extract value objects only
- /acc-refactor ./src/Service -- analyze testability, skip style
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, file or directory)
3. Second part = **meta-instructions** (optional, focus areas)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — customize refactoring focus

If meta-instructions provided, adjust analysis to:
- Focus on specific issue categories
- Skip categories if requested
- Prioritize specific refactorings
- Apply specific patterns

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the target path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `*.php` files
   - If not PHP code, report and stop

3. Check Git status:
   - Warn if there are uncommitted changes
   - Recommend committing before refactoring

## Instructions

Use the `acc-refactor-coordinator` agent to perform guided refactoring:

```
Task tool with subagent_type="acc-refactor-coordinator"
prompt: "Perform refactoring analysis on [PATH]. [META-INSTRUCTIONS if provided]

Analysis scope:
1. CODE SMELLS — God Class, Long Method, Primitive Obsession, Feature Envy, Data Clump
2. SOLID VIOLATIONS — SRP, OCP, LSP, ISP, DIP
3. READABILITY — Naming, complexity, nesting, magic values
4. TESTABILITY — DI issues, side effects, coverage gaps

Provide:
- Prioritized issue list (Critical/High/Medium)
- Refactoring techniques for each issue
- Generator commands for automated fixes
- Safety warnings and prerequisites
- Interactive prompts for execution"
```

## Analysis Categories

### Code Smells

| Smell | Detection | Refactoring |
|-------|-----------|-------------|
| **God Class** | >300 lines, >10 methods | Extract Class |
| **Long Method** | >30 lines | Extract Method |
| **Primitive Obsession** | String email, int price | Value Object |
| **Feature Envy** | Chain calls to other objects | Move Method |
| **Data Clump** | Same params in multiple methods | DTO/VO |
| **Long Parameter List** | >4 parameters | Builder/DTO |
| **Duplicate Code** | Similar code blocks | Extract Method |
| **Dead Code** | Unused methods/classes | Delete |

### SOLID Violations

| Principle | Violation | Fix | Generator |
|-----------|-----------|-----|-----------|
| **SRP** | Multiple responsibilities | Extract classes | `acc-ddd-generator`, `acc-cqrs-generator` |
| **OCP** | Type switches, if/else chains | Strategy pattern | `/acc-generate-patterns strategy` |
| **LSP** | Exceptions in overrides | Redesign hierarchy | Manual |
| **ISP** | Unused interface methods | Split interface | Manual |
| **DIP** | `new` in constructors | DI, Factories | `acc-create-factory` |

### Testability Issues

| Issue | Detection | Fix |
|-------|-----------|-----|
| Hard coupling | `new` in business logic | Inject dependencies |
| Static calls | `SomeClass::method()` | Inject instance |
| Global state | `$_SESSION`, `$_GET` | Request object |
| Side effects | File I/O, HTTP in logic | Infrastructure layer |
| No interfaces | Concrete dependencies | Extract interface |

## Expected Output

### 1. Executive Summary

```
Refactoring Analysis: src/Application/Service/OrderService.php

| Category | Issues | Critical | High | Medium |
|----------|--------|----------|------|--------|
| Code Smells | 8 | 2 | 4 | 2 |
| SOLID | 5 | 1 | 3 | 1 |
| Testability | 4 | 2 | 2 | 0 |
| Readability | 6 | 0 | 2 | 4 |

Overall Score: 45/100 (Needs Significant Refactoring)
```

### 2. Critical Issues

For each critical issue:

```markdown
### God Class: OrderService

**Location:** `src/Application/Service/OrderService.php`
**Metrics:**
- Lines: 523 (target: <300)
- Methods: 28 (target: <10)
- Dependencies: 12 (target: <5)

**Responsibilities Found:**
1. Order processing
2. Payment handling
3. Email notifications
4. Inventory updates
5. Logging

**Refactoring Plan:**
1. Extract `PaymentProcessor` (methods: processPayment, refundPayment)
2. Extract `OrderNotifier` (methods: sendConfirmation, sendShipment)
3. Extract `InventoryUpdater` (methods: reserveStock, releaseStock)
4. Keep `OrderService` as orchestrator

**Generator Commands:**
```bash
acc-create-domain-service PaymentProcessor
acc-create-domain-service OrderNotifier
/acc-generate-patterns mediator OrderWorkflow
```

**Prerequisites:**
- [ ] Ensure tests exist for OrderService
- [ ] Commit current state
```

### 3. Refactoring Roadmap

| Priority | Issue | File | Refactoring | Command |
|----------|-------|------|-------------|---------|
| P1 | God Class | OrderService.php | Extract classes | `acc-create-domain-service` |
| P1 | No DI | PaymentHandler.php | Add constructor DI | Manual |
| P2 | Primitive | User.php | Value Object | `acc-create-value-object Email` |
| P2 | Type Switch | DiscountHandler.php | Strategy | `/acc-generate-patterns strategy` |
| P3 | Magic values | Config.php | Constants | Manual |
| P3 | Long method | ReportGenerator.php | Extract method | Manual |

### 4. Quick Wins

Safe refactorings that can be applied immediately:

```markdown
1. **Rename variable** `$d` → `$orderDate` at OrderService.php:123
2. **Extract constant** `3` → `MAX_RETRY_COUNT` at ApiClient.php:45
3. **Add return type** `process(): Order` at OrderProcessor.php:78
4. **Remove dead code** `unusedMethod()` at Helper.php:200
```

### 5. Test Coverage Warning

```
⚠️ Before refactoring, add tests:

| File | Current | Required | Gap |
|------|---------|----------|-----|
| OrderService.php | 45% | 90% | 45% |
| PaymentHandler.php | 72% | 90% | 18% |

Run: /acc-generate-test ./src/Application/Service/OrderService.php
```

### 6. Generation Commands Summary

```bash
# Value Objects
acc-create-value-object EmailAddress
acc-create-value-object Money
acc-create-value-object OrderId

# Domain Services
acc-create-domain-service PaymentProcessor
acc-create-domain-service OrderNotifier

# Patterns
/acc-generate-patterns strategy DiscountCalculator
/acc-generate-patterns builder UserProfile

# Tests (run first!)
/acc-generate-test ./src/Application/Service/OrderService.php
```

## Refactoring Modes

### Analysis Only (Default)
```bash
/acc-refactor ./src/Domain/Order
```
Analyzes and provides recommendations without applying changes.

### Focus on Specific Issues
```bash
/acc-refactor ./src -- focus on SOLID violations
/acc-refactor ./src -- extract value objects only
/acc-refactor ./src -- analyze testability
```

### Quick Wins Only
```bash
/acc-refactor ./src -- apply quick wins only
```
Shows only safe, low-risk refactorings.

### With Pattern Generation
```bash
/acc-refactor ./src/Service/PaymentHandler.php -- apply Strategy pattern
```
Analyzes and generates recommended pattern.

## Safety Guidelines

1. **Always commit first** — Create a checkpoint before refactoring
2. **Run tests** — Ensure tests pass before and after
3. **One change at a time** — Don't combine multiple refactorings
4. **Review generated code** — Verify generators output matches context
5. **Incremental approach** — Start with quick wins, then tackle critical

## Usage Examples

```bash
# Full analysis of a file
/acc-refactor ./src/Domain/OrderService.php

# Directory analysis with focus
/acc-refactor ./src/Application -- focus on SOLID violations

# Quick wins only
/acc-refactor ./src -- quick wins only

# Specific pattern extraction
/acc-refactor ./src/Service/Payment -- extract Strategy pattern

# Testability focus
/acc-refactor ./src -- analyze testability, generate test suggestions
```
