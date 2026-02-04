---
name: acc-check-input-validation
description: Analyzes PHP code for input validation issues. Detects missing validation, weak regex, type coercion attacks, length/format gaps, whitelist violations.
---

# Input Validation Security Check

Analyze PHP code for input validation vulnerabilities.

## Detection Patterns

### 1. Missing Input Validation

```php
// CRITICAL: Direct use of request data
$id = $_GET['id'];
$this->delete($id); // No validation

// CRITICAL: Controller without validation
public function update(Request $request): Response
{
    $data = $request->all();
    $this->service->update($data); // Unvalidated
}

// CRITICAL: Command handler trusts input
public function handle(UpdateUserCommand $command): void
{
    $user->setEmail($command->email); // Not validated
}
```

### 2. Weak Regex Patterns

```php
// VULNERABLE: Anchors missing
if (preg_match('/[a-z]+/', $input)) { } // Matches substring

// VULNERABLE: Case sensitivity
if (preg_match('/^[a-z]+$/', $email)) { } // Misses uppercase

// VULNERABLE: Dot matches newline
if (preg_match('/^.+$/', $input)) { } // Dot doesn't match newline

// VULNERABLE: Overly permissive
if (preg_match('/.*/', $input)) { } // Matches everything
```

### 3. Type Coercion Attacks

```php
// VULNERABLE: Loose comparison
if ($request->get('admin') == true) { } // '1', 'true', 1 all pass

// VULNERABLE: Array injection
$where['id'] = $_GET['id']; // Could be array: ?id[]=1&id[]=2

// VULNERABLE: Type juggling
if ($_POST['password'] == 0) { } // 'password123' == 0 is true!
```

### 4. Length/Format Validation Gaps

```php
// VULNERABLE: No length limit
$description = $request->get('description');
$this->save($description); // Could be megabytes

// VULNERABLE: Missing format check
$phone = $request->get('phone'); // Could contain scripts

// VULNERABLE: No max items
$ids = $request->get('ids');
foreach ($ids as $id) { } // Unbounded array
```

### 5. Whitelist Violations

```php
// VULNERABLE: Blacklist instead of whitelist
$forbidden = ['<script>', 'javascript:'];
if (!in_array($input, $forbidden)) { } // Easy to bypass

// VULNERABLE: Dynamic field access
$field = $_GET['field'];
$value = $entity->$field; // Can access any property

// CORRECT: Whitelist approach
$allowed = ['name', 'email', 'phone'];
if (!in_array($field, $allowed, true)) {
    throw new InvalidArgumentException();
}
```

### 6. File Upload Validation

```php
// VULNERABLE: Only checking extension
if (pathinfo($file['name'], PATHINFO_EXTENSION) === 'jpg') { }

// VULNERABLE: MIME type can be spoofed
if ($file['type'] === 'image/jpeg') { }

// CORRECT: Check actual file content
$finfo = new finfo(FILEINFO_MIME_TYPE);
$mime = $finfo->file($file['tmp_name']);
$allowed = ['image/jpeg', 'image/png', 'image/gif'];
if (!in_array($mime, $allowed, true)) { }
```

### 7. Numeric Input Validation

```php
// VULNERABLE: No range check
$page = (int) $_GET['page']; // Could be negative or huge

// VULNERABLE: Float precision
$amount = (float) $_POST['amount']; // 0.1 + 0.2 != 0.3

// CORRECT: Full validation
$page = filter_var($_GET['page'], FILTER_VALIDATE_INT, [
    'options' => ['min_range' => 1, 'max_range' => 1000]
]);
```

## Grep Patterns

```bash
# Direct $_GET/$_POST usage
Grep: "\$_(GET|POST|REQUEST)\[['\"][^'\"]+['\"]\]" --glob "**/*.php"

# Missing filter_var
Grep: "\$request->get\([^)]+\)\s*;" --glob "**/*.php"

# Weak regex (no anchors)
Grep: "preg_match\(['\"]\/[^$^]" --glob "**/*.php"

# Dynamic property access
Grep: "\$\w+->\$" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| No input validation at all | 🔴 Critical |
| Type juggling vulnerability | 🔴 Critical |
| Missing file content check | 🟠 Major |
| Weak regex | 🟠 Major |
| Missing length limits | 🟡 Minor |

## Best Practices

### Use Validation Libraries

```php
// Symfony Validation
$constraints = new Assert\Collection([
    'email' => [new Assert\NotBlank(), new Assert\Email()],
    'age' => [new Assert\Range(['min' => 18, 'max' => 120])],
]);

// Laravel Validation
$validated = $request->validate([
    'email' => 'required|email|max:255',
    'age' => 'required|integer|min:18|max:120',
]);
```

### Always Use Strict Types

```php
declare(strict_types=1);

function process(int $id, string $email): void { }
```

## Output Format

```markdown
### Input Validation: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-20 (Improper Input Validation)

**Issue:**
[Description of missing/weak validation]

**Attack Vector:**
[How attacker exploits this]

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// With proper validation
```
```
