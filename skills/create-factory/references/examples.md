# Factory Pattern Examples

## Order Factory

**File:** `src/Domain/Order/Factory/OrderFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Factory;

use Domain\Order\Entity\Order;
use Domain\Order\Entity\OrderItem;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\ValueObject\Address;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Exception\EmptyOrderException;
use Domain\Order\Exception\InvalidOrderTotalException;
use Domain\Cart\Entity\Cart;

final class OrderFactory
{
    /**
     * @param array<OrderItem> $items
     * @throws EmptyOrderException
     * @throws InvalidOrderTotalException
     */
    public static function create(
        CustomerId $customerId,
        array $items,
        Address $shippingAddress,
        Address $billingAddress
    ): Order {
        self::validateItems($items);

        $orderId = OrderId::generate();

        return new Order(
            id: $orderId,
            customerId: $customerId,
            items: $items,
            shippingAddress: $shippingAddress,
            billingAddress: $billingAddress,
            status: OrderStatus::Pending,
            createdAt: new \DateTimeImmutable()
        );
    }

    public static function createFromCart(
        Cart $cart,
        Address $shippingAddress,
        Address $billingAddress
    ): Order {
        $items = array_map(
            fn(CartItem $item) => OrderItem::fromCartItem($item),
            $cart->items()
        );

        return self::create(
            customerId: $cart->customerId(),
            items: $items,
            shippingAddress: $shippingAddress,
            billingAddress: $billingAddress
        );
    }

    public static function reconstitute(
        OrderId $id,
        CustomerId $customerId,
        array $items,
        Address $shippingAddress,
        Address $billingAddress,
        OrderStatus $status,
        \DateTimeImmutable $createdAt,
        ?\DateTimeImmutable $updatedAt,
        ?Money $totalOverride = null
    ): Order {
        return new Order(
            id: $id,
            customerId: $customerId,
            items: $items,
            shippingAddress: $shippingAddress,
            billingAddress: $billingAddress,
            status: $status,
            createdAt: $createdAt,
            updatedAt: $updatedAt,
            totalOverride: $totalOverride
        );
    }

    /**
     * @param array<OrderItem> $items
     * @throws EmptyOrderException
     */
    private static function validateItems(array $items): void
    {
        if ($items === []) {
            throw new EmptyOrderException();
        }

        foreach ($items as $item) {
            if (!$item instanceof OrderItem) {
                throw new \InvalidArgumentException('Invalid order item');
            }
        }
    }
}
```

---

## User Factory with Multiple Creation Paths

**File:** `src/Domain/User/Factory/UserFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Factory;

use Domain\User\Entity\User;
use Domain\User\ValueObject\UserId;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\HashedPassword;
use Domain\User\ValueObject\Name;
use Domain\User\Enum\UserRole;
use Domain\User\Enum\UserStatus;
use Domain\User\Exception\InvalidEmailException;

final class UserFactory
{
    public static function register(
        Email $email,
        HashedPassword $password,
        Name $name
    ): User {
        return new User(
            id: UserId::generate(),
            email: $email,
            password: $password,
            name: $name,
            role: UserRole::Customer,
            status: UserStatus::PendingVerification,
            createdAt: new \DateTimeImmutable()
        );
    }

    public static function createAdmin(
        Email $email,
        HashedPassword $password,
        Name $name
    ): User {
        return new User(
            id: UserId::generate(),
            email: $email,
            password: $password,
            name: $name,
            role: UserRole::Admin,
            status: UserStatus::Active,
            createdAt: new \DateTimeImmutable()
        );
    }

    public static function createFromOAuth(
        string $provider,
        string $providerUserId,
        Email $email,
        Name $name
    ): User {
        return new User(
            id: UserId::generate(),
            email: $email,
            password: null,
            name: $name,
            role: UserRole::Customer,
            status: UserStatus::Active,
            oauthProvider: $provider,
            oauthProviderId: $providerUserId,
            createdAt: new \DateTimeImmutable()
        );
    }

    public static function reconstitute(
        UserId $id,
        Email $email,
        ?HashedPassword $password,
        Name $name,
        UserRole $role,
        UserStatus $status,
        ?string $oauthProvider,
        ?string $oauthProviderId,
        \DateTimeImmutable $createdAt,
        ?\DateTimeImmutable $updatedAt
    ): User {
        return new User(
            id: $id,
            email: $email,
            password: $password,
            name: $name,
            role: $role,
            status: $status,
            oauthProvider: $oauthProvider,
            oauthProviderId: $oauthProviderId,
            createdAt: $createdAt,
            updatedAt: $updatedAt
        );
    }
}
```

---

## Policy Factory (Instance Factory with Dependencies)

**File:** `src/Domain/Insurance/Factory/PolicyFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Insurance\Factory;

use Domain\Insurance\Entity\Policy;
use Domain\Insurance\Entity\Coverage;
use Domain\Insurance\ValueObject\PolicyId;
use Domain\Insurance\ValueObject\CustomerId;
use Domain\Insurance\ValueObject\Premium;
use Domain\Insurance\Service\PremiumCalculatorService;
use Domain\Insurance\Service\RiskAssessmentService;
use Domain\Insurance\Exception\UnacceptableRiskException;

final readonly class PolicyFactory
{
    public function __construct(
        private PremiumCalculatorService $premiumCalculator,
        private RiskAssessmentService $riskAssessment
    ) {}

    /**
     * @param array<Coverage> $coverages
     * @throws UnacceptableRiskException
     */
    public function create(
        CustomerId $customerId,
        array $coverages,
        \DateTimeImmutable $startDate,
        \DateTimeImmutable $endDate
    ): Policy {
        $riskScore = $this->riskAssessment->assess($customerId, $coverages);

        if ($riskScore->isUnacceptable()) {
            throw new UnacceptableRiskException($customerId, $riskScore);
        }

        $premium = $this->premiumCalculator->calculate(
            $coverages,
            $riskScore,
            $startDate,
            $endDate
        );

        return new Policy(
            id: PolicyId::generate(),
            customerId: $customerId,
            coverages: $coverages,
            premium: $premium,
            riskScore: $riskScore,
            startDate: $startDate,
            endDate: $endDate,
            createdAt: new \DateTimeImmutable()
        );
    }
}
```

---

## Unit Tests

### OrderFactoryTest

**File:** `tests/Unit/Domain/Order/Factory/OrderFactoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Factory;

use Domain\Order\Factory\OrderFactory;
use Domain\Order\Entity\Order;
use Domain\Order\Entity\OrderItem;
use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\ValueObject\Address;
use Domain\Order\ValueObject\ProductId;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Exception\EmptyOrderException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderFactory::class)]
final class OrderFactoryTest extends TestCase
{
    public function testCreatesOrderWithValidData(): void
    {
        $customerId = CustomerId::generate();
        $items = [$this->createOrderItem()];
        $shippingAddress = $this->createAddress();
        $billingAddress = $this->createAddress();

        $order = OrderFactory::create(
            $customerId,
            $items,
            $shippingAddress,
            $billingAddress
        );

        self::assertInstanceOf(Order::class, $order);
        self::assertTrue($order->customerId()->equals($customerId));
        self::assertSame(OrderStatus::Pending, $order->status());
        self::assertCount(1, $order->items());
    }

    public function testThrowsOnEmptyItems(): void
    {
        $this->expectException(EmptyOrderException::class);

        OrderFactory::create(
            CustomerId::generate(),
            [],
            $this->createAddress(),
            $this->createAddress()
        );
    }

    public function testCreateFromCartMapsItems(): void
    {
        $cart = $this->createCartWithItems(3);

        $order = OrderFactory::createFromCart(
            $cart,
            $this->createAddress(),
            $this->createAddress()
        );

        self::assertCount(3, $order->items());
    }

    public function testReconstitutePreservesAllFields(): void
    {
        $id = OrderId::generate();
        $customerId = CustomerId::generate();
        $items = [$this->createOrderItem()];
        $shippingAddress = $this->createAddress();
        $billingAddress = $this->createAddress();
        $status = OrderStatus::Confirmed;
        $createdAt = new \DateTimeImmutable('2024-01-01');
        $updatedAt = new \DateTimeImmutable('2024-01-02');

        $order = OrderFactory::reconstitute(
            $id,
            $customerId,
            $items,
            $shippingAddress,
            $billingAddress,
            $status,
            $createdAt,
            $updatedAt
        );

        self::assertTrue($order->id()->equals($id));
        self::assertSame($status, $order->status());
        self::assertEquals($createdAt, $order->createdAt());
        self::assertEquals($updatedAt, $order->updatedAt());
    }

    private function createOrderItem(): OrderItem
    {
        return new OrderItem(
            productId: ProductId::generate(),
            name: 'Test Product',
            price: Money::USD(1000),
            quantity: 1
        );
    }

    private function createAddress(): Address
    {
        return new Address(
            street: '123 Main St',
            city: 'Test City',
            postalCode: '12345',
            country: 'US'
        );
    }

    private function createCartWithItems(int $count): Cart
    {
        $items = [];
        for ($i = 0; $i < $count; $i++) {
            $items[] = new CartItem(
                productId: ProductId::generate(),
                name: "Product $i",
                price: Money::USD(1000),
                quantity: 1
            );
        }

        return new Cart(
            id: CartId::generate(),
            customerId: CustomerId::generate(),
            items: $items
        );
    }
}
```

### UserFactoryTest

**File:** `tests/Unit/Domain/User/Factory/UserFactoryTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\User\Factory;

use Domain\User\Factory\UserFactory;
use Domain\User\Entity\User;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\HashedPassword;
use Domain\User\ValueObject\Name;
use Domain\User\Enum\UserRole;
use Domain\User\Enum\UserStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(UserFactory::class)]
final class UserFactoryTest extends TestCase
{
    public function testRegisterCreatesCustomerWithPendingStatus(): void
    {
        $user = UserFactory::register(
            new Email('test@example.com'),
            HashedPassword::fromPlain('password123'),
            new Name('John', 'Doe')
        );

        self::assertInstanceOf(User::class, $user);
        self::assertSame(UserRole::Customer, $user->role());
        self::assertSame(UserStatus::PendingVerification, $user->status());
    }

    public function testCreateAdminCreatesActiveAdmin(): void
    {
        $user = UserFactory::createAdmin(
            new Email('admin@example.com'),
            HashedPassword::fromPlain('securepass'),
            new Name('Admin', 'User')
        );

        self::assertSame(UserRole::Admin, $user->role());
        self::assertSame(UserStatus::Active, $user->status());
    }

    public function testCreateFromOAuthCreatesActiveUserWithoutPassword(): void
    {
        $user = UserFactory::createFromOAuth(
            'google',
            'google-user-123',
            new Email('oauth@example.com'),
            new Name('OAuth', 'User')
        );

        self::assertSame(UserStatus::Active, $user->status());
        self::assertNull($user->password());
        self::assertSame('google', $user->oauthProvider());
    }
}
```
