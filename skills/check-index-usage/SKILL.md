---
name: acc-check-index-usage
description: Detects missing database indexes in PHP code. Identifies unindexed WHERE/JOIN columns, incorrect composite index order, covering index opportunities, and index-defeating patterns.
---

# Database Index Usage Audit

Analyze PHP code for missing or suboptimal database index usage.

## Detection Patterns

### 1. WHERE Clause Without Index

```php
// CRITICAL: Filtering on unindexed column
$qb->select('o')
    ->from(Order::class, 'o')
    ->where('o.status = :status')          // Is 'status' indexed?
    ->andWhere('o.createdAt > :date')      // Is 'createdAt' indexed?
    ->setParameter('status', 'pending')
    ->setParameter('date', $date);

// Detection: Extract columns from WHERE, check entity for indexes
```

### 2. JOIN Column Without Index

```php
// CRITICAL: JOIN on non-indexed foreign key
$qb->select('o', 'i')
    ->from(Order::class, 'o')
    ->join('o.items', 'i')                 // Is foreign key indexed?
    ->where('i.productId = :productId');   // Is productId indexed?

// Doctrine annotation check:
// @ORM\ManyToOne without @ORM\Index on the join column
```

### 3. Incorrect Composite Index Order

```php
// Entity mapping:
#[ORM\Index(columns: ['created_at', 'status'])]  // Index order

// Query:
->where('o.status = :status')          // Equality first
->andWhere('o.createdAt > :date')      // Range second
// WRONG ORDER! Should be Index(columns: ['status', 'created_at'])
// Equality columns first, then range columns
```

### 4. Function on Indexed Column (Index Defeat)

```php
// CRITICAL: Function prevents index usage
$qb->where('YEAR(o.createdAt) = :year');       // Index on createdAt NOT used!
$qb->where('LOWER(u.email) = :email');          // Index on email NOT used!
$qb->where('LENGTH(u.name) > :len');            // Index on name NOT used!

// CORRECT: Rewrite to use index
$qb->where('o.createdAt >= :yearStart AND o.createdAt < :yearEnd');
$qb->where('u.email = :email'); // Store normalized, query normalized
```

### 5. LIKE with Leading Wildcard

```php
// CRITICAL: Leading wildcard prevents index usage
$qb->where("u.name LIKE :name")
    ->setParameter('name', "%{$search}%");      // Full table scan!

// Partially indexed:
$qb->where("u.name LIKE :name")
    ->setParameter('name', "{$search}%");        // Can use index (prefix match)

// For full-text search, use dedicated solution:
// Full-text index, Elasticsearch, or application-level search
```

### 6. OR Conditions Defeating Index

```php
// VULNERABLE: OR can prevent index usage
$qb->where('o.status = :s1 OR o.priority = :p1');
// Unless BOTH status AND priority are indexed, this may full-scan

// CORRECT: Use UNION or separate queries for complex OR
$qb->where('o.status = :s1')
    ->orWhere('o.priority = :p1');
// Consider: separate queries + merge results if performance critical
```

### 7. Missing Index on Foreign Key

```php
// Doctrine entity without index on FK
#[ORM\Entity]
class OrderItem
{
    #[ORM\ManyToOne(targetEntity: Order::class)]
    #[ORM\JoinColumn(name: 'order_id')]
    private Order $order;
    // 'order_id' column may not be indexed!
    // MySQL InnoDB auto-indexes FKs, but PostgreSQL does NOT
}
```

### 8. ORDER BY Without Index

```php
// SLOW: Sorting large result set without index
$qb->select('o')
    ->from(Order::class, 'o')
    ->where('o.userId = :userId')
    ->orderBy('o.createdAt', 'DESC')    // Is (userId, createdAt) composite index?
    ->setMaxResults(20);
// Without composite index: fetch ALL user orders, sort in memory, return 20
// With composite index: read 20 rows directly from index
```

## Grep Patterns

```bash
# WHERE conditions (columns to check for indexes)
Grep: "->where\(|->andWhere\(|->orWhere\(" --glob "**/*Repository*.php"
Grep: "WHERE.*=|WHERE.*LIKE|WHERE.*IN" --glob "**/*.php"

# JOIN columns
Grep: "->join\(|->leftJoin\(|->innerJoin\(" --glob "**/*Repository*.php"
Grep: "JOIN.*ON" --glob "**/*.php"

# Functions on columns (index defeat)
Grep: "YEAR\(|MONTH\(|DATE\(|LOWER\(|UPPER\(|LENGTH\(" --glob "**/*.php"

# LIKE with variable
Grep: "LIKE.*%.*\\\$|LIKE.*:.*\n.*%\\\$" --glob "**/*.php"

# ORDER BY
Grep: "->orderBy\(|ORDER BY" --glob "**/*Repository*.php"

# Entity index annotations
Grep: "#\[ORM\\\\Index|@ORM\\\\Index|@Index" --glob "**/Domain/**/*.php"

# Foreign keys
Grep: "ManyToOne|OneToMany|ManyToMany|JoinColumn" --glob "**/Domain/**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| WHERE on unindexed column (large table) | 🔴 Critical |
| JOIN without FK index (PostgreSQL) | 🔴 Critical |
| Function on indexed column | 🟠 Major |
| Leading wildcard LIKE | 🟠 Major |
| Wrong composite index order | 🟠 Major |
| ORDER BY without covering index | 🟡 Minor |
| Missing index on small table | 🟡 Minor |

## Output Format

```markdown
### Index Usage: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Table/Entity:** [Table name]
**Column(s):** [Column names]

**Issue:**
[Description — missing index, wrong order, function defeating index]

**Query Pattern:**
```php
// The query that needs index support
```

**Recommended Index:**
```sql
CREATE INDEX idx_orders_status_created ON orders (status, created_at);
```

**Expected Improvement:**
Full table scan → index seek (1000x faster on large tables)
```
