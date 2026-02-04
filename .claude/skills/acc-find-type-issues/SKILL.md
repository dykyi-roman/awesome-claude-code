---
name: acc-find-type-issues
description: Detects type issues in PHP code. Finds implicit type coercion, mixed types in comparisons, unsafe casting, type mismatches in returns.
---

# Type Issue Detection

Analyze PHP code for type safety issues.

## Detection Patterns

### 1. Implicit Type Coercion

```php
// BUG: String to int coercion
$count = '10abc'; // PHP converts to 10
$total = $count + 5; // 15, not error

// BUG: Array comparison
$a = [1, 2, 3];
$b = '1,2,3';
if ($a == $b) { } // Unexpected comparison

// BUG: Boolean context
if ($string) { } // '0' is falsy, but non-empty
```

### 2. Loose Comparison Issues

```php
// BUG: == instead of ===
if ($status == 0) { } // 'active' == 0 is true!

// BUG: in_array without strict
if (in_array($value, $array)) { } // Type coercion
// FIXED: in_array($value, $array, true)

// BUG: array_search
$key = array_search($value, $array); // Returns false or key
if ($key) { } // Key 0 is falsy!
```

### 3. Unsafe Type Casting

```php
// BUG: Casting truncates
$float = 10.9;
$int = (int) $float; // 10, not 11

// BUG: String to array casting
$array = (array) $object; // May include private properties

// BUG: Object casting
$stdClass = (object) $array; // Loses type information
```

### 4. Mixed Type Parameters

```php
// BUG: Function accepts anything
function process($data) { // No type hint
    return $data['key']; // Assumes array
}

// BUG: Union type issues
function handle(string|int $id): void {
    echo strlen($id); // Fails if int
}
```

### 5. Return Type Mismatches

```php
// BUG: Inconsistent return types
function getValue(): int {
    if ($condition) {
        return '42'; // String, not int
    }
    return 0;
}

// BUG: Nullable inconsistency
function find(): User { // Not nullable
    if (!$found) {
        return null; // Type error
    }
}
```

### 6. Array Type Issues

```php
// BUG: Assuming array structure
/** @param array $data */
function process(array $data): void {
    foreach ($data['items'] as $item) { // 'items' may not exist
        echo $item['name']; // 'name' may not exist
    }
}

// BUG: Mixed array types
$mixed = [1, 'two', new User()]; // Hard to type
```

### 7. Numeric String Issues

```php
// BUG: Numeric string comparison
$a = '10';
$b = '9';
if ($a > $b) { } // String comparison: '1' < '9', so false!

// FIXED:
if ((int) $a > (int) $b) { }
```

### 8. JSON Type Issues

```php
// BUG: Assuming JSON structure
$data = json_decode($json, true);
$name = $data['user']['name']; // May not exist

// BUG: JSON encoding failures
$result = json_encode($data); // May return false
```

### 9. DateTime Type Issues

```php
// BUG: String date comparison
if ($date > '2024-01-01') { } // String comparison

// BUG: DateTime vs DateTimeImmutable
function setDate(DateTime $date): void { }
$immutable = new DateTimeImmutable();
$this->setDate($immutable); // Type error
```

## Grep Patterns

```bash
# Loose comparison with 0
Grep: "==\s*0[^.]|0\s*==" --glob "**/*.php"

# in_array without strict
Grep: "in_array\([^,]+,[^,]+\)" --glob "**/*.php"

# Casting with (int) or (string)
Grep: "\(int\)\s*\$|\(string\)\s*\$|\(array\)\s*\$" --glob "**/*.php"

# Mixed parameter types
Grep: "function\s+\w+\(\$\w+[,)]" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Loose comparison with sensitive data | 🔴 Critical |
| Return type mismatch | 🟠 Major |
| Missing strict in_array | 🟠 Major |
| Untyped parameters | 🟡 Minor |
| Implicit coercion | 🟡 Minor |

## Best Practices

### Use Strict Types

```php
declare(strict_types=1);
```

### Use Strict Comparison

```php
if ($status === 0) { }
if (in_array($value, $array, true)) { }
```

### Type Hints Everywhere

```php
function process(array $items): int
{
    return count($items);
}
```

### Use instanceof

```php
if ($object instanceof User) {
    $object->getName();
}
```

## Output Format

```markdown
### Type Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Coercion|Loose Comparison|Unsafe Cast|...]

**Issue:**
[Description of the type safety problem]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// Type-safe version
```
```
