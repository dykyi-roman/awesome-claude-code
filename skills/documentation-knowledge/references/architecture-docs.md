# Architecture Documentation

## ARCHITECTURE.md Structure for DDD Projects

### Complete Template

```markdown
# Architecture

## Overview

Brief description of the system purpose and key architectural decisions (2-3 sentences).
This system follows Domain-Driven Design with Clean Architecture, using CQRS for
command/query separation and Event Sourcing for the Order bounded context.

## System Context

```mermaid
C4Context
    title System Context Diagram

    Person(customer, "Customer", "Places and tracks orders")
    Person(admin, "Admin", "Manages catalog and orders")

    System(orderSystem, "Order System", "Handles order lifecycle")

    System_Ext(payment, "Payment Gateway", "Processes payments")
    System_Ext(shipping, "Shipping Provider", "Handles delivery")
    System_Ext(email, "Email Service", "Sends notifications")

    Rel(customer, orderSystem, "Places orders", "HTTPS/JSON")
    Rel(admin, orderSystem, "Manages", "HTTPS/JSON")
    Rel(orderSystem, payment, "Processes payments", "HTTPS")
    Rel(orderSystem, shipping, "Creates shipments", "HTTPS")
    Rel(orderSystem, email, "Sends emails", "AMQP")
```

## Bounded Contexts

### Context Map

```mermaid
graph LR
    subgraph "Core Domain"
        ORDER[Order Context]
        CATALOG[Catalog Context]
    end

    subgraph "Supporting Domain"
        PAYMENT[Payment Context]
        SHIPPING[Shipping Context]
    end

    subgraph "Generic Subdomain"
        NOTIFICATION[Notification Context]
        IDENTITY[Identity Context]
    end

    ORDER -->|Customer-Supplier| CATALOG
    ORDER -->|Partnership| PAYMENT
    ORDER -->|Conformist| SHIPPING
    ORDER -.->|Published Language| NOTIFICATION
    ORDER -->|Anti-Corruption Layer| IDENTITY
```

### Context Details

| Context | Type | Aggregates | Integration |
|---------|------|------------|-------------|
| **Order** | Core | Order, OrderLine | Event Sourcing + CQRS |
| **Catalog** | Core | Product, Category | CRUD + Cache |
| **Payment** | Supporting | Payment, Refund | ACL to Stripe |
| **Shipping** | Supporting | Shipment, Tracking | Conformist to DHL |
| **Notification** | Generic | Template, Channel | Async via RabbitMQ |

## Layer Dependencies

```mermaid
graph TD
    PRES[Presentation Layer] --> APP[Application Layer]
    APP --> DOM[Domain Layer]
    INFRA[Infrastructure Layer] --> DOM

    PRES -.->|"depends on"| APP
    APP -.->|"depends on"| DOM
    INFRA -.->|"implements"| DOM

    style DOM fill:#2d5016,color:#fff
    style APP fill:#1a3a5c,color:#fff
    style PRES fill:#5c3a1a,color:#fff
    style INFRA fill:#3a1a5c,color:#fff
```

### Layer Rules

| Rule | Description | Enforcement |
|------|-------------|-------------|
| Domain has no dependencies | No framework, no infrastructure imports | PHPStan rules, Deptrac |
| Application depends on Domain only | Interfaces in Domain, implementations in Infrastructure | Deptrac config |
| Infrastructure implements Domain | Repository abstractions defined alongside domain consumers | Interface compliance |
| Presentation calls Application | Actions/Controllers call UseCases/Services | Architectural tests |

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Presentation | Symfony 7.2 | HTTP routing, request handling |
| Application | PHP 8.4 | Business orchestration |
| Domain | PHP 8.4 (no deps) | Business logic |
| Database | PostgreSQL 16 | Primary persistence |
| Cache | Redis 7 | Read model cache, sessions |
| Queue | RabbitMQ 3.13 | Async event processing |
| Search | Elasticsearch 8 | Full-text search read model |
| Monitoring | Prometheus + Grafana | Metrics and alerting |

## Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API Layer
    participant CMD as Command Handler
    participant DOM as Domain
    participant ES as Event Store
    participant PROJ as Projector
    participant RM as Read Model

    C->>API: POST /orders
    API->>CMD: CreateOrderCommand
    CMD->>DOM: Order::create()
    DOM-->>CMD: OrderCreatedEvent
    CMD->>ES: Append events
    ES-->>PROJ: New events
    PROJ->>RM: Update read model
    C->>API: GET /orders/{id}
    API->>RM: Query read model
    RM-->>C: Order JSON
```

## Decisions

Architecture Decision Records are stored in `docs/adr/`.

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-001](docs/adr/001-use-ddd-architecture.md) | Use DDD with Clean Architecture | Accepted |
| [ADR-002](docs/adr/002-event-sourcing-for-orders.md) | Event Sourcing for Order context | Accepted |
| [ADR-003](docs/adr/003-cqrs-read-write-separation.md) | CQRS read/write separation | Accepted |
| [ADR-004](docs/adr/004-rabbitmq-for-messaging.md) | RabbitMQ for async messaging | Accepted |

## Deployment

```mermaid
graph TD
    LB[Load Balancer] --> APP1[App Server 1]
    LB --> APP2[App Server 2]

    APP1 --> PG_PRIMARY[(PostgreSQL Primary)]
    APP2 --> PG_PRIMARY
    PG_PRIMARY --> PG_REPLICA[(PostgreSQL Replica)]

    APP1 --> REDIS[(Redis Cluster)]
    APP2 --> REDIS

    APP1 --> RMQ[RabbitMQ Cluster]
    APP2 --> RMQ
    RMQ --> WORKER1[Worker 1]
    RMQ --> WORKER2[Worker 2]
```
```

## Documenting Bounded Context Relationships

### Integration Patterns

```markdown
### Order → Payment Integration

**Pattern:** Anti-Corruption Layer (ACL)

The Order context communicates with Payment via an ACL that translates
between domain models. The Payment ACL hides Stripe-specific details.

```php
// Domain interface (Order context)
interface PaymentGatewayInterface
{
    public function charge(OrderId $orderId, Money $amount): PaymentResult;
}

// ACL implementation (Infrastructure)
final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function charge(OrderId $orderId, Money $amount): PaymentResult
    {
        $stripeCharge = $this->stripe->charges->create([
            'amount' => $amount->cents(),
            'currency' => $amount->currency()->value,
            'metadata' => ['order_id' => $orderId->value],
        ]);

        return PaymentResult::fromStripe($stripeCharge);
    }
}
```

**Events published:** `OrderPaidEvent`, `PaymentFailedEvent`
**Events consumed:** none (initiator)
```

## Detection Patterns

```bash
# Check architecture docs exist
Glob: docs/architecture/README.md
Glob: ARCHITECTURE.md

# Check for C4 diagrams
Grep: "C4Context|C4Container|C4Component" --glob "docs/**/*.md"

# Check for bounded context documentation
Grep: "Bounded Context|Context Map" --glob "docs/**/*.md"

# Check for ADR references
Grep: "ADR|Architecture Decision" --glob "docs/architecture/**/*.md"

# Check for layer documentation
Grep: "Presentation Layer|Application Layer|Domain Layer|Infrastructure Layer" --glob "docs/**/*.md"
```

## Summary

| Section | Purpose | Audience |
|---------|---------|----------|
| **Overview** | System purpose and key decisions | Everyone |
| **System Context** | External dependencies and actors | Architects, new developers |
| **Bounded Contexts** | Domain decomposition and relationships | Domain experts, developers |
| **Layer Dependencies** | Code organization and dependency rules | Developers |
| **Technology Stack** | Tools and frameworks used | DevOps, new developers |
| **Data Flow** | Request processing and event flow | Developers, testers |
| **Decisions** | Why choices were made (links to ADRs) | Architects, future maintainers |
| **Deployment** | Infrastructure and scaling | DevOps, SREs |
