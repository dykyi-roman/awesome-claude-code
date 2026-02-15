---
name: acc-create-memento
description: Generates Memento pattern for PHP 8.4. Creates state capture and restoration mechanism for undo/redo functionality, with originator, memento, and caretaker components. Includes unit tests.
---

# Memento Pattern Generator

Creates Memento pattern infrastructure for capturing and restoring object state without violating encapsulation.

## When to Use

| Scenario | Example |
|----------|---------|
| Undo/Redo functionality | Document editor, form drafts, game state |
| State snapshots | Transaction rollback, checkpoint systems |
| State history tracking | Audit trail, version history |
| Transactional operations | Multi-step processes with rollback |

## Component Characteristics

### Originator
- Creates memento from current state
- Restores state from memento
- Owns the state being saved
- Knows what to save/restore

### Memento
- Stores originator's internal state
- Immutable snapshot (readonly)
- Protects against external access
- Returns state only to originator

### Caretaker
- Manages memento history
- Requests state saves
- Triggers state restoration
- Never examines memento contents

---

## Generation Process

### Step 1: Generate Memento

**Path:** `src/Domain/{BoundedContext}/Memento/`

1. `{Name}Memento.php` — Immutable state snapshot

### Step 2: Generate Originator

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}.php` — Object with createMemento() and restore() methods

### Step 3: Generate Caretaker

**Path:** `src/Application/{BoundedContext}/`

1. `{Name}History.php` — Manages memento stack for undo/redo

### Step 4: Generate Value Objects (Optional)

**Path:** `src/Domain/{BoundedContext}/ValueObject/`

1. `{State}.php` — State representation value object

### Step 5: Generate Tests

1. `{Name}MementoTest.php` — Memento creation tests
2. `{Name}HistoryTest.php` — Caretaker undo/redo tests

---

## File Placement

| Component | Path |
|-----------|------|
| Memento | `src/Domain/{BoundedContext}/Memento/` |
| Originator | `src/Domain/{BoundedContext}/` |
| Caretaker | `src/Application/{BoundedContext}/` |
| Value Objects | `src/Domain/{BoundedContext}/ValueObject/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Memento | `{Name}Memento` | `DocumentMemento` |
| Originator | `{Name}` | `Document` |
| Caretaker | `{Name}History` | `DocumentHistory` |
| Create Method | `createMemento()` | `createMemento()` |
| Restore Method | `restore()` or `restoreFromMemento()` | `restore()` |
| Test | `{ClassName}Test` | `DocumentMementoTest` |

---

## Quick Template Reference

### Memento

```php
final readonly class {Name}Memento
{
    public function __construct(
        private {StateType} $state,
        private \DateTimeImmutable $createdAt
    ) {}

    public function state(): {StateType}
    {
        return $this->state;
    }

    public function createdAt(): \DateTimeImmutable
    {
        return $this->createdAt;
    }
}
```

### Originator

```php
final class {Name}
{
    private {StateType} $state;

    public function createMemento(): {Name}Memento
    {
        return new {Name}Memento(
            state: $this->state,
            createdAt: new \DateTimeImmutable()
        );
    }

    public function restore({Name}Memento $memento): void
    {
        $this->state = $memento->state();
    }
}
```

### Caretaker

```php
final class {Name}History
{
    private array $mementos = [];
    private int $currentIndex = -1;

    public function save({Name}Memento $memento): void
    {
        $this->mementos = array_slice($this->mementos, 0, $this->currentIndex + 1);
        $this->mementos[] = $memento;
        ++$this->currentIndex;
    }

    public function undo(): ?{Name}Memento
    {
        if ($this->currentIndex > 0) {
            --$this->currentIndex;
            return $this->mementos[$this->currentIndex];
        }
        return null;
    }

    public function redo(): ?{Name}Memento
    {
        if ($this->currentIndex < count($this->mementos) - 1) {
            ++$this->currentIndex;
            return $this->mementos[$this->currentIndex];
        }
        return null;
    }
}
```

---

## Usage Example

```php
// Create originator
$document = new Document(content: 'Initial text');

// Create caretaker
$history = new DocumentHistory();

// Save initial state
$history->save($document->createMemento());

// Make changes
$document->setContent('Modified text');
$history->save($document->createMemento());

$document->setContent('Final text');
$history->save($document->createMemento());

// Undo changes
$memento = $history->undo();
if ($memento) {
    $document->restore($memento); // Back to 'Modified text'
}

// Redo changes
$memento = $history->redo();
if ($memento) {
    $document->restore($memento); // Forward to 'Final text'
}
```

---

## Common Memento Examples

| Domain | Use Cases |
|--------|-----------|
| Document Editor | Text content, formatting, cursor position |
| Form Management | Draft state, field values, validation state |
| Game Development | Player state, level progress, inventory |
| Order Processing | Order draft, item changes, pricing snapshots |
| Configuration | Settings snapshots, rollback points |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Mutable memento | State corruption | Use readonly classes |
| Public state access | Breaks encapsulation | Expose only via getters |
| Large state copies | Memory overhead | Store only changed fields |
| Missing timestamp | No audit trail | Include createdAt |
| Unbounded history | Memory leak | Implement history limit |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Memento, Originator, Caretaker templates
- `references/examples.md` — Document, Order, Form state management with tests
