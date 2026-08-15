---
name: estimate-complexity
description: Estimates algorithm complexity in PHP code. Analyzes time and space complexity, detects O(n²) algorithms, exponential growth patterns, inefficient data structures.
---

# Algorithm Complexity Estimation

Analyze PHP code to estimate time and space complexity.

## Complexity Patterns

### 1. O(n²) Algorithms

```php
// O(n²): Nested loop over same collection
foreach ($items as $i => $item1) {
    foreach ($items as $j => $item2) {
        if ($i !== $j && $item1->matches($item2)) {
            // Comparison
        }
    }
}

// O(n²): Array operations in loop
$result = [];
foreach ($items as $item) {
    if (!in_array($item, $result)) { // O(n) search
        $result[] = $item;
    }
}

// O(n): Using hash set
$seen = [];
$result = [];
foreach ($items as $item) {
    $key = $item->getKey();
    if (!isset($seen[$key])) {
        $seen[$key] = true;
        $result[] = $item;
    }
}
```

### 2. Exponential Growth O(2^n)

```php
// O(2^n): Naive Fibonacci
function fib(int $n): int {
    if ($n <= 1) return $n;
    return fib($n - 1) + fib($n - 2);
}

// O(n): Memoized
function fibMemo(int $n, array &$memo = []): int {
    if ($n <= 1) return $n;
    if (!isset($memo[$n])) {
        $memo[$n] = fibMemo($n - 1, $memo) + fibMemo($n - 2, $memo);
    }
    return $memo[$n];
}

// O(2^n): Subsets generation
function subsets(array $set): array {
    if (empty($set)) return [[]];
    $first = array_shift($set);
    $rest = subsets($set);
    $withFirst = array_map(fn($s) => array_merge([$first], $s), $rest);
    return array_merge($rest, $withFirst);
}
```

### 3. O(n!) Factorial

```php
// O(n!): Permutations
function permute(array $arr): array {
    if (count($arr) <= 1) return [$arr];
    $perms = [];
    foreach ($arr as $i => $item) {
        $rest = array_values(array_diff_key($arr, [$i => true]));
        foreach (permute($rest) as $perm) {
            $perms[] = array_merge([$item], $perm);
        }
    }
    return $perms;
}
```

### 4. Inefficient String Operations

```php
// NOT quadratic: `.=` is amortised O(1) in PHP
$result = '';
foreach ($lines as $line) {
    $result .= $line; // realloc in place while refcount === 1
}
// Total: O(total output length). Do NOT report this as O(n²).

// O(n²): concatenation that COPIES on every iteration
$result = '';
foreach ($lines as $line) {
    $result = $result . $line;      // same, still amortised O(1)
    $log[] = $result;               // ← THIS is the problem: n snapshots of a
                                    //   growing string → O(n²) memory and time
}

// O(n²): rebuilding a string through a function that returns a copy
foreach ($lines as $line) {
    $result = str_replace('a', 'b', $result . $line); // full re-scan each pass
}
```

**Rule:** `.=` alone is not a complexity smell. Flag it only when each intermediate
value is retained, re-scanned, or passed through a string function every iteration.

### 5. Inefficient Array Operations

```php
// O(n²): array_merge in loop
$result = [];
foreach ($batches as $batch) {
    $result = array_merge($result, $batch); // O(n) each time
}

// O(n): Spread operator
$result = array_merge(...$batches);

// O(n²): array_unshift in loop
$result = [];
foreach ($items as $item) {
    array_unshift($result, $item); // O(n) shift
}

// O(n): Build then reverse
$result = [];
foreach ($items as $item) {
    $result[] = $item;
}
$result = array_reverse($result);
```

### 6. Inefficient Search

```php
// O(n): Linear search each time
foreach ($queries as $query) {
    foreach ($items as $item) {
        if ($item->matches($query)) {
            $results[] = $item;
            break;
        }
    }
}
// Total: O(q*n)

// O(q + n): Build index first
$index = [];
foreach ($items as $item) {
    $index[$item->getKey()] = $item;
}
foreach ($queries as $query) {
    if (isset($index[$query])) {
        $results[] = $index[$query];
    }
}
```

### 7. Recursive Depth

```php
// O(n) stack depth: Linear recursion
function process(array $items): void {
    if (empty($items)) return;
    $first = array_shift($items);
    handle($first);
    process($items); // Stack depth = n
}

// O(log n) stack depth: Divide and conquer
function processTree(Node $node): void {
    if (!$node) return;
    process($node->value);
    processTree($node->left);
    processTree($node->right);
}
```

### 8. Space Complexity

```php
// O(n) space: Building result array
function transform(array $items): array {
    $result = [];
    foreach ($items as $item) {
        $result[] = process($item);
    }
    return $result;
}

// O(1) space: Generator
function transformGenerator(array $items): Generator {
    foreach ($items as $item) {
        yield process($item);
    }
}

// O(n²) space: Matrix
$matrix = [];
for ($i = 0; $i < $n; $i++) {
    $matrix[$i] = array_fill(0, $n, 0);
}
```

## Complexity Quick Reference

| Pattern | Time | Space |
|---------|------|-------|
| Simple loop | O(n) | O(1) |
| Nested loop | O(n²) | O(1) |
| Binary search | O(log n) | O(1) |
| Merge sort | O(n log n) | O(n) |
| Hash table lookup | O(1) avg | O(n) |
| in_array | O(n) | O(1) |
| isset/array key | O(1) | O(1) |

## Grep Patterns

```bash
These are candidate-narrowing greps — then Read the hit to confirm. A zero result is NOT
proof the code is clean; it usually means the construct spans lines the pattern did not cover.

```bash
# Nested foreach — spans lines, so --multiline is required (no dotall: `.` must not eat newlines)
Grep: "foreach[^\n]*\{[\s\S]{0,400}?foreach" --glob "**/*.php" --multiline

# in_array / array_search inside a loop body (two-pass: find the loop, then Read it)
Grep: "in_array|array_search" --glob "**/*.php"

# array_merge / array_unshift in a loop — genuinely O(n²)
Grep: "array_merge|array_unshift" --glob "**/*.php"

# Recursive function — ripgrep's Rust regex has NO backreferences, so match the
# declaration first and confirm self-recursion by reading the body
Grep: "^\s*(public|private|protected|static|final|\s)*function\s+\w+" --glob "**/*.php"
```

Not listed on purpose: `foreach.*\.=`. String concatenation in a loop is amortised O(1) —
see section 4. Grepping for it only produces false positives.

## Severity Classification

| Complexity | Dataset Size | Severity |
|------------|--------------|----------|
| O(n²) | > 1000 | 🔴 Critical |
| O(n²) | < 100 | 🟡 Minor |
| O(2^n) | > 20 | 🔴 Critical |
| O(n log n) | Any | ✅ Acceptable |
| O(n) | Any | ✅ Good |
| O(1) | Any | ✅ Optimal |

## Output Format

```markdown
### Algorithm Complexity: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`

**Current Complexity:**
- Time: O(n²)
- Space: O(n)

**Issue:**
[Description of the complexity problem]

**Code:**
```php
// Current algorithm
```

**Optimization:**
```php
// Optimized algorithm
```

**Optimized Complexity:**
- Time: O(n)
- Space: O(n)

**Performance Impact:**
For n = 10,000:
- Before: ~100M operations
- After: ~10K operations
```
