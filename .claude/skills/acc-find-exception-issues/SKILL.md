---
name: acc-find-exception-issues
description: Detects exception handling issues in PHP code. Finds swallowed exceptions, generic catches, missing exception handling, re-throwing without context, exception in finally.
---

# Exception Issue Detection

Analyze PHP code for exception handling problems.

## Detection Patterns

### 1. Swallowed Exceptions (Empty Catch)

```php
// BUG: Exception completely ignored
try {
    $this->riskyOperation();
} catch (Exception $e) {
    // Empty catch block - bug hidden
}

// BUG: Only logging, no handling
try {
    $this->process();
} catch (Exception $e) {
    $this->logger->error($e->getMessage());
    // No re-throw, no return, execution continues
}
```

### 2. Generic Exception Catching

```php
// BUG: Catches everything
try {
    $this->save();
} catch (Exception $e) {
    // Catches TypeError, LogicException, etc.
}

// BUG: Using Throwable carelessly
try {
    $this->process();
} catch (Throwable $t) {
    // Catches Error too, hiding fatal issues
}
```

### 3. Missing Exception Handling

```php
// BUG: Unchecked external call
$response = $httpClient->request('GET', $url); // May throw

// BUG: File operations without try
$content = file_get_contents($path); // Returns false on failure

// BUG: JSON without error check
$data = json_decode($json); // May return null on error
```

### 4. Re-throwing Without Context

```php
// BUG: Lost context
try {
    $this->process();
} catch (DatabaseException $e) {
    throw new RuntimeException('Failed'); // Lost original exception
}

// FIXED: Preserve chain
throw new RuntimeException('Failed to process', 0, $e);
```

### 5. Exception in Finally Block

```php
// BUG: Exception in finally hides original
try {
    $this->process();
} finally {
    $this->cleanup(); // If this throws, original exception is lost
}

// FIXED:
} finally {
    try {
        $this->cleanup();
    } catch (Exception $e) {
        $this->logger->warning('Cleanup failed', ['exception' => $e]);
    }
}
```

### 6. Catch Order Issues

```php
// BUG: Parent before child
try {
    $this->process();
} catch (Exception $e) {
    // Catches everything
} catch (InvalidArgumentException $e) {
    // Never reached
}
```

### 7. Return in Finally

```php
// BUG: Return in finally overrides exception
try {
    throw new Exception('Error');
} finally {
    return true; // Exception is suppressed
}
```

### 8. Using Exception for Control Flow

```php
// BUG: Exception as goto
try {
    foreach ($items as $item) {
        if ($found) {
            throw new FoundException($item);
        }
    }
} catch (FoundException $e) {
    $result = $e->getItem();
}
```

### 9. Missing @throws Documentation

```php
// BUG: Undocumented exception
public function process(): void
{
    if (!$valid) {
        throw new InvalidArgumentException(); // Not documented
    }
}
```

## Grep Patterns

```bash
# Empty catch blocks
Grep: "catch\s*\([^)]+\)\s*\{\s*\}" --glob "**/*.php"

# Generic Exception catch
Grep: "catch\s*\(\s*(Exception|\\\\Exception)\s+" --glob "**/*.php"

# Throwable catch
Grep: "catch\s*\(\s*(Throwable|\\\\Throwable)\s+" --glob "**/*.php"

# throw new without previous
Grep: "throw new \w+Exception\([^,)]+\);" --glob "**/*.php"

# Return in finally
Grep: "finally\s*\{[^}]*return" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Swallowed exception | 🔴 Critical |
| Return in finally | 🔴 Critical |
| Generic Throwable catch | 🟠 Major |
| Lost exception chain | 🟠 Major |
| Exception for control flow | 🟡 Minor |
| Missing @throws | 🟡 Minor |

## Best Practices

### Specific Exception Handling

```php
try {
    $this->save();
} catch (UniqueConstraintException $e) {
    throw new DuplicateEmailException($email, 0, $e);
} catch (ConnectionException $e) {
    throw new DatabaseUnavailableException(0, $e);
}
// Let other exceptions bubble up
```

### Proper Exception Chain

```php
throw new DomainException(
    sprintf('Failed to process order %s', $orderId),
    previous: $originalException
);
```

### Safe Finally

```php
try {
    $this->process();
} finally {
    try {
        $this->cleanup();
    } catch (Throwable $e) {
        // Log but don't throw
        $this->logger->error('Cleanup failed', ['exception' => $e]);
    }
}
```

## Output Format

```markdown
### Exception Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Swallowed|Generic Catch|Missing Chain|...]

**Issue:**
[Description of the exception handling problem]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// Proper exception handling
```
```
