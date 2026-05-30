---
name: create-aggregate
description: Generates DDD Aggregates for PHP 8.4. Creates consistency boundaries with root entity, domain events, and invariant protection. Includes unit tests.
---

# Aggregate Generator

Generate DDD-compliant Aggregates with root, domain events, and tests.

## Aggregate Characteristics

- **Consistency boundary**: All changes atomic
- **Root entity**: Single entry point
- **Transactional consistency**: Invariants always valid
- **Domain events**: Records what happened
- **Encapsulation**: Children accessed through root
- **Identity**: Referenced by root ID

---

## Generation Process

### Step 1: Generate Base AggregateRoot

Place alongside other shared domain primitives.

1. `AggregateRoot.php` — Base class with event recording

### Step 2: Generate Aggregate Root Entity

Place inside the bounded context's domain code.

1. `{Name}.php` — Main aggregate root

### Step 3: Generate Child Entities (if needed)

Co-located with the aggregate root in the same `Entity/` folder.

1. `{ChildName}.php` — Child entity inside aggregate

### Step 4: Generate Domain Events

Place in a sibling `Event/` folder under the bounded context.

1. `{Name}CreatedEvent.php`
2. `{Name}{Action}Event.php` for each behavior

### Step 5: Generate Tests

Mirror the production-code path under `tests/Unit/`.

---

## File Placement

| Component | Path |
|-----------|------|
| Base AggregateRoot | `src/{architecture-path}/Aggregate/AggregateRoot.php` |
| Aggregate Entity | `src/{architecture-path}/Entity/{Name}.php` |
| Child Entities | `src/{architecture-path}/Entity/{ChildName}.php` |
| Domain Events | `src/{architecture-path}/Event/{Name}CreatedEvent.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Entity/{Name}Test.php` |

> `{architecture-path}` represents your project's architecture-specific folders (e.g. `Domain/Shared` and `Domain/{BoundedContext}` in DDD-Layered, `{BoundedContext}/Domain` in Package-by-Feature). Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Aggregate Root | `{Name}` | `Order` |
| Child Entity | `{Parent}{Name}` | `OrderLine` |
| Created Event | `{Name}CreatedEvent` | `OrderCreatedEvent` |
| State Event | `{Name}{Action}Event` | `OrderConfirmedEvent` |

---

## Quick Template Reference

### Base AggregateRoot

```php
abstract class AggregateRoot
{
    private array $events = [];

    protected function recordEvent(DomainEvent $event): void
    {
        $this->events[] = $event;
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

### Aggregate Root Entity

```php
final class {Name} extends AggregateRoot
{
    private {Name}Status $status;

    private function __construct(
        private readonly {Name}Id $id,
        {properties}
    ) {
        $this->status = {Name}Status::Draft;
    }

    public static function create({Name}Id $id, {params}): self
    {
        $aggregate = new self($id, {args});

        $aggregate->recordEvent(new {Name}CreatedEvent(...));

        return $aggregate;
    }

    public function {behavior}({params}): void
    {
        $this->ensureValidState();
        // Apply change
        $this->recordEvent(new {Name}{Behavior}Event(...));
    }
}
```

### Child Entity

```php
final readonly class {ChildName}
{
    public function __construct(
        public {PropertyType} $property1,
        public {PropertyType} $property2
    ) {}

    public function total(): Money
    {
        return $this->unitPrice->multiply($this->quantity);
    }
}
```

---

## Design Rules

| Rule | Good | Bad |
|------|------|-----|
| Transaction Boundary | One aggregate per transaction | Multiple aggregates |
| Reference | By ID only | Full entity reference |
| Size | Small, focused | Large with many collections |
| Invariants | Always valid | Can be in invalid state |
| Events | Record all state changes | No event recording |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Large Aggregate | Performance issues | Split into smaller aggregates |
| Entity References | Tight coupling | Use IDs only |
| Public Setters | No invariant protection | Use behavior methods |
| Missing Events | Can't track history | Record event for each change |
| No Root | Multiple entry points | Single root entity |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — AggregateRoot, Entity, Child Entity, Test templates
- `references/examples.md` — Order aggregate with OrderLine, events, and tests
