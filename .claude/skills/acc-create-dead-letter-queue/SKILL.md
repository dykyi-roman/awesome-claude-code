---
name: acc-create-dead-letter-queue
description: Generates Dead Letter Queue components for PHP 8.4. Creates failed message capture, retry strategy with exponential backoff, failure classification, and unit tests.
---

# Dead Letter Queue Generator

Creates Dead Letter Queue pattern infrastructure for capturing and retrying failed messages.

## When to Use

| Scenario | Example |
|----------|---------|
| Poison messages | Messages that always cause handler failures |
| Processing failures | Temporary infrastructure issues (DB down, timeout) |
| Audit trail | Track all failed message processing attempts |
| Retry mechanism | Automatic retry with exponential backoff |
| Monitoring | Alert on DLQ threshold exceeded |

## Component Characteristics

### DeadLetterMessage
- Entity capturing failed message details
- Original message body, headers, routing key
- Error message and stack trace
- Attempt count and timestamps
- Failure classification (Transient, Permanent, Unknown)

### DeadLetterStoreInterface
- Application layer port
- store(DeadLetterMessage): void
- findRetryable(int limit): array — find messages eligible for retry
- markRetried(string id): void — increment attempt count
- markResolved(string id): void — mark as successfully reprocessed
- purge(DateTimeImmutable before): int — remove old entries

### DeadLetterHandler
- Catches exceptions from message handlers
- Classifies failure type (transient vs permanent)
- Stores to DLQ with full context
- Logs failure details

### RetryStrategy
- Configurable max attempts
- Exponential backoff with jitter
- Failure type classification
- Skip permanent failures

### FailureClassifier
- Classifies exceptions as Transient or Permanent
- Configurable exception mapping
- Default: ConnectionException=Transient, ValidationException=Permanent

### DlqProcessor
- Processes retryable messages from DLQ
- Applies RetryStrategy for backoff
- Removes successfully processed messages
- Re-stores still-failing messages

---

## Generation Process

### Step 1: Analyze Request

Determine:
- Storage backend (Database)
- Max retry attempts (default: 5)
- Backoff strategy (exponential with jitter)

### Step 2: Generate Core Components

1. **Domain Layer** (`src/Domain/Shared/DeadLetter/`)
   - `FailureType.php` — Enum (Transient, Permanent, Unknown)
   - `DeadLetterMessage.php` — Message entity

2. **Application Layer** (`src/Application/Shared/DeadLetter/`)
   - `DeadLetterStoreInterface.php` — Storage port
   - `DeadLetterHandler.php` — Exception handler
   - `RetryStrategy.php` — Retry configuration and backoff calculation
   - `FailureClassifier.php` — Exception classification
   - `DlqProcessor.php` — Retry processor

3. **Infrastructure Layer** (`src/Infrastructure/DeadLetter/`)
   - `DatabaseDeadLetterStore.php` — PDO implementation
   - Database migration

4. **Tests**
   - `DeadLetterMessageTest.php`
   - `RetryStrategyTest.php`
   - `FailureClassifierTest.php`
   - `DlqProcessorTest.php`

---

## File Placement

| Layer | Path |
|-------|------|
| Domain Types | `src/Domain/Shared/DeadLetter/` |
| Application | `src/Application/Shared/DeadLetter/` |
| Infrastructure | `src/Infrastructure/DeadLetter/` |
| Unit Tests | `tests/Unit/{Layer}/{Path}/` |

---

## Key Principles

### Failure Classification
1. **Transient**: Connection errors, timeouts, rate limits — eligible for retry
2. **Permanent**: Validation errors, business rule violations — never retry
3. **Unknown**: Unclassified exceptions — retry with caution

### Retry Strategy
1. Max attempts configurable (default: 5)
2. Exponential backoff: delay = baseDelay * 2^attempt
3. Jitter: random ±25% to prevent thundering herd
4. Skip messages exceeding max attempts

### Message Lifecycle
```
Message → Handler fails → DeadLetterHandler → Store to DLQ
                                                    ↓
                                          DlqProcessor retries
                                                    ↓
                                          Success → Remove from DLQ
                                          Failure → Re-store with incremented attempts
                                          Max exceeded → Mark as permanently failed
```

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Failure Enum | `FailureType` | `FailureType` |
| Message Entity | `DeadLetterMessage` | `DeadLetterMessage` |
| Store Interface | `DeadLetterStoreInterface` | `DeadLetterStoreInterface` |
| Handler | `DeadLetterHandler` | `DeadLetterHandler` |
| Strategy | `RetryStrategy` | `RetryStrategy` |
| Classifier | `FailureClassifier` | `FailureClassifier` |
| Processor | `DlqProcessor` | `DlqProcessor` |
| Test | `{ClassName}Test` | `RetryStrategyTest` |

---

## Quick Template Reference

### DeadLetterMessage

```php
final class DeadLetterMessage
{
    public function __construct(
        public readonly string $id,
        public readonly string $originalBody,
        public readonly string $originalRoutingKey,
        public readonly array $originalHeaders,
        public readonly string $errorMessage,
        public readonly string $errorTrace,
        public readonly FailureType $failureType,
        public readonly int $attemptCount,
        public readonly \DateTimeImmutable $failedAt,
        public readonly ?\DateTimeImmutable $nextRetryAt,
        public readonly ?\DateTimeImmutable $resolvedAt = null,
    ) {}

    public function isRetryable(int $maxAttempts): bool;
    public function withIncrementedAttempt(\DateTimeImmutable $nextRetryAt): self;
}
```

### DeadLetterStoreInterface

```php
interface DeadLetterStoreInterface
{
    public function store(DeadLetterMessage $message): void;
    /** @return array<DeadLetterMessage> */
    public function findRetryable(int $limit = 100): array;
    public function markRetried(string $id, \DateTimeImmutable $nextRetryAt): void;
    public function markResolved(string $id): void;
    public function purge(\DateTimeImmutable $before): int;
    public function countByType(FailureType $type): int;
}
```

---

## Database Schema

```sql
CREATE TABLE dead_letter_messages (
    id VARCHAR(255) PRIMARY KEY,
    original_body TEXT NOT NULL,
    original_routing_key VARCHAR(255) NOT NULL,
    original_headers JSONB NOT NULL DEFAULT '{}',
    error_message TEXT NOT NULL,
    error_trace TEXT,
    failure_type VARCHAR(50) NOT NULL,
    attempt_count INTEGER NOT NULL DEFAULT 1,
    failed_at TIMESTAMP(6) NOT NULL,
    next_retry_at TIMESTAMP(6),
    resolved_at TIMESTAMP(6)
);

CREATE INDEX idx_dlq_retryable ON dead_letter_messages (failure_type, next_retry_at)
    WHERE resolved_at IS NULL AND failure_type != 'permanent';
CREATE INDEX idx_dlq_failed_at ON dead_letter_messages (failed_at);
```

---

## References

For complete PHP templates and test examples, see:
- `references/templates.md` — All component templates
- `references/examples.md` — Message broker integration example and unit tests
