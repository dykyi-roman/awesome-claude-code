---
name: acc-ci-tools-knowledge
description: PHP CI tools knowledge base. Provides PHPStan levels and configuration, Psalm integration, PHP-CS-Fixer rules, DEPTRAC layer analysis, Rector automated refactoring, and code coverage tools.
---

# PHP CI Tools Knowledge Base

Quick reference for PHP static analysis, code quality, and testing tools.

## PHPStan

### Levels Overview

| Level | Description | Use Case |
|-------|-------------|----------|
| 0 | Basic checks (undefined variables, classes) | Legacy projects, quick start |
| 1 | + Undefined methods, properties | Minimal safety |
| 2 | + Unknown methods on `$this` | Medium safety |
| 3 | + Return types | Recommended minimum |
| 4 | + Dead code, unreachable | **Recommended for new projects** |
| 5 | + Argument types | Standard compliance |
| 6 | + Missing typehints | Strict typing |
| 7 | + Union types strict | High strictness |
| 8 | + No mixed, nullsafe | **Production recommended** |
| 9 | + Maximum strictness | Clean Architecture |
| max | Bleeding edge | Experimental only |

### Configuration Template

```neon
# phpstan.neon
includes:
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon
    - vendor/phpstan/phpstan-phpunit/extension.neon
    - phpstan-baseline.neon

parameters:
    level: 8
    paths:
        - src
        - tests
    excludePaths:
        - src/Infrastructure/Legacy/*
        - tests/Fixtures/*

    # PHP version
    phpVersion: 80400

    # Strict rules
    checkMissingIterableValueType: true
    checkGenericClassInNonGenericObjectType: true
    checkUninitializedProperties: true

    # Custom rules
    ignoreErrors:
        - '#Call to an undefined method [a-zA-Z0-9\\_]+::getId\(\)#'

    # Type aliases
    typeAliases:
        UserId: 'string'

    # Parallel processing
    parallel:
        maximumNumberOfProcesses: 4
```

### Common Extensions

| Extension | Purpose |
|-----------|---------|
| `phpstan-strict-rules` | Additional strict checks |
| `phpstan-deprecation-rules` | Deprecated usage detection |
| `phpstan-phpunit` | PHPUnit support |
| `phpstan-doctrine` | Doctrine ORM support |
| `phpstan-symfony` | Symfony container support |

### Baseline Management

```bash
# Generate baseline (for existing projects)
vendor/bin/phpstan analyse --generate-baseline

# Analyze with baseline
vendor/bin/phpstan analyse

# CI command
vendor/bin/phpstan analyse --no-progress --error-format=checkstyle > phpstan-report.xml
```

## Psalm

### Error Levels

| Level | Description |
|-------|-------------|
| 1 | Maximum strictness (recommended for new) |
| 2 | Very strict |
| 3 | Strict (recommended for existing) |
| 4 | Relaxed |
| 5-8 | Increasingly permissive |

### Configuration Template

```xml
<!-- psalm.xml -->
<?xml version="1.0"?>
<psalm
    errorLevel="2"
    resolveFromConfigFile="true"
    findUnusedBaselineEntry="true"
    findUnusedCode="true"
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

    <issueHandlers>
        <MixedAssignment errorLevel="suppress"/>
        <PropertyNotSetInConstructor>
            <errorLevel type="suppress">
                <directory name="src/Infrastructure/Doctrine"/>
            </errorLevel>
        </PropertyNotSetInConstructor>
    </issueHandlers>

    <plugins>
        <pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
        <pluginClass class="Psalm\SymfonyPsalmPlugin\Plugin"/>
    </plugins>
</psalm>
```

### Useful Commands

```bash
# Full analysis
vendor/bin/psalm

# Generate baseline
vendor/bin/psalm --set-baseline=psalm-baseline.xml

# Security analysis
vendor/bin/psalm --taint-analysis

# CI output
vendor/bin/psalm --output-format=checkstyle > psalm-report.xml
```

## PHP-CS-Fixer

### Configuration Template

```php
<?php
// .php-cs-fixer.dist.php

declare(strict_types=1);

use PhpCsFixer\Config;
use PhpCsFixer\Finder;

$finder = Finder::create()
    ->in([
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->exclude([
        'var',
        'vendor',
    ]);

return (new Config())
    ->setRiskyAllowed(true)
    ->setRules([
        '@PER-CS2.0' => true,
        '@PER-CS2.0:risky' => true,
        '@PHP84Migration' => true,
        '@PHP80Migration:risky' => true,
        '@PHPUnit100Migration:risky' => true,

        // Strict rules
        'declare_strict_types' => true,
        'strict_param' => true,
        'strict_comparison' => true,

        // Modern PHP
        'array_syntax' => ['syntax' => 'short'],
        'modernize_strpos' => true,
        'no_alias_functions' => true,
        'void_return' => true,

        // Clean code
        'no_unused_imports' => true,
        'ordered_imports' => ['imports_order' => ['class', 'function', 'const']],
        'single_line_throw' => false,
        'trailing_comma_in_multiline' => true,

        // DocBlocks
        'no_superfluous_phpdoc_tags' => true,
        'phpdoc_align' => false,
        'phpdoc_separation' => true,
    ])
    ->setFinder($finder)
    ->setCacheFile('.php-cs-fixer.cache');
```

### Commands

```bash
# Check (dry run)
vendor/bin/php-cs-fixer fix --dry-run --diff

# Fix
vendor/bin/php-cs-fixer fix

# CI check
vendor/bin/php-cs-fixer fix --dry-run --format=checkstyle > cs-report.xml
```

## DEPTRAC

### Configuration Template

```yaml
# deptrac.yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Domain
      collectors:
        - type: directory
          value: src/Domain/.*

    - name: Application
      collectors:
        - type: directory
          value: src/Application/.*

    - name: Infrastructure
      collectors:
        - type: directory
          value: src/Infrastructure/.*

    - name: Presentation
      collectors:
        - type: directory
          value: src/(Api|Web|Console)/.*

  ruleset:
    Domain: []  # Domain depends on nothing

    Application:
      - Domain

    Infrastructure:
      - Domain
      - Application

    Presentation:
      - Application
      - Domain

  skip_violations:
    # Temporary violations during migration
    App\Infrastructure\Legacy\*:
      - App\Domain\*
```

### Commands

```bash
# Analyze
vendor/bin/deptrac analyse

# With baseline
vendor/bin/deptrac analyse --baseline=deptrac-baseline.yaml

# CI output
vendor/bin/deptrac analyse --formatter=junit --output=deptrac-report.xml
```

## Rector

### Configuration Template

```php
<?php
// rector.php

declare(strict_types=1);

use Rector\Config\RectorConfig;
use Rector\Set\ValueObject\LevelSetList;
use Rector\Set\ValueObject\SetList;
use Rector\PHPUnit\Set\PHPUnitSetList;

return RectorConfig::configure()
    ->withPaths([
        __DIR__ . '/src',
        __DIR__ . '/tests',
    ])
    ->withSkip([
        __DIR__ . '/src/Infrastructure/Legacy',
    ])
    ->withPhpSets(php84: true)
    ->withSets([
        SetList::CODE_QUALITY,
        SetList::DEAD_CODE,
        SetList::TYPE_DECLARATION,
        PHPUnitSetList::PHPUNIT_100,
    ])
    ->withPreparedSets(
        deadCode: true,
        codeQuality: true,
        typeDeclarations: true,
        privatization: true,
        earlyReturn: true,
    );
```

### Commands

```bash
# Preview changes (dry run)
vendor/bin/rector process --dry-run

# Apply changes
vendor/bin/rector process

# Single file
vendor/bin/rector process src/Domain/Order.php
```

## Code Coverage Tools

### PHPUnit Coverage

```xml
<!-- phpunit.xml -->
<phpunit>
    <coverage>
        <report>
            <clover outputFile="coverage.xml"/>
            <html outputDirectory="coverage-html"/>
            <text outputFile="coverage.txt"/>
        </report>
        <include>
            <directory suffix=".php">src</directory>
        </include>
        <exclude>
            <directory>src/Infrastructure/Legacy</directory>
        </exclude>
    </coverage>
</phpunit>
```

### Coverage Drivers

| Driver | Speed | Accuracy | Use Case |
|--------|-------|----------|----------|
| Xdebug | Slow | High | Local dev, accurate metrics |
| PCOV | Fast | High | CI, fast feedback |
| PHPDBG | Medium | Medium | Alternative |

### CI Integration

```yaml
# GitHub Actions with PCOV
- uses: shivammathur/setup-php@v2
  with:
    php-version: '8.4'
    coverage: pcov

- run: vendor/bin/phpunit --coverage-clover coverage.xml

- uses: codecov/codecov-action@v4
  with:
    files: coverage.xml
```

## Infection (Mutation Testing)

### Configuration

```json
{
    "$schema": "vendor/infection/infection/resources/schema.json",
    "source": {
        "directories": ["src"]
    },
    "logs": {
        "text": "infection.log",
        "html": "infection.html"
    },
    "mutators": {
        "@default": true
    },
    "minMsi": 80,
    "minCoveredMsi": 90
}
```

### Commands

```bash
# Run with coverage
vendor/bin/infection --threads=4

# CI mode
vendor/bin/infection --min-msi=80 --min-covered-msi=90 --threads=max
```

## Tool Comparison Matrix

| Aspect | PHPStan | Psalm | DEPTRAC | Rector |
|--------|---------|-------|---------|--------|
| Type analysis | ✅ Deep | ✅ Deep | ❌ | ⚠️ Basic |
| Architecture | ❌ | ❌ | ✅ | ❌ |
| Security | ⚠️ | ✅ Taint | ❌ | ❌ |
| Auto-fix | ❌ | ❌ | ❌ | ✅ |
| Speed | Fast | Medium | Fast | Slow |
| Config | NEON | XML | YAML | PHP |

## Recommended CI Setup

```yaml
lint:
  parallel:
    matrix:
      - TOOL: [phpstan, psalm, cs-fixer, deptrac]
  script:
    - case $TOOL in
        phpstan) vendor/bin/phpstan analyse ;;
        psalm) vendor/bin/psalm ;;
        cs-fixer) vendor/bin/php-cs-fixer fix --dry-run ;;
        deptrac) vendor/bin/deptrac analyse ;;
      esac
```

## References

For detailed information, load these reference files:

- `references/phpstan-rules.md` — Custom PHPStan rules
- `references/psalm-plugins.md` — Psalm plugins and annotations
- `references/rector-rules.md` — Rector upgrade sets
