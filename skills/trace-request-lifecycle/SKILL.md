---
name: acc-trace-request-lifecycle
description: Traces full request lifecycle from Router through Middleware, Controller, UseCase, Repository to Response. Documents HTTP methods, routes, middleware stack, response codes, and error handling paths.
---

# Request Lifecycle Tracer

## Overview

Traces the complete lifecycle of an HTTP request or CLI command through all application layers — from entry point through middleware, handler, business logic, persistence, and back to response. Documents the full chain with data transformations at each step.

## Tracing Process

### Step 1: Identify the Request Entry

```bash
# Find route definition for the target endpoint
Grep: "#\\[Route\\(" --glob "**/*.php" -A 2
Grep: "Route::(get|post|put|delete)" --glob "**/routes/*.php"

# Find the handler for this route
# Read the route config or controller to identify the handler method
```

### Step 2: Trace Middleware Stack

```bash
# Symfony middleware (event listeners on kernel.request)
Grep: "kernel.request|kernel.controller|kernel.response" --glob "**/*.php"
Grep: "implements EventSubscriberInterface" --glob "**/*.php"

# Laravel middleware
Grep: "class.*Middleware" --glob "**/Middleware/**/*.php"
Grep: "'middleware'" --glob "**/Kernel.php"

# PSR-15 middleware
Grep: "implements MiddlewareInterface" --glob "**/*.php"

# Authentication middleware
Grep: "authenticat|JWT|Bearer|token" --glob "**/Middleware/**/*.php"

# Authorization middleware
Grep: "authoriz|permission|role|access" --glob "**/Middleware/**/*.php"
```

### Step 3: Trace Controller/Action

```bash
# Read the handler method
Read: controller/action file

# Find what it receives (Request object/DTO)
Grep: "function.*\\(.*Request|function.*\\(.*DTO|function.*\\(.*Command" in handler

# Find what it calls (service/use case)
Grep: "\\$this->.*->handle|\\$this->.*->execute|\\$this->.*->dispatch" in handler

# Find response construction
Grep: "return.*Response|return.*JsonResponse|return.*json\\(" in handler
```

### Step 4: Trace Use Case / Service

```bash
# Read the use case/service method
Read: use case file

# Find domain operations
Grep: "\\$this->.*Repository->find|\\$this->.*->save" in use case

# Find domain method calls
Grep: "\\$.*->create|\\$.*->update|\\$.*->process" in use case

# Find event dispatching
Grep: "dispatch|publish|raise" in use case
```

### Step 5: Trace Repository Operations

```bash
# Read repository implementation
Grep: "implements.*Repository" --glob "**/Infrastructure/**/*.php"

# Find query patterns
Grep: "->createQueryBuilder|->find\\(|->findOneBy" in repository

# Find persistence operations
Grep: "->persist|->flush|->save|->insert|->update" in repository
```

### Step 6: Trace Response Construction

```bash
# Response mapping
Grep: "->toArray|->toResponse|->jsonSerialize" in handler/response class

# Error responses
Grep: "ExceptionListener|ExceptionHandler|ErrorHandler" --glob "**/*.php"

# HTTP status codes used
Grep: "Response\\(.*[0-9]{3}|status.*[0-9]{3}|HTTP_" --glob "**/*.php"
```

## Output Format

```markdown
## Request Lifecycle

### Endpoint: POST /api/orders

#### Route Definition
- **Method:** POST
- **Path:** /api/orders
- **Controller:** `CreateOrderAction::__invoke`
- **Route file:** `config/routes/api.yaml:15`

#### Request Flow

```
Client Request (POST /api/orders, JSON body)
    │
    ▼
[1] Router (matches POST /api/orders → CreateOrderAction)
    │
    ▼
[2] Middleware Stack
    ├── CorsMiddleware — adds CORS headers
    ├── AuthenticationMiddleware — validates JWT token
    ├── RateLimitMiddleware — checks rate limits
    └── JsonRequestMiddleware — parses JSON body
    │
    ▼
[3] Controller/Action: CreateOrderAction::__invoke(CreateOrderRequest $request)
    │  Input: CreateOrderRequest (validated DTO)
    │  - customerId: string (from JWT)
    │  - items: array [{productId, quantity}]
    │  - shippingAddress: {street, city, zip}
    │
    ▼
[4] Use Case: CreateOrderUseCase::execute(CreateOrderCommand $command)
    │  Transforms: CreateOrderRequest → CreateOrderCommand
    │
    ├── [4a] CustomerRepository::find(customerId)
    │         Returns: Customer entity
    │
    ├── [4b] ProductRepository::findByIds(productIds)
    │         Returns: Product[] entities
    │
    ├── [4c] Order::create(customer, items, address)
    │         Domain logic: validates, calculates total
    │         Raises: OrderCreated event
    │
    ├── [4d] OrderRepository::save(order)
    │         Persists: INSERT into orders + order_items
    │
    └── [4e] EventBus::dispatch(OrderCreated)
             Async: sends to message queue
    │
    ▼
[5] Response Construction
    │  Transforms: Order entity → OrderResponse DTO
    │  OrderResponse: {id, status, total, items[], createdAt}
    │
    ▼
[6] HTTP Response
    Status: 201 Created
    Headers: Content-Type: application/json, Location: /api/orders/{id}
    Body: {"id": "...", "status": "pending", "total": 150.00, ...}
```

#### Error Paths

| Error | Where | HTTP Status | Response |
|-------|-------|-------------|----------|
| Invalid JSON | Middleware [2] | 400 | {"error": "Invalid JSON"} |
| Unauthorized | Middleware [2] | 401 | {"error": "Token expired"} |
| Validation fail | Action [3] | 422 | {"errors": {"items": "..."}} |
| Customer not found | UseCase [4a] | 404 | {"error": "Customer not found"} |
| Out of stock | Domain [4c] | 409 | {"error": "Product out of stock"} |
| DB error | Repository [4d] | 500 | {"error": "Internal error"} |

#### Data Transformation Chain

```
JSON Body → CreateOrderRequest (DTO)
  → CreateOrderCommand (CQRS Command)
    → Order Entity (Domain)
      → OrderResponse (DTO)
        → JSON Response
```

#### Key Files in Chain

| Step | File | Line | Purpose |
|------|------|------|---------|
| Route | config/routes/api.yaml | 15 | Route definition |
| Action | src/Api/Action/CreateOrderAction.php | 22 | HTTP handler |
| Request | src/Api/Request/CreateOrderRequest.php | 1 | Input validation |
| Command | src/Application/Command/CreateOrderCommand.php | 1 | CQRS command |
| UseCase | src/Application/UseCase/CreateOrderUseCase.php | 15 | Orchestration |
| Entity | src/Domain/Order/Order.php | 45 | Domain logic |
| Repo | src/Infrastructure/Repository/DoctrineOrderRepo.php | 30 | Persistence |
| Response | src/Api/Response/OrderResponse.php | 1 | Output mapping |
```

## Lifecycle Quality Indicators

| Indicator | Good | Warning |
|-----------|------|---------|
| Input validation | At boundary (Request/DTO) | In controller logic |
| Business logic | In Domain/UseCase | In controller |
| Error handling | Exception handler | Try-catch everywhere |
| Response mapping | Dedicated Response class | Array building in controller |
| Side effects | Via events (async) | Direct calls in handler |

## Integration

This skill is used by:
- `acc-data-flow-analyst` — provides lifecycle documentation
- `acc-trace-data-transformation` — traces DTO transformations
- `acc-explain-business-process` — maps processes to request flows
