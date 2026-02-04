---
name: acc-find-resource-leaks
description: Detects resource leaks in PHP code. Finds unclosed file handles, database connections not released, streams not freed, missing finally blocks, temporary files not cleaned.
---

# Resource Leak Detection

Analyze PHP code for resource leak issues.

## Detection Patterns

### 1. Unclosed File Handles

```php
// BUG: File handle not closed
$file = fopen('data.txt', 'r');
$content = fread($file, filesize('data.txt'));
// Missing: fclose($file);

// BUG: Early return without close
$file = fopen($path, 'w');
if (!$valid) {
    return false; // File handle leaked
}
fwrite($file, $data);
fclose($file);
```

### 2. Database Connections Not Released

```php
// BUG: Connection not closed
$pdo = new PDO($dsn, $user, $pass);
$stmt = $pdo->query($sql);
// PDO not unset, may hold connection

// BUG: In connection pool context
$connection = $pool->acquire();
$result = $connection->query($sql);
if ($error) {
    throw new Exception(); // Connection leaked
}
$pool->release($connection);
```

### 3. Streams Not Freed

```php
// BUG: Stream not closed
$stream = fopen('php://temp', 'r+');
fwrite($stream, $data);
// Missing: fclose($stream);

// BUG: cURL handle not closed
$ch = curl_init($url);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
$response = curl_exec($ch);
// Missing: curl_close($ch);
```

### 4. Missing Finally Blocks

```php
// BUG: No finally for cleanup
$lock = $this->acquireLock();
try {
    $this->process();
} catch (Exception $e) {
    $this->log($e);
    throw $e; // Lock not released on exception
}
$this->releaseLock($lock);

// FIXED:
$lock = $this->acquireLock();
try {
    $this->process();
} finally {
    $this->releaseLock($lock);
}
```

### 5. Temporary Files Not Cleaned

```php
// BUG: Temp file not deleted
$tempFile = tempnam(sys_get_temp_dir(), 'prefix_');
file_put_contents($tempFile, $data);
$result = $this->processFile($tempFile);
// Missing: unlink($tempFile);

// BUG: Early return leaves temp file
$temp = tmpfile();
if (!$valid) {
    return null; // Temp file not cleaned
}
```

### 6. Socket/Network Resources

```php
// BUG: Socket not closed
$socket = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
socket_connect($socket, $host, $port);
$data = socket_read($socket, 1024);
// Missing: socket_close($socket);

// BUG: SSH connection not closed
$connection = ssh2_connect($host);
ssh2_auth_password($connection, $user, $pass);
$stream = ssh2_exec($connection, $command);
// Resources not freed
```

### 7. Image/GD Resources

```php
// BUG: Image resource not destroyed
$image = imagecreatefromjpeg($path);
$resized = imagescale($image, 100, 100);
imagejpeg($resized, $output);
// Missing: imagedestroy($image); imagedestroy($resized);
```

### 8. Doctrine/ORM Resources

```php
// BUG: Large result set in memory
$query = $em->createQuery('SELECT u FROM User u');
$users = $query->getResult(); // All in memory

// BUG: Detached entities not cleared
foreach ($largeDataset as $data) {
    $entity = new Entity($data);
    $em->persist($entity);
    $em->flush();
    // Missing: $em->clear(); for large batches
}
```

## Grep Patterns

```bash
# fopen without fclose
Grep: "fopen\([^)]+\)" --glob "**/*.php"
Grep: "fclose\(" --glob "**/*.php"

# curl_init without curl_close
Grep: "curl_init\(" --glob "**/*.php"
Grep: "curl_close\(" --glob "**/*.php"

# try without finally
Grep: "try\s*\{[^}]+\}\s*catch" --glob "**/*.php"

# tempnam/tmpfile usage
Grep: "(tempnam|tmpfile)\(" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Database connection leak | 🔴 Critical |
| File handle in loop | 🔴 Critical |
| Lock not released | 🔴 Critical |
| Single file handle | 🟠 Major |
| Temp file not cleaned | 🟠 Major |
| Image resource | 🟡 Minor |

## Best Practices

### Use try-finally

```php
$resource = acquire();
try {
    process($resource);
} finally {
    release($resource);
}
```

### Use Context Managers (PHP 8.1+)

```php
// Custom destructor-based cleanup
$file = new FileHandler($path);
// Automatically closed on unset/scope exit
```

### Use Transactions Properly

```php
$connection->beginTransaction();
try {
    $this->process();
    $connection->commit();
} catch (Throwable $e) {
    $connection->rollBack();
    throw $e;
}
```

## Output Format

```markdown
### Resource Leak: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [File Handle|Connection|Stream|Lock|Temp File|...]

**Issue:**
Resource acquired but not properly released.

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// With proper cleanup
```
```
