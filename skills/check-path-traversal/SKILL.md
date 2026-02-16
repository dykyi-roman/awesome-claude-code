---
name: acc-check-path-traversal
description: Analyzes PHP code for path traversal vulnerabilities. Detects directory traversal, file inclusion with user input, missing path validation, symlink attacks.
---

# Path Traversal Security Check

Analyze PHP code for path/directory traversal vulnerabilities (OWASP A01:2021).

## Detection Patterns

### 1. File Operations with User Input

```php
// CRITICAL: Direct path from user
$content = file_get_contents($_GET['file']);
$content = file_get_contents('/uploads/' . $_GET['filename']);

// CRITICAL: File reading
$data = file($_POST['path']);
$lines = readfile($request->input('document'));

// CRITICAL: File writing
file_put_contents('/reports/' . $_GET['name'], $content);

// CRITICAL: File deletion
unlink('/uploads/' . $_POST['file']);
unlink($basePath . $userInput);
```

### 2. Include/Require with User Input

```php
// CRITICAL: Local File Inclusion (LFI)
include $_GET['page'];
include 'templates/' . $_GET['template'] . '.php';
require $request->input('module');

// CRITICAL: Remote File Inclusion (RFI) if allow_url_include=On
include 'http://' . $_GET['host'] . '/script.php';

// CRITICAL: Dynamic class loading
$class = $_GET['type'];
require "classes/{$class}.php";
```

### 3. Directory Traversal Patterns

```php
// CRITICAL: Basic traversal
$file = '/var/www/uploads/' . $_GET['name'];
// Input: ../../../etc/passwd
// Result: /var/www/uploads/../../../etc/passwd = /etc/passwd

// CRITICAL: Encoded traversal
// Input: ..%2F..%2F..%2Fetc/passwd (URL encoded)
// Input: ..%252f..%252f..%252fetc/passwd (double encoded)

// CRITICAL: Null byte injection (PHP < 5.3.4)
$file = '/templates/' . $_GET['name'] . '.php';
// Input: ../../../etc/passwd%00
// Result: /templates/../../../etc/passwd (null terminates string)
```

### 4. File Upload Path Manipulation

```php
// CRITICAL: User-controlled upload path
$uploadDir = '/uploads/' . $_POST['folder'] . '/';
move_uploaded_file($tmp, $uploadDir . $filename);

// CRITICAL: Original filename used directly
$filename = $_FILES['upload']['name'];
move_uploaded_file($tmp, "/uploads/{$filename}");
// Filename: ../../../var/www/html/shell.php
```

### 5. Archive Extraction (Zip Slip)

```php
// CRITICAL: Zip extraction without path validation
$zip = new ZipArchive();
$zip->open($_FILES['archive']['tmp_name']);
$zip->extractTo('/uploads/');
// Archive may contain: ../../var/www/html/malicious.php

// CRITICAL: Tar extraction
$phar = new PharData($uploadedFile);
$phar->extractTo('/uploads/');
```

### 6. Symlink Attacks

```php
// CRITICAL: Following symlinks
$realPath = '/uploads/' . $_GET['file'];
$content = file_get_contents($realPath);
// Attacker creates symlink: uploads/secret -> /etc/passwd

// CRITICAL: Checking existence without symlink validation
if (file_exists($userPath)) {
    include $userPath;
}
```

### 7. Image/File Processing

```php
// CRITICAL: Image path from user
$image = imagecreatefromjpeg('/images/' . $_GET['photo']);

// CRITICAL: PDF generation with user paths
$pdf->image('/assets/' . $_POST['logo']);

// CRITICAL: File download
$filepath = '/downloads/' . $_GET['file'];
header('Content-Disposition: attachment; filename="' . basename($filepath) . '"');
readfile($filepath);
```

### 8. Log File Access

```php
// CRITICAL: Log file path manipulation
$logFile = '/var/log/' . $_GET['app'] . '.log';
$content = file_get_contents($logFile);

// CRITICAL: Log viewing
$logPath = "/logs/{$_GET['date']}/app.log";
return file($logPath);
```

### 9. Configuration File Access

```php
// CRITICAL: Config path from user
$config = parse_ini_file('/config/' . $_GET['env'] . '.ini');

// CRITICAL: YAML loading
$yaml = yaml_parse_file('/config/' . $_POST['file']);
```

### 10. Backup/Export Path

```php
// CRITICAL: Backup destination from user
$backupPath = $_POST['backup_path'] . '/backup.sql';
file_put_contents($backupPath, $sqlDump);

// CRITICAL: Export path
$exportDir = '/exports/' . $_GET['folder'];
mkdir($exportDir, 0777, true);
```

## Grep Patterns

```bash
# File operations with variable
Grep: "(file_get_contents|file_put_contents|fopen|readfile|file)\s*\([^)]*\\\$" --glob "**/*.php"

# Include/require with variable
Grep: "(include|require|include_once|require_once)\s+[^;]*\\\$" --glob "**/*.php"

# Path concatenation
Grep: "(/uploads/|/downloads/|/files/|/images/).*\\\$" --glob "**/*.php"

# Unlink/delete with variable
Grep: "(unlink|rmdir)\s*\([^)]*\\\$" --glob "**/*.php"

# Archive extraction
Grep: "(extractTo|extract)\s*\(" --glob "**/*.php"

# move_uploaded_file
Grep: "move_uploaded_file\s*\(" --glob "**/*.php"
```

## Secure Patterns

### Validate with realpath()

```php
// SECURE: Validate path is within allowed directory
final class SafeFileReader
{
    public function __construct(
        private readonly string $baseDir,
    ) {}

    public function read(string $filename): string
    {
        $basePath = realpath($this->baseDir);
        $fullPath = realpath($this->baseDir . '/' . $filename);

        if ($fullPath === false) {
            throw new FileNotFoundException('File not found');
        }

        if (!str_starts_with($fullPath, $basePath . '/')) {
            throw new SecurityException('Path traversal detected');
        }

        return file_get_contents($fullPath);
    }
}
```

### Basename for Filenames

```php
// SECURE: Extract only filename, no path
$filename = basename($_GET['file']);
$filepath = '/uploads/' . $filename;

// SECURE: Remove path separators
$safeName = str_replace(['/', '\\', '..'], '', $_GET['file']);
```

### Whitelist Approach

```php
// SECURE: Whitelist allowed files
final class TemplateLoader
{
    private const ALLOWED_TEMPLATES = [
        'header',
        'footer',
        'sidebar',
        'content',
    ];

    public function load(string $name): string
    {
        if (!in_array($name, self::ALLOWED_TEMPLATES, true)) {
            throw new InvalidArgumentException('Invalid template');
        }

        return file_get_contents("/templates/{$name}.php");
    }
}
```

### ID-Based File Access

```php
// SECURE: Use database ID instead of filename
final class DocumentController
{
    public function download(int $documentId): Response
    {
        $document = $this->repository->find($documentId);

        if ($document === null) {
            throw new NotFoundException();
        }

        // User can't manipulate stored path
        return $this->file($document->getStoredPath());
    }
}
```

### Secure Archive Extraction

```php
// SECURE: Validate paths before extraction
final class SafeZipExtractor
{
    public function extract(string $zipPath, string $destDir): void
    {
        $zip = new ZipArchive();
        $zip->open($zipPath);

        $destDir = realpath($destDir);

        for ($i = 0; $i < $zip->numFiles; $i++) {
            $filename = $zip->getNameIndex($i);
            $targetPath = $destDir . '/' . $filename;

            // Resolve path
            $realTarget = realpath(dirname($targetPath));
            if ($realTarget === false) {
                $realTarget = $destDir;
            }

            // Validate within destination
            if (!str_starts_with($realTarget, $destDir)) {
                throw new SecurityException("Zip slip detected: {$filename}");
            }
        }

        $zip->extractTo($destDir);
        $zip->close();
    }
}
```

### Disable Symlinks

```php
// SECURE: Check if path is symlink
final class SafeFileHandler
{
    public function read(string $path): string
    {
        if (is_link($path)) {
            throw new SecurityException('Symlinks not allowed');
        }

        $realPath = realpath($path);
        if ($realPath === false || is_link($realPath)) {
            throw new SecurityException('Invalid path');
        }

        return file_get_contents($realPath);
    }
}
```

### Input Sanitization

```php
// SECURE: Remove dangerous characters
final class PathSanitizer
{
    public function sanitize(string $input): string
    {
        // Remove null bytes
        $input = str_replace("\0", '', $input);

        // Remove path traversal sequences
        $input = str_replace(['../', '..\\', '..'], '', $input);

        // Remove URL encoding
        $input = urldecode($input);
        $input = str_replace(['../', '..\\', '..'], '', $input);

        // Only allow alphanumeric, dash, underscore, dot
        if (!preg_match('/^[\w\-\.]+$/', $input)) {
            throw new InvalidArgumentException('Invalid characters in path');
        }

        return $input;
    }
}
```

## Severity Classification

| Pattern | Severity | CWE |
|---------|----------|-----|
| include/require with user input | 🔴 Critical | CWE-98 |
| File read with user path | 🔴 Critical | CWE-22 |
| File write with user path | 🔴 Critical | CWE-22 |
| Zip extraction without validation | 🔴 Critical | CWE-22 |
| Upload path manipulation | 🟠 Major | CWE-22 |
| Missing realpath validation | 🟠 Major | CWE-22 |
| Symlink following | 🟡 Minor | CWE-59 |

## Output Format

```markdown
### Path Traversal: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-22 (Path Traversal)

**Issue:**
User input is used in file path without validation, allowing access to arbitrary files.

**Attack Vector:**
1. Input: `../../../etc/passwd`
2. Path becomes: `/uploads/../../../etc/passwd`
3. Resolves to: `/etc/passwd`
4. Attacker reads system files

**Code:**
```php
// Vulnerable
$content = file_get_contents('/uploads/' . $_GET['file']);
```

**Fix:**
```php
// Secure: Validate path within allowed directory
$basePath = realpath('/uploads');
$fullPath = realpath('/uploads/' . $_GET['file']);

if ($fullPath === false || !str_starts_with($fullPath, $basePath . '/')) {
    throw new SecurityException('Invalid path');
}

$content = file_get_contents($fullPath);
```

**References:**
- [OWASP Path Traversal](https://owasp.org/www-community/attacks/Path_Traversal)
```
