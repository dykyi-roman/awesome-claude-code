---
description: Comprehensive architecture audit with pattern recommendations. Detects DDD, CQRS, Clean/Hexagonal/Layered Architecture, Event Sourcing, EDA, Outbox, Saga, and Stability patterns. Provides actionable recommendations with links to generation skills.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path-to-php-project>
---

# Architecture Audit Command

Perform a comprehensive architecture audit with actionable pattern recommendations.

## Target

Analyze the project at: `$ARGUMENTS`

If no path provided, analyze the current working directory.

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

Use the `acc-architecture-auditor` agent to analyze:
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

Use the `acc-pattern-auditor` agent to analyze:
- Stability Patterns (Circuit Breaker, Retry, Rate Limiter, Bulkhead)
- Behavioral Patterns (Strategy, State, Chain of Responsibility, Decorator, Null Object)
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

## Usage Examples

```bash
/acc-architecture-audit
/acc-architecture-audit src/
/acc-architecture-audit /path/to/project
```

