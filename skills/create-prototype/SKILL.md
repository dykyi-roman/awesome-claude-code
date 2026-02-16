---
name: acc-create-prototype
description: Generates Prototype pattern implementations for PHP 8.4. Creates deep/shallow copy, clone customization, prototype registries, and immutable object duplication.
---

# Prototype Pattern Generator

Generate Prototype pattern implementations for PHP 8.4 with proper deep/shallow copy semantics.

## Pattern Overview

Prototype creates new objects by cloning existing instances, avoiding costly construction and enabling runtime object configuration.

## Generation Templates

### 1. Basic Prototype with Clone

```php
<?php

declare(strict_types=1);

namespace {Namespace}\Domain\{Context};

final class {Name} implements \Cloneable
{
    public function __construct(
        private readonly {IdType} $id,
        private string $title,
        private array $metadata,
        private \DateTimeImmutable $createdAt,
    ) {}

    public function __clone(): void
    {
        // Deep copy mutable objects
        $this->createdAt = clone $this->createdAt;
        // Arrays are copied by value (shallow), but nested objects need cloning
        $this->metadata = array_map(
            fn (mixed $item) => is_object($item) ? clone $item : $item,
            $this->metadata,
        );
    }

    public function withTitle(string $title): self
    {
        $clone = clone $this;
        $clone->title = $title;
        return $clone;
    }

    public function withMetadata(array $metadata): self
    {
        $clone = clone $this;
        $clone->metadata = $metadata;
        return $clone;
    }
}
```

### 2. Prototype Registry

```php
<?php

declare(strict_types=1);

namespace {Namespace}\Domain\{Context};

final class {Name}PrototypeRegistry
{
    /** @var array<string, {Name}> */
    private array $prototypes = [];

    public function register(string $key, {Name} $prototype): void
    {
        $this->prototypes[$key] = $prototype;
    }

    public function create(string $key): {Name}
    {
        if (!isset($this->prototypes[$key])) {
            throw new \InvalidArgumentException(
                sprintf('Prototype "%s" not registered. Available: %s', $key, implode(', ', array_keys($this->prototypes))),
            );
        }

        return clone $this->prototypes[$key];
    }

    public function has(string $key): bool
    {
        return isset($this->prototypes[$key]);
    }

    /** @return list<string> */
    public function keys(): array
    {
        return array_keys($this->prototypes);
    }
}
```

### 3. Immutable Value Object Prototype

```php
<?php

declare(strict_types=1);

namespace {Namespace}\Domain\{Context}\ValueObject;

final readonly class {Name}
{
    public function __construct(
        private string $currency,
        private int $amount,
        private string $locale,
    ) {}

    // Immutable "clone" via named constructors
    public function withAmount(int $amount): self
    {
        return new self(
            currency: $this->currency,
            amount: $amount,
            locale: $this->locale,
        );
    }

    public function withCurrency(string $currency): self
    {
        return new self(
            currency: $currency,
            amount: $this->amount,
            locale: $this->locale,
        );
    }

    // Factory from prototype
    public static function fromPrototype(self $prototype, int $amount): self
    {
        return new self(
            currency: $prototype->currency,
            amount: $amount,
            locale: $prototype->locale,
        );
    }
}
```

### 4. Deep Clone with Object Graph

```php
<?php

declare(strict_types=1);

namespace {Namespace}\Domain\{Context};

final class {Name}
{
    /** @var list<{ChildType}> */
    private array $children;

    public function __construct(
        private readonly {IdType} $id,
        private {ConfigType} $config,
        array $children = [],
    ) {
        $this->children = $children;
    }

    public function __clone(): void
    {
        // Deep clone config object
        $this->config = clone $this->config;

        // Deep clone collection of children
        $this->children = array_map(
            fn ({ChildType} $child): {ChildType} => clone $child,
            $this->children,
        );
    }

    public function duplicate({IdType} $newId): self
    {
        $clone = clone $this;
        // Use reflection for readonly property if needed
        $ref = new \ReflectionProperty($clone, 'id');
        $ref->setValue($clone, $newId);
        return $clone;
    }
}
```

## Detection Patterns (Audit)

```bash
# Missing __clone on classes with mutable properties
Grep: "class.*\{" --glob "**/Domain/**/*.php"
# Then check for mutable object properties without __clone

# Shallow copy issues (clone without __clone)
Grep: "clone \$this" --glob "**/*.php"
Grep: "function __clone" --glob "**/*.php"

# Manual copy-paste construction (prototype candidate)
Grep: "new self\(.*\$this->" --glob "**/*.php"

# Prototype registry candidates
Grep: "array.*prototype|registry.*clone" --glob "**/*.php"
```

## Anti-Patterns to Avoid

```php
// BAD: Serialization for deep copy (slow, breaks resources)
$clone = unserialize(serialize($original));

// BAD: No __clone with mutable objects
$clone = clone $original;
$clone->getAddress()->setCity('New'); // Modifies original!

// BAD: Clone readonly object without proper handling
final readonly class Order
{
    // Cannot modify properties after clone!
    // Use "with" methods returning new instances instead
}
```

## Output Format

```markdown
### Prototype Pattern: {Name}

**Files Generated:**
- `src/Domain/{Context}/{Name}.php` — Prototype with __clone
- `src/Domain/{Context}/{Name}PrototypeRegistry.php` — Registry (if needed)

**Clone Strategy:**
- Deep copy: [list mutable properties]
- Shallow copy: [list immutable/scalar properties]
- Readonly: [list readonly properties — use with* methods]
```
