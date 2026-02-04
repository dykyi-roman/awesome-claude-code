---
name: acc-find-sql-injection
description: Detects SQL injection vulnerabilities in PHP code. Finds string concatenation in queries, unescaped user input, dynamic table/column names, missing prepared statements.
---

# SQL Injection Detection

Analyze PHP code for SQL injection vulnerabilities.

## Detection Patterns

### 1. String Concatenation in Queries

```php
// CRITICAL: Direct variable interpolation
$query = "SELECT * FROM users WHERE id = $id";
$query = "SELECT * FROM users WHERE email = '$email'";

// CRITICAL: Concatenation
$query = "SELECT * FROM users WHERE name = '" . $name . "'";
$query = 'SELECT * FROM users WHERE status = ' . $status;

// CRITICAL: sprintf without validation
$query = sprintf("SELECT * FROM users WHERE id = %d", $id); // Still risky if $id is user input
```

### 2. Unescaped User Input

```php
// CRITICAL: Direct from request
$query = "SELECT * FROM users WHERE id = " . $_GET['id'];
$query = "DELETE FROM posts WHERE id = " . $request->get('id');

// CRITICAL: In method parameters
public function findByEmail(string $email): ?User
{
    return $this->query("SELECT * FROM users WHERE email = '$email'");
}
```

### 3. Dynamic Table/Column Names

```php
// CRITICAL: User-controlled table name
$table = $_GET['table'];
$query = "SELECT * FROM $table";

// CRITICAL: User-controlled column
$column = $request->get('sort');
$query = "SELECT * FROM users ORDER BY $column";

// CRITICAL: User-controlled field in WHERE
$field = $request->get('field');
$query = "SELECT * FROM users WHERE $field = ?";
```

### 4. Missing Prepared Statements

```php
// CRITICAL: Direct query execution
$pdo->query("SELECT * FROM users WHERE id = $id");
$mysqli->query("DELETE FROM posts WHERE id = $id");

// CRITICAL: exec() usage
$pdo->exec("UPDATE users SET status = '$status' WHERE id = $id");
```

### 5. ORM Injection

```php
// CRITICAL: Doctrine DQL injection
$dql = "SELECT u FROM User u WHERE u.email = '$email'";
$query = $em->createQuery($dql);

// CRITICAL: Query builder with raw
$qb->where("u.status = $status"); // Raw expression

// CRITICAL: Native query without binding
$sql = "SELECT * FROM users WHERE name LIKE '%$search%'";
$em->getConnection()->executeQuery($sql);
```

### 6. LIKE Clause Issues

```php
// CRITICAL: Unescaped LIKE
$query = "SELECT * FROM products WHERE name LIKE '%$search%'";

// WARNING: LIKE wildcards not escaped
$stmt = $pdo->prepare("SELECT * FROM products WHERE name LIKE ?");
$stmt->execute(["%$search%"]); // $search may contain % or _
```

### 7. IN Clause Issues

```php
// CRITICAL: Building IN clause unsafely
$ids = implode(',', $_GET['ids']);
$query = "SELECT * FROM users WHERE id IN ($ids)";

// WARNING: Even with array_map, still risky
$ids = array_map('intval', $_GET['ids']); // What if empty?
$query = "SELECT * FROM users WHERE id IN (" . implode(',', $ids) . ")";
```

### 8. Stored Procedure Injection

```php
// CRITICAL: Unparameterized stored procedure
$query = "CALL process_order($orderId, '$status')";
$pdo->query($query);
```

## Grep Patterns

```bash
# Variable in SQL string
Grep: '"\s*SELECT.*\$\w+|"\s*INSERT.*\$\w+|"\s*UPDATE.*\$\w+|"\s*DELETE.*\$\w+' --glob "**/*.php"

# Concatenation in query
Grep: "query\([^)]*\.\s*\\\$" --glob "**/*.php"

# Direct $_GET/$_POST in query
Grep: '\$_(GET|POST|REQUEST)\[[^]]+\].*query' --glob "**/*.php"

# exec() with variable
Grep: "->exec\([^)]*\\\$" --glob "**/*.php"

# DQL with variable
Grep: "createQuery\([^)]*\\\$" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| $_GET/$_POST in query | 🔴 Critical |
| String concatenation in SQL | 🔴 Critical |
| Dynamic table/column name | 🔴 Critical |
| ORM raw query with variable | 🔴 Critical |
| LIKE without escaping wildcards | 🟠 Major |
| IN clause building | 🟠 Major |

## Secure Patterns

### Prepared Statements (PDO)

```php
$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');
$stmt->execute([$id]);

// Named parameters
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);
```

### Query Builder (Doctrine)

```php
$qb = $em->createQueryBuilder()
    ->select('u')
    ->from(User::class, 'u')
    ->where('u.email = :email')
    ->setParameter('email', $email);
```

### Safe Column Names

```php
$allowedColumns = ['name', 'email', 'created_at'];
$column = in_array($sort, $allowedColumns, true) ? $sort : 'id';
$query = "SELECT * FROM users ORDER BY $column";
```

### LIKE with Escaping

```php
$search = addcslashes($search, '%_');
$stmt = $pdo->prepare('SELECT * FROM products WHERE name LIKE ?');
$stmt->execute(["%$search%"]);
```

## Output Format

```markdown
### SQL Injection: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**Type:** [Concatenation|Dynamic Table|Unescaped Input|...]

**Issue:**
User input is included in SQL query without proper parameterization.

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// Parameterized query
```

**Impact:**
Attacker can read, modify, or delete database data.
```
