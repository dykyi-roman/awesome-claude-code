---
name: create-decorator
description: Generates Decorator pattern for PHP 8.4. Creates wrapper classes for dynamic behavior addition without inheritance. Includes unit tests.
---

# Decorator Pattern Generator

Creates Decorator pattern infrastructure for dynamically adding behavior to objects.

## When to Use

| Scenario | Example |
|----------|---------|
| Cross-cutting concerns | Logging, caching, metrics |
| Transparent wrapping | Add behavior without changing interface |
| Stackable features | Multiple decorators combined |
| Runtime behavior | Dynamic feature addition |

## Component Characteristics

### Component Interface
- Defines core operations
- Shared by concrete and decorators
- Enables transparent wrapping

### Abstract Decorator
- Wraps component
- Delegates to wrapped object
- Base for concrete decorators

### Concrete Decorators
- Add specific behavior
- Before/after wrapped call
- Can be stacked

---

## Generation Process

### Step 1: Generate Component Interface

Place alongside the existing service the decorators wrap.

1. `{Name}Interface.php` — Core operations contract

### Step 2: Generate Abstract Decorator

Place in a sibling `Decorator/` folder.

1. `Abstract{Name}Decorator.php` — Base decorator with delegation

### Step 3: Generate Concrete Decorators

Co-located with the abstract decorator in the same `Decorator/` folder (these typically pull in logging, caching, metrics, or transactional dependencies, so the folder lives near other infrastructure adapters).

1. `Logging{Name}Decorator.php` — Logging behavior
2. `Caching{Name}Decorator.php` — Caching behavior
3. `Metrics{Name}Decorator.php` — Performance metrics
4. `Transactional{Name}Decorator.php` — Transaction wrapping

### Step 4: Generate Factory (Optional)

Place in the parent folder (one level up from `Decorator/`), wiring decorators around the real service.

1. `{Name}Factory.php` — Stack decorators in correct order

### Step 5: Generate Tests

1. `{Feature}{Name}DecoratorTest.php` — Individual decorator tests

---

## File Placement

| Component | Path |
|-----------|------|
| Interface | `src/{architecture-path}/{Name}Interface.php` |
| Abstract Decorator | `src/{architecture-path}/Decorator/Abstract{Name}Decorator.php` |
| Concrete Decorators | `src/{architecture-path}/Decorator/{Feature}{Name}Decorator.php` |
| Factory | `src/{architecture-path}/{Name}Factory.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Decorator/` |

> `{architecture-path}` represents your project's architecture-specific folders. The interface and abstract decorator typically live alongside the service they wrap; concrete decorators with infrastructure dependencies (logging, caching, transaction) live with other infrastructure adapters. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `{Name}Interface` | `OrderServiceInterface` |
| Abstract Decorator | `Abstract{Name}Decorator` | `AbstractOrderServiceDecorator` |
| Concrete Decorator | `{Feature}{Name}Decorator` | `LoggingOrderServiceDecorator` |
| Factory | `{Name}Factory` | `OrderServiceFactory` |
| Test | `{ClassName}Test` | `LoggingOrderServiceDecoratorTest` |

---

## Quick Template Reference

### Abstract Decorator

```php
abstract class Abstract{Name}Decorator implements {Name}Interface
{
    public function __construct(
        protected readonly {Name}Interface $wrapped
    ) {}

    public function {operation}({params}): {returnType}
    {
        return $this->wrapped->{operation}({args});
    }
}
```

### Concrete Decorator

```php
final readonly class {Feature}{Name}Decorator extends Abstract{Name}Decorator
{
    public function __construct(
        {Name}Interface $wrapped,
        private {Dependency} $dependency
    ) {
        parent::__construct($wrapped);
    }

    public function {operation}({params}): {returnType}
    {
        {beforeBehavior}
        $result = parent::{operation}({args});
        {afterBehavior}
        return $result;
    }
}
```

---

## Usage Example

```php
// Stack decorators in order
$service = new TransactionalOrderServiceDecorator(
    new CachingOrderServiceDecorator(
        new MetricsOrderServiceDecorator(
            new LoggingOrderServiceDecorator(
                $baseService,
                $logger
            ),
            $metrics
        ),
        $cache
    ),
    $transaction
);

// Use normally - all decorators execute
$order = $service->create($command);
```

---

## Common Decorators

| Decorator | Purpose |
|-----------|---------|
| Logging | Log method calls and results |
| Caching | Cache expensive operations |
| Metrics | Collect performance metrics |
| Transaction | Wrap in database transaction |
| Retry | Retry failed operations |
| CircuitBreaker | Protect from cascading failures |
| Validation | Validate inputs before execution |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Missing Interface | Can't swap decorators | Use shared interface |
| Leaky Abstraction | Decorator-specific methods | Keep interface clean |
| Order Dependency | Wrong stacking order | Document decorator order |
| Heavy Decorators | Too much logic | Keep decorators focused |
| No Abstract | Code duplication | Create abstract decorator |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Abstract Decorator, Concrete Decorator, Interface templates
- `references/examples.md` — Logging, Caching, Metrics, Transaction decorators and tests
