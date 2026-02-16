# Iterator Pattern Examples

## Order Collection with Iterator

### Order Entity

**File:** `src/Domain/Order/Entity/Order.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Shared\ValueObject\Money;

final readonly class Order
{
    public function __construct(
        private string $id,
        private Money $total,
        private string $status = 'pending'
    ) {}

    public function id(): string
    {
        return $this->id;
    }

    public function total(): Money
    {
        return $this->total;
    }

    public function status(): string
    {
        return $this->status;
    }

    public function isPending(): bool
    {
        return $this->status === 'pending';
    }

    public function isCompleted(): bool
    {
        return $this->status === 'completed';
    }
}
```

---

### OrderCollection

**File:** `src/Domain/Order/Collection/OrderCollection.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Collection;

use Domain\Order\Entity\Order;

final readonly class OrderCollection implements \IteratorAggregate, \Countable
{
    /**
     * @param array<Order> $orders
     */
    public function __construct(
        private array $orders = []
    ) {}

    public function getIterator(): \Traversable
    {
        return new \ArrayIterator($this->orders);
    }

    public function count(): int
    {
        return count($this->orders);
    }

    public function add(Order $order): self
    {
        $orders = $this->orders;
        $orders[] = $order;

        return new self($orders);
    }

    public function filterByStatus(string $status): self
    {
        $filtered = array_filter(
            $this->orders,
            fn(Order $order): bool => $order->status() === $status
        );

        return new self(array_values($filtered));
    }

    public function totalAmount(): int
    {
        $total = 0;

        foreach ($this->orders as $order) {
            $total += $order->total()->cents();
        }

        return $total;
    }

    public function toArray(): array
    {
        return $this->orders;
    }
}
```

---

## User Collection with Custom Iterator

### User Entity

**File:** `src/Domain/User/Entity/User.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Entity;

final readonly class User
{
    public function __construct(
        private string $id,
        private string $email,
        private bool $active = true
    ) {}

    public function id(): string
    {
        return $this->id;
    }

    public function email(): string
    {
        return $this->email;
    }

    public function isActive(): bool
    {
        return $this->active;
    }
}
```

---

### UserCollection

**File:** `src/Domain/User/Collection/UserCollection.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Collection;

use Domain\User\Entity\User;
use Domain\User\Iterator\UserIterator;
use Domain\User\Iterator\ActiveUserIterator;

final readonly class UserCollection implements \IteratorAggregate, \Countable
{
    /**
     * @param array<User> $users
     */
    public function __construct(
        private array $users = []
    ) {}

    public function getIterator(): \Traversable
    {
        return new UserIterator($this->users);
    }

    public function getActiveIterator(): \Traversable
    {
        return new ActiveUserIterator($this->users);
    }

    public function count(): int
    {
        return count($this->users);
    }

    public function add(User $user): self
    {
        $users = $this->users;
        $users[] = $user;

        return new self($users);
    }

    public function findById(string $id): ?User
    {
        foreach ($this->users as $user) {
            if ($user->id() === $id) {
                return $user;
            }
        }

        return null;
    }

    public function toArray(): array
    {
        return $this->users;
    }
}
```

---

### ActiveUserIterator

**File:** `src/Domain/User/Iterator/ActiveUserIterator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Iterator;

use Domain\User\Entity\User;

final class ActiveUserIterator implements \Iterator
{
    private int $position = 0;
    private array $activeUsers = [];

    /**
     * @param array<User> $users
     */
    public function __construct(array $users)
    {
        $this->activeUsers = array_values(
            array_filter($users, fn(User $user): bool => $user->isActive())
        );
    }

    public function current(): User
    {
        return $this->activeUsers[$this->position];
    }

    public function next(): void
    {
        ++$this->position;
    }

    public function key(): int
    {
        return $this->position;
    }

    public function valid(): bool
    {
        return isset($this->activeUsers[$this->position]);
    }

    public function rewind(): void
    {
        $this->position = 0;
    }

    public function count(): int
    {
        return count($this->activeUsers);
    }
}
```

---

## Paginated Results

### PaginatedResultIterator

**File:** `src/Application/Iterator/PaginatedResultIterator.php`

```php
<?php

declare(strict_types=1);

namespace Application\Iterator;

final class PaginatedResultIterator implements \Iterator
{
    private int $currentPage = 0;
    private int $position = 0;

    /**
     * @param array<mixed> $items
     */
    public function __construct(
        private readonly array $items,
        private readonly int $pageSize = 20
    ) {}

    public function current(): mixed
    {
        return $this->items[$this->position];
    }

    public function next(): void
    {
        ++$this->position;

        if ($this->position % $this->pageSize === 0 && $this->valid()) {
            ++$this->currentPage;
        }
    }

    public function key(): int
    {
        return $this->position;
    }

    public function valid(): bool
    {
        return isset($this->items[$this->position]);
    }

    public function rewind(): void
    {
        $this->position = 0;
        $this->currentPage = 0;
    }

    public function getCurrentPage(): int
    {
        return $this->currentPage;
    }

    public function getTotalPages(): int
    {
        if (empty($this->items)) {
            return 0;
        }

        return (int) ceil(count($this->items) / $this->pageSize);
    }

    public function getPageItems(int $page): array
    {
        $offset = $page * $this->pageSize;

        return array_slice($this->items, $offset, $this->pageSize);
    }
}
```

---

## Product Iterator

### Product Value Object

**File:** `src/Domain/Product/ValueObject/Product.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Product\ValueObject;

use Domain\Shared\ValueObject\Money;

final readonly class Product
{
    public function __construct(
        private string $id,
        private string $name,
        private Money $price,
        private bool $inStock = true
    ) {}

    public function id(): string
    {
        return $this->id;
    }

    public function name(): string
    {
        return $this->name;
    }

    public function price(): Money
    {
        return $this->price;
    }

    public function isInStock(): bool
    {
        return $this->inStock;
    }
}
```

---

### ProductCollection

**File:** `src/Domain/Product/Collection/ProductCollection.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Product\Collection;

use Domain\Product\ValueObject\Product;

final readonly class ProductCollection implements \IteratorAggregate, \Countable
{
    /**
     * @param array<Product> $products
     */
    public function __construct(
        private array $products = []
    ) {}

    public function getIterator(): \Traversable
    {
        return new \ArrayIterator($this->products);
    }

    public function count(): int
    {
        return count($this->products);
    }

    public function inStock(): self
    {
        $inStock = array_filter(
            $this->products,
            fn(Product $product): bool => $product->isInStock()
        );

        return new self(array_values($inStock));
    }

    public function sortByPrice(bool $ascending = true): self
    {
        $products = $this->products;

        usort($products, function (Product $a, Product $b) use ($ascending): int {
            $result = $a->price()->cents() <=> $b->price()->cents();

            return $ascending ? $result : -$result;
        });

        return new self($products);
    }

    public function toArray(): array
    {
        return $this->products;
    }
}
```

---

## Unit Tests

### OrderCollectionTest

**File:** `tests/Unit/Domain/Order/Collection/OrderCollectionTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Collection;

use Domain\Order\Collection\OrderCollection;
use Domain\Order\Entity\Order;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderCollection::class)]
final class OrderCollectionTest extends TestCase
{
    public function testIteratesOverOrders(): void
    {
        $collection = new OrderCollection([
            new Order(id: '1', total: Money::cents(100)),
            new Order(id: '2', total: Money::cents(200)),
        ]);

        $count = 0;
        foreach ($collection as $order) {
            ++$count;
            self::assertInstanceOf(Order::class, $order);
        }

        self::assertSame(2, $count);
    }

    public function testCountsOrders(): void
    {
        $collection = new OrderCollection([
            new Order(id: '1', total: Money::cents(100)),
            new Order(id: '2', total: Money::cents(200)),
        ]);

        self::assertSame(2, $collection->count());
    }

    public function testAddsOrder(): void
    {
        $collection = new OrderCollection();
        $newCollection = $collection->add(
            new Order(id: '1', total: Money::cents(100))
        );

        self::assertSame(0, $collection->count());
        self::assertSame(1, $newCollection->count());
    }

    public function testFiltersByStatus(): void
    {
        $collection = new OrderCollection([
            new Order(id: '1', total: Money::cents(100), status: 'pending'),
            new Order(id: '2', total: Money::cents(200), status: 'completed'),
            new Order(id: '3', total: Money::cents(150), status: 'pending'),
        ]);

        $pending = $collection->filterByStatus('pending');

        self::assertSame(2, $pending->count());
    }

    public function testCalculatesTotalAmount(): void
    {
        $collection = new OrderCollection([
            new Order(id: '1', total: Money::cents(100)),
            new Order(id: '2', total: Money::cents(200)),
        ]);

        self::assertSame(300, $collection->totalAmount());
    }
}
```

---

### ActiveUserIteratorTest

**File:** `tests/Unit/Domain/User/Iterator/ActiveUserIteratorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\User\Iterator;

use Domain\User\Iterator\ActiveUserIterator;
use Domain\User\Entity\User;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ActiveUserIterator::class)]
final class ActiveUserIteratorTest extends TestCase
{
    public function testIteratesOnlyActiveUsers(): void
    {
        $users = [
            new User(id: '1', email: 'user1@test.com', active: true),
            new User(id: '2', email: 'user2@test.com', active: false),
            new User(id: '3', email: 'user3@test.com', active: true),
        ];

        $iterator = new ActiveUserIterator($users);

        $count = 0;
        foreach ($iterator as $user) {
            ++$count;
            self::assertTrue($user->isActive());
        }

        self::assertSame(2, $count);
    }

    public function testRewindsIterator(): void
    {
        $users = [
            new User(id: '1', email: 'user1@test.com', active: true),
            new User(id: '2', email: 'user2@test.com', active: true),
        ];

        $iterator = new ActiveUserIterator($users);

        foreach ($iterator as $user) {
            // First iteration
        }

        $iterator->rewind();
        self::assertTrue($iterator->valid());
        self::assertSame('1', $iterator->current()->id());
    }
}
```
