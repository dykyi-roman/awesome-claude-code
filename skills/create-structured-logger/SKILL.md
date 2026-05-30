---
name: create-structured-logger
description: Generates Structured Logger for PHP 8.4. Creates PSR-3 structured logging setup with Monolog processors, correlation ID propagation, and context middleware. Includes unit tests.
---

# Structured Logger Generator

Creates structured logging infrastructure for observability and request tracing.

## When to Use

| Scenario | Example |
|----------|---------|
| Distributed tracing | Correlate logs across microservices |
| Request debugging | Track full request lifecycle |
| Audit logging | Structured records with context |
| Error investigation | Rich context in error logs |

## Component Characteristics

### CorrelationId
- Value Object wrapping UUIDv4
- Immutable, self-validating
- Propagated via `X-Request-ID` header

### CorrelationIdProcessor
- Monolog processor adding `correlation_id` to every record
- Reads from CorrelationIdHolder thread-local storage
- Zero-config: auto-enriches all log entries

### RequestContextProcessor
- Monolog processor adding request metadata
- Captures method, URI, IP, user-agent
- Enables filtering logs by request attributes

### CorrelationIdMiddleware
- PSR-15 middleware extracting or generating X-Request-ID
- Stores in CorrelationIdHolder for downstream use
- Adds correlation ID to response headers

### CorrelationIdHolder
- Static thread-local storage for correlation ID
- Set once per request, available globally
- Reset after request completes

---

## Generation Process

### Step 1: Generate Core Components

Place alongside other logging / observability infrastructure.

1. `CorrelationId.php` — Value Object with UUID validation
2. `CorrelationIdHolder.php` — Thread-local correlation ID storage

### Step 2: Generate Monolog Processors

Place in a sibling `Processor/` sub-folder of the logging folder.

1. `CorrelationIdProcessor.php` — Adds correlation_id to log records
2. `RequestContextProcessor.php` — Adds request context to log records

### Step 3: Generate Middleware

Co-located with the core components in the logging folder.

1. `CorrelationIdMiddleware.php` — PSR-15 middleware for correlation ID

### Step 4: Generate Tests

1. `CorrelationIdTest.php` — Value Object tests
2. `CorrelationIdProcessorTest.php` — Processor enrichment tests
3. `CorrelationIdMiddlewareTest.php` — Middleware behavior tests

---

## File Placement

| Component | Path |
|-----------|------|
| Core Classes | `src/{architecture-path}/Logging/` |
| Processors | `src/{architecture-path}/Logging/Processor/` |
| Unit Tests | `tests/Unit/{architecture-path}/Logging/` |

> `{architecture-path}` represents your project's architecture-specific folders. Logger components typically live with other observability infrastructure. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Value Object | `CorrelationId` | `CorrelationId` |
| Holder | `CorrelationIdHolder` | `CorrelationIdHolder` |
| Processor | `{Context}Processor` | `CorrelationIdProcessor` |
| Middleware | `CorrelationIdMiddleware` | `CorrelationIdMiddleware` |
| Test | `{ClassName}Test` | `CorrelationIdTest` |

---

## Quick Template Reference

### CorrelationId

```php
final readonly class CorrelationId
{
    public function __construct(public string $value)
    {
        // Validates UUID v4 format
    }

    public static function generate(): self;
    public function toString(): string;
}
```

### CorrelationIdProcessor

```php
final readonly class CorrelationIdProcessor
{
    public function __invoke(LogRecord $record): LogRecord;
}
```

### CorrelationIdMiddleware

```php
final readonly class CorrelationIdMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface;
}
```

---

## Usage Example

```php
// Middleware extracts or generates correlation ID
$middleware = new CorrelationIdMiddleware(headerName: 'X-Request-ID');

// Monolog processor auto-enriches every log entry
$logger->pushProcessor(new CorrelationIdProcessor());
$logger->pushProcessor(new RequestContextProcessor($request));

// Log entry output:
// {"message":"Order created","correlation_id":"550e8400-...","method":"POST","uri":"/orders"}
```

---

## Log Flow

```
Request ──→ CorrelationIdMiddleware
                │
         Extract/Generate X-Request-ID
                │
         Store in CorrelationIdHolder
                │
         CorrelationIdProcessor ──→ Adds correlation_id to every log
         RequestContextProcessor ──→ Adds method, URI, IP to every log
                │
         Response ──→ Add X-Request-ID header
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Manual correlation IDs | Inconsistent, easy to forget | Auto-enrich via processor |
| Unstructured logs | Cannot query or filter | Use structured JSON format |
| No request context | Cannot trace request flow | Add request processor |
| Global mutable logger | Thread safety issues | Use holder with request scope |
| Missing response header | Client cannot correlate | Return X-Request-ID in response |
| No holder cleanup | Memory leak between requests | Reset holder after request |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — CorrelationId, Processors, Middleware, Holder templates
- `references/examples.md` — Service integration examples and tests
