---
name: acc-check-type-juggling
description: Detects PHP type juggling vulnerabilities. Identifies loose comparison with user input, in_array without strict mode, switch statement type coercion, and hash comparison bypasses.
---

# Type Juggling Security Check (A03:2021)

Analyze PHP code for type juggling vulnerabilities exploiting PHP's loose comparison behavior.

## Detection Patterns

### 1. Loose Comparison with User Input

```php
// CRITICAL: Loose == comparison with user input
if ($request->get('role') == 'admin') { } // '0' == 'admin' is false, but 0 == 'admin' is true!
if ($token == $expectedToken) { }          // Type juggling bypass possible

// CRITICAL: Password comparison
if ($password == $storedHash) { }          // NEVER use == for security checks

// CORRECT: Strict comparison
if ($request->get('role') === 'admin') { }
if (hash_equals($expectedToken, $token)) { } // Timing-safe comparison
```

### 2. in_array Without Strict Mode

```php
// CRITICAL: in_array defaults to loose comparison
$allowedRoles = ['admin', 'editor', 'viewer'];
if (in_array($request->get('role'), $allowedRoles)) { }
// in_array(0, ['admin', 'editor']) === true! (0 == 'admin' is true)
// in_array(true, ['admin']) === true!

// VULNERABLE: Checking allowed values
$allowedStatuses = ['active', 'inactive'];
if (in_array($input, $allowedStatuses)) { }
// true matches any string!

// CORRECT: Always use strict mode
if (in_array($request->get('role'), $allowedRoles, true)) { }
```

### 3. Switch Statement Type Coercion

```php
// VULNERABLE: Switch uses loose comparison
switch ($request->get('action')) {
    case 0:     // Matches any non-numeric string!
        $this->deleteAll();
        break;
    case 'view':
        $this->view();
        break;
}
// Input 'view' matches case 0 first! (if 0 is before 'view')

// CORRECT: Use match (strict comparison)
$result = match ($request->get('action')) {
    'view' => $this->view(),
    'edit' => $this->edit(),
    default => throw new InvalidActionException(),
};
```

### 4. Hash Comparison Bypass

```php
// CRITICAL: strcmp() returns 0 for array input
if (strcmp($input, $expected) == 0) { }
// strcmp([], 'password') returns NULL, and NULL == 0 is true!

// CRITICAL: md5/sha1 magic hashes
if (md5($input) == '0') { }
// md5('240610708') = '0e462097431906509019562988736854'
// '0e...' == '0' is true (scientific notation: 0 * 10^... = 0)

// CRITICAL: Loose comparison of hashes
if (md5($a) == md5($b)) { }
// Two different inputs can have 0e... hashes → both equal 0

// CORRECT: hash_equals for hash comparison
if (hash_equals($expectedHash, md5($input))) { }
```

### 5. Null Coalescing with Loose Types

```php
// VULNERABLE: isset + loose comparison
if (isset($data['admin']) && $data['admin'] == true) {
    $this->grantAdminAccess(); // 'yes', '1', 1, true all pass
}

// VULNERABLE: Empty check
if (!empty($request->get('verified'))) {
    // '0' is empty, but 'false' is not — inconsistent
}

// CORRECT: Explicit type check
if (($data['admin'] ?? false) === true) {
    $this->grantAdminAccess();
}
```

### 6. Array Key Type Juggling

```php
// VULNERABLE: Numeric string keys become integers
$permissions = ['0' => 'none', '1' => 'read', '2' => 'write'];
$level = $request->get('level'); // String from request
$permission = $permissions[$level]; // '01' !== 1, but both exist in different contexts

// VULNERABLE: Boolean key
$config = [true => 'enabled', false => 'disabled'];
// true becomes 1, false becomes 0 as array keys
```

### 7. JSON Decode Type Juggling

```php
// VULNERABLE: JSON sends integer where string expected
$data = json_decode($request->getContent(), true);
if ($data['token'] == $validToken) { }
// JSON: {"token": 0} → 0 == "any-string" is true!

// CORRECT: Validate type after decode
$data = json_decode($request->getContent(), true);
if (!is_string($data['token'] ?? null)) {
    throw new InvalidInputException('Token must be a string');
}
if (hash_equals($validToken, $data['token'])) { }
```

## Grep Patterns

```bash
# Loose comparison with variables
Grep: "\\\$.*==\s*['\"]|['\"].*==\s*\\\$" --glob "**/*.php"
Grep: "==\s*true|==\s*false|==\s*null|==\s*0\b" --glob "**/*.php"

# in_array without strict
Grep: "in_array\([^)]+\)(?!.*true)" --glob "**/*.php"

# switch instead of match
Grep: "switch\s*\(\\\$.*request\|switch\s*\(\\\$.*input\|switch\s*\(\\\$.*data" --glob "**/*.php"

# strcmp with loose comparison
Grep: "strcmp\(.*==\s*0|strcmp\(.*!=\s*0" --glob "**/*.php"

# Hash comparison with ==
Grep: "md5\(.*==|sha1\(.*==|hash\(.*==" --glob "**/*.php"

# array_search without strict
Grep: "array_search\([^)]+\)(?!.*true)" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Token/hash comparison with == | 🔴 Critical |
| Authentication check with == | 🔴 Critical |
| in_array without strict on security check | 🔴 Critical |
| JSON decode + loose comparison | 🟠 Major |
| switch on user input (instead of match) | 🟠 Major |
| in_array without strict (non-security) | 🟡 Minor |
| General loose == usage | 🟡 Minor |

## PHP Type Juggling Reference

| Comparison | Result | Why |
|-----------|--------|-----|
| `0 == 'admin'` | `true` | String cast to int = 0 |
| `0 == null` | `true` | Both falsy |
| `'' == null` | `true` | Both falsy |
| `'0e1' == '0e2'` | `true` | Both = 0 (scientific notation) |
| `true == 'anything'` | `true` | Non-empty string is truthy |
| `[] == false` | `true` | Empty array is falsy |

## Output Format

```markdown
### Type Juggling: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-1025 (Comparison Using Wrong Factors)
**OWASP:** A03:2021 — Injection

**Issue:**
[Description of the type juggling vulnerability]

**Exploit:**
Input `0` (integer) matches any non-numeric string via loose comparison.

**Code:**
```php
// Vulnerable code with ==
```

**Fix:**
```php
// Fixed with === or hash_equals()
```
```
