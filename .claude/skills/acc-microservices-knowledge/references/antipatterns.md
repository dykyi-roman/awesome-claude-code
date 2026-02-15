# Microservices Antipatterns Reference

## Distributed Monolith

### Description

Services are deployed independently but tightly coupled through synchronous calls, shared libraries, or shared data. Changes to one service require coordinated changes in others.

### Symptoms

```bash
# Many synchronous HTTP calls between services
Grep: "HttpClient|Guzzle|curl" --glob "**/Application/**/*.php"

# Service A directly calls Service B's API in business logic
Grep: "->get\(|->post\(|->request\(" --glob "**/Application/**/*.php"

# Shared libraries with business logic
Grep: "shared-kernel|common-lib" --glob "composer.json"
```

### Detection Checklist

- [ ] Can each service be deployed independently?
- [ ] Does a change in Service A require changes in Service B?
- [ ] Are there more than 3 synchronous calls in a single request path?
- [ ] Do services share database connections or schemas?

### Fix

| Problem | Solution |
|---------|----------|
| Sync call chains | Replace with async events |
| Shared domain libraries | Extract to separate bounded contexts |
| Deployment coupling | Establish contract testing |
| Data coupling | Database per service + events |

## Shared Database

### Description

Multiple services read/write to the same database tables. This creates hidden coupling and prevents independent scaling and deployment.

### Symptoms

```bash
# Multiple services using same database
Grep: "DATABASE_URL|DB_HOST" --glob "**/.env*"

# Same table names across services
Grep: "orders|users|payments" --glob "**/migrations/**/*.php"

# Direct SQL to tables owned by other services
Grep: "SELECT.*FROM.*users|JOIN.*orders" --glob "**/Repository/**/*.php"
```

### Detection Checklist

- [ ] Does each service have its own database/schema?
- [ ] Are there cross-service JOINs?
- [ ] Can you drop one service's tables without affecting others?

### Fix

1. Identify table ownership — assign each table to one service
2. Create APIs for cross-service data access
3. Use events for data synchronization
4. Implement eventual consistency where needed

## Missing Service Boundaries (Anemic Services)

### Description

Services are split by technical layer (API service, business logic service, data service) instead of by business capability. Results in "distributed layers" not microservices.

### Symptoms

```bash
# Services named by technical concern
Grep: "api-service|data-service|auth-service" --glob "**/docker-compose*.yml"

# No domain logic in service — just CRUD
Glob: **/Service/**/*Service.php
# Check if services only delegate to repositories without business logic
```

### Detection Checklist

- [ ] Is each service aligned with a business capability?
- [ ] Does each service have its own domain model?
- [ ] Can a business stakeholder name what each service does?

### Fix

| Problem | Solution |
|---------|----------|
| Technical splitting | Re-align with bounded contexts |
| No domain logic | Enrich domain model |
| CRUD-only services | Identify business invariants |

## Chatty Communication (N+1 Service Calls)

### Description

A single user request triggers multiple sequential calls between services. Similar to N+1 database query problem but across network boundaries.

### Symptoms

```bash
# Multiple HTTP calls in a single handler
Grep: "->request\(|->get\(|->post\(" --glob "**/Handler/**/*.php"
# Check if same handler makes > 2 HTTP calls

# Sequential service calls in loop
Grep: "foreach.*->get\(|for.*->request\(" --glob "**/*.php"
```

### Example (Bad)

```php
// N+1: calling user service for each order
$orders = $this->orderService->getOrders();
foreach ($orders as $order) {
    $order['customer'] = $this->customerService->getCustomer($order['customer_id']); // N calls!
}
```

### Fix

```php
// Batch: single call with all IDs
$orders = $this->orderService->getOrders();
$customerIds = array_unique(array_column($orders, 'customer_id'));
$customers = $this->customerService->getCustomersByIds($customerIds); // 1 call

foreach ($orders as &$order) {
    $order['customer'] = $customers[$order['customer_id']] ?? null;
}
```

### Prevention Strategies

| Strategy | Description |
|----------|-------------|
| Batch APIs | Support fetching multiple resources in one call |
| API Composition | Aggregate at gateway level |
| Data denormalization | Store needed data locally via events |
| BFF pattern | Optimize queries per client type |

## No API Versioning Strategy

### Description

Services change their API contracts without versioning, causing consumer breakage. No deprecation process or backward compatibility policy.

### Symptoms

```bash
# No version in URL paths
Grep: "Route.*\/v[0-9]" --glob "**/*.php"
# If no results → no versioning

# No Accept header versioning
Grep: "Accept.*version|application/vnd" --glob "**/*.php"

# Breaking changes in API responses
# (manual review needed — check git history for response structure changes)
```

### Fix

| Approach | Example | Best For |
|----------|---------|----------|
| URI versioning | `/v1/orders`, `/v2/orders` | Simple, explicit |
| Header versioning | `Accept: application/vnd.api.v2+json` | Clean URIs |
| Query param | `?version=2` | Easy testing |
| Consumer-driven contracts | Pact tests | Contract safety |

### Versioning Rules

1. Never remove fields from responses (additive changes only)
2. New required request fields need a new version
3. Deprecate with `Sunset` header before removing
4. Run contract tests for all consumers

## Missing Circuit Breakers on External Calls

### Description

Services call external dependencies (other services, APIs, databases) without circuit breakers. A single slow or failing dependency can cascade failures across the entire system.

### Symptoms

```bash
# HTTP calls without circuit breaker wrapper
Grep: "->request\(|->get\(|curl_exec" --glob "**/Infrastructure/**/*.php"
# Check if calls are wrapped in CircuitBreaker

# No timeout configuration
Grep: "timeout|connect_timeout" --glob "**/Infrastructure/**/*.php"
# If no results → no timeouts configured

# No fallback responses
Grep: "catch.*Exception.*return.*default|fallback" --glob "**/Infrastructure/**/*.php"
```

### Detection Checklist

- [ ] Are all external HTTP calls wrapped in circuit breakers?
- [ ] Are timeouts configured for every external call?
- [ ] Is there a fallback strategy for each external dependency?
- [ ] Are circuit breaker metrics monitored?

### Fix

```php
// Wrap all external calls in circuit breaker
$result = $this->circuitBreaker->execute(
    serviceName: 'payment-service',
    action: fn() => $this->paymentClient->processPayment($paymentData),
    fallback: fn() => PaymentResult::deferred('Payment service temporarily unavailable'),
);
```

### Required Resilience Stack

| Component | Purpose |
|-----------|---------|
| Circuit Breaker | Fail fast when dependency is down |
| Timeout | Prevent indefinite waiting |
| Retry | Handle transient failures |
| Bulkhead | Isolate failure domains |
| Fallback | Provide degraded response |

## Insufficient Monitoring

### Description

Services lack proper observability. When issues occur, it's impossible to trace requests across services or identify the failing component.

### Required Observability

| Layer | What to Monitor |
|-------|----------------|
| Distributed Tracing | Request flow across services (Jaeger, Zipkin) |
| Metrics | Latency, error rate, throughput per service (Prometheus) |
| Logging | Structured logs with correlation IDs (ELK, Loki) |
| Health Checks | Liveness and readiness probes per service |
| Alerting | SLO-based alerts (error budget, latency percentiles) |
