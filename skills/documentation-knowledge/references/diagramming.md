# Diagramming

## Mermaid Diagrams in Documentation

### Why Mermaid

- Rendered natively in GitHub, GitLab, and most markdown viewers
- Text-based: version-controlled alongside code
- No external tools needed for authoring
- Supports class, sequence, flowchart, ER, C4, state, and Gantt diagrams

## Diagram Types

### Class Diagram

Best for documenting domain model structure, aggregate boundaries, and Value Objects.

```mermaid
classDiagram
    class Order {
        -OrderId id
        -CustomerId customerId
        -OrderStatus status
        -OrderLine[] lines
        -DateTimeImmutable createdAt
        +create(OrderId, CustomerId, array) Order
        +confirm() void
        +cancel() void
        +total() Money
        +releaseEvents() DomainEvent[]
    }

    class OrderLine {
        -ProductId productId
        -int quantity
        -Money unitPrice
        +total() Money
    }

    class OrderId {
        +string value
        +generate() OrderId
    }

    class Money {
        -int cents
        -Currency currency
        +add(Money) Money
        +isNegativeOrZero() bool
        +zero(string) Money
    }

    Order "1" *-- "1..*" OrderLine : contains
    Order --> OrderId : identified by
    OrderLine --> Money : uses
    Order --> Money : calculates total
```

### Sequence Diagram

Best for documenting request flows, command handling, and event processing.

```mermaid
sequenceDiagram
    participant Client
    participant Action as CreateOrderAction
    participant Bus as CommandBus
    participant Handler as CreateOrderHandler
    participant Repo as OrderRepository
    participant Events as EventDispatcher

    Client->>Action: POST /api/orders
    Action->>Action: Validate request
    Action->>Bus: dispatch(CreateOrderCommand)
    Bus->>Handler: handle(command)
    Handler->>Repo: nextIdentity()
    Repo-->>Handler: OrderId
    Handler->>Handler: Order::create(...)
    Handler->>Repo: save(order)
    Handler->>Events: dispatch(OrderCreatedEvent)
    Events-->>Handler: async processing
    Handler-->>Bus: OrderId
    Bus-->>Action: OrderId
    Action-->>Client: 201 Created {id}
```

### Flowchart

Best for documenting business processes, decision logic, and workflows.

```mermaid
flowchart TD
    START([Order Received]) --> VALIDATE{Valid?}
    VALIDATE -->|No| REJECT[Return 422]
    VALIDATE -->|Yes| STOCK{In Stock?}
    STOCK -->|No| BACKORDER[Create Backorder]
    STOCK -->|Yes| PAYMENT{Payment OK?}
    PAYMENT -->|Failed| RETRY{Retries < 3?}
    RETRY -->|Yes| PAYMENT
    RETRY -->|No| CANCEL[Cancel Order]
    PAYMENT -->|Success| CONFIRM[Confirm Order]
    CONFIRM --> SHIP[Create Shipment]
    SHIP --> NOTIFY[Send Confirmation Email]
    NOTIFY --> DONE([Done])
```

### Entity-Relationship Diagram

Best for documenting database schema and read model structure.

```mermaid
erDiagram
    orders {
        uuid id PK
        uuid customer_id FK
        varchar status
        int total_cents
        timestamp created_at
        timestamp updated_at
    }

    order_lines {
        uuid id PK
        uuid order_id FK
        uuid product_id FK
        int quantity
        int unit_price_cents
    }

    order_events {
        bigint id PK
        uuid aggregate_id FK
        varchar event_type
        jsonb payload
        int version
        timestamp created_at
    }

    orders ||--o{ order_lines : contains
    orders ||--o{ order_events : "sourced from"
```

### C4 Diagram

Best for documenting system architecture at different zoom levels.

```mermaid
C4Context
    title System Context - Order Management

    Person(customer, "Customer", "Places orders via web/mobile")
    Person(admin, "Admin", "Manages orders and catalog")

    System(orderSystem, "Order System", "DDD/CQRS order management")

    System_Ext(stripe, "Stripe", "Payment processing")
    System_Ext(dhl, "DHL API", "Shipping and tracking")
    System_Ext(sendgrid, "SendGrid", "Email delivery")

    Rel(customer, orderSystem, "HTTPS/JSON")
    Rel(admin, orderSystem, "HTTPS/JSON")
    Rel(orderSystem, stripe, "HTTPS")
    Rel(orderSystem, dhl, "HTTPS")
    Rel(orderSystem, sendgrid, "AMQP")
```

### State Diagram

Best for documenting entity lifecycle, aggregate state transitions, and workflow statuses.

```mermaid
stateDiagram-v2
    [*] --> Draft: Order created
    Draft --> Confirmed: confirm()
    Draft --> Cancelled: cancel()
    Confirmed --> Paid: payment received
    Confirmed --> Cancelled: cancel()
    Paid --> Shipped: shipment created
    Shipped --> Delivered: delivery confirmed
    Cancelled --> [*]
    Delivered --> [*]
```

## Diagram Placement Guidelines

### Where to Place Diagrams

| Location | Diagram Type | Purpose |
|----------|-------------|---------|
| `README.md` | Flowchart | High-level system overview |
| `docs/architecture/` | C4, Class | Architecture documentation |
| `docs/api/` | Sequence | API request flows |
| `docs/adr/` | Flowchart, Class | Decision context |
| Bounded context `README.md` | Class, ER | Context-specific model |
| `CONTRIBUTING.md` | Flowchart | Development workflow |

### Sizing Rules

| Guideline | Recommendation |
|-----------|---------------|
| Max nodes per diagram | 9-12 (cognitive limit) |
| Max depth | 4 levels |
| Labels | Always use descriptive labels on edges |
| Node IDs | Use meaningful names, not A/B/C |
| Direction | Top-down for hierarchy, left-right for flow |

## Auto-Generating Diagrams

### From PHP Code (Class Diagrams)

```bash
# Using php-class-diagram (Smeghead)
vendor/bin/php-class-diagram src/Domain/Order/ --format mermaid > docs/diagrams/order-domain.md

# Using phpDocumentor class diagram
phpdoc --directory=src/ --target=docs/ --template="clean"
```

### From Database (ER Diagrams)

```bash
# Using SchemaSpy
java -jar schemaspy.jar -t pgsql -db orderdb -o docs/schema/

# Using Doctrine schema dump
bin/console doctrine:schema:create --dump-sql > docs/schema/schema.sql
```

### From OpenAPI (Sequence Diagrams)

```bash
# Generate from OpenAPI spec
npx openapi-to-mermaid openapi.yaml > docs/diagrams/api-flows.md
```

## Detection Patterns

```bash
# Find all Mermaid diagrams
Grep: "```mermaid" --glob "**/*.md"

# Find diagrams with too many nodes (> 12)
Grep: "```mermaid" -A 30 --glob "**/*.md"

# Find diagrams without labels on edges
Grep: "-->|-->" --glob "**/*.md"

# Find non-descriptive node IDs
Grep: "\b[A-B]\[" --glob "**/*.md"
```

## Summary

| Diagram Type | Best For | Example Use Case |
|-------------|----------|-----------------|
| **Class** | Domain model, aggregates | Show Order aggregate with Value Objects |
| **Sequence** | Request flows, event chains | Document command handling pipeline |
| **Flowchart** | Business logic, decisions | Order processing workflow |
| **ER** | Database schema, read models | CQRS read model structure |
| **C4** | System architecture, contexts | Bounded context relationships |
| **State** | Entity lifecycle, workflows | Order status transitions |
| **Gantt** | Project timelines, migration plans | Phased rollout schedule |
