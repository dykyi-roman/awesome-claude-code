---
name: acc-map-async-flows
description: Finds queue publishing (RabbitMQ, Redis), event dispatching, webhooks, and scheduled tasks. Documents synchronous-to-asynchronous boundaries, message formats, consumer chains, and retry policies.
---

# Async Flow Mapper

## Overview

Identifies all asynchronous communication patterns in the codebase — message queues, event dispatching, webhooks, scheduled tasks, and background jobs. Documents the sync-to-async boundaries, message formats, consumer chains, and error handling strategies.

## Detection Patterns

### Message Queue Publishing

```bash
# RabbitMQ (php-amqplib, Symfony Messenger)
Grep: "AMQPMessage|AMQPChannel|AMQPConnection" --glob "**/*.php"
Grep: "basic_publish|queue_declare|exchange_declare" --glob "**/*.php"

# Symfony Messenger
Grep: "MessageBusInterface|->dispatch\\(" --glob "**/*.php"
Grep: "#\\[AsMessageHandler\\]" --glob "**/*.php"
Grep: "Envelope|Stamp" --glob "**/*.php"

# Laravel Queue
Grep: "implements ShouldQueue" --glob "**/*.php"
Grep: "dispatch\\(new|Queue::push" --glob "**/*.php"

# Redis queues
Grep: "Redis::.*push|->lpush|->rpush" --glob "**/*.php"
Grep: "Predis|PhpRedis|redis" --glob "**/*.php"

# Generic publish patterns
Grep: "->publish\\(|->enqueue\\(|->sendToQueue" --glob "**/*.php"
```

### Event Dispatching

```bash
# Symfony EventDispatcher
Grep: "EventDispatcherInterface|->dispatch\\(" --glob "**/*.php"
Grep: "#\\[AsEventListener\\(" --glob "**/*.php"
Grep: "implements EventSubscriberInterface" --glob "**/*.php"

# Domain Events
Grep: "DomainEvent|->recordEvent|->raise" --glob "**/Domain/**/*.php"
Grep: "EventBus|DomainEventPublisher" --glob "**/*.php"

# Laravel Events
Grep: "event\\(new|Event::dispatch" --glob "**/*.php"
Grep: "class.*Listener" --glob "**/Listeners/**/*.php"
```

### Webhooks

```bash
# Outgoing webhooks
Grep: "webhook|Webhook" --glob "**/*.php"
Grep: "->post\\(.*callback|->send.*notification" --glob "**/*.php"

# Incoming webhook handlers
Grep: "function.*webhook|#\\[Route.*webhook" --glob "**/*.php"

# Webhook retry/delivery tracking
Grep: "WebhookDelivery|delivery_attempts|retry_after" --glob "**/*.php"
```

### Scheduled Tasks / Cron

```bash
# Symfony Scheduler
Grep: "#\\[AsCronTask\\]|#\\[AsPeriodicTask\\]" --glob "**/*.php"
Grep: "RecurringMessage|Schedule" --glob "**/*.php"

# Laravel Scheduler
Grep: "->command\\(|->call\\(|->job\\(" --glob "**/Console/Kernel.php"

# Custom schedulers
Grep: "cron|schedule|periodic|interval" --glob "config/**/*.{php,yaml,yml}"
```

### Background Jobs

```bash
# Process forking
Grep: "pcntl_fork|proc_open|Process::" --glob "**/*.php"

# Async operations
Grep: "async|promise|Future|Deferred" --glob "**/*.php"

# Worker patterns
Grep: "class.*Worker|class.*Consumer|class.*Processor" --glob "**/*.php"
Grep: "function consume|function process|function work" --glob "**/*.php"
```

## Analysis Process

### Step 1: Map Sync-Async Boundaries

For each message/event dispatch found:
1. **Read the publisher** — what triggers the async operation
2. **Read the message class** — what data is sent
3. **Find the consumer/handler** — what processes the message
4. **Check transport config** — queue name, exchange, routing

### Step 2: Trace Consumer Chains

```
Event Published → Handler 1 → may publish Event 2 → Handler 2 → ...
```

```bash
# Find what handlers dispatch
Grep: "->dispatch\\(|->publish\\(" --glob "**/Handler/**/*.php"
Grep: "->dispatch\\(|->publish\\(" --glob "**/Listener/**/*.php"
```

### Step 3: Document Error Handling

```bash
# Retry configuration
Grep: "retry|RetryStrategy|maxRetries|max_retries" --glob "**/*.php"
Grep: "retry:" --glob "config/**/*.yaml"

# Dead letter queue
Grep: "dead_letter|failed_queue|DLQ" --glob "**/*.php"
Grep: "dead_letter" --glob "config/**/*.yaml"

# Error handling in consumers
Grep: "catch.*Exception|->reject|->nack" --glob "**/Handler/**/*.php"
```

## Output Format

```markdown
## Async Communication Map

### Overview

| Type | Count | Transport |
|------|-------|-----------|
| Queue Messages | 8 | RabbitMQ (Symfony Messenger) |
| Domain Events | 12 | In-process + async relay |
| Webhooks (outgoing) | 3 | HTTP POST |
| Scheduled Tasks | 5 | Symfony Scheduler |

### Sync-Async Boundaries

```
[Sync World]                    [Async World]

CreateOrderUseCase
  ├── save(order)
  └── dispatch(OrderCreated) ──→ Queue: "orders"
                                   ├── SendConfirmationEmail
                                   ├── ReserveInventory
                                   └── NotifyAnalytics

ProcessPayment
  └── dispatch(PaymentReceived)→ Queue: "payments"
                                   ├── UpdateOrderStatus
                                   └── SendReceipt
```

### Message Catalog

| Message | Publisher | Consumer(s) | Queue | Async |
|---------|-----------|-------------|-------|-------|
| OrderCreated | CreateOrderUseCase | EmailHandler, InventoryHandler | orders | Yes |
| PaymentReceived | PaymentService | OrderStatusHandler, ReceiptHandler | payments | Yes |
| UserRegistered | RegisterUseCase | WelcomeEmailHandler | users | Yes |
| DailyReport | Scheduler (02:00) | ReportGenerator | reports | Yes |

### Consumer Chains

```
OrderCreated
  └── InventoryHandler
        └── dispatches: InventoryReserved
              └── WarehouseHandler
                    └── dispatches: PackingStarted
```

### Queue Configuration

| Queue | Exchange | Routing Key | Consumers | Prefetch |
|-------|----------|-------------|-----------|----------|
| orders | order_exchange | order.* | 3 | 10 |
| payments | payment_exchange | payment.# | 2 | 5 |
| notifications | notify_exchange | notify.email | 5 | 20 |

### Error Handling

| Message | Retry | Max Attempts | Dead Letter | Fallback |
|---------|-------|-------------|-------------|----------|
| OrderCreated | Exponential backoff | 3 | orders_dlq | Log + Alert |
| PaymentReceived | Fixed delay 5s | 5 | payments_dlq | Manual review |
| EmailNotification | Fixed delay 10s | 3 | None | Silent drop |

### Scheduled Tasks

| Schedule | Task | Description | Duration |
|----------|------|-------------|----------|
| 0 2 * * * | DailyReportCommand | Generate daily reports | ~5 min |
| */5 * * * * | HealthCheckCommand | Service health check | ~10 sec |
| 0 0 * * 0 | CleanupCommand | Remove expired data | ~15 min |

### Webhook Endpoints

| Direction | URL/Endpoint | Trigger | Payload |
|-----------|-------------|---------|---------|
| Outgoing | partner-api/notify | OrderShipped | {orderId, trackingNo} |
| Incoming | /webhooks/payment | Payment provider | {transactionId, status} |
```

## Async Flow Quality Indicators

| Indicator | Good | Warning |
|-----------|------|---------|
| Message idempotency | Handlers are idempotent | No deduplication |
| Error handling | Retry + DLQ + alerting | Silent failure |
| Message format | Typed message classes | Array/JSON strings |
| Consumer isolation | Each handler does one thing | Handler chains in one |
| Monitoring | Queue depth metrics | No monitoring |

## Integration

This skill is used by:
- `acc-data-flow-analyst` — documents async communication paths
- `acc-trace-request-lifecycle` — identifies where sync becomes async
- `acc-explain-business-process` — shows async steps in workflows
