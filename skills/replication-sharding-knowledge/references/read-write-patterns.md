# Read/Write Patterns Reference

## Doctrine DBAL PrimaryReadReplicaConnection Setup

### Symfony Configuration

```yaml
# config/packages/doctrine.yaml
doctrine:
    dbal:
        connections:
            default:
                wrapper_class: Doctrine\DBAL\Connections\PrimaryReadReplicaConnection
                driver: pdo_pgsql
                primary:
                    url: '%env(DATABASE_PRIMARY_URL)%'
                replica:
                    replica1:
                        url: '%env(DATABASE_REPLICA1_URL)%'
                    replica2:
                        url: '%env(DATABASE_REPLICA2_URL)%'
```

### Explicit Primary/Replica Control

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Doctrine\DBAL\Connections\PrimaryReadReplicaConnection;

final readonly class DoctrineReadWriteRepository
{
    public function __construct(
        private PrimaryReadReplicaConnection $connection,
    ) {}

    public function findById(string $id): ?array
    {
        // Automatically routes to replica
        $stmt = $this->connection->prepare('SELECT * FROM orders WHERE id = :id');
        $stmt->bindValue('id', $id);
        $result = $stmt->executeQuery();

        return $result->fetchAssociative() ?: null;
    }

    public function findByIdConsistent(string $id): ?array
    {
        // Force primary for critical reads (read-your-writes)
        $this->connection->ensureConnectedToPrimary();

        $stmt = $this->connection->prepare('SELECT * FROM orders WHERE id = :id');
        $stmt->bindValue('id', $id);
        $result = $stmt->executeQuery();

        return $result->fetchAssociative() ?: null;
    }

    public function save(string $id, array $data): void
    {
        // Writes always go to primary
        $this->connection->ensureConnectedToPrimary();

        $this->connection->insert('orders', array_merge(['id' => $id], $data));
    }
}
```

## Custom Connection Wrapper

### Full-Featured Read/Write Router

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

use Psr\Log\LoggerInterface;

final class ReadWriteRouter
{
    private bool $inTransaction = false;
    private ?\DateTimeImmutable $lastWriteAt = null;
    private int $readCount = 0;
    private int $writeCount = 0;

    /**
     * @param list<\PDO> $replicas
     */
    public function __construct(
        private readonly \PDO $primary,
        private readonly array $replicas,
        private readonly LoggerInterface $logger,
        private readonly int $stickyMasterSeconds = 5,
    ) {}

    public function query(string $sql, array $params = []): \PDOStatement
    {
        $connection = $this->route($sql);
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);

        return $stmt;
    }

    public function execute(string $sql, array $params = []): int
    {
        $stmt = $this->primary->prepare($sql);
        $stmt->execute($params);
        $this->writeCount++;
        $this->lastWriteAt = new \DateTimeImmutable();

        return $stmt->rowCount();
    }

    public function beginTransaction(): void
    {
        $this->primary->beginTransaction();
        $this->inTransaction = true;
    }

    public function commit(): void
    {
        $this->primary->commit();
        $this->inTransaction = false;
        $this->lastWriteAt = new \DateTimeImmutable();
    }

    public function rollBack(): void
    {
        $this->primary->rollBack();
        $this->inTransaction = false;
    }

    public function getStats(): array
    {
        return [
            'read_count' => $this->readCount,
            'write_count' => $this->writeCount,
            'replica_count' => count($this->replicas),
            'in_transaction' => $this->inTransaction,
        ];
    }

    private function route(string $sql): \PDO
    {
        if ($this->inTransaction) {
            $this->logger->debug('Routing to primary: inside transaction');
            return $this->primary;
        }

        if ($this->isWriteQuery($sql)) {
            $this->writeCount++;
            $this->lastWriteAt = new \DateTimeImmutable();
            return $this->primary;
        }

        if ($this->isStickyMasterActive()) {
            $this->logger->debug('Routing to primary: sticky master active');
            $this->readCount++;
            return $this->primary;
        }

        $this->readCount++;
        return $this->selectReplica();
    }

    private function isWriteQuery(string $sql): bool
    {
        $normalized = strtoupper(ltrim($sql));

        return str_starts_with($normalized, 'INSERT')
            || str_starts_with($normalized, 'UPDATE')
            || str_starts_with($normalized, 'DELETE')
            || str_starts_with($normalized, 'CREATE')
            || str_starts_with($normalized, 'ALTER')
            || str_starts_with($normalized, 'DROP')
            || str_starts_with($normalized, 'TRUNCATE')
            || str_contains($normalized, 'FOR UPDATE')
            || str_contains($normalized, 'FOR SHARE');
    }

    private function isStickyMasterActive(): bool
    {
        if ($this->lastWriteAt === null) {
            return false;
        }

        $elapsed = (new \DateTimeImmutable())->getTimestamp()
            - $this->lastWriteAt->getTimestamp();

        return $elapsed < $this->stickyMasterSeconds;
    }

    private function selectReplica(): \PDO
    {
        if ($this->replicas === []) {
            return $this->primary;
        }

        return $this->replicas[array_rand($this->replicas)];
    }
}
```

## Laravel Database Read/Write Config

### Full Configuration

```php
<?php

declare(strict_types=1);

// config/database.php
return [
    'default' => env('DB_CONNECTION', 'pgsql'),

    'connections' => [
        'pgsql' => [
            'driver' => 'pgsql',
            'read' => [
                'host' => [
                    env('DB_READ_HOST_1', '127.0.0.1'),
                    env('DB_READ_HOST_2', '127.0.0.1'),
                ],
                'port' => env('DB_READ_PORT', '5432'),
            ],
            'write' => [
                'host' => [
                    env('DB_WRITE_HOST', '127.0.0.1'),
                ],
                'port' => env('DB_WRITE_PORT', '5432'),
            ],
            'sticky' => true,
            'database' => env('DB_DATABASE', 'forge'),
            'username' => env('DB_USERNAME', 'forge'),
            'password' => env('DB_PASSWORD', ''),
            'charset' => 'utf8',
            'prefix' => '',
            'schema' => 'public',
            'sslmode' => env('DB_SSLMODE', 'prefer'),
        ],
    ],
];
```

### Forcing Primary in Laravel

```php
<?php

declare(strict_types=1);

namespace App\Application\UseCase;

use Illuminate\Support\Facades\DB;

final readonly class PlaceOrderUseCase
{
    public function execute(PlaceOrderCommand $command): OrderId
    {
        return DB::transaction(function () use ($command) {
            // All queries inside transaction go to write connection
            $order = Order::create([
                'customer_id' => $command->customerId,
                'total' => $command->total,
            ]);

            // This read also goes to write connection (inside transaction)
            $inventory = Inventory::where('product_id', $command->productId)
                ->lockForUpdate()
                ->first();

            $inventory->decrement('quantity', $command->quantity);

            return new OrderId($order->id);
        });
    }
}
```

## Transaction-Aware Routing

### Decorator Pattern

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final class TransactionAwareDecorator implements ConnectionInterface
{
    private bool $inTransaction = false;
    private int $transactionDepth = 0;

    public function __construct(
        private readonly \PDO $primary,
        private readonly \PDO $replica,
    ) {}

    public function select(string $sql, array $params = []): array
    {
        $pdo = $this->inTransaction ? $this->primary : $this->replica;
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);

        return $stmt->fetchAll(\PDO::FETCH_ASSOC);
    }

    public function insert(string $sql, array $params = []): string
    {
        $stmt = $this->primary->prepare($sql);
        $stmt->execute($params);

        return $this->primary->lastInsertId();
    }

    public function beginTransaction(): void
    {
        if ($this->transactionDepth === 0) {
            $this->primary->beginTransaction();
            $this->inTransaction = true;
        } else {
            $this->primary->exec(sprintf('SAVEPOINT sp_%d', $this->transactionDepth));
        }

        $this->transactionDepth++;
    }

    public function commit(): void
    {
        $this->transactionDepth--;

        if ($this->transactionDepth === 0) {
            $this->primary->commit();
            $this->inTransaction = false;
        } else {
            $this->primary->exec(sprintf('RELEASE SAVEPOINT sp_%d', $this->transactionDepth));
        }
    }

    public function rollBack(): void
    {
        $this->transactionDepth--;

        if ($this->transactionDepth === 0) {
            $this->primary->rollBack();
            $this->inTransaction = false;
        } else {
            $this->primary->exec(sprintf(
                'ROLLBACK TO SAVEPOINT sp_%d',
                $this->transactionDepth,
            ));
        }
    }
}
```

## Replica Lag Detection and Fallback

### PostgreSQL Lag Monitor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

use Psr\Log\LoggerInterface;

final readonly class ReplicaLagMonitor
{
    public function __construct(
        private \PDO $replica,
        private LoggerInterface $logger,
    ) {}

    public function getLagSeconds(): float
    {
        $stmt = $this->replica->query(
            "SELECT CASE
                WHEN pg_last_xact_replay_timestamp() IS NULL THEN -1
                ELSE EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp()))
            END AS lag_seconds"
        );

        $row = $stmt->fetch(\PDO::FETCH_ASSOC);

        return (float) $row['lag_seconds'];
    }

    public function isHealthy(float $maxLagSeconds = 2.0): bool
    {
        $lag = $this->getLagSeconds();

        if ($lag < 0) {
            $this->logger->warning('Replica lag unavailable (no replay timestamp)');
            return false;
        }

        if ($lag > $maxLagSeconds) {
            $this->logger->warning('Replica lag exceeds threshold', [
                'lag_seconds' => $lag,
                'threshold' => $maxLagSeconds,
            ]);
            return false;
        }

        return true;
    }
}
```

### MySQL Lag Monitor

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final readonly class MysqlReplicaLagMonitor
{
    public function __construct(
        private \PDO $replica,
    ) {}

    public function getLagSeconds(): ?int
    {
        $stmt = $this->replica->query('SHOW SLAVE STATUS');
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);

        if ($row === false) {
            return null;
        }

        return isset($row['Seconds_Behind_Master'])
            ? (int) $row['Seconds_Behind_Master']
            : null;
    }
}
```

## Health Check for Replicas

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

use Psr\Log\LoggerInterface;

final class ReplicaHealthChecker
{
    /** @var array<string, bool> */
    private array $healthStatus = [];

    /**
     * @param array<string, \PDO> $replicas
     */
    public function __construct(
        private readonly array $replicas,
        private readonly \PDO $primary,
        private readonly LoggerInterface $logger,
        private readonly float $maxLagSeconds = 2.0,
        private readonly int $queryTimeoutMs = 1000,
    ) {}

    public function getHealthyReplica(): \PDO
    {
        foreach ($this->replicas as $name => $replica) {
            if ($this->checkReplica($name, $replica)) {
                return $replica;
            }
        }

        $this->logger->warning('No healthy replicas available, falling back to primary');

        return $this->primary;
    }

    private function checkReplica(string $name, \PDO $replica): bool
    {
        try {
            $stmt = $replica->query('SELECT 1');
            $stmt->fetch();

            $lagMonitor = new ReplicaLagMonitor($replica, $this->logger);
            $healthy = $lagMonitor->isHealthy($this->maxLagSeconds);

            $this->healthStatus[$name] = $healthy;

            return $healthy;
        } catch (\Throwable $e) {
            $this->logger->error('Replica health check failed', [
                'replica' => $name,
                'error' => $e->getMessage(),
            ]);

            $this->healthStatus[$name] = false;

            return false;
        }
    }

    /**
     * @return array<string, bool>
     */
    public function getHealthStatus(): array
    {
        return $this->healthStatus;
    }
}
```

## Anti-Patterns

| Anti-Pattern | Problem | Correct Approach |
|--------------|---------|-----------------|
| All reads from primary | Primary overloaded, replicas unused | Route SELECTs to replicas |
| No sticky master | Read stale data after write | Enable sticky master (5-10s) |
| Replica in transaction | Inconsistent reads | All transaction queries to primary |
| No lag monitoring | Silent stale data | Monitor and alert on lag |
| No fallback | Read failures when replica down | Fall back to primary |
| Long-running queries on primary | Block replication | Route analytics to replica |
| `SELECT FOR UPDATE` on replica | No lock acquired, data race | Always route to primary |
