---
name: acc-check-sensitive-data
description: Analyzes PHP code for sensitive data exposure. Detects plaintext secrets, exposed credentials, PII in logs, insecure storage, hardcoded keys.
---

# Sensitive Data Security Check

Analyze PHP code for sensitive data exposure vulnerabilities.

## Detection Patterns

### 1. Hardcoded Credentials

```php
// CRITICAL: Hardcoded password
$pdo = new PDO($dsn, 'admin', 'SuperSecret123!');

// CRITICAL: API key in code
$apiKey = 'sk_live_abc123xyz789';
$stripe = new StripeClient($apiKey);

// CRITICAL: Hardcoded secret
define('JWT_SECRET', 'my-secret-key-123');
const ENCRYPTION_KEY = 'aes256-encryption-key';
```

### 2. Credentials in Version Control

```php
// CRITICAL: .env file committed
// Check .gitignore for:
// .env
// *.pem
// *.key
// config/secrets.php

// CRITICAL: Config with real credentials
// config/database.php
return [
    'password' => 'production_password_here',
];
```

### 3. PII in Logs

```php
// CRITICAL: Password in logs
$this->logger->info('Login', ['password' => $password]);

// CRITICAL: Credit card in logs
$this->logger->debug('Payment', ['card' => $cardNumber]);

// VULNERABLE: Full user object logged
$this->logger->info('User created', ['user' => $user]);

// VULNERABLE: Exception with sensitive data
throw new Exception("Login failed for password: $password");
```

### 4. Sensitive Data in URLs

```php
// CRITICAL: Password in URL
$url = "/reset?token=$token&email=$email&password=$password";

// CRITICAL: API key in URL
$url = "https://api.example.com?key=$apiKey";

// VULNERABLE: Session in URL
session_start();
header("Location: /dashboard?" . SID);
```

### 5. Insecure Data Storage

```php
// CRITICAL: Plain text password storage
$user->password = $request->get('password');
$em->persist($user);

// CRITICAL: Storing credit card in plain text
$order->setCreditCard($cardNumber);

// CRITICAL: Symmetric encryption with weak key
$encrypted = openssl_encrypt($ssn, 'aes-256-cbc', 'password');
```

### 6. Response Data Exposure

```php
// CRITICAL: Password in API response
return new JsonResponse([
    'user' => $user->toArray(), // May include password hash
]);

// CRITICAL: Internal data exposed
return new JsonResponse([
    'error' => $exception->getMessage(),
    'trace' => $exception->getTraceAsString(),
    'query' => $lastQuery,
]);
```

### 7. Debug Information Exposure

```php
// CRITICAL: Debug mode in production
ini_set('display_errors', 1);
error_reporting(E_ALL);

// CRITICAL: phpinfo exposed
phpinfo();

// CRITICAL: var_dump in production
var_dump($user);
print_r($config);
```

### 8. Sensitive Comments

```php
// CRITICAL: Credentials in comments
// TODO: Remove before production
// Username: admin
// Password: admin123

// CRITICAL: API keys in comments
// Old API key: sk_test_abc123
```

### 9. Backup/Temporary Files

```php
// Check for presence of:
// .sql files (database dumps)
// .bak files (backups)
// .old files
// .swp files (vim swap)
// .DS_Store
// Thumbs.db
```

### 10. Error Messages Revealing Data

```php
// CRITICAL: SQL error exposure
try {
    $pdo->query($sql);
} catch (PDOException $e) {
    echo $e->getMessage(); // Reveals table/column names
}

// CRITICAL: File path exposure
if (!file_exists($path)) {
    throw new Exception("File not found: $path");
}
```

## Grep Patterns

```bash
# Hardcoded passwords
Grep: "password\s*[=:]\s*['\"][^'\"]{4,}['\"]" -i --glob "**/*.php"

# API keys
Grep: "(api[_-]?key|apikey|secret[_-]?key)\s*[=:]\s*['\"]" -i --glob "**/*.php"

# AWS credentials
Grep: "AKIA[0-9A-Z]{16}" --glob "**/*.php"

# Private keys
Grep: "-----BEGIN (RSA |PRIVATE |EC )" --glob "**/*"

# Logging sensitive fields
Grep: "->log.*password|->info.*password|->debug.*token" -i --glob "**/*.php"
```

## Sensitive Data Types

| Type | Examples | Risk |
|------|----------|------|
| Authentication | Passwords, tokens, API keys | Account takeover |
| Financial | Credit cards, bank accounts | Financial fraud |
| PII | SSN, passport, ID numbers | Identity theft |
| Health | Medical records, diagnoses | Privacy violation |
| Location | Home address, GPS coords | Physical safety |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Hardcoded production credentials | 🔴 Critical |
| Password in logs | 🔴 Critical |
| API keys in code | 🔴 Critical |
| PII in error messages | 🟠 Major |
| Debug info in production | 🟠 Major |
| Sensitive comments | 🟡 Minor |

## Best Practices

### Use Environment Variables

```php
$apiKey = getenv('STRIPE_API_KEY');
$dbPassword = $_ENV['DB_PASSWORD'];
```

### Secure Logging

```php
$this->logger->info('Login attempt', [
    'user_id' => $user->getId(),
    // Never log: password, token, credit card, SSN
]);
```

### Data Masking

```php
function maskEmail(string $email): string
{
    $parts = explode('@', $email);
    return substr($parts[0], 0, 2) . '***@' . $parts[1];
}

function maskCard(string $card): string
{
    return '****-****-****-' . substr($card, -4);
}
```

### Secure Error Handling

```php
try {
    $this->process();
} catch (Exception $e) {
    $this->logger->error('Processing failed', ['exception' => $e]);
    throw new PublicException('An error occurred. Please try again.');
}
```

## Output Format

```markdown
### Sensitive Data Exposure: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-200 (Exposure of Sensitive Information)

**Issue:**
[Description of the data exposure]

**Data Type:** [Password|API Key|PII|...]

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// Secure handling
```
```
