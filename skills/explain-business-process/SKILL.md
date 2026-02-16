---
name: acc-explain-business-process
description: Identifies business workflows with actors, steps, preconditions, and outcomes. Translates method chains into natural language business processes like "When customer places order, system validates inventory..."
---

# Business Process Explainer

## Overview

Identifies and documents business processes implemented in code. Translates technical method chains, event flows, and service orchestrations into natural language descriptions with actors, steps, preconditions, and outcomes.

## Process Detection

### Use Case / Command Handler Analysis

```bash
# Find use cases and command handlers (primary business operations)
Grep: "class.*UseCase|class.*Handler" --glob "**/Application/**/*.php"
Grep: "function (execute|handle|__invoke)" --glob "**/Application/**/*.php"

# Read the handler to trace the full process
# Each handler method = one business process
```

### Service Orchestration

```bash
# Application services that orchestrate domain operations
Grep: "class.*Service" --glob "**/Application/**/*.php"
Grep: "function (create|update|delete|process|execute|handle)" --glob "**/Application/**/*.php"

# Domain services with business logic
Grep: "class.*Service" --glob "**/Domain/**/*.php"
```

### Event-Driven Processes

```bash
# Events that trigger subsequent processes
Grep: "class.*Event" --glob "**/Domain/**/*.php"
Grep: "dispatch|publish|raise|record" --glob "**/*.php"

# Event handlers (reaction to events)
Grep: "#\\[AsMessageHandler\\]|implements.*Handler" --glob "**/*.php"
Grep: "function.*handle.*Event" --glob "**/*.php"
```

## Analysis Process

### Step 1: Identify the Process

For each Use Case / Command Handler:

1. **Read the handler** — understand the sequence of operations
2. **Identify the actor** — who initiates this process (User, Admin, System, Scheduler)
3. **Identify preconditions** — what must be true before the process starts
4. **Trace the steps** — follow method calls through the layers
5. **Identify outcomes** — what changes after the process completes
6. **Find side effects** — events dispatched, notifications sent, logs written

### Step 2: Trace Method Chains

```
Handler::handle(Command)
  → Repository::find(id)           // Load data
  → Entity::performAction(args)    // Domain logic
  → Repository::save(entity)       // Persist changes
  → EventBus::dispatch(event)      // Side effects
```

Translate to:

> "When **[actor]** performs **[action]**, the system **[step 1]**, then **[step 2]**, and finally **[step 3]**."

### Step 3: Map to Business Language

| Technical Term | Business Term |
|---------------|---------------|
| `CreateOrderHandler` | "Place an order" |
| `Repository::find()` | "Look up the [entity]" |
| `Entity::validate()` | "Verify that [conditions]" |
| `Repository::save()` | "Record the [entity]" |
| `EventBus::dispatch()` | "Notify relevant parties" |
| `throw InvalidArgumentException` | "Reject if [condition]" |
| `Transaction::begin/commit` | "Ensure all-or-nothing" |

## Process Documentation Template

For each identified process:

```markdown
### Process: [Business Name]

**Trigger:** [What starts this process]
**Actor:** [Who initiates — Customer, Admin, System, Scheduler]
**Preconditions:**
- [What must be true before starting]
- [Required state/permissions]

**Steps:**
1. **[Actor]** [initiates action] (e.g., "submits order form")
2. **System** [validates/checks] (e.g., "validates order data")
3. **System** [performs domain logic] (e.g., "calculates total with discounts")
4. **System** [persists changes] (e.g., "saves the new order")
5. **System** [triggers side effects] (e.g., "sends confirmation email")

**Outcomes:**
- **Success:** [What happens on success]
- **Failure:** [What happens on failure — specific error scenarios]

**Side Effects:**
- [Events dispatched]
- [Notifications sent]
- [External systems called]

**Business Rules Applied:**
- [Rule references from acc-extract-business-rules]
```

## Output Format

```markdown
## Business Processes

### Overview

| # | Process | Actor | Trigger | Domain |
|---|---------|-------|---------|--------|
| 1 | Place Order | Customer | Submit order form | Order |
| 2 | Process Payment | System | Order confirmed | Payment |
| 3 | Ship Order | Warehouse | Payment received | Shipping |
| 4 | Cancel Order | Customer/Admin | User request | Order |

### Process 1: Place Order

**Trigger:** Customer submits order through API or web form
**Actor:** Customer (authenticated)

**Preconditions:**
- Customer is authenticated
- Shopping cart is not empty
- All items are in stock

**Steps:**
1. **Customer** submits order with items and delivery address
2. **System** validates order data (items exist, quantities available)
3. **System** checks customer's eligibility (account active, no blocks)
4. **System** calculates total price including taxes and shipping
5. **System** applies available discounts (loyalty, promotional)
6. **System** reserves inventory for ordered items
7. **System** creates the order record with "pending" status
8. **System** initiates payment process

**Outcomes:**
- **Success:** Order created with status "pending", confirmation sent
- **Failure (validation):** Error returned with specific field errors
- **Failure (stock):** "Items out of stock" with affected items listed
- **Failure (payment):** Order created but marked "payment_failed"

**Side Effects:**
- OrderCreated event → triggers confirmation email
- OrderCreated event → triggers inventory reservation
- OrderCreated event → triggers analytics tracking

**Business Rules:**
- INV-1: Order amount must be positive
- INV-2: Order must have at least one item
- POL-1: Free shipping for orders over $100

### Process Interaction Map

```
[Place Order] ──triggers──→ [Process Payment]
                               │
                    success ←──┘──→ failure
                       │              │
                       v              v
               [Ship Order]    [Cancel Order]
                    │
                    v
             [Deliver Order]
```
```

## Process Complexity Indicators

| Indicator | Simple | Medium | Complex |
|-----------|--------|--------|---------|
| Steps | 1-3 | 4-7 | 8+ |
| Actors | 1 | 2 | 3+ |
| Branches | 0-1 | 2-3 | 4+ |
| Side effects | 0-1 | 2-3 | 4+ |
| Domain events | 0 | 1-2 | 3+ |

## Integration

This skill is used by:
- `acc-business-logic-analyst` — documents all business processes
- `acc-extract-business-rules` — references rules in processes
- `acc-trace-request-lifecycle` — technical trace for each process
