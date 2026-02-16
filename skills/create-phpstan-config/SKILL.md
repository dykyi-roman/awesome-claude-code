---
name: acc-create-phpstan-config
description: Generates PHPStan configurations for PHP projects. Creates phpstan.neon with appropriate level, extensions, paths, baseline support, and DDD-specific rules.
---

# PHPStan Configuration Generator

Generates optimized PHPStan configurations for PHP 8.4+ projects.

## Generated Files

```
phpstan.neon              # Main configuration
phpstan-baseline.neon     # Error baseline (if needed)
```

## Configuration by Project Type

### New Project (Level 8-9)

```neon
# phpstan.neon
includes:
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon
    - vendor/phpstan/phpstan-phpunit/extension.neon

parameters:
    level: 8
    phpVersion: 80400

    paths:
        - src
        - tests

    excludePaths:
        - tests/Fixtures/*
        - src/Infrastructure/Legacy/*

    # Strict type checking
    checkMissingIterableValueType: true
    checkGenericClassInNonGenericObjectType: true
    checkUninitializedProperties: true
    checkImplicitMixed: true
    reportUnmatchedIgnoredErrors: true

    # Parallel processing
    parallel:
        maximumNumberOfProcesses: 4
```

### Existing Project with Baseline

```neon
# phpstan.neon
includes:
    - phpstan-baseline.neon
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon

parameters:
    level: 6

    paths:
        - src
        - tests

    excludePaths:
        - src/Legacy/*
        - tests/Fixtures/*

    # Gradually increase strictness
    checkMissingIterableValueType: false
    checkGenericClassInNonGenericObjectType: false

    # Type aliases for legacy code
    typeAliases:
        UserId: 'int|string'
        Timestamp: 'int|DateTimeInterface'
```

### DDD Project Configuration

```neon
# phpstan.neon
includes:
    - vendor/phpstan/phpstan-strict-rules/rules.neon
    - vendor/phpstan/phpstan-deprecation-rules/rules.neon
    - vendor/phpstan/phpstan-phpunit/extension.neon
    - vendor/phpstan/phpstan-doctrine/extension.neon

parameters:
    level: 9
    phpVersion: 80400

    paths:
        - src

    excludePaths:
        - src/Infrastructure/Migrations/*

    # Strict for Domain layer
    checkMissingIterableValueType: true
    checkGenericClassInNonGenericObjectType: true
    checkUninitializedProperties: true
    checkImplicitMixed: true

    # Report all issues
    reportUnmatchedIgnoredErrors: true
    reportStaticMethodSignatures: true

    # Parallel for speed
    parallel:
        maximumNumberOfProcesses: 8
        processTimeout: 300.0

    # Custom parameters
    doctrine:
        repositoryClass: App\Infrastructure\Persistence\DoctrineRepository
        objectManagerLoader: tests/object-manager.php

    # Ignore patterns
    ignoreErrors:
        # Doctrine entities
        - '#Property .+ has no type specified#'
          path: src/Infrastructure/Doctrine/Entity/*

        # Value Objects immutability
        - '#Readonly property .+ is assigned outside of its declaring class#'
          path: src/Domain/*/ValueObject/*

    # Custom rules
    rules:
        - App\PHPStan\DomainLayerRule
        - App\PHPStan\ValueObjectImmutabilityRule
```

## Extension Configuration

### PHPUnit Extension

```neon
includes:
    - vendor/phpstan/phpstan-phpunit/extension.neon

parameters:
    # PHPUnit-specific settings
    phpunit:
        configPath: phpunit.xml
```

### Doctrine Extension

```neon
includes:
    - vendor/phpstan/phpstan-doctrine/extension.neon

parameters:
    doctrine:
        repositoryClass: Doctrine\ORM\EntityRepository
        objectManagerLoader: tests/object-manager.php
```

### Symfony Extension

```neon
includes:
    - vendor/phpstan/phpstan-symfony/extension.neon
    - vendor/phpstan/phpstan-symfony/rules.neon

parameters:
    symfony:
        containerXmlPath: var/cache/dev/App_KernelDevDebugContainer.xml
        consoleApplicationLoader: tests/console-application.php
```

## Custom Error Patterns

### Common Ignore Patterns

```neon
parameters:
    ignoreErrors:
        # Constructor property promotion
        - '#Constructor of class .+ has an unused parameter#'

        # Doctrine entities
        - '#Property .+ does not accept null#'
          path: src/Infrastructure/Doctrine/Entity/*

        # Test doubles
        - '#Call to an undefined method .+Mock::#'
          path: tests/*

        # Dynamic properties in tests
        - '#Access to an undefined property .+Test::\$#'
          path: tests/*

        # Factory methods
        - '#Method .+Factory::create\(\) should return .+ but returns#'

        # Event handlers
        - '#Parameter .+ of method .+Handler::__invoke\(\) has no type specified#'
```

### Error Baseline Generation

```bash
# Generate baseline for existing errors
vendor/bin/phpstan analyse --generate-baseline

# Generate baseline with specific name
vendor/bin/phpstan analyse --generate-baseline=phpstan-baseline.neon

# Analyze and exclude baseline errors
vendor/bin/phpstan analyse
```

## Level Migration Guide

### From Level 0 to Level 8

```neon
# Step 1: Start with baseline at current level
parameters:
    level: 0

# Step 2: Generate baseline
# vendor/bin/phpstan analyse --generate-baseline

# Step 3: Increase level
parameters:
    level: 1

# Step 4: Fix new errors or add to baseline
# Repeat until level 8
```

### Recommended Progression

| Level | Focus | Timeline |
|-------|-------|----------|
| 0-2 | Basic errors, undefined variables | Week 1 |
| 3-4 | Return types, dead code | Week 2-3 |
| 5-6 | Argument types, type hints | Week 4-6 |
| 7-8 | Union types, no mixed | Week 7-10 |
| 9 | Maximum strictness | Ongoing |

## CI Configuration

### GitHub Actions

```yaml
phpstan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.4'
    - run: composer install
    - run: vendor/bin/phpstan analyse --memory-limit=1G --error-format=github
```

### GitLab CI

```yaml
phpstan:
  script:
    - vendor/bin/phpstan analyse --memory-limit=1G --error-format=gitlab > phpstan.json
  artifacts:
    reports:
      codequality: phpstan.json
```

## Performance Optimization

```neon
parameters:
    # Parallel processing
    parallel:
        maximumNumberOfProcesses: 8
        processTimeout: 300.0

    # Cache results
    tmpDir: var/cache/phpstan

    # Memory limit
    memoryLimitFile: 1G
```

## Generation Instructions

1. **Analyze project:**
   - Check `composer.json` for PHPStan version
   - Check existing `phpstan.neon`
   - Identify framework (Symfony, Laravel, etc.)
   - Count existing errors

2. **Determine level:**
   - New project: Level 8-9
   - Existing with few errors: Current + 1
   - Legacy: Level 0 + baseline

3. **Add extensions:**
   - PHPUnit if tests exist
   - Doctrine if ORM used
   - Symfony/Laravel if framework

4. **Generate baseline if needed:**
   - For existing projects with errors
   - Include command to regenerate

## Usage

Provide:
- Project type (new/existing/legacy)
- Framework (Symfony, Laravel, none)
- Current error count (if existing)
- Target level (optional)

The generator will:
1. Create appropriate configuration
2. Add relevant extensions
3. Include ignore patterns
4. Generate baseline commands if needed
