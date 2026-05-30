# Persistence in Yii3

ActiveRecord (`yiisoft/active-record`), Cycle ORM alternative, Query Builder, Migrations, and Repository pattern implementation.

## ActiveRecord (yiisoft/active-record)

### ActiveRecord Model (Infrastructure Layer)

```php
<?php

declare(strict_types=1);

namespace Persistence\ActiveRecord;

use Yiisoft\ActiveRecord\ActiveRecord;

final class OrderActiveRecord extends ActiveRecord
{
    public function tableName(): string
    {
        return '{{%orders}}';
    }

    public function relationQuery(string $name): ActiveQueryInterface
    {
        return match ($name) {
            'lines' => $this->hasMany(OrderLineActiveRecord::class, ['order_id' => 'id']),
            'customer' => $this->hasOne(CustomerActiveRecord::class, ['id' => 'customer_id']),
            default => parent::relationQuery($name),
        };
    }
}
```

### ActiveQuery Usage

```php
<?php

declare(strict_types=1);

use Yiisoft\ActiveRecord\ActiveQuery;

// Basic queries
$orders = (new ActiveQuery(OrderActiveRecord::class))
    ->where(['status' => 'confirmed'])
    ->orderBy(['created_at' => SORT_DESC])
    ->limit(10)
    ->all();

// With eager loading (relations)
$orders = (new ActiveQuery(OrderActiveRecord::class))
    ->with('lines', 'customer')
    ->where(['customer_id' => $customerId])
    ->all();

// Single record
$order = (new ActiveQuery(OrderActiveRecord::class))
    ->where(['id' => $orderId])
    ->one();
```

## Cycle ORM as Alternative

### Entity Definition with Cycle

```php
<?php

declare(strict_types=1);

namespace Persistence\Cycle;

use Cycle\Annotated\Annotation\Entity;
use Cycle\Annotated\Annotation\Column;
use Cycle\Annotated\Annotation\Relation\HasMany;

#[Entity(table: 'orders')]
final class OrderCycleEntity
{
    #[Column(type: 'string(36)', primary: true)]
    public string $id;

    #[Column(type: 'string(36)')]
    public string $customerId;

    #[Column(type: 'string(20)')]
    public string $status;

    #[Column(type: 'integer')]
    public int $totalCents;

    #[HasMany(target: OrderLineCycleEntity::class)]
    public array $lines = [];
}
```

### Cycle Repository

```php
<?php

declare(strict_types=1);

namespace Persistence\Cycle;

use Cycle\ORM\Select\Repository;
use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;

final readonly class CycleOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private Repository $cycleRepository,
        private OrderEntityMapper $mapper,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $entity = $this->cycleRepository->findByPK($id->value);

        return $entity !== null ? $this->mapper->toDomain($entity) : null;
    }

    public function save(Order $order): void
    {
        $entity = $this->mapper->toCycle($order);
        $this->cycleRepository->persist($entity);
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

## Query Builder (yiisoft/db)

### Building Queries

```php
<?php

declare(strict_types=1);

namespace Query;

use Yiisoft\Db\Connection\ConnectionInterface;
use Yiisoft\Db\Query\Query;

final readonly class OrderQueryService
{
    public function __construct(
        private ConnectionInterface $db,
    ) {}

    public function findHighValueOrders(int $minCents): array
    {
        return (new Query($this->db))
            ->select(['o.id', 'o.status', 'o.total_cents', 'c.name as customer_name'])
            ->from('{{%orders}} o')
            ->leftJoin('{{%customers}} c', 'c.id = o.customer_id')
            ->where(['>', 'o.total_cents', $minCents])
            ->andWhere(['o.status' => 'confirmed'])
            ->orderBy(['o.created_at' => SORT_DESC])
            ->limit(50)
            ->all();
    }

    public function countByStatus(): array
    {
        return (new Query($this->db))
            ->select(['status', 'COUNT(*) as count'])
            ->from('{{%orders}}')
            ->groupBy(['status'])
            ->all();
    }
}
```

### Command Builder (INSERT/UPDATE/DELETE)

```php
<?php

declare(strict_types=1);

// Insert
$this->db->createCommand()->insert('{{%orders}}', [
    'id' => $order->id()->value,
    'customer_id' => $order->customerId()->value,
    'status' => $order->status()->value,
    'total_cents' => $order->total()->cents(),
    'created_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s'),
])->execute();

// Update
$this->db->createCommand()->update('{{%orders}}', [
    'status' => $newStatus->value,
    'updated_at' => (new \DateTimeImmutable())->format('Y-m-d H:i:s'),
], ['id' => $orderId->value])->execute();

// Batch insert
$this->db->createCommand()->batchInsert('{{%order_lines}}', [
    'id', 'order_id', 'product_id', 'quantity', 'price_cents',
], $rows)->execute();
```

## Migrations (yiisoft/db-migration)

### Migration Class

```php
<?php

declare(strict_types=1);

namespace Migration;

use Yiisoft\Db\Migration\MigrationBuilder;
use Yiisoft\Db\Migration\RevertibleMigrationInterface;

final class M20240101_CreateOrdersTable implements RevertibleMigrationInterface
{
    public function up(MigrationBuilder $b): void
    {
        $b->createTable('{{%orders}}', [
            'id' => $b->char(36)->notNull(),
            'customer_id' => $b->char(36)->notNull(),
            'status' => $b->string(20)->notNull()->defaultValue('draft'),
            'total_cents' => $b->integer()->notNull()->defaultValue(0),
            'created_at' => $b->timestamp()->notNull()->defaultExpression('CURRENT_TIMESTAMP'),
            'updated_at' => $b->timestamp()->null(),
            'PRIMARY KEY (id)',
        ]);

        $b->createIndex('{{%orders}}', 'idx-orders-customer_id', 'customer_id');
        $b->createIndex('{{%orders}}', 'idx-orders-status', 'status');

        $b->addForeignKey(
            '{{%orders}}',
            'fk-orders-customer_id',
            'customer_id',
            '{{%customers}}',
            'id',
            'CASCADE',
            'CASCADE',
        );
    }

    public function down(MigrationBuilder $b): void
    {
        $b->dropTable('{{%orders}}');
    }
}
```

### Running Migrations

```bash
# Apply all pending migrations
./yii migrate/up

# Revert last migration
./yii migrate/down 1

# Create new migration
./yii migrate/create CreateOrdersTable
```

## Repository Pattern Implementation

### Interface (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace Repository;

use Entity\Order;
use ValueObject\OrderId;
use ValueObject\CustomerId;
use ValueObject\OrderStatus;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    /** @return array<Order> */
    public function findByCustomerId(CustomerId $customerId): array;

    /** @return array<Order> */
    public function findByStatus(OrderStatus $status, int $limit = 50): array;

    public function save(Order $order): void;

    public function remove(Order $order): void;

    public function nextIdentity(): OrderId;
}
```

### Implementation (Infrastructure Layer)

```php
<?php

declare(strict_types=1);

namespace Persistence\ActiveRecord;

use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\OrderId;
use ValueObject\CustomerId;
use ValueObject\OrderStatus;
use Exception\OrderNotFoundException;
use Yiisoft\ActiveRecord\ActiveQuery;

final readonly class ActiveRecordOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private ActiveQuery $orderQuery,
        private OrderEntityMapper $mapper,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $record = $this->orderQuery->where(['id' => $id->value])->one();

        return $record !== null ? $this->mapper->toDomain($record) : null;
    }

    /** @return array<Order> */
    public function findByCustomerId(CustomerId $customerId): array
    {
        $records = $this->orderQuery
            ->where(['customer_id' => $customerId->value])
            ->orderBy(['created_at' => SORT_DESC])
            ->all();

        return array_map(fn ($r) => $this->mapper->toDomain($r), $records);
    }

    /** @return array<Order> */
    public function findByStatus(OrderStatus $status, int $limit = 50): array
    {
        $records = $this->orderQuery
            ->where(['status' => $status->value])
            ->limit($limit)
            ->all();

        return array_map(fn ($r) => $this->mapper->toDomain($r), $records);
    }

    public function save(Order $order): void
    {
        $record = $this->orderQuery
            ->where(['id' => $order->id()->value])
            ->one() ?? new OrderActiveRecord();

        $this->mapper->toRecord($order, $record);
        $record->save();
    }

    public function remove(Order $order): void
    {
        $record = $this->orderQuery->where(['id' => $order->id()->value])->one();

        if ($record === null) {
            throw new OrderNotFoundException($order->id());
        }

        $record->delete();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

## Detection Patterns

```bash
# ActiveRecord in wrong layer
Grep: "extends ActiveRecord" --glob "**/Domain/**/*.php"
Grep: "extends ActiveRecord" --glob "**/Application/**/*.php"

# Direct query builder in Application layer
Grep: "new Query\|createCommand" --glob "**/Application/**/*.php"

# Missing repository interface
Grep: "ActiveQuery" --glob "**/Application/**/*.php"
Grep: "ActiveQuery" --glob "**/Presentation/**/*.php"

# Raw SQL outside Infrastructure
Grep: "SELECT.*FROM\|INSERT INTO\|UPDATE.*SET" --glob "**/Application/**/*.php"

# Migration files location
Glob: **/Migration/M*.php
```

## Comparison Matrix

| Feature | ActiveRecord | Cycle ORM | Query Builder |
|---------|-------------|-----------|---------------|
| Simplicity | High | Medium | High |
| DDD fit | Low (needs wrapper) | High | N/A (read only) |
| Relations | Built-in | Built-in | Manual JOINs |
| Performance | Good | Good | Best |
| Learning curve | Low | Medium | Low |
| Best for | CRUD, read models | Domain entities | Reports, dashboards |
