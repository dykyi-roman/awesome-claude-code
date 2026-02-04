---
name: acc-check-comments
description: Analyzes PHP code for comment quality issues. Detects missing PHPDoc, outdated comments, commented-out code, opportunities for self-documenting code.
---

# Comment Quality Check

Analyze PHP code for documentation and comment issues.

## Detection Patterns

### 1. Missing PHPDoc

```php
// BAD: No documentation on public method
public function process(array $items, bool $force = false): Result
{
}

// GOOD: Documented public method
/**
 * Process items with optional force flag.
 *
 * @param array<Item> $items Items to process
 * @param bool $force Force processing even if already processed
 * @return Result Processing result with status and errors
 *
 * @throws ProcessingException When processing fails
 */
public function process(array $items, bool $force = false): Result
{
}
```

### 2. Outdated Comments

```php
// BAD: Comment doesn't match code
// Calculates the discount percentage
public function calculateTax(Money $amount): Money
{
    return $amount->multiply(0.21);
}

// BAD: TODO that's been done or is stale
// TODO: Add validation (added 3 years ago)
$this->validate($data);

// BAD: Incorrect parameter documentation
/**
 * @param string $userId The user ID  // Actually int
 */
public function findUser(int $userId): User {}
```

### 3. Commented-Out Code

```php
// BAD: Dead code cluttering the file
public function process(Order $order): void
{
    // $this->legacyProcessor->process($order);
    // if ($order->needsSpecialHandling()) {
    //     $this->specialHandler->handle($order);
    // }

    $this->newProcessor->process($order);
}

// Remove commented code - use version control instead
public function process(Order $order): void
{
    $this->newProcessor->process($order);
}
```

### 4. Obvious Comments

```php
// BAD: Comments stating the obvious
// Get the user
$user = $this->getUser();

// Increment counter
$counter++;

// Loop through items
foreach ($items as $item) {}

// GOOD: Comments explaining WHY
// Fetch fresh user to ensure permissions are current
$user = $this->getUser();
```

### 5. Self-Documenting Code Opportunities

```php
// BAD: Comment needed due to unclear code
// Check if user can access premium features
if ($user->level >= 3 && $user->subscription !== null && $user->subscription->isActive()) {}

// GOOD: Self-documenting
if ($user->canAccessPremiumFeatures()) {}

// BAD: Magic number with comment
// 86400 seconds in a day
$expiry = time() + 86400;

// GOOD: Named constant
$expiry = time() + self::SECONDS_PER_DAY;
```

### 6. Missing Exception Documentation

```php
// BAD: Throws not documented
public function divide(int $a, int $b): float
{
    if ($b === 0) {
        throw new DivisionByZeroException();
    }
    return $a / $b;
}

// GOOD: Throws documented
/**
 * @throws DivisionByZeroException When divisor is zero
 */
public function divide(int $a, int $b): float {}
```

### 7. Noise Comments

```php
// BAD: File header noise
/***********************************
 * UserService.php
 * Created: 2024-01-01
 * Author: John Doe
 * Last Modified: 2024-06-15
 ***********************************/

// BAD: Section dividers
//////////////////////////////////
// GETTERS AND SETTERS
//////////////////////////////////

// BAD: Closing brace comments
} // end if
} // end foreach
} // end class
```

### 8. Inline Comment Placement

```php
// BAD: Comment on same line as code
$total = $price * $quantity; // Calculate total

// GOOD: Comment on line before
// Calculate order total including quantity discount
$total = $this->calculateTotal($price, $quantity);
```

## PHPDoc Best Practices

### Required Documentation

```php
/**
 * Classes: Brief description of purpose
 */
final class OrderProcessor
{
    /**
     * Public methods: What it does, params, returns, throws
     */
    public function process(Order $order): Result {}

    /**
     * Complex private methods: When non-obvious
     */
    private function calculateComplexDiscount(): Money {}
}
```

### Type Annotations

```php
/**
 * @param array<string, mixed> $config Configuration options
 * @param list<int> $ids List of integer IDs
 * @param Collection<int, User> $users User collection
 * @return array{success: bool, errors: list<string>}
 */
```

### When NOT to Comment

- Getters and setters (self-explanatory)
- Simple private methods
- Code that is self-documenting
- Obvious logic

## Grep Patterns

```bash
# Commented out code
Grep: "^\s*//\s*\\\$|^\s*//\s*if\s*\(|^\s*//\s*foreach" --glob "**/*.php"

# TODO/FIXME
Grep: "TODO|FIXME|HACK|XXX" --glob "**/*.php"

# Missing PHPDoc on public method
Grep: "^\s*public\s+function" --glob "**/*.php"
# Compare with lines having /** before them

# Old-style type hints in comments
Grep: "@param\s+\w+\s+\\\$\w+.*\bint\b|\bstring\b" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Outdated/misleading comments | 🟠 Major |
| Commented-out code | 🟡 Minor |
| Missing PHPDoc on public API | 🟡 Minor |
| Obvious comments | 🟢 Suggestion |
| Missing @throws | 🟢 Suggestion |

## Output Format

```markdown
### Comment Issue: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`
**Type:** [Missing PHPDoc|Outdated|Commented Code|...]

**Issue:**
[Description of the comment problem]

**Current:**
```php
// Calculate discount
public function calculateTax(): Money {}
```

**Suggested:**
```php
/**
 * Calculate applicable tax for the order.
 *
 * @return Money Tax amount in order currency
 */
public function calculateTax(): Money {}
```
```
