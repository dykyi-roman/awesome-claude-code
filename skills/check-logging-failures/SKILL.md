---
name: acc-check-logging-failures
description: Detects OWASP A09:2021 Security Logging and Monitoring Failures. Identifies log injection, PII in logs, missing audit trails, insufficient error context, and blind spots.
---

# Security Logging & Monitoring Failures (A09:2021)

Analyze PHP code for logging and monitoring security issues.

## Detection Patterns

### 1. Log Injection

```php
// CRITICAL: User input directly in log message
$this->logger->info("User logged in: " . $request->get('username'));
// Attacker input: "admin\n[CRITICAL] System breached"
// Creates fake log entries!

// CRITICAL: Multiline injection
$this->logger->info("Search query: " . $_GET['q']);
// Input: "test\n2025-01-01 [ERROR] Payment failed for user=admin token=abc123"

// CORRECT: Structured logging with context
$this->logger->info('User login attempt', [
    'username' => $request->get('username'), // In structured context, not message
    'ip' => $request->getClientIp(),
    'userAgent' => $request->headers->get('User-Agent'),
]);
```

### 2. PII / Sensitive Data in Logs

```php
// CRITICAL: Password in logs
$this->logger->debug('Login attempt', [
    'email' => $user->email(),
    'password' => $request->get('password'), // NEVER log passwords!
]);

// CRITICAL: Credit card in logs
$this->logger->info('Payment processed', [
    'cardNumber' => $payment->cardNumber(), // PCI-DSS violation!
    'cvv' => $payment->cvv(),               // NEVER!
]);

// CRITICAL: Token/secret in logs
$this->logger->info('API call', [
    'url' => $url,
    'token' => $this->apiToken, // Leaks authentication token
]);

// CORRECT: Mask sensitive data
$this->logger->info('Payment processed', [
    'cardLast4' => substr($payment->cardNumber(), -4),
    'amount' => $payment->amount()->toString(),
]);
```

### 3. Missing Audit Trail for Security Events

```php
// VULNERABLE: No logging on security-relevant actions
class PasswordResetService
{
    public function reset(string $token, string $newPassword): void
    {
        $user = $this->validateToken($token);
        $user->changePassword($newPassword);
        $this->userRepo->save($user);
        // No audit log! Cannot detect unauthorized resets
    }
}

// CORRECT: Full audit trail
class PasswordResetService
{
    public function reset(string $token, string $newPassword): void
    {
        $user = $this->validateToken($token);
        $user->changePassword($newPassword);
        $this->userRepo->save($user);

        $this->auditLogger->info('Password reset completed', [
            'userId' => $user->id()->toString(),
            'ip' => $this->request->getClientIp(),
            'timestamp' => (new \DateTimeImmutable())->format('c'),
            'action' => 'password_reset',
        ]);
    }
}
```

### 4. Missing Security Event Logging

Security events that MUST be logged:
```php
// MISSING: Failed login attempts
// MISSING: Authorization failures (403)
// MISSING: Input validation failures
// MISSING: Account lockout triggers
// MISSING: Admin actions (user creation, role changes)
// MISSING: Data export/download
// MISSING: Configuration changes
// MISSING: API key creation/revocation
```

### 5. Catch-All Swallowing Exceptions

```php
// CRITICAL: Exception swallowed silently
try {
    $this->processPayment($order);
} catch (\Throwable $e) {
    // Silently swallowed — no log, no alert, no trace
    return null;
}

// CRITICAL: Generic catch without context
try {
    $this->processPayment($order);
} catch (\Exception $e) {
    $this->logger->error($e->getMessage()); // Missing stack trace and context!
}

// CORRECT: Full exception logging
try {
    $this->processPayment($order);
} catch (\Throwable $e) {
    $this->logger->error('Payment processing failed', [
        'orderId' => $order->id()->toString(),
        'amount' => $order->total()->toString(),
        'exception' => $e::class,
        'message' => $e->getMessage(),
        'trace' => $e->getTraceAsString(),
    ]);
    throw new PaymentFailedException('Payment processing error', previous: $e);
}
```

### 6. No Log Level Discipline

```php
// ANTIPATTERN: Everything at same level
$this->logger->info('System starting');
$this->logger->info('User not found');     // Should be WARNING
$this->logger->info('Database connection failed'); // Should be CRITICAL
$this->logger->info('Invalid input');      // Should be WARNING

// CORRECT: Proper log levels (PSR-3)
$this->logger->info('System starting');                    // Informational
$this->logger->warning('User not found', ['id' => $id]);  // Expected edge case
$this->logger->critical('Database connection failed');     // System cannot operate
$this->logger->notice('Invalid input rejected');           // Security event
```

## Grep Patterns

```bash
# Log injection (string concatenation in log)
Grep: "logger->(info|debug|warning|error|critical)\([^,]*\." --glob "**/*.php"
Grep: "logger->.*\. \\\$" --glob "**/*.php"

# PII in logs
Grep: "logger->.*password|logger->.*card|logger->.*token|logger->.*secret" -i --glob "**/*.php"
Grep: "'password'.*=>|'cardNumber'.*=>|'ssn'.*=>|'token'.*=>" --glob "**/*.php"

# Silent exception swallowing
Grep: "catch.*\{[\s]*\}" --glob "**/*.php"
Grep: "catch.*\{[\s]*return" --glob "**/*.php"

# Missing logging in security methods
Grep: "function login|function authenticate|function resetPassword|function changeRole" --glob "**/*.php"

# Security events without logging
Grep: "password_verify|Authorization|403|401" --glob "**/*.php"
Grep: "logger" --glob "**/*Auth*Controller*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Log injection | 🔴 Critical |
| Passwords/secrets in logs | 🔴 Critical |
| No audit trail for auth events | 🔴 Critical |
| Silent exception swallowing | 🟠 Major |
| PII (email, name) in debug logs | 🟠 Major |
| Missing security event logging | 🟠 Major |
| Wrong log levels | 🟡 Minor |

## Output Format

```markdown
### Logging Failure: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-117 (Log Injection) / CWE-532 (Information in Log)
**OWASP:** A09:2021 — Security Logging and Monitoring Failures

**Issue:**
[Description of the logging vulnerability]

**Attack Vector:**
[How this aids attackers or violates compliance]

**Code:**
```php
// Vulnerable logging
```

**Fix:**
```php
// Secure logging
```
```
