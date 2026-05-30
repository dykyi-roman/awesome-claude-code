---
name: create-visitor
description: Generates Visitor pattern for PHP 8.4. Creates operations on object structures without modifying element classes, with visitor interface, concrete visitors, and visitable elements. Includes unit tests.
---

# Visitor Pattern Generator

Creates Visitor pattern infrastructure for operations on object structures without modifying classes.

## When to Use

| Scenario | Example |
|----------|---------|
| Operations on object structure | Calculate price/tax on order items |
| Adding operations without modification | Export visitors (JSON, XML, CSV) |
| Different operations on same elements | Validation, transformation, rendering |
| Double dispatch needed | Type-specific behavior without instanceof |

## Component Characteristics

### Visitor Interface
- Declares visit methods for each element type
- One method per visitable element
- Returns operation result
- Enables double dispatch

### Concrete Visitors
- Implement specific operations
- Process each element type differently
- Encapsulate algorithm logic
- Can accumulate state during traversal

### Visitable Elements
- Accept visitor via accept() method
- Call visitor's visit method with self
- Enable operation without modification
- Maintain element structure

---

## Generation Process

### Step 1: Generate Visitor Interface

Place in a `Visitor/` folder inside the bounded context.

1. `{Name}VisitorInterface.php` — Visitor contract with visit methods

### Step 2: Generate Concrete Visitors

Co-located with the interface when the operations are pure domain logic; place near the coordination layer when operations pull in application-level dependencies (export formats, external APIs).

1. `{Operation1}Visitor.php` — First operation implementation
2. `{Operation2}Visitor.php` — Second operation implementation
3. `{Operation3}Visitor.php` — Third operation implementation

### Step 3: Generate Visitable Interface

Place at the bounded context root, alongside the element classes that will implement it.

1. `VisitableInterface.php` — Element contract with accept() method

### Step 4: Update Existing Elements

The element classes that implement `VisitableInterface` live alongside the interface.

1. Add `implements VisitableInterface` to element classes
2. Add `accept()` method to each element

### Step 5: Generate Tests

1. `{Operation}VisitorTest.php` — Individual visitor tests
2. `{Element}AcceptTest.php` — Element accept() tests

---

## File Placement

| Component | Path |
|-----------|------|
| Visitor Interface | `src/{architecture-path}/Visitor/{Name}VisitorInterface.php` |
| Concrete Visitors (pure domain) | `src/{architecture-path}/Visitor/{Operation}Visitor.php` |
| Concrete Visitors (app-level deps) | `src/{architecture-path}/Visitor/{Operation}Visitor.php` (or coordination layer) |
| Visitable Interface | `src/{architecture-path}/VisitableInterface.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Visitor/` |

> `{architecture-path}` represents your project's architecture-specific folders. Visitor interface + pure-domain visitors live in a `Visitor/` sub-folder; visitors with application-level dependencies typically live near the coordination layer. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Visitor Interface | `{Name}VisitorInterface` | `OrderItemVisitorInterface` |
| Concrete Visitor | `{Operation}Visitor` | `PriceCalculatorVisitor` |
| Visitable Interface | `VisitableInterface` | `VisitableInterface` |
| Visit Method | `visit{ElementType}()` | `visitProduct()` |
| Accept Method | `accept()` | `accept()` |
| Test | `{ClassName}Test` | `PriceCalculatorVisitorTest` |

---

## Quick Template Reference

### Visitor Interface

```php
interface {Name}VisitorInterface
{
    public function visit{Element1}({Element1} $element): {ReturnType};
    public function visit{Element2}({Element2} $element): {ReturnType};
    public function visit{Element3}({Element3} $element): {ReturnType};
}
```

### Concrete Visitor

```php
final class {Operation}Visitor implements {Name}VisitorInterface
{
    public function visit{Element1}({Element1} $element): {ReturnType}
    {
        // Element1-specific operation
    }

    public function visit{Element2}({Element2} $element): {ReturnType}
    {
        // Element2-specific operation
    }
}
```

### Visitable Interface

```php
interface VisitableInterface
{
    public function accept({Name}VisitorInterface $visitor): mixed;
}
```

### Visitable Element

```php
final readonly class {Element} implements VisitableInterface
{
    public function accept({Name}VisitorInterface $visitor): mixed
    {
        return $visitor->visit{Element}($this);
    }
}
```

---

## Usage Example

```php
// Create elements
$order = new Order(items: [
    new Product(price: 100, quantity: 2),
    new Service(price: 50, duration: 1),
    new Discount(amount: 20),
]);

// Apply different visitors
$priceVisitor = new PriceCalculatorVisitor();
$taxVisitor = new TaxCalculatorVisitor(rate: 0.2);
$exportVisitor = new JsonExportVisitor();

$totalPrice = $order->accept($priceVisitor);
$totalTax = $order->accept($taxVisitor);
$json = $order->accept($exportVisitor);
```

---

## Common Visitor Operations

| Domain | Visitors |
|--------|----------|
| Order Items | PriceCalculator, TaxCalculator, DiscountApplier |
| AST/Expression Tree | Evaluator, Formatter, Validator |
| Document Structure | Renderer, Counter, Searcher |
| File System | SizeCalculator, Permissions, Backup |
| Shopping Cart | TotalCalculator, ShippingCost, Export |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| instanceof in visitor | Defeats purpose | Use proper visit methods |
| Mutable visitor state | Race conditions | Use readonly classes |
| Too many element types | Visitor interface bloat | Split into multiple visitors |
| Breaking element encapsulation | Tight coupling | Expose getters, not internals |
| Returning void | Limited usefulness | Return operation results |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Visitor Interface, Concrete Visitor, Visitable Element templates
- `references/examples.md` — PriceCalculator, TaxCalculator, Export visitors with tests
