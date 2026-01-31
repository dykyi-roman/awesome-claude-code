---
name: acc-create-repository
description: Generates DDD Repository interfaces and implementation stubs for PHP 8.4. Creates domain interfaces in Domain layer, implementation in Infrastructure.
---

# Repository Generator

Generate DDD-compliant Repository interfaces and implementation stubs.

## Repository Characteristics

- **Interface in Domain**: Contract defined in Domain layer
- **Implementation in Infrastructure**: Doctrine/Eloquent/etc. implementation
- **Works with Aggregates**: Not entities directly
- **Collection-like**: Find, save, remove operations
- **No business logic**: Only persistence operations

## Interface Template (Domain Layer)

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Repository;

use Domain\{BoundedContext}\Entity\{AggregateRoot};
use Domain\{BoundedContext}\ValueObject\{AggregateRoot}Id;

interface {AggregateRoot}RepositoryInterface
{
    public function findById({AggregateRoot}Id $id): ?{AggregateRoot};

    public function save({AggregateRoot} ${aggregateRoot}): void;

    {additionalMethods}
}
```

## Implementation Template (Infrastructure Layer)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence;

use Domain\{BoundedContext}\Entity\{AggregateRoot};
use Domain\{BoundedContext}\Repository\{AggregateRoot}RepositoryInterface;
use Domain\{BoundedContext}\ValueObject\{AggregateRoot}Id;
use Doctrine\ORM\EntityManagerInterface;

final readonly class Doctrine{AggregateRoot}Repository implements {AggregateRoot}RepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById({AggregateRoot}Id $id): ?{AggregateRoot}
    {
        return $this->em->find({AggregateRoot}::class, $id->value);
    }

    public function save({AggregateRoot} ${aggregateRoot}): void
    {
        $this->em->persist(${aggregateRoot});
        $this->em->flush();
    }

    {additionalImplementations}
}
```

## Complete Repository Examples

### Order Repository

**Interface (Domain Layer):**

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Repository;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;

interface OrderRepositoryInterface
{
    /**
     * Find an order by its ID.
     */
    public function findById(OrderId $id): ?Order;

    /**
     * Find orders by customer.
     *
     * @return array<Order>
     */
    public function findByCustomerId(CustomerId $customerId): array;

    /**
     * Find orders by status.
     *
     * @return array<Order>
     */
    public function findByStatus(OrderStatus $status): array;

    /**
     * Save an order (create or update).
     */
    public function save(Order $order): void;

    /**
     * Remove an order.
     */
    public function remove(Order $order): void;

    /**
     * Generate next identity.
     */
    public function nextIdentity(): OrderId;
}
```

**Doctrine Implementation:**

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function findByCustomerId(CustomerId $customerId): array
    {
        return $this->em->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.customerId = :customerId')
            ->setParameter('customerId', $customerId->value)
            ->getQuery()
            ->getResult();
    }

    public function findByStatus(OrderStatus $status): array
    {
        return $this->em->createQueryBuilder()
            ->select('o')
            ->from(Order::class, 'o')
            ->where('o.status = :status')
            ->setParameter('status', $status->value)
            ->getQuery()
            ->getResult();
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function remove(Order $order): void
    {
        $this->em->remove($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }
}
```

### User Repository

**Interface:**

```php
<?php

declare(strict_types=1);

namespace Domain\User\Repository;

use Domain\User\Entity\User;
use Domain\User\ValueObject\UserId;
use Domain\User\ValueObject\Email;

interface UserRepositoryInterface
{
    public function findById(UserId $id): ?User;

    public function findByEmail(Email $email): ?User;

    public function existsByEmail(Email $email): bool;

    public function save(User $user): void;

    public function remove(User $user): void;

    public function nextIdentity(): UserId;
}
```

**Doctrine Implementation:**

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine;

use Domain\User\Entity\User;
use Domain\User\Repository\UserRepositoryInterface;
use Domain\User\ValueObject\UserId;
use Domain\User\ValueObject\Email;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineUserRepository implements UserRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function findById(UserId $id): ?User
    {
        return $this->em->find(User::class, $id->value);
    }

    public function findByEmail(Email $email): ?User
    {
        return $this->em->createQueryBuilder()
            ->select('u')
            ->from(User::class, 'u')
            ->where('u.email = :email')
            ->setParameter('email', $email->value)
            ->getQuery()
            ->getOneOrNullResult();
    }

    public function existsByEmail(Email $email): bool
    {
        $count = $this->em->createQueryBuilder()
            ->select('COUNT(u.id)')
            ->from(User::class, 'u')
            ->where('u.email = :email')
            ->setParameter('email', $email->value)
            ->getQuery()
            ->getSingleScalarResult();

        return $count > 0;
    }

    public function save(User $user): void
    {
        $this->em->persist($user);
        $this->em->flush();
    }

    public function remove(User $user): void
    {
        $this->em->remove($user);
        $this->em->flush();
    }

    public function nextIdentity(): UserId
    {
        return UserId::generate();
    }
}
```

## In-Memory Repository (for Testing)

```php
<?php

declare(strict_types=1);

namespace Tests\Infrastructure\Persistence;

use Domain\Order\Entity\Order;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\Enum\OrderStatus;

final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */
    private array $orders = [];

    public function findById(OrderId $id): ?Order
    {
        return $this->orders[$id->value] ?? null;
    }

    public function findByCustomerId(CustomerId $customerId): array
    {
        return array_filter(
            $this->orders,
            fn (Order $order) => $order->customerId()->equals($customerId)
        );
    }

    public function findByStatus(OrderStatus $status): array
    {
        return array_filter(
            $this->orders,
            fn (Order $order) => $order->status() === $status
        );
    }

    public function save(Order $order): void
    {
        $this->orders[$order->id()->value] = $order;
    }

    public function remove(Order $order): void
    {
        unset($this->orders[$order->id()->value]);
    }

    public function nextIdentity(): OrderId
    {
        return OrderId::generate();
    }

    public function clear(): void
    {
        $this->orders = [];
    }

    public function count(): int
    {
        return count($this->orders);
    }
}
```

## Repository Design Rules

### 1. Interface in Domain Layer

```
Domain/
└── Order/
    └── Repository/
        └── OrderRepositoryInterface.php   ← Interface here

Infrastructure/
└── Persistence/
    └── Doctrine/
        └── DoctrineOrderRepository.php    ← Implementation here
```

### 2. Works with Aggregates, Not Entities

```php
// GOOD: Repository for aggregate root
interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
}

// BAD: Repository for child entity
interface OrderLineRepositoryInterface  // OrderLine is not an aggregate root
{
    public function findById(OrderLineId $id): ?OrderLine;
}
```

### 3. No Query Methods with Business Logic

```php
// GOOD: Simple query methods
interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function findByStatus(OrderStatus $status): array;
}

// BAD: Business logic in repository
interface OrderRepositoryInterface
{
    public function findOrdersEligibleForDiscount(): array;  // Business logic!
    public function findOverdueOrders(): array;               // Business logic!
}
```

### 4. Use Specifications for Complex Queries

```php
// For complex queries, use Specification pattern
interface OrderRepositoryInterface
{
    /**
     * @return array<Order>
     */
    public function findBySpecification(Specification $specification): array;
}

// Usage
$overdueSpec = new OverdueOrderSpecification();
$orders = $repository->findBySpecification($overdueSpec);
```

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Infrastructure\Persistence;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Infrastructure\Persistence\Doctrine\DoctrineOrderRepository;
use Doctrine\ORM\EntityManagerInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;

#[Group('integration')]
#[CoversClass(DoctrineOrderRepository::class)]
final class DoctrineOrderRepositoryTest extends KernelTestCase
{
    private EntityManagerInterface $em;
    private DoctrineOrderRepository $repository;

    protected function setUp(): void
    {
        $kernel = self::bootKernel();
        $this->em = $kernel->getContainer()->get('doctrine.orm.entity_manager');
        $this->repository = new DoctrineOrderRepository($this->em);
    }

    public function testSavesAndFindsOrder(): void
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: new CustomerId('customer-123')
        );

        $this->repository->save($order);

        $found = $this->repository->findById($order->id());

        self::assertNotNull($found);
        self::assertTrue($order->id()->equals($found->id()));
    }

    public function testReturnsNullWhenNotFound(): void
    {
        $found = $this->repository->findById(OrderId::generate());

        self::assertNull($found);
    }

    protected function tearDown(): void
    {
        $this->em->clear();
    }
}
```

## Generation Instructions

When asked to create a Repository:

1. **Identify the aggregate root**
2. **Define query methods** needed
3. **Create interface in Domain layer**
4. **Create implementation in Infrastructure**
5. **Optionally create in-memory version** for tests

## Usage

To generate a Repository, provide:
- Aggregate root name (e.g., "Order", "User")
- Bounded Context (e.g., "Order", "User")
- Query methods needed (findBy*, exists*, etc.)
- ORM type (Doctrine, Eloquent, etc.)
