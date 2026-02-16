# Outbox Pattern Antipatterns

## Critical Violations

### 1. Publishing Before Commit

**Problem:** Event is published before the database transaction commits.

```php
// ❌ WRONG: Publish can succeed but transaction can fail
public function execute(PlaceOrderCommand $command): void
{
    $this->transaction->begin();
    try {
        $order = Order::place(...);
        $this->orders->save($order);

        // Publishing before commit - DANGEROUS!
        $this->eventPublisher->publish(new OrderPlaced($order->id()));

        $this->transaction->commit();
    } catch (\Throwable $e) {
        $this->transaction->rollback();
        throw $e;
    }
}
```

**Consequence:** If transaction fails after publish, consumers receive event for non-existent order.

```php
// ✅ CORRECT: Use outbox in same transaction
public function execute(PlaceOrderCommand $command): void
{
    $this->transaction->execute(function () use ($command) {
        $order = Order::place(...);
        $this->orders->save($order);

        // Store in outbox within same transaction
        $this->outbox->save(new OutboxMessage(
            id: Uuid::uuid4()->toString(),
            eventType: 'order.placed',
            payload: json_encode(['order_id' => $order->id()->toString()])
        ));
    });
}
```

### 2. Two-Phase Commit Attempt

**Problem:** Trying to coordinate database and message broker in single transaction.

```php
// ❌ WRONG: Distributed transaction
public function execute(PlaceOrderCommand $command): void
{
    $this->dbTransaction->begin();
    $this->mqTransaction->begin();

    try {
        $order = Order::place(...);
        $this->orders->save($order);

        $this->mq->publish(new OrderPlaced($order->id()));

        $this->dbTransaction->commit();
        $this->mqTransaction->commit(); // Can fail after DB commit!
    } catch (\Throwable $e) {
        $this->dbTransaction->rollback();
        $this->mqTransaction->rollback();
        throw $e;
    }
}
```

**Consequence:** Partial failures leave system in inconsistent state.

### 3. Missing Idempotency Key

**Problem:** Outbox messages without unique identifiers.

```php
// ❌ WRONG: No way to deduplicate
final readonly class OutboxMessage
{
    public function __construct(
        public string $eventType,
        public string $payload
        // Missing: id, correlationId
    ) {}
}
```

**Consequence:** Duplicate processing on retry, no deduplication possible.

```php
// ✅ CORRECT: Always include unique ID
final readonly class OutboxMessage
{
    public function __construct(
        public string $id, // Unique, used for deduplication
        public string $eventType,
        public string $payload,
        public ?string $correlationId = null
    ) {}
}
```

### 4. Synchronous HTTP in Transaction

**Problem:** Making HTTP calls inside database transaction.

```php
// ❌ WRONG: HTTP call in transaction
public function execute(PlaceOrderCommand $command): void
{
    $this->transaction->execute(function () use ($command) {
        $order = Order::place(...);
        $this->orders->save($order);

        // HTTP call blocks transaction, can timeout
        $this->paymentGateway->reserve($order->total());
    });
}
```

**Consequence:** Long-held locks, timeouts, inconsistent state.

## Warning-Level Issues

### 5. No Retry Logic

**Problem:** Failed messages are lost.

```php
// ❌ WRONG: No retry, message lost on failure
public function processOutbox(): void
{
    foreach ($this->outbox->findUnprocessed() as $message) {
        try {
            $this->publisher->publish($message);
            $this->outbox->delete($message->id);
        } catch (\Throwable $e) {
            $this->outbox->delete($message->id); // Lost!
        }
    }
}
```

```php
// ✅ CORRECT: Retry with limit
public function processOutbox(): void
{
    foreach ($this->outbox->findUnprocessed() as $message) {
        try {
            $this->publisher->publish($message);
            $this->outbox->delete($message->id);
        } catch (\Throwable $e) {
            if ($message->retryCount >= self::MAX_RETRIES) {
                $this->deadLetter->store($message, $e);
                $this->outbox->delete($message->id);
            } else {
                $this->outbox->incrementRetry($message->id);
            }
        }
    }
}
```

### 6. No Dead Letter Handling

**Problem:** Poison messages block processing forever.

```php
// ❌ WRONG: Retry forever
public function processMessage(OutboxMessage $message): void
{
    while (true) {
        try {
            $this->publisher->publish($message);
            return;
        } catch (\Throwable $e) {
            sleep(1); // Retry forever
        }
    }
}
```

### 7. Unbounded Batch Processing

**Problem:** Processing all pending messages at once.

```php
// ❌ WRONG: Can load millions of records
public function processOutbox(): void
{
    $messages = $this->outbox->findUnprocessed(); // No limit!
    foreach ($messages as $message) {
        // ...
    }
}
```

```php
// ✅ CORRECT: Bounded batch
public function processOutbox(int $batchSize = 100): void
{
    $messages = $this->outbox->findUnprocessed($batchSize);
    // ...
}
```

### 8. Missing Ordering Guarantees

**Problem:** Events for same aggregate processed out of order.

```php
// ❌ WRONG: Parallel processing ignores ordering
public function processOutboxParallel(): void
{
    $messages = $this->outbox->findUnprocessed(1000);

    // Parallel processing breaks ordering
    Parallel::forEach($messages, fn($m) => $this->publish($m));
}
```

```php
// ✅ CORRECT: Order per aggregate
public function processOutbox(): void
{
    $grouped = $this->outbox->findUnprocessedGroupedByAggregate();

    foreach ($grouped as $aggregateId => $messages) {
        usort($messages, fn($a, $b) => $a->createdAt <=> $b->createdAt);

        foreach ($messages as $message) {
            if (!$this->tryPublish($message)) {
                break; // Stop this aggregate on failure
            }
        }
    }
}
```

### 9. No Monitoring

**Problem:** Silent failures go unnoticed.

```php
// ❌ WRONG: No visibility
public function processOutbox(): void
{
    foreach ($this->outbox->findUnprocessed() as $message) {
        try {
            $this->publisher->publish($message);
        } catch (\Throwable) {
            // Silent failure
        }
    }
}
```

```php
// ✅ CORRECT: Observable
public function processOutbox(): void
{
    $processed = 0;
    $failed = 0;

    foreach ($this->outbox->findUnprocessed() as $message) {
        try {
            $this->publisher->publish($message);
            $processed++;
        } catch (\Throwable $e) {
            $failed++;
            $this->logger->error('Outbox publish failed', [
                'message_id' => $message->id,
                'error' => $e->getMessage(),
            ]);
        }
    }

    $this->metrics->increment('outbox.processed', $processed);
    $this->metrics->increment('outbox.failed', $failed);
    $this->metrics->gauge('outbox.pending', $this->outbox->countUnprocessed());
}
```

## Detection Queries

```bash
# Find potential publish-before-commit
Grep: "publish.*commit|dispatch.*->save" --glob "**/UseCase/**/*.php"

# Find missing outbox usage
Grep: "EventDispatcher|EventPublisher" --glob "**/UseCase/**/*.php"
# Then check if same files use outbox

# Find synchronous HTTP in transactions
Grep: "transaction.*->get\(|transaction.*->post\(" --glob "**/*.php"

# Check for retry logic
Grep: "retryCount|retry_count" --glob "**/Outbox/**/*.php"

# Check for dead letter handling
Grep: "DeadLetter|dead_letter|DLQ" --glob "**/*.php"
```
