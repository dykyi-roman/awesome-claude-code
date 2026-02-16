---
name: acc-check-doc-examples
description: Verifies code examples in documentation. Checks that class names, method signatures, namespaces, and imports match actual codebase. Detects outdated and misleading examples.
---

# Documentation Code Examples Verification

Analyze documentation for code examples that don't match the actual codebase.

## Detection Patterns

### 1. Incorrect Class Name in Example

```markdown
<!-- DOC says: -->
```php
use App\Service\OrderProcessor;
$processor = new OrderProcessor();
```
<!-- But actual class is App\Application\Order\ProcessOrderUseCase -->
```

### 2. Wrong Method Signature

```markdown
<!-- DOC says: -->
```php
$user = $repository->findByEmail($email);
```
<!-- But actual method signature is: -->
```php
public function findByEmail(Email $email): ?User  // Uses Email VO, not string
```

### 3. Outdated Namespace

```markdown
<!-- DOC says: -->
```php
use App\Models\User;  // Laravel-style
```
<!-- But project uses DDD structure: -->
```php
use App\UserManagement\Domain\Entity\User;
```

### 4. Missing Required Parameters

```markdown
<!-- DOC says: -->
```php
$order = Order::create($userId, $items);
```
<!-- But actual method requires: -->
```php
Order::create(UserId $userId, ItemCollection $items, Currency $currency, Address $shippingAddress)
```

### 5. Deprecated API in Examples

```markdown
<!-- DOC says: -->
```php
$service->process($data);  // process() was renamed to execute()
```
<!-- Method was renamed but docs not updated -->

## Verification Process

### Step 1: Extract Code Blocks from Docs

```bash
# Find PHP code blocks in markdown
Grep: "```php" --glob "**/*.md" -A 20

# Find inline code references
Grep: "`[A-Z][a-zA-Z]+::[a-z]" --glob "**/*.md"
Grep: "`\\$[a-z]+->|new [A-Z]" --glob "**/*.md"
```

### Step 2: Verify Class References

```bash
# For each class mentioned in docs, verify it exists
# Example: doc mentions "OrderProcessor"
Grep: "class OrderProcessor" --glob "**/*.php"

# Verify namespace matches
Grep: "namespace.*Order" --glob "**/*.php"
```

### Step 3: Verify Method Signatures

```bash
# For each method call in doc examples
# Example: doc mentions "$repo->findByEmail($email)"
Grep: "function findByEmail" --glob "**/*.php"
# Compare parameter types and count
```

### Step 4: Check Import Paths

```bash
# For each use statement in doc examples
# Example: "use App\Service\OrderProcessor"
Glob: **/Service/OrderProcessor.php
# If not found, search for actual location
Grep: "class OrderProcessor" --glob "**/*.php"
```

### Step 5: Verify Constructor Parameters

```bash
# For each "new ClassName(...)" in docs
# Verify constructor matches
Grep: "class OrderProcessor" --glob "**/*.php" -A 20
# Check __construct parameters
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Non-existent class in install/quickstart | 🔴 Critical |
| Wrong method signature in API docs | 🔴 Critical |
| Outdated namespace in examples | 🟠 Major |
| Missing required parameters | 🟠 Major |
| Deprecated method in examples | 🟡 Minor |
| Style difference (not functional) | 🟡 Minor |

## Output Format

```markdown
### Code Example Mismatch: [Description]

**Severity:** 🔴/🟠/🟡
**Documentation:** `file.md:line`
**Code Reference:** `src/path/File.php:line`

**In Documentation:**
```php
// What the doc says
```

**In Actual Code:**
```php
// What the code actually is
```

**Fix:**
Update documentation to match current code.
```

## Summary Report Format

```markdown
## Code Examples Verification

| Metric | Count |
|--------|-------|
| Code blocks checked | X |
| Valid examples | X |
| Class name mismatches | X |
| Method signature mismatches | X |
| Namespace mismatches | X |
| Deprecated API usage | X |

### Mismatched Examples

| Doc File | Line | Reference | Issue |
|----------|------|-----------|-------|
| `README.md` | 45 | `OrderProcessor` | Class not found |
| `docs/api.md` | 78 | `findByEmail()` | Wrong parameters |
```
