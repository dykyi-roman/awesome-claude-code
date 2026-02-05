---
name: acc-generate-bug-fix
description: Generates minimal, safe bug fixes for PHP 8.5. Provides fix templates for each bug category with DDD/Clean Architecture patterns.
---

# Bug Fix Generator

Templates and patterns for generating minimal, safe bug fixes.

## Fix Generation Principles

### 1. Minimal Change
- Fix only what's broken
- No refactoring
- No "improvements"
- No formatting changes

### 2. Safe Change
- Preserve existing behavior
- Maintain API contracts
- Keep backward compatibility
- Add, don't remove

### 3. Tested Change
- Reproduction test first
- Fix makes test pass
- Existing tests still pass

## Fix Templates by Category

| Category | Patterns | See |
|----------|----------|-----|
| **Null Pointer** | Guard clause, Null object, Optional return | [templates.md](references/templates.md#1-null-pointer-fix) |
| **Logic Error** | Condition correction, Boolean inversion, Missing case | [templates.md](references/templates.md#2-logic-error-fix) |
| **Boundary** | Empty check, Index bounds, Range validation | [templates.md](references/templates.md#3-boundary-fix) |
| **Race Condition** | Database locking, Optimistic locking, Atomic operation | [templates.md](references/templates.md#4-race-condition-fix) |
| **Resource Leak** | Try-finally, Higher-level API, Pool return | [templates.md](references/templates.md#5-resource-leak-fix) |
| **Exception** | Specific catch, Exception chaining, Proper re-throw | [templates.md](references/templates.md#6-exception-handling-fix) |
| **Type Safety** | Strict types, Type validation, Boundary coercion | [templates.md](references/templates.md#7-type-safety-fix) |
| **SQL Injection** | Prepared statement, Query builder | [templates.md](references/templates.md#8-sql-injection-fix) |
| **Infinite Loop** | Iteration limit, Visited tracking, Depth limit | [templates.md](references/templates.md#9-infinite-loop-fix) |

## Quick Reference

### Null Pointer → Guard Clause
```php
$entity = $this->repository->find($id);
if ($entity === null) {
    throw new EntityNotFoundException($id);
}
```

### Logic Error → Condition Fix
```php
// Wrong: if ($a > $b)
// Fixed: if ($a >= $b)
```

### Boundary → Empty Check
```php
if ($items === []) {
    throw new EmptyCollectionException();
}
```

### Race Condition → Locking
```php
$this->em->beginTransaction();
try {
    $entity = $this->repository->findWithLock($id);
    // ... modify ...
    $this->em->commit();
} catch (\Throwable $e) {
    $this->em->rollback();
    throw $e;
}
```

### Resource Leak → Try-Finally
```php
$resource = acquire();
try {
    return process($resource);
} finally {
    release($resource);
}
```

## Fix Composition Rules

### Order of Operations
1. Add validation/guards at the top
2. Make the minimal code change
3. Keep existing code paths intact
4. Add new exception types if needed

### What NOT to Change
- Method signatures (unless required)
- Return types (unless fixing wrong type)
- Visibility modifiers
- Class structure
- Unrelated code

### Commit Message Format
```
fix(<scope>): <short description>

<detailed description of what was wrong and how it's fixed>

Fixes #<issue-number>
```
