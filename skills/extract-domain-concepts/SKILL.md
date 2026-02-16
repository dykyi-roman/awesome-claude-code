---
name: acc-extract-domain-concepts
description: Maps domain model components — Entities, Value Objects, Aggregates, Services, Events, Repositories. Builds Ubiquitous Language glossary connecting code names to business terminology.
---

# Domain Concepts Extractor

## Overview

Extracts and catalogs all domain model components from the codebase, maps relationships between them, and builds a Ubiquitous Language glossary that connects technical class names to business concepts.

## Domain Component Detection

### Entities

```bash
# DDD entities
Glob: "**/Domain/**/Entity/*.php"
Glob: "**/Domain/**/*Entity.php"
Grep: "class.*Entity|extends.*Entity" --glob "**/Domain/**/*.php"

# Doctrine entities
Grep: "#\\[ORM\\\\Entity" --glob "**/*.php"
Grep: "@ORM\\\\Entity" --glob "**/*.php"

# Identity markers
Grep: "function getId|private.*\\$id|readonly.*Id \\$id" --glob "**/Domain/**/*.php"
```

### Value Objects

```bash
# Explicit Value Objects
Glob: "**/Domain/**/ValueObject/*.php"
Glob: "**/ValueObject/**/*.php"
Grep: "class.*ValueObject|extends.*ValueObject" --glob "**/*.php"

# Readonly classes in Domain (likely VOs)
Grep: "readonly class" --glob "**/Domain/**/*.php"

# Common VO patterns
Grep: "class (Email|Money|Address|PhoneNumber|Name|Quantity|Price|DateRange)" --glob "**/*.php"

# Self-validating constructors (VO pattern)
Grep: "private function __construct" --glob "**/Domain/**/*.php"
```

### Aggregates

```bash
# Explicit aggregates
Grep: "class.*Aggregate|extends.*AggregateRoot" --glob "**/*.php"
Glob: "**/Domain/**/Aggregate/*.php"

# Aggregate behavior (event recording)
Grep: "function (recordEvent|raise|apply)" --glob "**/Domain/**/*.php"

# Classes with multiple entity relationships
Grep: "private.*Collection|private.*array.*\\$" --glob "**/Domain/**/*.php"
```

### Domain Events

```bash
# Event classes
Glob: "**/Domain/**/Event/*.php"
Grep: "class.*Event|extends.*DomainEvent" --glob "**/Domain/**/*.php"

# Event data (what happened)
Grep: "readonly class.*Event" --glob "**/*.php"
Grep: "function __construct" --glob "**/Domain/**/Event/**/*.php"
```

### Domain Services

```bash
# Domain services
Glob: "**/Domain/**/Service/*.php"
Grep: "class.*Service" --glob "**/Domain/**/*.php"

# Services with domain logic (not infrastructure)
# Read files and check for: no external dependencies, pure domain logic
```

### Repositories

```bash
# Repository interfaces (Domain)
Grep: "interface.*Repository" --glob "**/Domain/**/*.php"

# Repository methods
Grep: "function (find|findBy|save|remove|nextIdentity|exists)" --glob "**/Domain/**/*.php"

# Repository implementations (Infrastructure)
Grep: "implements.*Repository" --glob "**/Infrastructure/**/*.php"
```

### Enumerations

```bash
# PHP 8.1+ enums
Grep: "^enum " --glob "**/Domain/**/*.php"

# Backed enums
Grep: "enum.*: string|enum.*: int" --glob "**/Domain/**/*.php"

# Status/Type enums
Grep: "enum.*(Status|Type|State|Category|Priority|Role)" --glob "**/*.php"
```

### Specifications

```bash
# Specification pattern
Grep: "class.*Specification|implements.*Specification" --glob "**/*.php"
Grep: "function isSatisfiedBy" --glob "**/*.php"
```

## Analysis Process

1. **Discover** — Find all domain components using patterns above
2. **Read** — Read each component to understand its purpose
3. **Classify** — Categorize by DDD building block type
4. **Map relationships** — Identify which entities belong to which aggregates
5. **Build glossary** — Translate class names to business terms

### Relationship Mapping

For each aggregate:
- Which entities it contains
- Which value objects it uses
- Which events it raises
- Which repository manages it

```bash
# Find relationships by reading constructor and use statements
Read: aggregate file
# Extract: constructor parameters, property types, use statements
```

## Output Format

```markdown
## Domain Model

### Component Summary

| Type | Count | Examples |
|------|-------|---------|
| Entities | 12 | Order, Customer, Product |
| Value Objects | 18 | Money, Email, Address |
| Aggregates | 4 | Order, Customer, Product, Catalog |
| Domain Events | 8 | OrderCreated, PaymentReceived |
| Domain Services | 3 | PricingService, ShippingCalculator |
| Repositories | 6 | OrderRepository, CustomerRepository |
| Enumerations | 5 | OrderStatus, PaymentMethod |

### Aggregate Map

#### Order Aggregate
```
Order (Aggregate Root)
├── OrderId (Value Object) — unique identifier
├── OrderItem[] (Entity) — line items
│   ├── ProductId (Value Object) — reference to Product
│   ├── Quantity (Value Object) — item quantity
│   └── Price (Value Object) — item price
├── Money (Value Object) — total amount
├── OrderStatus (Enum) — current status
├── ShippingAddress (Value Object) — delivery address
└── Events:
    ├── OrderCreated
    ├── OrderConfirmed
    └── OrderShipped
```

### Ubiquitous Language Glossary

| Business Term | Code Name | Type | Description |
|---------------|-----------|------|-------------|
| Order | `Order` | Aggregate | A customer's purchase request |
| Line Item | `OrderItem` | Entity | Single product in an order |
| Price | `Money` | Value Object | Amount with currency |
| Order Number | `OrderId` | Value Object | Unique order identifier |
| Customer | `Customer` | Aggregate | Person who places orders |
| Shipping Address | `ShippingAddress` | Value Object | Delivery destination |
| Order Status | `OrderStatus` | Enum | pending, confirmed, shipped, delivered |

### Entity Relationship Diagram Data

| Entity | Relates To | Relationship | Description |
|--------|-----------|--------------|-------------|
| Order | Customer | belongs-to | Order placed by Customer |
| Order | OrderItem | has-many | Order contains items |
| OrderItem | Product | references | Item refers to Product |
| Payment | Order | belongs-to | Payment for an Order |

### Bounded Context Map (if multi-context)

| Context | Aggregates | Shared Concepts |
|---------|-----------|----------------|
| Order | Order, OrderItem | CustomerId, ProductId |
| Customer | Customer, Address | CustomerId |
| Payment | Payment, Transaction | OrderId, Money |
| Catalog | Product, Category | ProductId |
```

## Glossary Building Rules

1. **Use business names** — "Shopping Cart" not "CartAggregate"
2. **Define relationships** — "A Customer places Orders"
3. **Include synonyms** — "Purchase" = "Order" in this context
4. **Note ambiguities** — "Account" means different things in different contexts
5. **Map to code** — Always link to the actual class

## Integration

This skill is used by:
- `acc-business-logic-analyst` — provides domain model documentation
- `acc-explain-business-process` — references domain concepts
- `acc-extract-business-rules` — connects rules to domain entities
- `acc-diagram-designer` — generates class/ER diagrams from this data
