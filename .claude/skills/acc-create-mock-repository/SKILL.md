---
name: acc-create-mock-repository
description: Generates InMemory repository implementations for PHP 8.5 testing. Creates fake repositories with array storage, supporting CRUD operations and queries without database.
---

# Mock Repository Generator

Generates InMemory (Fake) repository implementations for testing.

## Characteristics

- **No database** — stores entities in memory
- **Fast** — no I/O operations
- **Isolated** — fresh state per test
- **Deterministic** — predictable behavior
- **Implements interface** — same contract as real repository

## Template

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use {RepositoryInterface};
use {Entity};
use {EntityId};

final class InMemory{Entity}Repository implements {RepositoryInterface}
{
    /** @var array<string, {Entity}> */
    private array $entities = [];

    public function save({Entity} $entity): void
    {
        $this->entities[$entity->id()->toString()] = $entity;
    }

    public function findById({EntityId} $id): ?{Entity}
    {
        return $this->entities[$id->toString()] ?? null;
    }

    public function delete({Entity} $entity): void
    {
        unset($this->entities[$entity->id()->toString()]);
    }

    /** @return list<{Entity}> */
    public function findAll(): array
    {
        return array_values($this->entities);
    }

    public function clear(): void
    {
        $this->entities = [];
    }
}
```

## Generation Instructions

1. **Read the repository interface:**
   - Extract all method signatures
   - Identify entity type
   - Identify ID type

2. **Generate InMemory implementation:**
   - Array storage keyed by ID
   - Implement all interface methods
   - Add `clear()` for test cleanup

3. **Handle complex queries:**
   - Use `array_filter` for criteria
   - Support specifications if used
   - Implement pagination with `array_slice`

4. **Add test helpers (optional):**
   - `getAll()` — access internal state
   - `has(Id $id)` — check existence
   - `count()` — entity count

5. **File placement:**
   - `tests/Fake/InMemory{Entity}Repository.php`
   - Or `tests/Double/` directory

## Best Practices

1. **Match interface exactly** — same method signatures
2. **Isolate per test** — use `clear()` in tearDown
3. **Avoid complexity** — simple in-memory logic
4. **Document deviations** — if behavior differs from real impl
5. **Consider thread safety** — for parallel tests (usually not needed)

## References

- `references/examples.md` — Complete repository examples (User, Order, Product)
- `references/other-fakes.md` — EventDispatcher, Mailer, Clock fakes
