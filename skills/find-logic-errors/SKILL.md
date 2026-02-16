---
name: acc-find-logic-errors
description: Detects logic errors in PHP code. Finds incorrect conditions, wrong operators, missing switch cases, inverted logic, short-circuit evaluation issues.
---

# Logic Error Detection

Analyze PHP code for logic errors that cause incorrect behavior.

## Detection Patterns

### 1. Incorrect Comparison Operators

```php
// BUG: Assignment instead of comparison
if ($status = 'active') { } // Should be ===

// BUG: Wrong comparison type
if ($count == '0') { } // '0' is truthy in string comparison

// BUG: Yoda condition error
if ('active' = $status) { } // Assignment error
```

### 2. Inverted Logic

```php
// BUG: Double negation confusion
if (!$user->isNotActive()) { } // Hard to reason about

// BUG: Wrong negation placement
if (!$a && $b) { } // vs if (!($a && $b))

// BUG: DeMorgan's law violation
if (!$a || !$b) { } // When meaning !($a && $b)
```

### 3. Missing Switch/Match Cases

```php
// BUG: Missing enum case
match ($status) {
    Status::Active => 'active',
    Status::Inactive => 'inactive',
    // Missing: Status::Pending, Status::Deleted
};

// BUG: Missing default
switch ($type) {
    case 'A': return 1;
    case 'B': return 2;
    // No default - undefined behavior for other values
}
```

### 4. Short-Circuit Evaluation Issues

```php
// BUG: Side effect in short-circuit
if ($valid && $this->save()) { } // save() not called if !$valid

// BUG: Order matters
if ($obj->method() && $obj !== null) { } // Null check too late
```

### 5. Off-by-One in Comparisons

```php
// BUG: Fence post error
if ($index < count($array)) { } // vs <=

// BUG: Wrong boundary
for ($i = 0; $i <= $length; $i++) { } // Off by one
```

### 6. Boolean Expression Errors

```php
// BUG: Always true/false
if ($age > 0 || $age <= 0) { } // Always true

// BUG: Unreachable condition
if ($x > 10 && $x < 5) { } // Always false

// BUG: Redundant condition
if ($status === 'active' && $status !== 'inactive') { } // Second part redundant
```

### 7. Return Value Ignorance

```php
// BUG: Ignoring important return
array_push($items, $new); // Returns count, not array
$string->trim(); // String is immutable, returns new string
```

## Grep Patterns

```bash
# Assignment in condition
Grep: "if\s*\([^=]*[^!=<>]=[^=][^)]*\)" --glob "**/*.php"

# Double negation
Grep: "!\$\w+->isNot|!!\$" --glob "**/*.php"

# Empty switch without default
Grep: "switch\s*\([^)]+\)\s*\{[^}]*\}" --glob "**/*.php"
```

## Output Format

```markdown
### Logic Error: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Incorrect Operator|Inverted Logic|Missing Case|...]

**Issue:**
[Description]

**Code:**
```php
// Current code
```

**Fix:**
```php
// Corrected code
```
```
