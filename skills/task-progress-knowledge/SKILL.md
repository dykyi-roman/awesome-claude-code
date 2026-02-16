---
name: acc-task-progress-knowledge
description: TaskCreate pattern guidelines for progress tracking in coordinator agents
---

# Task Progress Knowledge

Guidelines for using TaskCreate/TaskUpdate tools in coordinator agents to provide user visibility into multi-phase workflows.

## When to Use TaskCreate

Use TaskCreate in **coordinator agents** with **3+ major phases**:

- **Code review coordinators** — multiple review phases
- **Bug fix coordinators** — diagnose → fix → test pipeline
- **Refactoring coordinators** — analyze → plan → generate
- **Architecture auditors** — multi-domain audits
- **CI/CD coordinators** — setup/fix/optimize operations

**Do NOT use** for:
- Single-phase operations
- Simple generators
- Leaf agents (non-coordinators)

## TaskCreate Fields

| Field | Purpose | Example |
|-------|---------|---------|
| `subject` | Brief task title (imperative) | "Diagnose bug" |
| `description` | What happens in this phase | "Analyze code to identify bug category and root cause" |
| `activeForm` | Spinner text (present continuous) | "Diagnosing bug..." |

## Workflow Pattern

```
1. TaskCreate (all phases upfront)
   ├── Phase 1: subject="Analyze changes", activeForm="Analyzing changes..."
   ├── Phase 2: subject="Run reviewers", activeForm="Running reviewers..."
   └── Phase 3: subject="Generate report", activeForm="Generating report..."

2. Execute with status updates:
   For each phase:
   ├── TaskUpdate(taskId, status: in_progress)
   ├── ... execute phase work ...
   └── TaskUpdate(taskId, status: completed)
```

## Examples by Coordinator Type

### Bug Fix Coordinator (3 phases)

```
TaskCreate: subject="Diagnose bug", description="Identify bug category, severity, root cause", activeForm="Diagnosing bug..."
TaskCreate: subject="Generate fix", description="Create minimal, safe fix", activeForm="Generating fix..."
TaskCreate: subject="Create regression test", description="Generate test that catches this bug", activeForm="Creating test..."
```

### Code Review Coordinator (3 phases)

```
TaskCreate: subject="Analyze changes", description="Parse git diff, identify changed files", activeForm="Analyzing changes..."
TaskCreate: subject="Run reviewers", description="Execute specialized reviewers by level", activeForm="Running reviewers..."
TaskCreate: subject="Aggregate report", description="Combine findings, determine verdict", activeForm="Aggregating findings..."
```

### Architecture Auditor (4 phases)

```
TaskCreate: subject="Structural audit", description="DDD, Clean, Hexagonal, SOLID", activeForm="Auditing structure..."
TaskCreate: subject="Behavioral audit", description="CQRS, Event Sourcing, EDA", activeForm="Auditing behavior..."
TaskCreate: subject="Integration audit", description="Outbox, Saga, Stability", activeForm="Auditing integration..."
TaskCreate: subject="Cross-pattern analysis", description="Find conflicts between patterns", activeForm="Analyzing patterns..."
```

### CI Coordinator (3 phases)

```
TaskCreate: subject="Analyze configuration", description="Parse CI config, detect issues", activeForm="Analyzing config..."
TaskCreate: subject="Execute operation", description="Run setup/fix/optimize/audit", activeForm="Executing operation..."
TaskCreate: subject="Validate result", description="Verify changes, run syntax checks", activeForm="Validating result..."
```

### Refactor Coordinator (3 phases)

```
TaskCreate: subject="Analyze code quality", description="Run readability and testability reviewers", activeForm="Analyzing code..."
TaskCreate: subject="Plan refactoring", description="Prioritize issues, map to techniques", activeForm="Planning refactoring..."
TaskCreate: subject="Generate recommendations", description="Create actionable report with commands", activeForm="Generating recommendations..."
```

### DDD Auditor (3 phases)

```
TaskCreate: subject="Analyze layers", description="Check Domain, Application, Infrastructure separation", activeForm="Analyzing layers..."
TaskCreate: subject="Check dependencies", description="Detect violations between layers", activeForm="Checking dependencies..."
TaskCreate: subject="Verify patterns", description="Check DDD patterns compliance", activeForm="Verifying patterns..."
```

### Pattern Auditor (4 phases)

```
TaskCreate: subject="Audit stability patterns", description="Circuit Breaker, Retry, Rate Limiter, Bulkhead", activeForm="Auditing stability..."
TaskCreate: subject="Audit behavioral patterns", description="Strategy, State, Chain, Decorator", activeForm="Auditing behavioral..."
TaskCreate: subject="Audit creational patterns", description="Builder, Object Pool, Factory", activeForm="Auditing creational..."
TaskCreate: subject="Audit integration patterns", description="Outbox, Saga, ADR", activeForm="Auditing integration..."
```

## Best Practices

1. **Create all tasks upfront** — user sees full workflow before execution
2. **Keep phases coarse** — 3-5 major phases, not individual steps
3. **Use clear activeForm** — user sees this in spinner during execution
4. **Always complete tasks** — mark as completed even if phase finds nothing
5. **Don't nest tasks** — only coordinator creates tasks, not delegated agents
6. **Handle failures gracefully** — if phase fails, still mark task completed with error note
