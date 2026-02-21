# Persistence in No-Framework PHP

Standalone ORM setup, PDO repositories, database migrations, and query building without framework helpers.

## Detection Patterns

```bash
# Check for Doctrine ORM standalone usage
Grep: "doctrine/orm|doctrine/dbal" --glob "**/composer.json"

# Check for Cycle ORM usage
Grep: "cycle/orm|cycle/database" --glob "**/composer.json"

# Find raw PDO usage
Grep: "new PDO\(|PDO::" --glob "**/src/**/*.php"

# Detect SQL in Domain layer (violation)
Grep: "SELECT|INSERT|UPDATE|DELETE|PDO" --glob "**/Domain/**/*.php"

# Find Doctrine mapping files
Glob: **/Mapping/**/*.xml
Glob: **/Mapping/**/*.php

# Check for migration configuration
Grep: "doctrine/migrations" --glob "**/composer.json"
Grep: "migrations" --glob "**/config/**/*.php"

# Detect repository implementations
Grep: "implements.*RepositoryInterface" --glob "**/Infrastructure/**/*.php"
```

## Doctrine ORM Standalone Setup

**Bootstrap configuration (config/doctrine.php):**

```php
declare(strict_types=1);

use Doctrine\DBAL\DriverManager;
use Doctrine\ORM\EntityManager;
use Doctrine\ORM\ORMSetup;

return static function (): EntityManager {
    $paths = [dirname(__DIR__) . '/src/Infrastructure/Persistence/Doctrine/Mapping'];
    $isDevMode = $_ENV['APP_ENV'] === 'dev';

    $config = ORMSetup::createXMLMetadataConfiguration(
        paths: $paths,
        isDevMode: $isDevMode,
    );

    $connection = DriverManager::getConnection([
        'driver' => 'pdo_pgsql',
        'host' => $_ENV['DB_HOST'],
        'port' => (int) $_ENV['DB_PORT'],
        'dbname' => $_ENV['DB_NAME'],
        'user' => $_ENV['DB_USER'],
        'password' => $_ENV['DB_PASSWORD'],
    ]);

    return new EntityManager($connection, $config);
};
```

**XML mapping (keeps Domain pure — no annotations):**

```xml
<!-- src/Infrastructure/Persistence/Doctrine/Mapping/Domain.Order.Entity.Order.dcm.xml -->
<doctrine-mapping xmlns="http://doctrine-project.org/schemas/orm/doctrine-mapping">
    <entity name="Domain\Order\Entity\Order" table="orders">
        <id name="id" type="order_id" column="id"/>
        <field name="status" type="string" column="status" length="20"/>
        <one-to-many field="lines" target-entity="Domain\Order\ValueObject\OrderLine" mapped-by="order"/>
        <embedded name="customerId" class="Domain\Order\ValueObject\CustomerId"/>
    </entity>
</doctrine-mapping>
```

## Doctrine Repository Implementation

**Good — implements Domain interface, pure persistence:**

```php
declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine\Repository;

use Doctrine\ORM\EntityManagerInterface;
use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function delete(OrderId $id): void
    {
        $order = $this->findById($id);

        if ($order !== null) {
            $this->em->remove($order);
            $this->em->flush();
        }
    }

    /** @return array<Order> */
    public function findByCustomer(CustomerId $customerId): array
    {
        return $this->em->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.customerId = :customerId')
            ->setParameter('customerId', $customerId->value)
            ->getQuery()
            ->getResult();
    }
}
```

## Cycle ORM Alternative

**Cycle ORM bootstrap:**

```php
declare(strict_types=1);

use Cycle\Database\Config\DatabaseConfig;
use Cycle\Database\Config\PostgresDriverConfig;
use Cycle\Database\Config\Postgres\TcpConnectionConfig;
use Cycle\Database\DatabaseManager;
use Cycle\ORM\Factory;
use Cycle\ORM\ORM;
use Cycle\ORM\Schema;

$dbal = new DatabaseManager(new DatabaseConfig([
    'default' => 'default',
    'databases' => [
        'default' => ['connection' => 'postgres'],
    ],
    'connections' => [
        'postgres' => new PostgresDriverConfig(
            connection: new TcpConnectionConfig(
                database: $_ENV['DB_NAME'],
                host: $_ENV['DB_HOST'],
                port: (int) $_ENV['DB_PORT'],
                user: $_ENV['DB_USER'],
                password: $_ENV['DB_PASSWORD'],
            ),
        ),
    ],
]));

$orm = new ORM(
    factory: new Factory($dbal),
    schema: new Schema(require 'cycle-schema.php'),
);
```

## PDO + Repository Pattern

**For simpler projects without a full ORM:**

```php
declare(strict_types=1);

namespace Infrastructure\Persistence\Pdo\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\OrderStatus;

final readonly class PdoOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private \PDO $pdo,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $stmt = $this->pdo->prepare('SELECT * FROM orders WHERE id = :id');
        $stmt->execute(['id' => $id->value]);
        $row = $stmt->fetch(\PDO::FETCH_ASSOC);

        if ($row === false) {
            return null;
        }

        return $this->hydrate($row);
    }

    public function save(Order $order): void
    {
        $stmt = $this->pdo->prepare(
            'INSERT INTO orders (id, customer_id, status)
             VALUES (:id, :customer_id, :status)
             ON CONFLICT (id)
             DO UPDATE SET status = :status',
        );

        $stmt->execute([
            'id' => $order->id()->value,
            'customer_id' => $order->customerId()->value,
            'status' => $order->status()->value,
        ]);
    }

    private function hydrate(array $row): Order
    {
        return Order::reconstitute(
            id: new OrderId($row['id']),
            customerId: new CustomerId($row['customer_id']),
            status: OrderStatus::from($row['status']),
        );
    }
}
```

## Standalone Migrations

**doctrine/migrations CLI config (migrations.php):**

```php
declare(strict_types=1);

use Doctrine\Migrations\Configuration\EntityManager\ExistingEntityManager;
use Doctrine\Migrations\Configuration\Migration\PhpFile;
use Doctrine\Migrations\DependencyFactory;

$config = new PhpFile(dirname(__DIR__) . '/config/migrations-config.php');
$entityManager = (require dirname(__DIR__) . '/config/doctrine.php')();

return DependencyFactory::fromEntityManager($config, new ExistingEntityManager($entityManager));
```

**Migration config (config/migrations-config.php):**

```php
declare(strict_types=1);

return [
    'table_storage' => [
        'table_name' => 'migration_versions',
    ],
    'migrations_paths' => [
        'Migrations' => dirname(__DIR__) . '/migrations',
    ],
    'all_or_nothing' => true,
    'check_database_platform' => true,
];
```

**Running migrations:**

```bash
# Generate migration
vendor/bin/doctrine-migrations generate

# Run migrations
vendor/bin/doctrine-migrations migrate

# Check status
vendor/bin/doctrine-migrations status
```

## DBAL for Query Building

```php
declare(strict_types=1);

namespace Infrastructure\Persistence\ReadModel;

use Doctrine\DBAL\Connection;

final readonly class OrderReadRepository
{
    public function __construct(
        private Connection $connection,
    ) {}

    /** @return array<array{id: string, customer_name: string, total: int, status: string}> */
    public function findRecentOrders(int $limit = 20): array
    {
        return $this->connection->createQueryBuilder()
            ->select('o.id', 'c.name AS customer_name', 'o.total_cents AS total', 'o.status')
            ->from('orders', 'o')
            ->join('o', 'customers', 'c', 'o.customer_id = c.id')
            ->orderBy('o.created_at', 'DESC')
            ->setMaxResults($limit)
            ->executeQuery()
            ->fetchAllAssociative();
    }
}
```

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| SQL or PDO in Domain layer | Critical | Architecture purity |
| ORM annotations in Domain entities | Critical | Domain coupling |
| No migrations (manual schema changes) | Warning | Reproducibility |
| Raw PDO without prepared statements | Critical | SQL injection |
| Business logic in repository | Warning | Separation of concerns |
| Missing UPSERT / conflict handling | Info | Data integrity |
