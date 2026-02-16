---
name: acc-bug-fix-knowledge
description: Bug fix knowledge base. Provides bug categories, symptoms, fix patterns, and minimal intervention principles for PHP 8.4 projects.
---

# Bug Fix Knowledge Base

Comprehensive knowledge for diagnosing and fixing bugs in PHP applications following DDD, CQRS, and Clean Architecture patterns.

## Bug Categories and Symptoms

### 1. Logic Errors
**Symptoms:**
- Incorrect output for valid input
- Wrong branch taken in conditionals
- Inverted boolean logic
- Off-by-one errors in loops
- Missing edge case handling

**Common Causes:**
- `>` instead of `>=`, `&&` instead of `||`
- Negation errors (`!$condition` vs `$condition`)
- Loop boundary mistakes (`< count` vs `<= count`)
- Missing `break` in switch statements

**Fix Pattern:**
```php
// Before: Logic error
if ($amount > $limit) { // Should be >=
    throw new LimitExceededException();
}

// After: Fixed
if ($amount >= $limit) {
    throw new LimitExceededException();
}
```

### 2. Null Pointer Issues
**Symptoms:**
- "Call to a member function on null"
- "Cannot access property on null"
- Unexpected null returns
- Missing null checks after optional operations

**Common Causes:**
- Repository returning null for non-existent entity
- Optional relationships not checked
- Nullable parameters not validated
- Method chaining on potentially null objects

**Fix Pattern:**
```php
// Before: Null pointer risk
$user = $this->userRepository->find($id);
$email = $user->getEmail(); // Crashes if user is null

// After: Safe with null check
$user = $this->userRepository->find($id);
if ($user === null) {
    throw new UserNotFoundException($id);
}
$email = $user->getEmail();

// Alternative: Null coalescing
$email = $user?->getEmail() ?? throw new UserNotFoundException($id);
```

### 3. Boundary Issues
**Symptoms:**
- Array index out of bounds
- Empty collection access
- String index errors
- Numeric overflow/underflow

**Common Causes:**
- Accessing first/last element without checking emptiness
- Loop index exceeding array size
- Integer overflow in calculations
- Missing bounds validation

**Fix Pattern:**
```php
// Before: Boundary issue
$firstItem = $items[0]; // Crashes if empty

// After: Safe boundary check
if ($items === []) {
    throw new EmptyCollectionException('items');
}
$firstItem = $items[0];

// Alternative: Using first() with default
$firstItem = $items[0] ?? throw new EmptyCollectionException('items');
```

### 4. Race Conditions
**Symptoms:**
- Intermittent failures
- Data corruption under load
- Lost updates
- Duplicate records

**Common Causes:**
- Check-then-act without locking
- Shared mutable state
- Missing database transactions
- Concurrent file access

**Fix Pattern:**
```php
// Before: Race condition
if (!$this->repository->exists($id)) {
    $this->repository->save($entity); // Another process might insert between check and save
}

// After: Atomic operation with locking
$this->lockManager->acquire("entity:$id");
try {
    if (!$this->repository->exists($id)) {
        $this->repository->save($entity);
    }
} finally {
    $this->lockManager->release("entity:$id");
}

// Alternative: Database-level uniqueness
// Use UNIQUE constraint + INSERT ... ON DUPLICATE KEY
```

### 5. Resource Leaks
**Symptoms:**
- Memory exhaustion over time
- "Too many open files"
- Database connection pool exhaustion
- Slow performance degradation

**Common Causes:**
- Unclosed file handles
- Missing database connection release
- Event listeners not removed
- Circular references preventing GC

**Fix Pattern:**
```php
// Before: Resource leak
$handle = fopen($path, 'r');
$content = fread($handle, filesize($path));
// Missing fclose()

// After: Proper resource management
$handle = fopen($path, 'r');
try {
    $content = fread($handle, filesize($path));
} finally {
    fclose($handle);
}

// Better: Use high-level functions
$content = file_get_contents($path);
```

### 6. Exception Handling Issues
**Symptoms:**
- Silent failures
- Generic error messages
- Lost exception context
- Swallowed exceptions

**Common Causes:**
- Empty catch blocks
- Catching too broad exception types
- Not re-throwing after logging
- Missing exception chaining

**Fix Pattern:**
```php
// Before: Swallowed exception
try {
    $this->service->process($data);
} catch (Exception $e) {
    // Silent failure - bug hidden
}

// After: Proper exception handling
try {
    $this->service->process($data);
} catch (ValidationException $e) {
    throw new ProcessingFailedException(
        "Failed to process data: {$e->getMessage()}",
        previous: $e
    );
}
```

### 7. Type Issues
**Symptoms:**
- "Type error: Argument must be of type X, Y given"
- Unexpected type coercion
- String/int confusion
- Array/object mismatch

**Common Causes:**
- Missing strict_types declaration
- Implicit type casting
- Mixed types from external sources
- Legacy code without type hints

**Fix Pattern:**
```php
// Before: Type issue
function calculate($amount) { // No type hint
    return $amount * 1.1; // Fails if string passed
}

// After: Strict typing
declare(strict_types=1);

function calculate(float $amount): float {
    return $amount * 1.1;
}
```

### 8. SQL Injection
**Symptoms:**
- Security vulnerabilities
- Unexpected query results
- Data corruption
- Authentication bypass

**Common Causes:**
- String concatenation in queries
- Missing parameter binding
- Unvalidated user input in queries
- Dynamic table/column names

**Fix Pattern:**
```php
// Before: SQL injection vulnerability
$query = "SELECT * FROM users WHERE email = '$email'";

// After: Parameterized query
$query = "SELECT * FROM users WHERE email = :email";
$stmt = $pdo->prepare($query);
$stmt->execute(['email' => $email]);
```

### 9. Infinite Loops
**Symptoms:**
- Application hangs
- 100% CPU usage
- Request timeouts
- Memory exhaustion

**Common Causes:**
- Missing or unreachable exit condition
- Iterator not advancing
- Recursive call without base case
- Circular dependencies in processing

**Fix Pattern:**
```php
// Before: Potential infinite loop
while ($item = $queue->pop()) {
    $this->process($item);
    // If process() adds items back to queue, infinite loop
}

// After: Safe with limit
$maxIterations = 10000;
$iterations = 0;
while ($item = $queue->pop()) {
    if (++$iterations > $maxIterations) {
        throw new MaxIterationsExceededException($maxIterations);
    }
    $this->process($item);
}
```

## Minimal Intervention Principles

### 1. Single Responsibility Fix
- Fix ONLY the bug, nothing else
- No refactoring while fixing
- No "while I'm here" improvements
- Keep the diff minimal

### 2. Preserve Behavior
- Existing tests must pass
- API contracts must not change
- Side effects must be preserved (if intentional)
- Error messages format should match

### 3. Backward Compatibility
- Public method signatures unchanged
- Return types unchanged
- Exception types unchanged
- Event payloads unchanged

### 4. Test First
- Write failing test that reproduces bug
- Fix should make test pass
- No fix without reproduction test

## Fix Validation Checklist

Before applying a fix, verify:

1. **Reproduction Test Exists**
   - [ ] Test fails without fix
   - [ ] Test passes with fix
   - [ ] Test covers edge cases

2. **Minimal Change**
   - [ ] Only affected code changed
   - [ ] No unrelated refactoring
   - [ ] No formatting changes

3. **No Regressions**
   - [ ] All existing tests pass
   - [ ] No new warnings
   - [ ] Performance not degraded

4. **Code Quality**
   - [ ] No new code smells
   - [ ] SOLID principles respected
   - [ ] DDD patterns maintained

5. **Documentation**
   - [ ] PHPDoc updated if needed
   - [ ] CHANGELOG entry added
   - [ ] Issue linked in commit

## DDD-Specific Bug Patterns

### Domain Layer Bugs
- Value Object validation bypass
- Entity invariant violation
- Aggregate boundary crossing
- Domain Event lost

### Application Layer Bugs
- Use Case not transactional
- Command/Query mixing
- Missing authorization check
- Event handler not idempotent

### Infrastructure Layer Bugs
- Repository returning detached entity
- Cache invalidation missing
- Message not acknowledged
- Connection not released

## Quick Reference: Fix by Error Message

| Error Message | Likely Bug | Quick Fix |
|--------------|------------|-----------|
| "Call to member function on null" | Null pointer | Add null check |
| "Undefined array key" | Boundary issue | Check array_key_exists |
| "Type error: Argument X" | Type issue | Add type validation |
| "Maximum execution time" | Infinite loop | Add iteration limit |
| "Allowed memory exhausted" | Resource leak | Close resources in finally |
| "Integrity constraint violation" | Race condition | Add locking/transaction |
| "Cannot modify readonly property" | Immutability violation | Create new instance |
