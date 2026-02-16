---
name: acc-find-null-pointer-issues
description: Detects null pointer issues in PHP code. Finds property/method access on null, missing null checks, nullable returns without handling, optional chaining gaps.
---

# Null Pointer Detection

Analyze PHP code for null pointer dereference issues.

## Detection Patterns

### 1. Nullable Return Without Check

```php
// BUG: No null check after find
$user = $repository->find($id);
$user->getName(); // May be null

// BUG: Chained calls on nullable
$order = $this->orderRepository->findByUser($userId);
$order->getItems()->first()->getProduct(); // Multiple null risks
```

### 2. Missing Null Coalescing

```php
// BUG: Direct access to optional array key
$name = $data['user']['name']; // May not exist

// FIXED:
$name = $data['user']['name'] ?? 'default';
```

### 3. Method Calls on Nullable Type

```php
// Type hint: public function getUser(): ?User

// BUG: No null handling
$user = $service->getUser();
echo $user->getEmail(); // $user may be null

// FIXED:
$user = $service->getUser();
if ($user !== null) {
    echo $user->getEmail();
}
```

### 4. Collection First/Last on Empty

```php
// BUG: first() on potentially empty collection
$items = $repository->findByStatus('active');
$first = $items->first(); // Returns false/null if empty
$first->process(); // Crash if empty

// FIXED:
$first = $items->first();
if ($first !== null) {
    $first->process();
}
```

### 5. Optional Chaining Gaps

```php
// BUG: Inconsistent null safety
$name = $user?->getProfile()->getName(); // getProfile may return null

// FIXED:
$name = $user?->getProfile()?->getName();
```

### 6. Constructor Null Assignment

```php
// BUG: Uninitialized property access
class Order {
    private ?Customer $customer;

    public function getCustomerName(): string {
        return $this->customer->getName(); // $customer not initialized
    }
}
```

### 7. Doctrine/Eloquent Relationship Nulls

```php
// BUG: Relationship may be null
$order->getCustomer()->getAddress(); // Customer may be null

// BUG: Collection method on null relation
$user->getOrders()->filter(...); // getOrders may return null
```

## Grep Patterns

```bash
# Nullable return types
Grep: "function\s+\w+\([^)]*\)\s*:\s*\?" --glob "**/*.php"

# find() without null check
Grep: "->find\([^)]+\)\s*;" --glob "**/*.php"

# Chained calls after nullable
Grep: "\?>\w+\([^)]*\)->\w+" --glob "**/*.php"

# first()/last() usage
Grep: "->(first|last)\(\)\s*->" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| find() without null check | 🟠 Major |
| Chained calls on nullable | 🟠 Major |
| first()/last() on collection | 🟡 Minor |
| Missing null coalescing | 🟡 Minor |
| Uninitialized property | 🔴 Critical |

## Output Format

```markdown
### Null Pointer: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Nullable Return|Missing Check|Chained Access|...]

**Issue:**
Variable may be null when accessed.

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// With null check
```
```
