# Bug Fix Templates

Fix templates organized by bug category.

## 1. Null Pointer Fix

### Pattern A: Guard Clause

```php
// Before
public function process(Order $order): void
{
    $customer = $this->customerRepository->find($order->getCustomerId());
    $email = $customer->getEmail(); // Null pointer if not found
}

// After
public function process(Order $order): void
{
    $customer = $this->customerRepository->find($order->getCustomerId());
    if ($customer === null) {
        throw new CustomerNotFoundException($order->getCustomerId());
    }
    $email = $customer->getEmail();
}
```

### Pattern B: Null Object

```php
// Before
public function getDiscount(Order $order): Money
{
    $promotion = $this->promotionRepository->findActive();
    return $promotion->calculateDiscount($order); // Null pointer
}

// After
public function getDiscount(Order $order): Money
{
    $promotion = $this->promotionRepository->findActive()
        ?? new NullPromotion();
    return $promotion->calculateDiscount($order);
}
```

### Pattern C: Optional Return

```php
// Before
public function findUser(UserId $id): User
{
    return $this->users[$id->toString()]; // May not exist
}

// After
public function findUser(UserId $id): ?User
{
    return $this->users[$id->toString()] ?? null;
}
```

## 2. Logic Error Fix

### Pattern A: Condition Correction

```php
// Before - wrong operator
if ($amount > $limit) {
    throw new LimitExceededException();
}

// After - correct operator
if ($amount >= $limit) {
    throw new LimitExceededException();
}
```

### Pattern B: Boolean Inversion

```php
// Before - inverted logic
if (!$user->isActive()) {
    $this->sendWelcomeEmail($user);
}

// After - correct logic
if ($user->isActive()) {
    $this->sendWelcomeEmail($user);
}
```

### Pattern C: Missing Case

```php
// Before - missing case
public function getStatusLabel(OrderStatus $status): string
{
    return match ($status) {
        OrderStatus::DRAFT => 'Draft',
        OrderStatus::SUBMITTED => 'Submitted',
        // Missing CANCELLED case
    };
}

// After - complete cases
public function getStatusLabel(OrderStatus $status): string
{
    return match ($status) {
        OrderStatus::DRAFT => 'Draft',
        OrderStatus::SUBMITTED => 'Submitted',
        OrderStatus::CANCELLED => 'Cancelled',
    };
}
```

## 3. Boundary Fix

### Pattern A: Empty Collection Check

```php
// Before
public function getFirstItem(array $items): Item
{
    return $items[0]; // Fails on empty
}

// After
public function getFirstItem(array $items): Item
{
    if ($items === []) {
        throw new EmptyCollectionException('items');
    }
    return $items[0];
}
```

### Pattern B: Index Bounds Check

```php
// Before
public function getItemAt(array $items, int $index): Item
{
    return $items[$index]; // May be out of bounds
}

// After
public function getItemAt(array $items, int $index): Item
{
    if (!isset($items[$index])) {
        throw new IndexOutOfBoundsException($index, count($items));
    }
    return $items[$index];
}
```

### Pattern C: Range Validation

```php
// Before
public function setQuantity(int $quantity): void
{
    $this->quantity = $quantity; // Allows negative
}

// After
public function setQuantity(int $quantity): void
{
    if ($quantity < 0) {
        throw new InvalidArgumentException('Quantity cannot be negative');
    }
    $this->quantity = $quantity;
}
```

## 4. Race Condition Fix

### Pattern A: Database Locking

```php
// Before - race condition
public function reserveStock(ProductId $productId, int $quantity): void
{
    $product = $this->repository->find($productId);
    if ($product->getStock() >= $quantity) {
        $product->decreaseStock($quantity);
        $this->repository->save($product);
    }
}

// After - with pessimistic lock
public function reserveStock(ProductId $productId, int $quantity): void
{
    $this->entityManager->beginTransaction();
    try {
        $product = $this->repository->findWithLock($productId);
        if ($product->getStock() >= $quantity) {
            $product->decreaseStock($quantity);
            $this->repository->save($product);
        }
        $this->entityManager->commit();
    } catch (\Throwable $e) {
        $this->entityManager->rollback();
        throw $e;
    }
}
```

### Pattern B: Optimistic Locking

```php
// Before - race condition
public function updateOrder(Order $order): void
{
    $this->repository->save($order);
}

// After - with version check
public function updateOrder(Order $order): void
{
    $current = $this->repository->find($order->getId());
    if ($current->getVersion() !== $order->getVersion()) {
        throw new OptimisticLockException('Order was modified');
    }
    $order->incrementVersion();
    $this->repository->save($order);
}
```

### Pattern C: Atomic Operation

```php
// Before - check-then-act race
public function createIfNotExists(string $key, mixed $value): void
{
    if (!$this->cache->has($key)) {
        $this->cache->set($key, $value);
    }
}

// After - atomic operation
public function createIfNotExists(string $key, mixed $value): void
{
    $this->cache->add($key, $value); // Returns false if exists
}
```

## 5. Resource Leak Fix

### Pattern A: Try-Finally

```php
// Before - resource leak
public function readFile(string $path): string
{
    $handle = fopen($path, 'r');
    $content = fread($handle, filesize($path));
    return $content; // Handle not closed
}

// After - proper cleanup
public function readFile(string $path): string
{
    $handle = fopen($path, 'r');
    try {
        return fread($handle, filesize($path));
    } finally {
        fclose($handle);
    }
}
```

### Pattern B: Higher-Level API

```php
// Before - manual resource management
public function readJson(string $path): array
{
    $handle = fopen($path, 'r');
    $content = fread($handle, filesize($path));
    fclose($handle);
    return json_decode($content, true);
}

// After - use file_get_contents
public function readJson(string $path): array
{
    $content = file_get_contents($path);
    return json_decode($content, true);
}
```

### Pattern C: Connection Pool Return

```php
// Before - connection leak
public function query(string $sql): array
{
    $connection = $this->pool->acquire();
    return $connection->query($sql)->fetchAll();
    // Connection not returned to pool
}

// After - proper return
public function query(string $sql): array
{
    $connection = $this->pool->acquire();
    try {
        return $connection->query($sql)->fetchAll();
    } finally {
        $this->pool->release($connection);
    }
}
```

## 6. Exception Handling Fix

### Pattern A: Specific Catch

```php
// Before - catching too broad
try {
    $this->service->process($data);
} catch (Exception $e) {
    $this->logger->error($e->getMessage());
}

// After - specific exception
try {
    $this->service->process($data);
} catch (ValidationException $e) {
    throw new ProcessingException("Invalid data: {$e->getMessage()}", previous: $e);
} catch (ServiceException $e) {
    $this->logger->error('Service failed', ['exception' => $e]);
    throw $e;
}
```

### Pattern B: Exception Chaining

```php
// Before - lost context
try {
    $this->repository->save($entity);
} catch (PDOException $e) {
    throw new RepositoryException('Failed to save');
}

// After - preserved context
try {
    $this->repository->save($entity);
} catch (PDOException $e) {
    throw new RepositoryException(
        "Failed to save entity: {$e->getMessage()}",
        previous: $e
    );
}
```

### Pattern C: Proper Re-throw

```php
// Before - swallowed exception
try {
    $this->service->process($data);
} catch (Exception $e) {
    // Silent failure
}

// After - log and re-throw
try {
    $this->service->process($data);
} catch (ProcessingException $e) {
    $this->logger->error('Processing failed', [
        'data' => $data,
        'exception' => $e,
    ]);
    throw $e;
}
```

## 7. Type Safety Fix

### Pattern A: Strict Type Declaration

```php
// Before - missing strict types
function calculate($amount) {
    return $amount * 1.1;
}

// After - strict types
declare(strict_types=1);

function calculate(float $amount): float {
    return $amount * 1.1;
}
```

### Pattern B: Type Validation

```php
// Before - no validation
public function setPrice(mixed $price): void
{
    $this->price = $price;
}

// After - type validation
public function setPrice(int|float $price): void
{
    if ($price < 0) {
        throw new InvalidArgumentException('Price cannot be negative');
    }
    $this->price = (float) $price;
}
```

### Pattern C: Coercion at Boundary

```php
// Before - type error from external input
public function handleRequest(array $data): void
{
    $this->service->process($data['quantity']); // String from JSON
}

// After - explicit coercion
public function handleRequest(array $data): void
{
    $quantity = (int) ($data['quantity'] ?? 0);
    $this->service->process($quantity);
}
```

## 8. SQL Injection Fix

### Pattern A: Prepared Statement

```php
// Before - SQL injection
public function findByEmail(string $email): ?User
{
    $sql = "SELECT * FROM users WHERE email = '$email'";
    return $this->connection->query($sql)->fetch();
}

// After - prepared statement
public function findByEmail(string $email): ?User
{
    $sql = "SELECT * FROM users WHERE email = :email";
    $stmt = $this->connection->prepare($sql);
    $stmt->execute(['email' => $email]);
    return $stmt->fetch() ?: null;
}
```

### Pattern B: Query Builder

```php
// Before - concatenation
public function search(string $term): array
{
    return $this->connection->query(
        "SELECT * FROM products WHERE name LIKE '%$term%'"
    )->fetchAll();
}

// After - query builder
public function search(string $term): array
{
    return $this->queryBuilder
        ->select('*')
        ->from('products')
        ->where('name LIKE :term')
        ->setParameter('term', "%$term%")
        ->executeQuery()
        ->fetchAllAssociative();
}
```

## 9. Infinite Loop Fix

### Pattern A: Iteration Limit

```php
// Before - potential infinite loop
while ($item = $queue->dequeue()) {
    $this->process($item);
}

// After - with safety limit
$maxIterations = 10000;
$iterations = 0;
while ($item = $queue->dequeue()) {
    if (++$iterations > $maxIterations) {
        throw new MaxIterationsExceededException($maxIterations);
    }
    $this->process($item);
}
```

### Pattern B: Visited Tracking

```php
// Before - infinite recursion on cycles
public function traverse(Node $node): void
{
    $this->visit($node);
    foreach ($node->getChildren() as $child) {
        $this->traverse($child);
    }
}

// After - with cycle detection
public function traverse(Node $node, array &$visited = []): void
{
    $id = spl_object_id($node);
    if (isset($visited[$id])) {
        return; // Already visited
    }
    $visited[$id] = true;

    $this->visit($node);
    foreach ($node->getChildren() as $child) {
        $this->traverse($child, $visited);
    }
}
```

### Pattern C: Recursion Depth Limit

```php
// Before - unbounded recursion
public function flatten(array $nested): array
{
    $result = [];
    foreach ($nested as $item) {
        if (is_array($item)) {
            $result = array_merge($result, $this->flatten($item));
        } else {
            $result[] = $item;
        }
    }
    return $result;
}

// After - with depth limit
public function flatten(array $nested, int $depth = 0, int $maxDepth = 100): array
{
    if ($depth > $maxDepth) {
        throw new MaxDepthExceededException($maxDepth);
    }

    $result = [];
    foreach ($nested as $item) {
        if (is_array($item)) {
            $result = array_merge($result, $this->flatten($item, $depth + 1, $maxDepth));
        } else {
            $result[] = $item;
        }
    }
    return $result;
}
```
