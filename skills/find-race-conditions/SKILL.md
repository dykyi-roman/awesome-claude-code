---
name: acc-find-race-conditions
description: Detects race conditions in PHP code. Finds shared mutable state, check-then-act patterns, TOCTOU vulnerabilities, concurrent modification issues.
---

# Race Condition Detection

Analyze PHP code for concurrency issues and race conditions.

## Detection Patterns

### 1. Check-Then-Act (TOCTOU)

```php
// BUG: Time-of-check to time-of-use
if (file_exists($path)) {
    $content = file_get_contents($path); // File may be deleted
}

// BUG: Check then modify
if (!$user->hasOrder()) {
    $order = new Order();
    $user->addOrder($order); // Another request may add order
}

// BUG: Inventory check-then-act
if ($product->getStock() >= $quantity) {
    $product->decreaseStock($quantity); // Race with other orders
}
```

### 2. Shared Mutable State

```php
// BUG: Static mutable property
class Counter {
    private static int $count = 0;

    public function increment(): void {
        self::$count++; // Not atomic
    }
}

// BUG: Shared cache without locking
class Cache {
    private array $data = [];

    public function getOrSet(string $key, callable $factory): mixed {
        if (!isset($this->data[$key])) {
            $this->data[$key] = $factory(); // May compute twice
        }
        return $this->data[$key];
    }
}
```

### 3. Read-Modify-Write Without Lock

```php
// BUG: Non-atomic increment
$counter = $redis->get('counter');
$redis->set('counter', $counter + 1); // Lost update

// BUG: Balance update
$balance = $account->getBalance();
$account->setBalance($balance - $amount); // Race condition

// FIXED: Use atomic operations
$redis->incr('counter');
```

### 4. File System Race Conditions

```php
// BUG: Directory creation race
if (!is_dir($path)) {
    mkdir($path); // Another process may create it
}

// BUG: File write race
$data = json_decode(file_get_contents($file));
$data['count']++;
file_put_contents($file, json_encode($data)); // Lost update
```

### 5. Database Race Conditions

```php
// BUG: No optimistic locking
$entity = $repository->find($id);
$entity->setStatus('processed');
$entityManager->flush(); // Another process may have changed it

// BUG: Unique constraint race
if (!$repository->findByEmail($email)) {
    $user = new User($email);
    $entityManager->persist($user); // Duplicate may be created
}
```

### 6. Session Race Conditions

```php
// BUG: Session data race
$cart = $_SESSION['cart'];
$cart[] = $newItem;
$_SESSION['cart'] = $cart; // Lost update with concurrent requests
```

## Grep Patterns

```bash
# Check-then-act patterns
Grep: "if\s*\(file_exists\([^)]+\)\)\s*\{[^}]*file_get_contents" --glob "**/*.php"

# Static mutable properties
Grep: "private static\s+(?!readonly)" --glob "**/*.php"

# Read-modify-write on Redis
Grep: "->get\([^)]+\)[^;]*\+[^;]*->set" --glob "**/*.php"

# Non-atomic increment
Grep: "\+\+|\-\-|self::\$\w+\s*\+=" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Financial data race | 🔴 Critical |
| Inventory TOCTOU | 🔴 Critical |
| Unique constraint race | 🟠 Major |
| File system race | 🟠 Major |
| Cache stampede | 🟡 Minor |
| Counter race | 🟡 Minor |

## Fixes

### Use Locks

```php
// Database lock
$connection->beginTransaction();
$entity = $repository->find($id, LockMode::PESSIMISTIC_WRITE);
$entity->process();
$connection->commit();
```

### Use Atomic Operations

```php
// Redis atomic increment
$redis->incr('counter');

// Database atomic update
$connection->executeStatement(
    'UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?',
    [$quantity, $productId, $quantity]
);
```

### Use Optimistic Locking

```php
#[Version]
private int $version;

// Will throw OptimisticLockException on conflict
```

## Output Format

```markdown
### Race Condition: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [TOCTOU|Shared State|Read-Modify-Write|...]

**Issue:**
[Description of the race condition]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// Thread-safe version
```
```
