---
name: acc-check-cors-security
description: Audits CORS configuration security. Detects wildcard origins, credentials with wildcards, dynamic origin reflection, missing preflight handling, and overly permissive policies.
---

# CORS Security Audit (A05:2021)

Analyze PHP code for CORS misconfiguration vulnerabilities.

## Detection Patterns

### 1. Wildcard Origin

```php
// CRITICAL: Allows any website to make requests
header('Access-Control-Allow-Origin: *');

// In framework config:
'allowed_origins' => ['*'], // Any origin!
```

### 2. Credentials with Wildcard

```php
// CRITICAL: Browser ignores this (spec violation), but shows misconfiguration intent
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Credentials: true');
// Cannot use * with credentials — forces dynamic origin reflection
```

### 3. Dynamic Origin Reflection (Dangerous)

```php
// CRITICAL: Reflects any Origin header — equivalent to wildcard with credentials
class CorsMiddleware
{
    public function handle(Request $request, Response $response): Response
    {
        $origin = $request->headers->get('Origin');
        $response->headers->set('Access-Control-Allow-Origin', $origin); // Reflects ANY origin!
        $response->headers->set('Access-Control-Allow-Credentials', 'true');
        return $response;
    }
}

// CORRECT: Whitelist of allowed origins
class CorsMiddleware
{
    private const array ALLOWED_ORIGINS = [
        'https://app.example.com',
        'https://admin.example.com',
    ];

    public function handle(Request $request, Response $response): Response
    {
        $origin = $request->headers->get('Origin');
        if (in_array($origin, self::ALLOWED_ORIGINS, true)) {
            $response->headers->set('Access-Control-Allow-Origin', $origin);
            $response->headers->set('Access-Control-Allow-Credentials', 'true');
            $response->headers->set('Vary', 'Origin');
        }
        return $response;
    }
}
```

### 4. Missing Vary: Origin Header

```php
// VULNERABLE: Without Vary, CDN/proxy may cache wrong CORS headers
$response->headers->set('Access-Control-Allow-Origin', $dynamicOrigin);
// Missing: $response->headers->set('Vary', 'Origin');
// CDN caches response for origin A, serves to origin B
```

### 5. Overly Permissive Methods/Headers

```php
// VULNERABLE: Allows all methods including DELETE, PATCH
header('Access-Control-Allow-Methods: *');
header('Access-Control-Allow-Headers: *');

// CORRECT: Minimal required methods
$response->headers->set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
$response->headers->set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
```

### 6. Missing Preflight Handling

```php
// VULNERABLE: OPTIONS request not handled — browser blocks request
class ApiController
{
    public function handle(Request $request): Response
    {
        // No OPTIONS handling — preflight fails
        return $this->processRequest($request);
    }
}

// CORRECT: Handle preflight
if ($request->getMethod() === 'OPTIONS') {
    $response = new Response('', 204);
    $response->headers->set('Access-Control-Allow-Origin', $allowedOrigin);
    $response->headers->set('Access-Control-Allow-Methods', 'GET, POST');
    $response->headers->set('Access-Control-Max-Age', '86400');
    return $response;
}
```

### 7. Regex Origin Matching (Bypass Risk)

```php
// VULNERABLE: Regex can be bypassed
$origin = $request->headers->get('Origin');
if (preg_match('/example\.com$/', $origin)) {
    // Matches: evil-example.com, phishing-example.com
    $response->headers->set('Access-Control-Allow-Origin', $origin);
}

// CORRECT: Exact match or proper regex
if (preg_match('/^https:\/\/([a-z]+\.)?example\.com$/', $origin)) {
    $response->headers->set('Access-Control-Allow-Origin', $origin);
}
```

## Grep Patterns

```bash
# CORS headers
Grep: "Access-Control-Allow-Origin|Access-Control-Allow-Credentials" --glob "**/*.php"
Grep: "Access-Control-Allow-Methods|Access-Control-Allow-Headers" --glob "**/*.php"

# Wildcard origin
Grep: "Allow-Origin.*\*|allowed_origins.*\*" --glob "**/*.php" --glob "**/*.yaml"

# Dynamic origin reflection
Grep: "Origin.*header|getHeader.*Origin" --glob "**/*.php"

# CORS framework config
Grep: "cors|CORS" --glob "**/*.yaml" --glob "**/*.yml" --glob "**/*.php"

# Missing Vary header
Grep: "Allow-Origin" --glob "**/*.php"
Grep: "Vary.*Origin" --glob "**/*.php"

# Preflight handling
Grep: "OPTIONS|preflight" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Dynamic origin reflection + credentials | 🔴 Critical |
| Wildcard origin on authenticated API | 🔴 Critical |
| Weak regex origin matching | 🟠 Major |
| Missing Vary: Origin | 🟠 Major |
| Wildcard methods/headers | 🟡 Minor |
| Missing preflight handling | 🟡 Minor |

## Output Format

```markdown
### CORS Security: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-942 (Overly Permissive CORS Policy)
**OWASP:** A05:2021 — Security Misconfiguration

**Issue:**
[Description of the CORS misconfiguration]

**Attack Scenario:**
[How attacker exploits this from malicious origin]

**Current Configuration:**
```
Access-Control-Allow-Origin: *
Access-Control-Allow-Credentials: true
```

**Fix:**
```php
// Secure CORS configuration
```
```
