---
name: acc-check-batch-processing
description: Analyzes PHP code for batch processing issues. Detects single-item vs bulk operations, missing batch inserts, individual API calls in loops, transaction overhead.
---

# Batch Processing Analysis

Analyze PHP code for batch processing opportunities.

## Detection Patterns

### 1. Single-Item vs Bulk Operations

```php
// SLOW: Individual inserts
foreach ($users as $user) {
    $pdo->query("INSERT INTO users (name, email) VALUES ('$name', '$email')");
}

// FAST: Bulk insert
$values = [];
$params = [];
foreach ($users as $i => $user) {
    $values[] = "(:name{$i}, :email{$i})";
    $params["name{$i}"] = $user['name'];
    $params["email{$i}"] = $user['email'];
}
$sql = "INSERT INTO users (name, email) VALUES " . implode(', ', $values);
$pdo->prepare($sql)->execute($params);
```

### 2. Individual Database Operations

```php
// SLOW: Save each entity separately
foreach ($entities as $entity) {
    $this->em->persist($entity);
    $this->em->flush();
}

// FAST: Batch persist and single flush
foreach ($entities as $entity) {
    $this->em->persist($entity);
}
$this->em->flush();

// FAST: With memory management for large batches
$batchSize = 100;
foreach ($entities as $i => $entity) {
    $this->em->persist($entity);
    if ($i % $batchSize === 0) {
        $this->em->flush();
        $this->em->clear();
    }
}
$this->em->flush();
```

### 3. Individual API Calls in Loops

```php
// SLOW: HTTP call per item
foreach ($products as $product) {
    $price = $this->pricingApi->getPrice($product->getSku());
    $product->setPrice($price);
}

// FAST: Batch API call
$skus = array_map(fn($p) => $p->getSku(), $products);
$prices = $this->pricingApi->getPrices($skus);
foreach ($products as $product) {
    $product->setPrice($prices[$product->getSku()]);
}

// SLOW: Individual notifications
foreach ($users as $user) {
    $this->emailService->send($user->getEmail(), $message);
}

// FAST: Batch send
$emails = array_map(fn($u) => $u->getEmail(), $users);
$this->emailService->sendBatch($emails, $message);
```

### 4. Transaction Overhead

```php
// SLOW: Transaction per operation
foreach ($transfers as $transfer) {
    $this->connection->beginTransaction();
    try {
        $this->processTransfer($transfer);
        $this->connection->commit();
    } catch (Exception $e) {
        $this->connection->rollBack();
    }
}

// FAST: Single transaction (if appropriate)
$this->connection->beginTransaction();
try {
    foreach ($transfers as $transfer) {
        $this->processTransfer($transfer);
    }
    $this->connection->commit();
} catch (Exception $e) {
    $this->connection->rollBack();
}

// BALANCED: Chunked transactions
$chunks = array_chunk($transfers, 100);
foreach ($chunks as $chunk) {
    $this->connection->beginTransaction();
    try {
        foreach ($chunk as $transfer) {
            $this->processTransfer($transfer);
        }
        $this->connection->commit();
    } catch (Exception $e) {
        $this->connection->rollBack();
    }
}
```

### 5. Individual File Operations

```php
// SLOW: Separate file writes
foreach ($lines as $line) {
    file_put_contents($path, $line . "\n", FILE_APPEND);
}

// FAST: Batch write
$content = implode("\n", $lines);
file_put_contents($path, $content);

// FAST: Stream for large data
$handle = fopen($path, 'w');
foreach ($lines as $line) {
    fwrite($handle, $line . "\n");
}
fclose($handle);
```

### 6. Individual Cache Operations

```php
// SLOW: Individual cache calls
foreach ($items as $item) {
    $this->cache->set('item:' . $item->getId(), $item);
}

// FAST: Multi-set
$cacheItems = [];
foreach ($items as $item) {
    $cacheItems['item:' . $item->getId()] = $item;
}
$this->cache->setMultiple($cacheItems);

// SLOW: Individual gets
$results = [];
foreach ($ids as $id) {
    $results[$id] = $this->cache->get('item:' . $id);
}

// FAST: Multi-get
$keys = array_map(fn($id) => 'item:' . $id, $ids);
$results = $this->cache->getMultiple($keys);
```

### 7. Queue Message Publishing

```php
// SLOW: Individual publish
foreach ($events as $event) {
    $this->queue->publish($event);
}

// FAST: Batch publish
$this->queue->publishBatch($events);

// With RabbitMQ
$channel->batch_basic_publish();
foreach ($messages as $message) {
    $channel->batch_basic_publish($message, $exchange, $routingKey);
}
$channel->publish_batch();
```

### 8. Update vs Bulk Update

```php
// SLOW: Individual updates
foreach ($users as $user) {
    $user->setStatus('inactive');
    $this->em->flush();
}

// FAST: Bulk DQL update
$this->em->createQuery(
    'UPDATE User u SET u.status = :status WHERE u.id IN (:ids)'
)->setParameters([
    'status' => 'inactive',
    'ids' => array_map(fn($u) => $u->getId(), $users)
])->execute();
```

## Grep Patterns

```bash
# flush() in loop
Grep: "foreach.*->flush\(\)" --glob "**/*.php"

# API/HTTP calls in loop
Grep: "foreach.*->(request|get|post|send)\(" --glob "**/*.php"

# file_put_contents with APPEND in loop
Grep: "foreach.*file_put_contents.*FILE_APPEND" --glob "**/*.php"

# cache->set in loop
Grep: "foreach.*->set\(" --glob "**/*.php"

# Individual INSERT
Grep: "foreach.*INSERT INTO" --glob "**/*.php"
```

## Batch Size Guidelines

| Operation | Recommended Batch Size |
|-----------|------------------------|
| Database inserts | 100-1000 |
| Doctrine flush | 50-100 |
| API calls | Depends on API limits |
| Cache operations | 100-500 |
| File writes | Buffer in memory, single write |
| Queue publish | 100-500 |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Individual DB operations in loop | 🔴 Critical |
| HTTP calls in loop | 🔴 Critical |
| flush() per entity | 🟠 Major |
| Individual cache operations | 🟠 Major |
| Individual file appends | 🟡 Minor |

## Output Format

```markdown
### Batch Processing Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Individual DB|API Loop|Transaction Overhead|...]

**Issue:**
[Description of the batch processing problem]

**Current:** N operations in loop
**Optimal:** 1 batch operation

**Code:**
```php
// Individual operations
```

**Optimization:**
```php
// Batch operation
```

**Improvement:**
For 1000 items:
- Network round trips: 1000 → 1
- Execution time: ~10s → ~100ms
```
