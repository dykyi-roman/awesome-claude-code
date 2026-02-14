---
name: acc-create-entity
description: Generates DDD Entities for PHP 8.5. Creates identity-based objects with behavior, state transitions, and invariant protection. Includes unit tests.
---

# Entity Generator

Generate DDD-compliant Entities with identity, behavior, and tests.

## Entity Characteristics

- **Identity**: Has unique identifier (ID)
- **Lifecycle**: Created, modified, potentially deleted
- **Behavior**: Contains domain logic (not just data)
- **Invariants**: Protects business rules
- **State transitions**: Controlled mutations
- **No public setters**: State changed via behavior methods

## Entity Components

### Core Structure

Every Entity consists of:

| Component | Description |
|-----------|-------------|
| Identity (`{Name}Id`) | Unique identifier, readonly, set at construction |
| Status Enum | Lifecycle states with transition rules |
| Constructor | Sets identity, initial status, timestamps, validates invariants |
| Behavior methods | Domain actions (`confirm()`, `cancel()`, `addLine()`) |
| Query methods | State checks (`isActive()`, `canBeConfirmed()`, `isEmpty()`) |
| `touch()` helper | Updates `$updatedAt` timestamp on mutations |

### Supporting Files

| File | Location |
|------|----------|
| Entity | `src/Domain/{BoundedContext}/Entity/{Name}.php` |
| Status Enum | `src/Domain/{BoundedContext}/Enum/{Name}Status.php` |
| Exceptions | `src/Domain/{BoundedContext}/Exception/{...}Exception.php` |
| Unit Test | `tests/Unit/Domain/{BoundedContext}/Entity/{Name}Test.php` |

## Entity Design Principles

### 1. Behavior Over Data

Entities must encapsulate domain logic, not just hold data. Use meaningful behavior methods (`confirm()`, `activate()`) instead of anemic setters (`setStatus()`). Each behavior method enforces invariants before mutating state.

### 2. Invariant Protection

Every mutation method must validate business rules before making changes. Common invariants:
- State guards (e.g., can only modify draft orders)
- Value constraints (e.g., quantity must be positive)
- Relationship constraints (e.g., cannot confirm empty order)

### 3. State Transitions

Use a Status enum with explicit transition rules. The enum defines `canTransitionTo()` to enforce valid state machines. Entities delegate transition validation to the enum.

## Generation Process

When asked to create an Entity:

1. **Identify the identity** (what makes it unique)
2. **Define the lifecycle** (statuses/states)
3. **List invariants** (business rules to protect)
4. **Design behavior methods** (what it can do)
5. **Generate tests** for behavior and invariants

## Naming Conventions

| Concept | Method Pattern | Exception |
|---------|----------------|-----------|
| State change | `confirm()`, `activate()`, `cancel()` | `InvalidStateTransitionException` |
| Add relation | `addLine()`, `addItem()` | `CannotModifyException` |
| Update property | `changeEmail()`, `updateName()` | `InvalidValueException` |
| Query state | `isActive()`, `canBeConfirmed()` | N/A (boolean return) |

## Quick Template Reference

### Entity skeleton

```php
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

    public function id(): {Name}Id { return $this->id; }
    public function status(): {Name}Status { return $this->status; }

    {behaviorMethods}

    private function touch(): void { $this->updatedAt = new DateTimeImmutable(); }
}
```

### Test skeleton

```php
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
        return new {Name}(id: {Name}Id::generate(), {testConstructorArgs});
    }
}
```

## Usage

To generate an Entity, provide:
- Name (e.g., "Order", "User")
- Bounded Context (e.g., "Order", "User")
- Identity type (e.g., "OrderId")
- States/Statuses
- Key behaviors needed
- Invariants to protect

## References

- `references/templates.md` — full PHP code templates (Entity, Test, State Transition Enum, design principle code samples)
- `references/examples.md` — complete Order Entity and User Entity implementation examples
