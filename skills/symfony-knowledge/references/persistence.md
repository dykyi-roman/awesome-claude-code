# Persistence with Doctrine

Doctrine ORM mapping strategies, repository patterns, migrations, and keeping Doctrine out of the Domain layer.

## Entity Mapping Strategies

| Strategy | Pros | Cons | DDD Compatibility |
|----------|------|------|------------------|
| PHP Attributes | Auto-discovery, IDE support | Couples entity to Doctrine | Low |
| XML Mapping | Full separation from entity | Verbose, harder to navigate | High |
| PHP Config | Type-safe, IDE support | Less common, learning curve | High |

**Detection — mapping strategy in use:**
```bash
# Attribute-based mapping (common but DDD-unfriendly)
Grep: "#\\[ORM\\\\Entity|#\\[ORM\\\\Table|#\\[ORM\\\\Column" --glob "**/Entity/**/*.php"
Grep: "#\\[ORM\\\\Id|#\\[ORM\\\\GeneratedValue" --glob "**/Domain/**/*.php"

# XML mapping (DDD-friendly)
Glob: **/Doctrine/Mapping/*.orm.xml

# PHP config mapping
Glob: **/Doctrine/Mapping/*.php
```

### XML Mapping (Recommended for DDD)

```xml
<!-- src/Order/Infrastructure/Doctrine/Mapping/Order.orm.xml -->
<doctrine-mapping xmlns="http://doctrine-project.org/schemas/orm/doctrine-mapping">
    <entity name="App\Order\Domain\Entity\Order" table="orders">
        <id name="id" type="order_id" column="id"/>

        <field name="status" type="string" column="status" length="32"/>
        <field name="totalAmount" type="integer" column="total_amount"/>
        <field name="currency" type="string" column="currency" length="3"/>
        <field name="createdAt" type="datetime_immutable" column="created_at"/>
        <field name="updatedAt" type="datetime_immutable" column="updated_at" nullable="true"/>

        <many-to-one field="customer" target-entity="App\Customer\Domain\Entity\Customer">
            <join-column name="customer_id" referenced-column-name="id"/>
        </many-to-one>

        <one-to-many field="lines" target-entity="App\Order\Domain\Entity\OrderLine" mapped-by="order">
            <cascade>
                <cascade-persist/>
                <cascade-remove/>
            </cascade>
        </one-to-many>
    </entity>
</doctrine-mapping>
```

### Doctrine Configuration for XML Mapping

```yaml
# config/packages/doctrine.yaml
doctrine:
    dbal:
        url: '%env(resolve:DATABASE_URL)%'
        types:
            order_id: App\Shared\Infrastructure\Doctrine\Type\OrderIdType
            money: App\Shared\Infrastructure\Doctrine\Type\MoneyType
    orm:
        auto_generate_proxy_classes: true
        naming_strategy: doctrine.orm.naming_strategy.underscore_number_aware
        mappings:
            Order:
                type: xml
                dir: '%kernel.project_dir%/src/Order/Infrastructure/Doctrine/Mapping'
                prefix: 'App\Order\Domain\Entity'
                is_bundle: false
```

## Repository Pattern with Doctrine

### Domain Interface

```php
<?php

declare(strict_types=1);

namespace App\Order\Domain\Repository;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\ValueObject\OrderId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;

    public function save(Order $order): void;

    public function remove(Order $order): void;

    /** @return array<Order> */
    public function findByCustomer(CustomerId $customerId): array;
}
```

### Infrastructure Implementation

```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\Doctrine;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use App\Order\Domain\ValueObject\CustomerId;
use App\Order\Domain\ValueObject\OrderId;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $entityManager,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->entityManager->find(Order::class, $id);
    }

    public function save(Order $order): void
    {
        $this->entityManager->persist($order);
        $this->entityManager->flush();
    }

    public function remove(Order $order): void
    {
        $this->entityManager->remove($order);
        $this->entityManager->flush();
    }

    /** @return array<Order> */
    public function findByCustomer(CustomerId $customerId): array
    {
        return $this->entityManager
            ->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.customerId = :customerId')
            ->setParameter('customerId', $customerId->value)
            ->getQuery()
            ->getResult();
    }
}
```

**Detection — repository antipatterns:**
```bash
# Repository extends Doctrine ServiceEntityRepository (couples Domain to Doctrine)
Grep: "extends ServiceEntityRepository" --glob "**/Repository/**/*.php"
Grep: "extends EntityRepository" --glob "**/Domain/**/*.php"

# Repository with business logic
Grep: "private function (calculate|validate|check|process)" --glob "**/*Repository*.php"

# Missing repository interface
Grep: "class.*Repository" --glob "**/Infrastructure/**/*.php" | grep -v "implements"
```

## DQL and Query Builder

### Read Model with Query Builder

```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\Doctrine;

use App\Order\Application\DTO\OrderListDTO;
use App\Order\Domain\Repository\OrderReadRepositoryInterface;
use Doctrine\DBAL\Connection;

final readonly class DbalOrderReadRepository implements OrderReadRepositoryInterface
{
    public function __construct(
        private Connection $connection,
    ) {}

    /** @return array<OrderListDTO> */
    public function findRecentOrders(int $limit = 20): array
    {
        $result = $this->connection->createQueryBuilder()
            ->select('o.id', 'o.status', 'o.total_amount', 'o.created_at')
            ->from('orders', 'o')
            ->orderBy('o.created_at', 'DESC')
            ->setMaxResults($limit)
            ->executeQuery()
            ->fetchAllAssociative();

        return array_map(
            static fn(array $row): OrderListDTO => new OrderListDTO(
                id: $row['id'],
                status: $row['status'],
                totalAmount: (int) $row['total_amount'],
                createdAt: $row['created_at'],
            ),
            $result,
        );
    }
}
```

### CQRS Read Repository (DBAL for Performance)

| Approach | Use For | Performance | DDD |
|----------|---------|-------------|-----|
| EntityManager + DQL | Write model (commands) | Standard | Domain entities |
| DBAL QueryBuilder | Read model (queries) | Optimized | DTOs directly |
| Native SQL | Complex reporting | Best | Raw arrays/DTOs |

## Migrations Best Practices

```bash
# Generate migration from entity changes
php bin/console doctrine:migrations:diff

# Run migrations
php bin/console doctrine:migrations:migrate --no-interaction

# Check migration status
php bin/console doctrine:migrations:status
```

### Migration Structure

```php
<?php

declare(strict_types=1);

namespace DoctrineMigrations;

use Doctrine\DBAL\Schema\Schema;
use Doctrine\Migrations\AbstractMigration;

final class Version20260220120000 extends AbstractMigration
{
    public function getDescription(): string
    {
        return 'Create orders table with proper indexes';
    }

    public function up(Schema $schema): void
    {
        $this->addSql('CREATE TABLE orders (
            id UUID NOT NULL,
            customer_id UUID NOT NULL,
            status VARCHAR(32) NOT NULL,
            total_amount INT NOT NULL,
            currency VARCHAR(3) NOT NULL DEFAULT \'USD\',
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT NULL,
            PRIMARY KEY(id)
        )');

        $this->addSql('CREATE INDEX idx_orders_customer_id ON orders (customer_id)');
        $this->addSql('CREATE INDEX idx_orders_status ON orders (status)');
    }

    public function down(Schema $schema): void
    {
        $this->addSql('DROP TABLE orders');
    }
}
```

| Rule | Description |
|------|-------------|
| Always add `down()` | Reversible migrations for safety |
| Index early | Add indexes in the same migration as the table |
| No Doctrine ORM in migrations | Use raw SQL or DBAL Schema, not EntityManager |
| Descriptive names | `getDescription()` explains the change |
| Immutable after deploy | Never modify a deployed migration |

## Keeping Doctrine Out of Domain

| Concern | Wrong (Domain coupled) | Right (Domain pure) |
|---------|----------------------|---------------------|
| Entity mapping | `#[ORM\Entity]` on entity | XML/PHP mapping in Infrastructure |
| Collections | `Doctrine\Collections` | Native `array` with typed docblocks |
| ID generation | `#[ORM\GeneratedValue]` | Value Object with `Uuid::v7()` in factory |
| Timestamps | Doctrine lifecycle callbacks | Domain event or Application service |
| Soft delete | `#[Gedmo\SoftDeleteable]` | Domain `deactivate()` method + status field |
