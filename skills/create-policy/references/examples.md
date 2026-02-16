# Policy Pattern Examples

## Order Cancellation Policies

### OrderOwnershipPolicy

**File:** `src/Domain/Order/Policy/OrderOwnershipPolicy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Policy;

use Domain\Order\Entity\Order;
use Domain\Shared\Policy\PolicyResult;
use Domain\User\Entity\User;

final readonly class OrderOwnershipPolicy implements OrderCancellationPolicyInterface
{
    public function evaluate(User $user, Order $order): PolicyResult
    {
        if ($order->customerId()->equals($user->id())) {
            return PolicyResult::allow();
        }

        if ($user->isAdmin()) {
            return PolicyResult::allow();
        }

        return PolicyResult::deny(
            'User does not own this order',
            [
                'user_id' => $user->id()->toString(),
                'order_customer_id' => $order->customerId()->toString(),
            ]
        );
    }

    public function getRuleName(): string
    {
        return 'order_ownership';
    }
}
```

### OrderNotShippedPolicy

**File:** `src/Domain/Order/Policy/OrderNotShippedPolicy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Policy;

use Domain\Order\Entity\Order;
use Domain\Shared\Policy\PolicyResult;
use Domain\User\Entity\User;

final readonly class OrderNotShippedPolicy implements OrderCancellationPolicyInterface
{
    public function evaluate(User $user, Order $order): PolicyResult
    {
        if (!$order->isShipped()) {
            return PolicyResult::allow();
        }

        return PolicyResult::deny(
            'Cannot cancel shipped orders',
            [
                'order_id' => $order->id()->toString(),
                'order_status' => $order->getStateName(),
            ]
        );
    }

    public function getRuleName(): string
    {
        return 'order_not_shipped';
    }
}
```

### OrderCancellationTimePolicy

**File:** `src/Domain/Order/Policy/OrderCancellationTimePolicy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Policy;

use Domain\Order\Entity\Order;
use Domain\Shared\Policy\PolicyResult;
use Domain\User\Entity\User;
use Psr\Clock\ClockInterface;

final readonly class OrderCancellationTimePolicy implements OrderCancellationPolicyInterface
{
    private const MAX_CANCELLATION_HOURS = 24;

    public function __construct(
        private ClockInterface $clock
    ) {}

    public function evaluate(User $user, Order $order): PolicyResult
    {
        if ($user->isAdmin()) {
            return PolicyResult::allow();
        }

        $now = $this->clock->now();
        $orderTime = $order->createdAt();
        $hoursSinceOrder = ($now->getTimestamp() - $orderTime->getTimestamp()) / 3600;

        if ($hoursSinceOrder <= self::MAX_CANCELLATION_HOURS) {
            return PolicyResult::allow();
        }

        return PolicyResult::deny(
            sprintf('Order can only be cancelled within %d hours', self::MAX_CANCELLATION_HOURS),
            [
                'order_created_at' => $orderTime->format('c'),
                'hours_since_order' => round($hoursSinceOrder, 2),
            ]
        );
    }

    public function getRuleName(): string
    {
        return 'order_cancellation_time';
    }
}
```

### Composite OrderCancellationPolicy

**File:** `src/Domain/Order/Policy/OrderCancellationPolicy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Policy;

use Domain\Order\Entity\Order;
use Domain\Shared\Policy\PolicyResult;
use Domain\User\Entity\User;

final readonly class OrderCancellationPolicy implements OrderCancellationPolicyInterface
{
    public function __construct(
        private OrderOwnershipPolicy $ownershipPolicy,
        private OrderNotShippedPolicy $notShippedPolicy,
        private OrderCancellationTimePolicy $timePolicy
    ) {}

    public function evaluate(User $user, Order $order): PolicyResult
    {
        return $this->ownershipPolicy->evaluate($user, $order)
            ->and($this->notShippedPolicy->evaluate($user, $order))
            ->and($this->timePolicy->evaluate($user, $order));
    }

    public function getRuleName(): string
    {
        return 'order_cancellation';
    }
}
```

---

## Using Policies in UseCase

**File:** `src/Application/Order/UseCase/CancelOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Domain\Order\Policy\OrderCancellationPolicyInterface;
use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\User\Repository\UserRepositoryInterface;

final readonly class CancelOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private UserRepositoryInterface $users,
        private OrderCancellationPolicyInterface $cancellationPolicy
    ) {}

    public function execute(CancelOrderCommand $command): void
    {
        $user = $this->users->findById($command->userId);
        $order = $this->orders->findById($command->orderId);

        $result = $this->cancellationPolicy->evaluate($user, $order);

        if ($result->isDenied()) {
            throw new PolicyViolationException(
                $this->cancellationPolicy->getRuleName(),
                $result->getReason(),
                $result->metadata
            );
        }

        $order->cancel($command->reason);
        $this->orders->save($order);
    }
}
```

---

## Unit Tests

### OrderOwnershipPolicyTest

**File:** `tests/Unit/Domain/Order/Policy/OrderOwnershipPolicyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Policy;

use Domain\Order\Policy\OrderOwnershipPolicy;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderOwnershipPolicy::class)]
final class OrderOwnershipPolicyTest extends TestCase
{
    private OrderOwnershipPolicy $policy;

    protected function setUp(): void
    {
        $this->policy = new OrderOwnershipPolicy();
    }

    public function testAllowsOrderOwner(): void
    {
        $userId = UserId::generate();
        $user = $this->createUser($userId);
        $order = $this->createOrder(customerId: $userId);

        $result = $this->policy->evaluate($user, $order);

        self::assertTrue($result->isAllowed());
    }

    public function testAllowsAdmin(): void
    {
        $user = $this->createUser(isAdmin: true);
        $order = $this->createOrder(customerId: UserId::generate());

        $result = $this->policy->evaluate($user, $order);

        self::assertTrue($result->isAllowed());
    }

    public function testDeniesNonOwner(): void
    {
        $user = $this->createUser();
        $order = $this->createOrder(customerId: UserId::generate());

        $result = $this->policy->evaluate($user, $order);

        self::assertTrue($result->isDenied());
        self::assertStringContainsString('does not own', $result->getReason());
    }
}
```

### PolicyResultTest

**File:** `tests/Unit/Domain/Shared/Policy/PolicyResultTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Policy;

use Domain\Shared\Policy\PolicyResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(PolicyResult::class)]
final class PolicyResultTest extends TestCase
{
    public function testAllowCreatesAllowedResult(): void
    {
        $result = PolicyResult::allow();

        self::assertTrue($result->isAllowed());
        self::assertFalse($result->isDenied());
        self::assertNull($result->getReason());
    }

    public function testDenyCreatesDeniedResult(): void
    {
        $result = PolicyResult::deny('Not allowed', ['key' => 'value']);

        self::assertFalse($result->isAllowed());
        self::assertTrue($result->isDenied());
        self::assertSame('Not allowed', $result->getReason());
    }

    public function testAndReturnsDeniedIfFirstDenied(): void
    {
        $denied = PolicyResult::deny('First denied');
        $allowed = PolicyResult::allow();

        $result = $denied->and($allowed);

        self::assertTrue($result->isDenied());
        self::assertSame('First denied', $result->getReason());
    }

    public function testOrReturnsAllowedIfFirstAllowed(): void
    {
        $allowed = PolicyResult::allow();
        $denied = PolicyResult::deny('Denied');

        $result = $allowed->or($denied);

        self::assertTrue($result->isAllowed());
    }
}
```
