---
name: acc-check-timeout-strategy
description: Audits timeout configuration across HTTP clients, database connections, queue consumers, cache operations, and external service calls. Detects missing or misconfigured timeouts.
---

# Timeout Strategy Audit

Analyze PHP code for missing or misconfigured timeout strategies across all I/O boundaries.

## Detection Patterns

### 1. HTTP Client Without Timeout

```php
// CRITICAL: No timeout configured
$client = new GuzzleHttp\Client();
$response = $client->get('https://api.external.com/data');

// CRITICAL: Infinite timeout
$client = new GuzzleHttp\Client(['timeout' => 0]);

// CORRECT: Explicit timeouts
$client = new GuzzleHttp\Client([
    'connect_timeout' => 5,
    'timeout' => 30,
    'read_timeout' => 10,
]);
```

### 2. Database Connection Without Timeout

```php
// CRITICAL: No connection timeout
$pdo = new PDO($dsn, $user, $password);

// CRITICAL: No query timeout
$stmt = $pdo->prepare('SELECT * FROM large_table WHERE complex_condition');
$stmt->execute();

// CORRECT: With timeouts
$pdo = new PDO($dsn, $user, $password, [
    PDO::ATTR_TIMEOUT => 5,
    PDO::MYSQL_ATTR_READ_TIMEOUT => 30,
]);

// Doctrine: query timeout
$connection->executeStatement('SET SESSION wait_timeout = 30');
```

### 3. Queue Consumer Without Timeout

```php
// CRITICAL: Blocking forever
$message = $queue->consume(); // No timeout — blocks indefinitely

// CRITICAL: No processing timeout
while ($message = $queue->get()) {
    $this->handler->handle($message); // Could run forever
}

// CORRECT: With timeouts
$message = $queue->consume(timeout: 30);

// Processing timeout
$signal = pcntl_alarm(60); // 60-second processing limit
$this->handler->handle($message);
pcntl_alarm(0); // Cancel alarm
```

### 4. Cache Operations Without Timeout

```php
// CRITICAL: Redis without timeout
$redis = new Redis();
$redis->connect('redis-host', 6379); // No timeout

// CRITICAL: Blocking wait
$value = $redis->blPop('queue', 0); // Block forever

// CORRECT: With timeouts
$redis->connect('redis-host', 6379, 2.5); // 2.5s connect timeout
$redis->setOption(Redis::OPT_READ_TIMEOUT, 5);
$value = $redis->blPop('queue', 30); // 30s max block
```

### 5. External API Without Timeout

```php
// CRITICAL: file_get_contents without timeout
$data = file_get_contents('https://api.example.com/data');

// CRITICAL: curl without CURLOPT_TIMEOUT
$ch = curl_init('https://api.example.com/data');
curl_exec($ch);

// CORRECT: With stream context timeout
$context = stream_context_create([
    'http' => ['timeout' => 10],
]);
$data = file_get_contents('https://api.example.com/data', false, $context);

// CORRECT: curl with timeout
curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 5);
curl_setopt($ch, CURLOPT_TIMEOUT, 30);
```

### 6. Lock/Mutex Without Timeout

```php
// CRITICAL: Lock without timeout — potential deadlock
$lock->acquire(); // Blocks forever if not released

// CORRECT: With timeout
if (!$lock->acquire(timeout: 10)) {
    throw new LockTimeoutException('Failed to acquire lock within 10 seconds');
}
```

## Grep Patterns

```bash
# HTTP clients without timeout
Grep: "new.*Client\(\)|new.*GuzzleHttp|new.*HttpClient" --glob "**/*.php"
Grep: "connect_timeout|timeout.*=>" --glob "**/Infrastructure/**/*.php"

# Database connections
Grep: "new PDO\(|DriverManager::getConnection" --glob "**/*.php"
Grep: "ATTR_TIMEOUT|wait_timeout|read_timeout" --glob "**/*.php"

# Queue consumers
Grep: "->consume\(|->get\(|->receive\(" --glob "**/Consumer/**/*.php"
Grep: "pcntl_alarm|set_time_limit" --glob "**/*.php"

# Cache/Redis
Grep: "->connect\(|Redis\(\)|Memcached\(\)" --glob "**/*.php"
Grep: "OPT_READ_TIMEOUT|blPop|brPop" --glob "**/*.php"

# file_get_contents / curl
Grep: "file_get_contents\(.*http|curl_init" --glob "**/*.php"
Grep: "CURLOPT_TIMEOUT|CURLOPT_CONNECTTIMEOUT" --glob "**/*.php"

# Lock acquisition
Grep: "->acquire\(|->lock\(|flock\(" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| HTTP client without timeout | 🔴 Critical |
| Database without connection timeout | 🔴 Critical |
| Queue consumer blocking forever | 🔴 Critical |
| Lock without timeout (deadlock risk) | 🔴 Critical |
| Cache without read timeout | 🟠 Major |
| Missing processing timeout | 🟠 Major |
| file_get_contents without timeout | 🟡 Minor |

## Timeout Strategy Matrix

| Resource | Connect Timeout | Read Timeout | Processing Timeout |
|----------|----------------|--------------|-------------------|
| HTTP API | 5s | 30s | 60s |
| Database | 5s | 30s | N/A |
| Redis Cache | 2s | 5s | N/A |
| Message Queue | 5s | 30s | 120s |
| File Lock | N/A | N/A | 10s |
| DNS Resolution | 5s | N/A | N/A |

## Output Format

```markdown
### Timeout Strategy: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Resource Type:** HTTP/Database/Queue/Cache/Lock

**Issue:**
[Description of missing or misconfigured timeout]

**Risk:**
- Thread/process starvation
- Connection pool exhaustion
- Cascading failures to dependent services

**Code:**
```php
// Missing timeout
```

**Fix:**
```php
// With proper timeout configuration
```
```
