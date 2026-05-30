---
name: replication-sharding-knowledge
description: Replication and Sharding knowledge base. Provides read/write splitting at application level, connection wrapper patterns, replica lag handling, and query routing for database scaling audits.
---

# Replication and Sharding Knowledge Base

Quick reference for application-level read/write splitting, connection routing, and replica lag handling in PHP applications.

## Master-Slave (Primary-Replica) Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                   PRIMARY-REPLICA READ/WRITE SPLIT                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Application Layer                                                 │
│       │                                                              │
│       ├── INSERT / UPDATE / DELETE ──▶ Primary (Master)              │
│       │                                   │                         │
│       │                          Replication (async)                │
│       │                                   │                         │
│       │                        ┌──────────┼──────────┐              │
│       │                        │          │          │              │
│       │                        ▼          ▼          ▼              │
│       └── SELECT ──────────▶ Replica 1  Replica 2  Replica 3       │
│           (round-robin)                                             │
│                                                                      │
│   Benefits:                                                         │
│   • Read throughput scales linearly with replica count              │
│   • Primary handles only writes → reduced write latency             │
│   • Replicas can be in different regions → lower read latency       │
│                                                                      │
│   Trade-offs:                                                       │
│   • Replication lag: replicas may return stale data                 │
│   • Write scaling requires sharding (replicas don't help)           │
│   • Application must be aware of routing                            │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Connection Wrapper Pattern

Route SELECT queries to replicas, INSERT/UPDATE/DELETE to primary.

```php
<?php

declare(strict_types=1);

namespace Database;

final class ReadWriteConnection
{
    private ?\PDO $primaryConnection = null;
    private ?\PDO $replicaConnection = null;
    private bool $forcePrimary = false;

    /**
     * @param list<array{host: string, port: int}> $replicaConfigs
     */
    public function __construct(
        private readonly ConnectionConfig $primaryConfig,
        private readonly array $replicaConfigs,
        private readonly string $database,
        private readonly string $username,
        private readonly string $password,
    ) {}

    public function primary(): \PDO
    {
        if ($this->primaryConnection === null) {
            $this->primaryConnection = $this->connect(
                $this->primaryConfig->host,
                $this->primaryConfig->port,
            );
        }

        return $this->primaryConnection;
    }

    public function replica(): \PDO
    {
        if ($this->forcePrimary) {
            return $this->primary();
        }

        if ($this->replicaConnection === null) {
            $config = $this->replicaConfigs[array_rand($this->replicaConfigs)];
            $this->replicaConnection = $this->connect($config['host'], $config['port']);
        }

        return $this->replicaConnection;
    }

    public function usePrimary(): void
    {
        $this->forcePrimary = true;
    }

    public function releasePrimary(): void
    {
        $this->forcePrimary = false;
    }

    private function connect(string $host, int $port): \PDO
    {
        $dsn = sprintf('pgsql:host=%s;port=%d;dbname=%s', $host, $port, $this->database);

        return new \PDO($dsn, $this->username, $this->password, [
            \PDO::ATTR_ERRMODE => \PDO::ERRMODE_EXCEPTION,
            \PDO::ATTR_DEFAULT_FETCH_MODE => \PDO::FETCH_ASSOC,
            \PDO::ATTR_EMULATE_PREPARES => false,
        ]);
    }
}
```

## Query Routing Decision Tree

```
┌─────────────────────────────────────────────────────────────────────┐
│                   QUERY ROUTING DECISION TREE                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   Incoming Query                                                    │
│       │                                                              │
│       ▼                                                              │
│   Inside transaction?                                               │
│       │                                                              │
│       ├── YES ──▶ Route to PRIMARY (all queries in TX go to master) │
│       │                                                              │
│       └── NO                                                        │
│           │                                                          │
│           ▼                                                          │
│       Is write query? (INSERT/UPDATE/DELETE/DDL)                    │
│           │                                                          │
│           ├── YES ──▶ Route to PRIMARY                              │
│           │              │                                           │
│           │              ▼                                           │
│           │          Set "sticky master" flag                       │
│           │          (next reads go to primary for N seconds)       │
│           │                                                          │
│           └── NO (SELECT)                                           │
│               │                                                      │
│               ▼                                                      │
│           "Sticky master" active?                                   │
│               │                                                      │
│               ├── YES ──▶ Route to PRIMARY (read-your-writes)       │
│               │                                                      │
│               └── NO                                                │
│                   │                                                  │
│                   ▼                                                  │
│               Critical read? (consistency required)                 │
│                   │                                                  │
│                   ├── YES ──▶ Route to PRIMARY                      │
│                   │                                                  │
│                   └── NO ──▶ Route to REPLICA (round-robin)         │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

## Replica Lag Handling

### Strategies

| Strategy | Description | Consistency | Complexity |
|----------|-------------|-------------|------------|
| Sticky master | After write, read from master for N seconds | Strong (within window) | Low |
| Causal consistency token | Pass replication position to reader | Strong | Medium |
| Read from master | Critical reads always go to master | Strong | Low |
| Lag-aware routing | Check replica lag, fallback to master | Near-real-time | High |
| Eventual reads | Accept stale data | Eventual | None |

### Sticky Master Implementation

```php
<?php

declare(strict_types=1);

namespace Database;

final class StickyMasterConnection
{
    private ?\DateTimeImmutable $lastWriteAt = null;

    public function __construct(
        private readonly ReadWriteConnection $connection,
        private readonly int $stickyDurationSeconds = 5,
    ) {}

    public function executeWrite(string $sql, array $params = []): void
    {
        $stmt = $this->connection->primary()->prepare($sql);
        $stmt->execute($params);
        $this->lastWriteAt = new \DateTimeImmutable();
    }

    public function executeRead(string $sql, array $params = []): array
    {
        $pdo = $this->shouldUsePrimary()
            ? $this->connection->primary()
            : $this->connection->replica();

        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);

        return $stmt->fetchAll();
    }

    private function shouldUsePrimary(): bool
    {
        if ($this->lastWriteAt === null) {
            return false;
        }

        $elapsed = (new \DateTimeImmutable())->getTimestamp() - $this->lastWriteAt->getTimestamp();

        return $elapsed < $this->stickyDurationSeconds;
    }
}
```

### Lag-Aware Routing

```php
<?php

declare(strict_types=1);

namespace Database;

final readonly class LagAwareRouter
{
    public function __construct(
        private ReadWriteConnection $connection,
        private float $maxAcceptableLagSeconds = 1.0,
    ) {}

    public function selectReplica(): \PDO
    {
        $lag = $this->measureReplicaLag();

        if ($lag > $this->maxAcceptableLagSeconds) {
            return $this->connection->primary();
        }

        return $this->connection->replica();
    }

    private function measureReplicaLag(): float
    {
        // PostgreSQL: check replication lag
        $stmt = $this->connection->replica()->query(
            "SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds"
        );

        $row = $stmt->fetch();

        return (float) ($row['lag_seconds'] ?? PHP_FLOAT_MAX);
    }
}
```

## Transaction-Aware Routing

All queries inside a transaction must go to the primary to maintain ACID guarantees.

```php
<?php

declare(strict_types=1);

namespace Database;

final class TransactionAwareConnection
{
    private bool $inTransaction = false;

    public function __construct(
        private readonly ReadWriteConnection $connection,
    ) {}

    public function beginTransaction(): void
    {
        $this->connection->primary()->beginTransaction();
        $this->inTransaction = true;
        $this->connection->usePrimary();
    }

    public function commit(): void
    {
        $this->connection->primary()->commit();
        $this->inTransaction = false;
        $this->connection->releasePrimary();
    }

    public function rollBack(): void
    {
        $this->connection->primary()->rollBack();
        $this->inTransaction = false;
        $this->connection->releasePrimary();
    }

    public function query(string $sql, array $params = []): array
    {
        $pdo = $this->resolveConnection($sql);
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);

        return $stmt->fetchAll();
    }

    private function resolveConnection(string $sql): \PDO
    {
        if ($this->inTransaction) {
            return $this->connection->primary();
        }

        if ($this->isWriteQuery($sql)) {
            return $this->connection->primary();
        }

        return $this->connection->replica();
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
            || str_starts_with($normalized, 'TRUNCATE');
    }
}
```

## Framework Integration Examples

### Doctrine DBAL PrimaryReadReplicaConnection

```php
<?php

declare(strict_types=1);

// config/packages/doctrine.yaml equivalent
// Doctrine DBAL natively supports primary-replica via PrimaryReadReplicaConnection

$connectionParams = [
    'wrapperClass' => \Doctrine\DBAL\Connections\PrimaryReadReplicaConnection::class,
    'driver' => 'pdo_pgsql',
    'primary' => [
        'host' => 'db-primary',
        'port' => 5432,
        'dbname' => 'myapp',
        'user' => 'app',
        'password' => 'secret',
    ],
    'replica' => [
        [
            'host' => 'db-replica1',
            'port' => 5432,
            'dbname' => 'myapp',
            'user' => 'app_readonly',
            'password' => 'secret',
        ],
        [
            'host' => 'db-replica2',
            'port' => 5432,
            'dbname' => 'myapp',
            'user' => 'app_readonly',
            'password' => 'secret',
        ],
    ],
];

// Usage: Doctrine automatically routes reads to replicas
// $connection->ensureConnectedToPrimary(); // force primary for critical reads
```

### Laravel Read/Write Configuration

```php
<?php

declare(strict_types=1);

// config/database.php — Laravel read/write split
return [
    'connections' => [
        'pgsql' => [
            'read' => [
                'host' => [
                    env('DB_READ_HOST_1', 'db-replica1'),
                    env('DB_READ_HOST_2', 'db-replica2'),
                ],
            ],
            'write' => [
                'host' => env('DB_WRITE_HOST', 'db-primary'),
            ],
            'driver' => 'pgsql',
            'port' => env('DB_PORT', '5432'),
            'database' => env('DB_DATABASE', 'myapp'),
            'username' => env('DB_USERNAME', 'app'),
            'password' => env('DB_PASSWORD', ''),
            'sticky' => true, // sticky master after writes
        ],
    ],
];
```

## Quick Reference Tables

### Routing Rules Summary

| Query Type | Transaction Active | After Recent Write | Route To |
|------------|-------------------|-------------------|----------|
| SELECT | No | No | Replica |
| SELECT | No | Yes (< N sec) | Primary (sticky) |
| SELECT | Yes | — | Primary |
| SELECT FOR UPDATE | — | — | Primary |
| INSERT/UPDATE/DELETE | — | — | Primary |
| DDL (CREATE/ALTER) | — | — | Primary |

### Replication Topology Comparison

| Topology | Write Scaling | Read Scaling | Failover | Complexity |
|----------|--------------|-------------|----------|------------|
| Single primary, N replicas | No (1 writer) | Yes (N readers) | Manual/auto | Low |
| Multi-primary | Yes (N writers) | Yes (N readers) | Automatic | High |
| Cascading replicas | No | Yes (tree) | Complex | Medium |
| Circular replication | Limited | Yes | Complex | High |

### Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| All reads to primary | No read scaling benefit | Route SELECTs to replicas |
| Ignoring replica lag | Stale data in critical reads | Sticky master or read from primary |
| No fallback on replica failure | Read failures | Health check + fallback to primary |
| `SELECT FOR UPDATE` on replica | Lock not acquired | Always route locking reads to primary |
| Large transactions hold master | Blocks replication | Keep transactions short |
| No connection timeout | Hung connections | Set `connect_timeout` and `statement_timeout` |

## Detection Patterns

```bash
# Read/write split configuration
Grep: "read.*write|write.*read|PrimaryReadReplica|MasterSlave" --glob "**/*.php"
Grep: "read.*host|write.*host|DB_READ_HOST|DB_WRITE_HOST" --glob "**/.env*"

# Doctrine primary-replica
Grep: "PrimaryReadReplicaConnection|MasterSlaveConnection" --glob "**/*.php"
Grep: "ensureConnectedToPrimary|ensureConnectedToReplica" --glob "**/*.php"

# Laravel read/write config
Grep: "'read'.*=>|'write'.*=>|'sticky'.*=>.*true" --glob "**/database.php"

# Manual routing patterns
Grep: "primary\(\)|replica\(\)|master\(\)|slave\(\)" --glob "**/*.php"
Grep: "isWriteQuery|isReadQuery|routeQuery" --glob "**/*.php"

# Replication lag monitoring
Grep: "pg_last_xact_replay_timestamp|Seconds_Behind_Master|replication_lag" --glob "**/*.php"

# Connection configuration
Grep: "PDO::ATTR_PERSISTENT|ATTR_PERSISTENT" --glob "**/*.php"
Grep: "pgbouncer|proxysql" --glob "**/docker-compose*.yml"
```

## References

For detailed information, load these reference files:

- `references/read-write-patterns.md` — Doctrine DBAL PrimaryReadReplicaConnection setup, custom connection wrapper, Laravel read_write config, transaction-aware routing, replica lag detection, health checks
