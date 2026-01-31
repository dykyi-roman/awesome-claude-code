# Event Sourcing Antipatterns

Common Event Sourcing violations with detection patterns and fixes.

## Critical Violations

### 1. Mutable Events

**Description:** Events with setters or mutable properties.

**Why Critical:** Events represent facts that happened. Modifying them corrupts history.

**Detection:**
```bash
Grep: "public function set|private.*\$.*\;$" --glob "**/Event/**/*.php" | grep -v "readonly"
Grep: "class.*Event[^{]*\{" --glob "**/Event/**/*.php" | grep -v "readonly"
```

**Bad:**
```php
namespace Domain\Order\Event;

class OrderCreatedEvent
{
    private string $orderId;
    private string $customerId;

    public function setCustomerId(string $customerId): void  // MUTABLE!
    {
        $this->customerId = $customerId;
    }
}
```

**Good:**
```php
namespace Domain\Order\Event;

final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public DateTimeImmutable $createdAt,
        public EventMetadata $metadata
    ) {}
}
```

### 2. Direct State Mutation in Aggregate

**Description:** Aggregate modifies state without going through events.

**Why Critical:** State and event stream become desynchronized. Replay produces wrong state.

**Detection:**
```bash
# Look for direct property assignment not in apply methods
Grep: "\$this->[a-z]+ = " --glob "**/Entity/**/*.php" | grep -v "apply.*Event"
Grep: "function (?!apply)[a-z]+.*\$this->[a-z]+ = " --glob "**/Entity/**/*.php"
```

**Bad:**
```php
final class Order extends EventSourcedAggregate
{
    private OrderStatus $status;

    public function confirm(): void
    {
        // CRITICAL: Direct mutation without event
        $this->status = OrderStatus::Confirmed;
    }
}
```

**Good:**
```php
final class Order extends EventSourcedAggregate
{
    private OrderStatus $status;

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateException();
        }

        // Record event, then apply it
        $this->recordThat(new OrderConfirmedEvent(
            orderId: $this->id->value,
            confirmedAt: new DateTimeImmutable()
        ));
    }

    protected function applyOrderConfirmedEvent(OrderConfirmedEvent $event): void
    {
        // State only changes here
        $this->status = OrderStatus::Confirmed;
    }
}
```

### 3. Incomplete Event Data

**Description:** Event doesn't contain all data needed to reconstruct state.

**Why Critical:** Cannot rebuild aggregate state correctly from events.

**Detection:**
```bash
# Manual review - check event fields vs aggregate state
# Events should be self-contained
```

**Bad:**
```php
// Event missing data
final readonly class OrderLineAddedEvent
{
    public function __construct(
        public string $orderId,
        public string $productId,
        // Missing: quantity, price, etc.
    ) {}
}

// Aggregate needs to query for missing data
protected function applyOrderLineAddedEvent(OrderLineAddedEvent $event): void
{
    // BAD: Querying during replay
    $product = $this->productRepository->find($event->productId);
    $this->lines[] = new OrderLine($product->name, $product->price);
}
```

**Good:**
```php
// Event contains all needed data
final readonly class OrderLineAddedEvent
{
    public function __construct(
        public string $orderId,
        public string $productId,
        public string $productName,
        public int $quantity,
        public int $unitPriceCents,
        public string $currency
    ) {}
}

// Aggregate can rebuild purely from event
protected function applyOrderLineAddedEvent(OrderLineAddedEvent $event): void
{
    $this->lines[] = new OrderLine(
        productId: new ProductId($event->productId),
        productName: $event->productName,
        quantity: $event->quantity,
        unitPrice: new Money($event->unitPriceCents, $event->currency)
    );
}
```

### 4. Event Store Updates/Deletes

**Description:** Modifying or deleting events in the event store.

**Why Critical:** Destroys audit trail, corrupts history, breaks projections.

**Detection:**
```bash
Grep: "UPDATE event_store|DELETE FROM event_store" --glob "**/*.php"
Grep: "->update\(.*event|->delete\(.*event" --glob "**/EventStore*.php"
```

**Bad:**
```php
final class EventStore
{
    public function updateEvent(string $eventId, array $newPayload): void
    {
        // CRITICAL VIOLATION!
        $this->connection->update('event_store', $newPayload, ['event_id' => $eventId]);
    }

    public function deleteEvent(string $eventId): void
    {
        // CRITICAL VIOLATION!
        $this->connection->delete('event_store', ['event_id' => $eventId]);
    }
}
```

**Good:**
```php
interface EventStoreInterface
{
    // Only append-only operations
    public function append(string $streamId, array $events, int $expectedVersion): void;
    public function load(string $streamId): array;
    // No update/delete methods!
}
```

## Warnings

### 5. Business Logic in Events

**Description:** Events contain calculations or business decisions.

**Why Bad:** Events should be facts, not logic. Logic in events can't be fixed by code changes.

**Detection:**
```bash
Grep: "function (calculate|validate|check|is[A-Z])" --glob "**/Event/**/*.php"
Grep: "if \(|switch \(" --glob "**/Event/**/*.php"
```

**Bad:**
```php
final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public array $lines
    ) {}

    // BAD: Business logic in event
    public function calculateTotal(): int
    {
        return array_sum(array_map(
            fn ($line) => $line['quantity'] * $line['price'],
            $this->lines
        ));
    }

    // BAD: Validation in event
    public function isValid(): bool
    {
        return !empty($this->lines);
    }
}
```

**Good:**
```php
final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public int $totalCents,  // Pre-calculated, stored as fact
        public DateTimeImmutable $createdAt
    ) {}
    // No logic methods
}
```

### 6. Missing Event Metadata

**Description:** Events lack essential metadata (timestamp, causation ID, etc.).

**Why Bad:** Can't trace causality, debug issues, or implement sagas.

**Detection:**
```bash
Grep: "class.*Event.*{" --glob "**/Event/**/*.php" -A 20 | grep -v "eventId|occurredAt|metadata|timestamp|causation|correlation"
```

**Bad:**
```php
final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId
        // Missing: eventId, timestamp, causationId, correlationId
    ) {}
}
```

**Good:**
```php
final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public EventMetadata $metadata
    ) {}
}

final readonly class EventMetadata
{
    public function __construct(
        public string $eventId,
        public DateTimeImmutable $occurredAt,
        public ?string $causationId = null,     // What command caused this
        public ?string $correlationId = null,   // Original request ID
        public int $version = 1,                // Event schema version
        public ?string $userId = null           // Who triggered this
    ) {}
}
```

### 7. Non-Idempotent Projection

**Description:** Projection produces different results if same event is applied twice.

**Why Bad:** Re-processing events (after error, rebuild) corrupts read model.

**Detection:**
```bash
# Look for INSERT without ON CONFLICT
Grep: "INSERT INTO(?!.*ON CONFLICT)" --glob "**/Projection/**/*.php"
Grep: "->insert\(" --glob "**/Projection/**/*.php"
```

**Bad:**
```php
final class OrderCountProjection
{
    public function applyOrderCreatedEvent(OrderCreatedEvent $event): void
    {
        // NON-IDEMPOTENT: Replaying events doubles the count
        $this->connection->executeStatement(
            'UPDATE stats SET order_count = order_count + 1'
        );
    }
}
```

**Good:**
```php
final class OrderCountProjection
{
    public function applyOrderCreatedEvent(OrderCreatedEvent $event): void
    {
        // IDEMPOTENT: Uses upsert
        $this->connection->executeStatement(
            <<<SQL
                INSERT INTO order_list (id, customer_id)
                VALUES (:id, :customer_id)
                ON CONFLICT (id) DO NOTHING
            SQL,
            ['id' => $event->orderId, 'customer_id' => $event->customerId]
        );

        // Recount to ensure accuracy
        $this->connection->executeStatement(
            'UPDATE stats SET order_count = (SELECT COUNT(*) FROM order_list)'
        );
    }
}
```

### 8. Event Named in Present Tense

**Description:** Events named as commands or actions rather than facts.

**Why Bad:** Confusing semantics. Events represent past facts.

**Detection:**
```bash
Grep: "class (Create|Update|Delete|Process|Execute|Handle)[A-Z].*Event" --glob "**/Event/**/*.php"
```

**Bad:**
```php
class CreateOrderEvent { }      // Present tense - sounds like command
class ProcessPaymentEvent { }   // Present tense
class UpdateCustomerEvent { }   // Present tense
```

**Good:**
```php
class OrderCreatedEvent { }     // Past tense - fact
class PaymentProcessedEvent { } // Past tense
class CustomerUpdatedEvent { }  // Past tense
```

### 9. External Calls During Replay

**Description:** Aggregate or projection makes external calls when applying events.

**Why Bad:** Replay becomes slow, non-deterministic, may fail.

**Detection:**
```bash
Grep: "Repository|Service|Client|Api|Http" --glob "**/Entity/**/*apply*.php"
Grep: "->find\(|->get\(|->fetch\(" --glob "**/Entity/**/*.php"
```

**Bad:**
```php
final class Order extends EventSourcedAggregate
{
    public function __construct(
        private ProductRepository $products  // BAD: External dependency
    ) {}

    protected function applyOrderLineAddedEvent(OrderLineAddedEvent $event): void
    {
        // BAD: Database call during replay
        $product = $this->products->find($event->productId);
        $this->lines[] = new OrderLine($product);
    }
}
```

**Good:**
```php
final class Order extends EventSourcedAggregate
{
    // No external dependencies

    protected function applyOrderLineAddedEvent(OrderLineAddedEvent $event): void
    {
        // All data comes from event
        $this->lines[] = new OrderLine(
            productId: new ProductId($event->productId),
            productName: $event->productName,
            unitPrice: new Money($event->unitPriceCents, $event->currency)
        );
    }
}
```

### 10. Missing Optimistic Concurrency

**Description:** Event store doesn't check version on append.

**Why Bad:** Concurrent modifications cause lost updates.

**Detection:**
```bash
# Check if append method uses expectedVersion
Grep: "function append" --glob "**/EventStore*.php" -A 5 | grep -v "expectedVersion|expected_version|version"
```

**Bad:**
```php
final class EventStore
{
    public function append(string $streamId, array $events): void
    {
        // BAD: No version check
        foreach ($events as $event) {
            $this->insertEvent($streamId, $event);
        }
    }
}
```

**Good:**
```php
final class EventStore
{
    public function append(string $streamId, array $events, int $expectedVersion): void
    {
        $this->connection->transactional(function () use ($streamId, $events, $expectedVersion) {
            $currentVersion = $this->getVersionForUpdate($streamId);

            if ($currentVersion !== $expectedVersion) {
                throw new ConcurrencyException(
                    "Expected version {$expectedVersion}, got {$currentVersion}"
                );
            }

            $version = $expectedVersion;
            foreach ($events as $event) {
                $version++;
                $this->insertEvent($streamId, $event, $version);
            }
        });
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Mutable events | Critical | Data integrity | Medium |
| Direct state mutation | Critical | Data integrity | Medium |
| Incomplete event data | Critical | Replayability | High |
| Event store updates | Critical | Audit trail | Medium |
| Business logic in events | Warning | Maintainability | Medium |
| Missing metadata | Warning | Debugging | Low |
| Non-idempotent projection | Warning | Data integrity | Medium |
| Present tense naming | Warning | Readability | Low |
| External calls in replay | Warning | Performance | High |
| Missing concurrency check | Warning | Data integrity | Medium |

## Detection Summary

```bash
# Quick audit script

echo "=== Checking for mutable events ==="
Grep: "class.*Event[^{]*\{" --glob "**/Event/**/*.php" | grep -v "readonly"

echo "=== Checking for event store mutations ==="
Grep: "UPDATE event|DELETE FROM event" --glob "**/*.php"

echo "=== Checking for logic in events ==="
Grep: "function (calculate|validate|check|is[A-Z])" --glob "**/Event/**/*.php"

echo "=== Checking for non-idempotent projections ==="
Grep: "INSERT INTO(?!.*ON CONFLICT)" --glob "**/Projection/**/*.php"

echo "=== Checking for external calls in apply methods ==="
Grep: "Repository|Service|->find\(" --glob "**/Entity/**/*apply*.php"

echo "=== Checking for present-tense events ==="
Grep: "class (Create|Update|Delete|Process)[A-Z].*Event" --glob "**/Event/**/*.php"
```
