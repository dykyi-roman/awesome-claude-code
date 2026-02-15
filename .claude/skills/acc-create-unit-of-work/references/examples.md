# Unit of Work Examples

Real-world examples of Unit of Work pattern usage in PHP 8.4 projects.

---

## Example 1: Order + Payment Transaction

This example shows a UseCase that creates an Order and a Payment in a single transaction using Unit of Work.

### CreateOrderUseCase

**Path:** `src/Application/Order/UseCase/CreateOrder/CreateOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase\CreateOrder;

use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Order\Order;
use Domain\Order\OrderId;
use Domain\Order\CustomerId;
use Domain\Payment\Payment;
use Domain\Payment\PaymentId;
use Domain\Payment\Money;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private UnitOfWorkInterface $unitOfWork,
    ) {
    }

    public function execute(CreateOrderCommand $command): OrderId
    {
        $this->unitOfWork->begin();

        try {
            $order = Order::create(
                OrderId::generate(),
                CustomerId::fromString($command->customerId),
                $command->items,
            );

            $this->unitOfWork->registerNew($order);

            $payment = Payment::create(
                PaymentId::generate(),
                $order->id(),
                Money::fromAmount($order->totalAmount()),
            );

            $this->unitOfWork->registerNew($payment);

            $this->unitOfWork->flush();
            $this->unitOfWork->commit();

            return $order->id();
        } catch (\Throwable $e) {
            $this->unitOfWork->rollback();
            throw $e;
        }
    }
}
```

### CreateOrderCommand

**Path:** `src/Application/Order/UseCase/CreateOrder/CreateOrderCommand.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase\CreateOrder;

final readonly class CreateOrderCommand
{
    /**
     * @param array<array{product_id: string, quantity: int, price: float}> $items
     */
    public function __construct(
        public string $customerId,
        public array $items,
    ) {
    }
}
```

---

## Example 2: Repository Integration

This example shows how a repository uses Unit of Work for change tracking.

### OrderRepository

**Path:** `src/Infrastructure/Persistence/Doctrine/Repository/DoctrineOrderRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Persistence\Doctrine\Repository;

use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Order\Order;
use Domain\Order\OrderId;
use Domain\Order\OrderRepositoryInterface;
use Domain\Shared\UnitOfWork\EntityState;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $entityManager,
        private UnitOfWorkInterface $unitOfWork,
    ) {
    }

    public function save(Order $order): void
    {
        $state = $this->unitOfWork->getState($order);

        if ($state === null) {
            $this->unitOfWork->registerNew($order);
        } else {
            $this->unitOfWork->registerDirty($order);
        }
    }

    public function findById(OrderId $id): ?Order
    {
        $order = $this->entityManager->find(Order::class, $id->toString());

        if ($order instanceof Order && !$this->unitOfWork->isManaged($order)) {
            $this->unitOfWork->registerClean($order);
        }

        return $order;
    }

    public function delete(Order $order): void
    {
        $this->unitOfWork->registerDeleted($order);
    }
}
```

---

## Example 3: Domain Aggregate with Events

This example shows an Order aggregate that raises domain events.

### Order Aggregate

**Path:** `src/Domain/Order/Order.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order;

use Domain\Shared\Event\HasDomainEventsInterface;
use Domain\Shared\Event\RaisesDomainEventsTrait;

final class Order implements HasDomainEventsInterface
{
    use RaisesDomainEventsTrait;

    private OrderStatus $status;

    /**
     * @param array<OrderItem> $items
     */
    private function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private array $items,
    ) {
        $this->status = OrderStatus::Pending;
    }

    public static function create(
        OrderId $id,
        CustomerId $customerId,
        array $items,
    ): self {
        $order = new self($id, $customerId, $items);

        $order->raiseEvent(new OrderCreatedEvent(
            orderId: $id->toString(),
            customerId: $customerId->toString(),
            totalAmount: $order->totalAmount(),
            occurredAt: new \DateTimeImmutable(),
        ));

        return $order;
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Pending) {
            throw new \DomainException('Order cannot be confirmed');
        }

        $this->status = OrderStatus::Confirmed;

        $this->raiseEvent(new OrderConfirmedEvent(
            orderId: $this->id->toString(),
            confirmedAt: new \DateTimeImmutable(),
        ));
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function customerId(): CustomerId
    {
        return $this->customerId;
    }

    public function totalAmount(): float
    {
        return array_reduce(
            $this->items,
            fn (float $sum, OrderItem $item) => $sum + $item->total(),
            0.0
        );
    }
}
```

### OrderCreatedEvent

**Path:** `src/Domain/Order/Event/OrderCreatedEvent.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Event;

final readonly class OrderCreatedEvent
{
    public function __construct(
        public string $orderId,
        public string $customerId,
        public float $totalAmount,
        public \DateTimeImmutable $occurredAt,
    ) {
    }
}
```

---

## Example 4: DI Configuration (Symfony)

### services.yaml

```yaml
services:
  _defaults:
    autowire: true
    autoconfigure: true

  # Transaction Manager
  Domain\Shared\UnitOfWork\TransactionManagerInterface:
    class: Infrastructure\Persistence\UnitOfWork\DoctrineTransactionManager
    arguments:
      $connection: '@doctrine.dbal.default_connection'

  # Event Collector
  Domain\Shared\UnitOfWork\DomainEventCollectorInterface:
    class: Infrastructure\Persistence\UnitOfWork\DomainEventCollector
    arguments:
      $eventDispatcher: '@event_dispatcher'

  # Unit of Work
  Application\Shared\UnitOfWork\UnitOfWorkInterface:
    class: Infrastructure\Persistence\UnitOfWork\DoctrineUnitOfWork
    arguments:
      $entityManager: '@doctrine.orm.default_entity_manager'
      $transactionManager: '@Domain\Shared\UnitOfWork\TransactionManagerInterface'
      $eventCollector: '@Domain\Shared\UnitOfWork\DomainEventCollectorInterface'

  # Repositories
  Domain\Order\OrderRepositoryInterface:
    class: Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository
    arguments:
      $entityManager: '@doctrine.orm.default_entity_manager'
      $unitOfWork: '@Application\Shared\UnitOfWork\UnitOfWorkInterface'

  # Use Cases
  Application\Order\UseCase\CreateOrder\CreateOrderUseCase:
    arguments:
      $unitOfWork: '@Application\Shared\UnitOfWork\UnitOfWorkInterface'
```

---

## Example 5: Update Use Case with Dirty Tracking

### UpdateOrderUseCase

**Path:** `src/Application/Order/UseCase/UpdateOrder/UpdateOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase\UpdateOrder;

use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Order\OrderId;
use Domain\Order\OrderRepositoryInterface;

final readonly class UpdateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private UnitOfWorkInterface $unitOfWork,
    ) {
    }

    public function execute(UpdateOrderCommand $command): void
    {
        $this->unitOfWork->begin();

        try {
            $order = $this->orders->findById(OrderId::fromString($command->orderId));

            if ($order === null) {
                throw new \DomainException('Order not found');
            }

            if ($command->addItem !== null) {
                $order->addItem($command->addItem);
            }

            if ($command->removeItemId !== null) {
                $order->removeItem($command->removeItemId);
            }

            $this->unitOfWork->registerDirty($order);

            $this->unitOfWork->flush();
            $this->unitOfWork->commit();
        } catch (\Throwable $e) {
            $this->unitOfWork->rollback();
            throw $e;
        }
    }
}
```

---

## Example 6: Unit Tests for Use Case

### CreateOrderUseCaseTest

**Path:** `tests/Unit/Application/Order/UseCase/CreateOrder/CreateOrderUseCaseTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\Order\UseCase\CreateOrder;

use Application\Order\UseCase\CreateOrder\CreateOrderCommand;
use Application\Order\UseCase\CreateOrder\CreateOrderUseCase;
use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Order\Order;
use Domain\Payment\Payment;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderUseCase::class)]
final class CreateOrderUseCaseTest extends TestCase
{
    private UnitOfWorkInterface $unitOfWork;
    private CreateOrderUseCase $useCase;

    protected function setUp(): void
    {
        $this->unitOfWork = $this->createMock(UnitOfWorkInterface::class);
        $this->useCase = new CreateOrderUseCase($this->unitOfWork);
    }

    public function testExecuteCreatesOrderAndPayment(): void
    {
        $command = new CreateOrderCommand(
            customerId: 'customer-123',
            items: [
                ['product_id' => 'prod-1', 'quantity' => 2, 'price' => 10.0],
            ],
        );

        $this->unitOfWork->expects($this->once())->method('begin');
        $this->unitOfWork->expects($this->exactly(2))
            ->method('registerNew')
            ->with($this->logicalOr(
                $this->isInstanceOf(Order::class),
                $this->isInstanceOf(Payment::class)
            ));
        $this->unitOfWork->expects($this->once())->method('flush');
        $this->unitOfWork->expects($this->once())->method('commit');

        $orderId = $this->useCase->execute($command);

        self::assertNotNull($orderId);
    }

    public function testExecuteRollbacksOnFailure(): void
    {
        $command = new CreateOrderCommand(
            customerId: 'customer-123',
            items: [],
        );

        $this->unitOfWork->expects($this->once())->method('begin');
        $this->unitOfWork->expects($this->once())
            ->method('registerNew')
            ->willThrowException(new \RuntimeException('Database error'));
        $this->unitOfWork->expects($this->once())->method('rollback');
        $this->unitOfWork->expects($this->never())->method('commit');

        $this->expectException(\RuntimeException::class);

        $this->useCase->execute($command);
    }
}
```

---

## Example 7: Nested Transactions with Savepoints

### TransferMoneyUseCase

**Path:** `src/Application/Wallet/UseCase/TransferMoney/TransferMoneyUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Wallet\UseCase\TransferMoney;

use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Domain\Shared\UnitOfWork\TransactionManagerInterface;
use Domain\Wallet\WalletId;
use Domain\Wallet\WalletRepositoryInterface;
use Domain\Wallet\Money;

final readonly class TransferMoneyUseCase
{
    public function __construct(
        private WalletRepositoryInterface $wallets,
        private UnitOfWorkInterface $unitOfWork,
        private TransactionManagerInterface $transactionManager,
    ) {
    }

    public function execute(TransferMoneyCommand $command): void
    {
        $this->unitOfWork->begin();

        try {
            $fromWallet = $this->wallets->findById(WalletId::fromString($command->fromWalletId));
            $toWallet = $this->wallets->findById(WalletId::fromString($command->toWalletId));

            if ($fromWallet === null || $toWallet === null) {
                throw new \DomainException('Wallet not found');
            }

            $this->transactionManager->createSavepoint('before_debit');

            try {
                $fromWallet->debit(Money::fromAmount($command->amount));
                $this->unitOfWork->registerDirty($fromWallet);
                $this->unitOfWork->flush();
            } catch (\Throwable $e) {
                $this->transactionManager->rollbackToSavepoint('before_debit');
                throw $e;
            }

            $toWallet->credit(Money::fromAmount($command->amount));
            $this->unitOfWork->registerDirty($toWallet);

            $this->unitOfWork->flush();
            $this->unitOfWork->commit();
        } catch (\Throwable $e) {
            $this->unitOfWork->rollback();
            throw $e;
        }
    }
}
```

---

## Example 8: Integration Test with Doctrine

### CreateOrderIntegrationTest

**Path:** `tests/Integration/Application/Order/UseCase/CreateOrderIntegrationTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Integration\Application\Order\UseCase;

use Application\Order\UseCase\CreateOrder\CreateOrderCommand;
use Application\Order\UseCase\CreateOrder\CreateOrderUseCase;
use Application\Shared\UnitOfWork\UnitOfWorkInterface;
use Doctrine\ORM\EntityManagerInterface;
use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;

final class CreateOrderIntegrationTest extends KernelTestCase
{
    private EntityManagerInterface $entityManager;
    private UnitOfWorkInterface $unitOfWork;
    private CreateOrderUseCase $useCase;

    protected function setUp(): void
    {
        self::bootKernel();

        $this->entityManager = self::getContainer()->get(EntityManagerInterface::class);
        $this->unitOfWork = self::getContainer()->get(UnitOfWorkInterface::class);
        $this->useCase = self::getContainer()->get(CreateOrderUseCase::class);

        $this->entityManager->beginTransaction();
    }

    protected function tearDown(): void
    {
        $this->entityManager->rollback();
        $this->entityManager->close();
    }

    public function testCreateOrderPersistsOrderAndPayment(): void
    {
        $command = new CreateOrderCommand(
            customerId: 'customer-123',
            items: [
                ['product_id' => 'prod-1', 'quantity' => 2, 'price' => 10.0],
            ],
        );

        $orderId = $this->useCase->execute($command);

        $this->entityManager->clear();

        $order = $this->entityManager->find(\Domain\Order\Order::class, $orderId->toString());
        $payment = $this->entityManager->getRepository(\Domain\Payment\Payment::class)
            ->findOneBy(['orderId' => $orderId->toString()]);

        self::assertNotNull($order);
        self::assertNotNull($payment);
        self::assertSame(20.0, $order->totalAmount());
    }
}
```

---

## Key Takeaways

1. **UseCase controls transaction boundaries** — call `begin()`, `flush()`, `commit()`, `rollback()`
2. **Repository registers entity state** — `registerNew()`, `registerClean()`, `registerDirty()`, `registerDeleted()`
3. **flush() persists in order** — new → dirty → deleted, then collects domain events
4. **Events dispatched AFTER commit** — ensures transactional consistency
5. **Rollback clears tracker and events** — no partial state leaks
6. **Savepoints for nested operations** — fine-grained rollback control
7. **Identity Map prevents duplicates** — one instance per entity in memory
