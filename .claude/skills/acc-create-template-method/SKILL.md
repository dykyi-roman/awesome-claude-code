---
name: acc-create-template-method
description: Generates Template Method pattern for PHP 8.4. Creates abstract algorithm skeleton with customizable steps, allowing subclasses to override specific parts without changing structure. Includes unit tests.
---

# Template Method Pattern Generator

Creates Template Method pattern infrastructure for algorithm skeletons with customizable steps.

## When to Use

| Scenario | Example |
|----------|---------|
| Common algorithm structure | Data import/export with format variations |
| Controlled extension points | Report generation with customizable sections |
| Code reuse across variants | Order processing with type-specific steps |
| Invariant parts protection | Template rendering with hooks |

## Component Characteristics

### Abstract Template Class
- Defines algorithm skeleton
- Implements invariant steps
- Declares abstract/hook methods
- Calls methods in sequence

### Concrete Implementations
- Override specific steps
- Provide algorithm variants
- Inherit common behavior
- Maintain overall structure

### Hook Methods
- Optional override points
- Default empty implementation
- Allow customization
- Don't break flow

---

## Generation Process

### Step 1: Generate Abstract Template

**Path:** `src/Domain/{BoundedContext}/Template/`

1. `Abstract{Name}Template.php` — Algorithm skeleton with template method

### Step 2: Generate Concrete Templates

**Path:** `src/Domain/{BoundedContext}/Template/` or `src/Application/{BoundedContext}/`

1. `{Variant1}{Name}Template.php` — First variant implementation
2. `{Variant2}{Name}Template.php` — Second variant implementation
3. `{Variant3}{Name}Template.php` — Third variant implementation

### Step 3: Generate Support Classes (Optional)

**Path:** `src/Domain/{BoundedContext}/ValueObject/`

1. `{Name}Result.php` — Result value object
2. `{Name}Config.php` — Configuration value object

### Step 4: Generate Tests

1. `{Variant}{Name}TemplateTest.php` — Individual template tests
2. `Abstract{Name}TemplateTest.php` — Template skeleton tests

---

## File Placement

| Component | Path |
|-----------|------|
| Abstract Template | `src/Domain/{BoundedContext}/Template/` |
| Concrete Templates (Domain logic) | `src/Domain/{BoundedContext}/Template/` |
| Concrete Templates (App logic) | `src/Application/{BoundedContext}/` |
| Unit Tests | `tests/Unit/Domain/{BoundedContext}/Template/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Abstract | `Abstract{Name}Template` | `AbstractDataImporterTemplate` |
| Concrete | `{Variant}{Name}Template` | `CsvDataImporterTemplate` |
| Template Method | `execute()` or `process()` | `execute()` |
| Hook Method | `before{Step}()`, `after{Step}()` | `beforeValidation()` |
| Test | `{ClassName}Test` | `CsvDataImporterTemplateTest` |

---

## Quick Template Reference

### Abstract Template

```php
abstract readonly class Abstract{Name}Template
{
    public function execute({InputType} $input): {OutputType}
    {
        $this->validate($input);
        $data = $this->extract($input);
        $transformed = $this->transform($data);
        $result = $this->load($transformed);
        $this->afterLoad($result);

        return $result;
    }

    abstract protected function extract({InputType} $input): array;
    abstract protected function transform(array $data): array;

    protected function validate({InputType} $input): void
    {
        // Default validation
    }

    protected function afterLoad({OutputType} $result): void
    {
        // Hook method - optional override
    }
}
```

### Concrete Template

```php
final readonly class {Variant}{Name}Template extends Abstract{Name}Template
{
    protected function extract({InputType} $input): array
    {
        // Variant-specific extraction
    }

    protected function transform(array $data): array
    {
        // Variant-specific transformation
    }
}
```

---

## Usage Example

```php
// Create templates for different formats
$csvImporter = new CsvDataImporterTemplate();
$jsonImporter = new JsonDataImporterTemplate();
$xmlImporter = new XmlDataImporterTemplate();

// Use same interface
$result = $csvImporter->execute($fileContent);
```

---

## Common Template Method Variants

| Domain | Variants |
|--------|----------|
| Data Import | CSV, JSON, XML, Excel |
| Report Generation | PDF, Excel, HTML, Email |
| Order Processing | Standard, Express, International |
| Document Rendering | Markdown, LaTeX, HTML |
| Payment Flow | Card, Bank Transfer, Digital Wallet |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Too many abstract methods | Hard to implement | Use hook methods with defaults |
| Public template steps | Breaks encapsulation | Make steps protected/private |
| Mutable state | Side effects | Use readonly classes, pass data |
| Deep inheritance | Complexity | Limit to 2-3 levels max |
| Breaking LSP | Inconsistent behavior | Maintain contract in overrides |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Abstract Template, Concrete Template, Hook Methods templates
- `references/examples.md` — DataImporter, ReportGenerator, OrderProcessor with tests
