---
description: Generate design patterns. Creates Circuit Breaker, Retry, Rate Limiter, Bulkhead, Strategy, State, Chain of Responsibility, Decorator, Null Object, Template Method, Visitor, Iterator, Memento, Adapter, Facade, Proxy, Composite, Bridge, Flyweight, Builder, Object Pool, Factory, Outbox, Saga, ADR, Correlation Context patterns.
allowed-tools: Read, Write, Edit, Glob, Grep, Task
model: opus
argument-hint: <pattern-name> <ComponentName> [-- additional instructions]
---

# Generate Design Patterns

Generate design pattern implementations for PHP 8.5 with tests and DI configuration.

## Input Parsing

Parse `$ARGUMENTS` to extract pattern name, component name, and optional meta-instructions:

```
Format: <pattern-name> <ComponentName> [-- <meta-instructions>]

Examples:
- /acc-generate-patterns circuit-breaker PaymentGateway
- /acc-generate-patterns strategy PaymentProcessor
- /acc-generate-patterns saga CheckoutWorkflow
- /acc-generate-patterns builder UserProfile -- with validation
```

**Parsing rules:**
1. First part = **pattern name** (required, see list below)
2. Second part = **component/context name** (required)
3. After ` -- ` = **meta-instructions** (optional customizations)

## Supported Patterns

### Stability Patterns (Resilience)

| Pattern | Alias | Use Case |
|---------|-------|----------|
| `circuit-breaker` | `cb` | Fail-fast for failing external services |
| `retry` | `retry-pattern` | Transient failure handling with backoff |
| `rate-limiter` | `throttle` | Request throttling, token bucket |
| `bulkhead` | `isolation` | Resource isolation, prevent cascade |

### Behavioral Patterns (Algorithms)

| Pattern | Alias | Use Case |
|---------|-------|----------|
| `strategy` | - | Interchangeable algorithms |
| `state` | `state-machine` | State transitions, FSM |
| `chain-of-responsibility` | `chain`, `middleware` | Handler pipelines |
| `decorator` | `wrapper` | Dynamic behavior extension |
| `null-object` | `null` | Null check elimination |
| `template-method` | `template` | Algorithm skeleton with hooks |
| `visitor` | - | Operations without class modification |
| `iterator` | `collection` | Sequential access to collections |
| `memento` | `snapshot`, `undo` | State saving/restoration, undo/redo |

### Structural Patterns (GoF)

| Pattern | Alias | Use Case |
|---------|-------|----------|
| `adapter` | `wrapper` | Incompatible interface integration |
| `facade` | - | Simplified subsystem interface |
| `proxy` | `lazy-proxy`, `caching-proxy` | Access control, lazy loading, caching |
| `composite` | `tree` | Tree structures, uniform treatment |
| `bridge` | - | Abstraction-implementation decoupling |
| `flyweight` | - | Memory optimization via shared state |

### Creational Patterns (Construction)

| Pattern | Alias | Use Case |
|---------|-------|----------|
| `builder` | `fluent-builder` | Step-by-step construction |
| `object-pool` | `pool` | Connection/resource reuse |
| `factory` | `factory-method` | Encapsulated instantiation |

### Integration Patterns (Distributed)

| Pattern | Alias | Use Case |
|---------|-------|----------|
| `outbox` | `transactional-outbox` | Reliable message publishing |
| `saga` | `distributed-saga` | Distributed transaction coordination |
| `action` | `adr-action` | ADR Action (HTTP entry point) |
| `responder` | `adr-responder` | ADR Responder (HTTP response) |
| `correlation-context` | `correlation-id`, `request-id` | Correlation ID propagation middleware |

## Pre-flight Check

1. Verify valid pattern name:
   - If not provided, ask user which pattern to generate
   - If invalid, show list of supported patterns

2. Check project structure:
   - Read `composer.json` for namespace configuration
   - Determine target directory based on pattern type

## Instructions

Use the `acc-pattern-generator` coordinator to generate pattern implementations:

```
Task tool with subagent_type="acc-pattern-generator"
prompt: "Generate [PATTERN] for [COMPONENT_NAME]. [META-INSTRUCTIONS if provided]

Requirements:
1. PHP 8.5 with declare(strict_types=1)
2. PSR-12 coding style
3. Final readonly classes where appropriate
4. Constructor property promotion
5. Include interfaces
6. Include unit tests
7. Include DI container configuration
8. Include usage examples"
```

## Generation Examples

### Stability Patterns

#### Circuit Breaker
```bash
/acc-generate-patterns circuit-breaker PaymentGateway
/acc-generate-patterns cb ExternalApi -- with Redis state storage
```

Generates:
```
src/Infrastructure/Stability/CircuitBreaker/
├── CircuitBreakerInterface.php
├── CircuitBreaker.php
├── CircuitState.php (enum: Closed, Open, HalfOpen)
├── CircuitBreakerConfig.php
└── Exception/
    └── CircuitOpenException.php
```

#### Retry
```bash
/acc-generate-patterns retry HttpClient
/acc-generate-patterns retry-pattern ApiGateway -- exponential backoff with jitter
```

Generates:
- RetryInterface, RetryPolicy
- Backoff strategies (linear, exponential, jitter)
- Max attempts, delay configuration

#### Rate Limiter
```bash
/acc-generate-patterns rate-limiter ApiEndpoint
/acc-generate-patterns throttle UserRequests -- sliding window
```

Generates:
- RateLimiterInterface
- Token bucket / Sliding window implementations
- Redis storage adapter

#### Bulkhead
```bash
/acc-generate-patterns bulkhead DatabasePool
/acc-generate-patterns isolation QueueWorker
```

Generates:
- BulkheadInterface
- Semaphore-based isolation
- Concurrent request limiting

### Behavioral Patterns

#### Strategy
```bash
/acc-generate-patterns strategy PaymentProcessor
/acc-generate-patterns strategy Discount -- with composite
```

Generates:
```
src/Domain/Payment/Strategy/
├── PaymentStrategyInterface.php
├── CardPaymentStrategy.php
├── PayPalPaymentStrategy.php
├── CryptoPaymentStrategy.php
└── PaymentStrategyFactory.php
```

#### State
```bash
/acc-generate-patterns state Order
/acc-generate-patterns state-machine Document -- with transitions
```

Generates:
- StateInterface, Context
- Concrete states (Draft, Pending, Approved, etc.)
- Transition validation

#### Chain of Responsibility
```bash
/acc-generate-patterns chain ValidationPipeline
/acc-generate-patterns middleware RequestHandler
```

Generates:
- HandlerInterface
- AbstractHandler
- Concrete handlers
- Pipeline builder

#### Decorator
```bash
/acc-generate-patterns decorator Logger
/acc-generate-patterns wrapper Cache -- with metrics
```

Generates:
- Component interface
- Base component
- Decorator classes

#### Null Object
```bash
/acc-generate-patterns null-object Logger
/acc-generate-patterns null Notifier
```

Generates:
- Interface
- Real implementation
- Null implementation (no-op)

#### Template Method
```bash
/acc-generate-patterns template-method DataImporter
/acc-generate-patterns template ReportGenerator -- with CSV and PDF variants
```

Generates:
- Abstract class with final template method
- Hook methods for customization
- Concrete implementations

#### Visitor
```bash
/acc-generate-patterns visitor PriceCalculator
/acc-generate-patterns visitor ExportFormatter -- with JSON and XML
```

Generates:
- VisitorInterface with visit methods
- Element interface with accept method
- Concrete visitor implementations

#### Iterator
```bash
/acc-generate-patterns iterator OrderCollection
/acc-generate-patterns collection FilteredProducts -- with pagination
```

Generates:
- Collection class (IteratorAggregate)
- Custom Iterator implementation
- Filter/pagination support

#### Memento
```bash
/acc-generate-patterns memento DocumentEditor
/acc-generate-patterns undo FormWizard -- with history limit
```

Generates:
- Originator (creates/restores mementos)
- Memento (immutable state snapshot)
- History/Caretaker (manages memento stack)

### Structural Patterns (GoF)

#### Adapter
```bash
/acc-generate-patterns adapter StripePayment
/acc-generate-patterns wrapper TwilioSms -- with domain interface
```

Generates:
```
src/Domain/Payment/Port/
├── PaymentGatewayInterface.php
src/Infrastructure/Payment/Adapter/
├── StripePaymentAdapter.php
```

#### Facade
```bash
/acc-generate-patterns facade OrderProcessing
/acc-generate-patterns facade UserOnboarding -- with validation
```

Generates:
- Simplified interface to complex subsystem
- Delegates to internal services

#### Proxy
```bash
/acc-generate-patterns proxy ReportService
/acc-generate-patterns lazy-proxy HeavyRepository -- with caching
```

Generates:
- Subject interface
- Proxy implementation (Lazy/Caching/Access)

#### Composite
```bash
/acc-generate-patterns composite MenuTree
/acc-generate-patterns tree PermissionHierarchy
```

Generates:
- Component interface
- Leaf and Composite nodes
- Recursive operations

#### Bridge
```bash
/acc-generate-patterns bridge Notification
/acc-generate-patterns bridge Renderer -- with HTML and PDF
```

Generates:
- Abstraction with implementor reference
- Implementor interface
- Concrete implementors

#### Flyweight
```bash
/acc-generate-patterns flyweight Currency
/acc-generate-patterns flyweight Icon -- with factory
```

Generates:
- Flyweight interface (immutable)
- Concrete flyweight
- Factory with caching pool

### Creational Patterns

#### Builder
```bash
/acc-generate-patterns builder UserProfile
/acc-generate-patterns fluent-builder QueryCriteria -- with validation
```

Generates:
```
src/Domain/User/Builder/
├── UserProfileBuilder.php
├── UserProfileDirector.php (optional)
└── UserProfile.php
```

#### Object Pool
```bash
/acc-generate-patterns object-pool DatabaseConnection
/acc-generate-patterns pool RedisConnection
```

Generates:
- ObjectPoolInterface
- Pool implementation
- Acquire/release methods
- Max size configuration

#### Factory
```bash
/acc-generate-patterns factory Notification
/acc-generate-patterns factory-method Report
```

Generates:
- FactoryInterface
- Factory implementation
- Product interface and implementations

### Integration Patterns

#### Outbox
```bash
/acc-generate-patterns outbox Order
/acc-generate-patterns transactional-outbox Event
```

Generates:
```
src/Infrastructure/Messaging/Outbox/
├── OutboxMessage.php
├── OutboxRepository.php
├── OutboxProcessor.php
└── OutboxMiddleware.php
```

#### Saga
```bash
/acc-generate-patterns saga Checkout
/acc-generate-patterns distributed-saga OrderFulfillment
```

Generates:
- SagaInterface
- SagaStep with compensating actions
- SagaOrchestrator
- Step implementations

#### ADR Action/Responder
```bash
/acc-generate-patterns action CreateOrder
/acc-generate-patterns responder OrderResponse
```

Generates:
- Single-responsibility Action class
- Request DTO
- Responder with response building

#### Correlation Context
```bash
/acc-generate-patterns correlation-context
/acc-generate-patterns correlation-id Order -- with Symfony Messenger
```

Generates:
```
src/Domain/Shared/Correlation/
├── CorrelationId.php
└── CorrelationContext.php
src/Presentation/Middleware/
└── CorrelationContextMiddleware.php
src/Infrastructure/Logging/
└── CorrelationLogProcessor.php
src/Infrastructure/Messaging/
└── CorrelationMessageStamp.php
```

## Expected Output

### Generated Files Summary

```
Generated Circuit Breaker: PaymentGateway

Files created:
├── src/Infrastructure/Stability/CircuitBreaker/
│   ├── CircuitBreakerInterface.php
│   ├── PaymentGatewayCircuitBreaker.php
│   ├── CircuitState.php
│   └── Exception/CircuitOpenException.php
└── tests/Unit/Infrastructure/Stability/CircuitBreaker/
    └── PaymentGatewayCircuitBreakerTest.php
```

### DI Container Configuration

```php
// config/services.php
return [
    CircuitBreakerInterface::class => [
        'class' => PaymentGatewayCircuitBreaker::class,
        'arguments' => [
            'failureThreshold' => 5,
            'recoveryTimeout' => 30,
            'successThreshold' => 2,
        ],
    ],
];
```

### Usage Example

```php
$circuitBreaker = new PaymentGatewayCircuitBreaker(
    failureThreshold: 5,
    recoveryTimeout: 30,
);

try {
    $result = $circuitBreaker->execute(
        fn() => $paymentGateway->processPayment($payment)
    );
} catch (CircuitOpenException $e) {
    // Handle circuit open state
}
```

## Multiple Patterns

Generate related patterns together:

```bash
# Generate resilience stack
/acc-generate-patterns circuit-breaker PaymentApi
/acc-generate-patterns retry PaymentApi -- compose with circuit breaker

# Generate ADR trio
/acc-generate-patterns action CreateUser
/acc-generate-patterns responder UserResponse
```

## Usage Examples

```bash
/acc-generate-patterns circuit-breaker PaymentGateway
/acc-generate-patterns strategy PaymentProcessor
/acc-generate-patterns adapter StripePayment
/acc-generate-patterns facade OrderProcessing
/acc-generate-patterns template-method DataImporter
/acc-generate-patterns visitor PriceCalculator
/acc-generate-patterns saga CheckoutWorkflow
/acc-generate-patterns builder UserProfile -- with validation steps
/acc-generate-patterns outbox Order -- with Doctrine integration
```
