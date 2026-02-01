# Read Model / Projection Templates

## Read Model (Domain Layer)

**File:** `src/Domain/{BoundedContext}/ReadModel/{Name}ReadModel.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\ReadModel;

final readonly class {Name}ReadModel
{
    public function __construct(
        public string $id,
        {properties}
        public \DateTimeImmutable $createdAt,
        public \DateTimeImmutable $updatedAt
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            id: $data['id'],
            {propertyMapping}
            createdAt: new \DateTimeImmutable($data['created_at']),
            updatedAt: new \DateTimeImmutable($data['updated_at'])
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            {arrayMapping}
            'created_at' => $this->createdAt->format('c'),
            'updated_at' => $this->updatedAt->format('c'),
        ];
    }
}
```

---

## Read Model Repository Interface

**File:** `src/Domain/{BoundedContext}/ReadModel/{Name}ReadModelRepositoryInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\ReadModel;

interface {Name}ReadModelRepositoryInterface
{
    public function findById(string $id): ?{Name}ReadModel;

    /** @return array<{Name}ReadModel> */
    public function findAll(int $limit = 100, int $offset = 0): array;

    /** @return array<{Name}ReadModel> */
    public function findBy{Criteria}({CriteriaType} $value): array;

    public function count(): int;
}
```

---

## Projection Interface

**File:** `src/Application/{BoundedContext}/Projection/{Name}ProjectionInterface.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

use Domain\Shared\Event\DomainEventInterface;

interface {Name}ProjectionInterface
{
    public function project(DomainEventInterface $event): void;

    public function reset(): void;

    /** @return array<class-string<DomainEventInterface>> */
    public function subscribedEvents(): array;
}
```

---

## Projection Implementation

**File:** `src/Application/{BoundedContext}/Projection/{Name}Projection.php`

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\Projection;

use Domain\{BoundedContext}\Event\{Events};
use Domain\{BoundedContext}\ReadModel\{Name}ReadModel;
use Domain\Shared\Event\DomainEventInterface;
use Psr\Log\LoggerInterface;

final class {Name}Projection implements {Name}ProjectionInterface
{
    public function __construct(
        private readonly {Name}ReadModelStore $store,
        private readonly LoggerInterface $logger
    ) {}

    public function project(DomainEventInterface $event): void
    {
        match ($event::class) {
            {EventClass1}::class => $this->when{EventName1}($event),
            {EventClass2}::class => $this->when{EventName2}($event),
            default => null,
        };
    }

    public function reset(): void
    {
        $this->store->truncate();
        $this->logger->info('Projection reset', ['projection' => '{Name}']);
    }

    public function subscribedEvents(): array
    {
        return [
            {EventClass1}::class,
            {EventClass2}::class,
        ];
    }

    private function when{EventName1}({EventClass1} $event): void
    {
        {projectionLogic1}
    }

    private function when{EventName2}({EventClass2} $event): void
    {
        {projectionLogic2}
    }
}
```

---

## Read Model Store

**File:** `src/Infrastructure/{BoundedContext}/Projection/{Name}Store.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\{BoundedContext}\Projection;

use Doctrine\DBAL\Connection;

final readonly class {Name}Store
{
    private const TABLE = '{table_name}';

    public function __construct(
        private Connection $connection
    ) {}

    public function insert(array $data): void
    {
        $this->connection->insert(self::TABLE, $data);
    }

    public function update(string $id, array $data): void
    {
        $this->connection->update(self::TABLE, $data, ['id' => $id]);
    }

    public function upsert(string $id, array $data): void
    {
        $existing = $this->connection->fetchOne(
            'SELECT id FROM ' . self::TABLE . ' WHERE id = :id',
            ['id' => $id]
        );

        if ($existing) {
            $this->update($id, $data);
        } else {
            $this->insert(array_merge(['id' => $id], $data));
        }
    }

    public function delete(string $id): void
    {
        $this->connection->delete(self::TABLE, ['id' => $id]);
    }

    public function truncate(): void
    {
        $this->connection->executeStatement('TRUNCATE TABLE ' . self::TABLE);
    }
}
```
