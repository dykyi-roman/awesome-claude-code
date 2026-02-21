# C4 Model Reference

Detailed guide for C4 model diagrams in PHP DDD/CQRS projects using Mermaid syntax.

## C4 Model Overview

### What is the C4 Model?

A hierarchical approach to software architecture visualization with four abstraction levels, from system context down to code.

### C4 Levels

| Level | Name | Audience | What to Show | Scope |
|-------|------|----------|--------------|-------|
| **1** | Context | Everyone | System + external actors + external systems | Whole landscape |
| **2** | Container | Technical leads, architects | Deployable units (apps, DBs, queues) | Single system |
| **3** | Component | Developers | Modules, bounded contexts, layers | Single container |
| **4** | Code | Developers | Classes, interfaces, relationships | Single component |

## Level 1: System Context Diagram

### Purpose

Shows the system under design and its relationships with users and external systems.

### Mermaid C4Context Syntax

```mermaid
C4Context
    title E-Commerce System — Context Diagram

    Person(customer, "Customer", "Places orders, browses products")
    Person(admin, "Admin", "Manages catalog and orders")

    System(ecommerce, "E-Commerce System", "Handles orders, payments, inventory")

    System_Ext(payment, "Payment Gateway", "Stripe/PayPal")
    System_Ext(email, "Email Service", "SendGrid")
    System_Ext(shipping, "Shipping Provider", "DHL/FedEx API")
    System_Ext(analytics, "Analytics", "Google Analytics")

    Rel(customer, ecommerce, "Browses, Orders", "HTTPS")
    Rel(admin, ecommerce, "Manages", "HTTPS")
    Rel(ecommerce, payment, "Processes payments", "REST API")
    Rel(ecommerce, email, "Sends notifications", "SMTP/API")
    Rel(ecommerce, shipping, "Creates shipments", "REST API")
    Rel(ecommerce, analytics, "Sends events", "JS/API")
```

### Flowchart Alternative (Broader Compatibility)

```mermaid
flowchart TB
    subgraph external[External Systems]
        PS["Payment Gateway\n(Stripe)"]
        ES["Email Service\n(SendGrid)"]
        SH["Shipping Provider\n(DHL API)"]
    end

    subgraph users[Users]
        C["Customer"]
        A["Admin"]
    end

    subgraph boundary["E-Commerce System"]
        SYS["E-Commerce Platform\nPHP/Symfony"]
    end

    C -->|"Browse, Order\nHTTPS"| SYS
    A -->|"Manage catalog\nHTTPS"| SYS
    SYS -->|"Process payment\nREST"| PS
    SYS -->|"Send notification\nSMTP"| ES
    SYS -->|"Create shipment\nREST"| SH
```

### When to Use Level 1

- Stakeholder presentations
- Onboarding new team members
- Defining system boundaries
- Identifying external dependencies

## Level 2: Container Diagram

### Purpose

Shows the high-level technology choices and how containers communicate within the system.

### Mermaid C4Container Syntax

```mermaid
C4Container
    title E-Commerce System — Container Diagram

    Person(customer, "Customer")

    System_Boundary(ecommerce, "E-Commerce System") {
        Container(spa, "SPA", "React", "Product catalog, checkout UI")
        Container(api, "API Gateway", "PHP/Symfony", "REST API, authentication")
        Container(order_svc, "Order Service", "PHP/Symfony", "Order processing, CQRS")
        Container(catalog_svc, "Catalog Service", "PHP/Symfony", "Product management")
        Container(db_write, "Write DB", "PostgreSQL", "Event Store, write models")
        Container(db_read, "Read DB", "PostgreSQL", "Read models, projections")
        Container(cache, "Cache", "Redis", "Session, query cache")
        Container(queue, "Message Queue", "RabbitMQ", "Async commands, events")
    }

    System_Ext(payment, "Payment Gateway")

    Rel(customer, spa, "Uses", "HTTPS")
    Rel(spa, api, "Calls", "REST/JSON")
    Rel(api, order_svc, "Routes", "HTTP")
    Rel(api, catalog_svc, "Routes", "HTTP")
    Rel(order_svc, db_write, "Writes events", "SQL")
    Rel(order_svc, queue, "Publishes", "AMQP")
    Rel(queue, order_svc, "Consumes", "AMQP")
    Rel(order_svc, db_read, "Projects to", "SQL")
    Rel(catalog_svc, db_read, "Queries", "SQL")
    Rel(catalog_svc, cache, "Caches", "Redis Protocol")
    Rel(order_svc, payment, "Charges", "REST")
```

### Flowchart Alternative

```mermaid
flowchart TB
    subgraph ecommerce["E-Commerce System"]
        direction TB
        subgraph frontend[Frontend]
            SPA["SPA\nReact"]
        end
        subgraph backend[Backend Services]
            API["API Gateway\nPHP/Symfony"]
            ORD["Order Service\nPHP/Symfony\nCQRS + ES"]
            CAT["Catalog Service\nPHP/Symfony"]
        end
        subgraph data[Data Stores]
            PGW[("Write DB\nPostgreSQL\nEvent Store")]
            PGR[("Read DB\nPostgreSQL\nProjections")]
            RD[("Cache\nRedis")]
            MQ["Message Queue\nRabbitMQ"]
        end
    end

    SPA -->|"REST/JSON"| API
    API -->|"HTTP"| ORD
    API -->|"HTTP"| CAT
    ORD -->|"Append events"| PGW
    ORD -->|"Publish"| MQ
    MQ -->|"Consume"| ORD
    ORD -->|"Project"| PGR
    CAT -->|"Query"| PGR
    CAT -->|"Cache"| RD

    PS["Payment Gateway\nStripe"] ~~~ ecommerce
    ORD -->|"REST"| PS
```

### When to Use Level 2

- Architecture decision records
- DevOps and deployment planning
- Technology stack discussions
- Infrastructure cost estimation

## Level 3: Component Diagram

### Purpose

Shows the internal structure of a single container, focusing on bounded contexts and DDD layers.

### Mermaid C4Component Syntax

```mermaid
C4Component
    title Order Service — Component Diagram

    Container_Boundary(order_svc, "Order Service") {
        Component(action, "Order Actions", "Presentation", "HTTP endpoints")
        Component(cmd_bus, "Command Bus", "Application", "Routes commands to handlers")
        Component(qry_bus, "Query Bus", "Application", "Routes queries to handlers")
        Component(cmd_handler, "Command Handlers", "Application", "Order use cases")
        Component(qry_handler, "Query Handlers", "Application", "Read model queries")
        Component(aggregate, "Order Aggregate", "Domain", "Business rules, invariants")
        Component(events, "Domain Events", "Domain", "OrderCreated, OrderConfirmed...")
        Component(repo_if, "Repository Interface", "Domain", "OrderRepositoryInterface")
        Component(repo_impl, "ES Repository", "Infrastructure", "Event-sourced persistence")
        Component(projector, "Projectors", "Infrastructure", "Event-to-read-model sync")
    }

    ContainerDb(es, "Event Store", "PostgreSQL")
    ContainerDb(rm, "Read Model DB", "PostgreSQL")
    Container(mq, "RabbitMQ", "Message Queue")

    Rel(action, cmd_bus, "Dispatches command")
    Rel(action, qry_bus, "Dispatches query")
    Rel(cmd_bus, cmd_handler, "Routes to")
    Rel(qry_bus, qry_handler, "Routes to")
    Rel(cmd_handler, aggregate, "Loads, calls")
    Rel(aggregate, events, "Raises")
    Rel(cmd_handler, repo_if, "Saves via")
    Rel(repo_impl, repo_if, "Implements")
    Rel(repo_impl, es, "Appends events")
    Rel(projector, rm, "Updates projections")
    Rel(repo_impl, mq, "Publishes events")
    Rel(qry_handler, rm, "Reads from")
```

### Flowchart Alternative (Bounded Contexts)

```mermaid
flowchart TB
    subgraph order_svc["Order Service Container"]
        direction TB
        subgraph presentation["Presentation Layer"]
            OA["OrderAction\nCreateOrderAction\nGetOrderAction"]
        end

        subgraph application["Application Layer"]
            CB["CommandBus"]
            QB["QueryBus"]
            CH["CreateOrderHandler\nConfirmOrderHandler\nCancelOrderHandler"]
            QH["GetOrderDetailsHandler\nListOrdersHandler"]
        end

        subgraph domain["Domain Layer"]
            AG["Order Aggregate\n+ OrderLine\n+ Money"]
            VO["Value Objects\nOrderId, CustomerId\nOrderStatus, Money"]
            DE["Domain Events\nOrderCreated\nOrderConfirmed"]
            RI["OrderRepositoryInterface"]
        end

        subgraph infrastructure["Infrastructure Layer"]
            REPO["EventSourcedOrderRepository"]
            PROJ["OrderProjector\nOrderListProjector"]
            BUS["SymfonyCommandBus\nSymfonyQueryBus"]
        end
    end

    OA --> CB
    OA --> QB
    CB --> CH
    QB --> QH
    CH --> AG
    AG --> DE
    CH --> RI
    REPO -.->|implements| RI
    BUS -.->|implements| CB
    BUS -.->|implements| QB

    ES[("Event Store\nPostgreSQL")]
    RM[("Read Model\nPostgreSQL")]

    REPO --> ES
    PROJ --> RM
    QH --> RM
```

### When to Use Level 3

- Sprint planning for specific services
- Code review discussions
- DDD bounded context mapping
- New developer orientation to a service

## Level 4: Code Diagram

### Purpose

Shows class-level detail for a specific component. Use sparingly — only for complex aggregates or critical domain logic.

### Order Aggregate Class Diagram

```mermaid
classDiagram
    class Order {
        <<Aggregate Root>>
        -OrderId id
        -CustomerId customerId
        -OrderStatus status
        -Money totalAmount
        -OrderLineCollection lines
        -array~DomainEvent~ events
        +create(CustomerId, OrderLine[])$ Order
        +addLine(OrderLine) void
        +removeLine(OrderLineId) void
        +confirm() void
        +cancel(CancellationReason) void
        +ship(TrackingNumber) void
        +uncommittedEvents() DomainEvent[]
    }

    class OrderLine {
        <<Entity>>
        -OrderLineId id
        -ProductId productId
        -Quantity quantity
        -Money unitPrice
        +totalPrice() Money
    }

    class OrderId {
        <<Value Object>>
        +string value
        +generate()$ OrderId
        +fromString(string)$ OrderId
        +equals(OrderId) bool
    }

    class OrderStatus {
        <<Enumeration>>
        Pending
        Confirmed
        Shipped
        Delivered
        Cancelled
    }

    class Money {
        <<Value Object>>
        +int amount
        +string currency
        +add(Money) Money
        +subtract(Money) Money
        +multiply(int) Money
        +equals(Money) bool
    }

    class OrderCreatedEvent {
        <<Domain Event>>
        +OrderId orderId
        +CustomerId customerId
        +DateTimeImmutable occurredAt
    }

    class OrderConfirmedEvent {
        <<Domain Event>>
        +OrderId orderId
        +Money totalAmount
        +DateTimeImmutable occurredAt
    }

    class OrderRepositoryInterface {
        <<Interface>>
        +findById(OrderId) Order?
        +save(Order) void
    }

    Order "1" *-- "1..*" OrderLine : contains
    Order --> OrderId : identified by
    Order --> OrderStatus : has state
    Order --> Money : tracks total
    OrderLine --> Money : has unit price
    Order ..> OrderCreatedEvent : raises
    Order ..> OrderConfirmedEvent : raises
    OrderRepositoryInterface ..> Order : manages
```

### When to Use Level 4

- Documenting complex aggregates
- Reviewing domain model design
- Onboarding to specific bounded context
- Detecting DDD violations (anemic model, broken invariants)

## C4 Deployment Diagram

### Purpose

Shows how containers map to infrastructure nodes in production.

### Mermaid C4Deployment Syntax

```mermaid
C4Deployment
    title E-Commerce System — Production Deployment

    Deployment_Node(cloud, "AWS", "Cloud Provider") {
        Deployment_Node(alb, "ALB", "Load Balancer") {
            Container(lb, "Load Balancer", "AWS ALB", "HTTPS termination")
        }
        Deployment_Node(ecs, "ECS Cluster", "Container Orchestration") {
            Deployment_Node(api_task, "API Task", "Fargate") {
                Container(api, "API", "PHP-FPM/Nginx", "REST API")
            }
            Deployment_Node(worker_task, "Worker Task", "Fargate") {
                Container(worker, "Worker", "PHP CLI", "Queue consumer")
            }
        }
        Deployment_Node(rds, "RDS", "Managed Database") {
            ContainerDb(pg, "PostgreSQL", "RDS", "Write/Read DB")
        }
        Deployment_Node(elasticache, "ElastiCache", "Managed Cache") {
            ContainerDb(redis, "Redis", "ElastiCache", "Cache, sessions")
        }
        Deployment_Node(mq_node, "AmazonMQ", "Managed Queue") {
            Container(rabbitmq, "RabbitMQ", "AmazonMQ", "Message broker")
        }
    }

    Rel(lb, api, "Forwards", "HTTP")
    Rel(api, pg, "Reads/Writes", "SQL")
    Rel(api, redis, "Caches", "Redis")
    Rel(api, rabbitmq, "Publishes", "AMQP")
    Rel(rabbitmq, worker, "Delivers", "AMQP")
    Rel(worker, pg, "Reads/Writes", "SQL")
```

### Flowchart Alternative

```mermaid
flowchart TB
    subgraph aws["AWS Cloud"]
        subgraph alb["ALB (Load Balancer)"]
            LB["HTTPS Termination\nSSL/TLS"]
        end

        subgraph ecs["ECS Cluster (Fargate)"]
            subgraph api_svc["API Service (x3)"]
                API1["PHP-FPM + Nginx"]
            end
            subgraph worker_svc["Worker Service (x2)"]
                W1["PHP CLI Consumer"]
            end
        end

        subgraph data["Data Layer"]
            PG_W[("RDS Primary\nPostgreSQL\nWrite")]
            PG_R[("RDS Replica\nPostgreSQL\nRead")]
            REDIS[("ElastiCache\nRedis Cluster")]
            MQ["AmazonMQ\nRabbitMQ"]
        end
    end

    LB -->|"HTTP"| API1
    API1 -->|"Write SQL"| PG_W
    API1 -->|"Read SQL"| PG_R
    PG_W -.->|"Replication"| PG_R
    API1 -->|"Cache"| REDIS
    API1 -->|"Publish"| MQ
    MQ -->|"Consume"| W1
    W1 -->|"Write SQL"| PG_W
```

## C4 in PHP DDD Projects

### Bounded Context Map (Level 1.5)

```mermaid
flowchart LR
    subgraph contexts["Bounded Contexts"]
        subgraph order["Order Context"]
            OA["Order\nAggregate"]
        end
        subgraph catalog["Catalog Context"]
            PA["Product\nAggregate"]
        end
        subgraph customer["Customer Context"]
            CA["Customer\nAggregate"]
        end
        subgraph payment["Payment Context"]
            PYA["Payment\nAggregate"]
        end
        subgraph shipping["Shipping Context"]
            SA["Shipment\nAggregate"]
        end
    end

    order -->|"ProductId\n(ACL)"| catalog
    order -->|"CustomerId\n(ACL)"| customer
    order -.->|"OrderConfirmed\n(Event)"| payment
    order -.->|"OrderShipped\n(Event)"| shipping
    payment -.->|"PaymentReceived\n(Event)"| order
    shipping -.->|"ShipmentDelivered\n(Event)"| order
```

### DDD Layer Mapping to C4

| C4 Level | DDD Concept | What to Show |
|----------|-------------|--------------|
| Context | Bounded Contexts | Context map with relationships |
| Container | Deployable services | Service per bounded context (or monolith) |
| Component | DDD Layers | Presentation, Application, Domain, Infrastructure |
| Code | Domain Model | Aggregates, Entities, Value Objects, Events |

## Best Practices

### Do's and Don'ts

| Do | Don't |
|----|-------|
| Start at Level 1, zoom in as needed | Jump straight to Level 4 |
| Keep 5-9 elements per diagram | Cram everything into one view |
| Update diagrams when architecture changes | Let diagrams go stale |
| Use consistent notation across team | Mix C4 with ad-hoc boxes |
| Store diagrams as code (Mermaid in repo) | Use binary diagram files |
| Label relationships with protocol/data | Leave arrows unlabeled |

### Diagram Naming Convention

```
docs/diagrams/
  c4-context.md          # Level 1
  c4-container.md        # Level 2
  c4-component-order.md  # Level 3 per service
  c4-code-order-agg.md   # Level 4 per aggregate (rare)
  c4-deployment-prod.md  # Deployment view
```

## Detection Patterns

```bash
# Check for C4 diagrams in project
Grep: "C4Context|C4Container|C4Component|C4Deployment" --glob "**/*.md"

# Check for architecture documentation
Glob: **/docs/diagrams/*.md
Glob: **/ARCHITECTURE.md

# Check for bounded context mapping
Grep: "Bounded Context|Context Map|context map" --glob "**/*.md"

# Check for deployment diagrams
Grep: "C4Deployment|deployment.*diagram" --glob "**/*.md"

# Warning: Missing C4 diagrams
Grep: "flowchart|sequenceDiagram" --glob "**/ARCHITECTURE.md"
# If found but no C4 keywords — suggest upgrading to C4 model
```

## Summary

| Level | Audience | What to Show | Update Frequency | Example Trigger |
|-------|----------|--------------|------------------|-----------------|
| **Context** | All stakeholders | System + actors + external systems | Quarterly / new integration | New external dependency |
| **Container** | Tech leads, DevOps | Apps, DBs, queues, caches | Monthly / infra change | New service or database |
| **Component** | Developers | Layers, modules, bounded contexts | Per sprint / refactor | New aggregate or module |
| **Code** | Developers | Classes, interfaces, relationships | On demand / review | Complex aggregate design |
| **Deployment** | DevOps, SRE | Infra nodes, scaling, networking | Per release / infra change | New environment or scaling |
