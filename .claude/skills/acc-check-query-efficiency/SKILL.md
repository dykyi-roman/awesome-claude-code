---
name: acc-check-query-efficiency
description: Analyzes PHP code for query efficiency issues. Detects SELECT *, missing indexes hints, unnecessary joins, full table scans, suboptimal WHERE clauses.
---

# Query Efficiency Analysis

Analyze PHP code for database query efficiency issues.

## Detection Patterns

### 1. SELECT * Usage

```php
// INEFFICIENT: Fetches all columns
$sql = "SELECT * FROM users WHERE id = ?";
$query = "SELECT * FROM orders JOIN products ON ...";

// EFFICIENT: Only needed columns
$sql = "SELECT id, name, email FROM users WHERE id = ?";

// Doctrine partial select
$qb->select('partial u.{id, name, email}');
```

### 2. Missing Index Hints

```php
// SLOW: Likely missing index
"SELECT * FROM orders WHERE customer_email = ?"
// Suggest: CREATE INDEX idx_orders_customer_email ON orders(customer_email)

// SLOW: Function on indexed column
"SELECT * FROM users WHERE LOWER(email) = ?"
// Index on `email` won't be used

// SLOW: Leading wildcard
"SELECT * FROM products WHERE name LIKE '%search%'"
// Consider: Full-text search index
```

### 3. Unnecessary Joins

```php
// INEFFICIENT: Join when only ID needed
$qb->select('o', 'c')
   ->from(Order::class, 'o')
   ->join('o.customer', 'c')
   ->where('o.id = :id');
// If only order is used, don't join customer

// INEFFICIENT: Joining unused tables
"SELECT p.name FROM products p
 JOIN categories c ON p.category_id = c.id
 JOIN brands b ON p.brand_id = b.id"
// categories and brands not used in SELECT or WHERE
```

### 4. Full Table Scans

```php
// FULL SCAN: No WHERE clause
"SELECT * FROM users"
$repository->findAll(); // Loads entire table

// FULL SCAN: Non-indexed column
"SELECT * FROM logs WHERE message LIKE '%error%'"

// FULL SCAN: OR with different columns
"SELECT * FROM users WHERE email = ? OR phone = ?"
// May not use indexes efficiently
```

### 5. Suboptimal WHERE Clauses

```php
// INEFFICIENT: Function in WHERE
"SELECT * FROM orders WHERE YEAR(created_at) = 2024"
// Better: created_at >= '2024-01-01' AND created_at < '2025-01-01'

// INEFFICIENT: Implicit type conversion
"SELECT * FROM users WHERE id = '123'"
// ID is integer, passing string

// INEFFICIENT: NOT IN with many values
"SELECT * FROM products WHERE id NOT IN (1,2,3,...,1000)"
```

### 6. ORDER BY Without Index

```php
// SLOW: Sorting on non-indexed column
"SELECT * FROM orders ORDER BY total DESC"
// Consider: CREATE INDEX idx_orders_total ON orders(total)

// SLOW: Multi-column sort without composite index
"SELECT * FROM products ORDER BY category_id, name"
// Consider: CREATE INDEX idx_products_cat_name ON products(category_id, name)
```

### 7. LIMIT Without ORDER BY

```php
// UNPREDICTABLE: No guaranteed order
"SELECT * FROM logs LIMIT 10"

// CORRECT: Explicit ordering
"SELECT * FROM logs ORDER BY id DESC LIMIT 10"
```

### 8. Large OFFSET Pagination

```php
// SLOW: Large offset
"SELECT * FROM products ORDER BY id LIMIT 20 OFFSET 10000"
// Must scan and discard 10000 rows

// BETTER: Keyset pagination
"SELECT * FROM products WHERE id > :last_id ORDER BY id LIMIT 20"
```

### 9. Count Query Issues

```php
// SLOW: Full count
"SELECT COUNT(*) FROM huge_table"

// SLOW: Count with JOIN
"SELECT COUNT(*) FROM orders o
 JOIN line_items li ON o.id = li.order_id"

// BETTER: Count only when necessary
// Use estimates for large tables
"SELECT reltuples FROM pg_class WHERE relname = 'huge_table'"
```

### 10. Repeated Queries

```php
// INEFFICIENT: Same query multiple times
$user = $repository->find($userId);
// ... later ...
$user = $repository->find($userId); // Same query again

// Doctrine identity map helps, but not across requests
```

## Grep Patterns

```bash
# SELECT * usage
Grep: 'SELECT\s+\*\s+FROM' -i --glob "**/*.php"

# LIKE with leading wildcard
Grep: "LIKE\s+['\"]%" --glob "**/*.php"

# Function in WHERE
Grep: "WHERE.*(LOWER|UPPER|YEAR|MONTH|DATE)\s*\(" -i --glob "**/*.php"

# Large OFFSET
Grep: "OFFSET\s+\d{4,}" --glob "**/*.php"

# findAll() usage
Grep: "->findAll\(\)" --glob "**/*.php"
```

## Index Recommendations

```sql
-- Single column indexes for WHERE clauses
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_status ON orders(status);

-- Composite indexes for multi-column queries
CREATE INDEX idx_orders_user_date ON orders(user_id, created_at);

-- Covering indexes (include SELECT columns)
CREATE INDEX idx_products_cat_name ON products(category_id) INCLUDE (name, price);

-- Partial indexes for filtered queries
CREATE INDEX idx_orders_active ON orders(user_id) WHERE status = 'active';
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Full table scan on large table | 🔴 Critical |
| SELECT * with many columns | 🟠 Major |
| Missing composite index | 🟠 Major |
| Large OFFSET pagination | 🟠 Major |
| Function on indexed column | 🟡 Minor |
| Unnecessary joins | 🟡 Minor |

## Output Format

```markdown
### Query Efficiency: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Table(s):** users, orders

**Issue:**
[Description of the efficiency problem]

**Query:**
```sql
SELECT * FROM users WHERE LOWER(email) = 'test@example.com'
```

**Optimization:**
```sql
SELECT id, name, email FROM users WHERE email = 'test@example.com'
```

**Recommended Index:**
```sql
CREATE INDEX idx_users_email ON users(email);
```

**Expected Improvement:**
Query time: ~500ms → ~5ms
```
