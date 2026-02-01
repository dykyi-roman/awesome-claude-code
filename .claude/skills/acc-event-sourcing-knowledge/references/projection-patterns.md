# Projection Patterns

Detailed patterns for Event Sourcing Projections in PHP.

## Projection Definition

### What is a Projection?

A read model built by processing domain events. Projections transform the event stream into optimized query structures.

### Characteristics

| Aspect | Description |
|--------|-------------|
| **Derived** | Built entirely from events |
| **Rebuildable** | Can be recreated from scratch |
| **Optimized** | Structured for specific queries |
| **Eventually consistent** | May lag behind write model |
| **Idempotent** | Same event applied twice = same result |

## PHP 8.5 Implementation

### Projection Interface

```php
<?php

declare(strict_types=1);

namespace Application\Projection;

use Domain\Shared\Event\DomainEvent;

interface ProjectionInterface
{
    /**
     * Handle a domain event.
     */
    public function apply(DomainEvent $event): void;

    /**
     * Reset projection to initial state.
     */
    public function reset(): void;

    /**
     * Get last processed position.
     */
    public function getPosition(): int;

    /**
     * Update last processed position.
     */
    public function updatePosition(int $position): void;
}
```

### Simple Projection

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Projection;

use Domain\Order\Event\OrderCreatedEvent;
use Domain\Order\Event\OrderConfirmedEvent;
use Domain\Order\Event\OrderShippedEvent;

final class OrderListProjection implements ProjectionInterface
{
    private int $position = 0;

    public function __construct(
        private readonly Connection $connection
    ) {}

    public function apply(DomainEvent $event): void
    {
        match ($event::class) {
            OrderCreatedEvent::class => $this->applyOrderCreated($event),
            OrderConfirmedEvent::class => $this->applyOrderConfirmed($event),
            OrderShippedEvent::class => $this->applyOrderShipped($event),
            default => null, // Ignore unknown events
        };
    }

    private function applyOrderCreated(OrderCreatedEvent $event): void
    {
        $this->connection->insert('order_list', [
            'id' => $event->orderId,
            'customer_id' => $event->customerId,
            'status' => 'draft',
            'total_cents' => 0,
            'created_at' => $event->createdAt->format('Y-m-d H:i:s'),
        ]);
    }

    private function applyOrderConfirmed(OrderConfirmedEvent $event): void
    {
        $this->connection->update('order_list', [
            'status' => 'confirmed',
            'total_cents' => $event->totalCents,
            'confirmed_at' => $event->confirmedAt->format('Y-m-d H:i:s'),
        ], ['id' => $event->orderId]);
    }

    private function applyOrderShipped(OrderShippedEvent $event): void
    {
        $this->connection->update('order_list', [
            'status' => 'shipped',
            'shipped_at' => $event->shippedAt->format('Y-m-d H:i:s'),
            'tracking_number' => $event->trackingNumber,
        ], ['id' => $event->orderId]);
    }

    public function reset(): void
    {
        $this->connection->executeStatement('TRUNCATE order_list');
        $this->position = 0;
    }

    public function getPosition(): int
    {
        return $this->position;
    }

    public function updatePosition(int $position): void
    {
        $this->position = $position;
    }
}
```

### Projection with Position Tracking

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Projection;

final class OrderListProjection implements ProjectionInterface
{
    private const PROJECTION_NAME = 'order_list';

    public function __construct(
        private readonly Connection $connection
    ) {}

    public function getPosition(): int
    {
        $sql = 'SELECT position FROM projection_positions WHERE name = :name';
        $position = $this->connection->fetchOne($sql, ['name' => self::PROJECTION_NAME]);

        return $position !== false ? (int) $position : 0;
    }

    public function updatePosition(int $position): void
    {
        $this->connection->executeStatement(
            <<<SQL
                INSERT INTO projection_positions (name, position)
                VALUES (:name, :position)
                ON CONFLICT (name) DO UPDATE SET position = :position
            SQL,
            ['name' => self::PROJECTION_NAME, 'position' => $position]
        );
    }

    public function reset(): void
    {
        $this->connection->transactional(function () {
            $this->connection->executeStatement('TRUNCATE order_list');
            $this->connection->delete('projection_positions', ['name' => self::PROJECTION_NAME]);
        });
    }
}
```

## Projection Patterns

### Async Projection Runner

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Projection;

final class ProjectionRunner
{
    private bool $running = true;

    public function __construct(
        private readonly EventStoreInterface $eventStore,
        private readonly array $projections,
        private readonly LoggerInterface $logger
    ) {}

    public function run(): void
    {
        while ($this->running) {
            foreach ($this->projections as $projection) {
                $this->processProjection($projection);
            }
            usleep(100_000); // 100ms between batches
        }
    }

    private function processProjection(ProjectionInterface $projection): void
    {
        $position = $projection->getPosition();
        $events = $this->eventStore->loadAll($position, limit: 100);

        if (empty($events)) {
            return;
        }

        foreach ($events as $storedEvent) {
            try {
                $event = $this->deserialize($storedEvent);
                $projection->apply($event);
                $projection->updatePosition($storedEvent->globalPosition);
            } catch (\Throwable $e) {
                $this->logger->error('Projection error', [
                    'projection' => $projection::class,
                    'event' => $storedEvent->eventId,
                    'error' => $e->getMessage(),
                ]);
                throw $e;
            }
        }
    }

    public function stop(): void
    {
        $this->running = false;
    }
}
```

### Catch-Up Projection

Projection that processes all historical events, then switches to live mode:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Projection;

final class CatchUpProjectionRunner
{
    public function __construct(
        private readonly EventStoreInterface $eventStore,
        private readonly ProjectionInterface $projection,
        private readonly EventDispatcher $liveDispatcher
    ) {}

    public function start(): void
    {
        // Phase 1: Catch up with historical events
        $this->catchUp();

        // Phase 2: Subscribe to live events
        $this->liveDispatcher->subscribe(
            fn (DomainEvent $event, int $position) => $this->handleLiveEvent($event, $position)
        );
    }

    private function catchUp(): void
    {
        $position = $this->projection->getPosition();

        while (true) {
            $events = $this->eventStore->loadAll($position, limit: 1000);

            if (empty($events)) {
                break;
            }

            foreach ($events as $storedEvent) {
                $event = $this->deserialize($storedEvent);
                $this->projection->apply($event);
                $position = $storedEvent->globalPosition;
            }

            $this->projection->updatePosition($position);
        }
    }

    private function handleLiveEvent(DomainEvent $event, int $position): void
    {
        // Skip if already processed during catch-up
        if ($position <= $this->projection->getPosition()) {
            return;
        }

        $this->projection->apply($event);
        $this->projection->updatePosition($position);
    }
}
```

### Multi-Stream Projection

Projection that combines events from multiple aggregate types:

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Projection;

final class CustomerOrderSummaryProjection implements ProjectionInterface
{
    public function __construct(
        private readonly Connection $connection
    ) {}

    public function apply(DomainEvent $event): void
    {
        match ($event::class) {
            // Customer events
            CustomerRegisteredEvent::class => $this->applyCustomerRegistered($event),
            CustomerEmailChangedEvent::class => $this->applyCustomerEmailChanged($event),

            // Order events
            OrderCreatedEvent::class => $this->applyOrderCreated($event),
            OrderCompletedEvent::class => $this->applyOrderCompleted($event),

            default => null,
        };
    }

    private function applyCustomerRegistered(CustomerRegisteredEvent $event): void
    {
        $this->connection->insert('customer_order_summary', [
            'customer_id' => $event->customerId,
            'customer_name' => $event->name,
            'customer_email' => $event->email,
            'total_orders' => 0,
            'total_spent_cents' => 0,
        ]);
    }

    private function applyOrderCompleted(OrderCompletedEvent $event): void
    {
        $this->connection->executeStatement(
            <<<SQL
                UPDATE customer_order_summary
                SET total_orders = total_orders + 1,
                    total_spent_cents = total_spent_cents + :amount,
                    last_order_at = :completed_at
                WHERE customer_id = :customer_id
            SQL,
            [
                'customer_id' => $event->customerId,
                'amount' => $event->totalCents,
                'completed_at' => $event->completedAt->format('Y-m-d H:i:s'),
            ]
        );
    }
}
```

## Idempotency Patterns

### Upsert Pattern

```php
private function applyOrderCreated(OrderCreatedEvent $event): void
{
    // Upsert - safe to apply multiple times
    $this->connection->executeStatement(
        <<<SQL
            INSERT INTO order_list (id, customer_id, status, created_at)
            VALUES (:id, :customer_id, :status, :created_at)
            ON CONFLICT (id) DO NOTHING
        SQL,
        [
            'id' => $event->orderId,
            'customer_id' => $event->customerId,
            'status' => 'draft',
            'created_at' => $event->createdAt->format('Y-m-d H:i:s'),
        ]
    );
}
```

### Event ID Tracking

```php
final class IdempotentProjection implements ProjectionInterface
{
    public function apply(DomainEvent $event): void
    {
        $eventId = $event->metadata()->eventId;

        // Check if already processed
        if ($this->isProcessed($eventId)) {
            return;
        }

        // Process event
        $this->doApply($event);

        // Mark as processed
        $this->markProcessed($eventId);
    }

    private function isProcessed(string $eventId): bool
    {
        $sql = 'SELECT 1 FROM processed_events WHERE event_id = :event_id';
        return $this->connection->fetchOne($sql, ['event_id' => $eventId]) !== false;
    }

    private function markProcessed(string $eventId): void
    {
        $this->connection->insert('processed_events', ['event_id' => $eventId]);
    }
}
```

## Read Model Patterns

### Dedicated Read Model

```php
<?php

declare(strict_types=1);

namespace Application\Order\ReadModel;

interface OrderReadModelInterface
{
    public function findById(string $id): ?OrderDetailsDTO;

    /**
     * @return array<OrderListItemDTO>
     */
    public function findByCustomer(string $customerId, int $limit, int $offset): array;

    /**
     * @return array<OrderListItemDTO>
     */
    public function findByStatus(string $status, int $limit, int $offset): array;

    public function countByCustomer(string $customerId): int;
}
```

### Read Model Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\ReadModel;

final readonly class DbalOrderReadModel implements OrderReadModelInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function findById(string $id): ?OrderDetailsDTO
    {
        $sql = <<<SQL
            SELECT
                o.id,
                o.customer_id,
                c.name as customer_name,
                o.status,
                o.total_cents,
                o.created_at,
                o.confirmed_at,
                o.shipped_at
            FROM order_list o
            JOIN customer_order_summary c ON c.customer_id = o.customer_id
            WHERE o.id = :id
        SQL;

        $row = $this->connection->fetchAssociative($sql, ['id' => $id]);

        if ($row === false) {
            return null;
        }

        return OrderDetailsDTO::fromArray($row);
    }
}
```

## Rebuilding Projections

### Full Rebuild

```php
final class ProjectionRebuilder
{
    public function rebuild(ProjectionInterface $projection): void
    {
        // Reset projection
        $projection->reset();

        // Process all events
        $position = 0;
        while (true) {
            $events = $this->eventStore->loadAll($position, limit: 1000);

            if (empty($events)) {
                break;
            }

            foreach ($events as $storedEvent) {
                $event = $this->deserialize($storedEvent);
                $projection->apply($event);
                $position = $storedEvent->globalPosition;
            }

            $projection->updatePosition($position);

            // Progress logging
            $this->logger->info("Rebuilt to position {$position}");
        }

        $this->logger->info('Projection rebuild complete');
    }
}
```

### Partial Rebuild (Category)

```php
final class ProjectionRebuilder
{
    public function rebuildCategory(ProjectionInterface $projection, string $category): void
    {
        $position = 0;
        while (true) {
            $events = $this->eventStore->loadByCategory($category, $position, limit: 1000);

            if (empty($events)) {
                break;
            }

            foreach ($events as $storedEvent) {
                $event = $this->deserialize($storedEvent);
                $projection->apply($event);
                $position = $storedEvent->globalPosition;
            }
        }
    }
}
```

## Detection Patterns

```bash
# Find projections
Glob: **/Projection/**/*Projection.php
Grep: "implements ProjectionInterface|class.*Projection" --glob "**/*.php"

# Check for apply methods
Grep: "function apply.*Event" --glob "**/Projection/**/*.php"

# Check for idempotency
Grep: "ON CONFLICT|ON DUPLICATE|UPSERT|DO NOTHING|DO UPDATE" --glob "**/Projection/**/*.php"

# Check for position tracking
Grep: "getPosition|updatePosition" --glob "**/Projection/**/*.php"

# Warning: Non-idempotent operations
Grep: "INSERT INTO(?!.*ON CONFLICT)" --glob "**/Projection/**/*.php"
Grep: "->insert\(" --glob "**/Projection/**/*.php"

# Check for reset capability
Grep: "function reset|TRUNCATE" --glob "**/Projection/**/*.php"
```
