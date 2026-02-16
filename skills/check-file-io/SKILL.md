---
name: acc-check-file-io
description: Audits file I/O patterns in PHP code. Detects full-file reads into memory, missing file locks, temp file cleanup issues, missing stream usage, and insecure file operations.
---

# File I/O Patterns Audit

Analyze PHP code for suboptimal or dangerous file I/O patterns.

## Detection Patterns

### 1. Full File Read Into Memory

```php
// CRITICAL: Entire file loaded into memory
$content = file_get_contents('/path/to/large-file.csv'); // 500MB file → OOM!
$lines = file('/path/to/large-file.csv'); // Loads all lines into array!

// CRITICAL: Reading large file to process line by line
$content = file_get_contents($path);
$lines = explode("\n", $content); // Double memory: content + lines array
foreach ($lines as $line) {
    $this->process($line);
}

// CORRECT: Stream processing
$handle = fopen($path, 'rb');
while (($line = fgets($handle)) !== false) {
    $this->process(trim($line));
}
fclose($handle);

// CORRECT: Generator for large files
function readLines(string $path): \Generator
{
    $handle = fopen($path, 'rb');
    try {
        while (($line = fgets($handle)) !== false) {
            yield trim($line);
        }
    } finally {
        fclose($handle);
    }
}
```

### 2. Missing File Locks

```php
// CRITICAL: Concurrent writes without locking
class FileLogger
{
    public function log(string $message): void
    {
        $handle = fopen($this->path, 'ab');
        fwrite($handle, $message . "\n"); // Race condition with concurrent writers!
        fclose($handle);
    }
}

// CRITICAL: Read-modify-write without lock
$counter = (int) file_get_contents('counter.txt');
$counter++;
file_put_contents('counter.txt', (string) $counter);
// Concurrent requests: both read 5, both write 6 instead of 7

// CORRECT: File locking
$handle = fopen($this->path, 'cb+');
if (flock($handle, LOCK_EX)) {
    $counter = (int) stream_get_contents($handle);
    $counter++;
    ftruncate($handle, 0);
    rewind($handle);
    fwrite($handle, (string) $counter);
    flock($handle, LOCK_UN);
}
fclose($handle);
```

### 3. Temp File Not Cleaned Up

```php
// CRITICAL: Temp file created but never deleted
class PdfGenerator
{
    public function generate(array $data): string
    {
        $tmpFile = tempnam(sys_get_temp_dir(), 'pdf_');
        file_put_contents($tmpFile, $this->render($data));
        $pdf = $this->converter->convert($tmpFile);
        // $tmpFile never deleted! Disk fills up over time
        return $pdf;
    }
}

// CORRECT: Always clean up in finally
class PdfGenerator
{
    public function generate(array $data): string
    {
        $tmpFile = tempnam(sys_get_temp_dir(), 'pdf_');
        try {
            file_put_contents($tmpFile, $this->render($data));
            return $this->converter->convert($tmpFile);
        } finally {
            if (file_exists($tmpFile)) {
                unlink($tmpFile);
            }
        }
    }
}
```

### 4. Missing File Handle Cleanup

```php
// CRITICAL: File handle not closed on exception
class CsvProcessor
{
    public function process(string $path): array
    {
        $handle = fopen($path, 'rb');
        $results = [];
        while (($row = fgetcsv($handle)) !== false) {
            $results[] = $this->transform($row); // If this throws, handle leaks!
        }
        fclose($handle);
        return $results;
    }
}

// CORRECT: try/finally pattern
class CsvProcessor
{
    public function process(string $path): array
    {
        $handle = fopen($path, 'rb');
        try {
            $results = [];
            while (($row = fgetcsv($handle)) !== false) {
                $results[] = $this->transform($row);
            }
            return $results;
        } finally {
            fclose($handle);
        }
    }
}
```

### 5. SplFileObject Not Used for CSV

```php
// ANTIPATTERN: Manual CSV parsing
$handle = fopen($path, 'rb');
$header = fgetcsv($handle);
while ($row = fgetcsv($handle)) {
    $data = array_combine($header, $row);
}
fclose($handle);

// CORRECT: SplFileObject with generator
function readCsv(string $path): \Generator
{
    $file = new \SplFileObject($path, 'rb');
    $file->setFlags(\SplFileObject::READ_CSV | \SplFileObject::SKIP_EMPTY);
    $header = $file->fgetcsv();
    foreach ($file as $row) {
        if ($row === [null]) continue;
        yield array_combine($header, $row);
    }
}
```

### 6. Unsafe File Path Construction

```php
// CRITICAL: Path traversal + race condition
$path = '/uploads/' . $request->get('filename');
if (file_exists($path)) {        // Check
    $content = file_get_contents($path); // Use — TOCTOU!
}

// CORRECT: Validate and use realpath
$basePath = realpath('/uploads');
$fullPath = realpath('/uploads/' . basename($request->get('filename')));
if ($fullPath === false || !str_starts_with($fullPath, $basePath)) {
    throw new SecurityException('Invalid file path');
}
$content = file_get_contents($fullPath);
```

### 7. Writing Large Output Without Streaming

```php
// CRITICAL: Building entire response in memory
class ExportController
{
    public function export(): Response
    {
        $data = $this->repository->findAll(); // 100K rows
        $csv = '';
        foreach ($data as $row) {
            $csv .= implode(',', $row) . "\n"; // String grows to 500MB
        }
        return new Response($csv);
    }
}

// CORRECT: Streaming response
class ExportController
{
    public function export(): StreamedResponse
    {
        return new StreamedResponse(function () {
            $handle = fopen('php://output', 'wb');
            foreach ($this->repository->findAllIterable() as $row) {
                fputcsv($handle, $row);
                flush();
            }
            fclose($handle);
        }, 200, ['Content-Type' => 'text/csv']);
    }
}
```

## Grep Patterns

```bash
# Full file reads
Grep: "file_get_contents\(|file\(" --glob "**/*.php"

# Missing file locks
Grep: "fwrite\(|file_put_contents\(" --glob "**/*.php"
Grep: "flock\(" --glob "**/*.php"

# Temp files
Grep: "tempnam\(|sys_get_temp_dir\(|tmpfile\(" --glob "**/*.php"
Grep: "unlink\(.*tmp" --glob "**/*.php"

# File handles without finally
Grep: "fopen\(" --glob "**/*.php"
Grep: "finally.*fclose" --glob "**/*.php"

# CSV processing
Grep: "fgetcsv\(|SplFileObject" --glob "**/*.php"

# String concatenation for output
Grep: "\\\$.*\.=.*\\\\n|\\\$.*\.= implode" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Full file read of unbounded size | 🔴 Critical |
| File handle leak on exception | 🔴 Critical |
| Write without lock (shared file) | 🟠 Major |
| Temp file not cleaned up | 🟠 Major |
| Building large string in memory | 🟠 Major |
| Missing SplFileObject for CSV | 🟡 Minor |

## Output Format

```markdown
### File I/O: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Impact:** [Memory/Performance/Data integrity]

**Issue:**
[Description of the file I/O problem]

**Code:**
```php
// Problematic pattern
```

**Fix:**
```php
// Stream-based / locked / cleaned-up pattern
```

**Expected Improvement:**
Memory: 500MB → 4KB (streaming)
```
