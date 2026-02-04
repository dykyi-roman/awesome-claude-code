---
name: acc-check-sql-injection
description: Analyzes PHP code for SQL injection vulnerabilities. Detects query concatenation, ORM misuse, raw queries, dynamic identifiers, prepared statement bypasses.
---

# SQL Injection Security Check

Analyze PHP code for SQL injection vulnerabilities.

## Detection Patterns

### 1. String Concatenation in Queries

```php
// CRITICAL: Direct concatenation
$sql = "SELECT * FROM users WHERE id = " . $id;
$sql = "SELECT * FROM users WHERE email = '" . $email . "'";
$sql = "DELETE FROM posts WHERE id = $id";

// CRITICAL: In method
public function findByEmail(string $email): ?User
{
    $sql = "SELECT * FROM users WHERE email = '$email'";
    return $this->query($sql);
}
```

### 2. Variable Interpolation

```php
// CRITICAL: Double-quoted strings
$sql = "SELECT * FROM $table WHERE $column = '$value'";
$sql = "SELECT * FROM users WHERE name LIKE '%{$search}%'";

// CRITICAL: Heredoc/Nowdoc
$sql = <<<SQL
    SELECT * FROM users WHERE id = $id
SQL;
```

### 3. Dynamic Table/Column Names

```php
// CRITICAL: User-controlled identifiers
$table = $_GET['table'];
$query = "SELECT * FROM $table";

$column = $request->get('sort');
$query = "SELECT * FROM users ORDER BY $column";

// Even with prepared statements:
$stmt = $pdo->prepare("SELECT * FROM $table WHERE id = ?");
// Table name is still injectable!
```

### 4. ORM Raw Queries

```php
// CRITICAL: Doctrine raw DQL
$dql = "SELECT u FROM User u WHERE u.email = '$email'";
$query = $em->createQuery($dql);

// CRITICAL: Query builder with raw
$qb->where("u.status = $status");
$qb->orderBy($userInput);

// CRITICAL: Native query
$sql = "SELECT * FROM users WHERE name = '$name'";
$em->getConnection()->executeQuery($sql);
```

### 5. Eloquent/Laravel Raw

```php
// CRITICAL: Raw methods
User::whereRaw("email = '$email'")->get();
DB::select("SELECT * FROM users WHERE id = $id");
DB::raw("COUNT(*) as count WHERE status = '$status'");

// VULNERABLE: Order by
User::orderBy($request->input('sort'))->get();
User::orderByRaw($request->input('order'))->get();
```

### 6. LIKE Clause Injection

```php
// CRITICAL: Unescaped in LIKE
$sql = "SELECT * FROM products WHERE name LIKE '%$search%'";

// VULNERABLE: Wildcards not escaped
$stmt = $pdo->prepare("SELECT * FROM products WHERE name LIKE ?");
$stmt->execute(["%$search%"]);
// User can input: %' OR '1'='1

// CORRECT: Escape wildcards
$search = addcslashes($search, '%_');
$stmt->execute(["%{$search}%"]);
```

### 7. IN Clause Vulnerabilities

```php
// CRITICAL: Building IN unsafely
$ids = implode(',', $_GET['ids']);
$sql = "SELECT * FROM users WHERE id IN ($ids)";

// VULNERABLE: Array could contain non-integers
$ids = array_map('intval', $_GET['ids']);
$sql = "SELECT * FROM users WHERE id IN (" . implode(',', $ids) . ")";
// Empty array results in "IN ()" - SQL error

// CORRECT: Use parameter binding
$placeholders = implode(',', array_fill(0, count($ids), '?'));
$stmt = $pdo->prepare("SELECT * FROM users WHERE id IN ($placeholders)");
$stmt->execute($ids);
```

### 8. Second-Order Injection

```php
// CRITICAL: Data from database used unsafely
$user = $this->getUserFromDatabase($id);
$sql = "SELECT * FROM orders WHERE user_name = '" . $user->name . "'";
// If name was originally injected: O'Malley' OR '1'='1
```

### 9. Prepared Statement Bypasses

```php
// VULNERABLE: prepare() but not using parameters
$sql = "SELECT * FROM users WHERE id = $id";
$stmt = $pdo->prepare($sql);
$stmt->execute(); // No binding!

// VULNERABLE: Mixing bound and unbound
$stmt = $pdo->prepare("SELECT * FROM $table WHERE id = ?");
$stmt->execute([$id]); // Table still injectable
```

### 10. Stored Procedure Injection

```php
// CRITICAL: Procedure call with user input
$sql = "CALL process_order($orderId, '$status')";
$pdo->query($sql);

// CRITICAL: Even with prepare
$stmt = $pdo->prepare("CALL get_user_data('$userId')");
// Parameter inside string literal is not bound
```

## Grep Patterns

```bash
# Variable in SQL
Grep: '(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*\$\w+' -i --glob "**/*.php"

# Concatenation in query methods
Grep: "(query|execute|prepare)\s*\([^)]*\.\s*\\\$" --glob "**/*.php"

# Raw ORM methods
Grep: "(whereRaw|orderByRaw|selectRaw|DB::raw)\s*\(" --glob "**/*.php"

# DQL with variable
Grep: "createQuery\s*\([^)]*\\\$" --glob "**/*.php"

# LIKE without escaping
Grep: "LIKE.*'%.*\\\$.*%'" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Direct concatenation in SQL | 🔴 Critical |
| $_GET/$_POST in query | 🔴 Critical |
| Dynamic table/column name | 🔴 Critical |
| ORM raw with variable | 🔴 Critical |
| LIKE without wildcard escape | 🟠 Major |
| Second-order injection risk | 🟠 Major |

## Secure Patterns

### PDO Prepared Statements

```php
// Positional parameters
$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ? AND status = ?');
$stmt->execute([$id, $status]);

// Named parameters
$stmt = $pdo->prepare('SELECT * FROM users WHERE email = :email');
$stmt->execute(['email' => $email]);
```

### Doctrine Query Builder

```php
$qb = $em->createQueryBuilder()
    ->select('u')
    ->from(User::class, 'u')
    ->where('u.email = :email')
    ->setParameter('email', $email);
```

### Safe Dynamic Identifiers

```php
// Whitelist for table/column names
$allowedTables = ['users', 'orders', 'products'];
if (!in_array($table, $allowedTables, true)) {
    throw new InvalidArgumentException('Invalid table');
}

$allowedColumns = ['name', 'email', 'created_at'];
$column = in_array($sort, $allowedColumns, true) ? $sort : 'id';
```

### Laravel Eloquent

```php
// Safe binding
User::where('email', $email)->first();

// With array
User::whereIn('id', $ids)->get();

// Order by validation
$allowed = ['name', 'created_at'];
$sort = in_array($input, $allowed) ? $input : 'id';
User::orderBy($sort)->get();
```

## Output Format

```markdown
### SQL Injection: [Description]

**Severity:** 🔴 Critical
**Location:** `file.php:line`
**CWE:** CWE-89 (SQL Injection)

**Issue:**
User input is included in SQL without parameterization.

**Attack Vector:**
Input: `' OR '1'='1' --`
Result: Query returns all rows, bypassing conditions.

**Code:**
```php
// Vulnerable code
```

**Fix:**
```php
// Parameterized query
```
```
