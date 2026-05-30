# Read/Write Connection Proxy Examples

## Repository Using Connection Proxy

**File:** `src/{architecture-path}/Persistence/UserRepository.php`

```php
<?php

declare(strict_types=1);

namespace Persistence;

use User\UserRepositoryInterface;
use Database\ReadWriteConnectionInterface;

final readonly class UserRepository implements UserRepositoryInterface
{
    public function __construct(
        private ReadWriteConnectionInterface $connection
    ) {}

    public function findById(string $id): ?array
    {
        $rows = $this->connection->query(
            'SELECT * FROM users WHERE id = ?',
            [$id]
        );

        return $rows[0] ?? null;
    }

    public function findActive(): array
    {
        return $this->connection->query(
            'SELECT * FROM users WHERE active = ? ORDER BY created_at DESC',
            [1]
        );
    }

    public function save(array $userData): void
    {
        $this->connection->execute(
            'INSERT INTO users (id, name, email, active) VALUES (?, ?, ?, ?)
             ON DUPLICATE KEY UPDATE name = VALUES(name), email = VALUES(email)',
            [$userData['id'], $userData['name'], $userData['email'], $userData['active']]
        );
    }

    public function delete(string $id): void
    {
        $this->connection->execute(
            'DELETE FROM users WHERE id = ?',
            [$id]
        );
    }
}
```

---

## Transactional Use Case

**File:** `src/{architecture-path}/UseCase/PlaceOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Order;

use Database\ReadWriteConnectionInterface;

final readonly class PlaceOrderUseCase
{
    public function __construct(
        private ReadWriteConnectionInterface $connection
    ) {}

    public function execute(PlaceOrderRequest $request): string
    {
        $this->connection->beginTransaction();

        try {
            $this->connection->execute(
                'INSERT INTO orders (id, customer_id, total) VALUES (?, ?, ?)',
                [$request->orderId, $request->customerId, $request->total]
            );

            foreach ($request->items as $item) {
                $this->connection->execute(
                    'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
                    [$request->orderId, $item['product_id'], $item['quantity'], $item['price']]
                );

                $this->connection->execute(
                    'UPDATE inventory SET stock = stock - ? WHERE product_id = ?',
                    [$item['quantity'], $item['product_id']]
                );
            }

            $this->connection->commit();

            return $request->orderId;
        } catch (\Throwable $e) {
            $this->connection->rollback();
            throw $e;
        }
    }
}
```

---

## Connection Factory

**File:** `src/{architecture-path}/Database/ConnectionFactory.php`

```php
<?php

declare(strict_types=1);

namespace Database;

final readonly class ConnectionFactory
{
    public static function create(ConnectionConfig $config): ReadWriteConnectionInterface
    {
        $healthChecker = new ReplicaHealthChecker($config, checkIntervalSeconds: 30);

        return new ReadWriteConnectionProxy($config, $healthChecker);
    }

    public static function fromEnvironment(): ReadWriteConnectionInterface
    {
        $config = new ConnectionConfig(
            primaryDsn: $_ENV['DB_PRIMARY_DSN'],
            replicaDsns: array_filter([
                $_ENV['DB_REPLICA1_DSN'] ?? '',
                $_ENV['DB_REPLICA2_DSN'] ?? '',
            ]),
            stickyAfterWrite: true,
            username: $_ENV['DB_USERNAME'] ?? '',
            password: $_ENV['DB_PASSWORD'] ?? ''
        );

        return self::create($config);
    }
}
```

---

## Unit Tests

### ConnectionConfigTest

**File:** `tests/Unit/ConnectionConfigTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Database;

use Database\ConnectionConfig;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ConnectionConfig::class)]
final class ConnectionConfigTest extends TestCase
{
    public function testCreateWithPrimaryOnly(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'mysql:host=localhost;dbname=app');

        self::assertSame('mysql:host=localhost;dbname=app', $config->primaryDsn);
        self::assertFalse($config->hasReplicas());
        self::assertSame(0, $config->replicaCount());
    }

    public function testCreateWithReplicas(): void
    {
        $config = new ConnectionConfig(
            primaryDsn: 'mysql:host=primary;dbname=app',
            replicaDsns: ['mysql:host=replica1;dbname=app', 'mysql:host=replica2;dbname=app']
        );

        self::assertTrue($config->hasReplicas());
        self::assertSame(2, $config->replicaCount());
    }

    public function testStickyAfterWriteDefaultsToTrue(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'mysql:host=localhost;dbname=app');

        self::assertTrue($config->stickyAfterWrite);
    }

    public function testRejectsEmptyPrimaryDsn(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new ConnectionConfig(primaryDsn: '');
    }
}
```

---

### ReadWriteConnectionProxyTest

**File:** `tests/Unit/ReadWriteConnectionProxyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Database;

use Database\ConnectionConfig;
use Database\ReadWriteConnectionProxy;
use Database\ReplicaHealthChecker;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ReadWriteConnectionProxy::class)]
final class ReadWriteConnectionProxyTest extends TestCase
{
    public function testStartsOutsideTransaction(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'sqlite::memory:');
        $healthChecker = $this->createMock(ReplicaHealthChecker::class);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        self::assertFalse($proxy->inTransaction());
    }

    public function testSelectQueryUsesReplica(): void
    {
        $config = new ConnectionConfig(
            primaryDsn: 'sqlite::memory:',
            replicaDsns: ['sqlite::memory:']
        );

        $healthChecker = $this->createMock(ReplicaHealthChecker::class);
        $healthChecker->method('getHealthyIndexes')->willReturn([0]);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        $result = $proxy->query('SELECT 1 AS val');

        self::assertSame([['val' => '1']], $result);
    }

    public function testFallsToPrimaryWhenNoHealthyReplicas(): void
    {
        $config = new ConnectionConfig(
            primaryDsn: 'sqlite::memory:',
            replicaDsns: ['sqlite::memory:']
        );

        $healthChecker = $this->createMock(ReplicaHealthChecker::class);
        $healthChecker->method('getHealthyIndexes')->willReturn([]);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        $result = $proxy->query('SELECT 1 AS val');

        self::assertSame([['val' => '1']], $result);
    }

    public function testExecuteRoutesToPrimary(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'sqlite::memory:');
        $healthChecker = $this->createMock(ReplicaHealthChecker::class);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        $proxy->execute('CREATE TABLE test (id INTEGER PRIMARY KEY)');
        $affected = $proxy->execute('INSERT INTO test (id) VALUES (1)');

        self::assertSame(1, $affected);
    }

    public function testTransactionRoutesAllToPrimary(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'sqlite::memory:');
        $healthChecker = $this->createMock(ReplicaHealthChecker::class);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        $proxy->execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)');

        $proxy->beginTransaction();
        self::assertTrue($proxy->inTransaction());

        $proxy->execute('INSERT INTO test (id, name) VALUES (1, ?)', ['Alice']);
        $rows = $proxy->query('SELECT * FROM test WHERE id = 1');

        $proxy->commit();
        self::assertFalse($proxy->inTransaction());
        self::assertCount(1, $rows);
    }

    public function testRollbackRevertsChanges(): void
    {
        $config = new ConnectionConfig(primaryDsn: 'sqlite::memory:');
        $healthChecker = $this->createMock(ReplicaHealthChecker::class);

        $proxy = new ReadWriteConnectionProxy($config, $healthChecker);

        $proxy->execute('CREATE TABLE test (id INTEGER PRIMARY KEY)');
        $proxy->beginTransaction();
        $proxy->execute('INSERT INTO test (id) VALUES (1)');
        $proxy->rollback();

        $rows = $proxy->query('SELECT * FROM test');

        self::assertCount(0, $rows);
    }
}
```
