---
name: acc-check-ssrf
description: Analyzes PHP code for SSRF vulnerabilities. Detects unvalidated URLs, internal network access, DNS rebinding, cloud metadata access, URL parsing bypass attempts.
---

# SSRF (Server-Side Request Forgery) Security Check

Analyze PHP code for SSRF vulnerabilities (OWASP A10:2021).

## Detection Patterns

### 1. User-Controlled URLs

```php
// CRITICAL: Direct URL from user input
$url = $_GET['url'];
$content = file_get_contents($url);

// CRITICAL: Request URL from parameter
$response = $httpClient->get($request->input('callback'));

// CRITICAL: User input in cURL
$ch = curl_init($_POST['endpoint']);
curl_exec($ch);

// CRITICAL: Guzzle with user input
$client = new GuzzleHttp\Client();
$client->request('GET', $userProvidedUrl);
```

### 2. Cloud Metadata Endpoint Access

```php
// CRITICAL: AWS metadata endpoint
$url = 'http://169.254.169.254/latest/meta-data/iam/security-credentials/';
// User could redirect to this endpoint

// CRITICAL: GCP metadata
$url = 'http://metadata.google.internal/computeMetadata/v1/';

// CRITICAL: Azure metadata
$url = 'http://169.254.169.254/metadata/instance';

// Detection: URLs that could reach metadata
if (strpos($url, '169.254.') !== false) { /* Block */ }
```

### 3. Internal Network Access

```php
// CRITICAL: Access to internal services
$response = file_get_contents("http://internal-api:8080/admin");

// CRITICAL: Localhost bypass
$url = $_GET['url'];
// User inputs: http://localhost/admin, http://127.0.0.1/admin
// Or: http://0.0.0.0/, http://[::1]/, http://127.1/

// CRITICAL: Private IP ranges
// 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
$url = 'http://10.0.0.1/internal-service';
```

### 4. URL Parsing Bypass

```php
// CRITICAL: Protocol confusion
$url = 'http://evil.com@internal-server/';
$url = 'http://internal-server#@evil.com/';
$url = 'http://internal-server\@evil.com/';

// CRITICAL: URL encoding bypass
$url = 'http://127.0.0.1%00.evil.com/';
$url = 'http://127。0。0。1/'; // Unicode dots

// CRITICAL: DNS rebinding - domain resolves to internal IP
$url = 'http://rebind.attacker.com/'; // First resolves to public, then to 127.0.0.1

// CRITICAL: Redirect chains
$url = 'http://allowed.com/redirect?to=http://internal/';
```

### 5. Protocol Attacks

```php
// CRITICAL: File protocol
$url = 'file:///etc/passwd';
$content = file_get_contents($url);

// CRITICAL: Gopher protocol (can access Redis, memcached)
$url = 'gopher://127.0.0.1:6379/_*1%0d%0a$8%0d%0aflushall';

// CRITICAL: Dict protocol
$url = 'dict://127.0.0.1:6379/info';

// CRITICAL: LDAP protocol
$url = 'ldap://evil.com/o=evil';
```

### 6. PDF/Image Generation SSRF

```php
// CRITICAL: HTML to PDF with user content
$html = '<img src="' . $userUrl . '">';
$pdf->loadHtml($html);

// CRITICAL: Image URL in PDF
$pdf->image($request->input('logo_url'));

// CRITICAL: wkhtmltopdf with user HTML
shell_exec("wkhtmltopdf '$userHtml' output.pdf");
```

### 7. Webhook/Callback SSRF

```php
// CRITICAL: User-provided webhook URL
$webhookUrl = $request->input('webhook_url');
$httpClient->post($webhookUrl, ['json' => $data]);

// CRITICAL: OAuth callback
$callbackUrl = $request->input('redirect_uri');
return redirect($callbackUrl . '?code=' . $code);

// CRITICAL: Import from URL
$data = file_get_contents($request->input('import_url'));
$this->importData($data);
```

### 8. SVG/XML External References

```php
// CRITICAL: SVG with external references
// User uploads SVG containing:
// <image xlink:href="http://internal/secret" />
// <use xlink:href="http://internal/api" />

$svg = file_get_contents($uploadedFile);
// Rendering SVG may fetch external resources
```

## Grep Patterns

```bash
# User URL in HTTP functions
Grep: "(file_get_contents|fopen|curl_init|readfile)\s*\([^)]*\\\$" --glob "**/*.php"

# HTTP client with variable
Grep: "(->get|->post|->request)\s*\([^)]*\\\$" --glob "**/*.php"

# Webhook/callback patterns
Grep: "(webhook|callback|redirect).*url.*\\\$" -i --glob "**/*.php"

# URL from request
Grep: "\\\$_(GET|POST|REQUEST)\[.*url" -i --glob "**/*.php"
```

## Validation Patterns

### URL Allowlist

```php
// SECURE: Strict allowlist
final class UrlValidator
{
    private const ALLOWED_HOSTS = [
        'api.trusted-service.com',
        'cdn.example.com',
    ];

    public function validate(string $url): bool
    {
        $parsed = parse_url($url);
        if ($parsed === false || !isset($parsed['host'])) {
            return false;
        }

        return in_array($parsed['host'], self::ALLOWED_HOSTS, true);
    }
}
```

### Block Internal Networks

```php
// SECURE: Block private/internal IPs
final class SafeUrlFetcher
{
    public function fetch(string $url): string
    {
        $parsed = parse_url($url);
        $ip = gethostbyname($parsed['host']);

        if ($this->isPrivateIp($ip) || $this->isMetadataIp($ip)) {
            throw new SecurityException('Internal URL not allowed');
        }

        return file_get_contents($url);
    }

    private function isPrivateIp(string $ip): bool
    {
        return filter_var(
            $ip,
            FILTER_VALIDATE_IP,
            FILTER_FLAG_NO_PRIV_RANGE | FILTER_FLAG_NO_RES_RANGE
        ) === false;
    }

    private function isMetadataIp(string $ip): bool
    {
        return str_starts_with($ip, '169.254.');
    }
}
```

### Protocol Allowlist

```php
// SECURE: Only allow HTTPS
final class SecureUrlValidator
{
    public function validate(string $url): bool
    {
        $parsed = parse_url($url);

        // Only HTTPS allowed
        if (($parsed['scheme'] ?? '') !== 'https') {
            return false;
        }

        // No credentials in URL
        if (isset($parsed['user']) || isset($parsed['pass'])) {
            return false;
        }

        return true;
    }
}
```

### Disable Redirects

```php
// SECURE: Prevent redirect-based SSRF
$client = new GuzzleHttp\Client([
    'allow_redirects' => false,
    // Or limit redirects and verify each
    'allow_redirects' => [
        'max' => 3,
        'on_redirect' => function ($request, $response, $uri) {
            if (!$this->isAllowedHost($uri->getHost())) {
                throw new SecurityException('Redirect to disallowed host');
            }
        },
    ],
]);
```

## Severity Classification

| Pattern | Severity | OWASP |
|---------|----------|-------|
| Cloud metadata access | 🔴 Critical | A10 |
| Internal network access | 🔴 Critical | A10 |
| User URL without validation | 🔴 Critical | A10 |
| File/gopher protocol | 🔴 Critical | A10 |
| Webhook URL unvalidated | 🟠 Major | A10 |
| Missing redirect validation | 🟠 Major | A10 |
| Protocol not restricted | 🟡 Minor | A10 |

## Output Format

```markdown
### SSRF: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-918 (Server-Side Request Forgery)

**Issue:**
User-controlled URL is fetched without validation, allowing access to internal services.

**Attack Vector:**
1. Attacker provides URL: `http://169.254.169.254/latest/meta-data/`
2. Server fetches AWS credentials from metadata service
3. Attacker receives IAM credentials

**Code:**
```php
// Vulnerable
$data = file_get_contents($_GET['url']);
```

**Fix:**
```php
// Secure: Validate URL before fetching
if (!$this->urlValidator->isAllowed($url)) {
    throw new SecurityException('URL not allowed');
}
$data = file_get_contents($url);
```

**References:**
- [OWASP SSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Server_Side_Request_Forgery_Prevention_Cheat_Sheet.html)
```
