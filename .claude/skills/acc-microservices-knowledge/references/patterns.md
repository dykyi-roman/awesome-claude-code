# Microservices Patterns Reference

## Service Mesh

### Overview

A service mesh is a dedicated infrastructure layer for handling service-to-service communication. It provides observability, traffic management, and security without changing application code.

```
┌─────────────────────────────────────────────────────┐
│                    SERVICE MESH                       │
│                                                       │
│   ┌──────────┐  sidecar  ┌──────────────────┐       │
│   │ Service A │◄────────▶│  Envoy Proxy     │       │
│   └──────────┘           └────────┬─────────┘       │
│                                    │                  │
│                            ┌───────▼───────┐         │
│                            │  Control Plane │         │
│                            │  (Istio/Linkerd)│        │
│                            └───────┬───────┘         │
│                                    │                  │
│   ┌──────────┐  sidecar  ┌────────▼─────────┐       │
│   │ Service B │◄────────▶│  Envoy Proxy     │       │
│   └──────────┘           └──────────────────┘       │
└─────────────────────────────────────────────────────┘
```

### Service Mesh Capabilities

| Capability | Description |
|-----------|-------------|
| Traffic Management | Load balancing, routing rules, retries, timeouts |
| Security | mTLS, access policies, certificate management |
| Observability | Distributed tracing, metrics, access logs |
| Resilience | Circuit breaking, rate limiting, fault injection |

### Service Mesh Implementations

| Implementation | Language | Key Features |
|---------------|----------|--------------|
| Istio | Go | Full-featured, Envoy sidecar, complex |
| Linkerd | Rust/Go | Lightweight, simple, Kubernetes-native |
| Consul Connect | Go | Multi-platform, service discovery built-in |
| Kuma | Go | Multi-zone, universal (K8s + VMs) |

## API Gateway Implementation Patterns

### Simple Proxy Gateway

Routes requests directly to backend services:

```
Client → Gateway → Service
```

- 1:1 mapping of routes to services
- Gateway handles: TLS termination, authentication, rate limiting
- No request transformation

### Gateway Aggregation

Combines multiple backend calls into a single response:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Gateway;

final readonly class OrderDetailsAggregator
{
    public function __construct(
        private OrderServiceClient $orderService,
        private CustomerServiceClient $customerService,
        private PaymentServiceClient $paymentService,
    ) {}

    public function getOrderDetails(string $orderId): array
    {
        // Parallel calls to multiple services
        $orderFuture = $this->orderService->getOrderAsync($orderId);
        $customerFuture = null;
        $paymentFuture = null;

        $order = $orderFuture->wait();
        $customerFuture = $this->customerService->getCustomerAsync($order['customer_id']);
        $paymentFuture = $this->paymentService->getPaymentAsync($orderId);

        return [
            'order' => $order,
            'customer' => $customerFuture->wait(),
            'payment' => $paymentFuture->wait(),
        ];
    }
}
```

### Backend for Frontend (BFF)

Dedicated gateway per client type:

```
Mobile App  → Mobile BFF Gateway  → Services
Web App     → Web BFF Gateway     → Services
Third-party → Public API Gateway  → Services
```

| BFF Type | Optimized For |
|----------|---------------|
| Mobile BFF | Bandwidth, battery, minimal payloads |
| Web BFF | Rich UI data, pagination, filtering |
| Public API | Versioning, rate limiting, documentation |

## Service Discovery Detailed

### Client-Side Discovery

```
┌──────────┐     ┌──────────────────┐
│  Client   │────▶│ Service Registry │
│           │     │ (Consul/Eureka)  │
│           │     └────────┬─────────┘
│           │              │ returns instances
│           │◄─────────────┘
│           │
│           │  direct call to selected instance
│           │────▶ Service Instance A (10.0.0.1:8080)
│           │────▶ Service Instance B (10.0.0.2:8080)
└──────────┘
```

### Server-Side Discovery

```
┌──────────┐     ┌──────────────┐     ┌──────────────────┐
│  Client   │────▶│ Load Balancer│────▶│ Service Registry │
│           │     │ (Nginx/ALB)  │     │ (Consul/etcd)    │
└──────────┘     └──────┬───────┘     └──────────────────┘
                        │
                        │ routes to healthy instance
                        ▼
              Service Instance A / B / C
```

### PHP Service Registry Client

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Discovery;

final readonly class ConsulServiceDiscovery implements ServiceDiscoveryInterface
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private string $consulUrl,
    ) {}

    /** @return list<ServiceInstance> */
    public function discover(string $serviceName): array
    {
        $response = $this->httpClient->request(
            'GET',
            sprintf('%s/v1/health/service/%s?passing=true', $this->consulUrl, $serviceName),
        );

        $entries = json_decode($response->getBody()->getContents(), true, 512, JSON_THROW_ON_ERROR);

        return array_map(
            static fn(array $entry): ServiceInstance => new ServiceInstance(
                id: $entry['Service']['ID'],
                host: $entry['Service']['Address'],
                port: $entry['Service']['Port'],
                metadata: $entry['Service']['Meta'] ?? [],
            ),
            $entries,
        );
    }
}
```

## Inter-Service Communication

### Synchronous: REST with Resilience

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Client;

final readonly class ResilientServiceClient
{
    public function __construct(
        private HttpClientInterface $httpClient,
        private CircuitBreakerInterface $circuitBreaker,
        private RetryPolicyInterface $retryPolicy,
        private string $baseUrl,
    ) {}

    /**
     * @throws ServiceUnavailableException
     */
    public function get(string $path): array
    {
        return $this->circuitBreaker->execute(
            fn() => $this->retryPolicy->execute(
                fn() => $this->doRequest('GET', $path),
            ),
        );
    }

    private function doRequest(string $method, string $path): array
    {
        $response = $this->httpClient->request($method, $this->baseUrl . $path, [
            'headers' => [
                'Accept' => 'application/json',
                'X-Correlation-ID' => CorrelationContext::current()->correlationId(),
            ],
            'timeout' => 5,
        ]);

        if ($response->getStatusCode() >= 500) {
            throw new ServiceUnavailableException($path, $response->getStatusCode());
        }

        return json_decode($response->getBody()->getContents(), true, 512, JSON_THROW_ON_ERROR);
    }
}
```

### Synchronous: gRPC

| Aspect | REST | gRPC |
|--------|------|------|
| Protocol | HTTP/1.1 or HTTP/2 | HTTP/2 |
| Payload | JSON (text) | Protobuf (binary) |
| Contract | OpenAPI (optional) | .proto (required) |
| Streaming | Limited (SSE, WebSocket) | Bidirectional built-in |
| Code generation | Optional | Required |
| Browser support | Native | Requires grpc-web |

### Asynchronous: Event-Based

```
Service A publishes event → Message Broker → Service B consumes event
                                           → Service C consumes event
```

Key advantages:
- Temporal decoupling (services don't need to be online simultaneously)
- Spatial decoupling (services don't need to know each other's location)
- Failure isolation (one service failure doesn't cascade)

## Data Consistency Patterns

### Saga Pattern (Choreography)

```
Order Service → OrderCreated event
    → Payment Service processes payment → PaymentCompleted event
        → Inventory Service reserves stock → StockReserved event
            → Shipping Service creates shipment → ShipmentCreated event
```

Compensation on failure:
```
Shipping fails → StockReserved compensated → PaymentRefunded → OrderCancelled
```

### Saga Pattern (Orchestration)

```
Saga Orchestrator:
    1. Create Order → Order Service
    2. Process Payment → Payment Service
    3. Reserve Stock → Inventory Service
    4. Create Shipment → Shipping Service

On failure at step 3:
    Compensate step 2: Refund Payment
    Compensate step 1: Cancel Order
```

### API Composition for Queries

```php
<?php

declare(strict_types=1);

namespace Application\Query;

final readonly class GetCustomerOrdersHandler
{
    public function __construct(
        private CustomerServiceClient $customerService,
        private OrderServiceClient $orderService,
        private PaymentServiceClient $paymentService,
    ) {}

    public function handle(GetCustomerOrdersQuery $query): CustomerOrdersView
    {
        $customer = $this->customerService->getCustomer($query->customerId);
        $orders = $this->orderService->getOrdersByCustomer($query->customerId);
        $payments = $this->paymentService->getPaymentsByCustomer($query->customerId);

        return new CustomerOrdersView(
            customer: CustomerDTO::fromServiceResponse($customer),
            orders: array_map(
                fn(array $order) => OrderWithPaymentDTO::merge(
                    $order,
                    $payments[$order['id']] ?? null,
                ),
                $orders,
            ),
        );
    }
}
```

### Database per Service Enforcement

| Rule | Description |
|------|-------------|
| Private schema | Each service has its own schema/database |
| No shared tables | Services never access each other's tables |
| API-only access | Data shared only via APIs or events |
| Own migrations | Each service manages its own schema migrations |
| Separate credentials | Each service has unique database credentials |
