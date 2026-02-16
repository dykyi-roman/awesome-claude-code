---
name: acc-create-rector-config
description: Generates Rector configurations for PHP projects. Creates rector.php with PHP upgrade sets, code quality rules, dead code removal, and framework-specific migrations.
---

# Rector Configuration Generator

Generates optimized Rector configurations for automated PHP refactoring.

## Generated Files

```
rector.php                # Main configuration
```

## Configuration by Use Case

### PHP Version Upgrade

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->withSkip([
        __DIR__ . '/src/Infrastructure/Legacy',
        __DIR__ . '/src/Infrastructure/Migrations',
    ])
    // PHP 8.4 upgrade
    ->withPhpSets(php84: true)
    // Prepared sets
    ->withPreparedSets(
        deadCode: true,
        codeQuality: true,
        typeDeclarations: true,
    );
```

### Code Quality Focus

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Set\ValueObject\SetList;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src',
    ])
    ->withPhpSets(php84: true)
    ->withSets([
        SetList::CODE_QUALITY,
        SetList::CODING_STYLE,
        SetList::DEAD_CODE,
        SetList::EARLY_RETURN,
        SetList::PRIVATIZATION,
        SetList::TYPE_DECLARATION,
        SetList::INSTANCEOF,
    ])
    ->withPreparedSets(
        deadCode: true,
        codeQuality: true,
        typeDeclarations: true,
        privatization: true,
        earlyReturn: true,
        strictBooleans: true,
    );
```

### PHPUnit Migration

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\PHPUnit\Set\PHPUnitSetList;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/tests',
    ])
    ->withPhpSets(php84: true)
    ->withSets([
        PHPUnitSetList::PHPUNIT_100,
        PHPUnitSetList::PHPUNIT_CODE_QUALITY,
        PHPUnitSetList::ANNOTATIONS_TO_ATTRIBUTES,
    ])
    ->withPreparedSets(
        phpunitCodeQuality: true,
    );
```

### Symfony Migration

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Symfony\Set\SymfonySetList;
use Rector\Doctrine\Set\DoctrineSetList;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->withPhpSets(php84: true)
    ->withSets([
        // Symfony 7.x
        SymfonySetList::SYMFONY_70,
        SymfonySetList::SYMFONY_CODE_QUALITY,
        SymfonySetList::ANNOTATIONS_TO_ATTRIBUTES,

        // Doctrine
        DoctrineSetList::DOCTRINE_ORM_30,
        DoctrineSetList::ANNOTATIONS_TO_ATTRIBUTES,
    ])
    ->withSymfonyContainerXml(__DIR__ . '/var/cache/dev/App_KernelDevDebugContainer.xml');
```

### DDD Project Configuration

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Set\ValueObject\SetList;
use Rector\DeadCode\Rector\ClassMethod\RemoveUnusedPrivateMethodRector;
use Rector\TypeDeclaration\Rector\ClassMethod\ReturnTypeFromStrictNativeCallRector;
use Rector\TypeDeclaration\Rector\ClassMethod\ReturnTypeFromStrictScalarReturnExprRector;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src/Domain',
        __DIR__ . '/src/Application',
        __DIR__ . '/src/Infrastructure',
        __DIR__ . '/src/Api',
    ])
    ->withSkip([
        __DIR__ . '/src/Infrastructure/Migrations',
        __DIR__ . '/src/Infrastructure/Legacy',

        // Skip certain rules for specific paths
        RemoveUnusedPrivateMethodRector::class => [
            __DIR__ . '/src/Domain/*/Event/*',  // Event handlers may seem unused
        ],
    ])
    ->withPhpSets(php84: true)
    ->withPreparedSets(
        deadCode: true,
        codeQuality: true,
        typeDeclarations: true,
        privatization: true,
        earlyReturn: true,
    )
    // Strict for Domain layer
    ->withRules([
        ReturnTypeFromStrictNativeCallRector::class,
        ReturnTypeFromStrictScalarReturnExprRector::class,
    ])
    // Configure individual rules
    ->withConfiguredRule(
        \Rector\Naming\Rector\Class_\RenamePropertyToMatchTypeRector::class,
        [
            // Custom naming rules
        ]
    );
```

## Available Set Lists

### PHP Version Sets

```php
->withPhpSets(
    php53: true,  // PHP 5.3 features
    php54: true,  // PHP 5.4 features
    php55: true,  // ...
    php56: true,
    php70: true,
    php71: true,
    php72: true,
    php73: true,
    php74: true,
    php80: true,
    php81: true,
    php82: true,
    php83: true,
    php84: true,  // Latest
)
```

### Quality Sets

```php
use Rector\Set\ValueObject\SetList;

->withSets([
    SetList::CODE_QUALITY,          // General code quality
    SetList::CODING_STYLE,          // Coding style improvements
    SetList::DEAD_CODE,             // Remove dead code
    SetList::EARLY_RETURN,          // Early return patterns
    SetList::PRIVATIZATION,         // Privatize where possible
    SetList::TYPE_DECLARATION,      // Add type declarations
    SetList::INSTANCEOF,            // Instanceof improvements
    SetList::STRICT_BOOLEANS,       // Strict boolean comparisons
])
```

### Framework Sets

```php
// Symfony
use Rector\Symfony\Set\SymfonySetList;
SymfonySetList::SYMFONY_60
SymfonySetList::SYMFONY_70
SymfonySetList::SYMFONY_CODE_QUALITY
SymfonySetList::ANNOTATIONS_TO_ATTRIBUTES

// Doctrine
use Rector\Doctrine\Set\DoctrineSetList;
DoctrineSetList::DOCTRINE_ORM_29
DoctrineSetList::DOCTRINE_ORM_30
DoctrineSetList::ANNOTATIONS_TO_ATTRIBUTES

// PHPUnit
use Rector\PHPUnit\Set\PHPUnitSetList;
PHPUnitSetList::PHPUNIT_100
PHPUnitSetList::PHPUNIT_CODE_QUALITY
PHPUnitSetList::ANNOTATIONS_TO_ATTRIBUTES
```

## Skip Configuration

### Skip Paths

```php
->withSkip([
    __DIR__ . '/src/Legacy/*',
    __DIR__ . '/src/Infrastructure/Migrations/*',
    __DIR__ . '/var/*',
    __DIR__ . '/vendor/*',
])
```

### Skip Rules

```php
use Rector\DeadCode\Rector\ClassMethod\RemoveUnusedPrivateMethodRector;
use Rector\Privatization\Rector\Class_\FinalizeClassesWithoutChildrenRector;

->withSkip([
    // Skip globally
    RemoveUnusedPrivateMethodRector::class,

    // Skip for specific files
    FinalizeClassesWithoutChildrenRector::class => [
        __DIR__ . '/src/Domain/*/Entity/*',
    ],
])
```

## CI Integration

### Dry Run (Preview)

```bash
# Preview changes without applying
vendor/bin/rector process --dry-run

# Output diff format
vendor/bin/rector process --dry-run --output-format=json
```

### GitHub Actions

```yaml
rector:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.4'
    - run: composer install
    - name: Check Rector
      run: vendor/bin/rector process --dry-run --ansi

    # Optional: Auto-fix in PR
    - name: Apply Rector
      if: github.event_name == 'pull_request'
      run: |
        vendor/bin/rector process
        git diff --quiet || (git add -A && git commit -m "Apply Rector fixes")
```

### GitLab CI

```yaml
rector:
  script:
    - vendor/bin/rector process --dry-run
  allow_failure: true

rector:fix:
  script:
    - vendor/bin/rector process
    - git diff --quiet || exit 1
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

## Common Transformations

### PHP 8.4 Features

```php
// Before: Null coalescing
$value = isset($array['key']) ? $array['key'] : 'default';

// After: Null coalescing operator
$value = $array['key'] ?? 'default';

// Before: Constructor property promotion
class User {
    private string $name;

    public function __construct(string $name) {
        $this->name = $name;
    }
}

// After: Property promotion
class User {
    public function __construct(
        private string $name,
    ) {}
}
```

### Dead Code Removal

```php
// Removes:
// - Unused private methods
// - Unused private properties
// - Unreachable code after return/throw
// - Empty methods that do nothing
// - Unused parameters (configurable)
```

### Type Declarations

```php
// Adds return types from:
// - Strict native calls (strlen, count, etc.)
// - Scalar return expressions
// - Property types from constructor

// Before
public function getName() {
    return $this->name;
}

// After
public function getName(): string {
    return $this->name;
}
```

## Generation Instructions

1. **Analyze project:**
   - Check current PHP version
   - Check target PHP version
   - Identify frameworks (Symfony, Laravel)
   - Check for PHPUnit

2. **Select sets:**
   - PHP version upgrade sets
   - Framework migration sets
   - Code quality sets

3. **Configure skips:**
   - Legacy directories
   - Generated code
   - Migrations

4. **Generate config:**
   - Create rector.php
   - Add appropriate sets
   - Configure skips

## Usage

Provide:
- Current PHP version
- Target PHP version
- Frameworks used
- Directories to process
- Directories to skip

The generator will:
1. Create rector.php configuration
2. Include appropriate version sets
3. Include framework sets
4. Configure quality improvements
5. Set up proper skips
