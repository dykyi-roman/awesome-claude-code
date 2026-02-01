# Repository Pattern Examples

## Order Repository Interface

**File:** `src/Domain/Order/Repository/OrderRepositoryInterface.php`

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
    public function findById(OrderId $id): ?Order;

    /**
     * @return array<Order>
     */
    public function findByCustomerId(CustomerId $customerId): array;

    /**
     * @return array<Order>
     */
    public function findByStatus(OrderStatus $status): array;

    public function save(Order $order): void;

    public function remove(Order $order): void;

    public function nextIdentity(): OrderId;
}
```

---

## Doctrine Order Repository

**File:** `src/Infrastructure/Persistence/Doctrine/DoctrineOrderRepository.php`

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

---

## User Repository Interface

**File:** `src/Domain/User/Repository/UserRepositoryInterface.php`

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

---

## Doctrine User Repository

**File:** `src/Infrastructure/Persistence/Doctrine/DoctrineUserRepository.php`

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

---

## In-Memory Order Repository (for Testing)

**File:** `tests/Infrastructure/Persistence/InMemoryOrderRepository.php`

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

---

## Integration Tests

### DoctrineOrderRepositoryTest

**File:** `tests/Integration/Infrastructure/Persistence/DoctrineOrderRepositoryTest.php`

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

    public function testFindsByCustomerId(): void
    {
        $customerId = new CustomerId('customer-456');

        $order1 = Order::create(OrderId::generate(), $customerId);
        $order2 = Order::create(OrderId::generate(), $customerId);
        $order3 = Order::create(OrderId::generate(), new CustomerId('other'));

        $this->repository->save($order1);
        $this->repository->save($order2);
        $this->repository->save($order3);

        $found = $this->repository->findByCustomerId($customerId);

        self::assertCount(2, $found);
    }

    protected function tearDown(): void
    {
        $this->em->clear();
    }
}
```
