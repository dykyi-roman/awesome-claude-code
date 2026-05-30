---
name: create-repository
description: Generates Repository abstraction and concrete implementation stubs for PHP 8.4. The Repository pattern from DDD provides a collection-like interface for retrieving and persisting aggregates. Placement of the abstraction vs concrete implementation varies by architecture.
---

# Repository Generator

Generate Repository abstraction and concrete implementation stubs following DDD principles.

## Repository Characteristics

- **Abstraction + Concrete**: The pattern is usually split into an abstraction (interface) and one or more concrete implementations (Doctrine, Eloquent, In-Memory). The split enables Dependency Inversion.
- **Works with Aggregates**: One Repository per aggregate root, not per entity
- **Collection-like**: Find, save, remove operations
- **No business logic**: Only persistence operations; business filtering can live in query methods (e.g. `findShippableOrdersForToday()`)
- **Placement varies**: Where the abstraction lives (alongside the domain that uses it, in a Port folder, in a feature folder) is an architectural choice — see File Placement below

---

## Generation Process

### Step 1: Generate Abstraction

Place alongside the aggregate root the repository serves (see File Placement note for per-architecture guidance).

1. `{AggregateRoot}RepositoryInterface.php` — Repository contract

### Step 2: Generate Concrete Implementation

Place at the persistence integration boundary with other ORM/database adapters.

1. `Doctrine{AggregateRoot}Repository.php` — Doctrine implementation

### Step 3: Generate In-Memory Repository (Optional)

Place under the tests tree alongside other test doubles.

1. `InMemory{AggregateRoot}Repository.php` — For unit testing

### Step 4: Generate Integration Tests

Mirror the production persistence path under `tests/Integration/`.

---

## File Placement

| Component | Path |
|-----------|------|
| Abstraction | `src/{architecture-path}/Repository/{AggregateRoot}RepositoryInterface.php` |
| Doctrine Impl | `src/{architecture-path}/Persistence/Doctrine/Doctrine{AggregateRoot}Repository.php` |
| In-Memory | `tests/{architecture-path}/Persistence/InMemory{AggregateRoot}Repository.php` |
| Integration Tests | `tests/Integration/{architecture-path}/Persistence/` |

> `{architecture-path}` represents your project's architecture-specific folders. Repository placement varies by architecture: in Clean / Onion / DDD-Layered the abstraction is conventionally co-located with the aggregate it serves (often in a `Repository/` sub-folder of the bounded context) and the concrete is co-located with other persistence adapters; in Hexagonal it may live in a `Port/` folder; in Package-by-Feature both abstraction and concrete may live inside the feature folder; in MVC there is often just a single `Repositories/` folder without an abstraction split. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `{AggregateRoot}RepositoryInterface` | `OrderRepositoryInterface` |
| Doctrine Impl | `Doctrine{AggregateRoot}Repository` | `DoctrineOrderRepository` |
| In-Memory | `InMemory{AggregateRoot}Repository` | `InMemoryOrderRepository` |

---

## Quick Template Reference

### Interface

```php
interface {AggregateRoot}RepositoryInterface
{
    public function findById({AggregateRoot}Id $id): ?{AggregateRoot};

    public function save({AggregateRoot} $aggregate): void;

    public function remove({AggregateRoot} $aggregate): void;

    public function nextIdentity(): {AggregateRoot}Id;
}
```

### Doctrine Implementation

```php
final readonly class Doctrine{AggregateRoot}Repository implements {AggregateRoot}RepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById({AggregateRoot}Id $id): ?{AggregateRoot}
    {
        return $this->em->find({AggregateRoot}::class, $id->value);
    }

    public function save({AggregateRoot} $aggregate): void
    {
        $this->em->persist($aggregate);
        $this->em->flush();
    }

    public function remove({AggregateRoot} $aggregate): void
    {
        $this->em->remove($aggregate);
        $this->em->flush();
    }

    public function nextIdentity(): {AggregateRoot}Id
    {
        return {AggregateRoot}Id::generate();
    }
}
```

### In-Memory Implementation

```php
final class InMemory{AggregateRoot}Repository implements {AggregateRoot}RepositoryInterface
{
    private array $items = [];

    public function findById({AggregateRoot}Id $id): ?{AggregateRoot}
    {
        return $this->items[$id->value] ?? null;
    }

    public function save({AggregateRoot} $aggregate): void
    {
        $this->items[$aggregate->id()->value] = $aggregate;
    }

    public function clear(): void
    {
        $this->items = [];
    }
}
```

---

## Design Rules

| Rule | Good | Bad |
|------|------|-----|
| Dependency Direction | Client code depends on the abstraction, not on a concrete ORM class | Client code instantiates Doctrine repositories directly |
| Aggregate Scope | Repository per aggregate root | Repository per entity |
| Query Methods | Simple filters; business-shaped finders (`findShippableOrdersForToday`) are acceptable | Business decisions / state changes inside repository methods |
| Identity | `nextIdentity()` method | External ID generation scattered across callers |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Entity Repository | Bypasses aggregate | Only aggregate roots |
| Business Queries | Logic in repository | Use Specification pattern |
| ORM Leak | Client code depends on a concrete ORM class | Depend on the repository abstraction, not the concrete implementation |
| Generic Repository | Too abstract | Specific per aggregate |
| Missing nextIdentity | Can't generate IDs | Add to interface |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Interface, Doctrine, In-Memory, Test templates
- `references/examples.md` — Order, User repositories with Doctrine and In-Memory implementations
