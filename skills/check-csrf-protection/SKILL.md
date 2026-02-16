---
name: acc-check-csrf-protection
description: Analyzes PHP code for CSRF vulnerabilities. Detects missing CSRF tokens, state-changing GET requests, token validation gaps.
---

# CSRF Protection Security Check

Analyze PHP code for Cross-Site Request Forgery vulnerabilities.

## Detection Patterns

### 1. Missing CSRF Tokens

```php
// CRITICAL: Form without CSRF token
<form method="POST" action="/transfer">
    <input name="amount" value="1000">
    <input name="to" value="attacker">
    <button>Transfer</button>
</form>

// CRITICAL: No token validation
public function transfer(Request $request): Response
{
    $amount = $request->get('amount');
    $to = $request->get('to');
    $this->bankService->transfer($amount, $to);
    // No CSRF check!
}
```

### 2. State-Changing GET Requests

```php
// CRITICAL: Modification via GET
#[Route('/user/delete/{id}', methods: ['GET'])]
public function deleteUser(int $id): Response
{
    $this->userService->delete($id);
}

// CRITICAL: Toggle via GET
#[Route('/user/activate/{id}')]
public function activateUser(int $id): Response
{
    $user = $this->userRepository->find($id);
    $user->setActive(true);
}

// VULNERABLE: Logout via GET (session hijacking)
<a href="/logout">Logout</a>
```

### 3. Token Validation Gaps

```php
// VULNERABLE: Token not validated server-side
public function handle(Request $request): Response
{
    // Frontend sends token but backend doesn't check
    $this->processPayment($request);
}

// VULNERABLE: Weak token validation
if ($request->get('_token')) { // Just checks existence
    $this->process();
}

// VULNERABLE: Token not regenerated after login
session_start();
$_SESSION['user'] = $user;
// CSRF token remains same from anonymous session
```

### 4. AJAX/API CSRF Issues

```php
// VULNERABLE: No CSRF for AJAX
fetch('/api/update', {
    method: 'POST',
    body: JSON.stringify(data)
});

// VULNERABLE: Only Origin check, no token
if ($_SERVER['HTTP_ORIGIN'] === 'https://example.com') {
    $this->process(); // Origin can be spoofed in some scenarios
}

// VULNERABLE: CORS misconfiguration
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Credentials: true');
```

### 5. Cookie-Based Token Issues

```php
// VULNERABLE: Token in cookie only
setcookie('csrf_token', $token);
// Attacker can't read but browser sends automatically

// CORRECT: Double Submit Cookie pattern
// Token in cookie AND in request header/body
// Server compares both values
```

### 6. Token Per-Session vs Per-Request

```php
// LESS SECURE: Same token for entire session
$_SESSION['csrf_token'] = bin2hex(random_bytes(32));

// MORE SECURE: New token per form
$token = bin2hex(random_bytes(32));
$_SESSION['csrf_tokens'][] = $token; // Store multiple
```

### 7. Subresource Integrity

```php
// VULNERABLE: Third-party script without SRI
<script src="https://cdn.example.com/lib.js"></script>

// CORRECT: With subresource integrity
<script src="https://cdn.example.com/lib.js"
        integrity="sha384-abc123..."
        crossorigin="anonymous"></script>
```

### 8. SameSite Cookie Missing

```php
// VULNERABLE: No SameSite attribute
setcookie('session_id', $sessionId);

// CORRECT: SameSite=Strict
setcookie('session_id', $sessionId, [
    'samesite' => 'Strict', // or 'Lax'
    'secure' => true,
    'httponly' => true
]);
```

## Grep Patterns

```bash
# Forms without csrf token
Grep: '<form[^>]*method=["\']post["\'][^>]*>' -i --glob "**/*.php"
Grep: 'csrf|_token|token' --glob "**/*.php"

# GET routes that modify state
Grep: '#\[Route.*methods:.*GET.*\]' --glob "**/*.php"
Grep: 'public function delete|update|create' --glob "**/*.php"

# Cookie without samesite
Grep: "setcookie\([^)]+\)\s*;" --glob "**/*.php"

# CORS allow all
Grep: "Access-Control-Allow-Origin.*\*" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| State change via GET | 🔴 Critical |
| No CSRF token on forms | 🔴 Critical |
| Token not validated | 🔴 Critical |
| Missing SameSite cookie | 🟠 Major |
| Token per session only | 🟡 Minor |

## Best Practices

### Framework CSRF Protection

```php
// Symfony
{{ csrf_token('authenticate') }}

// Laravel Blade
@csrf

// Validation
$request->validate([
    '_token' => 'required|string'
]);
```

### Manual CSRF Token

```php
// Generate
$token = bin2hex(random_bytes(32));
$_SESSION['csrf_token'] = $token;

// Include in form
<input type="hidden" name="_token" value="<?= $token ?>">

// Validate
if (!hash_equals($_SESSION['csrf_token'], $_POST['_token'])) {
    throw new CsrfException();
}
```

### API CSRF Protection

```php
// Use custom header (can't be set cross-origin)
fetch('/api/update', {
    method: 'POST',
    headers: {
        'X-Requested-With': 'XMLHttpRequest',
        'X-CSRF-Token': csrfToken
    },
    body: JSON.stringify(data)
});

// Server validates header
$token = $request->headers->get('X-CSRF-Token');
if (!$this->csrfManager->isValid($token)) {
    throw new CsrfException();
}
```

### SameSite Cookies

```php
session_start([
    'cookie_samesite' => 'Strict', // Prevents cross-site sending
    'cookie_secure' => true,
    'cookie_httponly' => true,
]);
```

## Output Format

```markdown
### CSRF Vulnerability: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-352 (Cross-Site Request Forgery)

**Issue:**
[Description of the CSRF weakness]

**Attack Vector:**
Attacker creates malicious page that submits form to victim's browser.

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// With CSRF protection
```
```
