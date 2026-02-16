---
name: acc-extract-state-machine
description: Detects state machines from enums, status fields, switch/match statements, and transition methods. Extracts states, transitions, guards, and actions to build state diagram data.
---

# State Machine Extractor

## Overview

Identifies implicit and explicit state machines in code — status fields, enum-based states, transition methods, guard conditions, and actions. Produces structured state diagram data for visualization.

## Detection Patterns

### Enum-Based States

```bash
# Status/State enums
Grep: "enum.*(Status|State)" --glob "**/*.php"

# Backed enum cases
Grep: "case [A-Z]" --glob "**/*.php" -A 0
# Read full enum to get all cases

# Enum with methods (transition logic)
Grep: "function (canTransitionTo|allowedTransitions|next)" --glob "**/*.php"
```

### Status Fields

```bash
# Status properties
Grep: "private.*\\$status|readonly.*Status|private.*Status \\$" --glob "**/*.php"

# Status setters/changers
Grep: "function (setStatus|changeStatus|updateStatus|transitionTo)" --glob "**/*.php"

# Status constants (legacy pattern)
Grep: "const STATUS_|const STATE_" --glob "**/*.php"
```

### Transition Methods

```bash
# Named transition methods (domain verbs)
Grep: "function (activate|deactivate|approve|reject|cancel|complete|suspend|resume|archive|publish|draft|submit|confirm|expire|close|open|block|unblock|verify|process|ship|deliver|refund|pay)" --glob "**/Domain/**/*.php"

# Status check before transition (guard)
Grep: "if.*status.*!==|if.*status.*===|match.*status" --glob "**/*.php"

# Transition with event recording
Grep: "->(recordEvent|raise|apply).*new.*Event" --glob "**/*.php"
```

### Switch/Match State Logic

```bash
# Match expression on status
Grep: "match.*\\(.*status|match.*\\(.*state|match.*\\(.*->getStatus" --glob "**/*.php"

# Switch on status
Grep: "switch.*\\(.*status|switch.*\\(.*state" --glob "**/*.php"

# State-dependent behavior
Grep: "case.*Status::|case.*State::" --glob "**/*.php"
```

### Symfony Workflow Component

```bash
# Workflow configuration
Glob: "config/packages/workflow.yaml"
Glob: "config/packages/workflow.php"

# Workflow service usage
Grep: "WorkflowInterface|Workflow::" --glob "**/*.php"
Grep: "->can\\(|->apply\\(|->getMarking" --glob "**/*.php"
```

## Analysis Process

### Step 1: Find State Holders

For each entity/aggregate with a status field:

1. **Read the enum/status definition** — get all possible states
2. **Find transition methods** — methods that change the status
3. **Extract guards** — conditions checked before transition
4. **Extract actions** — what happens during/after transition
5. **Find events** — events raised on transition

### Step 2: Build Transition Table

For each transition method found:

```
Read the method body:
1. What is the source state? (guard/precondition)
2. What is the target state? (assignment/return)
3. What conditions must be met? (if/match checks)
4. What side effects occur? (events, notifications)
```

### Step 3: Validate Completeness

- Can every state be reached from the initial state?
- Are there dead-end states (no outgoing transitions)?
- Are there unreachable states?
- Are all transitions guarded?

## Output Format

```markdown
## State Machines

### Summary

| Entity | States | Transitions | Has Guards | Events |
|--------|--------|-------------|-----------|--------|
| Order | 6 | 8 | Yes | 5 |
| Payment | 4 | 5 | Yes | 3 |
| User | 3 | 4 | Partial | 2 |

### Order State Machine

#### States

| State | Description | Terminal |
|-------|-------------|---------|
| `draft` | Order created but not submitted | No |
| `pending` | Submitted, awaiting payment | No |
| `confirmed` | Payment received | No |
| `shipped` | Items dispatched | No |
| `delivered` | Items received by customer | Yes |
| `cancelled` | Order cancelled | Yes |

#### Transitions

| # | From | To | Method | Guard | Action |
|---|------|----|--------|-------|--------|
| 1 | draft | pending | submit() | Has items | Validate totals |
| 2 | pending | confirmed | confirm() | Payment OK | Record payment |
| 3 | confirmed | shipped | ship() | Items packed | Send tracking |
| 4 | shipped | delivered | deliver() | Tracking confirms | Close order |
| 5 | draft | cancelled | cancel() | - | Release items |
| 6 | pending | cancelled | cancel() | - | Refund if paid |
| 7 | confirmed | cancelled | cancel() | Not shipped | Refund payment |

#### State Diagram Data (Mermaid-ready)

```
stateDiagram-v2
    [*] --> draft
    draft --> pending : submit()
    draft --> cancelled : cancel()
    pending --> confirmed : confirm()
    pending --> cancelled : cancel()
    confirmed --> shipped : ship()
    confirmed --> cancelled : cancel()
    shipped --> delivered : deliver()
    delivered --> [*]
    cancelled --> [*]
```

#### Guards Detail

| Transition | Guard Condition | Error on Failure |
|-----------|-----------------|-----------------|
| submit() | Order has at least 1 item | "Cannot submit empty order" |
| confirm() | Payment amount matches total | "Payment mismatch" |
| ship() | All items available in warehouse | "Items not available" |
| cancel() | Status is not shipped/delivered | "Cannot cancel shipped order" |

#### Events Raised

| Transition | Event | Listeners |
|-----------|-------|-----------|
| submit() | OrderSubmitted | InventoryReserve, NotifyAdmin |
| confirm() | OrderConfirmed | SendConfirmation, StartPacking |
| ship() | OrderShipped | SendTracking, NotifyCustomer |
| deliver() | OrderDelivered | RequestReview, CloseTicket |
| cancel() | OrderCancelled | ReleaseInventory, RefundPayment |
```

## State Machine Quality Indicators

| Indicator | Good | Warning | Critical |
|-----------|------|---------|----------|
| All transitions guarded | Yes | Partial | No guards |
| No dead-end states | No dead ends | With purpose (terminal) | Unreachable |
| Events on transitions | All important | Some | None |
| Explicit state enum | Yes | Constants | String literals |
| Transition methods named | Domain verbs | Generic setStatus | Direct field set |

## Common Anti-Patterns

| Anti-Pattern | Detection | Issue |
|-------------|-----------|-------|
| String-based status | `$status = 'pending'` | No type safety |
| Direct field mutation | `$this->status = 'new'` | No guard enforcement |
| Missing transitions | State reachable only via DB | Bypasses domain logic |
| God transition | One method handles all transitions | No guard per transition |

## Integration

This skill is used by:
- `acc-business-logic-analyst` — documents state machines in domain
- `acc-diagram-designer` — generates state diagrams from extracted data
- `acc-explain-business-process` — references state transitions in workflows
