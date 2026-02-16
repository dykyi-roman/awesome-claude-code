---
name: acc-detect-architecture-pattern
description: Detects architectural patterns (MVC, DDD, Hexagonal, CQRS, Layered, Event Sourcing, Microservice) from namespace structure, interface placement, and dependency direction. Outputs confidence score per pattern.
---

# Architecture Pattern Detector

## Overview

Analyzes a PHP codebase to detect which architectural patterns are in use. Examines namespace structure, interface placement, dependency direction, and code organization to determine patterns with confidence scores.

## Detectable Patterns

| Pattern | Key Indicators | Confidence Markers |
|---------|---------------|-------------------|
| MVC | Controllers + Models + Views | Framework routing, template engine |
| DDD | Domain layer with Entities/VOs/Aggregates | Repository interfaces in Domain |
| Hexagonal | Ports (interfaces) + Adapters | Inbound/outbound port separation |
| CQRS | Separate Command/Query models | CommandBus, QueryBus, separate handlers |
| Layered | Domain/Application/Infrastructure | Clear namespace separation |
| Event Sourcing | Event store, aggregate replay | EventStore, AggregateRoot::apply() |
| Clean Architecture | Use Cases + Entity + Gateway | Dependency inversion at boundaries |
| Microservice | Independent deployable | Own database, API gateway, docker |

## Detection Algorithms

### MVC Detection

```bash
# Controllers
Grep: "class.*Controller" --glob "**/*.php"
Grep: "extends.*Controller" --glob "**/*.php"

# Models (Eloquent/Doctrine entities)
Grep: "extends Model|#\\[ORM\\\\Entity" --glob "**/*.php"

# Views/Templates
Glob: "**/*.twig"
Glob: "**/*.blade.php"
Glob: "resources/views/**"
Glob: "templates/**"
```

**Confidence scoring:**
- Controllers found: +30
- Models found: +30
- Views/templates found: +20
- Framework routing: +20

### DDD Detection

```bash
# Domain entities
Grep: "namespace.*\\\\Domain\\\\.*\\\\Entity" --glob "**/*.php"
Grep: "namespace.*\\\\Domain\\\\.*\\\\Model" --glob "**/*.php"

# Value Objects
Grep: "class.*ValueObject|ValueObject|readonly.*class" --glob "**/Domain/**/*.php"
Glob: "**/ValueObject/**/*.php"
Glob: "**/Domain/**/ValueObject/*.php"

# Aggregates
Grep: "AggregateRoot|Aggregate" --glob "**/Domain/**/*.php"

# Domain Events
Grep: "DomainEvent|extends.*Event" --glob "**/Domain/**/*.php"
Glob: "**/Domain/**/Event/*.php"

# Repository interfaces in Domain
Grep: "interface.*Repository" --glob "**/Domain/**/*.php"

# Domain Services
Glob: "**/Domain/**/Service/*.php"
```

**Confidence scoring:**
- Domain namespace exists: +15
- Entities in Domain: +15
- Value Objects found: +15
- Repository interfaces in Domain: +20
- Aggregates found: +15
- Domain Events found: +10
- Domain Services found: +10

### Hexagonal Detection

```bash
# Port interfaces
Grep: "namespace.*\\\\Port\\\\" --glob "**/*.php"
Grep: "namespace.*\\\\Ports\\\\" --glob "**/*.php"
Glob: "**/Port/**/*.php"

# Adapter implementations
Grep: "namespace.*\\\\Adapter\\\\" --glob "**/*.php"
Glob: "**/Adapter/**/*.php"

# Inbound/Outbound separation
Glob: "**/Port/Inbound/**"
Glob: "**/Port/Outbound/**"
Glob: "**/Port/In/**"
Glob: "**/Port/Out/**"

# Use case interfaces (driving ports)
Grep: "interface.*UseCase|interface.*Port" --glob "**/*.php"
```

**Confidence scoring:**
- Port namespace exists: +30
- Adapter namespace exists: +25
- Inbound/Outbound separation: +25
- Use case interfaces: +20

### CQRS Detection

```bash
# Command/Query separation
Glob: "**/Command/**/*.php"
Glob: "**/Query/**/*.php"

# Command handlers
Grep: "CommandHandler|implements.*CommandHandler" --glob "**/*.php"
Grep: "#\\[AsMessageHandler\\]" --glob "**/Command/**/*.php"

# Query handlers
Grep: "QueryHandler|implements.*QueryHandler" --glob "**/*.php"

# Command/Query bus
Grep: "CommandBus|QueryBus|MessageBus" --glob "**/*.php"

# Separate read models
Grep: "ReadModel|Projection|View" --glob "**/*.php"
Glob: "**/ReadModel/**/*.php"
Glob: "**/Projection/**/*.php"
```

**Confidence scoring:**
- Command namespace: +20
- Query namespace: +20
- Command handlers: +15
- Query handlers: +15
- Bus implementation: +15
- Read models: +15

### Event Sourcing Detection

```bash
# Event store
Grep: "EventStore|EventStream" --glob "**/*.php"

# Aggregate with apply/record
Grep: "->apply\(|->recordThat\(|->record\(" --glob "**/*.php"
Grep: "function apply.*Event" --glob "**/*.php"

# Event replay
Grep: "reconstitute|reconstruct|replay" --glob "**/*.php"

# Projections
Grep: "Projector|Projection|ReadModelProjector" --glob "**/*.php"
Glob: "**/Projection/**/*.php"

# Snapshots
Grep: "Snapshot|SnapshotStore" --glob "**/*.php"
```

**Confidence scoring:**
- EventStore found: +30
- Aggregate apply pattern: +25
- Reconstitute/replay: +20
- Projections: +15
- Snapshots: +10

### Layered Architecture Detection

```bash
# Standard layers
Glob: "src/Domain/"
Glob: "src/Application/"
Glob: "src/Infrastructure/"
Glob: "src/Presentation/"

# Alternative naming
Glob: "src/Core/"
Glob: "src/Service/"
Glob: "src/Repository/"

# Namespace analysis
Grep: "namespace.*\\\\Domain\\\\" --glob "**/*.php"
Grep: "namespace.*\\\\Application\\\\" --glob "**/*.php"
Grep: "namespace.*\\\\Infrastructure\\\\" --glob "**/*.php"
```

**Confidence scoring:**
- 4 distinct layers: +40
- 3 distinct layers: +25
- 2 distinct layers: +15
- Proper namespace separation: +30
- No cross-layer imports: +30

### Dependency Direction Analysis

```bash
# Check for violations (Infrastructure → Domain is OK, Domain → Infrastructure is NOT)
# Domain should not import from Infrastructure
Grep: "use.*\\\\Infrastructure\\\\" --glob "**/Domain/**/*.php"

# Domain should not import from Application
Grep: "use.*\\\\Application\\\\" --glob "**/Domain/**/*.php"

# Application should not import from Presentation
Grep: "use.*\\\\(Controller|Action|Console)\\\\" --glob "**/Application/**/*.php"

# Infrastructure should implement Domain interfaces
Grep: "implements.*\\\\Domain\\\\" --glob "**/Infrastructure/**/*.php"
```

## Output Format

```markdown
## Architecture Pattern Analysis

### Detected Patterns

| Pattern | Confidence | Evidence |
|---------|-----------|----------|
| DDD | 85% | Domain layer, VOs, Aggregates, Repository interfaces |
| CQRS | 70% | Command/Query separation, handlers, bus |
| Layered | 90% | 4 layers with proper namespace separation |
| Hexagonal | 40% | Partial port/adapter separation |
| Event Sourcing | 0% | No event store or replay patterns found |

### Primary Pattern: DDD + Layered Architecture
The codebase follows Domain-Driven Design within a Layered Architecture.

### Dependency Direction
```
Presentation → Application → Domain ← Infrastructure
     ✓              ✓           ✓ (no violations)
```

### Violations Found
| From | To | File | Import |
|------|----|------|--------|
| Domain | Infrastructure | Order.php:5 | use App\Infrastructure\... |

### Pattern Maturity Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Layer separation | Strong | Clear namespace boundaries |
| Domain purity | Good | 2 minor violations |
| CQRS completeness | Partial | Commands done, queries mixed |
| Interface segregation | Good | Ports defined in Domain |
```

## Confidence Scale

| Score | Level | Description |
|-------|-------|-------------|
| 80-100% | Strong | Pattern is clearly and consistently applied |
| 60-79% | Moderate | Pattern is present with some inconsistencies |
| 40-59% | Partial | Pattern is partially applied or emerging |
| 20-39% | Weak | Some elements present but not systematic |
| 0-19% | Absent | Pattern not detected |

## Integration

This skill is used by:
- `acc-codebase-navigator` — determines overall architecture approach
- `acc-explain-coordinator` — decides which analysis agents to invoke
- `acc-structural-auditor` — provides pattern context for audit
