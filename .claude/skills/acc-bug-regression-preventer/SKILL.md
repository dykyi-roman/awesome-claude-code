---
name: acc-bug-regression-preventer
description: Regression prevention checklist for bug fixes. Ensures API compatibility, behavior preservation, and no unintended side effects.
---

# Bug Regression Preventer

Systematic checklist to ensure bug fixes don't introduce new problems.

## Pre-Fix Checklist

### 1. Reproduction Verification
- [ ] Bug can be consistently reproduced
- [ ] Reproduction steps documented
- [ ] Environment conditions noted
- [ ] Expected vs actual behavior clear

### 2. Test Coverage Check
- [ ] Existing tests identified
- [ ] Missing test cases noted
- [ ] Flaky tests identified
- [ ] Performance benchmarks available (if relevant)

### 3. Impact Assessment
- [ ] Callers identified
- [ ] Dependents mapped
- [ ] Events/messages reviewed
- [ ] API contracts reviewed

## Fix Validation Checklist

### API Compatibility

#### Method Signature
```php
// BEFORE
public function process(Order $order): OrderResult

// AFTER - Must maintain compatibility
public function process(Order $order): OrderResult  // ✓ Same signature
public function process(Order $order): Result       // ✗ Return type changed
public function process(Order $order, bool $flag): OrderResult // ✗ New required param
public function process(Order $order, bool $flag = false): OrderResult // ✓ Optional param OK
```

**Checklist:**
- [ ] Return type unchanged
- [ ] Parameter types unchanged
- [ ] Parameter order unchanged
- [ ] No new required parameters
- [ ] No removed parameters

#### Exception Contract
```php
// BEFORE - throws ValidationException
public function validate(Data $data): void

// AFTER - Must throw same or subtype
public function validate(Data $data): void  // throws ValidationException ✓
public function validate(Data $data): void  // throws DataValidationException extends ValidationException ✓
public function validate(Data $data): void  // throws RuntimeException ✗ Different hierarchy
```

**Checklist:**
- [ ] Same exception types thrown
- [ ] New exceptions are subtypes of existing
- [ ] Exception messages format preserved (if parsed downstream)
- [ ] Exception codes unchanged (if used)

### Behavior Preservation

#### Return Value Semantics
```php
// BEFORE
public function findUser(UserId $id): ?User
// Returns null for non-existent user

// AFTER - Preserve null semantics
public function findUser(UserId $id): ?User
// Must still return null for non-existent user
// NOT throw NotFoundException (behavior change)
```

**Checklist:**
- [ ] Null return preserved (if applicable)
- [ ] Empty collection return preserved (if applicable)
- [ ] Default values unchanged
- [ ] Error conditions unchanged

#### Side Effects
```php
// BEFORE - Has side effects
public function completeOrder(Order $order): void
{
    $order->complete();                    // 1. State change
    $this->repository->save($order);       // 2. Database write
    $this->events->publish($event);        // 3. Event published
}

// AFTER - Must preserve all side effects
// Unless the bug IS one of these side effects
```

**Checklist:**
- [ ] State changes preserved
- [ ] Database writes preserved
- [ ] Events still published
- [ ] Messages still sent
- [ ] Logs still written
- [ ] Metrics still recorded

### Data Integrity

#### Database Schema
- [ ] No schema changes required
- [ ] Existing data remains valid
- [ ] Indexes still effective
- [ ] Constraints not violated

#### Data Format
```php
// BEFORE - stored as "2024-01-15"
// AFTER - must stay "2024-01-15"
// NOT "2024-01-15T00:00:00Z" (format change)
```

**Checklist:**
- [ ] Serialization format unchanged
- [ ] JSON structure unchanged
- [ ] Date/time formats unchanged
- [ ] Numeric precision unchanged

### Performance

#### Query Patterns
- [ ] No new N+1 queries
- [ ] No removed indexes usage
- [ ] No added full table scans
- [ ] Transaction scope unchanged

#### Resource Usage
- [ ] Memory usage not increased significantly
- [ ] CPU usage not increased significantly
- [ ] Network calls not increased
- [ ] File I/O not increased

## Test Requirements

### Mandatory Tests

#### 1. Reproduction Test
```php
/**
 * This test reproduces the original bug.
 * It MUST fail before the fix and pass after.
 */
#[Test]
public function testBugReproduction(): void
{
    // Arrange: Set up conditions that trigger the bug
    $order = OrderBuilder::create()
        ->withItem(null) // The bug trigger
        ->build();

    // Act & Assert: Verify bug is fixed
    $result = $this->service->calculateTotal($order);

    // Before fix: throws NullPointerException
    // After fix: returns Money::zero()
    $this->assertEquals(Money::zero('USD'), $result);
}
```

#### 2. Edge Case Tests
```php
#[Test]
public function testEdgeCases(): void
{
    // Test boundary conditions around the fix
    $this->assertEquals($expected, $this->service->process($emptyInput));
    $this->assertEquals($expected, $this->service->process($maxInput));
    $this->assertEquals($expected, $this->service->process($nullableInput));
}
```

#### 3. Regression Tests
```php
#[Test]
public function testExistingBehaviorPreserved(): void
{
    // Test that normal cases still work
    $normalOrder = OrderBuilder::create()
        ->withItem($validItem)
        ->build();

    $result = $this->service->calculateTotal($normalOrder);

    $this->assertEquals($expectedTotal, $result);
}
```

### Test Coverage Matrix

| Scenario | Before Fix | After Fix | Test Required |
|----------|------------|-----------|---------------|
| Bug trigger case | Fails/crashes | Works correctly | ✓ Reproduction |
| Normal case | Works | Must still work | ✓ Regression |
| Edge cases | May vary | Defined behavior | ✓ Edge case |
| Related features | Work | Must still work | ✓ Integration |

## Common Regression Patterns

### 1. Over-Fixing
```php
// Bug: Null pointer when item is null
// WRONG: Remove null items entirely (behavior change)
$items = array_filter($items, fn($i) => $i !== null);

// CORRECT: Handle null gracefully
foreach ($items as $item) {
    if ($item === null) {
        continue; // Skip null, preserve others
    }
    // ... process item
}
```

### 2. Breaking Callers
```php
// Bug: Method should return early for invalid state
// WRONG: Change return type
public function process(): void // Was: ?Result

// CORRECT: Return null for invalid state (preserve contract)
public function process(): ?Result
{
    if (!$this->isValid()) {
        return null;
    }
    // ...
}
```

### 3. Hiding Errors
```php
// Bug: Exception crashes application
// WRONG: Swallow exception
try {
    $this->service->process($data);
} catch (Exception $e) {
    // Silent failure - bug hidden
}

// CORRECT: Handle specific exception appropriately
try {
    $this->service->process($data);
} catch (ValidationException $e) {
    return Result::invalid($e->getErrors());
}
```

### 4. Performance Regression
```php
// Bug: Missing validation
// WRONG: Add validation that queries database in loop
foreach ($items as $item) {
    if (!$this->repository->exists($item->getId())) { // N+1 query!
        throw new NotFoundException();
    }
}

// CORRECT: Batch validation
$ids = array_map(fn($i) => $i->getId(), $items);
$existing = $this->repository->findByIds($ids);
if (count($existing) !== count($items)) {
    throw new NotFoundException();
}
```

## Post-Fix Verification

### Manual Testing
- [ ] Bug no longer reproducible manually
- [ ] Normal workflows still work
- [ ] Edge cases handled correctly
- [ ] Error messages appropriate

### Automated Testing
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] No new test failures

### Code Review Points
- [ ] Fix is minimal (only affected code changed)
- [ ] No unrelated changes
- [ ] No commented-out code
- [ ] No debug statements left
- [ ] Proper exception handling
- [ ] No new code smells

### Documentation
- [ ] PHPDoc updated if public API affected
- [ ] CHANGELOG entry added
- [ ] Issue linked in commit
- [ ] Breaking changes documented (if any)

## Rollback Plan

### Before Deployment
1. Tag current version: `git tag pre-fix-{issue-id}`
2. Document rollback command: `git revert {commit-hash}`
3. Identify monitoring dashboards
4. Set alert thresholds

### Monitoring After Deployment
- [ ] Error rates normal
- [ ] Latency normal
- [ ] Resource usage normal
- [ ] No new exception types
- [ ] Business metrics stable

### Rollback Triggers
- Error rate increase > 5%
- Latency increase > 20%
- New critical errors appearing
- Business metric anomaly

## Quick Checklist Summary

```markdown
## Pre-Fix
- [ ] Bug reproduced
- [ ] Impact assessed
- [ ] Existing tests identified

## Fix Applied
- [ ] API compatible
- [ ] Behavior preserved
- [ ] Side effects intact
- [ ] Data integrity maintained

## Tests Added
- [ ] Reproduction test
- [ ] Edge case tests
- [ ] Regression tests

## Post-Fix
- [ ] All tests pass
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Monitoring ready
```
