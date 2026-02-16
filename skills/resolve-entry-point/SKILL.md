---
name: acc-resolve-entry-point
description: Resolves HTTP routes (GET /api/orders) and console commands (app:process-payments) to their handler files. Detects framework, searches route/command definitions, extracts handler class and method, locates file via PSR-4 mapping.
---

# Entry Point Resolver

## Overview

Resolves user-provided HTTP routes or console commands to their handler file(s). Given a route like `POST /api/orders` or a command like `app:process-payments`, finds the exact handler class, method, file path, and surrounding context (middleware, route definition, schedule).

## Input Types

### HTTP Route

```
Pattern: ^(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/
Examples:
  GET /api/orders
  POST /api/orders/{id}/status
  DELETE /api/users/{id}
```

### Console Command

```
Pattern: ^[a-z][a-z0-9_-]*:[a-z][a-z0-9:_-]*$
Examples:
  app:process-payments
  import:products
  cache:clear
```

## Resolution Process

### Step 1: Detect Framework

```bash
# Check for Symfony
Glob: "config/bundles.php"
Grep: "symfony/framework-bundle" --glob "composer.json"

# Check for Laravel
Glob: "artisan"
Grep: "laravel/framework" --glob "composer.json"

# Check for Slim
Grep: "slim/slim" --glob "composer.json"

# Fallback: generic PHP (attribute-based routing)
```

### Step 2: Resolve HTTP Route

#### Extract HTTP method and path from input

```
Input: "POST /api/orders/{id}/status"
Method: POST
Path: /api/orders/{id}/status
Path pattern (regex-escaped): /api/orders/\{[^}]+\}/status
Path pattern (simplified): /api/orders/.*/status
```

#### Symfony Route Resolution

```bash
# 1. Search PHP attribute routes
Grep: "#\[Route\(" --glob "**/*.php" --output_mode content

# Then filter by path match:
# Look for exact path or path with parameter placeholders
Grep: "#\[Route\(['\"][^'\"]*(/api/orders)" --glob "**/*.php" --output_mode content

# 2. Search YAML route definitions
Grep: "path:\s.*(/api/orders)" --glob "config/routes*.yaml" --output_mode content
Grep: "path:\s.*(/api/orders)" --glob "config/routes/**/*.yaml" --output_mode content

# 3. Search XML route definitions
Grep: "path=\"[^\"]*(/api/orders)" --glob "config/routes*.xml" --output_mode content

# 4. Check for method restriction
# In the found route attribute, look for methods parameter
Grep: "methods:\s*\[.*POST" in matched file --output_mode content
```

#### Laravel Route Resolution

```bash
# 1. Search routes files
Grep: "Route::(post|any)\(\s*['\"]/?api/orders" --glob "routes/*.php" --output_mode content

# 2. Search for resource routes
Grep: "Route::apiResource\(['\"]orders" --glob "routes/*.php" --output_mode content
Grep: "Route::resource\(['\"]orders" --glob "routes/*.php" --output_mode content

# 3. Search controller annotations
Grep: "#\[Route\(" --glob "app/Http/Controllers/**/*.php" --output_mode content
```

#### Generic / Attribute-based Resolution

```bash
# Search all PHP files for route attributes matching the path
Grep: "#\[Route\(['\"][^'\"]*(/api/orders)" --glob "**/*.php" --output_mode content

# Search for Slim-style route definitions
Grep: "->(post|get|put|delete|patch)\(\s*['\"]/?api/orders" --glob "**/*.php" --output_mode content
```

### Step 3: Resolve Console Command

#### Symfony Command Resolution

```bash
# 1. Search AsCommand attribute
Grep: "#\[AsCommand\(['\"]app:process-payments" --glob "**/*.php" --output_mode content

# 2. Search $defaultName property
Grep: "\\\$defaultName\s*=\s*['\"]app:process-payments" --glob "**/*.php" --output_mode content

# 3. Search configure() method for setName()
Grep: "setName\(['\"]app:process-payments" --glob "**/*.php" --output_mode content

# 4. Search services.yaml for command tag
Grep: "console.command" --glob "config/services*.yaml" --output_mode content
```

#### Laravel Command Resolution

```bash
# 1. Search $signature property
Grep: "\\\$signature\s*=\s*['\"]app:process-payments" --glob "**/*.php" --output_mode content

# 2. Search $name property
Grep: "\\\$name\s*=\s*['\"]app:process-payments" --glob "**/*.php" --output_mode content

# 3. Search Kernel commands registration
Grep: "app:process-payments" --glob "app/Console/Kernel.php" --output_mode content
```

#### Generic Resolution

```bash
# Search any PHP file containing the command name as a string
Grep: "['\"]app:process-payments['\"]" --glob "**/*.php" --output_mode content
```

### Step 4: Extract Handler Details

Once the route/command definition file is found:

```bash
# Read the file containing the route/command definition
Read: matched_file

# Extract class name and namespace
Grep: "^namespace\s+" in matched_file --output_mode content
Grep: "^class\s+" in matched_file --output_mode content

# For route: extract the handler method
# - If class has __invoke → method is __invoke
# - If route attribute is on a specific method → that method
# - If route file points to Controller@method → extract method

# For command: handler method is execute() (Symfony) or handle() (Laravel)
```

### Step 5: Locate Handler File via PSR-4

If the route definition references a different handler class:

```bash
# Read composer.json for PSR-4 autoload mapping
Read: composer.json → extract autoload.psr-4 section

# Convert namespace to path
# Example: App\Api\Action\CreateOrderAction
# PSR-4: "App\\" => "src/"
# Path: src/Api/Action/CreateOrderAction.php

# Verify file exists
Glob: "src/Api/Action/CreateOrderAction.php"
```

### Step 6: Extract Middleware / Context

#### For HTTP Routes

```bash
# Symfony: find middleware (event listeners on kernel.request)
Grep: "kernel.request|kernel.controller" --glob "**/*.php" --output_mode content

# Check route-level middleware in attributes
Grep: "#\[IsGranted\(|#\[Security\(" in handler file --output_mode content

# Laravel: check middleware in route definition
Grep: "->middleware\(" in route definition context --output_mode content

# Check controller constructor middleware
Grep: "\$this->middleware\(" in handler file --output_mode content
```

#### For Console Commands

```bash
# Check if command is scheduled
# Symfony
Grep: "app:process-payments" --glob "config/scheduler*.{php,yaml}" --output_mode content
Grep: "RecurringMessage" --glob "**/*.php" --output_mode content

# Laravel
Grep: "app:process-payments" --glob "app/Console/Kernel.php" --output_mode content
Grep: "schedule\(" --glob "routes/console.php" --output_mode content
```

## Output Format

### HTTP Route Resolution

```markdown
## Resolved Entry Point

| Field | Value |
|-------|-------|
| Type | HTTP Route |
| Input | POST /api/orders |
| Handler | App\Api\Action\CreateOrderAction::__invoke |
| File | src/Api/Action/CreateOrderAction.php |
| Route definition | config/routes/api.yaml:15 |
| HTTP Method | POST |
| Path | /api/orders |
| Path params | — |
| Middleware | auth, json-body |
| Auth | #[IsGranted('ROLE_USER')] |
| Framework | Symfony 7.x |

### Handler Chain
Route definition → Middleware (auth, json) → CreateOrderAction::__invoke → CreateOrderUseCase
```

### Console Command Resolution

```markdown
## Resolved Entry Point

| Field | Value |
|-------|-------|
| Type | Console Command |
| Input | app:process-payments |
| Handler | App\Console\Command\ProcessPaymentsCommand::execute |
| File | src/Console/Command/ProcessPaymentsCommand.php |
| Command definition | #[AsCommand('app:process-payments')] |
| Arguments | --batch-size (optional, default: 100) |
| Schedule | Daily at 02:00 (config/scheduler.php) |
| Framework | Symfony 7.x |

### Execution Chain
Schedule/Manual → ProcessPaymentsCommand::execute → ProcessPaymentUseCase
```

### Resolution Failed

```markdown
## Resolution Failed

| Field | Value |
|-------|-------|
| Input | GET /api/nonexistent |
| Type | HTTP Route |
| Framework | Symfony 7.x |

### Search Results
No matching route definition found.

### Suggestions
1. Check available routes: `php bin/console debug:router | grep api`
2. Verify the route path is correct (case-sensitive)
3. The route may be defined dynamically or via imported bundle
4. Try searching with a broader path: `/acc-explain GET /api/`
```

## Multiple Matches

When multiple handlers match (e.g., versioned APIs, route overrides):

```markdown
## Resolved Entry Points (multiple matches)

### Match 1 (primary)
| Field | Value |
|-------|-------|
| Handler | App\Api\V2\CreateOrderAction |
| File | src/Api/V2/CreateOrderAction.php |
| Route | config/routes/api_v2.yaml:8 |

### Match 2
| Field | Value |
|-------|-------|
| Handler | App\Api\V1\CreateOrderAction |
| File | src/Api/V1/CreateOrderAction.php |
| Route | config/routes/api_v1.yaml:12 |

**Note:** Multiple handlers found. Using Match 1 (most recent/specific definition).
```

## Path Parameter Handling

When resolving routes with parameters:

```
Input: GET /api/orders/{id}/items
Search patterns:
  1. Exact: /api/orders/{id}/items
  2. Regex attr: /api/orders/\{[^}]+\}/items
  3. Simplified: orders.*items (fallback)
```

## Integration

This skill is used by:
- `acc-codebase-navigator` — resolves user-provided routes/commands to handler files before navigation
- `acc-explain-coordinator` — Phase 0 resolution for route/command input types
