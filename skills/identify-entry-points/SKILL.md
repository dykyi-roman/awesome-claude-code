---
name: acc-identify-entry-points
description: Finds application entry points — Controllers, Actions, Console Commands, Event Handlers, Message Consumers, route definitions, middleware, and scheduled tasks. Maps HTTP/CLI/async entry points to their handlers.
---

# Entry Points Identifier

## Overview

Identifies all entry points into the application — HTTP routes, CLI commands, event handlers, message consumers, and scheduled tasks. Maps each entry point to its handler and the business operation it triggers.

## Detection Patterns

### HTTP Entry Points

#### Controllers / Actions

```bash
# Symfony controllers
Grep: "#\\[Route\\(" --glob "**/*.php"
Grep: "@Route\\(" --glob "**/*.php"
Grep: "extends.*AbstractController" --glob "**/*.php"

# Laravel controllers
Grep: "extends Controller" --glob "**/Controller/**/*.php"
Grep: "Route::(get|post|put|patch|delete)" --glob "**/routes/*.php"

# ADR Actions
Grep: "__invoke.*Request" --glob "**/Action/**/*.php"
Grep: "class.*Action" --glob "**/*.php"

# Slim/custom route handlers
Grep: "->(?:get|post|put|delete|patch)\(" --glob "**/routes*.php"
```

#### Route Definitions

```bash
# Symfony YAML routes
Grep: "path:|prefix:" --glob "config/routes*.yaml"

# Symfony attribute routes (extract path and methods)
Grep: "#\\[Route\\('[^']+'" --glob "**/*.php"

# Laravel routes
Grep: "Route::" --glob "routes/*.php"

# API resource routes
Grep: "apiResource|Route::resource" --glob "routes/*.php"
```

#### Middleware

```bash
# Symfony event subscribers acting as middleware
Grep: "implements EventSubscriberInterface" --glob "**/*.php"
Grep: "kernel.request|kernel.response|kernel.exception" --glob "**/*.php"

# Laravel middleware
Grep: "class.*Middleware|implements Middleware" --glob "**/*.php"
Grep: "'middleware'" --glob "routes/*.php"

# PSR-15 middleware
Grep: "implements MiddlewareInterface" --glob "**/*.php"
```

### CLI Entry Points

```bash
# Symfony console commands
Grep: "extends Command" --glob "**/*.php"
Grep: "#\\[AsCommand\\(" --glob "**/*.php"
Grep: "protected.*\\$defaultName" --glob "**/*.php"

# Laravel artisan commands
Grep: "extends Command" --glob "**/Console/**/*.php"
Grep: "protected.*\\$signature" --glob "**/*.php"

# Custom CLI scripts
Glob: "bin/*"
Glob: "scripts/*.php"
```

### Event/Message Entry Points

```bash
# Symfony messenger handlers
Grep: "#\\[AsMessageHandler\\]" --glob "**/*.php"
Grep: "implements MessageHandlerInterface" --glob "**/*.php"
Grep: "__invoke.*Message|__invoke.*Command|__invoke.*Event" --glob "**/*.php"

# Symfony event listeners
Grep: "#\\[AsEventListener\\(" --glob "**/*.php"
Grep: "implements EventSubscriberInterface" --glob "**/*.php"

# Laravel event listeners
Grep: "class.*Listener" --glob "**/Listeners/**/*.php"
Grep: "implements ShouldQueue" --glob "**/*.php"

# Custom event handlers
Grep: "implements.*Handler|implements.*Listener|implements.*Subscriber" --glob "**/*.php"

# RabbitMQ consumers
Grep: "ConsumerInterface|implements.*Consumer" --glob "**/*.php"
```

### Scheduled Tasks

```bash
# Symfony scheduler
Grep: "#\\[AsSchedule\\]|#\\[AsCronTask\\]" --glob "**/*.php"
Grep: "RecurringMessage::every|RecurringMessage::cron" --glob "**/*.php"

# Laravel scheduler
Grep: "->command\\(|->call\\(|->job\\(" --glob "**/Kernel.php"
Grep: "->cron\\(|->daily\\(|->hourly\\(" --glob "**/*.php"

# Cron definitions
Glob: "crontab*"
Glob: "config/scheduler*.{php,yaml}"
```

## Analysis Process

1. **Scan** — Find all entry points using detection patterns above
2. **Classify** — Group by type (HTTP, CLI, Event, Scheduled)
3. **Map** — Trace each entry point to its handler/use case
4. **Document** — Build entry point catalog

### Handler Mapping

For each entry point, trace the chain:

```
Entry Point → Middleware/Guard → Handler → UseCase/Service → Domain
```

```bash
# Find what the handler calls
# Read the handler method body
Read: handler file

# Look for service/use case invocations
Grep: "\$this->[a-z]+(Handler|Service|UseCase|Bus)" in handler file

# Trace command/query dispatch
Grep: "->dispatch\(|->handle\(|->execute\(" in handler file
```

## Output Format

```markdown
## Entry Points Map

### HTTP Endpoints

| Method | Route | Handler | Operation | Auth |
|--------|-------|---------|-----------|------|
| GET | /api/orders | OrderController::list | List orders | JWT |
| POST | /api/orders | CreateOrderAction::__invoke | Create order | JWT |
| GET | /api/orders/{id} | OrderController::show | Get order | JWT |
| PUT | /api/orders/{id}/status | UpdateOrderStatusAction | Change status | JWT + Role |

### CLI Commands

| Command | Handler | Purpose | Schedule |
|---------|---------|---------|----------|
| app:import-orders | ImportOrdersCommand | Import from CSV | Daily 02:00 |
| app:cleanup-expired | CleanupCommand | Remove expired | Hourly |

### Event Handlers

| Event/Message | Handler | Trigger | Async |
|---------------|---------|---------|-------|
| OrderCreated | SendConfirmationEmail | After order create | Yes (queue) |
| PaymentReceived | UpdateOrderStatus | After payment | Yes (queue) |
| UserRegistered | SendWelcomeEmail | After registration | Yes (queue) |

### Message Consumers

| Queue | Consumer | Message Type | Processing |
|-------|----------|-------------|-----------|
| orders | OrderConsumer | OrderCommand | Sequential |
| notifications | NotificationConsumer | NotificationMessage | Parallel |

### Scheduled Tasks

| Schedule | Task | Description |
|----------|------|-------------|
| 0 2 * * * | ImportOrdersCommand | Daily order import |
| */5 * * * * | HealthCheckCommand | Health monitoring |

### Entry Point Flow
```
HTTP Request → Middleware Stack → Controller/Action → UseCase → Domain → Response
CLI Command → Input Parsing → Handler → Service → Domain → Output
Event → Listener/Handler → UseCase → Domain → Side Effects
Queue Message → Consumer → Handler → UseCase → Domain → Ack
```
```

## Entry Point Quality Indicators

| Indicator | Good | Warning |
|-----------|------|---------|
| Handler responsibility | Delegates to UseCase | Contains business logic |
| Input validation | Uses typed Request/DTO | Raw array access |
| Auth check | Attribute/middleware | Inline if-checks |
| Error handling | Exception handler | Try-catch in handler |
| Response format | Typed Response/DTO | Array/string |

## Integration

This skill is used by:
- `acc-codebase-navigator` — builds complete entry point catalog
- `acc-trace-request-lifecycle` — starts from identified entry points
- `acc-explain-business-process` — maps entry points to business operations
