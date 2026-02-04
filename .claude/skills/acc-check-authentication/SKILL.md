---
name: acc-check-authentication
description: Analyzes PHP code for authentication issues. Detects weak password handling, insecure sessions, missing auth checks, token vulnerabilities.
---

# Authentication Security Check

Analyze PHP code for authentication vulnerabilities.

## Detection Patterns

### 1. Weak Password Handling

```php
// CRITICAL: Plain text password storage
$user->setPassword($_POST['password']);

// CRITICAL: Weak hashing (MD5, SHA1)
$hash = md5($password);
$hash = sha1($password);
$hash = hash('sha256', $password);

// VULNERABLE: No salt
$hash = password_hash($password, PASSWORD_DEFAULT); // OK, but check algo

// CRITICAL: Password in logs
$this->logger->info('Login attempt', ['password' => $password]);
```

### 2. Insecure Session Management

```php
// VULNERABLE: Predictable session ID
session_id('user_' . $userId);

// VULNERABLE: Session fixation
session_start();
$_SESSION['user'] = $userId; // No regenerate_id

// VULNERABLE: Session in URL
session_start();
echo '<a href="page.php?' . SID . '">'; // Session ID in URL

// CORRECT: Regenerate on privilege change
session_regenerate_id(true);
$_SESSION['user'] = $userId;
```

### 3. Missing Authentication Checks

```php
// CRITICAL: No auth check in controller
public function deleteUser(int $id): Response
{
    $this->userService->delete($id); // Who can call this?
}

// CRITICAL: Auth bypass via parameter
if ($_GET['admin'] === 'true') {
    $this->grantAdminAccess();
}

// VULNERABLE: Relying only on hidden field
if ($_POST['is_admin'] === '1') { }
```

### 4. Token Vulnerabilities

```php
// CRITICAL: Weak token generation
$token = md5(time()); // Predictable
$token = rand(); // Not cryptographically secure
$token = uniqid(); // Not secure

// CRITICAL: Token without expiry
$token = $this->generateToken();
$user->setResetToken($token); // No expiry time

// CRITICAL: Timing attack on comparison
if ($token === $storedToken) { } // Use hash_equals

// CORRECT:
$token = bin2hex(random_bytes(32));
if (hash_equals($storedToken, $token)) { }
```

### 5. Credential Exposure

```php
// CRITICAL: Password in URL
$url = "/login?password=" . urlencode($password);

// CRITICAL: Credentials in error message
throw new AuthException("Invalid password: $password");

// CRITICAL: Auth token in logs
$this->logger->debug('API call', ['token' => $apiToken]);
```

### 6. Remember Me Issues

```php
// CRITICAL: Predictable remember token
$token = md5($userId . time());
setcookie('remember', $token);

// VULNERABLE: No secure flag
setcookie('session_id', $sessionId); // Missing secure, httponly

// CORRECT:
setcookie('remember', $token, [
    'expires' => time() + 86400 * 30,
    'path' => '/',
    'secure' => true,
    'httponly' => true,
    'samesite' => 'Strict'
]);
```

### 7. Brute Force Vulnerability

```php
// VULNERABLE: No rate limiting
public function login(string $email, string $password): bool
{
    return $this->auth->attempt($email, $password);
    // No lockout, no rate limit
}

// VULNERABLE: User enumeration
if (!$user = $this->findByEmail($email)) {
    throw new Exception('User not found'); // Different from wrong password
}
```

### 8. OAuth/Social Login Issues

```php
// VULNERABLE: State parameter not validated
$code = $_GET['code'];
$token = $this->oauth->getToken($code); // CSRF possible

// VULNERABLE: Trusting social provider email
$email = $oauthUser->getEmail();
$user = $this->findOrCreateByEmail($email); // Account takeover risk
```

## Grep Patterns

```bash
# Weak hashing
Grep: "md5\(\$|sha1\(\$|hash\(['\"]sha" --glob "**/*.php"

# Missing session_regenerate_id
Grep: "session_start" --glob "**/*.php"
Grep: "session_regenerate_id" --glob "**/*.php"

# Weak random
Grep: "rand\(|mt_rand\(|uniqid\(" --glob "**/*.php"

# Cookie without flags
Grep: "setcookie\([^,]+,[^,]+\)" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Plain text password | 🔴 Critical |
| Weak hashing (MD5/SHA1) | 🔴 Critical |
| Missing auth check | 🔴 Critical |
| Session fixation | 🔴 Critical |
| Predictable tokens | 🔴 Critical |
| No rate limiting | 🟠 Major |
| User enumeration | 🟠 Major |
| Cookie without flags | 🟡 Minor |

## Best Practices

### Password Hashing

```php
// Hash
$hash = password_hash($password, PASSWORD_ARGON2ID);

// Verify
if (password_verify($password, $hash)) { }

// Rehash on login if needed
if (password_needs_rehash($hash, PASSWORD_ARGON2ID)) {
    $newHash = password_hash($password, PASSWORD_ARGON2ID);
    $user->setPassword($newHash);
}
```

### Secure Tokens

```php
$token = bin2hex(random_bytes(32));
$hashedToken = hash('sha256', $token);
// Store $hashedToken, send $token to user
// On verify: hash submitted token and compare
```

### Session Security

```php
session_start([
    'cookie_lifetime' => 0,
    'cookie_secure' => true,
    'cookie_httponly' => true,
    'cookie_samesite' => 'Strict',
    'use_strict_mode' => true,
]);
```

## Output Format

```markdown
### Authentication Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-287 (Improper Authentication)

**Issue:**
[Description of the authentication weakness]

**Attack Vector:**
[How attacker exploits this]

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// Secure implementation
```
```
