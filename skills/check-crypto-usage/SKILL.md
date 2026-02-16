---
name: acc-check-crypto-usage
description: Analyzes PHP code for cryptography issues. Detects weak algorithms, hardcoded keys, insecure random, poor key management, deprecated functions.
---

# Cryptography Security Check

Analyze PHP code for cryptographic vulnerabilities.

## Detection Patterns

### 1. Weak Hashing Algorithms

```php
// CRITICAL: Broken for passwords
$hash = md5($password);
$hash = sha1($password);
$hash = hash('sha256', $password);
$hash = crypt($password, '$1$salt$'); // MD5-based

// CRITICAL: No salt
$hash = hash('sha256', $password); // Rainbow table attack

// CORRECT:
$hash = password_hash($password, PASSWORD_ARGON2ID);
$hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
```

### 2. Weak Encryption Algorithms

```php
// CRITICAL: Deprecated algorithms
$encrypted = mcrypt_encrypt(MCRYPT_DES, $key, $data);
$encrypted = mcrypt_encrypt(MCRYPT_RIJNDAEL_256, $key, $data);

// CRITICAL: ECB mode
$encrypted = openssl_encrypt($data, 'aes-256-ecb', $key);

// VULNERABLE: RC4, Blowfish, 3DES
$encrypted = openssl_encrypt($data, 'des-ede3-cbc', $key);

// CORRECT:
$encrypted = openssl_encrypt($data, 'aes-256-gcm', $key, 0, $iv, $tag);
```

### 3. Hardcoded Keys

```php
// CRITICAL: Key in source code
$key = 'my-secret-key-12345';
$encrypted = openssl_encrypt($data, 'aes-256-cbc', $key);

// CRITICAL: IV hardcoded
$iv = '1234567890123456';

// CRITICAL: Key derived from password directly
$key = $password; // Should use key derivation function
```

### 4. Insecure Random Number Generation

```php
// CRITICAL: Predictable random
$token = rand();
$token = mt_rand();
$token = uniqid();
$token = time();
$token = microtime();

// CRITICAL: Weak seed
srand(time());
mt_srand(getmypid());

// CORRECT:
$token = bin2hex(random_bytes(32));
$token = random_int(1, 1000000);
```

### 5. Poor Key Management

```php
// CRITICAL: Key stored with encrypted data
$encrypted = openssl_encrypt($data, 'aes-256-cbc', $key, 0, $iv);
file_put_contents('data.enc', $encrypted . "\n" . $key);

// CRITICAL: Same key for all users
$key = GLOBAL_ENCRYPTION_KEY;
$encrypted = encrypt($userData, $key);

// CRITICAL: Key in database with encrypted data
$user->setEncryptionKey($key);
$user->setEncryptedData($encrypted);
```

### 6. Missing Integrity Protection

```php
// VULNERABLE: Encryption without authentication
$encrypted = openssl_encrypt($data, 'aes-256-cbc', $key, 0, $iv);
// No MAC/tag - susceptible to bit-flipping

// CORRECT: Authenticated encryption
$encrypted = openssl_encrypt($data, 'aes-256-gcm', $key, 0, $iv, $tag);
// Or use sodium_crypto_aead_*
```

### 7. IV/Nonce Issues

```php
// CRITICAL: No IV
$encrypted = openssl_encrypt($data, 'aes-256-cbc', $key);

// CRITICAL: Reused IV
static $iv = null;
if (!$iv) $iv = random_bytes(16);
$encrypted = openssl_encrypt($data, 'aes-256-cbc', $key, 0, $iv);

// CRITICAL: IV from predictable source
$iv = str_pad($userId, 16, '0');

// CORRECT:
$iv = random_bytes(openssl_cipher_iv_length('aes-256-cbc'));
```

### 8. Deprecated Crypto Functions

```php
// CRITICAL: mcrypt is deprecated (removed PHP 7.2+)
mcrypt_encrypt();
mcrypt_decrypt();
mcrypt_create_iv();

// CRITICAL: create_function (code injection + deprecated)
create_function('$a', 'return $a;');
```

### 9. Timing Attacks

```php
// VULNERABLE: Non-constant-time comparison
if ($userToken === $storedToken) { }
if (strcmp($a, $b) === 0) { }

// CORRECT:
if (hash_equals($storedToken, $userToken)) { }
```

### 10. Certificate Validation

```php
// CRITICAL: Disabled SSL verification
curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, 0);

// CRITICAL: In stream context
$context = stream_context_create([
    'ssl' => ['verify_peer' => false]
]);
```

## Grep Patterns

```bash
# Weak hashing
Grep: "md5\(|sha1\(|crypt\(" --glob "**/*.php"

# Weak encryption
Grep: "mcrypt_|MCRYPT_|des-|rc4|blowfish" -i --glob "**/*.php"

# Hardcoded keys
Grep: "(key|secret|password)\s*=\s*['\"][^'\"]{8,}['\"]" -i --glob "**/*.php"

# Weak random
Grep: "rand\(|mt_rand\(|uniqid\(" --glob "**/*.php"

# Disabled SSL
Grep: "SSL_VERIFYPEER.*false|verify_peer.*false" --glob "**/*.php"

# Non-constant-time comparison
Grep: "===.*token|\$token\s*===" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| MD5/SHA1 for passwords | 🔴 Critical |
| Hardcoded encryption keys | 🔴 Critical |
| Disabled SSL verification | 🔴 Critical |
| Predictable random | 🔴 Critical |
| ECB mode encryption | 🟠 Major |
| Missing integrity check | 🟠 Major |
| Timing attack | 🟠 Major |
| Reused IV | 🟠 Major |

## Best Practices

### Password Hashing

```php
$hash = password_hash($password, PASSWORD_ARGON2ID, [
    'memory_cost' => 65536,
    'time_cost' => 4,
    'threads' => 3
]);

// Or bcrypt
$hash = password_hash($password, PASSWORD_BCRYPT, ['cost' => 12]);
```

### Encryption

```php
// Use libsodium (built into PHP 7.2+)
$key = sodium_crypto_secretbox_keygen();
$nonce = random_bytes(SODIUM_CRYPTO_SECRETBOX_NONCEBYTES);
$encrypted = sodium_crypto_secretbox($data, $nonce, $key);

// Or OpenSSL with GCM
$iv = random_bytes(12);
$encrypted = openssl_encrypt($data, 'aes-256-gcm', $key, 0, $iv, $tag);
```

### Secure Random

```php
$bytes = random_bytes(32);
$int = random_int(1, 100);
```

### Key Derivation

```php
$key = sodium_crypto_pwhash(
    32,
    $password,
    $salt,
    SODIUM_CRYPTO_PWHASH_OPSLIMIT_INTERACTIVE,
    SODIUM_CRYPTO_PWHASH_MEMLIMIT_INTERACTIVE
);
```

## Output Format

```markdown
### Cryptography Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-327 (Use of Broken Crypto Algorithm)

**Issue:**
[Description of the cryptographic weakness]

**Attack Vector:**
[How attacker exploits this]

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// Secure cryptography
```
```
