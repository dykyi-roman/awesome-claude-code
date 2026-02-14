---
description: Generate DDD components. Creates entities, value objects, aggregates, commands, queries, repositories, domain services, factories, specifications, DTOs, ACL, event stores, snapshots, and use cases for PHP 8.5.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: opus
argument-hint: <component-type> <ComponentName> [-- additional instructions]
---

# Generate DDD Components

Generate Domain-Driven Design components for PHP 8.5 with tests and proper layer placement.

## Input Parsing

Parse `$ARGUMENTS` to extract component type, name, and optional meta-instructions:

```
Format: <component-type> <ComponentName> [-- <meta-instructions>]

Examples:
- /acc-generate-ddd entity Order
- /acc-generate-ddd vo Email
- /acc-generate-ddd aggregate Order -- with OrderLine child entity
- /acc-generate-ddd command CreateOrder
- /acc-generate-ddd query GetOrderById
```

**Parsing rules:**
1. First part = **component type** (required, see list below)
2. Second part = **component name** (required)
3. After ` -- ` = **meta-instructions** (optional customizations)

## Supported Components

### Domain Layer Components

| Component | Aliases | Skill Used |
|-----------|---------|------------|
| `entity` | `ent` | acc-create-entity |
| `value-object` | `vo`, `valueobject` | acc-create-value-object |
| `aggregate` | `agg`, `aggregate-root` | acc-create-aggregate |
| `domain-event` | `event`, `de` | acc-create-domain-event |
| `repository` | `repo` | acc-create-repository |
| `domain-service` | `service`, `ds` | acc-create-domain-service |
| `factory` | `fact` | acc-create-factory |
| `specification` | `spec` | acc-create-specification |

### Application Layer Components

| Component | Aliases | Skill Used |
|-----------|---------|------------|
| `command` | `cmd` | acc-create-command |
| `query` | `qry` | acc-create-query |
| `use-case` | `usecase`, `uc` | acc-create-use-case |
| `dto` | `data-transfer` | acc-create-dto |

### Event Sourcing Components

| Component | Aliases | Skill Used |
|-----------|---------|------------|
| `event-store` | `es`, `eventstore` | acc-create-event-store |
| `snapshot` | `snap` | acc-create-snapshot |
| `read-model` | `rm`, `projection` | acc-create-read-model |

### Integration Layer Components

| Component | Aliases | Skill Used |
|-----------|---------|------------|
| `acl` | `anti-corruption` | acc-create-anti-corruption-layer |

## Pre-flight Check

1. Verify valid component type:
   - If not provided, ask user which component to generate
   - If invalid, show list of supported components

2. Check project structure:
   - Read `composer.json` for namespace configuration
   - Determine target directory based on component type

## Instructions

Use the `acc-ddd-generator` agent to generate DDD components:

```
Task tool with subagent_type="acc-ddd-generator"
prompt: "Generate [COMPONENT_TYPE] named [COMPONENT_NAME]. [META-INSTRUCTIONS if provided]

Requirements:
1. PHP 8.5 with declare(strict_types=1)
2. PSR-12 coding style
3. Final readonly classes where appropriate
4. Constructor property promotion
5. Include related components (exceptions, enums)
6. Include unit tests
7. Follow existing project patterns"
```

## Output Structure

```
Domain:        src/Domain/{BC}/{Entity,ValueObject,Repository,Service,Factory,Specification,Event,Enum,Exception}/
Application:   src/Application/{BC}/{Command,Query,UseCase,DTO,ReadModel,Snapshot}/
Infrastructure: src/Infrastructure/{BC}/{Persistence,ACL,EventStore,Snapshot}/
Tests:         tests/Unit/{Domain,Application,Infrastructure}/{BC}/...
```

## Examples

```bash
/acc-generate-ddd entity Order
/acc-generate-ddd vo Email -- with DNS validation
/acc-generate-ddd aggregate ShoppingCart -- with CartItem child
/acc-generate-ddd command CreateOrder
/acc-generate-ddd query GetUserOrders -- with pagination
/acc-generate-ddd event-store Order -- with Doctrine implementation
/acc-generate-ddd snapshot Payment
/acc-generate-ddd acl StripePayment -- translate to domain Money
```
