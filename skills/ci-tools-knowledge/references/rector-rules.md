# Rector Rules for DDD & Clean Architecture

Rector configuration, PHP upgrade sets, dead code removal, type declaration rules, and custom DDD-specific rules for PHP 8.4 projects.

Targets Rector 2.x (`rector/rector: ^2.0`) — configs use the `RectorConfig::configure()` builder only.

## Detection Patterns

```bash
# Find Rector configuration
ls -la rector.php rector.php.dist 2>/dev/null

# Check Rector version
composer show rector/rector 2>/dev/null | grep "versions"

# Find custom Rector rules
grep -rn "extends AbstractRector\|implements RectorInterface" --include="*.php" src/ tools/

# Detect Rector sets in use
grep -rn "withPhpSets\|SetList::\|LevelSetList::\|PHPUnitSetList::" rector.php 2>/dev/null

# Check for Rector in CI
grep -rn "rector" --include="*.yml" --include="*.yaml" .github/ .gitlab-ci.yml 2>/dev/null

# Find dry-run results
ls -la rector-diff.txt 2>/dev/null
```

## Configuration Patterns

### Full DDD Configuration (rector.php)

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\CodeQuality\Rector\Class_\InlineConstructorDefaultToPropertyRector;
use Rector\DeadCode\Rector\ClassMethod\RemoveUselessParamTagRector;
use Rector\DeadCode\Rector\ClassMethod\RemoveUselessReturnTagRector;
use Rector\Php84\Rector\Param\ExplicitNullableParamTypeRector;
use Rector\Strict\Rector\Empty_\DisallowedEmptyRuleFixerRector;
use Rector\TypeDeclaration\Rector\StmtsAwareInterface\DeclareStrictTypesRector;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->withSkip([
        __DIR__ . '/src/Infrastructure/Legacy',
        __DIR__ . '/src/Kernel.php',
        __DIR__ . '/tests/Fixtures',

        // Skip specific rules for specific paths
        RemoveUselessParamTagRector::class => [
            __DIR__ . '/src/Domain/*/Repository/*Interface.php',
        ],
    ])
    ->withPhpSets(php84: true)
    // PHPUnit version sets picked from composer.json
    ->withComposerBased(phpunit: true)
    ->withPreparedSets(
        deadCode: true,
        codeQuality: true,
        typeDeclarations: true,
        privatization: true,
        naming: true,
        earlyReturn: true,
    )
    ->withRules([
        DeclareStrictTypesRector::class,
        InlineConstructorDefaultToPropertyRector::class,
        ExplicitNullableParamTypeRector::class,
        DisallowedEmptyRuleFixerRector::class,
    ])
    ->withImportNames(
        importNames: true,
        importDocBlockNames: true,
        importShortClasses: false,
        removeUnusedImports: true,
    );
```

### Minimal Starter Configuration

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src'])
    ->withPhpSets(php84: true)
    ->withPreparedSets(deadCode: true, typeDeclarations: true);
```

## PHP Upgrade Sets

### PHP 8.2 to 8.3

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src'])
    ->withPhpSets(php83: true);
```

Key transformations:

**Before (PHP 8.2):**
```php
<?php

declare(strict_types=1);

final readonly class OrderStatus
{
    public function label(): string
    {
        return match ($this->value) {
            'draft' => 'Draft',
            'confirmed' => 'Confirmed',
            default => 'Unknown',
        };
    }
}

// json_validate did not exist
function isValidJson(string $json): bool
{
    json_decode($json);
    return json_last_error() === JSON_ERROR_NONE;
}
```

**After (PHP 8.3):**
```php
<?php

declare(strict_types=1);

final readonly class OrderStatus
{
    public function label(): string
    {
        return match ($this->value) {
            'draft' => 'Draft',
            'confirmed' => 'Confirmed',
            default => 'Unknown',
        };
    }
}

// json_validate available natively
function isValidJson(string $json): bool
{
    return json_validate($json);
}
```

### PHP 8.3 to 8.4

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src'])
    ->withPhpSets(php84: true);
```

Key transformations:

**Before (PHP 8.3):**
```php
<?php

declare(strict_types=1);

final readonly class Order
{
    // Explicit nullable parameter type
    public function __construct(
        private string $id,
        private ?string $note = null,  // Implicit nullable
    ) {}
}

// array_find polyfill
function findFirstMatch(array $items, callable $callback): mixed
{
    foreach ($items as $item) {
        if ($callback($item)) {
            return $item;
        }
    }
    return null;
}
```

**After (PHP 8.4):**
```php
<?php

declare(strict_types=1);

final readonly class Order
{
    // Explicit nullable parameter type (PHP 8.4 deprecates implicit)
    public function __construct(
        private string $id,
        private ?string $note = null,  // Explicit nullable required
    ) {}
}

// Native array_find (PHP 8.4)
function findFirstMatch(array $items, callable $callback): mixed
{
    return array_find($items, $callback);
}
```

### Property Hooks (PHP 8.4)

```php
<?php

declare(strict_types=1);

// Before: manual getter/setter
final class Money
{
    public function __construct(
        private int $amount,
        private string $currency,
    ) {}

    public function amount(): int
    {
        return $this->amount;
    }

    public function currency(): string
    {
        return $this->currency;
    }
}

// After: property hooks (PHP 8.4)
final class Money
{
    public int $amount {
        get => $this->amount;
    }

    public string $currency {
        get => $this->currency;
    }

    public function __construct(int $amount, string $currency)
    {
        $this->amount = $amount;
        $this->currency = $currency;
    }
}
```

## Dead Code Removal Rules

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Set\ValueObject\SetList;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src'])
    ->withSets([SetList::DEAD_CODE]);
```

What gets removed:

| Rule | What It Removes |
|------|----------------|
| `RemoveUnusedPrivateMethodRector` | Private methods never called |
| `RemoveUnusedPrivatePropertyRector` | Private properties never read |
| `RemoveUnusedConstructorParamRector` | Constructor params never used |
| `RemoveDeadConditionAboveReturnRector` | Conditions after return/throw |
| `RemoveUselessParamTagRector` | PHPDoc `@param` matching signature |
| `RemoveUselessReturnTagRector` | PHPDoc `@return` matching signature |
| `RemoveUnusedVariableAssignRector` | Assigned but never read variables |
| `RemoveDeadTryCatchRector` | Try-catch with empty catch body |
| `RemoveParentCallWithoutParentRector` | `parent::` calls with no parent method |

**Bad:** Dead code left in production domain classes.

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

final class Order
{
    private string $legacyField;  // Never read or written

    /**
     * @param string $id The order ID  // Useless PHPDoc
     */
    public function __construct(
        private readonly string $id,
        private readonly string $unused,  // Never accessed
    ) {}

    private function oldCalculation(): float  // Never called
    {
        return 0.0;
    }
}
```

**Good:** Clean class after Rector dead code removal.

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

final class Order
{
    public function __construct(
        private readonly string $id,
    ) {}
}
```

## Type Declaration Rules

```php
<?php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Set\ValueObject\SetList;

return RectorConfig::configure()
    ->withPaths([__DIR__ . '/src'])
    ->withSets([SetList::TYPE_DECLARATION]);
```

Key rules:

| Rule | What It Adds |
|------|-------------|
| `DeclareStrictTypesRector` | Adds `declare(strict_types=1)` to all files |
| `AddReturnTypeDeclarationBasedOnParentClassMethodRector` | Infers return types from parent |
| `ReturnTypeFromReturnNewRector` | Adds return type when returning `new Foo()` |
| `AddClosureVoidReturnTypeWhereNoReturnRector` | Adds `: void` to closures |
| `ParamTypeByMethodCallTypeRector` | Infers param types from usage |
| `PropertyTypeDeclarationRector` | Adds typed properties from assignments |
| `ReturnNeverTypeRector` | Adds `never` return type when method always throws |

**Before:**
```php
<?php

namespace Domain\Order\Service;

class PricingService
{
    private $taxRate;

    public function __construct($taxRate)
    {
        $this->taxRate = $taxRate;
    }

    public function calculate($amount)
    {
        return $amount * (1 + $this->taxRate);
    }

    public function impossible()
    {
        throw new \RuntimeException('Not implemented');
    }
}
```

**After:**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\Service;

class PricingService
{
    private float $taxRate;

    public function __construct(float $taxRate)
    {
        $this->taxRate = $taxRate;
    }

    public function calculate(float $amount): float
    {
        return $amount * (1 + $this->taxRate);
    }

    public function impossible(): never
    {
        throw new \RuntimeException('Not implemented');
    }
}
```

## DDD-Specific Rector Rules

### ReadonlyClassRector

Converts classes to readonly where all properties are readonly.

**Before:**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

final class OrderId
{
    public function __construct(
        private readonly string $value,
    ) {}

    public function value(): string
    {
        return $this->value;
    }
}
```

**After:**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

final readonly class OrderId
{
    public function __construct(
        private string $value,
    ) {}

    public function value(): string
    {
        return $this->value;
    }
}
```

### ConstructorPromotionRector

Converts constructor assignment to promoted properties.

**Before:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    private OrderRepositoryInterface $orders;
    private EventDispatcherInterface $events;

    public function __construct(
        OrderRepositoryInterface $orders,
        EventDispatcherInterface $events,
    ) {
        $this->orders = $orders;
        $this->events = $events;
    }
}
```

**After:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}
}
```

## Custom Rector Rule for Domain Purity

```php
<?php

declare(strict_types=1);

namespace App\Rector\Rules;

use PhpParser\Node;
use PhpParser\Node\Stmt\Use_;
use PhpParser\NodeVisitor;
use Rector\Rector\AbstractRector;
use Symplify\RuleDocGenerator\ValueObject\RuleDefinition;
use Symplify\RuleDocGenerator\ValueObject\CodeSample\CodeSample;

final class ForbidInfrastructureInDomainRector extends AbstractRector
{
    private const FORBIDDEN_NAMESPACES = [
        'Doctrine\\',
        'Symfony\\',
        'Illuminate\\',
        'Infrastructure\\',
    ];

    public function getRuleDefinition(): RuleDefinition
    {
        return new RuleDefinition(
            'Remove infrastructure imports from Domain layer classes',
            [
                new CodeSample(
                    <<<'CODE_SAMPLE'
                    namespace Domain\Order\Entity;

                    use Doctrine\ORM\Mapping as ORM;

                    final class Order {}
                    CODE_SAMPLE,
                    <<<'CODE_SAMPLE'
                    namespace Domain\Order\Entity;

                    final class Order {}
                    CODE_SAMPLE,
                ),
            ],
        );
    }

    /** @return array<class-string<Node>> */
    public function getNodeTypes(): array
    {
        return [Use_::class];
    }

    public function refactor(Node $node): int|Node|null
    {
        if (!$node instanceof Use_) {
            return null;
        }

        $filePath = $this->file->getFilePath();

        if (!str_contains($filePath, '/Domain/')) {
            return null;
        }

        foreach ($node->uses as $use) {
            $name = $use->name->toString();

            foreach (self::FORBIDDEN_NAMESPACES as $forbidden) {
                if (str_starts_with($name, $forbidden)) {
                    return NodeVisitor::REMOVE_NODE;
                }
            }
        }

        return null;
    }
}
```

Register custom rule:

```php
<?php
// rector.php

use App\Rector\Rules\ForbidInfrastructureInDomainRector;
use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withRules([
        ForbidInfrastructureInDomainRector::class,
    ]);
```

## Running Rector in CI

### Dry-Run Mode (Recommended for CI)

```yaml
# GitHub Actions
- name: Rector (dry-run)
  run: vendor/bin/rector process --dry-run --no-progress-bar

# Fail CI if Rector finds changes
- name: Rector check
  run: |
    vendor/bin/rector process --dry-run --no-progress-bar 2>&1 | tee rector-output.txt
    if grep -q "files with changes" rector-output.txt; then
      echo "::error::Rector found code that needs refactoring. Run 'vendor/bin/rector process' locally."
      exit 1
    fi
```

### Auto-Apply Mode (Optional, with PR)

```yaml
# GitHub Actions - auto-apply and create PR
rector-auto-fix:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4

    - name: Setup PHP
      uses: shivammathur/setup-php@v2
      with:
        php-version: '8.4'

    - name: Install dependencies
      run: composer install --no-progress

    - name: Run Rector
      run: vendor/bin/rector process --no-progress-bar

    - name: Create PR if changes
      uses: peter-evans/create-pull-request@v6
      with:
        title: 'refactor: Apply Rector automated improvements'
        body: 'Automated code improvements by Rector.'
        branch: rector/auto-improvements
        commit-message: 'refactor: apply Rector automated improvements'
```

### GitLab CI

```yaml
rector:
  stage: quality
  image: php:8.4-cli
  before_script:
    - composer install --no-progress
  script:
    - vendor/bin/rector process --dry-run --no-progress-bar
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Combining with Other Tools

### Recommended CI Pipeline Order

```yaml
quality:
  stage: quality
  parallel:
    matrix:
      - TOOL: [rector, phpstan, psalm, cs-fixer, deptrac]
  script:
    - case $TOOL in
        rector)    vendor/bin/rector process --dry-run ;;
        phpstan)   vendor/bin/phpstan analyse --no-progress ;;
        psalm)     vendor/bin/psalm --no-progress ;;
        cs-fixer)  vendor/bin/php-cs-fixer fix --dry-run --diff ;;
        deptrac)   vendor/bin/deptrac analyse ;;
      esac
```

**Run order locally:**

1. `vendor/bin/rector process` -- auto-fix what can be fixed
2. `vendor/bin/php-cs-fixer fix` -- fix formatting after Rector changes
3. `vendor/bin/phpstan analyse` -- verify type safety
4. `vendor/bin/psalm` -- deep type + security analysis
5. `vendor/bin/deptrac analyse` -- verify layer boundaries

## Summary Table

| Rule Set / Rule | Purpose | Impact |
|-----------------|---------|--------|
| `withPhpSets(php84: true)` | Upgrade syntax to PHP 8.4 idioms | Property hooks, explicit nullable, array functions |
| `SetList::DEAD_CODE` | Remove unused code (methods, properties, params) | Cleaner codebase, smaller surface area |
| `SetList::TYPE_DECLARATION` | Add missing type declarations everywhere | Strict typing, better static analysis |
| `SetList::CODE_QUALITY` | Simplify conditionals, extract methods | Readability, reduced complexity |
| `SetList::PRIVATIZATION` | Make properties/methods private where possible | Encapsulation, reduced API surface |
| `SetList::EARLY_RETURN` | Convert nested ifs to early returns | Reduced nesting, clearer flow |
| `SetList::NAMING` | Improve variable and method naming | Self-documenting code |
| `PHPUnitSetList::PHPUNIT_100` | Migrate test syntax to PHPUnit 10+ | Modern test attributes, removed deprecations |
| `DeclareStrictTypesRector` | Add `declare(strict_types=1)` to all PHP files | Type safety at runtime |
| `ReadonlyClassRector` | Convert classes with all readonly props to `readonly class` | Immutability enforcement |
| `ConstructorPromotionRector` | Convert to constructor property promotion | Reduced boilerplate |
| `ExplicitNullableParamTypeRector` | Make implicit nullable params explicit | PHP 8.4 compatibility |
| `ReturnNeverTypeRector` | Add `never` return type to always-throwing methods | Better static analysis |
| Custom `ForbidInfrastructureInDomainRector` | Remove infrastructure imports from Domain layer | DDD layer purity |
