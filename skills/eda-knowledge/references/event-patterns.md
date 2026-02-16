# Event Patterns

Detailed patterns for events in Event-Driven Architecture.

## Event Types

### 1. Domain Events

Business facts within a bounded context.

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

use Domain\Shared\Event\DomainEvent;

final readonly class OrderPlaced implements DomainEvent
{
    public function __construct(
        public string $eventId,
        public string $orderId,
        public string $customerId,
        public array $lineItems,
        public int $totalCents,
        public string $currency,
        public \DateTimeImmutable $occurredAt
    ) {}

    public function eventName(): string
    {
        return 'order.placed';
    }

    public function aggregateId(): string
    {
        return $this->orderId;
    }

    public function aggregateType(): string
    {
        return 'Order';
    }
}
```

### 2. Integration Events

Cross-bounded-context communication.

```php
<?php

declare(strict_types=1);

namespace Application\Order\IntegrationEvent;

use Application\Shared\IntegrationEvent;

final readonly class OrderPlacedIntegrationEvent implements IntegrationEvent
{
    public function __construct(
        public string $eventId,
        public string $orderId,
        public string $customerId,
        public int $totalCents,
        public string $currency,
        public \DateTimeImmutable $occurredAt,
        // Simplified data for external consumers
        // No internal domain details
    ) {}

    public static function fromDomainEvent(OrderPlaced $event): self
    {
        return new self(
            eventId: Uuid::uuid4()->toString(),
            orderId: $event->orderId,
            customerId: $event->customerId,
            totalCents: $event->totalCents,
            currency: $event->currency,
            occurredAt: $event->occurredAt
        );
    }

    public function routingKey(): string
    {
        return 'orders.placed';
    }
}
```

### 3. System Events

Infrastructure and operational events.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Event;

final readonly class ServiceHealthChanged
{
    public function __construct(
        public string $serviceName,
        public string $status,  // healthy, degraded, unhealthy
        public ?string $reason,
        public \DateTimeImmutable $occurredAt
    ) {}
}

final readonly class CircuitBreakerOpened
{
    public function __construct(
        public string $serviceName,
        public int $failureCount,
        public string $lastError,
        public \DateTimeImmutable $occurredAt
    ) {}
}
```

## Event Structure

### Base Event Interface

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Event;

interface DomainEvent
{
    public function eventName(): string;
    public function aggregateId(): string;
    public function occurredAt(): \DateTimeImmutable;
    public function toArray(): array;
}
```

### Event with Metadata

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Event;

abstract readonly class BaseEvent implements DomainEvent
{
    public function __construct(
        public string $eventId,
        public \DateTimeImmutable $occurredAt,
        public ?string $correlationId = null,
        public ?string $causationId = null,
        public array $metadata = []
    ) {}

    public function withCorrelationId(string $correlationId): static
    {
        return new static(
            eventId: $this->eventId,
            occurredAt: $this->occurredAt,
            correlationId: $correlationId,
            causationId: $this->causationId,
            metadata: $this->metadata
        );
    }

    public function withCausationId(string $causationId): static
    {
        return new static(
            eventId: $this->eventId,
            occurredAt: $this->occurredAt,
            correlationId: $this->correlationId,
            causationId: $causationId,
            metadata: $this->metadata
        );
    }
}
```

### Event Envelope

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class EventEnvelope
{
    public function __construct(
        public string $messageId,
        public string $eventType,
        public array $payload,
        public array $headers,
        public \DateTimeImmutable $timestamp,
        public int $version = 1
    ) {}

    public static function wrap(DomainEvent $event): self
    {
        return new self(
            messageId: $event->eventId ?? Uuid::uuid4()->toString(),
            eventType: $event->eventName(),
            payload: $event->toArray(),
            headers: [
                'correlation_id' => $event->correlationId ?? null,
                'causation_id' => $event->causationId ?? null,
                'aggregate_id' => $event->aggregateId(),
                'aggregate_type' => $event->aggregateType(),
            ],
            timestamp: $event->occurredAt(),
            version: 1
        );
    }

    public function toJson(): string
    {
        return json_encode([
            'message_id' => $this->messageId,
            'event_type' => $this->eventType,
            'payload' => $this->payload,
            'headers' => $this->headers,
            'timestamp' => $this->timestamp->format('c'),
            'version' => $this->version,
        ], JSON_THROW_ON_ERROR);
    }
}
```

## Publishing Patterns

### 1. Direct Publishing

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class PlaceOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventPublisherInterface $events
    ) {}

    public function execute(PlaceOrderCommand $command): OrderDTO
    {
        $order = Order::place(
            id: $this->orders->nextIdentity(),
            customerId: new CustomerId($command->customerId),
            lines: $command->lines
        );

        $this->orders->save($order);

        // Publish events after successful save
        foreach ($order->releaseEvents() as $event) {
            $this->events->publish($event);
        }

        return OrderDTO::fromEntity($order);
    }
}
```

### 2. Transactional Outbox Pattern

Ensures events are published even if broker is unavailable.

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Outbox;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'outbox_messages')]
class OutboxMessage
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;

    #[ORM\Column(type: 'string')]
    private string $eventType;

    #[ORM\Column(type: 'json')]
    private array $payload;

    #[ORM\Column(type: 'datetime_immutable')]
    private \DateTimeImmutable $createdAt;

    #[ORM\Column(type: 'datetime_immutable', nullable: true)]
    private ?\DateTimeImmutable $processedAt = null;

    public static function fromEvent(DomainEvent $event): self
    {
        $message = new self();
        $message->id = Uuid::uuid4()->toString();
        $message->eventType = $event->eventName();
        $message->payload = $event->toArray();
        $message->createdAt = new \DateTimeImmutable();
        return $message;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class PlaceOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private OutboxRepositoryInterface $outbox,
        private TransactionManagerInterface $transaction
    ) {}

    public function execute(PlaceOrderCommand $command): OrderDTO
    {
        return $this->transaction->transactional(function () use ($command) {
            $order = Order::place(...);

            $this->orders->save($order);

            // Store events in outbox (same transaction)
            foreach ($order->releaseEvents() as $event) {
                $this->outbox->save(OutboxMessage::fromEvent($event));
            }

            return OrderDTO::fromEntity($order);
        });
    }
}
```

### 3. Outbox Processor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging\Outbox;

final readonly class OutboxProcessor
{
    public function __construct(
        private OutboxRepositoryInterface $outbox,
        private EventPublisherInterface $publisher,
        private LoggerInterface $logger
    ) {}

    public function process(int $batchSize = 100): int
    {
        $messages = $this->outbox->findUnprocessed($batchSize);
        $processed = 0;

        foreach ($messages as $message) {
            try {
                $this->publisher->publishRaw(
                    $message->eventType(),
                    $message->payload()
                );

                $message->markAsProcessed();
                $this->outbox->save($message);
                $processed++;

            } catch (\Throwable $e) {
                $this->logger->error('Failed to publish outbox message', [
                    'message_id' => $message->id(),
                    'error' => $e->getMessage(),
                ]);
            }
        }

        return $processed;
    }
}
```

## Subscribing Patterns

### 1. Event Handler Interface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Port\Input;

interface EventHandlerInterface
{
    public function handle(DomainEvent $event): void;

    public static function subscribedTo(): array;
}
```

### 2. Single Event Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

final readonly class UpdateInventoryOnOrderPlaced implements EventHandlerInterface
{
    public function __construct(
        private InventoryServiceInterface $inventory
    ) {}

    public function handle(DomainEvent $event): void
    {
        if (!$event instanceof OrderPlaced) {
            return;
        }

        foreach ($event->lineItems as $item) {
            $this->inventory->reserve(
                productId: $item['product_id'],
                quantity: $item['quantity'],
                orderId: $event->orderId
            );
        }
    }

    public static function subscribedTo(): array
    {
        return [OrderPlaced::class];
    }
}
```

### 3. Multi-Event Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

final readonly class OrderNotificationHandler implements EventHandlerInterface
{
    public function __construct(
        private NotificationServiceInterface $notifications
    ) {}

    public function handle(DomainEvent $event): void
    {
        match ($event::class) {
            OrderPlaced::class => $this->onOrderPlaced($event),
            OrderShipped::class => $this->onOrderShipped($event),
            OrderDelivered::class => $this->onOrderDelivered($event),
            default => null,
        };
    }

    private function onOrderPlaced(OrderPlaced $event): void
    {
        $this->notifications->send(
            $event->customerId,
            'order_placed',
            ['order_id' => $event->orderId]
        );
    }

    private function onOrderShipped(OrderShipped $event): void
    {
        $this->notifications->send(
            $event->customerId,
            'order_shipped',
            [
                'order_id' => $event->orderId,
                'tracking_number' => $event->trackingNumber,
            ]
        );
    }

    public static function subscribedTo(): array
    {
        return [
            OrderPlaced::class,
            OrderShipped::class,
            OrderDelivered::class,
        ];
    }
}
```

### 4. Idempotent Handler

```php
<?php

declare(strict_types=1);

namespace Application\Order\EventHandler;

final readonly class IdempotentEventHandler implements EventHandlerInterface
{
    public function __construct(
        private EventHandlerInterface $inner,
        private ProcessedEventRepositoryInterface $processedEvents
    ) {}

    public function handle(DomainEvent $event): void
    {
        $eventId = $event->eventId;

        if ($this->processedEvents->exists($eventId)) {
            return; // Already processed
        }

        $this->inner->handle($event);

        $this->processedEvents->markAsProcessed($eventId);
    }

    public static function subscribedTo(): array
    {
        return $this->inner::subscribedTo();
    }
}
```

## Event Versioning

### Version in Event

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

final readonly class OrderPlacedV2 implements DomainEvent
{
    public const VERSION = 2;

    public function __construct(
        public string $eventId,
        public string $orderId,
        public string $customerId,
        public array $lineItems,
        public int $totalCents,
        public string $currency,
        public ?string $promotionCode, // New field in V2
        public \DateTimeImmutable $occurredAt
    ) {}

    public function version(): int
    {
        return self::VERSION;
    }
}
```

### Event Upcaster

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class OrderPlacedUpcaster implements EventUpcasterInterface
{
    public function canUpcast(string $eventType, int $version): bool
    {
        return $eventType === 'order.placed' && $version < 2;
    }

    public function upcast(array $payload, int $fromVersion): array
    {
        if ($fromVersion === 1) {
            // Add default value for new field
            $payload['promotion_code'] = null;
        }

        return $payload;
    }
}
```

## Event Dispatcher

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Messaging;

final readonly class EventDispatcher implements EventDispatcherInterface
{
    /** @param iterable<EventHandlerInterface> $handlers */
    public function __construct(
        private iterable $handlers
    ) {}

    public function dispatch(DomainEvent $event): void
    {
        foreach ($this->handlers as $handler) {
            if ($this->shouldHandle($handler, $event)) {
                $handler->handle($event);
            }
        }
    }

    private function shouldHandle(EventHandlerInterface $handler, DomainEvent $event): bool
    {
        $subscribedTo = $handler::subscribedTo();
        return in_array($event::class, $subscribedTo, true);
    }
}
```

## Directory Structure

```
src/
├── Domain/
│   └── Order/
│       └── Event/
│           ├── OrderPlaced.php
│           ├── OrderConfirmed.php
│           ├── OrderShipped.php
│           └── OrderCancelled.php
│
├── Application/
│   ├── Order/
│   │   ├── EventHandler/
│   │   │   ├── SendConfirmationEmail.php
│   │   │   └── UpdateInventory.php
│   │   └── IntegrationEvent/
│   │       └── OrderPlacedIntegrationEvent.php
│   └── Shared/
│       └── Port/
│           └── Output/
│               └── EventPublisherInterface.php
│
└── Infrastructure/
    └── Messaging/
        ├── RabbitMQEventPublisher.php
        ├── EventDispatcher.php
        └── Outbox/
            ├── OutboxMessage.php
            ├── OutboxRepository.php
            └── OutboxProcessor.php
```
