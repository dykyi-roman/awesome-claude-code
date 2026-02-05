---
name: acc-check-deserialization
description: Analyzes PHP code for insecure deserialization. Detects unserialize with user input, missing allowed_classes, PHP object injection risks, gadget chains.
---

# Insecure Deserialization Security Check

Analyze PHP code for insecure deserialization vulnerabilities (OWASP A08:2021).

## Detection Patterns

### 1. Unserialize with User Input

```php
// CRITICAL: Direct user input
$data = unserialize($_GET['data']);
$object = unserialize($_POST['payload']);
$config = unserialize($_COOKIE['session']);

// CRITICAL: Request object
$data = unserialize($request->input('data'));

// CRITICAL: From file upload
$content = file_get_contents($_FILES['import']['tmp_name']);
$data = unserialize($content);
```

### 2. Missing allowed_classes Option

```php
// CRITICAL: No allowed_classes restriction (PHP 7+)
$data = unserialize($serialized);
// Can instantiate ANY class

// CRITICAL: allowed_classes = true (default behavior)
$data = unserialize($serialized, ['allowed_classes' => true]);

// SECURE: No objects allowed
$data = unserialize($serialized, ['allowed_classes' => false]);

// SECURE: Whitelist specific classes
$data = unserialize($serialized, [
    'allowed_classes' => [User::class, Config::class],
]);
```

### 3. Gadget Chain Triggers

```php
// VULNERABLE: Classes with dangerous magic methods
class FileHandler
{
    private string $path;

    // Called on unserialize - could delete arbitrary files
    public function __wakeup(): void
    {
        unlink($this->path);
    }
}

class Logger
{
    private string $logFile;
    private string $data;

    // Called when object destroyed - could write arbitrary files
    public function __destruct()
    {
        file_put_contents($this->logFile, $this->data);
    }
}

class DataLoader
{
    private string $source;

    // Called on property access - SSRF/file read
    public function __get($name)
    {
        return file_get_contents($this->source);
    }
}

class CommandRunner
{
    private string $command;

    // Called when object used as string - RCE
    public function __toString(): string
    {
        return shell_exec($this->command);
    }
}
```

### 4. Database-Stored Serialized Data

```php
// CRITICAL: Trusting database content
$row = $db->query("SELECT settings FROM users WHERE id = ?", [$id]);
$settings = unserialize($row['settings']);
// If attacker can modify DB (SQL injection), they control serialized data

// CRITICAL: Session storage
$sessionData = unserialize($redis->get('session:' . $sessionId));
```

### 5. Phar Deserialization

```php
// CRITICAL: Phar metadata triggers unserialize
$phar = new Phar($userUploadedFile);
// Reading phar file deserializes metadata

// CRITICAL: File operations on phar://
file_exists('phar://' . $uploadedFile);
file_get_contents('phar://' . $userFile);
is_dir('phar://' . $path);
fopen('phar://' . $filename, 'r');

// CRITICAL: include/require phar
include 'phar://' . $plugin . '/bootstrap.php';
```

### 6. Base64-Encoded Serialized Data

```php
// CRITICAL: Common pattern to hide serialized data
$payload = base64_decode($_GET['token']);
$data = unserialize($payload);

// CRITICAL: In cookies
$sessionData = unserialize(base64_decode($_COOKIE['session']));

// CRITICAL: In headers
$auth = unserialize(base64_decode($request->header('X-Auth-Data')));
```

### 7. JSON with Object Mapping

```php
// POTENTIALLY VULNERABLE: JSON to object without validation
$json = file_get_contents('php://input');
$data = json_decode($json);

// CRITICAL: Mapping to class with dangerous methods
$object = (new UserDTO())->fromArray(json_decode($json, true));
// If class has __set or __call that executes code

// CRITICAL: Doctrine/JMS Serializer without type whitelist
$user = $this->serializer->deserialize($json, 'object', 'json');
```

### 8. Cache Deserialization

```php
// CRITICAL: Cache poisoning leads to object injection
$cacheKey = 'user_' . $userId;
$user = unserialize($cache->get($cacheKey));
// If cache can be poisoned, attacker controls object

// CRITICAL: File-based cache
$cached = file_get_contents("/tmp/cache/{$key}.cache");
$data = unserialize($cached);
```

### 9. Framework-Specific Patterns

```php
// CRITICAL: Laravel signed URLs without validation
$data = unserialize($request->input('signed_data'));

// CRITICAL: Symfony serialized tokens
$token = unserialize($session->get('_security_main'));

// CRITICAL: Custom session handlers
class MySessionHandler implements SessionHandlerInterface
{
    public function read($id): string|false
    {
        $data = $this->storage->get($id);
        return unserialize($data); // Dangerous
    }
}
```

### 10. RPC/IPC Serialization

```php
// CRITICAL: Inter-process communication
$message = unserialize(file_get_contents('php://stdin'));

// CRITICAL: Queue messages
$job = unserialize($queue->pop());

// CRITICAL: Socket data
$data = unserialize(socket_read($socket, 1024));
```

## Grep Patterns

```bash
# unserialize calls
Grep: "unserialize\s*\(" --glob "**/*.php"

# unserialize with user input
Grep: "unserialize\s*\([^)]*(\\\$_GET|\\\$_POST|\\\$_COOKIE|\\\$_REQUEST)" --glob "**/*.php"

# phar:// usage
Grep: "phar://" --glob "**/*.php"

# Magic methods that could be exploited
Grep: "__wakeup|__destruct|__toString|__call\s*\(" --glob "**/*.php"

# Missing allowed_classes
Grep: "unserialize\s*\([^)]+\)\s*;" --glob "**/*.php"
```

## Secure Patterns

### Use JSON Instead

```php
// SECURE: JSON for data interchange
$data = json_decode($input, true, 512, JSON_THROW_ON_ERROR);

// SECURE: Validate JSON structure
$data = json_decode($input, true);
if (!isset($data['expected_field'])) {
    throw new InvalidInputException();
}
```

### Restrict allowed_classes

```php
// SECURE: Only allow specific classes
$allowed = [
    UserDTO::class,
    ConfigDTO::class,
];

$data = unserialize($serialized, ['allowed_classes' => $allowed]);

// SECURE: No objects at all (for arrays/primitives)
$data = unserialize($serialized, ['allowed_classes' => false]);
```

### Signature Verification

```php
// SECURE: Sign serialized data
final class SecureSerializer
{
    public function __construct(
        private readonly string $secretKey,
    ) {}

    public function serialize(mixed $data): string
    {
        $serialized = serialize($data);
        $signature = hash_hmac('sha256', $serialized, $this->secretKey);
        return base64_encode($signature . $serialized);
    }

    public function unserialize(string $input, array $allowedClasses = []): mixed
    {
        $decoded = base64_decode($input, true);
        if ($decoded === false || strlen($decoded) < 64) {
            throw new SecurityException('Invalid data format');
        }

        $signature = substr($decoded, 0, 64);
        $serialized = substr($decoded, 64);

        $expected = hash_hmac('sha256', $serialized, $this->secretKey);
        if (!hash_equals($expected, $signature)) {
            throw new SecurityException('Invalid signature');
        }

        return unserialize($serialized, ['allowed_classes' => $allowedClasses]);
    }
}
```

### Use Typed DTOs

```php
// SECURE: Manual mapping to DTO
final readonly class CreateUserRequest
{
    public function __construct(
        public string $name,
        public string $email,
        public int $age,
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            name: $data['name'] ?? throw new ValidationException('Name required'),
            email: $data['email'] ?? throw new ValidationException('Email required'),
            age: (int) ($data['age'] ?? throw new ValidationException('Age required')),
        );
    }
}

// Usage
$data = json_decode($input, true);
$request = CreateUserRequest::fromArray($data);
```

### Disable Phar Wrapper

```php
// In php.ini
; phar.readonly = 1  (prevents phar creation)

// At runtime - remove phar wrapper
stream_wrapper_unregister('phar');

// Validate file type before operations
if (pathinfo($file, PATHINFO_EXTENSION) === 'phar') {
    throw new SecurityException('Phar files not allowed');
}
```

## Severity Classification

| Pattern | Severity | CWE |
|---------|----------|-----|
| unserialize($_GET/$_POST) | 🔴 Critical | CWE-502 |
| unserialize without allowed_classes | 🔴 Critical | CWE-502 |
| Phar with user-controlled path | 🔴 Critical | CWE-502 |
| Classes with dangerous __destruct | 🟠 Major | CWE-502 |
| Cache/DB deserialization | 🟠 Major | CWE-502 |
| Missing signature verification | 🟡 Minor | CWE-502 |

## Output Format

```markdown
### Insecure Deserialization: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-502 (Deserialization of Untrusted Data)

**Issue:**
User-controlled data is deserialized without restrictions, allowing object injection.

**Attack Vector:**
1. Attacker crafts serialized payload with gadget chain
2. Payload triggers __destruct() that writes to file
3. Attacker achieves remote code execution

**Code:**
```php
// Vulnerable
$data = unserialize($_POST['data']);
```

**Fix:**
```php
// Secure: Use JSON or restrict classes
$data = json_decode($_POST['data'], true);

// Or with signature and whitelist
$data = unserialize($payload, [
    'allowed_classes' => [SafeDTO::class],
]);
```

**References:**
- [OWASP Deserialization](https://owasp.org/www-project-web-security-testing-guide/latest/4-Web_Application_Security_Testing/07-Input_Validation_Testing/15-Testing_for_HTTP_Incoming_Requests)
- [PHP Object Injection](https://owasp.org/www-community/vulnerabilities/PHP_Object_Injection)
```
