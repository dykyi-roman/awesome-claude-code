---
name: acc-create-psalm-config
description: Generates Psalm configurations for PHP projects. Creates psalm.xml with appropriate error level, plugins, taint analysis, and DDD-specific settings.
---

# Psalm Configuration Generator

Generates optimized Psalm configurations for PHP 8.4+ projects.

## Generated Files

```
psalm.xml                 # Main configuration
psalm-baseline.xml        # Error baseline (if needed)
```

## Configuration by Project Type

### New Project (Level 1-2)

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="2"
    resolveFromConfigFile="true"
    findUnusedBaselineEntry="true"
    findUnusedCode="true"
    findUnusedVariablesAndParams="true"
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

    <plugins>
        <pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
    </plugins>
</psalm>
```

### Existing Project with Baseline

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="4"
    resolveFromConfigFile="true"
    errorBaseline="psalm-baseline.xml"
    findUnusedBaselineEntry="true"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="https://getpsalm.org/schema/config"
    xsi:schemaLocation="https://getpsalm.org/schema/config vendor/vimeo/psalm/config.xsd"
>
    <projectFiles>
        <directory name="src"/>
        <ignoreFiles>
            <directory name="vendor"/>
            <directory name="src/Legacy"/>
        </ignoreFiles>
    </projectFiles>

    <issueHandlers>
        <!-- Gradually enable -->
        <MixedAssignment errorLevel="suppress"/>
        <MixedMethodCall errorLevel="suppress"/>
        <MixedArgument errorLevel="suppress"/>
    </issueHandlers>
</psalm>
```

### DDD Project Configuration

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="1"
    resolveFromConfigFile="true"
    findUnusedBaselineEntry="true"
    findUnusedCode="true"
    findUnusedVariablesAndParams="true"
    strictBinaryOperands="true"
    phpVersion="8.4"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns="https://getpsalm.org/schema/config"
    xsi:schemaLocation="https://getpsalm.org/schema/config vendor/vimeo/psalm/config.xsd"
>
    <projectFiles>
        <directory name="src"/>
        <ignoreFiles>
            <directory name="vendor"/>
            <directory name="src/Infrastructure/Migrations"/>
        </ignoreFiles>
    </projectFiles>

    <!-- Domain layer - strictest -->
    <projectFiles>
        <directory name="src/Domain">
            <errorLevel type="error">
                <MixedAssignment/>
                <MixedMethodCall/>
                <MixedArgument/>
            </errorLevel>
        </directory>
    </projectFiles>

    <plugins>
        <pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
        <pluginClass class="Weirdan\DoctrinePsalmPlugin\Plugin"/>
        <pluginClass class="Psalm\SymfonyPsalmPlugin\Plugin"/>
    </plugins>

    <issueHandlers>
        <!-- Doctrine entities -->
        <PropertyNotSetInConstructor>
            <errorLevel type="suppress">
                <directory name="src/Infrastructure/Doctrine/Entity"/>
            </errorLevel>
        </PropertyNotSetInConstructor>

        <!-- Value Objects immutability -->
        <ImmutablePropertyAssignment>
            <errorLevel type="error">
                <directory name="src/Domain"/>
            </errorLevel>
        </ImmutablePropertyAssignment>

        <!-- Allow missing return types in interfaces (for contravariance) -->
        <MissingReturnType>
            <errorLevel type="suppress">
                <directory name="src/Domain/Repository"/>
            </errorLevel>
        </MissingReturnType>
    </issueHandlers>

    <!-- Stubs for external libraries -->
    <stubs>
        <file name="stubs/Doctrine.phpstub"/>
    </stubs>
</psalm>
```

## Plugin Configuration

### PHPUnit Plugin

```xml
<plugins>
    <pluginClass class="Psalm\PhpUnitPlugin\Plugin"/>
</plugins>
```

### Doctrine Plugin

```xml
<plugins>
    <pluginClass class="Weirdan\DoctrinePsalmPlugin\Plugin">
        <enableObjectManagerGenerator value="true"/>
    </pluginClass>
</plugins>
```

### Symfony Plugin

```xml
<plugins>
    <pluginClass class="Psalm\SymfonyPsalmPlugin\Plugin">
        <containerXml>var/cache/dev/App_KernelDevDebugContainer.xml</containerXml>
    </pluginClass>
</plugins>
```

### Laravel Plugin

```xml
<plugins>
    <pluginClass class="Psalm\LaravelPlugin\Plugin"/>
</plugins>
```

## Issue Handlers

### Common Suppressions

```xml
<issueHandlers>
    <!-- Allow mixed in legacy code -->
    <MixedAssignment>
        <errorLevel type="suppress">
            <directory name="src/Legacy"/>
        </errorLevel>
    </MixedAssignment>

    <!-- Allow property initialization in setUp() -->
    <PropertyNotSetInConstructor>
        <errorLevel type="suppress">
            <directory name="tests"/>
        </errorLevel>
    </PropertyNotSetInConstructor>

    <!-- Suppress for mocks -->
    <UndefinedMagicMethod>
        <errorLevel type="suppress">
            <directory name="tests"/>
        </errorLevel>
    </UndefinedMagicMethod>

    <!-- Allow unused parameters in event handlers -->
    <UnusedParam>
        <errorLevel type="suppress">
            <file name="src/Application/EventHandler/*.php"/>
        </errorLevel>
    </UnusedParam>

    <!-- Suppress deprecated in migrations -->
    <DeprecatedMethod>
        <errorLevel type="suppress">
            <directory name="src/Infrastructure/Migrations"/>
        </errorLevel>
    </DeprecatedMethod>
</issueHandlers>
```

### Strict Mode for Domain

```xml
<issueHandlers>
    <!-- Enforce strict types in Domain -->
    <MixedAssignment>
        <errorLevel type="error">
            <directory name="src/Domain"/>
        </errorLevel>
        <errorLevel type="suppress">
            <directory name="src/Infrastructure"/>
        </errorLevel>
    </MixedAssignment>

    <!-- Enforce immutability -->
    <ImmutablePropertyAssignment>
        <errorLevel type="error">
            <directory name="src/Domain/ValueObject"/>
        </errorLevel>
    </ImmutablePropertyAssignment>
</issueHandlers>
```

## Taint Analysis Configuration

```xml
<?xml version="1.0"?>
<psalm
    errorLevel="2"
    runTaintAnalysis="true"
>
    <!-- Taint sources -->
    <taintAnalysis>
        <taintSource name="$_GET"/>
        <taintSource name="$_POST"/>
        <taintSource name="$_REQUEST"/>
        <taintSource name="$_COOKIE"/>

        <!-- Custom sources -->
        <taintSource name="Request::input"/>
        <taintSource name="Request::query"/>
    </taintAnalysis>

    <!-- Taint sinks -->
    <issueHandlers>
        <TaintedSql errorLevel="error"/>
        <TaintedHtml errorLevel="error"/>
        <TaintedShell errorLevel="error"/>
        <TaintedFile errorLevel="error"/>
        <TaintedHeader errorLevel="error"/>
        <TaintedSSRF errorLevel="error"/>
    </issueHandlers>
</psalm>
```

## Baseline Management

### Generate Baseline

```bash
# Generate baseline for all errors
vendor/bin/psalm --set-baseline=psalm-baseline.xml

# Update baseline (remove fixed issues)
vendor/bin/psalm --update-baseline

# Analyze with baseline
vendor/bin/psalm
```

### Baseline Format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<files psalm-version="5.x">
  <file src="src/SomeClass.php">
    <MixedAssignment>
      <code>$variable</code>
    </MixedAssignment>
  </file>
</files>
```

## Level Migration Guide

### Error Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| 1 | Strictest | New projects, Domain layer |
| 2 | Very strict | Clean codebases |
| 3 | Strict | Recommended default |
| 4 | Relaxed | Mixed codebases |
| 5-7 | Permissive | Legacy code |
| 8 | Very permissive | Initial analysis only |

### Migration Steps

```xml
<!-- Step 1: Start with baseline -->
<psalm errorLevel="8" errorBaseline="psalm-baseline.xml">

<!-- Step 2: Decrease level, update baseline -->
<psalm errorLevel="7" errorBaseline="psalm-baseline.xml">

<!-- Step 3: Continue until target level -->
<psalm errorLevel="3">
```

## CI Configuration

### GitHub Actions

```yaml
psalm:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: shivammathur/setup-php@v2
      with:
        php-version: '8.4'
    - run: composer install
    - run: vendor/bin/psalm --output-format=github
```

### GitLab CI

```yaml
psalm:
  script:
    - vendor/bin/psalm --output-format=checkstyle > psalm-report.xml
  artifacts:
    paths:
      - psalm-report.xml
```

### Security Scan

```yaml
psalm-taint:
  script:
    - vendor/bin/psalm --taint-analysis
  allow_failure: true
```

## Generation Instructions

1. **Analyze project:**
   - Check `composer.json` for Psalm version
   - Check existing `psalm.xml`
   - Identify framework
   - Count existing errors

2. **Determine level:**
   - New project: Level 1-2
   - Existing clean: Level 3
   - Legacy: Level 5+ with baseline

3. **Add plugins:**
   - PHPUnit always
   - Doctrine if ORM
   - Symfony/Laravel if framework

4. **Configure issue handlers:**
   - Strict for Domain
   - Relaxed for Infrastructure/Legacy

## Usage

Provide:
- Project type (new/existing/legacy)
- Framework (Symfony, Laravel, none)
- Target level (optional)
- Taint analysis (yes/no)

The generator will:
1. Create appropriate configuration
2. Add relevant plugins
3. Configure issue handlers
4. Set up baseline if needed
5. Include taint analysis if requested
