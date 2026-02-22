---
name: create-read-write-proxy
description: Generates Read/Write Connection Proxy for PHP 8.4. Creates connection wrapper with query routing logic, transaction-aware routing, and replica health checks. Includes unit tests.
---

# Read/Write Connection Proxy Generator

Creates database connection proxy infrastructure for read/write splitting and replica routing.

## When to Use

| Scenario | Example |
|----------|---------|
| High read load | Route SELECT queries to replicas |
| Database scaling | Distribute reads across multiple replicas |
| Write protection | Ensure writes go to primary only |
| Transaction safety | Route all queries in transaction to primary |

## Component Characteristics

### ReadWriteConnectionInterface
- Connection contract abstracting primary/replica routing
- Query, execute, transaction methods
- Transparent to application code

### ReadWriteConnectionProxy
- Routes SELECT queries to replicas automatically
- Sends INSERT/UPDATE/DELETE to primary
- Transaction-aware: all queries in transaction go to primary
- Sticky connection after write within same request

### ConnectionConfig
- Configuration Value Object for primary and replica DSNs
- Supports multiple replica endpoints
- Immutable with validation

### ReplicaHealthChecker
- Monitors replica availability
- Removes unhealthy replicas from rotation
- Periodic health check with configurable interval

---

## Generation Process

### Step 1: Generate Core Components

**Path:** `src/Infrastructure/Database/`

1. `ReadWriteConnectionInterface.php` — Connection contract
2. `ConnectionConfig.php` — Configuration value object
3. `ConnectionRole.php` — Enum (Primary, Replica)

### Step 2: Generate Proxy

**Path:** `src/Infrastructure/Database/`

1. `ReadWriteConnectionProxy.php` — Query routing proxy

### Step 3: Generate Health Checker

**Path:** `src/Infrastructure/Database/`

1. `ReplicaHealthChecker.php` — Replica availability monitor

### Step 4: Generate Tests

1. `ConnectionConfigTest.php` — Configuration validation tests
2. `ReadWriteConnectionProxyTest.php` — Routing behavior tests

---

## File Placement

| Component | Path |
|-----------|------|
| All Classes | `src/Infrastructure/Database/` |
| Unit Tests | `tests/Unit/Infrastructure/Database/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `ReadWriteConnectionInterface` | `ReadWriteConnectionInterface` |
| Proxy | `ReadWriteConnectionProxy` | `ReadWriteConnectionProxy` |
| Config VO | `ConnectionConfig` | `ConnectionConfig` |
| Role Enum | `ConnectionRole` | `ConnectionRole::Primary` |
| Health Checker | `ReplicaHealthChecker` | `ReplicaHealthChecker` |
| Test | `{ClassName}Test` | `ReadWriteConnectionProxyTest` |

---

## Quick Template Reference

### ReadWriteConnectionInterface

```php
interface ReadWriteConnectionInterface
{
    /** @return list<array<string, mixed>> */
    public function query(string $sql, array $params = []): array;
    public function execute(string $sql, array $params = []): int;
    public function beginTransaction(): void;
    public function commit(): void;
    public function rollback(): void;
    public function inTransaction(): bool;
}
```

### ConnectionConfig

```php
final readonly class ConnectionConfig
{
    /** @param list<string> $replicaDsns */
    public function __construct(
        public string $primaryDsn,
        public array $replicaDsns = [],
        public bool $stickyAfterWrite = true
    ) {}
}
```

### ReadWriteConnectionProxy

```php
final class ReadWriteConnectionProxy implements ReadWriteConnectionInterface
{
    public function query(string $sql, array $params = []): array;
    public function execute(string $sql, array $params = []): int;
    public function beginTransaction(): void;
    public function commit(): void;
    public function rollback(): void;
}
```

---

## Usage Example

```php
$config = new ConnectionConfig(
    primaryDsn: 'mysql:host=primary.db;dbname=app',
    replicaDsns: [
        'mysql:host=replica1.db;dbname=app',
        'mysql:host=replica2.db;dbname=app',
    ],
    stickyAfterWrite: true
);

$connection = new ReadWriteConnectionProxy($config, $pdoFactory, $healthChecker);

// Routed to replica
$users = $connection->query('SELECT * FROM users WHERE active = ?', [1]);

// Routed to primary
$connection->execute('UPDATE users SET name = ? WHERE id = ?', ['John', 1]);

// After write, reads also go to primary (sticky)
$user = $connection->query('SELECT * FROM users WHERE id = ?', [1]);
```

---

## Routing Logic

```
query(SQL) ──→ Is SELECT?
                │          │
               YES         NO
                │          │
         In transaction? ──→ Primary
                │
         Sticky after write? ──→ Primary
                │
         Pick healthy replica ──→ Replica
                │
         No healthy replicas? ──→ Primary (fallback)
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Read-after-write to replica | Stale data returned | Use sticky connection |
| No health checks | Route to dead replica | Periodic health monitoring |
| Replica in transaction | Inconsistent reads | All transaction queries to primary |
| Single replica | No load distribution | Support multiple replicas |
| No fallback | Failure when all replicas down | Fall back to primary |
| SELECT FOR UPDATE to replica | Locking on read-only connection | Detect locking queries |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — ConnectionInterface, Proxy, Config, HealthChecker templates
- `references/examples.md` — Repository integration examples and tests
