---
name: acc-create-flyweight
description: Generates Flyweight pattern for PHP 8.4. Optimizes memory via shared intrinsic state. Includes unit tests.
---

# Flyweight Pattern Generator

Creates Flyweight pattern infrastructure for memory optimization through object sharing.

## When to Use

| Scenario | Example |
|----------|---------|
| Large number of similar objects | Icons, glyphs, particles |
| Memory constraints | Mobile apps, embedded systems |
| Immutable shared state | Currency codes, tax rates |
| Performance optimization | Reduce object creation overhead |

## Component Characteristics

### Flyweight Interface
- Defines operations
- Accepts extrinsic state as parameters

### ConcreteFlyweight
- Stores intrinsic state (shared)
- Immutable
- Reusable across contexts

### FlyweightFactory
- Creates and manages flyweights
- Returns existing or new flyweight
- Ensures sharing

---

## Generation Process

### Step 1: Generate Flyweight Interface

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Interface.php` — Operations contract

### Step 2: Generate ConcreteFlyweight

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Flyweight.php` — Shared object

### Step 3: Generate FlyweightFactory

**Path:** `src/Domain/{BoundedContext}/Factory/` or `src/Infrastructure/`

1. `{Name}FlyweightFactory.php` — Manages flyweights

### Step 4: Generate Tests

1. `{ClassName}Test.php` — Flyweight behavior and sharing verification

---

## File Placement

| Component | Path |
|-----------|------|
| Flyweight Interface | `src/Domain/{BoundedContext}/` |
| ConcreteFlyweight | `src/Domain/{BoundedContext}/` |
| FlyweightFactory | `src/Domain/{BoundedContext}/Factory/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Flyweight Interface | `{Name}Interface` | `CurrencyInterface` |
| ConcreteFlyweight | `{Name}Flyweight` | `CurrencyFlyweight` |
| FlyweightFactory | `{Name}FlyweightFactory` | `CurrencyFlyweightFactory` |
| Test | `{ClassName}Test` | `CurrencyFlyweightTest` |

---

## Quick Template Reference

### Flyweight

```php
final readonly class {Name}Flyweight implements {Name}Interface
{
    public function __construct(
        private string $intrinsicState
    ) {}

    public function {operation}(string $extrinsicState): {returnType}
    {
        return {combine intrinsic and extrinsic state};
    }
}
```

### FlyweightFactory

```php
final class {Name}FlyweightFactory
{
    private array $flyweights = [];

    public function getFlyweight(string $key): {Name}Interface
    {
        if (!isset($this->flyweights[$key])) {
            $this->flyweights[$key] = new {Name}Flyweight($key);
        }

        return $this->flyweights[$key];
    }

    public function getCount(): int
    {
        return count($this->flyweights);
    }
}
```

---

## Usage Example

```php
$factory = new CurrencyFlyweightFactory();

// Same object returned
$usd1 = $factory->getFlyweight('USD');
$usd2 = $factory->getFlyweight('USD');

assert($usd1 === $usd2); // true

// Format with extrinsic state
$usd1->format(100.50); // "$100.50"
```

---

## Common Flyweights

| Flyweight | Purpose |
|-----------|---------|
| CurrencyFlyweight | Currency codes and symbols |
| IconFlyweight | UI icons |
| TaxRuleFlyweight | Tax rates by region |
| CharacterFlyweight | Text rendering glyphs |
| ColorFlyweight | Color palettes |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Mutable Flyweight | State changes affect all users | Make flyweights immutable |
| No Factory | Manual object management | Use flyweight factory |
| Large Intrinsic State | Memory not optimized | Keep intrinsic state minimal |
| Extrinsic in Flyweight | Not reusable | Pass extrinsic via parameters |
| Premature Optimization | Complexity without benefit | Profile first |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Flyweight, factory templates
- `references/examples.md` — Currency, icon, tax rule flyweights with unit tests
