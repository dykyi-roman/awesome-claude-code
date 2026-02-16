---
name: acc-check-magic-values
description: Analyzes PHP code for magic values. Detects hardcoded numbers, string literals without constants, configuration values embedded in code.
---

# Magic Value Check

Analyze PHP code for hardcoded values that should be constants or configuration.

## Detection Patterns

### 1. Magic Numbers

```php
// BAD: Unexplained numbers
if ($retries > 3) {}
$timeout = 30;
$discount = $price * 0.15;
$pageSize = 20;
sleep(5);

// GOOD: Named constants
private const MAX_RETRIES = 3;
private const DEFAULT_TIMEOUT_SECONDS = 30;
private const DISCOUNT_PERCENT = 0.15;
private const DEFAULT_PAGE_SIZE = 20;
private const RETRY_DELAY_SECONDS = 5;

if ($retries > self::MAX_RETRIES) {}
$timeout = self::DEFAULT_TIMEOUT_SECONDS;
```

### 2. Magic Strings

```php
// BAD: Hardcoded strings
if ($status === 'active') {}
$role = 'admin';
$type = 'subscription';
$format = 'Y-m-d H:i:s';

// GOOD: Constants or Enums
enum UserStatus: string {
    case Active = 'active';
    case Inactive = 'inactive';
}

if ($status === UserStatus::Active->value) {}

private const DATE_FORMAT = 'Y-m-d H:i:s';
private const ROLE_ADMIN = 'admin';
```

### 3. Configuration Values in Code

```php
// BAD: Config in code
$dsn = 'mysql:host=localhost;dbname=myapp';
$apiKey = 'sk_live_abc123';
$emailFrom = 'noreply@example.com';
$maxUploadSize = 10485760; // 10MB

// GOOD: Environment/config
$dsn = getenv('DATABASE_URL');
$apiKey = $this->config->get('stripe.api_key');
$emailFrom = $this->config->get('mail.from');
$maxUploadSize = $this->config->get('upload.max_size');
```

### 4. URL/Path Literals

```php
// BAD: Hardcoded URLs
$apiUrl = 'https://api.example.com/v1';
$webhookUrl = 'https://myapp.com/webhook';
$cdnUrl = 'https://cdn.example.com/assets';

// GOOD: Configuration
$apiUrl = $this->config->get('api.base_url');
$webhookUrl = $this->urlGenerator->generate('webhook_handler');
```

### 5. Array Index Numbers

```php
// BAD: Magic array indices
$name = $parts[0];
$city = $address[2];
$code = $result[1];

// GOOD: Named keys or destructuring
[$name, $city] = $parts;
$name = $result['name'];

// Or use objects/DTOs
$address->getCity();
```

### 6. Bit Flags/Masks

```php
// BAD: Magic bit values
$permissions = 7;
if ($flags & 4) {}
$mode = 0755;

// GOOD: Named constants
public const PERMISSION_READ = 1;
public const PERMISSION_WRITE = 2;
public const PERMISSION_EXECUTE = 4;
public const PERMISSION_ALL = self::PERMISSION_READ |
                               self::PERMISSION_WRITE |
                               self::PERMISSION_EXECUTE;
```

### 7. Time Values

```php
// BAD: Magic time values
$expiry = time() + 3600;
$cacheTime = 86400;
sleep(300);

// GOOD: Named constants with units in name
private const TOKEN_EXPIRY_HOURS = 1;
private const CACHE_TTL_DAYS = 1;
private const RETRY_DELAY_MINUTES = 5;

$expiry = time() + (self::TOKEN_EXPIRY_HOURS * 3600);
```

### 8. HTTP Status Codes

```php
// BAD: Raw status codes
return new Response('', 201);
if ($response->getStatusCode() === 404) {}

// GOOD: Named constants (or Symfony constants)
use Symfony\Component\HttpFoundation\Response;

return new Response('', Response::HTTP_CREATED);
if ($response->getStatusCode() === Response::HTTP_NOT_FOUND) {}
```

### 9. Regex Patterns

```php
// BAD: Unexplained regex
if (preg_match('/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/', $email)) {}

// GOOD: Named pattern
private const EMAIL_PATTERN = '/^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/';

if (preg_match(self::EMAIL_PATTERN, $email)) {}

// BETTER: Use validation library
$this->validator->validate($email, new Email());
```

## Acceptable Magic Values

Some values are universally understood and acceptable:

```php
// OK: Loop initialization
for ($i = 0; $i < $count; $i++) {}

// OK: Array index 0 for first element
$first = $array[0];

// OK: Mathematical identities
$doubled = $value * 2;
$half = $value / 2;

// OK: Empty checks
if (count($items) === 0) {}
if (strlen($string) > 0) {}

// OK: Boolean literals
$isActive = true;
```

## Grep Patterns

```bash
# Numbers in comparisons
Grep: ">\s*\d{2,}|<\s*\d{2,}|===?\s*\d{2,}" --glob "**/*.php"

# Hardcoded strings in conditions
Grep: "===?\s*['\"][a-z_]+['\"]" --glob "**/*.php"

# Time values
Grep: "3600|86400|604800" --glob "**/*.php"

# HTTP status codes
Grep: "Response\([^)]*\d{3}" --glob "**/*.php"

# API keys/secrets patterns
Grep: "(sk_|pk_|api_|key_)[a-zA-Z0-9]+" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Hardcoded credentials | 🔴 Critical (security) |
| Configuration in code | 🟠 Major |
| Business logic numbers | 🟡 Minor |
| Common status codes | 🟢 Suggestion |

## Output Format

```markdown
### Magic Value: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`
**Value:** `3600`

**Issue:**
Hardcoded number `3600` without explanation.

**Current:**
```php
$cache->set($key, $value, 3600);
```

**Suggested:**
```php
private const CACHE_TTL_SECONDS = 3600; // 1 hour

$cache->set($key, $value, self::CACHE_TTL_SECONDS);
```

**Benefit:**
- Self-documenting code
- Single point of change
- Easier to find all usages
```
