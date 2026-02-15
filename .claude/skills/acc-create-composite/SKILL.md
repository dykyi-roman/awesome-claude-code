---
name: acc-create-composite
description: Generates Composite pattern for PHP 8.4. Creates tree structures with uniform treatment of individual and composite objects. Includes unit tests.
---

# Composite Pattern Generator

Creates Composite pattern infrastructure for treating individual objects and compositions uniformly.

## When to Use

| Scenario | Example |
|----------|---------|
| Tree structures | Menus, file systems, organization charts |
| Part-whole hierarchies | UI components, product categories |
| Recursive operations | Calculate totals, render trees |
| Uniform treatment | Same interface for leaf and composite |

## Component Characteristics

### Component Interface
- Defines operations for all objects
- Shared by leaf and composite
- Enables uniform treatment

### Leaf
- Represents individual object
- No children
- Implements component operations

### Composite
- Contains children (leaf or composite)
- Delegates operations to children
- Implements component operations

---

## Generation Process

### Step 1: Generate Component Interface

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Interface.php` — Operations contract

### Step 2: Generate Leaf

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Leaf.php` — Individual object

### Step 3: Generate Composite

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Composite.php` — Container for children

### Step 4: Generate Tests

1. `{ClassName}Test.php` — Component behavior verification

---

## File Placement

| Component | Path |
|-----------|------|
| Component Interface | `src/Domain/{BoundedContext}/` |
| Leaf | `src/Domain/{BoundedContext}/` |
| Composite | `src/Domain/{BoundedContext}/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Component Interface | `{Name}Interface` | `MenuItemInterface` |
| Leaf | `{Name}` | `MenuItem` |
| Composite | `{Name}Composite` | `MenuComposite` |
| Test | `{ClassName}Test` | `MenuCompositeTest` |

---

## Quick Template Reference

### Component Interface

```php
interface {Name}Interface
{
    public function {operation}(): {returnType};
}
```

### Leaf

```php
final readonly class {Name} implements {Name}Interface
{
    public function {operation}(): {returnType}
    {
        return {leafBehavior};
    }
}
```

### Composite

```php
final class {Name}Composite implements {Name}Interface
{
    private array $children = [];

    public function add({Name}Interface $child): void
    {
        $this->children[] = $child;
    }

    public function {operation}(): {returnType}
    {
        $result = {initialValue};

        foreach ($this->children as $child) {
            $result {combineOperation} $child->{operation}();
        }

        return $result;
    }
}
```

---

## Usage Example

```php
$menu = new MenuComposite('Products');
$menu->add(new MenuItem('Laptops'));

$submenu = new MenuComposite('Accessories');
$submenu->add(new MenuItem('Mouse'));
$submenu->add(new MenuItem('Keyboard'));

$menu->add($submenu);

// Uniform treatment
$menu->render();
```

---

## Common Composites

| Composite | Purpose |
|-----------|---------|
| MenuComposite | Nested menu structures |
| PermissionComposite | Permission hierarchies |
| PriceRuleComposite | Combined pricing rules |
| FileSystemComposite | Files and directories |
| OrganizationComposite | Company structure |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Type Checking | instanceof checks everywhere | Use polymorphism |
| Leaf Operations in Composite | add/remove on leafs | Throw exception or use separate interfaces |
| Deep Hierarchies | Performance issues | Limit depth or use flyweight |
| Missing Parent Reference | Can't navigate up | Store parent in composite |
| Circular References | Infinite loops | Validate before adding |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Component interface, leaf, composite templates
- `references/examples.md` — Menu, permission, price rule composites with unit tests
