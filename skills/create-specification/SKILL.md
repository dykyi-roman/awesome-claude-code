---
name: create-specification
description: Generates DDD Specification for PHP 8.4. Creates reusable business rule objects for validation, filtering, and querying with composite pattern support. Includes unit tests.
---

# Specification Generator

Generate DDD-compliant Specifications for encapsulating business rules and filtering logic.

## Specification Characteristics

- **Single Responsibility**: One business rule per specification
- **Composable**: AND, OR, NOT combinations
- **Reusable**: Same spec for validation and querying
- **Domain Language**: Named using ubiquitous language
- **Testable**: Easy to unit test in isolation
- **Immutable**: No state changes after creation

## When to Use Specification

| Scenario | Example |
|----------|---------|
| Business rule validation | `IsActiveCustomer`, `CanPlaceOrder` |
| Collection filtering | `OverdueInvoice`, `PremiumProduct` |
| Repository queries | `OrdersByCustomer`, `ActiveUsers` |
| Policy enforcement | `EligibleForDiscount`, `CanBeShipped` |
| Complex conditions | Composite AND/OR specifications |

---

## Generation Process

### Step 1: Generate Base Infrastructure

Place alongside other shared domain primitives.

1. `SpecificationInterface.php` — Generic interface with `isSatisfiedBy()`
2. `AbstractSpecification.php` — Base with AND/OR/NOT methods
3. `AndSpecification.php` — Composite AND
4. `OrSpecification.php` — Composite OR
5. `NotSpecification.php` — Negation wrapper

### Step 2: Generate Concrete Specification

Place inside the bounded context whose business rule the specification expresses.

1. `{Name}Specification.php` — Implements business rule

### Step 3: Generate Tests

Mirror the production-code path under `tests/Unit/`.

---

## File Placement

| Component | Path |
|-----------|------|
| Base Interface | `src/{architecture-path}/Specification/SpecificationInterface.php` |
| Abstract Spec | `src/{architecture-path}/Specification/AbstractSpecification.php` |
| Composites | `src/{architecture-path}/Specification/` |
| Concrete Specs | `src/{architecture-path}/Specification/{Name}Specification.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Specification/` |

> `{architecture-path}` represents your project's architecture-specific folders. Base specification types are shared across contexts; concrete specifications live inside the bounded context whose business rule they express. Adjust to your project's layout.

---

## Naming Conventions

| Pattern | Example |
|---------|---------|
| `Is{Condition}Specification` | `IsActiveCustomerSpecification` |
| `Has{Property}Specification` | `HasPurchaseHistorySpecification` |
| `Can{Action}Specification` | `CanBeCancelledSpecification` |
| Factory Method | `IsOverdueInvoiceSpecification::now()` |

---

## Quick Template Reference

### Specification Interface

```php
/**
 * @template T
 */
interface SpecificationInterface
{
    public function isSatisfiedBy(mixed $candidate): bool;
    public function and(self $other): self;
    public function or(self $other): self;
    public function not(): self;
}
```

### Concrete Specification

```php
/**
 * @extends AbstractSpecification<{Entity}>
 */
final readonly class {Name}Specification extends AbstractSpecification
{
    public function __construct({parameters}) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof {Entity}) {
            return false;
        }
        return {businessRule};
    }
}
```

### Composite Usage

```php
$eligible = $isActive
    ->and($hasPurchases)
    ->and($isNotBlacklisted->not());

$customers = array_filter(
    $all,
    fn($c) => $eligible->isSatisfiedBy($c)
);
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| God Specification | Too many conditions | Split into composable specs |
| Side Effects | Modifies candidate | Keep pure, read-only |
| Infrastructure | DB calls in spec | Keep in domain, use for in-memory |
| Weak Typing | `isSatisfiedBy(mixed)` | Add type check first |
| No Composition | Copy-paste conditions | Use AND/OR composition |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Interface, Abstract, Composite, Concrete templates
- `references/examples.md` — Customer, Product, Invoice, Order specifications and tests
