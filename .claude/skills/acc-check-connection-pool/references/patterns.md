# Connection Pool — Detection Patterns & Secure Examples

## Detection Patterns

### 1. Connection Leaks

```php
// LEAK: Connection not closed in exception path
public function process(): void
{
    $pdo = new PDO($dsn, $user, $pass);
    $this->doWork($pdo);
    $pdo = null; // Only reached if no exception
}

// LEAK: Early return without cleanup
public function getData(): ?array
{
    $pdo = new PDO($dsn, $user, $pass);

    if (!$this->isValid()) {
        return null; // Connection leak!
    }

    $data = $pdo->query('SELECT * FROM data')->fetchAll();
    $pdo = null;
    return $data;
}

// LEAK: Redis connection not closed
$redis = new Redis();
$redis->connect('localhost');
$data = $redis->get('key');
// Missing: $redis->close();
```

### 2. Connection Created in Loop

```php
// CRITICAL: New connection per iteration
foreach ($userIds as $userId) {
    $pdo = new PDO($dsn, $user, $pass);
    $stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');
    $stmt->execute([$userId]);
    $users[] = $stmt->fetch();
}

// CRITICAL: HTTP client per request
foreach ($urls as $url) {
    $client = new GuzzleHttp\Client();
    $responses[] = $client->get($url);
}

// CRITICAL: Redis connection per operation
foreach ($keys as $key) {
    $redis = new Redis();
    $redis->connect('localhost');
    $values[$key] = $redis->get($key);
}
```

### 3. Missing Connection Timeout

```php
// PROBLEMATIC: No connection timeout
$pdo = new PDO($dsn, $user, $pass);
// Will hang indefinitely if DB is unresponsive

// PROBLEMATIC: No socket timeout
$redis = new Redis();
$redis->connect('localhost');
// No read/write timeout set

// FIXED: Set timeouts
$pdo = new PDO($dsn, $user, $pass, [
    PDO::ATTR_TIMEOUT => 5,
]);

$redis->connect('localhost', 6379, 2.5); // 2.5s timeout
$redis->setOption(Redis::OPT_READ_TIMEOUT, 2.5);
```

### 4. Persistent Connection Misuse

```php
// PROBLEMATIC: Persistent without understanding implications
$pdo = new PDO($dsn, $user, $pass, [
    PDO::ATTR_PERSISTENT => true,
]);
// Issues:
// - Transaction state may leak between requests
// - Lock state may persist
// - Connection pool per PHP-FPM worker

// PROBLEMATIC: Persistent connections + transactions
$pdo->beginTransaction();
// ... work ...
// If script crashes, transaction may stay open on persistent connection

// BETTER: Explicit cleanup for persistent connections
register_shutdown_function(function() use ($pdo) {
    if ($pdo->inTransaction()) {
        $pdo->rollBack();
    }
});
```

### 5. Connection Pool Exhaustion

```php
// PROBLEMATIC: Opening many connections without pooling
class DataFetcher
{
    public function fetchAll(array $queries): array
    {
        $results = [];
        foreach ($queries as $query) {
            // Each creates new connection
            $pdo = $this->createConnection();
            $results[] = $pdo->query($query)->fetchAll();
            // Connection not reused
        }
        return $results;
    }
}

// PROBLEMATIC: Parallel requests exhausting pool
$promises = [];
foreach ($requests as $request) {
    // Each may hold connection
    $promises[] = $this->httpClient->requestAsync('GET', $request);
}
// All connections held simultaneously
```

### 6. Missing finally for Cleanup

```php
// LEAK: Exception skips cleanup
public function withConnection(): array
{
    $connection = $this->pool->acquire();

    $result = $this->processData($connection);

    $this->pool->release($connection); // Skipped on exception!

    return $result;
}

// FIXED: Use finally
public function withConnection(): array
{
    $connection = $this->pool->acquire();

    try {
        return $this->processData($connection);
    } finally {
        $this->pool->release($connection);
    }
}
```

### 7. Connection State Not Reset

```php
// PROBLEMATIC: Connection returned with modified state
public function process(): void
{
    $pdo = $this->pool->acquire();

    $pdo->exec('SET SESSION sql_mode = "STRICT_ALL_TABLES"');
    // ... work ...

    $this->pool->release($pdo); // Returns with modified session state
}

// PROBLEMATIC: Prepared statements cached indefinitely
public function query(string $sql): array
{
    static $statements = [];

    if (!isset($statements[$sql])) {
        // Statement never released, holds connection reference
        $statements[$sql] = $this->pdo->prepare($sql);
    }

    return $statements[$sql]->execute()->fetchAll();
}
```

### 8. Doctrine Connection Issues

```php
// PROBLEMATIC: EntityManager not closed
foreach ($items as $item) {
    $this->em->persist($item);
}
// Missing: $this->em->flush(); $this->em->clear();

// PROBLEMATIC: Connection held during long operation
$this->em->beginTransaction();
$this->longRunningProcess(); // Connection held entire time
$this->em->commit();

// PROBLEMATIC: Stale connection after error
try {
    $this->em->persist($entity);
    $this->em->flush();
} catch (\Exception $e) {
    // EntityManager may be in invalid state
    // Connection may be broken
}
```

### 9. Queue/Worker Connection Issues

```php
// PROBLEMATIC: Long-running worker with single connection
while (true) {
    $job = $this->queue->pop();
    $this->process($job); // Uses same DB connection forever
    // Connection may timeout, be killed, etc.
}

// PROBLEMATIC: Connection cached in static
class Database
{
    private static ?PDO $connection = null;

    public static function get(): PDO
    {
        return self::$connection ??= new PDO($dsn);
    }
    // Connection never refreshed, may become stale
}
```

### 10. HTTP Client Connection Issues

```php
// PROBLEMATIC: No connection pooling
foreach ($urls as $url) {
    $response = file_get_contents($url); // No connection reuse
}

// PROBLEMATIC: Missing keepalive
$client = new GuzzleHttp\Client();
// Default may not use persistent connections efficiently

// FIXED: Configure for connection reuse
$client = new GuzzleHttp\Client([
    'http_errors' => false,
    'headers' => [
        'Connection' => 'keep-alive',
    ],
]);
```

## Secure Patterns

### Connection Pool Implementation

```php
// SECURE: Simple connection pool
final class ConnectionPool
{
    /** @var SplQueue<PDO> */
    private SplQueue $available;
    private int $created = 0;

    public function __construct(
        private readonly string $dsn,
        private readonly string $user,
        private readonly string $password,
        private readonly int $maxSize = 10,
        private readonly int $timeout = 5,
    ) {
        $this->available = new SplQueue();
    }

    public function acquire(): PDO
    {
        if (!$this->available->isEmpty()) {
            return $this->available->dequeue();
        }

        if ($this->created < $this->maxSize) {
            $this->created++;
            return $this->createConnection();
        }

        throw new PoolExhaustedException('No connections available');
    }

    public function release(PDO $connection): void
    {
        // Reset connection state
        if ($connection->inTransaction()) {
            $connection->rollBack();
        }

        $this->available->enqueue($connection);
    }

    private function createConnection(): PDO
    {
        return new PDO($this->dsn, $this->user, $this->password, [
            PDO::ATTR_TIMEOUT => $this->timeout,
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }
}
```

### Safe Connection Wrapper

```php
// SECURE: Automatic cleanup with closure
final class SafeDatabase
{
    public function __construct(
        private readonly ConnectionPool $pool,
    ) {}

    /**
     * @template T
     * @param callable(PDO): T $callback
     * @return T
     */
    public function withConnection(callable $callback): mixed
    {
        $connection = $this->pool->acquire();

        try {
            return $callback($connection);
        } finally {
            $this->pool->release($connection);
        }
    }
}

// Usage
$result = $db->withConnection(function (PDO $pdo) {
    return $pdo->query('SELECT * FROM users')->fetchAll();
});
```

### Connection Health Check

```php
// SECURE: Validate connection before use
final class ResilientConnectionPool
{
    public function acquire(): PDO
    {
        $connection = $this->pool->acquire();

        if (!$this->isHealthy($connection)) {
            $this->pool->remove($connection);
            return $this->createNewConnection();
        }

        return $connection;
    }

    private function isHealthy(PDO $connection): bool
    {
        try {
            $connection->query('SELECT 1');
            return true;
        } catch (\PDOException) {
            return false;
        }
    }
}
```

### Worker Connection Refresh

```php
// SECURE: Refresh connection in long-running workers
final class QueueWorker
{
    private int $processedCount = 0;
    private const REFRESH_INTERVAL = 100;

    public function run(): void
    {
        while ($job = $this->queue->pop()) {
            $this->process($job);

            if (++$this->processedCount % self::REFRESH_INTERVAL === 0) {
                $this->reconnect();
            }
        }
    }

    private function reconnect(): void
    {
        $this->connection = null; // Release old connection
        $this->connection = $this->createConnection();
    }
}
```
