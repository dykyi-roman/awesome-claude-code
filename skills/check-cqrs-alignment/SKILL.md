---
name: acc-check-cqrs-alignment
description: Audits CQRS and Event Sourcing alignment. Checks command/query separation, projection idempotency, event store consistency, and read/write model synchronization.
---

# CQRS & Event Sourcing Alignment Audit

Analyze PHP code for proper CQRS implementation and Event Sourcing compliance.

## Detection Patterns

### 1. Command Returning Data

```php
// ANTIPATTERN: Command handler returns data (violates CQS)
final readonly class CreateOrderHandler
{
    public function handle(CreateOrderCommand $command): OrderDTO // Returns data!
    {
        $order = Order::create($command->userId(), $command->items());
        $this->orderRepo->save($order);
        return OrderDTO::fromEntity($order); // Mixing write + read
    }
}

// CORRECT: Command returns void or just ID
final readonly class CreateOrderHandler
{
    public function handle(CreateOrderCommand $command): OrderId
    {
        $order = Order::create($command->userId(), $command->items());
        $this->orderRepo->save($order);
        return $order->id(); // Only identity, not projection
    }
}
```

### 2. Query Modifying State

```php
// CRITICAL: Query handler with side effects
final readonly class GetOrderHandler
{
    public function handle(GetOrderQuery $query): OrderDTO
    {
        $order = $this->orderRepo->find($query->orderId());
        $order->markAsViewed(); // Side effect in query!
        $this->orderRepo->save($order); // Write in read path!
        return OrderDTO::fromEntity($order);
    }
}

// CORRECT: Query is pure read
final readonly class GetOrderHandler
{
    public function handle(GetOrderQuery $query): OrderReadModel
    {
        return $this->orderReadRepo->find($query->orderId());
    }
}
```

### 3. Read Model Using Write Repository

```php
// ANTIPATTERN: Read side uses write model
final readonly class OrderListHandler
{
    public function handle(OrderListQuery $query): array
    {
        // Using write-side repository for reads
        $orders = $this->orderRepository->findByUser($query->userId());
        return array_map(fn (Order $o) => OrderDTO::fromEntity($o), $orders);
        // Hydrates full aggregate just to read!
    }
}

// CORRECT: Dedicated read model
final readonly class OrderListHandler
{
    public function handle(OrderListQuery $query): array
    {
        // Flat read from read-optimized storage
        return $this->orderReadRepository->findByUser($query->userId());
    }
}
```

### 4. Non-Idempotent Projection

```php
// CRITICAL: Projection not idempotent — replaying events duplicates data
class OrderProjection
{
    public function onOrderCreated(OrderCreated $event): void
    {
        $this->db->insert('order_read_model', [
            'id' => $event->orderId(),
            'total' => $event->total(),
        ]);
        // If event replayed → duplicate row!
    }
}

// CORRECT: Idempotent projection (upsert)
class OrderProjection
{
    public function onOrderCreated(OrderCreated $event): void
    {
        $this->db->executeStatement(
            'INSERT INTO order_read_model (id, total, updated_at)
             VALUES (:id, :total, :updated_at)
             ON DUPLICATE KEY UPDATE total = :total, updated_at = :updated_at',
            [
                'id' => $event->orderId()->toString(),
                'total' => $event->total()->amount(),
                'updated_at' => $event->occurredAt()->format('Y-m-d H:i:s'),
            ],
        );
    }
}
```

### 5. Event Without Version/Timestamp

```php
// ANTIPATTERN: Event missing essential metadata
final readonly class OrderCreated
{
    public function __construct(
        public OrderId $orderId,
        public UserId $userId,
        // Missing: version, timestamp, aggregate version
    ) {}
}

// CORRECT: Full event metadata
final readonly class OrderCreated implements DomainEvent
{
    public function __construct(
        public OrderId $orderId,
        public UserId $userId,
        public Money $total,
        public int $aggregateVersion,
        public \DateTimeImmutable $occurredAt,
        public EventId $eventId,
    ) {}
}
```

### 6. Mixed Command and Query Bus

```php
// ANTIPATTERN: Single bus for commands and queries
class MessageBus
{
    public function dispatch(mixed $message): mixed
    {
        // Cannot enforce "commands return void" vs "queries return data"
        $handler = $this->handlers[get_class($message)];
        return $handler->handle($message);
    }
}

// CORRECT: Separate buses
interface CommandBus
{
    public function dispatch(Command $command): void;
}

interface QueryBus
{
    public function dispatch(Query $query): mixed;
}
```

### 7. Event Store Without Optimistic Locking

```php
// CRITICAL: No concurrency control on event append
class EventStore
{
    public function append(AggregateId $id, array $events): void
    {
        foreach ($events as $event) {
            $this->db->insert('events', [
                'aggregate_id' => $id->toString(),
                'payload' => serialize($event),
            ]);
        }
        // No version check — concurrent writes corrupt stream!
    }
}

// CORRECT: Optimistic locking with expected version
class EventStore
{
    public function append(AggregateId $id, array $events, int $expectedVersion): void
    {
        $currentVersion = $this->getVersion($id);
        if ($currentVersion !== $expectedVersion) {
            throw new ConcurrencyException(
                "Expected version {$expectedVersion}, got {$currentVersion}",
            );
        }
        // Append with version increment...
    }
}
```

## Grep Patterns

```bash
# Command returning data
Grep: "class.*CommandHandler.*\n.*function handle.*:.*(?!void|.*Id)" --glob "**/*.php"
Grep: "CommandHandler.*return.*DTO|CommandHandler.*return.*Response" --glob "**/*.php"

# Query with side effects
Grep: "->save\(|->persist\(|->flush\(" --glob "**/*QueryHandler*.php"
Grep: "->save\(|->persist\(|->flush\(" --glob "**/*ReadModel*.php"

# Read using write repository
Grep: "Repository->find|Repository->findBy" --glob "**/*QueryHandler*.php"

# Non-idempotent projection
Grep: "->insert\(" --glob "**/*Projection*.php"

# Missing event metadata
Grep: "class.*Event\b" --glob "**/Domain/**/*.php"
Grep: "occurredAt|aggregateVersion|eventId" --glob "**/Domain/**/*Event*.php"

# Single bus for both
Grep: "class.*Bus.*dispatch.*mixed" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Query modifying state | 🔴 Critical |
| Non-idempotent projection | 🔴 Critical |
| Event store without locking | 🔴 Critical |
| Command returning rich data | 🟠 Major |
| Read using write repository | 🟠 Major |
| Mixed command/query bus | 🟡 Minor |
| Event without version | 🟡 Minor |

## Output Format

```markdown
### CQRS Alignment: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Side:** Command/Query/Projection

**CQRS Rule Violated:**
[Which CQRS/ES principle is broken]

**Issue:**
[Description of the alignment violation]

**Code:**
```php
// Misaligned code
```

**Fix:**
```php
// Properly separated code
```
```
