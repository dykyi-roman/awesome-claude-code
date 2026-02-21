# Sequence Diagram Patterns

Mermaid sequence diagram patterns for PHP DDD/CQRS/Event Sourcing projects.

## Command Flow (CQRS Write Side)

### Basic Command Dispatch

```mermaid
sequenceDiagram
    participant C as Controller/Action
    participant CB as CommandBus
    participant MW as Middleware
    participant H as CommandHandler
    participant R as Repository
    participant A as Aggregate
    participant ES as EventStore

    C->>CB: dispatch(CreateOrderCommand)
    CB->>MW: handle(command, next)
    Note over MW: Validation, Auth, Logging
    MW->>H: __invoke(CreateOrderCommand)

    H->>A: Order::create(customerId, lines)
    Note over A: Apply business rules
    A-->>H: Order (with uncommitted events)

    H->>R: save(order)
    R->>ES: append(streamId, events, expectedVersion)
    ES-->>R: void
    R-->>H: void

    H-->>MW: OrderId
    MW-->>CB: OrderId
    CB-->>C: OrderId
```

### Command with Domain Validation

```mermaid
sequenceDiagram
    participant C as Controller
    participant CB as CommandBus
    participant H as ConfirmOrderHandler
    participant R as OrderRepository
    participant A as Order Aggregate
    participant DS as DomainService

    C->>CB: dispatch(ConfirmOrderCommand)
    CB->>H: __invoke(command)

    H->>R: findById(orderId)
    R-->>H: Order

    H->>DS: validateOrderForConfirmation(order)

    alt Valid Order
        DS-->>H: void
        H->>A: confirm()
        Note over A: status = Confirmed
        Note over A: raise OrderConfirmedEvent
        H->>R: save(order)
        R-->>H: void
        H-->>CB: void
        CB-->>C: void
    else Invalid Order
        DS-->>H: throw DomainException
        H-->>CB: DomainException
        CB-->>C: 422 Unprocessable Entity
    end
```

### Command with Saga Coordination

```mermaid
sequenceDiagram
    participant C as Controller
    participant CB as CommandBus
    participant H as PlaceOrderHandler
    participant OR as OrderRepository
    participant A as Order
    participant EB as EventBus
    participant PH as PaymentHandler
    participant SH as StockHandler

    C->>CB: dispatch(PlaceOrderCommand)
    CB->>H: __invoke(command)
    H->>A: Order::create(...)
    H->>OR: save(order)
    OR-->>H: void

    H->>EB: publish(OrderCreatedEvent)

    par Process Payment
        EB->>PH: handle(OrderCreatedEvent)
        Note over PH: Reserve payment
        PH-->>EB: PaymentReservedEvent
    and Reserve Stock
        EB->>SH: handle(OrderCreatedEvent)
        Note over SH: Reserve inventory
        SH-->>EB: StockReservedEvent
    end

    H-->>CB: OrderId
    CB-->>C: 201 Created
```

## Query Flow (CQRS Read Side)

### Basic Query Dispatch

```mermaid
sequenceDiagram
    participant C as Controller/Action
    participant QB as QueryBus
    participant H as QueryHandler
    participant RM as ReadModel
    participant CA as Cache

    C->>QB: dispatch(GetOrderDetailsQuery)
    QB->>H: __invoke(query)

    H->>CA: get(order:{orderId})

    alt Cache Hit
        CA-->>H: OrderDetailsDTO
    else Cache Miss
        CA-->>H: null
        H->>RM: findOrderDetails(orderId)
        RM-->>H: OrderDetailsDTO
        H->>CA: set(order:{orderId}, dto, ttl: 300)
    end

    H-->>QB: OrderDetailsDTO
    QB-->>C: OrderDetailsDTO
```

### Paginated List Query

```mermaid
sequenceDiagram
    participant C as Controller
    participant QB as QueryBus
    participant H as ListOrdersHandler
    participant RM as ReadModel DB

    C->>QB: dispatch(ListOrdersQuery)
    Note over C: page=2, perPage=20,<br/>status=confirmed

    QB->>H: __invoke(query)

    H->>RM: SELECT * FROM order_list_view<br/>WHERE status = 'confirmed'<br/>ORDER BY created_at DESC<br/>LIMIT 20 OFFSET 20
    RM-->>H: rows[]

    H->>RM: SELECT COUNT(*) FROM order_list_view<br/>WHERE status = 'confirmed'
    RM-->>H: total = 156

    Note over H: Build PaginatedResult<br/>items, total, page, perPage

    H-->>QB: PaginatedResult
    QB-->>C: PaginatedResult
```

## Event Sourcing Patterns

### Aggregate Reconstitution

```mermaid
sequenceDiagram
    participant H as CommandHandler
    participant R as EventSourcedRepository
    participant ES as EventStore
    participant SS as SnapshotStore
    participant A as Order Aggregate

    H->>R: findById(orderId)

    R->>SS: load(orderId)

    alt Snapshot Exists
        SS-->>R: Snapshot (version=50, state)
        R->>ES: loadFromVersion(streamId, fromVersion=50)
        ES-->>R: events[51..55]
        R->>A: reconstitute(snapshot, events)
    else No Snapshot
        SS-->>R: null
        R->>ES: load(streamId)
        ES-->>R: events[1..55]
        R->>A: reconstitute(events)
    end

    Note over A: Replay events to rebuild state
    A-->>R: Order (version=55)
    R-->>H: Order
```

### Event Projection Flow

```mermaid
sequenceDiagram
    participant A as Aggregate
    participant ES as EventStore
    participant EB as EventBus/Queue
    participant P as Projector
    participant RM as Read Model DB
    participant PS as ProjectionState

    A->>ES: append(events)
    ES->>EB: publish(OrderConfirmedEvent)

    EB->>P: handle(OrderConfirmedEvent)

    P->>PS: getLastProcessedPosition()
    PS-->>P: position=1042

    Note over P: Check event position > 1042

    P->>RM: UPDATE order_list SET<br/>status='confirmed',<br/>confirmed_at=NOW()<br/>WHERE id = :orderId
    RM-->>P: void

    P->>PS: updatePosition(1043)
    PS-->>P: void

    P-->>EB: ack
```

### Full Event Sourcing Cycle

```mermaid
sequenceDiagram
    participant C as Controller
    participant CB as CommandBus
    participant H as Handler
    participant R as ES Repository
    participant ES as EventStore
    participant MQ as RabbitMQ
    participant W as Worker
    participant P1 as OrderListProjector
    participant P2 as CustomerStatsProjector
    participant RM as Read Model

    C->>CB: dispatch(ConfirmOrderCommand)
    CB->>H: __invoke(command)
    H->>R: findById(orderId)
    R->>ES: load(streamId)
    ES-->>R: events
    R-->>H: Order (reconstituted)

    H->>H: order->confirm()
    H->>R: save(order)
    R->>ES: append(OrderConfirmedEvent)
    ES-->>R: void
    R->>MQ: publish(OrderConfirmedEvent)

    H-->>CB: void
    CB-->>C: 200 OK

    Note over MQ: Async event delivery

    MQ->>W: deliver(OrderConfirmedEvent)

    par Order List Projection
        W->>P1: project(OrderConfirmedEvent)
        P1->>RM: UPDATE order_list...
    and Customer Stats Projection
        W->>P2: project(OrderConfirmedEvent)
        P2->>RM: UPDATE customer_stats...
    end
```

## Saga / Process Manager Patterns

### Orchestration Saga

```mermaid
sequenceDiagram
    participant EB as EventBus
    participant S as OrderFulfillmentSaga
    participant PB as PaymentBus
    participant IB as InventoryBus
    participant SB as ShippingBus
    participant SS as SagaStateStore

    EB->>S: handle(OrderCreatedEvent)
    S->>SS: save(sagaId, state=STARTED)

    S->>PB: dispatch(ReservePaymentCommand)
    PB-->>S: PaymentReservedEvent
    S->>SS: save(sagaId, state=PAYMENT_RESERVED)

    S->>IB: dispatch(ReserveStockCommand)
    IB-->>S: StockReservedEvent
    S->>SS: save(sagaId, state=STOCK_RESERVED)

    S->>SB: dispatch(CreateShipmentCommand)
    SB-->>S: ShipmentCreatedEvent
    S->>SS: save(sagaId, state=COMPLETED)

    S->>EB: publish(OrderFulfilledEvent)
```

### Saga with Compensation

```mermaid
sequenceDiagram
    participant S as OrderFulfillmentSaga
    participant PB as PaymentBus
    participant IB as InventoryBus
    participant SS as SagaStateStore

    S->>PB: dispatch(ReservePaymentCommand)
    PB-->>S: PaymentReservedEvent
    S->>SS: save(state=PAYMENT_RESERVED)

    S->>IB: dispatch(ReserveStockCommand)

    alt Stock Available
        IB-->>S: StockReservedEvent
        S->>SS: save(state=STOCK_RESERVED)
        Note over S: Continue with next step...
    else Out of Stock
        IB-->>S: StockUnavailableEvent
        S->>SS: save(state=COMPENSATING)
        Note over S: Begin compensation

        S->>PB: dispatch(ReleasePaymentCommand)
        PB-->>S: PaymentReleasedEvent

        S->>SS: save(state=COMPENSATED)
        S->>S: publish(OrderFailedEvent)
    end
```

### Choreography Saga

```mermaid
sequenceDiagram
    participant OA as Order Aggregate
    participant MQ as RabbitMQ
    participant PH as PaymentHandler
    participant PA as Payment Aggregate
    participant IH as InventoryHandler
    participant IA as Inventory Aggregate

    OA->>MQ: OrderCreatedEvent

    par Payment Processing
        MQ->>PH: consume(OrderCreatedEvent)
        PH->>PA: reservePayment(orderId, amount)
        PA->>MQ: PaymentReservedEvent
    and Inventory Processing
        MQ->>IH: consume(OrderCreatedEvent)
        IH->>IA: reserveStock(orderId, items)
        IA->>MQ: StockReservedEvent
    end

    Note over MQ: Both events published

    MQ->>OA: consume(PaymentReservedEvent)
    MQ->>OA: consume(StockReservedEvent)
    Note over OA: Check all preconditions met
    OA->>MQ: OrderReadyForShipmentEvent
```

## Async Patterns

### Event-Driven Worker Processing

```mermaid
sequenceDiagram
    participant API as API Service
    participant MQ as RabbitMQ
    participant W as Worker Process
    participant H as EventHandler
    participant EXT as External Service
    participant DLQ as Dead Letter Queue

    API->>MQ: publish(event, routing_key)
    Note over MQ: Exchange routes to queue

    MQ->>W: deliver(message)
    W->>H: handle(event)

    alt Success
        H->>EXT: call(payload)
        EXT-->>H: 200 OK
        H-->>W: void
        W->>MQ: ack(message)
    else Transient Failure
        H->>EXT: call(payload)
        EXT-->>H: 503 Unavailable
        H-->>W: throw RetryableException
        W->>MQ: nack(message, requeue=true)
        Note over MQ: Retry with backoff
    else Permanent Failure
        H->>EXT: call(payload)
        EXT-->>H: 400 Bad Request
        H-->>W: throw PermanentException
        W->>MQ: nack(message, requeue=false)
        MQ->>DLQ: route to DLQ
    end
```

### Scheduled Job Pattern

```mermaid
sequenceDiagram
    participant CRON as Scheduler (Cron)
    participant CMD as Console Command
    participant R as Repository
    participant CB as CommandBus
    participant H as Handler
    participant MQ as RabbitMQ

    CRON->>CMD: php bin/console app:expire-orders
    CMD->>R: findExpiredOrders(threshold)
    R-->>CMD: Order[] (pending > 24h)

    loop For each expired order
        CMD->>CB: dispatch(CancelOrderCommand)
        CB->>H: __invoke(command)
        H->>H: order->cancel(Reason::Expired)
        H->>MQ: publish(OrderCancelledEvent)
    end

    CMD-->>CRON: exit 0
```

## Error Handling in Sequences

### Optimistic Concurrency Conflict

```mermaid
sequenceDiagram
    participant H as Handler
    participant R as Repository
    participant ES as EventStore
    participant A as Aggregate

    H->>R: findById(orderId)
    R->>ES: load(streamId)
    ES-->>R: events (version=5)
    R-->>H: Order (version=5)

    H->>A: confirm()

    H->>R: save(order)
    R->>ES: append(events, expectedVersion=5)

    alt No Conflict
        ES-->>R: void
        R-->>H: void
    else Concurrent Modification
        ES-->>R: ConcurrencyException
        Note over R: Version is now 6

        R-->>H: ConcurrencyException
        Note over H: Retry: reload + re-apply

        H->>R: findById(orderId)
        R->>ES: load(streamId)
        ES-->>R: events (version=6)
        R-->>H: Order (version=6)
        H->>A: confirm()
        H->>R: save(order)
        R->>ES: append(events, expectedVersion=6)
        ES-->>R: void
    end
```

### Circuit Breaker Pattern

```mermaid
sequenceDiagram
    participant H as Handler
    participant CB as CircuitBreaker
    participant EXT as External API

    H->>CB: call(fn)

    alt Circuit Closed (Normal)
        CB->>EXT: request()
        EXT-->>CB: response
        CB-->>H: result
    else Circuit Open (Failing)
        Note over CB: Failures > threshold
        CB-->>H: CircuitOpenException
        Note over H: Return fallback / cached data
    else Circuit Half-Open (Testing)
        CB->>EXT: request()
        alt Success
            EXT-->>CB: response
            Note over CB: Reset failure count
            CB-->>H: result
        else Failure
            EXT-->>CB: error
            Note over CB: Reopen circuit
            CB-->>H: CircuitOpenException
        end
    end
```

## Common DDD Interaction Patterns

### Anti-Corruption Layer

```mermaid
sequenceDiagram
    participant H as OrderHandler
    participant ACL as ProductACL
    participant API as Catalog API
    participant VO as ProductSnapshot VO

    H->>ACL: getProductSnapshot(productId)
    ACL->>API: GET /products/{id}
    API-->>ACL: {"id": "...", "name": "...",<br/>"price": {"value": 2999, "currency": "USD"}}

    Note over ACL: Translate external model<br/>to domain value object

    ACL->>VO: new ProductSnapshot(...)
    VO-->>ACL: ProductSnapshot

    ACL-->>H: ProductSnapshot
    Note over H: Use domain VO, not external DTO
```

### Domain Event Notification

```mermaid
sequenceDiagram
    participant A as Order Aggregate
    participant H as Handler
    participant EB as EventBus
    participant N as NotificationHandler
    participant E as EmailAdapter
    participant L as AuditLogHandler
    participant AL as AuditLog

    A->>H: uncommittedEvents()
    H->>EB: publishAll(events)

    par Send Notification
        EB->>N: handle(OrderConfirmedEvent)
        N->>E: sendOrderConfirmation(orderId, email)
        E-->>N: void
    and Write Audit Log
        EB->>L: handle(OrderConfirmedEvent)
        L->>AL: log(action, aggregateId, userId)
        AL-->>L: void
    end
```

## Detection Patterns

```bash
# Check for sequence diagram documentation
Grep: "sequenceDiagram" --glob "**/*.md"

# Check for CQRS flow documentation
Grep: "CommandBus|QueryBus" --glob "**/docs/**/*.md"

# Check for saga patterns
Grep: "Saga|ProcessManager|Orchestrat" --glob "**/*.php"
Grep: "compensation|compensate" --glob "**/*.php"

# Check for async patterns
Grep: "RabbitMQ|AMQP|queue.*publish" --glob "**/*.php"
Grep: "dead.letter|DLQ|dlq" --glob "**/*.php"

# Warning: Missing interaction documentation
# If handlers exist but no sequence diagrams
Glob: **/Handler/**/*Handler.php
Grep: "sequenceDiagram" --glob "**/docs/**/*.md"
```

## Summary

| Pattern | When to Use | Key Participants | Async |
|---------|-------------|------------------|-------|
| **Command Flow** | Any write operation | Controller, Bus, Handler, Aggregate, Repository | No |
| **Query Flow** | Any read operation | Controller, Bus, Handler, ReadModel, Cache | No |
| **Aggregate Reconstitution** | Event-sourced load | Repository, EventStore, SnapshotStore, Aggregate | No |
| **Event Projection** | Read model sync | EventStore, Queue, Projector, ReadModel | Yes |
| **Full ES Cycle** | Complete write+project | All of the above combined | Partial |
| **Orchestration Saga** | Multi-step with central control | Saga, multiple Buses, SagaStateStore | Yes |
| **Compensation Saga** | Rollback on failure | Saga, Buses, compensation commands | Yes |
| **Choreography Saga** | Decoupled multi-step | Aggregates, Queue, Handlers | Yes |
| **Worker Processing** | Background jobs | API, Queue, Worker, Handler, DLQ | Yes |
| **Circuit Breaker** | Unreliable external calls | Handler, CircuitBreaker, External API | No |
| **Anti-Corruption Layer** | Cross-context integration | Handler, ACL, External API, Value Object | No |
| **Domain Event Notification** | Side effects after command | Aggregate, EventBus, multiple Handlers | Partial |
