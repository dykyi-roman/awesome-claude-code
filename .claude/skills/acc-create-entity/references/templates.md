# Entity Generator Templates

## Entity Template

**File:** `src/Domain/{BoundedContext}/Entity/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\ValueObject\{Name}Id;
use Domain\{BoundedContext}\Enum\{Name}Status;
use Domain\{BoundedContext}\Exception\{Exceptions};

final class {Name}
{
    private {Name}Status $status;
    private DateTimeImmutable $createdAt;
    private ?DateTimeImmutable $updatedAt = null;

    public function __construct(
        private readonly {Name}Id $id,
        {constructorProperties}
    ) {
        {constructorValidation}
        $this->status = {Name}Status::default();
        $this->createdAt = new DateTimeImmutable();
    }

    public function id(): {Name}Id
    {
        return $this->id;
    }

    public function status(): {Name}Status
    {
        return $this->status;
    }

    {behaviorMethods}

    private function touch(): void
    {
        $this->updatedAt = new DateTimeImmutable();
    }
}
```

## Test Template

**File:** `tests/Unit/Domain/{BoundedContext}/Entity/{Name}Test.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\Entity\{Name};
use Domain\{BoundedContext}\ValueObject\{Name}Id;
use Domain\{BoundedContext}\Enum\{Name}Status;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}::class)]
final class {Name}Test extends TestCase
{
    public function testCreatesWithValidData(): void
    {
        $entity = $this->createEntity();

        self::assertInstanceOf({Name}Id::class, $entity->id());
        self::assertSame({Name}Status::default(), $entity->status());
    }

    {behaviorTests}

    private function createEntity(): {Name}
    {
        return new {Name}(
            id: {Name}Id::generate(),
            {testConstructorArgs}
        );
    }
}
```

## State Transition Enum Template

**File:** `src/Domain/{BoundedContext}/Enum/{Name}Status.php`

```php
enum OrderStatus: string
{
    case Draft = 'draft';
    case Confirmed = 'confirmed';
    case Paid = 'paid';
    case Shipped = 'shipped';
    case Cancelled = 'cancelled';

    public function canTransitionTo(self $target): bool
    {
        return match($this) {
            self::Draft => in_array($target, [self::Confirmed, self::Cancelled]),
            self::Confirmed => in_array($target, [self::Paid, self::Cancelled]),
            self::Paid => in_array($target, [self::Shipped, self::Cancelled]),
            self::Shipped => false,
            self::Cancelled => false,
        };
    }

    public function canBeCancelled(): bool
    {
        return $this->canTransitionTo(self::Cancelled);
    }
}
```

## Design Principle Templates

### Behavior Over Data

```php
// BAD: Anemic entity
class Order
{
    public function setStatus(string $status): void
    {
        $this->status = $status;
    }
}

// GOOD: Rich entity with behavior
class Order
{
    public function confirm(): void
    {
        if (!$this->canBeConfirmed()) {
            throw new InvalidStateTransitionException();
        }
        $this->status = OrderStatus::Confirmed;
        $this->confirmedAt = new DateTimeImmutable();
    }

    private function canBeConfirmed(): bool
    {
        return $this->status === OrderStatus::Draft && !empty($this->lines);
    }
}
```

### Invariant Protection

```php
// Protect invariants in every method
public function addLine(Product $product, int $quantity): void
{
    // Invariant: Can only modify draft orders
    if ($this->status !== OrderStatus::Draft) {
        throw new CannotModifyConfirmedOrderException();
    }

    // Invariant: Quantity must be positive
    if ($quantity <= 0) {
        throw new InvalidQuantityException();
    }

    $this->lines[] = new OrderLine($product, $quantity);
}
```
