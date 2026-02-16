---
name: acc-detect-unnecessary-loops
description: Detects unnecessary loop patterns in PHP code. Finds nested loop inefficiency, redundant iterations, in-loop operations that could be batched, loop invariant code.
---

# Unnecessary Loop Detection

Analyze PHP code for inefficient loop patterns.

## Detection Patterns

### 1. Nested Loop Inefficiency

```php
// O(n*m): Nested search
foreach ($users as $user) {
    foreach ($orders as $order) {
        if ($order->getUserId() === $user->getId()) {
            // Found order for user
        }
    }
}

// O(n): Use indexed lookup
$ordersByUser = [];
foreach ($orders as $order) {
    $ordersByUser[$order->getUserId()][] = $order;
}
foreach ($users as $user) {
    $userOrders = $ordersByUser[$user->getId()] ?? [];
}
```

### 2. Redundant Iterations

```php
// REDUNDANT: Multiple passes
$filtered = [];
foreach ($items as $item) {
    if ($item->isActive()) {
        $filtered[] = $item;
    }
}
$transformed = [];
foreach ($filtered as $item) {
    $transformed[] = $item->toArray();
}
$sorted = usort($transformed, fn($a, $b) => $a['name'] <=> $b['name']);

// BETTER: Single pass + built-in sort
$result = [];
foreach ($items as $item) {
    if ($item->isActive()) {
        $result[] = $item->toArray();
    }
}
usort($result, fn($a, $b) => $a['name'] <=> $b['name']);
```

### 3. In-Loop Operations That Could Be Batched

```php
// SLOW: Individual inserts
foreach ($users as $user) {
    $this->repository->save($user);
    $this->em->flush(); // Flush each iteration
}

// FAST: Batch insert
foreach ($users as $user) {
    $this->em->persist($user);
}
$this->em->flush(); // Single flush

// SLOW: Individual API calls
foreach ($items as $item) {
    $this->api->update($item); // HTTP call per item
}

// FAST: Batch API call
$this->api->updateBatch($items);
```

### 4. Loop Invariant Code

```php
// INEFFICIENT: Repeated computation
foreach ($items as $item) {
    $config = $this->loadConfig(); // Same result each iteration
    $now = new DateTime(); // Same time each iteration
    $taxRate = $this->getTaxRate($country); // Constant
    process($item, $config, $now, $taxRate);
}

// FIXED: Hoist invariants
$config = $this->loadConfig();
$now = new DateTime();
$taxRate = $this->getTaxRate($country);
foreach ($items as $item) {
    process($item, $config, $now, $taxRate);
}
```

### 5. Array Functions vs Loops

```php
// VERBOSE: Manual filter
$active = [];
foreach ($users as $user) {
    if ($user->isActive()) {
        $active[] = $user;
    }
}

// CLEANER: array_filter
$active = array_filter($users, fn($u) => $u->isActive());

// VERBOSE: Manual map
$names = [];
foreach ($users as $user) {
    $names[] = $user->getName();
}

// CLEANER: array_map
$names = array_map(fn($u) => $u->getName(), $users);

// VERBOSE: Manual reduce
$total = 0;
foreach ($orders as $order) {
    $total += $order->getAmount();
}

// CLEANER: array_reduce
$total = array_reduce($orders, fn($sum, $o) => $sum + $o->getAmount(), 0);
```

### 6. Early Exit Missing

```php
// INEFFICIENT: Continues after finding
foreach ($users as $user) {
    if ($user->getId() === $targetId) {
        $found = $user;
    }
}

// EFFICIENT: Break when found
foreach ($users as $user) {
    if ($user->getId() === $targetId) {
        $found = $user;
        break;
    }
}

// BETTER: Use array_filter/first or collection method
$found = $collection->first(fn($u) => $u->getId() === $targetId);
```

### 7. Counting in Loop

```php
// SLOW: strlen in loop condition
for ($i = 0; $i < strlen($string); $i++) {
    // strlen called each iteration
}

// FAST: Cache length
$len = strlen($string);
for ($i = 0; $i < $len; $i++) {
    // ...
}

// SLOW: count() in loop
for ($i = 0; $i < count($array); $i++) {
    // count called each iteration
}
```

### 8. Unnecessary array_merge

```php
// SLOW: array_merge in loop creates new array each time
$result = [];
foreach ($batches as $batch) {
    $result = array_merge($result, $batch);
}

// FAST: Spread operator
$result = array_merge(...$batches);

// FAST: Direct append
$result = [];
foreach ($batches as $batch) {
    foreach ($batch as $item) {
        $result[] = $item;
    }
}
```

## Grep Patterns

```bash
# Nested foreach
Grep: "foreach.*foreach" --glob "**/*.php"

# flush() in loop
Grep: "foreach.*->flush\(\)" --glob "**/*.php"

# strlen/count in loop condition
Grep: "for\s*\([^;]+;\s*\$\w+\s*<\s*(strlen|count)\(" --glob "**/*.php"

# array_merge in loop
Grep: "foreach.*array_merge" --glob "**/*.php"
```

## Complexity Comparison

| Pattern | Before | After |
|---------|--------|-------|
| Nested loop search | O(n*m) | O(n+m) with index |
| Multiple passes | O(3n) | O(n) single pass |
| In-loop flush | n DB round trips | 1 round trip |
| strlen in condition | O(n²) | O(n) |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Nested loop O(n²) | 🔴 Critical |
| Individual DB operations in loop | 🔴 Critical |
| Loop invariant code | 🟠 Major |
| Multiple array passes | 🟠 Major |
| strlen in condition | 🟡 Minor |
| Verbose vs array_* | 🟢 Suggestion |

## Output Format

```markdown
### Unnecessary Loop: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Current Complexity:** O(n²)
**Optimized Complexity:** O(n)

**Issue:**
[Description of the inefficient pattern]

**Code:**
```php
// Inefficient loop
```

**Optimization:**
```php
// Optimized version
```

**Improvement:**
For 1000 items: 1,000,000 ops → 2,000 ops
```
