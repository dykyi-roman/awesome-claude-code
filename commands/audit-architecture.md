---
description: Comprehensive architecture audit with pattern recommendations. Detects DDD, CQRS, Clean/Hexagonal/Layered Architecture, Event Sourcing, EDA, Outbox, Saga, Stability, GoF Structural (Adapter, Facade, Proxy, Composite, Bridge, Flyweight), and Behavioral (Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento) patterns. Provides actionable recommendations with links to generation skills.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path> [level] [-- meta-instructions]
---

# Architecture Audit Command

Perform a comprehensive architecture audit with actionable pattern recommendations.

## Input Parsing

Parse `$ARGUMENTS` to extract path, level, and optional meta-instructions:

```
Format: <path> [level] [-- <meta-instructions>]

Arguments:
- path: Target directory or file (required, default: current directory)
- level: Audit depth - quick|standard|deep (optional, default: standard)
- -- meta-instructions: Additional focus areas or filters (optional)

Examples:
- /acc-audit-architecture ./src
- /acc-audit-architecture ./src deep
- /acc-audit-architecture ./src quick
- /acc-audit-architecture ./src -- focus on CQRS and Event Sourcing
- /acc-audit-architecture ./src deep -- only structural audit (DDD, Clean, SOLID)
- /acc-audit-architecture ./src -- level:deep (backward compatible)
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = positional arguments, Second part = meta-instructions
3. In positional arguments, check if last word is a valid level (`quick|standard|deep`)
4. If level found → extract it; remaining = path
5. Also accept `level:quick|standard|deep` in meta-instructions (backward compatibility)
6. Priority: positional > meta-instruction > default (`standard`)
7. Default path: current directory (if empty)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — use to customize audit scope

If meta-instructions provided, adjust audit to:
- Focus on specific patterns/auditors mentioned
- Skip certain auditors if requested (structural/behavioral/integration)
- Apply additional checks
- Modify report format if requested

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Instructions

Execute a two-phase audit using specialized agents:

### Phase 1: Architecture Audit

Level is an optional positional parameter. Default: `standard`.

Use the `acc-architecture-auditor` agent (with audit level and progress tracking) to analyze:
- DDD (Domain-Driven Design)
- CQRS (Command Query Responsibility Segregation)
- Clean Architecture
- Event Sourcing
- Hexagonal Architecture
- Layered Architecture
- Event-Driven Architecture
- Outbox Pattern
- Saga Pattern

### Phase 2: Design Patterns Audit

Pass to each agent: `"Audit level: [LEVEL]. Use TaskCreate/TaskUpdate for progress visibility."`

Use the `acc-pattern-auditor` agent to analyze:
- Stability Patterns (Circuit Breaker, Retry, Rate Limiter, Bulkhead)
- Behavioral Patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento)
- GoF Structural Patterns (Adapter, Facade, Proxy, Composite, Bridge, Flyweight)
- Creational Patterns (Builder, Object Pool)
- Enterprise Patterns (Read Model, Policy)

### Phase 3: Generate Recommendations

Based on detected issues, map problems to solutions:

| Issue Type | Pattern | Generation Skill |
|------------|---------|------------------|
| External API failures | Circuit Breaker | `acc-create-circuit-breaker` |
| Transient errors | Retry | `acc-create-retry-pattern` |
| API rate limits | Rate Limiter | `acc-create-rate-limiter` |
| Resource exhaustion | Bulkhead | `acc-create-bulkhead` |
| Message loss risk | Outbox | `acc-create-outbox-pattern` |
| Distributed transactions | Saga | `acc-create-saga-pattern` |
| Primitive obsession | Value Object | `acc-create-value-object` |
| Anemic entities | Entity | `acc-create-entity` |
| Missing invariants | Aggregate | `acc-create-aggregate` |
| Complex creation | Factory | `acc-create-factory` |
| Complex queries | Specification | `acc-create-specification` |
| Cross-layer data | DTO | `acc-create-dto` |
| External systems | Anti-Corruption Layer | `acc-create-anti-corruption-layer` |
| Algorithm switching | Strategy | `acc-create-strategy` |
| State transitions | State | `acc-create-state` |
| Request pipelines | Chain of Responsibility | `acc-create-chain-of-responsibility` |
| Dynamic behavior | Decorator | `acc-create-decorator` |
| Null checks | Null Object | `acc-create-null-object` |
| Algorithm skeleton | Template Method | `acc-create-template-method` |
| Operations on structure | Visitor | `acc-create-visitor` |
| Collection traversal | Iterator | `acc-create-iterator` |
| Undo/redo, snapshots | Memento | `acc-create-memento` |
| Interface incompatibility | Adapter | `acc-create-adapter` |
| Complex subsystem access | Facade | `acc-create-facade` |
| Lazy loading, caching | Proxy | `acc-create-proxy` |
| Tree structures | Composite | `acc-create-composite` |
| Class explosion | Bridge | `acc-create-bridge` |
| Repeated immutable objects | Flyweight | `acc-create-flyweight` |
| Complex construction | Builder | `acc-create-builder` |
| Expensive resources | Object Pool | `acc-create-object-pool` |
| Query optimization | Read Model | `acc-create-read-model` |
| Authorization rules | Policy | `acc-create-policy` |

## Expected Output

A structured markdown report containing:

### 1. Executive Summary
- Overall architecture health score
- Detected patterns overview
- Critical issues count

### 2. Pattern Detection Matrix
| Pattern | Detected | Compliance | Status |
|---------|----------|------------|--------|

### 3. Critical Issues
Issues requiring immediate attention with:
- File locations
- Code snippets
- Severity level
- Fix recommendations

### 4. Warnings
Best practice violations with improvement suggestions.

### 5. Cross-Pattern Analysis
Conflicts between architectural patterns.

### 6. Pattern Recommendations

**Actionable recommendations linking issues to solutions:**

#### Resilience Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| [Specific issue] | Circuit Breaker | Run `/acc-create-circuit-breaker` |

#### Integration Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| [Specific issue] | Outbox Pattern | Run `/acc-create-outbox-pattern` |

#### DDD Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| [Specific issue] | Value Object | Run `/acc-create-value-object` |

### 7. Prioritized Action Items
1. **Critical:** [Action with skill reference]
2. **High:** [Action with skill reference]
3. **Medium:** [Action with skill reference]

## Audit Levels

Level is an optional positional parameter. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Layer detection | Architecture type detection, basic layer compliance |
| `standard` | Full pattern analysis | All architecture + design patterns, compliance matrix |
| `deep` | Standard + cross-analysis | Standard + cross-pattern conflicts, opportunity detection, SOLID/GRASP |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Domain → Infrastructure dependency, framework leakage into Domain |
| High | 🟠 | Missing resilience patterns, unprotected external calls, anemic models |
| Medium | 🟡 | Suboptimal pattern usage, missing opportunities |
| Low | 🟢 | Style improvements, optional pattern suggestions |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on CQRS` | Deep CQRS/Event Sourcing analysis |
| `focus on stability` | Prioritize stability patterns |
| `structural only` | Only DDD/Clean/Hexagonal audit |
| `skip behavioral` | Exclude behavioral patterns |
| `level:quick` | Quick audit (same as positional `quick`) |
| `level:standard` | Standard audit (same as positional `standard`) |
| `level:deep` | Deep audit (same as positional `deep`) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

## Usage Examples

```bash
/acc-audit-architecture ./src
/acc-audit-architecture ./src quick
/acc-audit-architecture ./src deep
/acc-audit-architecture ./src -- focus on CQRS and Event Sourcing
/acc-audit-architecture ./src deep -- only structural audit
/acc-audit-architecture ./src -- level:deep
```

