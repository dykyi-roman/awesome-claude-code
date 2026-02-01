# Null Object Pattern Examples

## NullCustomer

**File:** `src/Domain/Customer/CustomerInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Customer;

use Domain\Customer\ValueObject\CustomerId;
use Domain\Customer\ValueObject\Email;
use Domain\Customer\ValueObject\Name;
use Domain\Shared\ValueObject\Money;

interface CustomerInterface
{
    public function id(): CustomerId;

    public function name(): Name;

    public function email(): Email;

    public function isVip(): bool;

    public function getDiscount(): float;

    public function getCreditLimit(): Money;

    public function isNull(): bool;
}
```

**File:** `src/Domain/Customer/NullCustomer.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Customer;

use Domain\Customer\ValueObject\CustomerId;
use Domain\Customer\ValueObject\Email;
use Domain\Customer\ValueObject\Name;
use Domain\Shared\ValueObject\Money;

final readonly class NullCustomer implements CustomerInterface
{
    public function id(): CustomerId
    {
        return CustomerId::empty();
    }

    public function name(): Name
    {
        return Name::anonymous();
    }

    public function email(): Email
    {
        return Email::empty();
    }

    public function isVip(): bool
    {
        return false;
    }

    public function getDiscount(): float
    {
        return 0.0;
    }

    public function getCreditLimit(): Money
    {
        return Money::zero('USD');
    }

    public function isNull(): bool
    {
        return true;
    }
}
```

**File:** `src/Domain/Customer/Customer.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Customer;

use Domain\Customer\ValueObject\CustomerId;
use Domain\Customer\ValueObject\Email;
use Domain\Customer\ValueObject\Name;
use Domain\Shared\ValueObject\Money;

final readonly class Customer implements CustomerInterface
{
    public function __construct(
        private CustomerId $id,
        private Name $name,
        private Email $email,
        private bool $vip = false,
        private float $discount = 0.0,
        private Money $creditLimit = new Money(0, 'USD')
    ) {}

    public function id(): CustomerId
    {
        return $this->id;
    }

    public function name(): Name
    {
        return $this->name;
    }

    public function email(): Email
    {
        return $this->email;
    }

    public function isVip(): bool
    {
        return $this->vip;
    }

    public function getDiscount(): float
    {
        return $this->discount;
    }

    public function getCreditLimit(): Money
    {
        return $this->creditLimit;
    }

    public function isNull(): bool
    {
        return false;
    }
}
```

---

## NullNotifier

**File:** `src/Domain/Notification/NotifierInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

interface NotifierInterface
{
    public function send(Notification $notification): NotificationResult;

    public function sendBulk(array $notifications): array;

    public function isNull(): bool;
}
```

**File:** `src/Domain/Notification/NullNotifier.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Notification;

final readonly class NullNotifier implements NotifierInterface
{
    public function send(Notification $notification): NotificationResult
    {
        return NotificationResult::skipped($notification->id());
    }

    /**
     * @param array<Notification> $notifications
     * @return array<NotificationResult>
     */
    public function sendBulk(array $notifications): array
    {
        return array_map(
            fn(Notification $n) => NotificationResult::skipped($n->id()),
            $notifications
        );
    }

    public function isNull(): bool
    {
        return true;
    }
}
```

---

## Repository Returning Null Object

**File:** `src/Domain/Customer/CustomerRepositoryInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Customer;

use Domain\Customer\ValueObject\CustomerId;

interface CustomerRepositoryInterface
{
    public function findById(CustomerId $id): CustomerInterface;

    public function findByEmail(string $email): CustomerInterface;
}
```

**File:** `src/Infrastructure/Customer/DoctrineCustomerRepository.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Customer;

use Domain\Customer\Customer;
use Domain\Customer\CustomerInterface;
use Domain\Customer\CustomerRepositoryInterface;
use Domain\Customer\NullCustomer;
use Domain\Customer\ValueObject\CustomerId;
use Doctrine\DBAL\Connection;

final readonly class DoctrineCustomerRepository implements CustomerRepositoryInterface
{
    public function __construct(
        private Connection $connection
    ) {}

    public function findById(CustomerId $id): CustomerInterface
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM customers WHERE id = :id',
            ['id' => $id->toString()]
        );

        if ($row === false) {
            return new NullCustomer();
        }

        return $this->hydrate($row);
    }

    public function findByEmail(string $email): CustomerInterface
    {
        $row = $this->connection->fetchAssociative(
            'SELECT * FROM customers WHERE email = :email',
            ['email' => $email]
        );

        if ($row === false) {
            return new NullCustomer();
        }

        return $this->hydrate($row);
    }

    private function hydrate(array $row): Customer
    {
        return new Customer(
            id: CustomerId::fromString($row['id']),
            name: Name::fromString($row['name']),
            email: Email::fromString($row['email']),
            vip: (bool) $row['is_vip'],
            discount: (float) $row['discount']
        );
    }
}
```

---

## Client Code Without Null Checks

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private CustomerRepositoryInterface $customers,
        private OrderRepositoryInterface $orders
    ) {}

    public function execute(CreateOrderCommand $command): Order
    {
        $customer = $this->customers->findById($command->customerId);

        $discount = $customer->getDiscount();

        $order = Order::create(
            customerId: $customer->id(),
            items: $command->items,
            discount: $discount
        );

        $this->orders->save($order);

        return $order;
    }
}
```

---

## Unit Tests

### NullCustomerTest

**File:** `tests/Unit/Domain/Customer/NullCustomerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Customer;

use Domain\Customer\NullCustomer;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(NullCustomer::class)]
final class NullCustomerTest extends TestCase
{
    private NullCustomer $customer;

    protected function setUp(): void
    {
        $this->customer = new NullCustomer();
    }

    public function testIsNullReturnsTrue(): void
    {
        self::assertTrue($this->customer->isNull());
    }

    public function testReturnsEmptyId(): void
    {
        self::assertTrue($this->customer->id()->isEmpty());
    }

    public function testReturnsAnonymousName(): void
    {
        self::assertSame('Anonymous', $this->customer->name()->toString());
    }

    public function testIsNotVip(): void
    {
        self::assertFalse($this->customer->isVip());
    }

    public function testReturnsZeroDiscount(): void
    {
        self::assertSame(0.0, $this->customer->getDiscount());
    }

    public function testReturnsZeroCreditLimit(): void
    {
        self::assertTrue($this->customer->getCreditLimit()->isZero());
    }
}
```

---

### NullCacheTest

**File:** `tests/Unit/Infrastructure/Cache/NullCacheTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Cache;

use Infrastructure\Cache\NullCache;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(NullCache::class)]
final class NullCacheTest extends TestCase
{
    private NullCache $cache;

    protected function setUp(): void
    {
        $this->cache = new NullCache();
    }

    public function testIsNullReturnsTrue(): void
    {
        self::assertTrue($this->cache->isNull());
    }

    public function testGetAlwaysReturnsNull(): void
    {
        $this->cache->set('key', 'value');

        self::assertNull($this->cache->get('key'));
    }

    public function testHasAlwaysReturnsFalse(): void
    {
        $this->cache->set('key', 'value');

        self::assertFalse($this->cache->has('key'));
    }

    public function testSetDoesNotThrow(): void
    {
        $this->cache->set('key', 'value', 3600);

        $this->expectNotToPerformAssertions();
    }

    public function testDeleteDoesNotThrow(): void
    {
        $this->cache->delete('key');

        $this->expectNotToPerformAssertions();
    }

    public function testClearDoesNotThrow(): void
    {
        $this->cache->clear();

        $this->expectNotToPerformAssertions();
    }
}
```

---

### Repository with NullObject Test

**File:** `tests/Unit/Infrastructure/Customer/DoctrineCustomerRepositoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Customer;

use Domain\Customer\NullCustomer;
use Infrastructure\Customer\DoctrineCustomerRepository;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(DoctrineCustomerRepository::class)]
final class DoctrineCustomerRepositoryTest extends TestCase
{
    public function testReturnsNullCustomerWhenNotFound(): void
    {
        $connection = $this->createMock(Connection::class);
        $connection->method('fetchAssociative')->willReturn(false);

        $repository = new DoctrineCustomerRepository($connection);

        $customer = $repository->findById(CustomerId::generate());

        self::assertInstanceOf(NullCustomer::class, $customer);
        self::assertTrue($customer->isNull());
    }

    public function testReturnsRealCustomerWhenFound(): void
    {
        $connection = $this->createMock(Connection::class);
        $connection->method('fetchAssociative')->willReturn([
            'id' => 'abc-123',
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'is_vip' => true,
            'discount' => 10.0,
        ]);

        $repository = new DoctrineCustomerRepository($connection);

        $customer = $repository->findById(CustomerId::fromString('abc-123'));

        self::assertFalse($customer->isNull());
        self::assertSame('John Doe', $customer->name()->toString());
    }
}
```
