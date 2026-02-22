---
name: check-database-scaling
description: Analyzes PHP code for database scaling issues. Detects single DB connection for all queries, missing read replica configuration, SELECT queries hitting master, and missing connection pooling.
---

# Database Scaling Check

Analyze PHP code for database access patterns that prevent horizontal scaling, overload the primary database, and miss read replica offloading opportunities.

## Detection Patterns

### 1. Single DB Connection for All Queries

```php
<?php

declare(strict_types=1);

// BAD: All queries use the same connection
final readonly class DatabaseConnection
{
    private PDO $pdo;

    public function __construct()
    {
        $this->pdo = new PDO(
            'mysql:host=db-primary;dbname=app',
            'root',
            'password',
        );
        // All reads AND writes go through this single connection
    }

    public function query(string $sql): array
    {
        return $this->pdo->query($sql)->fetchAll();
    }
}

// GOOD: Separate read/write connections
final readonly class ReadWriteConnection
{
    public function __construct(
        private PDO $writeConnection,
        private PDO $readConnection,
    ) {}

    public static function fromConfig(DatabaseConfig $config): self
    {
        return new self(
            writeConnection: new PDO($config->writeDsn(), $config->user(), $config->password()),
            readConnection: new PDO($config->readDsn(), $config->user(), $config->password()),
        );
    }

    public function forWrite(): PDO
    {
        return $this->writeConnection;
    }

    public function forRead(): PDO
    {
        return $this->readConnection;
    }
}
```

### 2. Missing Read Replica Configuration

```php
<?php

declare(strict_types=1);

// BAD: Only one database host configured
// .env:
// DATABASE_URL=mysql://root:pass@primary-db:3306/app
// No DB_READ_HOST, no replica DSN

// BAD: Doctrine with single connection
// doctrine.yaml:
// doctrine:
//     dbal:
//         url: '%env(DATABASE_URL)%'

// GOOD: Doctrine with read replica(s)
// doctrine.yaml:
// doctrine:
//     dbal:
//         default_connection: default
//         connections:
//             default:
//                 wrapper_class: Doctrine\DBAL\Connections\PrimaryReadReplicaConnection
//                 primary:
//                     url: '%env(DATABASE_PRIMARY_URL)%'
//                 replica:
//                     replica1:
//                         url: '%env(DATABASE_REPLICA1_URL)%'
//                     replica2:
//                         url: '%env(DATABASE_REPLICA2_URL)%'

// GOOD: Environment with read replica
// .env:
// DATABASE_PRIMARY_URL=mysql://root:pass@primary-db:3306/app
// DATABASE_REPLICA1_URL=mysql://root:pass@replica1-db:3306/app
// DATABASE_REPLICA2_URL=mysql://root:pass@replica2-db:3306/app
```

### 3. SELECT Queries Hitting Primary

```php
<?php

declare(strict_types=1);

// BAD: Read queries go to primary database
final readonly class ProductRepository
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function findAll(): array
    {
        // Uses default (primary) connection for reads
        return $this->em->getRepository(Product::class)->findAll();
    }

    public function findById(ProductId $id): ?Product
    {
        // Every SELECT hits the primary -- wasting write capacity
        return $this->em->find(Product::class, $id->toString());
    }
}

// GOOD: Explicit read connection for queries
final readonly class ProductRepository
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function findAll(): array
    {
        $connection = $this->em->getConnection();
        if ($connection instanceof PrimaryReadReplicaConnection) {
            $connection->ensureConnectedToReplica();
        }

        return $this->em->getRepository(Product::class)->findAll();
    }
}

// GOOD: CQRS -- separate read model with read-only connection
final readonly class ProductReadRepository
{
    public function __construct(
        private Connection $readConnection, // Injected read-only connection
    ) {}

    public function findAll(): array
    {
        return $this->readConnection
            ->executeQuery('SELECT id, name, price FROM products WHERE active = 1')
            ->fetchAllAssociative();
    }
}
```

### 4. Missing Connection Pooling

```php
<?php

declare(strict_types=1);

// BAD: New connection per request without pooling
final readonly class LegacyDatabase
{
    public function query(string $sql): array
    {
        // Each PHP-FPM request opens a new connection
        $pdo = new PDO('mysql:host=db;dbname=app', 'root', 'pass');
        $result = $pdo->query($sql)->fetchAll();
        // Connection closed at end of request
        // Under 1000 RPS = 1000 connections to DB
        return $result;
    }
}

// GOOD: Persistent connections + external pooler (PgBouncer/ProxySQL)
// Connection through PgBouncer/ProxySQL
final readonly class PooledDatabase
{
    public function __construct(
        private PDO $pdo, // Injected once, persistent
    ) {}

    // With PDO persistent connections
    public static function createPersistent(string $dsn, string $user, string $pass): self
    {
        return new self(new PDO($dsn, $user, $pass, [
            PDO::ATTR_PERSISTENT => true,
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        ]));
    }
}

// docker-compose.yml or infrastructure:
// pgbouncer:
//     image: edoburu/pgbouncer
//     environment:
//         DATABASE_URL: postgres://user:pass@postgres:5432/app
//         POOL_MODE: transaction
//         MAX_CLIENT_CONN: 1000
//         DEFAULT_POOL_SIZE: 20
```

### 5. Heavy Queries on Primary

```php
<?php

declare(strict_types=1);

// BAD: Reporting/analytics queries on write database
final readonly class ReportService
{
    public function generateMonthlyReport(DateTimeImmutable $month): Report
    {
        // Heavy aggregation on primary -- blocks writes!
        $data = $this->em->createQuery(
            'SELECT SUM(o.total), COUNT(o) FROM Order o
             WHERE o.createdAt BETWEEN :start AND :end
             GROUP BY o.status'
        )
            ->setParameter('start', $month->modify('first day of this month'))
            ->setParameter('end', $month->modify('last day of this month'))
            ->getResult();

        return new Report($data);
    }
}

// GOOD: Heavy queries on dedicated read replica or analytics database
final readonly class ReportService
{
    public function __construct(
        private Connection $analyticsConnection, // Separate replica for analytics
    ) {}

    public function generateMonthlyReport(DateTimeImmutable $month): Report
    {
        $data = $this->analyticsConnection->executeQuery(
            'SELECT SUM(total) as revenue, COUNT(*) as order_count, status
             FROM orders
             WHERE created_at BETWEEN :start AND :end
             GROUP BY status',
            [
                'start' => $month->modify('first day of this month')->format('Y-m-d'),
                'end' => $month->modify('last day of this month')->format('Y-m-d 23:59:59'),
            ],
        )->fetchAllAssociative();

        return new Report($data);
    }
}
```

## Grep Patterns

```bash
# Single database connection
Grep: "new PDO\(|DriverManager::getConnection" --glob "**/*.php"

# Read replica configuration
Grep: "DB_READ_HOST|DATABASE_REPLICA|replica|PrimaryReadReplicaConnection" --glob "**/*.php"
Grep: "DB_READ_HOST|DATABASE_REPLICA|replica" --glob "**/.env*"

# Connection pooling indicators
Grep: "ATTR_PERSISTENT|pgbouncer|ProxySQL|pool_size" --glob "**/*.php"
Grep: "pgbouncer|proxysql" --glob "**/docker-compose*.yml"

# Heavy queries (GROUP BY, SUM, COUNT, subqueries)
Grep: "GROUP BY|SUM\(|COUNT\(|AVG\(|HAVING" --glob "**/*.php"

# Report/analytics queries
Grep: "class.*Report|generateReport|analytics" --glob "**/*.php"

# Doctrine read/write split
Grep: "ensureConnectedToReplica|ensureConnectedToPrimary" --glob "**/*.php"

# All database connections in config
Grep: "DATABASE_URL|DB_HOST|DB_CONNECTION" --glob "**/.env*"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| All queries on single primary connection | 🔴 Critical |
| Reporting/analytics on primary database | 🔴 Critical |
| No read replica configuration | 🟠 Major |
| No connection pooling under high load | 🟠 Major |
| SELECT queries not routed to replica | 🟠 Major |
| New PDO connection per query | 🟡 Minor |
| Missing persistent connections | 🟡 Minor |

## Output Format

```markdown
### Database Scaling Issue: [Brief Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Type:** [Single Connection|No Replica|SELECT on Primary|No Pooling|Heavy Query]

**Issue:**
[Description of the database scaling problem]

**Impact:**
- Primary database overloaded with reads
- Write latency increases under read load
- Cannot scale reads independently

**Code:**
```php
// Non-scalable database access
```

**Fix:**
```php
// With read/write split and pooling
```
```

## When This Is Acceptable

- **Low-traffic applications** -- Under 100 QPS, a single database connection is sufficient
- **Single-server deployment** -- When horizontal scaling is not a requirement
- **Development/staging** -- Non-production environments don't need read replicas
- **Write-heavy workloads** -- If 90%+ of operations are writes, read replicas add complexity without benefit

### False Positive Indicators
- Application is a CLI tool or batch processor (not serving HTTP traffic)
- Database is already behind a managed proxy (AWS RDS Proxy, Cloud SQL Proxy)
- Read/write split is configured at the ORM level but not visible in code
- PDO is created once in a service container and reused across requests
