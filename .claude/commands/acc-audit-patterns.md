---
description: Design patterns audit. Analyzes stability (Circuit Breaker, Retry, Rate Limiter, Bulkhead), behavioral (Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento), GoF structural (Adapter, Facade, Proxy, Composite, Bridge, Flyweight), creational (Builder, Factory, Pool), integration (Outbox, Saga, ADR), and SOLID/GRASP compliance.
allowed-tools: Read, Grep, Glob, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# Design Patterns Audit

Perform a comprehensive design patterns audit covering stability, behavioral, creational, and integration patterns with SOLID/GRASP analysis.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-patterns ./src
- /acc-audit-patterns ./src -- focus on stability patterns
- /acc-audit-patterns ./src/Infrastructure -- check Circuit Breaker and Retry
- /acc-audit-patterns ./src -- skip creational, analyze behavioral only
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, focus areas)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — customize audit focus

If meta-instructions provided, adjust audit to:
- Focus on specific pattern categories
- Skip categories if requested
- Analyze specific patterns in depth
- Modify output format

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Instructions

Use the `acc-pattern-auditor` coordinator to perform a comprehensive patterns audit:

```
Task tool with subagent_type="acc-pattern-auditor"
prompt: "Perform design patterns audit on [PATH]. Audit level: [LEVEL]. [META-INSTRUCTIONS if provided]

Use TaskCreate/TaskUpdate for progress visibility. Create tasks for each audit phase.

Analyze the following pattern categories:

1. STABILITY PATTERNS (resilience for external calls)
   - Circuit Breaker: fail-fast for failing services
   - Retry: transient failure handling with backoff
   - Rate Limiter: request throttling
   - Bulkhead: resource isolation

2. BEHAVIORAL PATTERNS (algorithm/behavior encapsulation)
   - Strategy: interchangeable algorithms
   - State: state machine implementations
   - Chain of Responsibility: handler pipelines
   - Decorator: dynamic behavior extension
   - Null Object: null check elimination
   - Template Method: algorithm skeleton with hooks
   - Visitor: operations without class modification
   - Iterator: sequential collection access
   - Memento: state saving/restoration

3. GOF STRUCTURAL PATTERNS (class/object composition)
   - Adapter: incompatible interface integration
   - Facade: simplified subsystem interface
   - Proxy: access control, lazy loading, caching
   - Composite: tree structures, uniform treatment
   - Bridge: abstraction-implementation decoupling
   - Flyweight: memory optimization via sharing

5. CREATIONAL PATTERNS (object creation)
   - Builder: step-by-step construction
   - Object Pool: connection/resource reuse
   - Factory: encapsulated instantiation

4. INTEGRATION PATTERNS (distributed systems)
   - Outbox: transactional message publishing
   - Saga: distributed transaction coordination
   - ADR: Action-Domain-Responder for HTTP

6. SOLID PRINCIPLES
   - SRP, OCP, LSP, ISP, DIP compliance

7. GRASP PRINCIPLES
   - Information Expert, Creator, Controller, etc.

Provide:
- Pattern detection results
- Implementation quality assessment
- Missing pattern opportunities
- SOLID/GRASP violations
- Skill recommendations for fixing issues"
```

## Analysis Scope

### Pattern Categories

| Category | Patterns | Use Cases |
|----------|----------|-----------|
| **Stability** | Circuit Breaker, Retry, Rate Limiter, Bulkhead | External APIs, microservices |
| **Behavioral** | Strategy, State, Chain, Decorator, Null Object, Template Method, Visitor, Iterator, Memento | Business logic encapsulation |
| **GoF Structural** | Adapter, Facade, Proxy, Composite, Bridge, Flyweight | Interface compatibility, composition |
| **Creational** | Builder, Object Pool, Factory | Complex object construction |
| **Integration** | Outbox, Saga, ADR | Distributed systems, HTTP |

### Detection Indicators

```php
// Missing Circuit Breaker (Critical)
$response = $httpClient->request('GET', $externalUrl); // No failure protection

// Strategy Candidate (Major)
switch ($paymentType) {
    case 'card': return $this->processCard($payment);
    case 'paypal': return $this->processPaypal($payment);
    // Switch statement = Strategy pattern candidate
}

// Builder Candidate (Minor)
public function __construct(
    $a, $b, $c, $d, $e, $f, $g, $h // 8+ parameters = Builder candidate
) { ... }

// Missing Outbox (Critical for microservices)
$this->entityManager->persist($order);
$this->entityManager->flush();
$this->messageBus->dispatch(new OrderCreated($order)); // Not atomic!
```

## Expected Output

A structured markdown report containing:

### 1. Executive Summary

| Category | Patterns Checked | Issues Found | Compliance |
|----------|-----------------|--------------|------------|
| Stability | 4 | 3 | 60% |
| Behavioral | 9 | 2 | 85% |
| GoF Structural | 6 | 3 | 75% |
| Creational | 3 | 1 | 90% |
| Integration | 3 | 4 | 70% |
| SOLID | 5 | 2 | 80% |
| GRASP | 5 | 1 | 95% |

**Overall Compliance: XX%**

### 2. Stability Patterns Analysis

| Pattern | Found | Status | Issues |
|---------|-------|--------|--------|
| Circuit Breaker | ❌ | Missing | 3 unprotected external calls |
| Retry | ⚠️ | Partial | No jitter in backoff |
| Rate Limiter | ✅ | Good | Properly configured |
| Bulkhead | ❌ | Missing | No resource isolation |

### 3. Behavioral Patterns Analysis

| Pattern | Found | Status | Issues |
|---------|-------|--------|--------|
| Strategy | ⚠️ | Candidate | 2 type switches found |
| State | ✅ | Good | Proper FSM in Order |
| Chain of Responsibility | ⚠️ | Partial | Missing interface |
| Decorator | ✅ | Good | Logger decorators |
| Null Object | ❌ | Missing | 15 null checks |

### 4. GoF Structural Patterns Analysis

| Pattern | Found | Status | Issues |
|---------|-------|--------|--------|
| Adapter | ❌ | Missing | 3 direct SDK usages in Domain |
| Facade | ✅ | Good | Proper subsystem hiding |
| Proxy | ❌ | Missing | Heavy initialization not lazy |
| Composite | ⚠️ | Candidate | Recursive structures found |
| Bridge | ❌ | Missing | Class explosion detected |
| Flyweight | ❌ | Missing | Repeated immutable objects |

### 5. Creational Patterns Analysis

| Pattern | Found | Status | Issues |
|---------|-------|--------|--------|
| Builder | ⚠️ | Needed | 3 classes with 8+ params |
| Object Pool | ❌ | Missing | DB connections not pooled |
| Factory | ✅ | Good | Domain factories present |

### 6. Integration Patterns Analysis

| Pattern | Found | Status | Issues |
|---------|-------|--------|--------|
| Outbox | ❌ | Missing | Direct message dispatch |
| Saga | ❌ | Missing | Distributed tx needed |
| ADR | ⚠️ | Partial | Fat controllers |

### 7. SOLID/GRASP Compliance

#### SOLID Violations
| Principle | Score | Issues |
|-----------|-------|--------|
| SRP | 70% | 5 god classes |
| OCP | 85% | 3 type switches |
| LSP | 95% | 1 violation |
| ISP | 80% | 2 fat interfaces |
| DIP | 75% | 8 concrete deps |

#### GRASP Violations
| Principle | Score | Issues |
|-----------|-------|--------|
| Information Expert | 90% | 2 violations |
| Creator | 85% | 3 violations |
| Controller | 95% | 1 violation |

### 8. Pattern Recommendations

| Gap Identified | Location | Pattern Needed | Generation Skill |
|----------------|----------|----------------|------------------|
| Unprotected API | `ApiClient.php:45` | Circuit Breaker | `/acc-generate-patterns circuit-breaker ApiClient` |
| Type switch | `PaymentHandler.php:34` | Strategy | `/acc-generate-patterns strategy Payment` |
| 8 constructor params | `User.php:15` | Builder | `/acc-generate-patterns builder User` |
| Direct publishing | `OrderService.php:120` | Outbox | `/acc-generate-patterns outbox Order` |

### 9. Priority Actions

1. **Critical** — Add Circuit Breaker to external API calls
2. **Critical** — Implement Outbox pattern for message consistency
3. **Warning** — Refactor type switches to Strategy pattern
4. **Warning** — Add Builder for complex object construction

## Audit Levels

Extract audit level from meta-instructions: `level:quick`, `level:standard`, `level:deep`. Default: `standard`.

| Level | Scope | What's Checked |
|-------|-------|----------------|
| `quick` | Pattern detection | Detect used patterns, basic compliance check |
| `standard` | Compliance matrix | Full pattern analysis, compliance scoring, implementation quality |
| `deep` | Standard + opportunities | Standard + opportunity detection, cross-pattern conflicts, SOLID/GRASP |

## Severity Levels

| Level | Symbol | Criteria |
|-------|--------|----------|
| Critical | 🔴 | Missing resilience patterns for external calls, non-atomic transactions |
| High | 🟠 | Broken pattern implementation, missing error handling in patterns |
| Medium | 🟡 | Suboptimal pattern usage, candidate patterns not implemented |
| Low | 🟢 | Style improvements, optional pattern suggestions |

## Meta-Instructions Guide

| Instruction | Effect |
|-------------|--------|
| `focus on stability` | Deep stability patterns analysis |
| `focus on behavioral` | Prioritize behavioral patterns |
| `skip creational` | Exclude creational patterns |
| `stability only` | Only stability pattern audit |
| `level:quick` | Fast audit (pattern detection only) |
| `level:deep` | Deep audit (+ opportunity detection + SOLID/GRASP) |
| `detailed report` | Maximum detail in report |
| `на русском` | Report in Russian |

## Usage Examples

```bash
/acc-audit-patterns ./src
/acc-audit-patterns ./src/Infrastructure -- focus on stability patterns
/acc-audit-patterns ./src/Domain -- check behavioral patterns only
/acc-audit-patterns ./src -- level:deep
/acc-audit-patterns ./src -- level:quick
```
