# PHPStan Rules for DDD & Clean Architecture

Custom PHPStan rules, extensions, and configuration patterns for PHP 8.4 projects following DDD principles.

## Level Progression Strategy

| Level | When to Use | Migration Path |
|-------|-------------|----------------|
| 0-3 | Legacy projects, initial adoption | Generate baseline, fix incrementally |
| 4-5 | Active development, moderate strictness | Raise `level` one step at a time (0-10), rebaseline each step |
| 6-7 | Strict typing projects | Generics/iterable value types are checked by the level itself |
| 8 | **Production DDD projects** | Recommended target for Clean Architecture |
| 9 | Maximum strictness | All union types fully resolved |
| max | Bleeding edge (unstable rules) | Only for CI experimentation, not blocking |

### Level Migration Script

```bash
# Test each level to find current passing level
for level in $(seq 0 9); do
    echo "Testing level $level..."
    vendor/bin/phpstan analyse --level=$level --no-progress 2>/dev/null && echo "PASS" || echo "FAIL"
done
```

## Detection Patterns

```bash
# Find PHPStan configuration
grep -rn "phpstan" --include="*.neon" --include="*.neon.dist" .
grep -rn "phpstan" --include="composer.json" .

# Check current level
grep -rn "level:" --include="*.neon" --include="*.neon.dist" .

# Find baseline file
ls -la phpstan-baseline.neon 2>/dev/null

# Check for custom rules
grep -rn "class.*implements.*Rule" --include="*.php" src/
grep -rn "implements.*Rules\\Rule" --include="*.php" src/

# Detect PHPStan extensions in use
grep -rn "phpstan-strict-rules\|phpstan-deprecation-rules\|phpstan-phpunit\|phpstan-doctrine\|phpstan-symfony" composer.json
```

## Configuration Patterns

### Full DDD Configuration (phpstan.neon)

```neon
# phpstan.neon — targets PHPStan 2.x (level 0-10, 10 = max)
includes:
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon
    - vendor/phpstan/phpstan-phpunit/extension.neon
    - phpstan-baseline.neon

parameters:
    level: 8
    phpVersion: 80400

    paths:
        - src
        - tests

    excludePaths:
        - src/Infrastructure/Legacy/*
        - tests/Fixtures/*
        - src/Kernel.php

    # Strict type checking (stricter iterable/generics/mixed checks come from `level` in 2.x)
    checkUninitializedProperties: true
    checkTooWideReturnTypesInProtectedAndPublicMethods: true
    reportUnmatchedIgnoredErrors: true

    # Treat PHPDoc as authoritative
    treatPhpDocTypesAsCertain: true

    # Parallel processing
    parallel:
        maximumNumberOfProcesses: 4

    # Type aliases for domain concepts
    typeAliases:
        OrderId: 'string'
        CustomerId: 'string'
        Money: 'int'

    # Ignored errors with expiration comments
    ignoreErrors:
        -
            message: '#Parameter \#1 .* expects .*, .* given#'
            path: src/Infrastructure/Doctrine/*
            count: 5

    # Custom rules
    rules:
        - App\PHPStan\Rules\ForbiddenFrameworkDependencyRule
        - App\PHPStan\Rules\ImmutableValueObjectRule
        - App\PHPStan\Rules\DomainLayerPurityRule
        - App\PHPStan\Rules\FinalClassRule

    # Services for custom rules
    services:
        - class: App\PHPStan\Rules\ForbiddenFrameworkDependencyRule
          tags: [phpstan.rules.rule]
        - class: App\PHPStan\Rules\ImmutableValueObjectRule
          tags: [phpstan.rules.rule]
        - class: App\PHPStan\Rules\DomainLayerPurityRule
          tags: [phpstan.rules.rule]
        - class: App\PHPStan\Rules\FinalClassRule
          tags: [phpstan.rules.rule]
```

### Minimal Starter Configuration

```neon
# phpstan.neon (starter)
parameters:
    level: 4
    phpVersion: 80400
    paths:
        - src
    excludePaths:
        - src/Infrastructure/Legacy/*
```

## Custom PHPStan Rules for DDD

### ForbiddenFrameworkDependencyRule

Ensures Domain layer has no framework dependencies.

```php
<?php

declare(strict_types=1);

namespace App\PHPStan\Rules;

use PhpParser\Node;
use PhpParser\Node\Stmt\Use_;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * @implements Rule<Use_>
 */
final readonly class ForbiddenFrameworkDependencyRule implements Rule
{
    private const FORBIDDEN_NAMESPACES = [
        'Symfony\\',
        'Doctrine\\',
        'Illuminate\\',
        'Laminas\\',
        'GuzzleHttp\\',
        'Psr\\Log\\',
    ];

    public function getNodeType(): string
    {
        return Use_::class;
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    public function processNode(Node $node, Scope $scope): array
    {
        $file = $scope->getFile();

        if (!str_contains($file, '/Domain/')) {
            return [];
        }

        $errors = [];

        foreach ($node->uses as $use) {
            $usedNamespace = $use->name->toString();

            foreach (self::FORBIDDEN_NAMESPACES as $forbidden) {
                if (str_starts_with($usedNamespace, $forbidden)) {
                    $errors[] = RuleErrorBuilder::message(
                        sprintf(
                            'Domain layer must not depend on framework namespace "%s". Use a domain interface instead.',
                            $forbidden,
                        ),
                    )->identifier('ddd.domainPurity')->build();
                }
            }
        }

        return $errors;
    }
}
```

### ImmutableValueObjectRule

Ensures Value Objects in Domain layer are immutable.

```php
<?php

declare(strict_types=1);

namespace App\PHPStan\Rules;

use PhpParser\Node;
use PhpParser\Node\Stmt\Class_;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * @implements Rule<Class_>
 */
final readonly class ImmutableValueObjectRule implements Rule
{
    public function getNodeType(): string
    {
        return Class_::class;
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    public function processNode(Node $node, Scope $scope): array
    {
        $file = $scope->getFile();

        if (!str_contains($file, '/Domain/') || !str_contains($file, '/ValueObject/')) {
            return [];
        }

        $errors = [];
        $className = $node->name?->toString() ?? 'anonymous';

        if (!$node->isReadonly()) {
            $errors[] = RuleErrorBuilder::message(
                sprintf('Value Object "%s" must be declared as readonly class.', $className),
            )->identifier('ddd.valueObjectReadonly')->build();
        }

        foreach ($node->getMethods() as $method) {
            $methodName = $method->name->toString();

            if (str_starts_with($methodName, 'set') || str_starts_with($methodName, 'change')) {
                $errors[] = RuleErrorBuilder::message(
                    sprintf(
                        'Value Object "%s" must not have setter method "%s". Value Objects are immutable.',
                        $className,
                        $methodName,
                    ),
                )->identifier('ddd.valueObjectImmutable')->build();
            }
        }

        return $errors;
    }
}
```

### DomainLayerPurityRule

Prevents infrastructure concerns from leaking into Domain layer.

```php
<?php

declare(strict_types=1);

namespace App\PHPStan\Rules;

use PhpParser\Node;
use PhpParser\Node\Stmt\Use_;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * @implements Rule<Use_>
 */
final readonly class DomainLayerPurityRule implements Rule
{
    private const FORBIDDEN_PATTERNS = [
        'Application\\' => 'Domain must not depend on Application layer',
        'Infrastructure\\' => 'Domain must not depend on Infrastructure layer',
        'Presentation\\' => 'Domain must not depend on Presentation layer',
        'Api\\' => 'Domain must not depend on API layer',
        'Console\\' => 'Domain must not depend on Console layer',
    ];

    public function getNodeType(): string
    {
        return Use_::class;
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    public function processNode(Node $node, Scope $scope): array
    {
        if (!str_contains($scope->getFile(), '/Domain/')) {
            return [];
        }

        $errors = [];

        foreach ($node->uses as $use) {
            $namespace = $use->name->toString();

            foreach (self::FORBIDDEN_PATTERNS as $pattern => $message) {
                if (str_contains($namespace, $pattern)) {
                    $errors[] = RuleErrorBuilder::message(
                        sprintf('%s. Found: "%s".', $message, $namespace),
                    )->identifier('ddd.layerViolation')->build();
                }
            }
        }

        return $errors;
    }
}
```

### FinalClassRule

Ensures all classes are declared final (DDD best practice).

```php
<?php

declare(strict_types=1);

namespace App\PHPStan\Rules;

use PhpParser\Node;
use PhpParser\Node\Stmt\Class_;
use PHPStan\Analyser\Scope;
use PHPStan\Rules\Rule;
use PHPStan\Rules\RuleErrorBuilder;

/**
 * @implements Rule<Class_>
 */
final readonly class FinalClassRule implements Rule
{
    private const EXCLUDED_SUFFIXES = ['Exception', 'TestCase'];

    public function getNodeType(): string
    {
        return Class_::class;
    }

    /** @return list<\PHPStan\Rules\RuleError> */
    public function processNode(Node $node, Scope $scope): array
    {
        if ($node->isAbstract() || $node->isFinal() || $node->isAnonymous()) {
            return [];
        }

        $className = $node->name?->toString() ?? '';

        foreach (self::EXCLUDED_SUFFIXES as $suffix) {
            if (str_ends_with($className, $suffix)) {
                return [];
            }
        }

        return [
            RuleErrorBuilder::message(
                sprintf('Class "%s" must be declared as final. Use composition over inheritance.', $className),
            )->identifier('ddd.finalClass')->build(),
        ];
    }
}
```

## phpstan-strict-rules Extension

Additional checks enabled by `phpstan/phpstan-strict-rules`:

| Rule | What It Catches |
|------|----------------|
| `BooleansInConditionRule` | Non-boolean expressions in `if`/`while`/ternary |
| `DisallowedConstructsRule` | `empty()`, `isset()` when type system suffices |
| `StrictCallsRule` | `in_array` without strict mode (`true` as 3rd arg) |
| `ClosureReturnTypeRule` | Missing return types on closures |
| `MatchExpressionRule` | Non-exhaustive `match` expressions |
| `NoVariableVariablesRule` | Variable variables (`$$name`) |
| `OverwriteVariablesWithAssignRule` | Foreach reference reuse |

```bash
# Install
composer require --dev phpstan/phpstan-strict-rules
```

## phpstan-deprecation-rules Extension

Detects usage of deprecated code before upgrading.

```bash
# Install
composer require --dev phpstan/phpstan-deprecation-rules

# Find deprecated usages before PHP/framework upgrade
vendor/bin/phpstan analyse --no-progress 2>&1 | grep "deprecated"
```

## Baseline Management

### Generating a Baseline

```bash
# Generate baseline from all current errors
vendor/bin/phpstan analyse --generate-baseline

# Generate baseline for specific error types only
vendor/bin/phpstan analyse --generate-baseline=phpstan-baseline.neon

# Verify no new errors beyond baseline
vendor/bin/phpstan analyse
```

### Reducing Baseline Over Time

```bash
# Show baseline statistics
wc -l phpstan-baseline.neon

# Find most common error types in baseline
grep "message:" phpstan-baseline.neon | sort | uniq -c | sort -rn | head -20

# Regenerate baseline after fixing errors
vendor/bin/phpstan analyse --generate-baseline
```

**Bad:** Ignoring all errors permanently in baseline.

```neon
# phpstan-baseline.neon (never reviewed, grows forever)
parameters:
    ignoreErrors:
        - '#.*#'  # NEVER do this
```

**Good:** Baseline with reduction targets and review dates.

```neon
# phpstan-baseline.neon (reviewed monthly, shrinks over sprint)
parameters:
    ignoreErrors:
        -
            message: '#Call to method .* on mixed#'
            path: src/Infrastructure/Legacy/*
            count: 12  # was 45, target: 0 by Q2
```

## CI Integration

```yaml
# GitHub Actions
- name: PHPStan
  run: vendor/bin/phpstan analyse --no-progress --error-format=github

# GitLab CI
phpstan:
  script:
    - vendor/bin/phpstan analyse --no-progress --error-format=checkstyle > phpstan-report.xml
  artifacts:
    reports:
      junit: phpstan-report.xml
```

## Summary Table

| Rule | Purpose | Level |
|------|---------|-------|
| `ForbiddenFrameworkDependencyRule` | Prevent framework imports in Domain layer | Custom |
| `ImmutableValueObjectRule` | Enforce readonly + no setters on Value Objects | Custom |
| `DomainLayerPurityRule` | Prevent upward/lateral dependencies in Domain | Custom |
| `FinalClassRule` | Enforce `final` keyword on all classes | Custom |
| `phpstan-strict-rules` | Strict boolean, comparison, and construct checks | Extension |
| `phpstan-deprecation-rules` | Detect deprecated API usage before upgrades | Extension |
| `phpstan-phpunit` | PHPUnit assertion type narrowing | Extension |
| `phpstan-doctrine` | Doctrine entity and DQL type support | Extension |
| `phpstan-symfony` | Symfony container and config type support | Extension |
| `treatPhpDocTypesAsCertain` | Trust PHPDoc types when narrowing (default `true`) | Any |
| `reportUnmatchedIgnoredErrors` | Fail on stale `ignoreErrors`/baseline entries (default `true`) | Any |
| `checkUninitializedProperties` | Detect uninitialized class properties | Level 8+ |
| `checkTooWideReturnTypesInProtectedAndPublicMethods` | Flag overly broad return types | Level 9 |
