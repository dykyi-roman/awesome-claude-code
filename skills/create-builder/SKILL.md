---
name: create-builder
description: Generates Builder pattern for PHP 8.4. Creates step-by-step object construction with fluent interface and validation. Includes unit tests.
---

# Builder Pattern Generator

Creates Builder pattern infrastructure for step-by-step construction of complex objects.

## When to Use

| Scenario | Example |
|----------|---------|
| Many constructor parameters | Order with 10+ fields |
| Optional parameters | Email with optional CC, BCC |
| Complex validation | Build-time validation |
| Step-by-step construction | Query building |
| Multiple representations | Different order types |

## Component Characteristics

### Builder Interface
- Defines building steps
- Returns self for fluent interface
- Has build() method for final product

### Concrete Builder
- Implements building steps
- Maintains product state
- Validates before building

### Director (Optional)
- Defines construction order
- Reusable build sequences
- Hides complexity from client

---

## Generation Process

### Step 1: Analyze Requirements

Determine:
- Target product class
- Required vs optional properties
- Validation rules
- Whether Director is needed

### Step 2: Generate Builder Components

Place alongside the product class being built.

1. `{Name}BuilderInterface.php` — Builder contract
2. `{Name}Builder.php` — Concrete builder implementation
3. `BuilderValidationException.php` — Validation exception
4. `{Name}Director.php` — Optional director for common builds

### Step 3: Generate Tests

Mirror the production-code path under `tests/Unit/`.

1. `{Name}BuilderTest.php` — Builder functionality tests

---

## File Placement

| Component | Path |
|-----------|------|
| Builder Interface | `src/{architecture-path}/Builder/{Name}BuilderInterface.php` |
| Concrete Builder | `src/{architecture-path}/Builder/{Name}Builder.php` |
| Director | `src/{architecture-path}/Builder/{Name}Director.php` |
| Exception | `src/{architecture-path}/Builder/BuilderValidationException.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Builder/` |

> `{architecture-path}` represents your project's architecture-specific folders. Builders typically live alongside the product class they build. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `{Name}BuilderInterface` | `OrderBuilderInterface` |
| Concrete Builder | `{Name}Builder` | `OrderBuilder` |
| Director | `{Name}Director` | `OrderDirector` |
| Exception | `BuilderValidationException` | `BuilderValidationException` |
| Test | `{ClassName}Test` | `OrderBuilderTest` |

---

## Quick Template Reference

### Builder Interface

```php
interface {Name}BuilderInterface
{
    public function with{Property1}({Type1} $value): self;
    public function with{Property2}({Type2} $value): self;
    public function build(): {Product};
    public function reset(): self;
}
```

### Concrete Builder

```php
final class {Name}Builder implements {Name}BuilderInterface
{
    private ?{Type1} ${property1} = null;
    private ?{Type2} ${property2} = null;
    private array $errors = [];

    public function with{Property1}({Type1} $value): self
    {
        $this->{property1} = $value;
        return $this;
    }

    public function build(): {Product}
    {
        $this->validate();
        if ($this->errors !== []) {
            throw new BuilderValidationException($this->errors);
        }
        return new {Product}(...);
    }

    public function reset(): self
    {
        $this->{property1} = null;
        $this->errors = [];
        return $this;
    }
}
```

### Director

```php
final readonly class {Name}Director
{
    public function __construct(private {Name}BuilderInterface $builder) {}

    public function buildMinimal{Name}(/* required params */): {Product}
    {
        return $this->builder
            ->reset()
            ->with{Required1}($value1)
            ->build();
    }

    public function buildFull{Name}(/* all params */): {Product}
    {
        return $this->builder
            ->reset()
            ->with{Property1}($value1)
            ->with{Property2}($value2)
            ->build();
    }
}
```

---

## Usage Example

```php
// Direct builder usage
$order = (new OrderBuilder())
    ->forCustomer($customerId)
    ->withShippingAddress($address)
    ->addItem($item1)
    ->addItem($item2)
    ->withDiscountCode('SAVE10')
    ->build();

// Using Director
$director = new OrderDirector(new OrderBuilder());
$minimalOrder = $director->buildMinimalOrder($customerId, $address, $item);
$giftOrder = $director->buildGiftOrder($customerId, $shipping, $billing, $items, 'Happy Birthday!');
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| No Validation | Invalid objects built | Validate in build() |
| Mutable Product | Product can change after build | Return immutable objects |
| Missing Reset | Builder state persists | Add reset() method |
| Too Many Steps | Hard to use | Use Director or defaults |
| No Fluent Interface | Verbose client code | Return self from setters |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Builder, QueryBuilder templates
- `references/examples.md` — OrderBuilder, EmailBuilder examples and tests
