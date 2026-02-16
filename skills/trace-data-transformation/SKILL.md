---
name: acc-trace-data-transformation
description: Maps data transformation chains — Request DTO to Command to Entity to Response DTO. Identifies mappers, serializers, type conversions, and data loss points across layer boundaries.
---

# Data Transformation Tracer

## Overview

Traces how data transforms as it passes through application layers — from raw HTTP input through DTOs, Commands, Entities, and back to Response objects. Identifies mappers, serializers, converters, and potential data loss points.

## Transformation Chain Patterns

### Standard CQRS Chain

```
HTTP Request Body (JSON/Form)
  → Request DTO (validated input)
    → Command/Query (application layer input)
      → Entity/Aggregate (domain model)
        → Domain Event (side effect data)
        → Response DTO (output format)
          → HTTP Response (JSON/XML)
```

### Detection Patterns

#### Input Transformation

```bash
# Request DTOs / Form Requests
Grep: "class.*Request|class.*Input" --glob "**/Api/**/*.php"
Grep: "class.*Request" --glob "**/Presentation/**/*.php"

# Request to Command mapping
Grep: "new.*Command\\(|Command::from|Command::create" --glob "**/*.php"

# Deserialization
Grep: "deserialize|fromArray|fromRequest|fromJson" --glob "**/*.php"
Grep: "Serializer::deserialize|denormalize" --glob "**/*.php"
```

#### Entity Transformation

```bash
# Entity factories / named constructors
Grep: "static function (create|from|of|new)" --glob "**/Domain/**/*.php"

# Entity to DTO conversion
Grep: "function (toArray|toDTO|toResponse|toView)" --glob "**/Domain/**/*.php"
Grep: "::fromEntity|::fromDomain|::fromModel" --glob "**/*.php"
```

#### Output Transformation

```bash
# Response DTOs
Grep: "class.*Response|class.*Output|class.*View" --glob "**/Api/**/*.php"
Grep: "class.*Resource" --glob "**/Http/**/*.php"

# Serialization
Grep: "jsonSerialize|toArray|normalize" --glob "**/*.php"
Grep: "JsonResponse|json_encode" --glob "**/*.php"

# Collection transformation
Grep: "->map\\(|array_map|->transform" --glob "**/*.php"
```

#### Mappers and Converters

```bash
# Explicit mapper classes
Grep: "class.*Mapper|class.*Converter|class.*Transformer|class.*Assembler" --glob "**/*.php"

# Mapping methods
Grep: "function (map|convert|transform|assemble|adapt)" --glob "**/*.php"

# AutoMapper / Symfony Serializer
Grep: "AutoMapper|ObjectNormalizer|PropertyNormalizer" --glob "**/*.php"
```

## Analysis Process

### Step 1: Identify Transformation Points

For a given request flow:
1. **Read the entry point** — what data format comes in
2. **Find each class boundary** — where data changes shape
3. **Read constructor/factory** — what fields are mapped
4. **Track field names** — which fields are renamed, combined, or dropped

### Step 2: Map Field Transformations

| Source | Target | Transformation |
|--------|--------|---------------|
| `request.customer_name` | `CreateOrderCommand.customerName` | snake_case → camelCase |
| `command.customerId` | `Customer entity` | ID → full entity (repo lookup) |
| `entity.createdAt` | `response.created_at` | DateTime → string ISO 8601 |
| `entity.money` | `response.amount` | Money VO → float |

### Step 3: Identify Data Loss Points

Check for:
- Fields present in source but missing in target
- Type narrowing (DateTime → string, loses timezone)
- Precision loss (float → int)
- Relationship flattening (Entity → ID only)

## Output Format

```markdown
## Data Transformation Map

### Flow: Create Order

#### Transformation Chain

```
[1] JSON Input
    {
      "customer_id": "uuid-123",
      "items": [{"product_id": "p-1", "quantity": 2}],
      "shipping_address": {"street": "...", "city": "..."}
    }
         │
         ▼  (Deserialization + Validation)
[2] CreateOrderRequest
    customerId: string (validated: uuid format)
    items: CreateOrderItemRequest[] (validated: non-empty)
    shippingAddress: AddressRequest (validated: all fields required)
         │
         ▼  (Mapping: CreateOrderRequest → CreateOrderCommand)
[3] CreateOrderCommand
    customerId: CustomerId (Value Object wrapping)
    items: OrderItemData[] (DTO with productId + quantity)
    shippingAddress: AddressData (DTO)
         │
         ▼  (Domain Factory: Order::create())
[4] Order Entity
    id: OrderId (generated)
    customerId: CustomerId
    items: OrderItem[] (entities with calculated prices)
    total: Money (calculated from items)
    status: OrderStatus::Pending
    shippingAddress: ShippingAddress (Value Object)
    createdAt: DateTimeImmutable
         │
         ▼  (Response Mapping: OrderResponse::fromEntity())
[5] OrderResponse
    id: string (OrderId → string)
    customerId: string (CustomerId → string)
    items: OrderItemResponse[] (entity → response)
    total: float (Money → float, currency separate)
    currency: string (from Money)
    status: string (enum → string)
    shippingAddress: AddressResponse
    createdAt: string (ISO 8601)
         │
         ▼  (JSON Serialization)
[6] JSON Output
    {"id": "...", "customer_id": "...", "total": 150.00, ...}
```

#### Field Mapping Table

| Layer | Field | Type | Source | Transformation |
|-------|-------|------|--------|---------------|
| Input → Request | customer_id → customerId | string | JSON key | snake → camel |
| Request → Command | customerId → customerId | string → CustomerId | DTO | Wrap in VO |
| Command → Entity | items → OrderItem[] | DTO[] → Entity[] | Factory | Enrich with prices |
| Entity → Response | total → total | Money → float | Mapper | Extract amount |
| Entity → Response | createdAt → createdAt | DateTimeImmutable → string | Mapper | Format ISO 8601 |
| Response → JSON | customerId → customer_id | string | Serializer | camel → snake |

#### Data Enrichment Points

| Step | What's Added | Source |
|------|-------------|--------|
| Command → Entity | OrderId | Generated (UUID) |
| Command → Entity | Item prices | ProductRepository lookup |
| Command → Entity | Total amount | Calculated from items |
| Command → Entity | Created timestamp | System clock |
| Command → Entity | Initial status | Domain default (Pending) |

#### Potential Data Loss Points

| Step | Field | Issue |
|------|-------|-------|
| Money → float | precision | Floating point precision loss |
| DateTime → string | timezone | Check if timezone preserved |
| Entity → Response | internal state | Domain internals not exposed (expected) |
```

## Transformation Quality Indicators

| Indicator | Good | Warning |
|-----------|------|---------|
| Type safety | Typed DTOs at boundaries | Untyped arrays |
| Validation | At input boundary | Scattered or missing |
| Mapping | Explicit mapper/factory | Implicit in controller |
| Value Objects | Domain uses VOs | Primitives throughout |
| Serialization | Controlled (toArray/normalize) | json_encode on entity |

## Common Anti-Patterns

| Anti-Pattern | Detection | Issue |
|-------------|-----------|-------|
| Entity as Response | `return json_encode($entity)` | Exposes internals |
| Array transport | `$data = ['key' => $value]` | No type safety |
| Missing DTO | Controller → Repository direct | Skips validation |
| Leaky abstraction | Domain types in API response | Tight coupling |

## Integration

This skill is used by:
- `acc-data-flow-analyst` — documents data transformation chains
- `acc-trace-request-lifecycle` — enriches lifecycle with data details
- `acc-explain-business-process` — shows data perspective of processes
