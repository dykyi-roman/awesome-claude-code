---
name: acc-find-infinite-loops
description: Detects infinite loop risks in PHP code. Finds missing break conditions, incorrect loop variables, unbounded recursion, circular references.
---

# Infinite Loop Detection

Analyze PHP code for potential infinite loops and unbounded execution.

## Detection Patterns

### 1. Missing Break Conditions

```php
// BUG: No exit condition
while (true) {
    $item = $queue->pop();
    process($item);
    // No break when queue is empty
}

// BUG: Condition never changes
$running = true;
while ($running) {
    doWork();
    // $running never set to false
}

// BUG: Break inside nested condition
while ($items) {
    foreach ($items as $item) {
        if ($item->isDone()) {
            break; // Only breaks inner loop
        }
    }
}
```

### 2. Incorrect Loop Variable Modification

```php
// BUG: Wrong variable incremented
for ($i = 0; $i < count($items); $j++) { // Should be $i++
    process($items[$i]);
}

// BUG: Variable modified in wrong direction
for ($i = 10; $i > 0; $i++) { // Should be $i--
    process($i);
}

// BUG: Loop variable reset
$i = 0;
while ($i < 10) {
    if ($condition) {
        $i = 0; // Resets counter
    }
    $i++;
}
```

### 3. Unbounded Recursion

```php
// BUG: No base case
function factorial(int $n): int
{
    return $n * factorial($n - 1); // Never stops
}

// BUG: Base case unreachable
function traverse(Node $node): void
{
    $this->traverse($node->getNext()); // What if getNext returns self?
    // Missing: if ($node === null) return;
}

// BUG: Mutual recursion
function a($n) { return b($n); }
function b($n) { return a($n); } // Infinite cycle
```

### 4. Circular References

```php
// BUG: Circular linked list traversal
while ($node !== null) {
    $node = $node->next; // What if list is circular?
}

// BUG: Object graph cycle
function serialize($obj, $visited = []): string
{
    foreach ($obj->getRelations() as $rel) {
        $result .= serialize($rel); // May revisit objects
    }
}

// FIXED:
function serialize($obj, array &$visited = []): string
{
    if (in_array($obj, $visited, true)) {
        return '[circular]';
    }
    $visited[] = $obj;
    // ...
}
```

### 5. Event/Listener Loops

```php
// BUG: Event triggers itself
class UserUpdatedListener
{
    public function handle(UserUpdated $event): void
    {
        $user = $event->getUser();
        $user->touch(); // Triggers another UserUpdated event
    }
}

// BUG: Message queue requeue loop
public function handle(Message $message): void
{
    try {
        $this->process($message);
    } catch (Exception $e) {
        $this->queue->publish($message); // Requeues failed message infinitely
    }
}
```

### 6. Retry Without Limit

```php
// BUG: Infinite retry
function fetch(string $url): string
{
    while (true) {
        try {
            return $this->httpClient->get($url);
        } catch (Exception $e) {
            sleep(1);
            // No max retries, infinite loop on persistent failure
        }
    }
}

// FIXED:
function fetch(string $url, int $maxRetries = 3): string
{
    $attempts = 0;
    while ($attempts < $maxRetries) {
        try {
            return $this->httpClient->get($url);
        } catch (Exception $e) {
            $attempts++;
            if ($attempts >= $maxRetries) {
                throw $e;
            }
            sleep(1);
        }
    }
}
```

### 7. Generator Infinite Yield

```php
// BUG: Generator never ends
function allNumbers(): Generator
{
    $i = 0;
    while (true) {
        yield $i++;
        // Fine for generators, but consuming code may not limit
    }
}

// Usage BUG:
foreach (allNumbers() as $n) {
    echo $n; // Infinite loop
}
```

### 8. Database Pagination Without Limit

```php
// BUG: Potentially infinite
$offset = 0;
while (true) {
    $batch = $repository->findBy([], null, 100, $offset);
    if (empty($batch)) {
        break;
    }
    process($batch);
    // Missing: $offset += 100;
}
```

## Grep Patterns

```bash
# while(true) without break
Grep: "while\s*\(\s*true\s*\)" --glob "**/*.php"

# Recursion
Grep: "function\s+(\w+)\([^)]*\)[^{]*\{[^}]*\1\s*\(" --glob "**/*.php"

# for loop with wrong increment
Grep: "for\s*\([^;]+;\s*\$\w+\s*[<>]\s*[^;]+;\s*\$(?!\1)" --glob "**/*.php"

# while without modification
Grep: "while\s*\(\s*\$\w+\s*\)" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Infinite retry without limit | 🔴 Critical |
| Missing recursion base case | 🔴 Critical |
| Wrong loop variable | 🔴 Critical |
| Circular reference traversal | 🟠 Major |
| Event self-triggering | 🟠 Major |
| while(true) without clear exit | 🟠 Major |

## Prevention Patterns

### Always Use Limits

```php
const MAX_ITERATIONS = 1000;

$iterations = 0;
while ($condition && $iterations < self::MAX_ITERATIONS) {
    // ...
    $iterations++;
}

if ($iterations >= self::MAX_ITERATIONS) {
    throw new RuntimeException('Max iterations exceeded');
}
```

### Track Visited Nodes

```php
function traverse($node, array &$visited = []): void
{
    $id = spl_object_id($node);
    if (isset($visited[$id])) {
        return;
    }
    $visited[$id] = true;
    // ...
}
```

### Recursion Depth Limit

```php
function process($data, int $depth = 0): mixed
{
    if ($depth > 100) {
        throw new RuntimeException('Max recursion depth');
    }
    return process($child, $depth + 1);
}
```

## Output Format

```markdown
### Infinite Loop Risk: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Missing Break|Wrong Variable|Unbounded Recursion|...]

**Issue:**
[Description of how infinite loop can occur]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// With proper termination
```

**Trigger Condition:**
[When this infinite loop would occur]
```
