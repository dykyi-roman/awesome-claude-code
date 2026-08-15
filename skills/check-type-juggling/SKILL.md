---
name: check-type-juggling
description: Detects PHP type juggling vulnerabilities. Identifies loose comparison with user input, in_array without strict mode, switch statement type coercion, and hash comparison bypasses.
---

# Type Juggling Security Check (A03:2021)

Analyze PHP code for type juggling vulnerabilities exploiting PHP's loose comparison behavior.

**PHP version baseline: 8.4.** PHP 8.0 changed number-to-string comparison
([Saner string to number comparisons](https://wiki.php.net/rfc/string_to_number_comparison)):
an int compared with a *non-numeric* string is now compared **as a string**, so `0 == 'admin'`
is `false`. Do not report the pre-8.0 bypass. What survives is listed below — bools, numeric
strings, `null`, and `false`-returning functions.

## Detection Patterns

### 1. Loose Comparison with User Input

```php
// CRITICAL: Loose == comparison with user input
if ($request->get('role') == 'admin') { } // true == 'admin' is true — a JSON body can send a bool
if ($id == '100') { }                     // '1e2' == '100' is true — both are numeric strings

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
// in_array(true, ['admin', 'editor']) === true!  — bool vs non-empty string
// in_array(0, ['admin']) is false since PHP 8 — do not report that one

// VULNERABLE: numeric-string values still collide
$allowedIds = ['100', '200'];
if (in_array($input, $allowedIds)) { }
// '1e2' == '100' is true → '1e2' and ' 100' both pass

// CORRECT: Always use strict mode
if (in_array($request->get('role'), $allowedRoles, true)) { }
```

### 3. Switch Statement Type Coercion

```php
// VULNERABLE: Switch uses loose comparison
switch ($request->get('id')) {
    case 100:   // '1e2' and ' 100' both match — numeric-string coercion
        $this->deleteAll();
        break;
    case 'view':
        $this->view();
        break;
}
// Since PHP 8 a non-numeric string no longer matches `case 0`,
// but numeric strings and bools still coerce into the wrong branch.

// CORRECT: Use match (strict comparison)
$result = match ($request->get('action')) {
    'view' => $this->view(),
    'edit' => $this->edit(),
    default => throw new InvalidActionException(),
};
```

### 4. Hash Comparison Bypass

```php
// CRITICAL: comparing a false-returning function with == instead of ===
if (strpos($url, 'https://') == 0) { }
// strpos() returns false when not found, and false == 0 is true →
// every URL WITHOUT the prefix passes as "starts with https://"

// CORRECT
if (str_starts_with($url, 'https://')) { }

// NOTE: strcmp() with an array argument throws TypeError since PHP 8 —
// the old "strcmp() returns null" bypass no longer exists. Still use ===
// on its result, because == hides an int|false mix-up on sibling functions.

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
// VULNERABLE: JSON sends a bool where a string is expected
$data = json_decode($request->getContent(), true);
if ($data['token'] == $validToken) { }
// JSON: {"token": true} → true == "any-non-empty-string" is true!
// (JSON: {"token": 0} no longer matches a non-numeric string in PHP 8)

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

# in_array without strict — two-pass: ripgrep has no lookahead, so widen then confirm
# 1) list every call site, 2) Read each hit and check for a third `true` argument
Grep: "in_array\s*\(" --glob "**/*.php"

# switch instead of match (ripgrep uses `|`, never the BRE `\|`)
Grep: "switch\s*\(\\\$(request|input|data)" --glob "**/*.php"

# strcmp with loose comparison
Grep: "strcmp\(.*==\s*0|strcmp\(.*!=\s*0" --glob "**/*.php"

# Hash comparison with ==
Grep: "md5\(.*==|sha1\(.*==|hash\(.*==" --glob "**/*.php"

# array_search without strict — same two-pass approach as in_array
Grep: "array_search\s*\(" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Token/hash comparison with == | 🔴 Critical |
| Authentication check with == | 🔴 Critical |
| `false`-returning function compared with == (e.g. `strpos(...) == 0`) | 🔴 Critical |
| in_array without strict on security check | 🟠 Major |
| JSON decode + loose comparison | 🟠 Major |
| switch on user input (instead of match) | 🟠 Major |
| in_array without strict (non-security) | 🟡 Minor |
| General loose == usage | 🟡 Minor |

**Do not report as Critical on PHP 8+:** a bare `in_array($string, $stringList)` where every element
is a *non-numeric* string. The pre-8.0 `0 == 'admin'` bypass is gone; the residual risk is a bool or
numeric-string input, which is Major, not Critical. Confirm the input can actually be a bool or a
numeric string before escalating.

## PHP Type Juggling Reference

Verified against PHP 8.4. The first row is the one that changed in 8.0 — everything below it still holds.

| Comparison | Result | Why |
|-----------|--------|-----|
| `0 == 'admin'` | `false` | **PHP 8+:** int is compared as a string against a non-numeric string |
| `'1e2' == '100'` | `true` | Both are numeric strings → compared numerically |
| `' 1' == '1'` | `true` | Leading whitespace is allowed in a numeric string |
| `0 == null` | `true` | `null` casts to `0` |
| `'' == null` | `true` | `null` casts to `''` |
| `'0e1' == '0e2'` | `true` | Both numeric strings evaluate to 0 (magic-hash bypass) |
| `true == 'anything'` | `true` | Non-empty string casts to `true` |
| `[] == false` | `true` | Empty array casts to `false` |
| `false == 0` | `true` | The `strpos()`/`strstr()` false-return trap |

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
