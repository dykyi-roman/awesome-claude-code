# Read/Write Connection Proxy Templates

## ConnectionRole Enum

**File:** `src/Infrastructure/Database/ConnectionRole.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

enum ConnectionRole: string
{
    case Primary = 'primary';
    case Replica = 'replica';
}
```

---

## ReadWriteConnectionInterface

**File:** `src/Infrastructure/Database/ReadWriteConnectionInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

interface ReadWriteConnectionInterface
{
    /**
     * @param array<int|string, mixed> $params
     * @return list<array<string, mixed>>
     */
    public function query(string $sql, array $params = []): array;

    /**
     * @param array<int|string, mixed> $params
     * @return int Affected row count
     */
    public function execute(string $sql, array $params = []): int;

    public function beginTransaction(): void;

    public function commit(): void;

    public function rollback(): void;

    public function inTransaction(): bool;
}
```

---

## ConnectionConfig

**File:** `src/Infrastructure/Database/ConnectionConfig.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final readonly class ConnectionConfig
{
    /**
     * @param list<string> $replicaDsns
     */
    public function __construct(
        public string $primaryDsn,
        public array $replicaDsns = [],
        public bool $stickyAfterWrite = true,
        public string $username = '',
        public string $password = ''
    ) {
        if ($this->primaryDsn === '') {
            throw new \InvalidArgumentException('Primary DSN cannot be empty');
        }
    }

    public function hasReplicas(): bool
    {
        return $this->replicaDsns !== [];
    }

    public function replicaCount(): int
    {
        return count($this->replicaDsns);
    }
}
```

---

## ReadWriteConnectionProxy

**File:** `src/Infrastructure/Database/ReadWriteConnectionProxy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final class ReadWriteConnectionProxy implements ReadWriteConnectionInterface
{
    private const READ_PATTERN = '/^\s*(SELECT|SHOW|DESCRIBE|EXPLAIN)\b/i';
    private const LOCKING_PATTERN = '/\b(FOR\s+UPDATE|FOR\s+SHARE|LOCK\s+IN)\b/i';

    private ?\PDO $primaryConnection = null;
    /** @var array<int, \PDO> */
    private array $replicaConnections = [];
    private bool $inTransaction = false;
    private bool $hadWrite = false;

    public function __construct(
        private readonly ConnectionConfig $config,
        private readonly ReplicaHealthChecker $healthChecker
    ) {}

    public function query(string $sql, array $params = []): array
    {
        $connection = $this->resolveConnection($sql);
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);

        return $stmt->fetchAll(\PDO::FETCH_ASSOC);
    }

    public function execute(string $sql, array $params = []): int
    {
        $this->hadWrite = true;
        $connection = $this->getPrimary();
        $stmt = $connection->prepare($sql);
        $stmt->execute($params);

        return $stmt->rowCount();
    }

    public function beginTransaction(): void
    {
        $this->inTransaction = true;
        $this->getPrimary()->beginTransaction();
    }

    public function commit(): void
    {
        $this->getPrimary()->commit();
        $this->inTransaction = false;
    }

    public function rollback(): void
    {
        $this->getPrimary()->rollBack();
        $this->inTransaction = false;
    }

    public function inTransaction(): bool
    {
        return $this->inTransaction;
    }

    private function resolveConnection(string $sql): \PDO
    {
        if ($this->shouldUsePrimary($sql)) {
            return $this->getPrimary();
        }

        return $this->getReplica();
    }

    private function shouldUsePrimary(string $sql): bool
    {
        if ($this->inTransaction) {
            return true;
        }

        if ($this->hadWrite && $this->config->stickyAfterWrite) {
            return true;
        }

        if (!preg_match(self::READ_PATTERN, $sql)) {
            return true;
        }

        if (preg_match(self::LOCKING_PATTERN, $sql)) {
            return true;
        }

        return !$this->config->hasReplicas();
    }

    private function getPrimary(): \PDO
    {
        if ($this->primaryConnection === null) {
            $this->primaryConnection = $this->createConnection($this->config->primaryDsn);
        }

        return $this->primaryConnection;
    }

    private function getReplica(): \PDO
    {
        $healthyIndexes = $this->healthChecker->getHealthyIndexes();

        if ($healthyIndexes === []) {
            return $this->getPrimary();
        }

        $index = $healthyIndexes[array_rand($healthyIndexes)];

        if (!isset($this->replicaConnections[$index])) {
            $this->replicaConnections[$index] = $this->createConnection(
                $this->config->replicaDsns[$index]
            );
        }

        return $this->replicaConnections[$index];
    }

    private function createConnection(string $dsn): \PDO
    {
        return new \PDO(
            $dsn,
            $this->config->username,
            $this->config->password,
            [
                \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
                \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
                \PDO::ATTR_EMULATE_PREPARES => false,
            ]
        );
    }
}
```

---

## ReplicaHealthChecker

**File:** `src/Infrastructure/Database/ReplicaHealthChecker.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Database;

final class ReplicaHealthChecker
{
    /** @var array<int, bool> */
    private array $healthStatus = [];
    private ?float $lastCheckTime = null;

    public function __construct(
        private readonly ConnectionConfig $config,
        private readonly int $checkIntervalSeconds = 30
    ) {}

    /**
     * @return list<int>
     */
    public function getHealthyIndexes(): array
    {
        $this->refreshIfNeeded();

        $healthy = [];
        foreach ($this->config->replicaDsns as $index => $dsn) {
            if ($this->healthStatus[$index] ?? true) {
                $healthy[] = $index;
            }
        }

        return $healthy;
    }

    public function markUnhealthy(int $index): void
    {
        $this->healthStatus[$index] = false;
    }

    public function markHealthy(int $index): void
    {
        $this->healthStatus[$index] = true;
    }

    private function refreshIfNeeded(): void
    {
        $now = microtime(true);

        if ($this->lastCheckTime !== null && ($now - $this->lastCheckTime) < $this->checkIntervalSeconds) {
            return;
        }

        foreach ($this->config->replicaDsns as $index => $dsn) {
            try {
                $pdo = new \PDO($dsn, $this->config->username, $this->config->password);
                $pdo->query('SELECT 1');
                $this->healthStatus[$index] = true;
            } catch (\PDOException) {
                $this->healthStatus[$index] = false;
            }
        }

        $this->lastCheckTime = $now;
    }
}
```
