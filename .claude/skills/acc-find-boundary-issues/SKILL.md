---
name: acc-find-boundary-issues
description: Detects boundary issues in PHP code. Finds array index out of bounds, empty collection access, off-by-one errors, integer overflow, string length issues.
---

# Boundary Issue Detection

Analyze PHP code for boundary and range violations.

## Detection Patterns

### 1. Array Index Out of Bounds

```php
// BUG: No bounds check
$items = [1, 2, 3];
$last = $items[count($items)]; // Off by one, should be count - 1

// BUG: Hardcoded index
$third = $data[2]; // May not have 3 elements

// BUG: Negative index
$item = $array[$index]; // $index could be negative
```

### 2. Empty Collection Access

```php
// BUG: first() on empty
$users = $repository->findBy(['status' => 'vip']);
$topUser = $users[0]; // May be empty

// BUG: array_pop on empty
$items = [];
$last = array_pop($items); // Returns null

// BUG: reset() on empty
$first = reset($emptyArray); // Returns false
```

### 3. Off-by-One Errors

```php
// BUG: Loop boundary
for ($i = 0; $i <= count($items); $i++) { // Should be <
    process($items[$i]); // Last iteration fails
}

// BUG: Substring
$sub = substr($string, 0, strlen($string) + 1); // Off by one

// BUG: Slice
$slice = array_slice($array, 0, count($array) + 1);
```

### 4. Integer Overflow/Underflow

```php
// BUG: No overflow check
$total = $price * $quantity; // May overflow

// BUG: Negative result
$remaining = $stock - $ordered; // May go negative

// BUG: Division truncation
$average = $total / $count; // Integer division loses precision
```

### 5. String Length Issues

```php
// BUG: Empty string access
$first = $string[0]; // Undefined if empty

// BUG: Multibyte issues
$length = strlen($utf8String); // Wrong for multibyte
$char = $string[5]; // May split multibyte char

// BUG: No length check
$sub = substr($name, 0, 10); // May be shorter than 10
```

### 6. Range Validation

```php
// BUG: Unchecked range
$page = $request->get('page'); // Could be 0, negative, or huge
$items = $repository->findPage($page); // Invalid page

// BUG: Missing min/max
$age = (int) $input; // Could be negative or 1000
```

### 7. Date/Time Boundaries

```php
// BUG: Invalid month/day
$date = new DateTime("2024-13-45"); // Invalid date

// BUG: Leap year
$date = new DateTime("2023-02-29"); // Not a leap year
```

## Grep Patterns

```bash
# Direct array index access
Grep: "\$\w+\[\d+\]" --glob "**/*.php"

# count() in loop condition
Grep: "for\s*\([^;]+;\s*\$\w+\s*<=\s*count" --glob "**/*.php"

# Array access after find
Grep: "findBy[^;]+;\s*\n\s*\$\w+\[0\]" --glob "**/*.php"

# Hardcoded string index
Grep: '\$\w+\["\w+"\]\[\d+\]' --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Unchecked array index | 🟠 Major |
| Off-by-one in loop | 🟠 Major |
| Empty collection access | 🟠 Major |
| Integer overflow | 🟡 Minor |
| Multibyte string issue | 🟡 Minor |

## Output Format

```markdown
### Boundary Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Array Bounds|Off-by-One|Empty Access|Overflow|...]

**Issue:**
[Description of the boundary violation]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// With bounds check
```
```
