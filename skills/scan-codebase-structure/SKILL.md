---
name: acc-scan-codebase-structure
description: Scans directory tree to identify architectural layers (Domain, Application, Infrastructure, Presentation), detect framework (Symfony, Laravel, custom), count files per layer, and build project structure map.
---

# Codebase Structure Scanner

## Overview

Analyzes a directory tree to build a structured map of the project: identifies architectural layers, detects the framework in use, counts files per layer, and determines the overall project organization pattern.

## Scanning Process

### Step 1: Directory Tree Analysis

```bash
# Get top-level structure
Glob: "*" in target path

# Get full PHP file tree
Glob: "**/*.php" in target path

# Get configuration files
Glob: "{composer.json,*.yaml,*.yml,*.xml,*.neon,*.json}" in target path
```

### Step 2: Framework Detection

| Framework | Detection Pattern | Key Files |
|-----------|-------------------|-----------|
| Symfony | `symfony/framework-bundle` in composer.json | `config/bundles.php`, `config/services.yaml` |
| Laravel | `laravel/framework` in composer.json | `artisan`, `app/Providers/` |
| Yii2 | `yiisoft/yii2` in composer.json | `config/web.php`, `config/console.php` |
| Slim | `slim/slim` in composer.json | `routes/`, `public/index.php` |
| Custom/None | No major framework | `composer.json` only |

```bash
# Check composer.json for framework
Grep: "symfony/framework-bundle|laravel/framework|yiisoft/yii2|slim/slim" in composer.json

# Check for Symfony bundles
Glob: "config/bundles.php"

# Check for Laravel artisan
Glob: "artisan"

# Check for framework config patterns
Glob: "config/{services,bundles,web,console,app}.{php,yaml,yml}"
```

### Step 3: Layer Identification

Detect architectural layers by namespace patterns and directory structure:

#### Domain Layer

```bash
# Standard DDD directories
Glob: "**/Domain/**/*.php"
Glob: "**/Model/**/*.php"
Glob: "**/Entity/**/*.php"

# Domain components
Grep: "namespace.*\\\\Domain\\\\" --glob "**/*.php"
Grep: "namespace.*\\\\Model\\\\" --glob "**/*.php"

# Domain markers
Grep: "interface.*Repository" --glob "**/*.php"
Grep: "class.*ValueObject|extends.*ValueObject" --glob "**/*.php"
Grep: "class.*AggregateRoot|extends.*AggregateRoot" --glob "**/*.php"
Grep: "class.*DomainEvent|extends.*DomainEvent" --glob "**/*.php"
```

#### Application Layer

```bash
# Standard Application directories
Glob: "**/Application/**/*.php"
Glob: "**/UseCase/**/*.php"
Glob: "**/Service/**/*.php"

# Application components
Grep: "namespace.*\\\\Application\\\\" --glob "**/*.php"
Grep: "namespace.*\\\\UseCase\\\\" --glob "**/*.php"

# CQRS markers
Grep: "CommandHandler|QueryHandler|CommandBus|QueryBus" --glob "**/*.php"
Grep: "class.*Command\\b|class.*Query\\b" --glob "**/*.php"
```

#### Infrastructure Layer

```bash
# Standard Infrastructure directories
Glob: "**/Infrastructure/**/*.php"
Glob: "**/Persistence/**/*.php"
Glob: "**/Adapter/**/*.php"

# Infrastructure components
Grep: "namespace.*\\\\Infrastructure\\\\" --glob "**/*.php"
Grep: "implements.*Repository" --glob "**/*.php"

# External integrations
Grep: "Redis|RabbitMQ|Doctrine|Elasticsearch|Guzzle" --glob "**/*.php"
```

#### Presentation Layer

```bash
# Standard Presentation directories
Glob: "**/Controller/**/*.php"
Glob: "**/Action/**/*.php"
Glob: "**/Api/**/*.php"
Glob: "**/Console/**/*.php"

# Presentation components
Grep: "namespace.*\\\\(Controller|Action|Api|Console|Cli)\\\\" --glob "**/*.php"
Grep: "extends.*Controller|extends.*AbstractController" --glob "**/*.php"
Grep: "#\\[Route\\(|@Route" --glob "**/*.php"
```

### Step 4: Module/Bounded Context Detection

```bash
# Detect bounded contexts (common patterns)
# Pattern 1: src/{Context}/Domain|Application|Infrastructure
Glob: "src/*/Domain/"
Glob: "src/*/Application/"

# Pattern 2: src/Domain/{Context}/
Glob: "src/Domain/*/"

# Pattern 3: packages/{context}/
Glob: "packages/*/"

# Pattern 4: modules/{context}/
Glob: "modules/*/"
```

### Step 5: File Statistics

For each detected layer, count:
- Total PHP files
- Classes (class keyword)
- Interfaces (interface keyword)
- Abstract classes
- Enums (PHP 8.1+)
- Traits

```bash
# Count by type per directory
Grep: "^(final |abstract |readonly )?class " --glob "**/*.php" in each layer
Grep: "^interface " --glob "**/*.php" in each layer
Grep: "^enum " --glob "**/*.php" in each layer
Grep: "^trait " --glob "**/*.php" in each layer
```

## Output Format

```markdown
## Project Structure Map

### Framework
- **Framework:** Symfony 6.4 / Laravel 11 / Custom
- **PHP Version:** 8.4 (from composer.json require.php)
- **Type:** Monolith / Modular Monolith / Microservice

### Layers Overview

| Layer | Directory | Files | Classes | Interfaces | Enums |
|-------|-----------|-------|---------|------------|-------|
| Domain | src/Domain/ | 45 | 30 | 10 | 5 |
| Application | src/Application/ | 22 | 20 | 2 | 0 |
| Infrastructure | src/Infrastructure/ | 18 | 15 | 0 | 3 |
| Presentation | src/Api/, src/Console/ | 12 | 12 | 0 | 0 |

### Bounded Contexts (if detected)

| Context | Domain | Application | Infrastructure | Presentation |
|---------|--------|-------------|----------------|-------------|
| Order | 15 files | 8 files | 6 files | 4 files |
| User | 10 files | 5 files | 4 files | 3 files |
| Payment | 8 files | 4 files | 3 files | 2 files |

### Directory Tree
```
src/
├── Domain/
│   ├── Order/
│   │   ├── Entity/
│   │   ├── ValueObject/
│   │   ├── Event/
│   │   └── Repository/
│   └── User/
├── Application/
│   ├── Command/
│   ├── Query/
│   └── Service/
├── Infrastructure/
│   ├── Persistence/
│   └── Messaging/
└── Presentation/
    ├── Api/
    └── Console/
```

### Key Configuration Files
| File | Purpose |
|------|---------|
| composer.json | Dependencies, autoloading |
| config/services.yaml | DI container configuration |
| config/routes.yaml | Route definitions |
```

## Key Indicators

### Project Size Classification

| Size | Files | Description |
|------|-------|-------------|
| Small | < 50 | Single module or microservice |
| Medium | 50-200 | Standard application |
| Large | 200-500 | Complex monolith |
| Very Large | > 500 | Enterprise application |

### Layer Health Indicators

- **Domain > Infrastructure** = Good DDD adherence
- **Infrastructure > Domain** = Potential coupling issues
- **No Application layer** = Possible logic leak to controllers
- **No Domain layer** = Transaction script pattern

## Integration

This skill provides the structural foundation for:
- `acc-identify-entry-points` — uses layer map to find entry points
- `acc-detect-architecture-pattern` — uses structure for pattern detection
- All analysis agents — uses layer map for scoped analysis
