# Common Issues

## Common Documentation Problems in PHP Projects

### 1. Outdated API Documentation

Code changes without corresponding doc updates. Most frequent in active DDD projects
where domain model evolves rapidly.

```php
// Code was refactored from:
public function createOrder(string $customerId, array $lines): Order

// To (Value Objects introduced):
public function createOrder(CustomerId $customerId, OrderLineCollection $lines): OrderId

// But docs still show:
// $order = $service->createOrder('cust-123', [...]);
```

**Detection:**

```bash
# Find public method signatures in code
Grep: "public function " --glob "src/Application/**/*.php"

# Find code examples in docs
Grep: "```php" -A 15 --glob "docs/api/**/*.md"

# Compare method signatures — flag mismatches
```

### 2. Missing Architecture Documentation

No ARCHITECTURE.md or equivalent. Developers cannot understand bounded contexts,
layer dependencies, or integration patterns.

**Detection:**

```bash
# Check for architecture docs
Glob: ARCHITECTURE.md
Glob: docs/architecture/README.md
Glob: docs/architecture/*.md

# Check for bounded context documentation
Grep: "Bounded Context|Context Map" --glob "docs/**/*.md"

# Check for layer documentation
Grep: "Domain Layer|Application Layer|Infrastructure Layer" --glob "docs/**/*.md"
```

**Impact:** New developers spend 2-3x longer understanding the system. Architectural
decisions are lost when original team members leave.

### 3. Broken Internal Links

Documentation references files that have been moved, renamed, or deleted.

**Detection:**

```bash
# Find all relative markdown links
Grep: "\]\((?!http)[^\)]+\.md\)" --glob "**/*.md"

# Find all relative image links
Grep: "\]\((?!http)[^\)]+\.(png|jpg|svg)\)" --glob "**/*.md"

# Validate each path exists
# For each match, extract path and check with: Glob: {path}
```

**Common causes:**
- File renamed without updating references (`git mv` without doc update)
- Directory restructured (e.g., moving from `src/` to `src/Domain/`)
- Image files deleted during cleanup

### 4. Inconsistent Naming Between Code and Docs

Documentation uses different names than the actual code.

```markdown
<!-- Doc says "OrderService" -->
## OrderService

The OrderService handles order creation...

<!-- But code has -->
final readonly class CreateOrderHandler  // Not "OrderService"
```

**Detection:**

```bash
# Find class names in docs
Grep: "## [A-Z][a-zA-Z]+|`[A-Z][a-zA-Z]+`" --glob "docs/**/*.md"

# Verify each class exists
Grep: "class {ClassName}" --glob "src/**/*.php"

# Find namespace references in docs
Grep: "App\\\\[A-Za-z\\\\]+" --glob "docs/**/*.md"
# Verify each namespace exists
```

### 5. Missing Setup/Installation Instructions

README assumes reader has the environment already configured. No Docker setup,
no environment variable documentation, no database migration steps.

**Detection:**

```bash
# Check for installation section
Grep: "## Installation|## Setup|## Getting Started" --glob "README.md"

# Check for Docker instructions
Grep: "docker|Docker|docker-compose" --glob "README.md"
Glob: docker-compose.yml

# Check for environment setup
Glob: .env.example
Grep: "\.env|environment|ENV" --glob "README.md"

# Check for migration instructions
Grep: "migration|migrate|schema" --glob "README.md"
Grep: "migration|migrate|schema" --glob "docs/guides/getting-started.md"
```

### 6. No Error Handling Documentation

API consumers don't know what errors to expect. No documentation of domain
exceptions, HTTP error codes, or error response format.

**Detection:**

```bash
# Find domain exceptions
Grep: "class.*Exception" --glob "src/Domain/**/*.php"

# Check if documented
Grep: "Exception|Error|error" --glob "docs/api/**/*.md"

# Find HTTP error codes in controllers
Grep: "HTTP_[A-Z_]+|status.*[45][0-9][0-9]" --glob "src/Presentation/**/*.php"

# Check for error response documentation
Grep: "## Error|## Errors|error response|Error Response" --glob "docs/api/**/*.md"
```

### 7. Stale Code Examples

Examples use deprecated methods, old PHP syntax, or removed packages.

```php
// Doc shows PHP 7.x style:
$order = new Order();
$order->setCustomerId($customerId);  // Setter removed in DDD refactor
$order->setLines($lines);

// Current code uses factory method:
$order = Order::create(
    id: OrderId::generate(),
    customerId: new CustomerId($customerId),
    lines: $lines,
);
```

**Detection:**

```bash
# Find setter usage in docs (likely outdated in DDD project)
Grep: "->set[A-Z]" --glob "docs/**/*.md"

# Find old-style constructors without named arguments
Grep: "new [A-Z][a-zA-Z]+\([^)]*," --glob "docs/**/*.md"
# Compare with actual constructor signatures

# Find references to removed packages
Grep: "use [A-Za-z\\\\]+;" --glob "docs/**/*.md"
# Verify each namespace exists in vendor/ or src/
```

### 8. Missing PHPDoc on Public API

Public classes and methods lack documentation, making it impossible to generate
API reference docs.

**Detection:**

```bash
# Find public methods without PHPDoc
Grep: "^\s+public function " -B 1 --glob "src/**/*.php"
# Flag methods where preceding line is not */ (no PHPDoc)

# Count documented vs undocumented
Grep: "/\*\*" --glob "src/**/*.php" | wc -l
Grep: "public function " --glob "src/**/*.php" | wc -l
# Coverage = documented / total
```

### 9. Diagrams Don't Match Code

Mermaid or image diagrams show outdated architecture. Bounded contexts renamed,
layers reorganized, or integrations changed.

**Detection:**

```bash
# Find class names in diagrams
Grep: "class [A-Z]" --glob "docs/**/*.md"

# Find component names in C4 diagrams
Grep: "System\(|Container\(|Component\(" --glob "docs/**/*.md"

# Cross-reference with actual codebase
Grep: "namespace " --glob "src/**/*.php"
```

### 10. No CHANGELOG or Inconsistent Format

Version history missing, or CHANGELOG doesn't follow a standard format (Keep a Changelog).

**Detection:**

```bash
# Check CHANGELOG exists
Glob: CHANGELOG.md

# Check format compliance
Grep: "## \[" --glob "CHANGELOG.md"  # Versioned sections
Grep: "### Added|### Changed|### Fixed|### Removed" --glob "CHANGELOG.md"

# Check versions match tags
git tag --list
Grep: "## \[[0-9]" --glob "CHANGELOG.md"
```

## Issue Priority Matrix

```
             | High Impact         | Low Impact
-------------|---------------------|------------------
Quick Fix    | Broken links,       | Missing badges,
             | version mismatch,   | typos,
             | missing .env.example| formatting issues
-------------|---------------------|------------------
Hard Fix     | Missing arch docs,  | Diagram updates,
             | stale API docs,     | glossary creation,
             | no error handling   | example expansion
```

## Summary

| Issue | Detection | Impact | Fix |
|-------|-----------|--------|-----|
| Outdated API docs | Compare code vs doc signatures | High — users get errors | Update docs with current API |
| Missing architecture | Check for ARCHITECTURE.md | High — onboarding blocked | Create architecture overview |
| Broken links | Validate all relative paths | Medium — dead ends | Run markdown-link-check in CI |
| Inconsistent naming | Cross-reference class names | Medium — confusion | Standardize terms, add glossary |
| Missing setup | Check README sections | Critical — cannot start | Add complete setup guide |
| No error docs | Find undocumented exceptions | High — poor error handling | Document all error responses |
| Stale examples | Compare example syntax vs code | High — broken copy-paste | Rewrite with current API |
| Missing PHPDoc | Count documented public methods | Medium — no API reference | Add PHPDoc to public API |
| Outdated diagrams | Cross-reference diagram entities | Medium — wrong mental model | Regenerate from code |
| No CHANGELOG | Check for CHANGELOG.md format | Low — no version history | Generate from git history |
