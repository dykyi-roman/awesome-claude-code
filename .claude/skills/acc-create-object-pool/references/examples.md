# Object Pool Pattern Examples

## Database Connection Pool

**File:** `src/Infrastructure/Persistence/ConnectionPool.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Infrastructure\Pool\ObjectPool;
use Infrastructure\Pool\PoolConfig;
use Infrastructure\Pool\PoolInterface;
use Psr\Log\LoggerInterface;

final class ConnectionPool
{
    /** @var PoolInterface<PoolableConnection> */
    private PoolInterface $pool;

    public function __construct(
        private readonly ConnectionFactory $factory,
        PoolConfig $config,
        LoggerInterface $logger
    ) {
        $this->pool = new ObjectPool(
            name: 'database',
            factory: fn() => $this->factory->create(),
            config: $config,
            logger: $logger
        );
    }

    public function getConnection(): PoolableConnection
    {
        return $this->pool->acquire();
    }

    public function releaseConnection(PoolableConnection $connection): void
    {
        $this->pool->release($connection);
    }

    /**
     * @template T
     * @param callable(PoolableConnection): T $operation
     * @return T
     */
    public function execute(callable $operation): mixed
    {
        $connection = $this->getConnection();

        try {
            return $operation($connection);
        } finally {
            $this->releaseConnection($connection);
        }
    }
}
```

**File:** `src/Infrastructure/Persistence/PoolableConnection.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Infrastructure\Pool\PoolableInterface;

final class PoolableConnection implements PoolableInterface
{
    private bool $inTransaction = false;

    public function __construct(
        private readonly \PDO $pdo
    ) {}

    public function getPdo(): \PDO
    {
        return $this->pdo;
    }

    public function beginTransaction(): void
    {
        $this->pdo->beginTransaction();
        $this->inTransaction = true;
    }

    public function commit(): void
    {
        $this->pdo->commit();
        $this->inTransaction = false;
    }

    public function rollback(): void
    {
        $this->pdo->rollBack();
        $this->inTransaction = false;
    }

    public function reset(): void
    {
        if ($this->inTransaction) {
            $this->rollback();
        }
    }

    public function isValid(): bool
    {
        try {
            $this->pdo->query('SELECT 1');
            return true;
        } catch (\PDOException) {
            return false;
        }
    }

    public function close(): void
    {
        if ($this->inTransaction) {
            $this->rollback();
        }
    }
}
```

---

## HTTP Client Pool

**File:** `src/Infrastructure/Http/HttpClientPool.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Pool\ObjectPool;
use Infrastructure\Pool\PoolConfig;
use Infrastructure\Pool\PoolInterface;
use Psr\Log\LoggerInterface;

final class HttpClientPool
{
    /** @var PoolInterface<PoolableHttpClient> */
    private PoolInterface $pool;

    public function __construct(
        string $baseUrl,
        array $defaultHeaders,
        LoggerInterface $logger
    ) {
        $this->pool = new ObjectPool(
            name: 'http-client',
            factory: fn() => new PoolableHttpClient($baseUrl, $defaultHeaders),
            config: PoolConfig::forHttpClients(),
            logger: $logger
        );
    }

    /**
     * @template T
     * @param callable(PoolableHttpClient): T $operation
     * @return T
     */
    public function execute(callable $operation): mixed
    {
        $client = $this->pool->acquire();

        try {
            return $operation($client);
        } finally {
            $this->pool->release($client);
        }
    }
}
```

**File:** `src/Infrastructure/Http/PoolableHttpClient.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Pool\PoolableInterface;

final class PoolableHttpClient implements PoolableInterface
{
    private \CurlHandle $curl;
    private array $requestHeaders = [];

    public function __construct(
        private readonly string $baseUrl,
        private readonly array $defaultHeaders
    ) {
        $this->curl = curl_init();
        $this->configure();
    }

    public function get(string $path, array $headers = []): Response
    {
        return $this->request('GET', $path, null, $headers);
    }

    public function post(string $path, mixed $body, array $headers = []): Response
    {
        return $this->request('POST', $path, $body, $headers);
    }

    public function reset(): void
    {
        curl_reset($this->curl);
        $this->configure();
        $this->requestHeaders = [];
    }

    public function isValid(): bool
    {
        return is_resource($this->curl) || $this->curl instanceof \CurlHandle;
    }

    public function close(): void
    {
        curl_close($this->curl);
    }

    private function configure(): void
    {
        curl_setopt_array($this->curl, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_FOLLOWLOCATION => true,
            CURLOPT_TIMEOUT => 30,
            CURLOPT_CONNECTTIMEOUT => 10,
        ]);
    }

    private function request(
        string $method,
        string $path,
        mixed $body,
        array $headers
    ): Response {
        $url = $this->baseUrl . $path;
        $allHeaders = array_merge($this->defaultHeaders, $headers);

        curl_setopt_array($this->curl, [
            CURLOPT_URL => $url,
            CURLOPT_CUSTOMREQUEST => $method,
            CURLOPT_HTTPHEADER => $this->formatHeaders($allHeaders),
        ]);

        if ($body !== null) {
            curl_setopt($this->curl, CURLOPT_POSTFIELDS, json_encode($body));
        }

        $response = curl_exec($this->curl);
        $statusCode = curl_getinfo($this->curl, CURLINFO_HTTP_CODE);

        return new Response($statusCode, $response ?: '');
    }

    private function formatHeaders(array $headers): array
    {
        return array_map(
            fn($key, $value) => "$key: $value",
            array_keys($headers),
            array_values($headers)
        );
    }
}
```

---

## Unit Tests

### ObjectPool Test

**File:** `tests/Unit/Infrastructure/Pool/ObjectPoolTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Pool;

use Infrastructure\Pool\ObjectPool;
use Infrastructure\Pool\PoolableInterface;
use Infrastructure\Pool\PoolConfig;
use Infrastructure\Pool\PoolExhaustedException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(ObjectPool::class)]
final class ObjectPoolTest extends TestCase
{
    public function testAcquiresNewObject(): void
    {
        $pool = $this->createPool(maxSize: 5);

        $object = $pool->acquire();

        self::assertInstanceOf(PoolableInterface::class, $object);
        self::assertSame(1, $pool->getActiveCount());
    }

    public function testReleasesObjectBackToPool(): void
    {
        $pool = $this->createPool(maxSize: 5);

        $object = $pool->acquire();
        $pool->release($object);

        self::assertSame(0, $pool->getActiveCount());
        self::assertSame(1, $pool->getAvailableCount());
    }

    public function testReusesReleasedObjects(): void
    {
        $pool = $this->createPool(maxSize: 1);

        $object1 = $pool->acquire();
        $pool->release($object1);

        $object2 = $pool->acquire();

        self::assertSame($object1, $object2);
    }

    public function testThrowsWhenExhausted(): void
    {
        $pool = $this->createPool(maxSize: 1, maxWaitMs: 10);

        $pool->acquire();

        $this->expectException(PoolExhaustedException::class);
        $pool->acquire();
    }

    public function testWarmsUpPool(): void
    {
        $pool = $this->createPool(minSize: 3, maxSize: 5);

        self::assertSame(3, $pool->getAvailableCount());
    }

    public function testClearsPool(): void
    {
        $pool = $this->createPool(minSize: 3, maxSize: 5);

        $pool->acquire();
        $pool->clear();

        self::assertSame(0, $pool->getAvailableCount());
        self::assertSame(0, $pool->getActiveCount());
    }

    public function testDiscardsInvalidObjectsOnAcquire(): void
    {
        $createCount = 0;
        $pool = new ObjectPool(
            name: 'test',
            factory: function () use (&$createCount) {
                $createCount++;
                $mock = $this->createMock(PoolableInterface::class);
                $mock->method('isValid')->willReturn($createCount > 1);
                return $mock;
            },
            config: new PoolConfig(validateOnAcquire: true),
            logger: new NullLogger()
        );

        $pool->acquire();
        $pool->release($pool->acquire());

        $object = $pool->acquire();

        self::assertSame(2, $createCount);
    }

    public function testResetsObjectOnRelease(): void
    {
        $mock = $this->createMock(PoolableInterface::class);
        $mock->expects($this->once())->method('reset');
        $mock->method('isValid')->willReturn(true);

        $pool = new ObjectPool(
            name: 'test',
            factory: fn() => $mock,
            config: PoolConfig::default(),
            logger: new NullLogger()
        );

        $object = $pool->acquire();
        $pool->release($object);
    }

    private function createPool(
        int $minSize = 0,
        int $maxSize = 10,
        int $maxWaitMs = 100
    ): ObjectPool {
        return new ObjectPool(
            name: 'test',
            factory: function () {
                $mock = $this->createMock(PoolableInterface::class);
                $mock->method('isValid')->willReturn(true);
                return $mock;
            },
            config: new PoolConfig(
                minSize: $minSize,
                maxSize: $maxSize,
                maxWaitTimeMs: $maxWaitMs
            ),
            logger: new NullLogger()
        );
    }
}
```

### Connection Pool Test

**File:** `tests/Unit/Infrastructure/Persistence/ConnectionPoolTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Persistence;

use Infrastructure\Persistence\ConnectionPool;
use Infrastructure\Persistence\PoolableConnection;
use Infrastructure\Pool\PoolConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Log\NullLogger;

#[Group('unit')]
#[CoversClass(ConnectionPool::class)]
final class ConnectionPoolTest extends TestCase
{
    public function testExecutesWithConnection(): void
    {
        $factory = $this->createMock(ConnectionFactory::class);
        $factory->method('create')->willReturn($this->createConnection());

        $pool = new ConnectionPool(
            factory: $factory,
            config: PoolConfig::default(),
            logger: new NullLogger()
        );

        $result = $pool->execute(fn($conn) => 'executed');

        self::assertSame('executed', $result);
    }

    public function testReleasesConnectionAfterExecution(): void
    {
        $connection = $this->createConnection();
        $factory = $this->createMock(ConnectionFactory::class);
        $factory->method('create')->willReturn($connection);

        $pool = new ConnectionPool(
            factory: $factory,
            config: new PoolConfig(maxSize: 1),
            logger: new NullLogger()
        );

        $pool->execute(fn($conn) => null);

        $secondConnection = $pool->getConnection();
        self::assertSame($connection, $secondConnection);
    }

    public function testReleasesConnectionOnException(): void
    {
        $connection = $this->createConnection();
        $factory = $this->createMock(ConnectionFactory::class);
        $factory->method('create')->willReturn($connection);

        $pool = new ConnectionPool(
            factory: $factory,
            config: new PoolConfig(maxSize: 1),
            logger: new NullLogger()
        );

        try {
            $pool->execute(fn($conn) => throw new \RuntimeException('fail'));
        } catch (\RuntimeException) {}

        $secondConnection = $pool->getConnection();
        self::assertSame($connection, $secondConnection);
    }

    private function createConnection(): PoolableConnection
    {
        $mock = $this->createMock(PoolableConnection::class);
        $mock->method('isValid')->willReturn(true);
        return $mock;
    }
}
```
