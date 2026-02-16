---
name: acc-check-secure-headers
description: Audits HTTP security headers configuration. Checks CSP, X-Frame-Options, HSTS, X-Content-Type-Options, Referrer-Policy, Permissions-Policy, and cache control headers.
---

# Secure Headers Audit (A05:2021)

Analyze PHP code for missing or misconfigured HTTP security headers.

## Detection Patterns

### 1. Missing Content-Security-Policy (CSP)

```php
// VULNERABLE: No CSP — allows XSS via inline scripts
class ResponseMiddleware
{
    public function handle(Request $request, Response $response): Response
    {
        // No Content-Security-Policy header
        return $response;
    }
}

// CORRECT: Strict CSP
$response->headers->set('Content-Security-Policy',
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
);
```

### 2. Missing X-Frame-Options

```php
// VULNERABLE: Page can be embedded in iframe (clickjacking)
// No X-Frame-Options or frame-ancestors CSP directive

// CORRECT:
$response->headers->set('X-Frame-Options', 'DENY');
// Or for same-origin iframes:
$response->headers->set('X-Frame-Options', 'SAMEORIGIN');
```

### 3. Missing HSTS (HTTP Strict Transport Security)

```php
// VULNERABLE: No HSTS — allows SSL stripping attacks
// User can be downgraded from HTTPS to HTTP

// CORRECT:
$response->headers->set('Strict-Transport-Security',
    'max-age=31536000; includeSubDomains; preload'
);
```

### 4. Missing X-Content-Type-Options

```php
// VULNERABLE: Browser may MIME-sniff responses
// A CSS file could be executed as JavaScript

// CORRECT:
$response->headers->set('X-Content-Type-Options', 'nosniff');
```

### 5. Missing Referrer-Policy

```php
// VULNERABLE: Full URL sent as Referer to external sites
// Leaks sensitive URL parameters (tokens, IDs)

// CORRECT:
$response->headers->set('Referrer-Policy', 'strict-origin-when-cross-origin');
// Or most restrictive:
$response->headers->set('Referrer-Policy', 'no-referrer');
```

### 6. Missing Permissions-Policy

```php
// VULNERABLE: Browser features available by default
// Camera, microphone, geolocation accessible

// CORRECT:
$response->headers->set('Permissions-Policy',
    'camera=(), microphone=(), geolocation=(), payment=()'
);
```

### 7. Insecure Cache Headers on Sensitive Pages

```php
// VULNERABLE: Sensitive page cached by browser/proxy
class AccountController
{
    public function profile(): Response
    {
        // No cache control — profile page cached!
        return new Response($this->render('profile'));
    }
}

// CORRECT: No caching for sensitive pages
$response->headers->set('Cache-Control', 'no-store, no-cache, must-revalidate, private');
$response->headers->set('Pragma', 'no-cache');
$response->headers->set('Expires', '0');
```

### 8. Weak CSP Configuration

```php
// VULNERABLE: Overly permissive CSP
$response->headers->set('Content-Security-Policy', "default-src *"); // Allows everything!

// VULNERABLE: unsafe-eval allows XSS
$response->headers->set('Content-Security-Policy',
    "script-src 'self' 'unsafe-eval' 'unsafe-inline'" // Defeats CSP purpose
);
```

## Grep Patterns

```bash
# Security headers being set
Grep: "Content-Security-Policy|X-Frame-Options|Strict-Transport-Security" --glob "**/*.php"
Grep: "X-Content-Type-Options|Referrer-Policy|Permissions-Policy" --glob "**/*.php"

# Middleware/response handling
Grep: "class.*Middleware|function handle.*Response" --glob "**/*.php"
Grep: "headers->set\(|header\(" --glob "**/*.php"

# Framework security configs
Grep: "security.*headers|secure.*headers" --glob "**/*.yaml" --glob "**/*.yml"
Grep: "nelmio_security|security_headers" --glob "**/*.yaml"

# Cache headers on sensitive routes
Grep: "Cache-Control|no-store|no-cache" --glob "**/*.php"

# Weak CSP
Grep: "unsafe-eval|unsafe-inline|\*" --glob "**/*.php"
```

## Required Headers Checklist

| Header | Value | Purpose |
|--------|-------|---------|
| `Content-Security-Policy` | `default-src 'self'` | Prevent XSS, data injection |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer leakage |
| `Permissions-Policy` | `camera=(), microphone=()` | Restrict browser features |
| `Cache-Control` | `no-store` (on sensitive pages) | Prevent caching secrets |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Missing CSP | 🔴 Critical |
| Missing HSTS | 🔴 Critical |
| unsafe-eval in CSP | 🔴 Critical |
| Missing X-Frame-Options | 🟠 Major |
| Missing X-Content-Type-Options | 🟠 Major |
| Missing Referrer-Policy | 🟡 Minor |
| Missing Permissions-Policy | 🟡 Minor |

## Output Format

```markdown
### Secure Headers: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line` or framework config
**CWE:** CWE-693 (Protection Mechanism Failure)
**OWASP:** A05:2021 — Security Misconfiguration

**Missing/Misconfigured Header:**
`Header-Name: expected-value`

**Risk:**
[What attack this enables]

**Fix:**
```php
$response->headers->set('Header-Name', 'secure-value');
```
```
