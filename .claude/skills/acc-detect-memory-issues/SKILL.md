---
name: acc-detect-memory-issues
description: Detects memory issues in PHP code. Finds large arrays in memory, missing generators, memory leaks, unbounded data loading, inefficient data structures.
---

# Memory Issue Detection

Analyze PHP code for memory usage problems.

## Detection Patterns

### 1. Large Arrays in Memory

```php
// MEMORY HOG: Loading entire table
$users = $repository->findAll(); // 1M users = OOM
foreach ($users as $user) {
    process($user);
}

// MEMORY HOG: Building large array
$data = [];
foreach ($hugeDataset as $item) {
    $data[] = transform($item); // Array grows unbounded
}

// FIXED: Use generator
function processUsers(Repository $repo): Generator {
    foreach ($repo->iterate() as $user) {
        yield transform($user);
    }
}
```

### 2. Missing Generators

```php
// MEMORY HOG: Entire file in memory
$lines = file('large-file.txt'); // 1GB file = OOM
foreach ($lines as $line) {
    process($line);
}

// FIXED: Generator-based reading
function readLines(string $path): Generator {
    $handle = fopen($path, 'r');
    while (($line = fgets($handle)) !== false) {
        yield $line;
    }
    fclose($handle);
}

// MEMORY HOG: Collect then process
function getAllProducts(): array {
    $products = [];
    foreach ($this->fetchBatch() as $batch) {
        $products = array_merge($products, $batch);
    }
    return $products; // Entire dataset
}
```

### 3. Unbounded Data Loading

```php
// MEMORY HOG: No LIMIT
$logs = $repository->findBy(['level' => 'error']);
// Could be millions of records

// MEMORY HOG: Pagination loading all
$page = 1;
$allItems = [];
do {
    $items = $api->fetch($page++);
    $allItems = array_merge($allItems, $items);
} while (!empty($items));

// FIXED: Process in batches
$page = 1;
do {
    $items = $api->fetch($page++);
    foreach ($items as $item) {
        yield $item;
    }
} while (!empty($items));
```

### 4. Object Graph Loading

```php
// MEMORY HOG: Deep object graph
$department = $repo->find($id);
$employees = $department->getEmployees(); // Loads all
foreach ($employees as $emp) {
    $projects = $emp->getProjects(); // Loads more
    foreach ($projects as $project) {
        $tasks = $project->getTasks(); // Even more
    }
}
// Entire object graph in memory
```

### 5. String Concatenation in Loop

```php
// MEMORY HOG: String grows each iteration
$output = '';
foreach ($lines as $line) {
    $output .= $line . "\n"; // Creates new string each time
}

// FIXED: Use array and implode
$parts = [];
foreach ($lines as $line) {
    $parts[] = $line;
}
$output = implode("\n", $parts);

// BETTER: Use stream
$handle = fopen('output.txt', 'w');
foreach ($lines as $line) {
    fwrite($handle, $line . "\n");
}
```

### 6. Image/Binary Processing

```php
// MEMORY HOG: Entire image in memory
$image = file_get_contents('large-image.jpg');
$processed = processImage($image);
file_put_contents('output.jpg', $processed);

// MEMORY HOG: Multiple image resources
foreach ($images as $path) {
    $img = imagecreatefromjpeg($path);
    $resized = imagescale($img, 100, 100);
    imagejpeg($resized, $outPath);
    // Missing: imagedestroy($img); imagedestroy($resized);
}
```

### 7. Cache/Buffer Growth

```php
// MEMORY LEAK: Cache grows unbounded
class Cache {
    private array $data = [];

    public function get(string $key): mixed {
        if (!isset($this->data[$key])) {
            $this->data[$key] = $this->load($key);
            // Never evicted
        }
        return $this->data[$key];
    }
}

// MEMORY LEAK: Event listeners accumulate
$dispatcher->addListener('event', function() {
    // New closure each time
});
```

### 8. Doctrine Batch Processing

```php
// MEMORY HOG: Doctrine identity map
foreach ($repository->findAll() as $entity) {
    $entity->process();
    $em->flush(); // Identity map keeps all entities
}

// FIXED: Clear periodically
$batchSize = 100;
$i = 0;
foreach ($repository->iterate() as $entity) {
    $entity->process();
    if (++$i % $batchSize === 0) {
        $em->flush();
        $em->clear(); // Free memory
    }
}
$em->flush();
```

### 9. Session/Global Storage

```php
// MEMORY HOG: Large session data
$_SESSION['search_results'] = $hugeArray;

// MEMORY HOG: Static cache
class Service {
    private static array $cache = [];

    public static function process($item) {
        self::$cache[$item->getId()] = $item;
        // Never cleared
    }
}
```

## Grep Patterns

```bash
# file() usage
Grep: "file\([^)]+\)" --glob "**/*.php"

# findAll without iterate
Grep: "->findAll\(\)" --glob "**/*.php"

# array_merge in loop
Grep: "foreach.*array_merge" --glob "**/*.php"

# String concatenation in loop
Grep: 'foreach.*\.=' --glob "**/*.php"

# Static array properties
Grep: "private static array" --glob "**/*.php"
```

## Memory Estimation

| Operation | Memory Usage |
|-----------|--------------|
| 1M integers in array | ~32 MB |
| 1M strings (avg 50 chars) | ~250 MB |
| 1M Doctrine entities | ~500 MB - 2 GB |
| 1 GB file via file() | ~1 GB + overhead |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Unbounded data loading | 🔴 Critical |
| Full table in memory | 🔴 Critical |
| Missing imagedestroy | 🟠 Major |
| Static cache without limit | 🟠 Major |
| String concat in loop | 🟡 Minor |

## Output Format

```markdown
### Memory Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Estimated Memory:** ~500 MB for 100K records

**Issue:**
[Description of the memory problem]

**Code:**
```php
// Memory-intensive code
```

**Fix:**
```php
// Memory-efficient alternative
```

**Memory Reduction:**
Before: ~500 MB peak
After: ~10 MB peak (streaming)
```

## When This Is Acceptable

- **CLI commands/workers** — Console commands may legitimately use more memory for batch processing
- **Known bounded datasets** — Loading all items when the table is guaranteed small (e.g., countries, currencies)
- **Cached data** — Large arrays that are built once and cached for reuse

### False Positive Indicators
- Code is in a console command or queue worker with explicit memory management
- Collection is loaded from a known-small dataset (< 1000 records by business rule)
- Large array is built for cache warming with explicit garbage collection
