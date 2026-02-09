---
name: acc-create-test-builder
description: Generates Test Data Builder and Object Mother patterns for PHP 8.5. Creates fluent builders with sensible defaults and factory methods for test data creation.
---

# Test Data Builder Generator

Generates Test Data Builder and Object Mother patterns for test data creation.

## Patterns

### Test Data Builder

Fluent interface for constructing test objects with customizable properties.

**When to use:**
- Complex objects with many properties
- Need to customize specific properties per test
- Want to express test intent clearly

### Object Mother

Factory methods returning pre-configured objects for common scenarios.

**When to use:**
- Standard test fixtures (default user, pending order)
- Shared across many tests
- Named scenarios (premium customer, expired subscription)

## References

- `references/templates.md` — Builder and Object Mother class templates
- `references/examples.md` — Complete Order example with Value Object builders and usage

## Generation Instructions

1. **Analyze the target class:**
   - Constructor parameters
   - Required vs optional properties
   - Value objects used
   - State transitions (for entities)

2. **Determine sensible defaults:**
   - Generate IDs automatically
   - Use common/valid values
   - Consider relationships

3. **Create Builder with:**
   - Private constructor with defaults
   - Static factory method (`aOrder`, `anEmail`)
   - `with*` methods for each property
   - Immutable (clone in each method)
   - `build()` method

4. **Create Mother with:**
   - `default()` method
   - Named scenarios (`pending`, `confirmed`, `premium`)
   - Parameterized methods (`forCustomer`, `withTotal`)

5. **File placement:**
   - Builders: `tests/Builder/{ClassName}Builder.php`
   - Mothers: `tests/Mother/{ClassName}Mother.php`

## Best Practices

1. **Sensible defaults** — Tests should work without customization
2. **Fluent interface** — Chain method calls
3. **Immutable builders** — Clone in each `with*` method
4. **Expressive names** — `pending()` not `withStatus(pending)`
5. **Composition** — Builders can use other Mothers/Builders
6. **Single Responsibility** — One builder per aggregate/entity
