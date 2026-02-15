---
name: acc-create-idempotent-consumer
description: Generates Idempotent Consumer components for PHP 8.4. Creates message deduplication infrastructure with idempotency key management, storage backends, middleware, and unit tests.
---

# Idempotent Consumer Generator

Creates Idempotent Consumer pattern infrastructure for exactly-once message processing guarantees.

## When to Use

| Scenario | Example |
|----------|---------|
| Payment processing | Prevent double charges on message replay |
| Inventory updates | Avoid duplicate stock deductions |
| Event handlers | Process domain events exactly once |
| Webhook processing | Handle duplicate webhook deliveries |
| Message queue consumers | Deduplicate redelivered messages |

## Component Characteristics

### IdempotencyKey
- Value object combining messageId + handlerName
- Deterministic key generation
- Immutable with toString() representation

### IdempotencyStoreInterface
- Application layer port
- has(IdempotencyKey): bool — check if already processed
- mark(IdempotencyKey, DateTimeImmutable ttl): void — mark as processed
- remove(IdempotencyKey): void — remove entry (for reprocessing)

### DatabaseIdempotencyStore
- PDO-based implementation
- TTL-based automatic cleanup
- Unique constraint prevents race conditions

### RedisIdempotencyStore
- Redis SETNX-based implementation
- TTL via Redis EXPIRE
- Atomic check-and-set

### IdempotentConsumerMiddleware
- Wraps message handler
- Checks idempotency before processing
- Marks as processed after success
- Returns ProcessingResult enum

### ProcessingResult
- Enum: Processed, Duplicate, Failed
- Includes original result data on success
- Includes reason on duplicate/failure

---

## Generation Process

### Step 1: Analyze Request

Determine:
- Storage backend (Database, Redis, or both)
- TTL for idempotency keys (default: 7 days)
- Integration point (middleware, decorator, manual)

### Step 2: Generate Core Components

1. **Domain Layer** (`src/Domain/Shared/Idempotency/`)
   - `IdempotencyKey.php` — Key value object
   - `ProcessingResult.php` — Result value object with status
   - `ProcessingStatus.php` — Status enum (Processed/Duplicate/Failed)

2. **Application Layer** (`src/Application/Shared/Idempotency/`)
   - `IdempotencyStoreInterface.php` — Storage port
   - `IdempotentConsumerMiddleware.php` — Middleware wrapper

3. **Infrastructure Layer** (`src/Infrastructure/Idempotency/`)
   - `DatabaseIdempotencyStore.php` — PDO implementation
   - `RedisIdempotencyStore.php` — Redis implementation
   - Database migration

4. **Tests**
   - `IdempotencyKeyTest.php`
   - `ProcessingResultTest.php`
   - `IdempotentConsumerMiddlewareTest.php`
   - `DatabaseIdempotencyStoreTest.php`

---

## File Placement

| Layer | Path |
|-------|------|
| Domain Types | `src/Domain/Shared/Idempotency/` |
| Application Port | `src/Application/Shared/Idempotency/` |
| Infrastructure | `src/Infrastructure/Idempotency/` |
| Unit Tests | `tests/Unit/{Layer}/{Path}/` |

---

## Key Principles

### Idempotency Strategy
1. Generate deterministic key from message ID + handler name
2. Check store BEFORE processing
3. Mark as processed AFTER successful handling
4. Use database unique constraint as safety net
5. TTL cleanup prevents unbounded growth

### Race Condition Handling
1. Use INSERT ... ON CONFLICT (database)
2. Use SETNX (Redis)
3. If duplicate detected mid-processing, return Duplicate result

### TTL Management
1. Default TTL: 7 days (configurable)
2. Cleanup via cron/scheduled command
3. Redis handles TTL automatically via EXPIRE

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Key VO | `IdempotencyKey` | `IdempotencyKey` |
| Result VO | `ProcessingResult` | `ProcessingResult` |
| Status Enum | `ProcessingStatus` | `ProcessingStatus` |
| Store Interface | `IdempotencyStoreInterface` | `IdempotencyStoreInterface` |
| DB Store | `DatabaseIdempotencyStore` | `DatabaseIdempotencyStore` |
| Redis Store | `RedisIdempotencyStore` | `RedisIdempotencyStore` |
| Middleware | `IdempotentConsumerMiddleware` | `IdempotentConsumerMiddleware` |
| Test | `{ClassName}Test` | `IdempotencyKeyTest` |

---

## Quick Template Reference

### IdempotencyKey

```php
final readonly class IdempotencyKey
{
    public function __construct(
        public string $messageId,
        public string $handlerName,
    ) {}

    public static function fromMessage(string $messageId, string $handlerName): self;
    public function toString(): string;
    public function equals(self $other): bool;
}
```

### IdempotencyStoreInterface

```php
interface IdempotencyStoreInterface
{
    public function has(IdempotencyKey $key): bool;
    public function mark(IdempotencyKey $key, \DateTimeImmutable $expiresAt): void;
    public function remove(IdempotencyKey $key): void;
}
```

### Usage

```php
$middleware = new IdempotentConsumerMiddleware($store);

$result = $middleware->process(
    key: IdempotencyKey::fromMessage($message->id, 'handle_payment'),
    handler: fn() => $paymentHandler->handle($message),
    ttl: new \DateTimeImmutable('+7 days')
);

match ($result->status) {
    ProcessingStatus::Processed => $logger->info('Processed'),
    ProcessingStatus::Duplicate => $logger->info('Skipped duplicate'),
    ProcessingStatus::Failed => $logger->error('Failed', ['error' => $result->error]),
};
```

---

## Database Schema

```sql
CREATE TABLE idempotency_keys (
    key VARCHAR(255) PRIMARY KEY,
    handler_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMP(6) NOT NULL,
    expires_at TIMESTAMP(6) NOT NULL
);

CREATE INDEX idx_idempotency_expires ON idempotency_keys (expires_at);
```

---

## References

For complete PHP templates and test examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — Payment handler example and unit tests
