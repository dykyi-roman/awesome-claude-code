# Psalm Plugins and Annotations for DDD

Psalm plugins, custom annotations, stub files, and configuration patterns for PHP 8.4 projects following DDD principles.

## Error Level Strategy

| Level | Strictness | When to Use |
|-------|-----------|-------------|
| 1 | Maximum | New DDD projects, greenfield development |
| 2 | Very strict | **Recommended for production DDD projects** |
| 3 | Strict | Existing projects with good type coverage |
| 4 | Relaxed | Legacy codebases being migrated |
| 5-6 | Permissive | Initial adoption on large legacy projects |
| 7-8 | Minimal | Barely useful, only basic checks |

### Level Migration Script

```bash
# Test each level to find current passing level
for level in $(seq 1 8); do
    echo "Testing level $level..."
    vendor/bin/psalm --error-level=$level --no-progress 2>/dev/null && echo "PASS" || echo "FAIL"
done
```

## Detection Patterns

```bash
# Find Psalm configuration
ls -la psalm.xml psalm.xml.dist 2>/dev/null

# Check current error level
grep -rn "errorLevel" psalm.xml psalm.xml.dist 2>/dev/null

# Find baseline file
ls -la psalm-baseline.xml 2>/dev/null

# Check for Psalm plugins in use
grep -rn "pluginClass" psalm.xml psalm.xml.dist 2>/dev/null

# Detect Psalm annotations in code
grep -rn "@psalm-" --include="*.php" src/

# Check for custom Psalm plugins
grep -rn "implements.*PluginEntryPointInterface" --include="*.php" src/

# Find Psalm plugins in composer.json
grep -rn "psalm-plugin\|psalm/plugin" composer.json
```

## Configuration Patterns

### Full DDD Configuration (psalm.xml)

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="2"
    resolveFromConfigFile="true"
    findUnusedBaselineEntry="true"
    findUnusedCode="true"
    findUnusedVariablesAndParams="true"
    ensureArrayStringOffsetsExist="true"
    ensureArrayIntOffsetsExist="true"
    memoizeMethodCallResults="true"
    allowStringToStandInForClass="true"
    phpVersion="8.4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="https://getpsalm.org/schema/config"
    xsi:schemaLocation="https://getpsalm.org/schema/config vendor/vimeo/psalm/config.xsd"
>
    <projectFiles>
        <directory name="src"/>
        <ignoreFiles>
            <directory name="vendor"/>
            <directory name="src/Infrastructure/Legacy"/>
        </ignoreFiles>
    </projectFiles>

    <plugins>
        <pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
        <pluginClass class="Psalm\SymfonyPsalmPlugin\Plugin">
            <containerXml>var/cache/dev/App_KernelDevDebugContainer.xml</containerXml>
        </pluginClass>
        <pluginClass class="App\Psalm\Plugin\DomainLayerPurityPlugin"/>
    </plugins>

    <issueHandlers>
        <!-- Suppress for Doctrine entities (properties set by ORM) -->
        <PropertyNotSetInConstructor>
            <errorLevel type="suppress">
                <directory name="src/Infrastructure/Doctrine/Entity"/>
            </errorLevel>
        </PropertyNotSetInConstructor>

        <!-- Allow mixed in infrastructure adapters -->
        <MixedAssignment>
            <errorLevel type="suppress">
                <directory name="src/Infrastructure/External"/>
            </errorLevel>
        </MixedAssignment>

        <!-- Suppress unused code in event subscribers (called by framework) -->
        <PossiblyUnusedMethod>
            <errorLevel type="suppress">
                <directory name="src/Infrastructure/EventSubscriber"/>
            </errorLevel>
        </PossiblyUnusedMethod>
    </issueHandlers>

    <stubs>
        <file name="stubs/FrameworkStubs.phpstub"/>
    </stubs>
</psalm>
```

### Minimal Starter Configuration

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="4"
    resolveFromConfigFile="true"
    phpVersion="8.4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="https://getpsalm.org/schema/config"
    xsi:schemaLocation="https://getpsalm.org/schema/config vendor/vimeo/psalm/config.xsd"
>
    <projectFiles>
        <directory name="src"/>
        <ignoreFiles>
            <directory name="vendor"/>
        </ignoreFiles>
    </projectFiles>
</psalm>
```

## Framework Plugins

### psalm-plugin-symfony

```bash
composer require --dev psalm/plugin-symfony
vendor/bin/psalm-plugin enable psalm/plugin-symfony
```

Features: container autowiring types, form type inference, route parameter types, event subscriber analysis.

```xml
<pluginClass class="Psalm\SymfonyPsalmPlugin\Plugin">
    <containerXml>var/cache/dev/App_KernelDevDebugContainer.xml</containerXml>
</pluginClass>
```

### psalm-plugin-laravel

```bash
composer require --dev psalm/plugin-laravel
vendor/bin/psalm-plugin enable psalm/plugin-laravel
```

Features: facade resolution, model attribute types, collection generics, request validation types.

### psalm-plugin-phpunit

```bash
composer require --dev psalm/plugin-phpunit
vendor/bin/psalm-plugin enable psalm/plugin-phpunit
```

Features: assertion type narrowing, mock type inference, data provider types, `createMock()` return types.

```xml
<pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
```

## Custom Psalm Plugin for DDD

### DomainLayerPurityPlugin

```php
<?php

declare(strict_types=1);

namespace App\Psalm\Plugin;

use Psalm\Plugin\PluginEntryPointInterface;
use Psalm\Plugin\RegistrationInterface;
use SimpleXMLElement;

final class DomainLayerPurityPlugin implements PluginEntryPointInterface
{
    public function __invoke(RegistrationInterface $registration, ?SimpleXMLElement $config = null): void
    {
        $registration->registerHooksFromClass(DomainLayerPurityHook::class);
    }
}
```

### DomainLayerPurityHook

```php
<?php

declare(strict_types=1);

namespace App\Psalm\Plugin;

use Psalm\CodeLocation;
use Psalm\IssueBuffer;
use Psalm\Plugin\EventHandler\AfterClassLikeVisitInterface;
use Psalm\Plugin\EventHandler\Event\AfterClassLikeVisitEvent;
use Psalm\Issue\PluginIssue;

final class DomainLayerPurityHook implements AfterClassLikeVisitInterface
{
    private const FORBIDDEN_NAMESPACES = [
        'Symfony\\',
        'Doctrine\\',
        'Illuminate\\',
        'Infrastructure\\',
        'Application\\',
        'Presentation\\',
    ];

    public static function afterClassLikeVisit(AfterClassLikeVisitEvent $event): void
    {
        $statementsSource = $event->getStatementsSource();
        $classLikeStorage = $event->getStorage();
        $namespace = $classLikeStorage->name;

        if (!str_contains($namespace, '\\Domain\\')) {
            return;
        }

        foreach ($classLikeStorage->used_traits as $trait => $_) {
            self::checkForbiddenDependency($trait, $namespace, $statementsSource);
        }

        foreach ($classLikeStorage->parent_classes as $parent) {
            self::checkForbiddenDependency($parent, $namespace, $statementsSource);
        }

        foreach ($classLikeStorage->class_implements as $interface) {
            self::checkForbiddenDependency($interface, $namespace, $statementsSource);
        }
    }

    private static function checkForbiddenDependency(
        string $dependency,
        string $className,
        mixed $source,
    ): void {
        foreach (self::FORBIDDEN_NAMESPACES as $forbidden) {
            if (str_contains($dependency, $forbidden)) {
                IssueBuffer::maybeAdd(
                    new PluginIssue(
                        sprintf(
                            'Domain class "%s" must not depend on "%s". Domain layer must remain pure.',
                            $className,
                            $dependency,
                        ),
                        new CodeLocation($source, $source->getNode()),
                    ),
                );
            }
        }
    }
}
```

## Psalm Annotations

### Immutability Annotations

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

/**
 * @psalm-immutable
 */
final readonly class Money
{
    public function __construct(
        private int $amount,
        private string $currency,
    ) {}

    /** @psalm-pure */
    public function add(self $other): self
    {
        if ($this->currency !== $other->currency) {
            throw new CurrencyMismatchException($this->currency, $other->currency);
        }

        return new self($this->amount + $other->amount, $this->currency);
    }

    /** @psalm-pure */
    public function isZero(): bool
    {
        return $this->amount === 0;
    }

    /** @psalm-mutation-free */
    public function amount(): int
    {
        return $this->amount;
    }
}
```

### Template/Generic Annotations

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Repository;

/**
 * @template T of object
 */
interface RepositoryInterface
{
    /**
     * @psalm-param string $id
     * @psalm-return T|null
     */
    public function findById(string $id): ?object;

    /**
     * @psalm-param T $entity
     */
    public function save(object $entity): void;

    /**
     * @psalm-return list<T>
     */
    public function findAll(): array;
}
```

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Repository;

/**
 * @extends RepositoryInterface<Order>
 */
interface OrderRepositoryInterface extends RepositoryInterface
{
    /** @return list<Order> */
    public function findByCustomer(CustomerId $customerId): array;
}
```

### Assertion Annotations

```php
<?php

declare(strict_types=1);

namespace Domain\Shared;

final readonly class Assert
{
    /**
     * @psalm-assert non-empty-string $value
     * @psalm-pure
     */
    public static function nonEmptyString(string $value, string $field): void
    {
        if ($value === '') {
            throw new \InvalidArgumentException(
                sprintf('Field "%s" must not be empty.', $field),
            );
        }
    }

    /**
     * @psalm-assert positive-int $value
     * @psalm-pure
     */
    public static function positiveInt(int $value, string $field): void
    {
        if ($value <= 0) {
            throw new \InvalidArgumentException(
                sprintf('Field "%s" must be positive, got %d.', $field, $value),
            );
        }
    }

    /**
     * @psalm-assert !null $value
     * @psalm-pure
     */
    public static function notNull(mixed $value, string $field): void
    {
        if ($value === null) {
            throw new \InvalidArgumentException(
                sprintf('Field "%s" must not be null.', $field),
            );
        }
    }
}
```

### Type Narrowing Annotations

```php
<?php

declare(strict_types=1);

/**
 * @psalm-type OrderData = array{
 *     id: non-empty-string,
 *     customer_id: non-empty-string,
 *     lines: list<array{product_id: string, quantity: positive-int, price: int}>,
 *     status: 'draft'|'confirmed'|'shipped'|'cancelled',
 *     created_at: non-empty-string
 * }
 */

/**
 * @psalm-type PaginatedResult = array{
 *     items: list<OrderData>,
 *     total: non-negative-int,
 *     page: positive-int,
 *     per_page: positive-int
 * }
 */
```

## Stub Files for Framework Integration

### Creating Stubs

```php
<?php
// stubs/FrameworkStubs.phpstub

namespace Symfony\Component\Messenger;

/**
 * @template T of object
 */
interface MessageBusInterface
{
    /**
     * @psalm-param T $message
     * @psalm-return Envelope<T>
     */
    public function dispatch(object $message, array $stamps = []): Envelope;
}

namespace Doctrine\ORM;

/**
 * @template T of object
 * @template-extends ObjectRepository<T>
 */
interface EntityRepository
{
    /**
     * @psalm-return T|null
     */
    public function find(mixed $id): ?object;

    /**
     * @psalm-return list<T>
     */
    public function findAll(): array;
}
```

## Baseline Management

### Generating a Baseline

```bash
# Generate baseline from current errors
vendor/bin/psalm --set-baseline=psalm-baseline.xml

# Update baseline (removes fixed issues)
vendor/bin/psalm --update-baseline

# Show baseline statistics
grep -c "code=" psalm-baseline.xml
```

### Reducing Baseline Over Time

```bash
# Count errors by type in baseline
grep "code=" psalm-baseline.xml | sed 's/.*code="\([^"]*\)".*/\1/' | sort | uniq -c | sort -rn | head -20

# Find most common error files
grep "src=" psalm-baseline.xml | sed 's/.*src="\([^"]*\)".*/\1/' | sort | uniq -c | sort -rn | head -20
```

**Bad:** Suppressing issues globally without review.

```xml
<!-- Never suppress globally -->
<issueHandlers>
    <MixedAssignment errorLevel="suppress"/>  <!-- Hides real bugs -->
    <MixedReturnStatement errorLevel="suppress"/>
</issueHandlers>
```

**Good:** Targeted suppression with scope.

```xml
<!-- Suppress only where necessary -->
<issueHandlers>
    <MixedAssignment>
        <errorLevel type="suppress">
            <directory name="src/Infrastructure/External"/>  <!-- 3rd-party API adapters -->
        </errorLevel>
    </MixedAssignment>
</issueHandlers>
```

## Taint Analysis (Security)

```bash
# Run security-focused taint analysis
vendor/bin/psalm --taint-analysis

# Check for SQL injection, XSS, command injection
vendor/bin/psalm --taint-analysis --show-info=true
```

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

final readonly class CreateOrderAction
{
    public function __invoke(Request $request): JsonResponse
    {
        /** @psalm-taint-escape sql */
        $customerId = $this->validateUuid($request->get('customer_id'));

        /** @psalm-taint-escape html */
        $note = htmlspecialchars($request->get('note'), ENT_QUOTES, 'UTF-8');

        // Safe to use in queries and output
    }
}
```

## CI Integration

```yaml
# GitHub Actions
- name: Psalm
  run: vendor/bin/psalm --no-progress --output-format=github --shepherd

# GitLab CI
psalm:
  script:
    - vendor/bin/psalm --no-progress --output-format=checkstyle > psalm-report.xml
  artifacts:
    reports:
      junit: psalm-report.xml
```

## Summary Table

| Plugin / Annotation | Purpose | When to Use |
|---------------------|---------|-------------|
| `psalm-plugin-symfony` | Symfony container, forms, routes type support | Symfony projects |
| `psalm-plugin-laravel` | Facade resolution, model types, collection generics | Laravel projects |
| `psalm-plugin-phpunit` | Assertion narrowing, mock types, data providers | All projects with PHPUnit |
| `DomainLayerPurityPlugin` | Enforce DDD layer boundaries at analysis time | DDD/Clean Architecture projects |
| `@psalm-immutable` | Mark entire class as immutable (no property writes) | Value Objects, DTOs |
| `@psalm-readonly` | Mark property as read-only after construction | Entity properties |
| `@psalm-pure` | Mark method as side-effect free (deterministic) | Value Object methods, factories |
| `@psalm-mutation-free` | Method does not mutate `$this` state | Getter-like methods |
| `@psalm-assert` | Narrow types after assertion method call | Validation helpers, guard clauses |
| `@psalm-type` | Define complex type aliases for reuse | API contracts, DTO shapes |
| `@psalm-template` | Generic type parameters on classes/methods | Repositories, collections |
| `@psalm-taint-escape` | Mark value as sanitized for taint analysis | Input validation, escaping |
| Baseline (`psalm-baseline.xml`) | Track known issues, prevent new regressions | Legacy migration, incremental adoption |
| Taint analysis (`--taint-analysis`) | Detect SQL injection, XSS, command injection | Security audits, OWASP compliance |
