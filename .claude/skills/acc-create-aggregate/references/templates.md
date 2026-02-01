# Aggregate Pattern Templates

## Aggregate Root Template

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\ValueObject\{Name}Id;
use Domain\{BoundedContext}\Enum\{Name}Status;
use Domain\{BoundedContext}\Event\{Events};
use Domain\Shared\Aggregate\AggregateRoot;

final class {Name} extends AggregateRoot
{
    private {Name}Status $status;
    {privateProperties}
    private DateTimeImmutable $createdAt;

    private function __construct(
        private readonly {Name}Id $id,
        {constructorProperties}
    ) {
        $this->status = {Name}Status::default();
        $this->createdAt = new DateTimeImmutable();
    }

    public static function create(
        {Name}Id $id,
        {factoryProperties}
    ): self {
        $aggregate = new self($id, {constructorArgs});

        $aggregate->recordEvent(new {Name}CreatedEvent(
            {eventProperties}
        ));

        return $aggregate;
    }

    public function id(): {Name}Id
    {
        return $this->id;
    }

    {behaviorMethods}
}
```

---

## Base Aggregate Root

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Aggregate;

use Domain\Shared\Event\DomainEvent;

abstract class AggregateRoot
{
    /** @var array<DomainEvent> */
    private array $events = [];

    protected function recordEvent(DomainEvent $event): void
    {
        $this->events[] = $event;
    }

    /**
     * @return array<DomainEvent>
     */
    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }

    public function hasUncommittedEvents(): bool
    {
        return !empty($this->events);
    }
}
```

---

## Child Entity Template

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\ValueObject\{ValueObjects};

final readonly class {ChildName}
{
    public function __construct(
        public {PropertyType} $property1,
        public {PropertyType} $property2,
        {additionalProperties}
    ) {}

    {methods}
}
```

---

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\Entity\{Name};
use Domain\{BoundedContext}\ValueObject\{Name}Id;
use Domain\{BoundedContext}\Event\{Name}CreatedEvent;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}::class)]
final class {Name}Test extends TestCase
{
    public function testCreatesWithEvent(): void
    {
        $aggregate = {Name}::create(
            id: {Name}Id::generate(),
            {factoryParams}
        );

        self::assertSame({Name}Status::default(), $aggregate->status());

        $events = $aggregate->releaseEvents();
        self::assertCount(1, $events);
        self::assertInstanceOf({Name}CreatedEvent::class, $events[0]);
    }

    public function test{Behavior}RecordsEvent(): void
    {
        $aggregate = $this->create{Name}();

        $aggregate->{behavior}({params});

        $events = $aggregate->releaseEvents();
        self::assertInstanceOf({Event}::class, end($events));
    }

    public function testEnforcesInvariant(): void
    {
        $aggregate = $this->create{Name}();

        $this->expectException({Exception}::class);

        $aggregate->{invalidBehavior}();
    }

    private function create{Name}(): {Name}
    {
        return {Name}::create(
            id: {Name}Id::generate(),
            {factoryParams}
        );
    }
}
```

---

## Design Rules

### Single Transaction Boundary

```php
// GOOD: One aggregate per transaction
$order = $this->orderRepository->findById($orderId);
$order->confirm();
$this->orderRepository->save($order);

// BAD: Multiple aggregates in one transaction
$order = $this->orderRepository->findById($orderId);
$inventory = $this->inventoryRepository->findByProductId($productId);
$order->confirm();
$inventory->reserve($quantity);  // Different aggregate!
```

### Reference by ID

```php
// GOOD: Reference by ID
final class Order
{
    private readonly CustomerId $customerId;  // Just the ID
}

// BAD: Direct reference
final class Order
{
    private Customer $customer;  // Full entity reference
}
```

### Small Aggregates

```php
// GOOD: Small, focused aggregate
final class Order
{
    private readonly OrderId $id;
    private array $lines = [];  // Limited collection
}

// BAD: Large aggregate
final class Customer
{
    private array $orders = [];      // All orders ever!
    private array $addresses = [];   // All addresses!
}
```
