---
description: DDD architecture audit with pattern recommendations. Analyzes layer separation, domain model richness, and architectural violations. Provides actionable recommendations with links to generation skills.
allowed-tools: Read, Grep, Glob, Bash, Task
model: opus
argument-hint: <path> [-- additional instructions]
---

# DDD Architecture Audit

Perform a comprehensive DDD architecture audit with actionable pattern recommendations.

## Input Parsing

Parse `$ARGUMENTS` to extract path and optional meta-instructions:

```
Format: <path> [-- <meta-instructions>]

Examples:
- /acc-audit-ddd ./src
- /acc-audit-ddd ./src -- focus on Order bounded context
- /acc-audit-ddd ./src -- skip Infrastructure, check aggregates only
- /acc-audit-ddd ./src -- особое внимание на Event Sourcing паттерны
```

**Parsing rules:**
1. Split `$ARGUMENTS` by ` -- ` (space-dash-dash-space)
2. First part = **path** (required, default: current directory)
3. Second part = **meta-instructions** (optional, additional focus/filters)

## Target

- **Path**: First part of `$ARGUMENTS` (before `--`)
- **Meta-instructions**: Second part (after `--`) — use to customize audit focus

If meta-instructions provided, adjust audit to:
- Focus on specific areas mentioned
- Skip areas if requested
- Apply additional checks
- Modify output format if requested

## Pre-flight Check

1. Verify the path exists:
   - If `$ARGUMENTS` is empty, ask user for the project path
   - If path doesn't exist, report error and stop

2. Verify it's a PHP project:
   - Check for `composer.json` or `*.php` files
   - If not a PHP project, report and stop

## Instructions

Use the `acc-ddd-auditor` agent to perform a comprehensive DDD audit:

### Analysis Scope

1. **Layer Structure** — Domain, Application, Infrastructure, Presentation
2. **Domain Model** — Entities, Value Objects, Aggregates, Domain Services
3. **Application Layer** — UseCases, DTOs, Command/Query Handlers
4. **Infrastructure** — Repository implementations, external integrations
5. **Presentation Layer** — Actions/Controllers, Request/Response DTOs, Middleware
6. **Dependencies** — layer violations, circular dependencies

### Generate Recommendations

Based on detected issues, map problems to solutions:

| Issue Type | Pattern | Generation Skill |
|------------|---------|------------------|
| Primitive obsession | Value Object | `acc-create-value-object` |
| Anemic entities | Rich Entity | `acc-create-entity` |
| Missing invariants | Aggregate Root | `acc-create-aggregate` |
| Complex object creation | Factory | `acc-create-factory` |
| Complex business rules | Specification | `acc-create-specification` |
| Cross-layer data transfer | DTO | `acc-create-dto` |
| External system integration | Anti-Corruption Layer | `acc-create-anti-corruption-layer` |
| Missing domain events | Domain Event | `acc-create-domain-event` |
| Stateless business logic | Domain Service | `acc-create-domain-service` |
| Write operations | Command + Handler | `acc-create-command` |
| Read operations | Query + Handler | `acc-create-query` |
| Data persistence | Repository | `acc-create-repository` |
| Business orchestration | Use Case | `acc-create-use-case` |

## Expected Output

A structured markdown report containing:

### 1. Executive Summary
- Overall DDD compliance score
- Layer structure overview
- Critical issues count

### 2. Layer Compliance Matrix
| Layer | Found | Compliance | Issues |
|-------|-------|------------|--------|

### 3. Critical Issues
Architecture violations requiring immediate attention:
- Domain → Infrastructure dependencies
- Framework leakage into Domain
- Business logic in wrong layers

### 4. Warnings
Antipatterns detected:
- Anemic domain models
- Primitive obsession
- Magic strings (should be Enums)
- Public setters (breaks encapsulation)

### 5. Pattern Recommendations

**Actionable recommendations linking issues to solutions:**

#### Domain Model Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| String email field | Value Object | Run `/acc-create-value-object Email` |
| Entity with only getters | Rich Entity | Run `/acc-create-entity` |
| No aggregate boundaries | Aggregate | Run `/acc-create-aggregate` |

#### Application Layer Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| Missing orchestration | Use Case | Run `/acc-create-use-case` |
| No command separation | Command | Run `/acc-create-command` |
| No query separation | Query | Run `/acc-create-query` |

#### Infrastructure Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| No repository interface | Repository | Run `/acc-create-repository` |
| Direct external API calls | ACL | Run `/acc-create-anti-corruption-layer` |

#### Presentation Layer Improvements
| Problem Found | Recommended | Skill to Use |
|---------------|-------------|--------------|
| Fat controller | Action (ADR) | Run `acc-create-action` |
| Missing response DTO | Responder | Run `acc-create-responder` |
| No input validation | Request DTO | Run `acc-create-dto` |

### 6. Prioritized Action Items
1. **Critical:** [Action with skill reference]
2. **High:** [Action with skill reference]
3. **Medium:** [Action with skill reference]

## Usage Examples

```bash
/acc-ddd-audit
/acc-ddd-audit src/
/acc-ddd-audit /path/to/project
```

