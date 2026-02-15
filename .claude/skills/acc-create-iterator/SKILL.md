---
name: acc-create-iterator
description: Generates Iterator pattern for PHP 8.4. Creates sequential access to aggregate elements without exposing underlying representation, with iterator interface and iterable collections. Includes unit tests.
---

# Iterator Pattern Generator

Creates Iterator pattern infrastructure for sequential access to collection elements.

## When to Use

| Scenario | Example |
|----------|---------|
| Traverse collections | Order items, user lists, product catalog |
| Multiple traversal algorithms | Forward, backward, filtered iteration |
| Unified collection interface | Standardize iteration across different types |
| Hide collection structure | Encapsulate internal representation |

## Component Characteristics

### Iterator Interface
- Extends \Iterator or \IteratorAggregate
- Provides current(), next(), key(), valid()
- Enables foreach compatibility
- Type-safe element access

### Concrete Iterator
- Implements traversal algorithm
- Maintains iteration state
- Provides filtering/transformation
- Resets to beginning via rewind()

### Iterable Collection
- Implements \IteratorAggregate
- Returns iterator via getIterator()
- Encapsulates collection data
- Supports type-safe operations

---

## Generation Process

### Step 1: Generate Iterator Interface (Optional)

**Path:** `src/Domain/{BoundedContext}/Iterator/`

1. `{Name}IteratorInterface.php` — Custom iterator contract (extends \Iterator)

### Step 2: Generate Concrete Iterator

**Path:** `src/Domain/{BoundedContext}/Iterator/`

1. `{Name}Iterator.php` — Iterator implementation with traversal logic
2. `Filtered{Name}Iterator.php` — Filtered variant (optional)

### Step 3: Generate Iterable Collection

**Path:** `src/Domain/{BoundedContext}/Collection/`

1. `{Name}Collection.php` — Collection implementing \IteratorAggregate

### Step 4: Generate Value Objects (Optional)

**Path:** `src/Domain/{BoundedContext}/ValueObject/`

1. `{Element}.php` — Collection element type

### Step 5: Generate Tests

1. `{Name}IteratorTest.php` — Iterator behavior tests
2. `{Name}CollectionTest.php` — Collection tests

---

## File Placement

| Component | Path |
|-----------|------|
| Iterator Interface | `src/Domain/{BoundedContext}/Iterator/` |
| Concrete Iterator | `src/Domain/{BoundedContext}/Iterator/` |
| Collection | `src/Domain/{BoundedContext}/Collection/` |
| Value Objects | `src/Domain/{BoundedContext}/ValueObject/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Iterator Interface | `{Name}IteratorInterface` | `OrderIteratorInterface` |
| Concrete Iterator | `{Name}Iterator` | `OrderIterator` |
| Filtered Iterator | `Filtered{Name}Iterator` | `FilteredUserIterator` |
| Collection | `{Name}Collection` | `OrderCollection` |
| Test | `{ClassName}Test` | `OrderIteratorTest` |

---

## Quick Template Reference

### Iterator (using \Iterator)

```php
final class {Name}Iterator implements \Iterator
{
    private int $position = 0;

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

### Iterable Collection (using \IteratorAggregate)

```php
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
}
```

---

## Usage Example

```php
// Create collection
$orders = new OrderCollection([
    new Order(id: '1', total: 100),
    new Order(id: '2', total: 200),
    new Order(id: '3', total: 50),
]);

// Iterate with foreach
foreach ($orders as $order) {
    echo $order->total();
}

// Filtered iteration
$filtered = new FilteredOrderIterator(
    orders: $orders,
    filter: fn(Order $o) => $o->total() > 100
);

foreach ($filtered as $order) {
    // Only orders with total > 100
}
```

---

## Common Iterator Patterns

| Domain | Iterators |
|--------|-----------|
| Collections | OrderCollection, UserCollection, ProductCollection |
| Filtering | ActiveUserIterator, PendingOrderIterator |
| Pagination | PaginatedResultIterator, PageIterator |
| Tree Structures | DepthFirstIterator, BreadthFirstIterator |
| Composite | RecursiveIterator, FlatteningIterator |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Mutable iterator state leak | External modification | Use readonly collections |
| Breaking foreach contract | Invalid implementation | Implement all \Iterator methods |
| Expensive current() | Performance issues | Cache current element |
| Missing rewind() | Can't iterate twice | Implement proper rewind() |
| Violating LSP | Inconsistent behavior | Follow SPL iterator contracts |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Iterator, IteratorAggregate, Filtered Iterator templates
- `references/examples.md` — OrderCollection, UserIterator, Pagination with tests
