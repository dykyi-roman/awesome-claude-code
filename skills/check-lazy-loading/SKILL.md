---
name: acc-check-lazy-loading
description: Analyzes PHP code for lazy loading issues. Detects premature loading, missing pagination, inappropriate eager loading, infinite scroll problems.
---

# Lazy Loading Analysis

Analyze PHP code for lazy loading patterns and issues.

## Detection Patterns

### 1. Premature Loading

```php
// PREMATURE: Loading before needed
public function getOrder(int $id): Order
{
    $order = $this->repository->find($id);
    $items = $order->getItems(); // Loads immediately
    $customer = $order->getCustomer(); // Loads immediately

    return $order; // Items and customer may not be used
}

// BETTER: Let caller decide
public function getOrder(int $id): Order
{
    return $this->repository->find($id);
    // Items load only when accessed
}
```

### 2. Missing Pagination

```php
// NO PAGINATION: Loads entire table
public function listUsers(): array
{
    return $this->userRepository->findAll();
}

// NO PAGINATION: API returns everything
public function getProducts(): JsonResponse
{
    $products = $this->repository->findBy(['active' => true]);
    return new JsonResponse($products); // Could be 100K products
}

// WITH PAGINATION:
public function listUsers(int $page = 1, int $limit = 20): array
{
    return $this->repository->findBy(
        [],
        ['createdAt' => 'DESC'],
        $limit,
        ($page - 1) * $limit
    );
}
```

### 3. Inappropriate Eager Loading

```php
// OVER-EAGER: Loading unused relations
$qb = $em->createQueryBuilder()
    ->select('u', 'o', 'p', 'c', 'a')
    ->from(User::class, 'u')
    ->join('u.orders', 'o')
    ->join('o.products', 'p')
    ->join('u.comments', 'c')
    ->join('u.addresses', 'a')
    ->where('u.id = :id');
// Only needed user name

// RIGHT-SIZED: Load what's needed
$qb = $em->createQueryBuilder()
    ->select('u.name')
    ->from(User::class, 'u')
    ->where('u.id = :id');
```

### 4. Infinite Scroll Issues

```php
// SLOW: Offset-based pagination degrades
public function loadMore(int $offset): array
{
    return $this->repository->findBy(
        [],
        ['id' => 'DESC'],
        20,
        $offset // Slow when offset is large
    );
}

// BETTER: Cursor-based pagination
public function loadMore(?int $lastId = null): array
{
    $qb = $this->createQueryBuilder('p')
        ->orderBy('p.id', 'DESC')
        ->setMaxResults(20);

    if ($lastId !== null) {
        $qb->where('p.id < :lastId')
           ->setParameter('lastId', $lastId);
    }

    return $qb->getQuery()->getResult();
}
```

### 5. Lazy Loading in Serialization

```php
// PROBLEM: Lazy loading during JSON encode
public function getOrder(int $id): JsonResponse
{
    $order = $this->repository->find($id);
    return new JsonResponse($order);
    // Serializer may trigger lazy loading of all relations
}

// FIXED: Explicit DTO or groups
public function getOrder(int $id): JsonResponse
{
    $order = $this->repository->find($id);
    return $this->json($order, 200, [], ['groups' => ['order:read']]);
}
```

### 6. Count Without Data

```php
// INEFFICIENT: Load all to count
$users = $this->repository->findBy(['status' => 'active']);
$count = count($users); // Loaded all users just to count

// EFFICIENT: COUNT query
$count = $this->repository->count(['status' => 'active']);

// EFFICIENT: DQL count
$count = $em->createQuery(
    'SELECT COUNT(u) FROM User u WHERE u.status = :status'
)->setParameter('status', 'active')
 ->getSingleScalarResult();
```

### 7. Exists Check Loading Full Entity

```php
// INEFFICIENT: Load entity to check existence
$user = $this->repository->find($id);
if ($user !== null) {
    // User exists
}

// EFFICIENT: EXISTS query or count
$exists = $this->repository->count(['id' => $id]) > 0;

// EFFICIENT: DQL
$exists = (bool) $em->createQuery(
    'SELECT 1 FROM User u WHERE u.id = :id'
)->setParameter('id', $id)
 ->setMaxResults(1)
 ->getOneOrNullResult();
```

### 8. Loading for Single Property

```php
// INEFFICIENT: Load full entity for one field
$user = $this->repository->find($id);
$email = $user->getEmail();

// EFFICIENT: Select only needed field
$email = $em->createQuery(
    'SELECT u.email FROM User u WHERE u.id = :id'
)->setParameter('id', $id)
 ->getSingleScalarResult();

// EFFICIENT: Partial object
$user = $em->createQuery(
    'SELECT partial u.{id, email} FROM User u WHERE u.id = :id'
)->setParameter('id', $id)
 ->getSingleResult();
```

## Grep Patterns

```bash
# findAll usage
Grep: "->findAll\(\)" --glob "**/*.php"

# count(findBy)
Grep: "count\(.*->find" --glob "**/*.php"

# Large offset
Grep: "OFFSET\s+\$|setFirstResult\(" --glob "**/*.php"

# Missing limit
Grep: "findBy\([^)]+\)\s*;" --glob "**/*.php"
```

## Pagination Patterns

### Offset-Based (Simple, Slower for Large Offsets)

```php
$results = $repository->findBy(
    $criteria,
    ['id' => 'DESC'],
    $limit,
    $offset
);
```

### Cursor-Based (Efficient, Consistent)

```php
$qb = $this->createQueryBuilder('e')
    ->where('e.id < :cursor')
    ->setParameter('cursor', $cursor)
    ->orderBy('e.id', 'DESC')
    ->setMaxResults($limit);
```

### Keyset Pagination (Most Efficient)

```php
$qb = $this->createQueryBuilder('e')
    ->where('(e.createdAt, e.id) < (:createdAt, :id)')
    ->setParameters([
        'createdAt' => $lastCreatedAt,
        'id' => $lastId,
    ])
    ->orderBy('e.createdAt', 'DESC')
    ->addOrderBy('e.id', 'DESC')
    ->setMaxResults($limit);
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Missing pagination on list endpoint | 🔴 Critical |
| Load all to count | 🟠 Major |
| Large offset pagination | 🟠 Major |
| Full entity for single field | 🟡 Minor |
| Over-eager loading | 🟡 Minor |

## Output Format

```markdown
### Lazy Loading Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Missing Pagination|Premature Loading|...]

**Issue:**
[Description of the lazy loading problem]

**Code:**
```php
// Current code
```

**Fix:**
```php
// Optimized code
```

**Improvement:**
Data loaded: 10,000 records → 20 records per page
Memory: 50 MB → 1 MB
```
