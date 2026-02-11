---
name: acc-create-correlation-context
description: Generates Correlation ID propagation components for PHP 8.5. Creates PSR-15 middleware, Monolog processor, message bus header propagation, and CorrelationContext value object. Includes unit tests.
---

# Correlation Context Generator

Creates Correlation ID propagation infrastructure for distributed PHP applications.

## When to Use

- Need to trace requests across multiple services or layers
- Log entries from different components must be linked together
- Async flows (RabbitMQ, Symfony Messenger) lose request context
- Debugging distributed systems requires end-to-end tracing
- Implementing observability and distributed tracing

## Generated Components

| Component | Layer | Path | Purpose |
|-----------|-------|------|---------|
| `CorrelationId` | Domain/Shared | `src/Domain/Shared/Correlation/CorrelationId.php` | UUID-based Value Object |
| `CorrelationContext` | Domain/Shared | `src/Domain/Shared/Correlation/CorrelationContext.php` | Immutable context holder |
| `CorrelationContextMiddleware` | Presentation | `src/Presentation/Middleware/CorrelationContextMiddleware.php` | PSR-15 middleware |
| `CorrelationLogProcessor` | Infrastructure | `src/Infrastructure/Logging/CorrelationLogProcessor.php` | Monolog processor |
| `CorrelationMessageStamp` | Infrastructure | `src/Infrastructure/Messaging/CorrelationMessageStamp.php` | Message bus stamp |
| Unit tests | Tests | `tests/Unit/...` | Tests for all components |

## Component Characteristics

### CorrelationId Value Object
- Immutable, `final readonly` class in Domain layer
- UUID v4 based with factory method `generate()`
- Constructor accepts existing string UUID
- Implements `Stringable` and `JsonSerializable`
- Equality comparison via `equals()` method

### CorrelationContext
- Immutable context holder with `correlationId`, `causationId`, optional `userId`
- Factory method `create()` generates new correlation ID
- Factory method `fromRequest()` extracts from PSR-7 request headers
- Wither methods: `withCausationId()`, `withUserId()`

### CorrelationContextMiddleware (PSR-15)
- Extracts `X-Correlation-ID` header from incoming request (or generates new UUID)
- Also reads `X-Causation-ID` if present
- Stores `CorrelationContext` as request attribute
- Adds `X-Correlation-ID` to response headers
- Thread-safe via request attribute passing (no global state)

### CorrelationLogProcessor (Monolog)
- Implements Monolog `ProcessorInterface`
- Adds `correlation_id`, `causation_id` to every log record `extra` field
- Reads context from a `CorrelationContextHolder` (request-scoped)

### CorrelationMessageStamp
- Implements Symfony Messenger `StampInterface` (or custom stamp interface)
- Carries `correlationId` and `causationId` through message bus
- Used by middleware to propagate context into async handlers
- AMQP header mapping for RabbitMQ interoperability

---

## Generation Process

### Step 1: Generate Domain Layer

**Path:** `src/Domain/Shared/Correlation/`

1. `CorrelationId.php` -- UUID-based Value Object
2. `CorrelationContext.php` -- Immutable context holder

Use templates from `references/templates.md` (Domain section).

### Step 2: Generate Presentation Layer

**Path:** `src/Presentation/Middleware/`

1. `CorrelationContextMiddleware.php` -- PSR-15 middleware

Use templates from `references/templates.md` (Presentation section).

### Step 3: Generate Infrastructure Layer

**Path:** `src/Infrastructure/Logging/` and `src/Infrastructure/Messaging/`

1. `CorrelationLogProcessor.php` -- Monolog processor
2. `CorrelationMessageStamp.php` -- Message bus stamp

Use templates from `references/templates.md` (Infrastructure section).

### Step 4: Generate Tests

**Path:** `tests/Unit/Domain/Shared/Correlation/` and `tests/Unit/Presentation/Middleware/` and `tests/Unit/Infrastructure/`

1. `CorrelationIdTest.php`
2. `CorrelationContextTest.php`
3. `CorrelationContextMiddlewareTest.php`
4. `CorrelationLogProcessorTest.php`

Use templates from `references/templates.md` (Tests section).

---

## File Placement

| Component | Default Path |
|-----------|--------------|
| CorrelationId | `src/Domain/Shared/Correlation/CorrelationId.php` |
| CorrelationContext | `src/Domain/Shared/Correlation/CorrelationContext.php` |
| Middleware | `src/Presentation/Middleware/CorrelationContextMiddleware.php` |
| Log Processor | `src/Infrastructure/Logging/CorrelationLogProcessor.php` |
| Message Stamp | `src/Infrastructure/Messaging/CorrelationMessageStamp.php` |
| Tests | `tests/Unit/{layer}/...Test.php` |

Adapt paths to match existing project structure detected via:
```
Glob: src/Domain/**/*.php
Glob: src/Presentation/**/*.php
Glob: src/Infrastructure/**/*.php
```

---

## Quick Template Reference

### CorrelationId (Value Object)
```php
final readonly class CorrelationId implements \Stringable, \JsonSerializable
{
    public function __construct(public string $value) {}
    public static function generate(): self { /* UUID v4 */ }
    public function equals(self $other): bool { /* comparison */ }
}
```

### CorrelationContext (Context Holder)
```php
final readonly class CorrelationContext
{
    public function __construct(
        public CorrelationId $correlationId,
        public ?string $causationId = null,
        public ?string $userId = null,
    ) {}
    public static function create(): self { /* new with generated ID */ }
    public static function fromRequest(ServerRequestInterface $request): self { /* extract headers */ }
}
```

### Middleware (PSR-15)
```php
final readonly class CorrelationContextMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $context = CorrelationContext::fromRequest($request);
        $request = $request->withAttribute(CorrelationContext::class, $context);
        $response = $handler->handle($request);
        return $response->withHeader('X-Correlation-ID', $context->correlationId->value);
    }
}
```

See `references/templates.md` for complete implementations and `references/examples.md` for integration examples.

---

## Usage Example

### Middleware Registration (Slim/Mezzio)
```php
$app->add(new CorrelationContextMiddleware());
```

### DI Configuration
```php
return [
    CorrelationContextMiddleware::class => autowire(),
    CorrelationLogProcessor::class => autowire(),
];
```

### Reading Context in Handler
```php
$context = $request->getAttribute(CorrelationContext::class);
$this->logger->info('Processing order', ['orderId' => $orderId]);
// Log automatically includes correlation_id via processor
```

See `references/examples.md` for Symfony, Laravel, and message bus integration.
