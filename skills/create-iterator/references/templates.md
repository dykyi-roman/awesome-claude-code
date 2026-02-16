# Iterator Pattern Templates

## Basic Iterator

**File:** `src/Domain/{BoundedContext}/Iterator/{Name}Iterator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Iterator;

final class {Name}Iterator implements \Iterator
{
    private int $position = 0;

    /**
     * @param array<{ElementType}> $items
     */
    public function __construct(
        private readonly array $items
    ) {}

    public function current(): {ElementType}
    {
        return $this->items[$this->position];
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
        return isset($this->items[$this->position]);
    }

    public function rewind(): void
    {
        $this->position = 0;
    }
}
```

---

## Filtered Iterator

**File:** `src/Domain/{BoundedContext}/Iterator/Filtered{Name}Iterator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Iterator;

final class Filtered{Name}Iterator implements \Iterator
{
    private int $position = 0;
    private array $filteredItems = [];

    /**
     * @param array<{ElementType}> $items
     * @param callable({ElementType}): bool $filter
     */
    public function __construct(
        array $items,
        callable $filter
    ) {
        $this->filteredItems = array_values(array_filter($items, $filter));
    }

    public function current(): {ElementType}
    {
        return $this->filteredItems[$this->position];
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
        return isset($this->filteredItems[$this->position]);
    }

    public function rewind(): void
    {
        $this->position = 0;
    }
}
```

---

## Iterable Collection (IteratorAggregate)

**File:** `src/Domain/{BoundedContext}/Collection/{Name}Collection.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Collection;

use Domain\{BoundedContext}\Iterator\{Name}Iterator;

final readonly class {Name}Collection implements \IteratorAggregate, \Countable
{
    /**
     * @param array<{ElementType}> $items
     */
    public function __construct(
        private array $items = []
    ) {}

    public function getIterator(): \Traversable
    {
        return new {Name}Iterator($this->items);
    }

    public function count(): int
    {
        return count($this->items);
    }

    public function add({ElementType} $item): self
    {
        $items = $this->items;
        $items[] = $item;

        return new self($items);
    }

    public function toArray(): array
    {
        return $this->items;
    }
}
```

---

## Order Collection

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

    public function filter(callable $predicate): self
    {
        return new self(array_filter($this->orders, $predicate));
    }

    public function map(callable $mapper): array
    {
        return array_map($mapper, $this->orders);
    }

    public function toArray(): array
    {
        return $this->orders;
    }
}
```

---

## Paginated Iterator

**File:** `src/Domain/{BoundedContext}/Iterator/PaginatedIterator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Iterator;

final class PaginatedIterator implements \Iterator
{
    private int $currentPage = 0;
    private int $position = 0;

    /**
     * @param array<{ElementType}> $items
     */
    public function __construct(
        private readonly array $items,
        private readonly int $pageSize = 10
    ) {}

    public function current(): {ElementType}
    {
        return $this->items[$this->position];
    }

    public function next(): void
    {
        ++$this->position;

        if ($this->position % $this->pageSize === 0) {
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
        return (int) ceil(count($this->items) / $this->pageSize);
    }
}
```

---

## User Iterator

**File:** `src/Domain/User/Iterator/UserIterator.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Iterator;

use Domain\User\Entity\User;

final class UserIterator implements \Iterator
{
    private int $position = 0;

    /**
     * @param array<User> $users
     */
    public function __construct(
        private readonly array $users
    ) {}

    public function current(): User
    {
        return $this->users[$this->position];
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
        return isset($this->users[$this->position]);
    }

    public function rewind(): void
    {
        $this->position = 0;
    }
}
```

---

## Active User Iterator (Filtered)

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
}
```
