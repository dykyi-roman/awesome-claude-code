# Event Versioning Patterns

Detailed patterns for Event Schema Evolution in PHP.

## Why Event Versioning?

Events are immutable and stored forever. But requirements change:
- New fields needed
- Field names change
- Field types change
- Fields become required/optional
- Events split or merge

**Problem:** Old code writes events, new code must read them.

## Versioning Strategies

### Strategy 1: Event Upcasting

Transform old events to new format when loading.

```
Event Store:              After Upcasting:
┌─────────────────────┐   ┌─────────────────────┐
│ OrderCreated v1     │   │ OrderCreated v2     │
│ { orderId: "123" }  │ → │ { orderId: "123",   │
│                     │   │   currency: "USD" } │
└─────────────────────┘   └─────────────────────┘
```

### Strategy 2: Multiple Event Versions

Support reading multiple event versions.

### Strategy 3: Weak Schema

Events have flexible schema, handle missing fields gracefully.

## PHP 8.4 Implementation

### Upcaster Interface

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

interface UpcasterInterface
{
    /**
     * Check if this upcaster can handle the event.
     */
    public function canUpcast(string $eventType, int $version): bool;

    /**
     * Transform event data to newer version.
     *
     * @param array $payload Original event payload
     * @param array $metadata Original event metadata
     * @return array{payload: array, metadata: array, version: int}
     */
    public function upcast(array $payload, array $metadata): array;
}
```

### Single Event Upcaster

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore\Upcaster;

final readonly class OrderCreatedV1ToV2Upcaster implements UpcasterInterface
{
    public function canUpcast(string $eventType, int $version): bool
    {
        return $eventType === 'OrderCreated' && $version === 1;
    }

    public function upcast(array $payload, array $metadata): array
    {
        // V1 -> V2: Add currency field with default
        return [
            'payload' => [
                ...$payload,
                'currency' => $payload['currency'] ?? 'USD',
            ],
            'metadata' => [
                ...$metadata,
                'version' => 2,
            ],
            'version' => 2,
        ];
    }
}
```

### Chain Upcaster

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore\Upcaster;

final class ChainUpcaster
{
    /** @var array<UpcasterInterface> */
    private array $upcasters = [];

    public function addUpcaster(UpcasterInterface $upcaster): void
    {
        $this->upcasters[] = $upcaster;
    }

    public function upcast(string $eventType, array $payload, array $metadata, int $version): array
    {
        $currentPayload = $payload;
        $currentMetadata = $metadata;
        $currentVersion = $version;

        // Keep upcasting until no more upcasters match
        $upcasted = true;
        while ($upcasted) {
            $upcasted = false;
            foreach ($this->upcasters as $upcaster) {
                if ($upcaster->canUpcast($eventType, $currentVersion)) {
                    $result = $upcaster->upcast($currentPayload, $currentMetadata);
                    $currentPayload = $result['payload'];
                    $currentMetadata = $result['metadata'];
                    $currentVersion = $result['version'];
                    $upcasted = true;
                    break; // Restart the loop with new version
                }
            }
        }

        return [
            'payload' => $currentPayload,
            'metadata' => $currentMetadata,
            'version' => $currentVersion,
        ];
    }
}
```

### Event Serializer with Upcasting

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

final readonly class UpcastingEventSerializer
{
    public function __construct(
        private EventTypeRegistry $typeRegistry,
        private ChainUpcaster $upcaster
    ) {}

    public function deserialize(array $row): DomainEvent
    {
        $eventType = $row['event_type'];
        $payload = json_decode($row['payload'], true, 512, JSON_THROW_ON_ERROR);
        $metadata = json_decode($row['metadata'], true, 512, JSON_THROW_ON_ERROR);
        $version = $metadata['version'] ?? 1;

        // Upcast to current version
        $upcasted = $this->upcaster->upcast($eventType, $payload, $metadata, $version);

        // Now hydrate with current event class
        $className = $this->typeRegistry->getClassName($eventType);

        return $this->hydrate($className, $upcasted['payload'], $upcasted['metadata']);
    }
}
```

## Common Versioning Scenarios

### Adding a Field

**Problem:** New field needed, old events don't have it.

```php
// V1: OrderCreatedEvent { orderId, customerId }
// V2: OrderCreatedEvent { orderId, customerId, currency }

final readonly class OrderCreatedV1ToV2Upcaster implements UpcasterInterface
{
    public function canUpcast(string $eventType, int $version): bool
    {
        return $eventType === 'OrderCreated' && $version === 1;
    }

    public function upcast(array $payload, array $metadata): array
    {
        return [
            'payload' => [
                ...$payload,
                'currency' => 'USD',  // Default value
            ],
            'metadata' => [...$metadata, 'version' => 2],
            'version' => 2,
        ];
    }
}
```

### Renaming a Field

**Problem:** Field name changed, old events use old name.

```php
// V1: OrderCreatedEvent { order_id, customer_id }
// V2: OrderCreatedEvent { orderId, customerId }

final readonly class OrderCreatedV1ToV2Upcaster implements UpcasterInterface
{
    public function upcast(array $payload, array $metadata): array
    {
        return [
            'payload' => [
                'orderId' => $payload['order_id'],
                'customerId' => $payload['customer_id'],
            ],
            'metadata' => [...$metadata, 'version' => 2],
            'version' => 2,
        ];
    }
}
```

### Changing Field Type

**Problem:** Field type changed (e.g., int to Money object).

```php
// V1: OrderConfirmedEvent { totalAmount: 15000 }  // cents as int
// V2: OrderConfirmedEvent { total: { amount: 15000, currency: "USD" } }

final readonly class OrderConfirmedV1ToV2Upcaster implements UpcasterInterface
{
    public function upcast(array $payload, array $metadata): array
    {
        return [
            'payload' => [
                'orderId' => $payload['orderId'],
                'total' => [
                    'amount' => $payload['totalAmount'],
                    'currency' => 'USD',  // Assumed default
                ],
                'confirmedAt' => $payload['confirmedAt'],
            ],
            'metadata' => [...$metadata, 'version' => 2],
            'version' => 2,
        ];
    }
}
```

### Splitting an Event

**Problem:** One event needs to become two events.

```php
// V1: OrderCompletedEvent { orderId, paidAt, shippedAt }
// V2: Separate events: OrderPaidEvent + OrderShippedEvent

final readonly class OrderCompletedSplitUpcaster implements UpcasterInterface
{
    public function canUpcast(string $eventType, int $version): bool
    {
        return $eventType === 'OrderCompleted' && $version === 1;
    }

    // Returns array of events
    public function upcastToMultiple(array $payload, array $metadata): array
    {
        return [
            [
                'type' => 'OrderPaid',
                'payload' => [
                    'orderId' => $payload['orderId'],
                    'paidAt' => $payload['paidAt'],
                ],
                'metadata' => [...$metadata, 'version' => 1],
            ],
            [
                'type' => 'OrderShipped',
                'payload' => [
                    'orderId' => $payload['orderId'],
                    'shippedAt' => $payload['shippedAt'],
                ],
                'metadata' => [...$metadata, 'version' => 1],
            ],
        ];
    }
}
```

### Merging Events

**Problem:** Two events should become one.

```php
// V1: Separate OrderPaid + OrderShipped
// V2: Combined OrderCompleted

// Usually handled by projection logic rather than upcasting
// Keep old events, project them into new read model structure
```

### Removing a Field

**Problem:** Field no longer needed.

```php
// V1: OrderCreatedEvent { orderId, customerId, legacyField }
// V2: OrderCreatedEvent { orderId, customerId }

final readonly class OrderCreatedV1ToV2Upcaster implements UpcasterInterface
{
    public function upcast(array $payload, array $metadata): array
    {
        // Simply don't include the removed field
        return [
            'payload' => [
                'orderId' => $payload['orderId'],
                'customerId' => $payload['customerId'],
                // legacyField omitted
            ],
            'metadata' => [...$metadata, 'version' => 2],
            'version' => 2,
        ];
    }
}
```

## Weak Schema Approach

Alternative to upcasting: handle missing/extra fields gracefully.

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public string $currency = 'USD',      // Default for V1 events
        public ?string $notes = null,         // Optional field
        public array $extraData = []          // Catch-all for future fields
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            orderId: $data['orderId'],
            customerId: $data['customerId'],
            currency: $data['currency'] ?? 'USD',
            notes: $data['notes'] ?? null,
            extraData: array_diff_key($data, array_flip([
                'orderId', 'customerId', 'currency', 'notes'
            ]))
        );
    }
}
```

## Event Type Registry

Map event type names to classes (and handle renames).

```php
<?php

declare(strict_types=1);

namespace Infrastructure\EventStore;

final class EventTypeRegistry
{
    /** @var array<string, class-string> */
    private array $typeToClass = [];

    /** @var array<class-string, string> */
    private array $classToType = [];

    /** @var array<string, string> */
    private array $aliases = [];

    public function register(string $typeName, string $className): void
    {
        $this->typeToClass[$typeName] = $className;
        $this->classToType[$className] = $typeName;
    }

    public function registerAlias(string $oldName, string $newName): void
    {
        $this->aliases[$oldName] = $newName;
    }

    public function getClassName(string $typeName): string
    {
        // Resolve aliases
        while (isset($this->aliases[$typeName])) {
            $typeName = $this->aliases[$typeName];
        }

        if (!isset($this->typeToClass[$typeName])) {
            throw new UnknownEventTypeException($typeName);
        }

        return $this->typeToClass[$typeName];
    }

    public function getTypeName(string $className): string
    {
        if (!isset($this->classToType[$className])) {
            throw new UnregisteredEventClassException($className);
        }

        return $this->classToType[$className];
    }
}

// Configuration
$registry->register('OrderCreated', OrderCreatedEvent::class);
$registry->register('OrderConfirmed', OrderConfirmedEvent::class);

// Handle renamed events
$registry->registerAlias('OrderCreatedV1', 'OrderCreated');
$registry->registerAlias('order.created', 'OrderCreated');
```

## Best Practices

### 1. Always Version Events

```php
final readonly class OrderCreatedEvent
{
    public const VERSION = 2;

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
        public int $version = OrderCreatedEvent::VERSION
    ) {}
}
```

### 2. Keep Old Event Classes (or Upcasters)

Never delete old event definitions until all events are migrated.

### 3. Test Upcasters

```php
final class OrderCreatedUpcasterTest extends TestCase
{
    public function testUpcastsV1ToV2(): void
    {
        $upcaster = new OrderCreatedV1ToV2Upcaster();

        $v1Payload = ['orderId' => '123', 'customerId' => '456'];
        $v1Metadata = ['version' => 1];

        $result = $upcaster->upcast($v1Payload, $v1Metadata);

        self::assertEquals('USD', $result['payload']['currency']);
        self::assertEquals(2, $result['version']);
    }
}
```

### 4. Document Changes

```php
/**
 * OrderCreatedEvent
 *
 * Version History:
 * - V1 (2023-01-01): Initial version { orderId, customerId }
 * - V2 (2023-06-15): Added currency field { orderId, customerId, currency }
 * - V3 (2024-02-01): Added metadata field { orderId, customerId, currency, createdBy }
 */
final readonly class OrderCreatedEvent
{
    public const VERSION = 3;
}
```

## Detection Patterns

```bash
# Find upcasters
Grep: "implements.*Upcaster|class.*Upcaster" --glob "**/*.php"

# Check for version in events
Grep: "const VERSION|->version|metadata.*version" --glob "**/Event/**/*.php"

# Find event type registry
Grep: "EventTypeRegistry|typeToClass|classToType" --glob "**/*.php"

# Check for schema evolution handling
Grep: "\?\? '|?? null|array_diff_key" --glob "**/Event/**/*.php"

# Find event aliases
Grep: "registerAlias|aliases" --glob "**/*.php"
```
