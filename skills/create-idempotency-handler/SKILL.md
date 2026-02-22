---
name: create-idempotency-handler
description: Generates Idempotency Handler for PHP 8.4. Creates PSR-15 middleware with Redis-backed deduplication, IdempotencyKey value object, and storage interface. Includes unit tests.
---

# Idempotency Handler Generator

Creates idempotency handling infrastructure for safe request deduplication.

## When to Use

| Scenario | Example |
|----------|---------|
| Payment processing | Prevent duplicate charges on retry |
| Order creation | Avoid duplicate orders from network retries |
| Webhook handling | Deduplicate incoming webhook deliveries |
| API mutations | Ensure POST/PUT/PATCH safety on retry |

## Component Characteristics

### IdempotencyKey
- Value Object validating UUID v4 format
- Immutable, self-validating on construction
- Extracted from `Idempotency-Key` HTTP header

### IdempotencyStorageInterface
- Storage contract for idempotency records
- Methods: `exists()`, `store()`, `get()`, `remove()`
- TTL-based expiration support

### RedisIdempotencyStorage
- Redis SETNX implementation for atomic check-and-store
- Configurable TTL for automatic key expiration
- Stores serialized response for replay

### IdempotencyMiddleware
- PSR-15 middleware intercepting requests
- Checks for existing idempotency key before processing
- Stores response after successful processing
- Returns cached response on duplicate request

### IdempotencyException
- Thrown when duplicate request detected without stored response
- Contains the conflicting idempotency key

---

## Generation Process

### Step 1: Generate Core Components

**Path:** `src/Infrastructure/Idempotency/`

1. `IdempotencyKey.php` — Value Object with UUID validation
2. `IdempotencyException.php` — Duplicate request exception
3. `StoredResponse.php` — Serializable response wrapper

### Step 2: Generate Storage Layer

**Path:** `src/Infrastructure/Idempotency/`

1. `IdempotencyStorageInterface.php` — Storage contract
2. `RedisIdempotencyStorage.php` — Redis SETNX + TTL implementation

### Step 3: Generate Middleware

**Path:** `src/Infrastructure/Idempotency/`

1. `IdempotencyMiddleware.php` — PSR-15 middleware

### Step 4: Generate Tests

1. `IdempotencyKeyTest.php` — Value Object validation tests
2. `IdempotencyMiddlewareTest.php` — Middleware behavior tests

---

## File Placement

| Component | Path |
|-----------|------|
| All Classes | `src/Infrastructure/Idempotency/` |
| Unit Tests | `tests/Unit/Infrastructure/Idempotency/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Value Object | `IdempotencyKey` | `IdempotencyKey` |
| Storage Interface | `IdempotencyStorageInterface` | `IdempotencyStorageInterface` |
| Redis Storage | `RedisIdempotencyStorage` | `RedisIdempotencyStorage` |
| Middleware | `IdempotencyMiddleware` | `IdempotencyMiddleware` |
| Response VO | `StoredResponse` | `StoredResponse` |
| Exception | `IdempotencyException` | `IdempotencyException` |
| Test | `{ClassName}Test` | `IdempotencyKeyTest` |

---

## Quick Template Reference

### IdempotencyKey

```php
final readonly class IdempotencyKey
{
    public function __construct(public string $value)
    {
        // Validates UUID v4 format
    }

    public static function fromHeader(string $headerValue): self;
    public function toString(): string;
}
```

### IdempotencyStorageInterface

```php
interface IdempotencyStorageInterface
{
    public function exists(IdempotencyKey $key): bool;
    public function store(IdempotencyKey $key, StoredResponse $response, int $ttl): void;
    public function get(IdempotencyKey $key): ?StoredResponse;
    public function remove(IdempotencyKey $key): void;
}
```

### IdempotencyMiddleware

```php
final readonly class IdempotencyMiddleware implements MiddlewareInterface
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
$middleware = new IdempotencyMiddleware(
    storage: $redisStorage,
    ttl: 86400,
    headerName: 'Idempotency-Key'
);

// Client sends: POST /orders with header Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
// First request: processes and stores response
// Retry request: returns cached response immediately
```

---

## Request Flow

```
Request ──→ Extract Idempotency-Key header
                │
         Key exists in storage?
           │              │
          YES             NO
           │              │
    Return stored    Process request
     response           │
                   Store response
                        │
                   Return response
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No TTL on keys | Storage grows unbounded | Set TTL (e.g., 24h) |
| In-memory storage | Lost on restart, no clustering | Use Redis or database |
| Idempotency on GET | GET is already idempotent | Only apply to mutations |
| Missing key validation | Accept invalid keys | Validate UUID format |
| No response caching | Cannot replay response | Store full response |
| Race conditions | Concurrent duplicates | Use SETNX atomic operation |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — IdempotencyKey, StorageInterface, RedisStorage, Middleware templates
- `references/examples.md` — API integration examples and tests
