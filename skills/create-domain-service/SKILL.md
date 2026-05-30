---
name: create-domain-service
description: Generates DDD Domain Services for PHP 8.4. Creates stateless services for business logic that doesn't belong to entities or value objects. Includes unit tests.
---

# Domain Service Generator

Generate DDD-compliant Domain Services for business operations spanning multiple aggregates or requiring external coordination.

## Domain Service Characteristics

- **Stateless**: No internal state, operates on passed arguments
- **Domain Logic**: Contains business rules that don't fit in entities
- **Cross-Aggregate**: Coordinates multiple aggregates
- **Named by Domain Operation**: Verb-based naming (e.g., TransferMoney, CalculateShipping)
- **No Infrastructure**: Pure domain logic, no DB/HTTP calls
- **Immutable Dependencies**: Uses repository interfaces, not implementations

## When to Use Domain Service

| Scenario | Example |
|----------|---------|
| Operation spans multiple aggregates | MoneyTransfer between accounts |
| Complex business calculation | PricingCalculator, TaxCalculator |
| Domain policy enforcement | PasswordPolicy, OrderPolicy |
| Stateless transformation | CurrencyConverter |
| Aggregate coordination | OrderFulfillmentService |

## Template

```php
<?php

declare(strict_types=1);

namespace Service;

use Entity\{Entity};
use ValueObject\{ValueObjects};
use Repository\{RepositoryInterfaces};
use Exception\{DomainExceptions};

final readonly class {Name}Service
{
    public function __construct(
        {repositoryDependencies}
    ) {}

    /**
     * @throws {DomainException}
     */
    public function {operation}({parameters}): {ReturnType}
    {
        {domainLogic}
    }

    {privateMethods}
}
```

## Examples

### Money Transfer Service

```php
<?php

declare(strict_types=1);

namespace Service;

use Entity\Account;
use ValueObject\Money;
use Repository\AccountRepositoryInterface;
use Exception\InsufficientFundsException;
use Exception\SameAccountTransferException;

final readonly class MoneyTransferService
{
    public function __construct(
        private AccountRepositoryInterface $accounts
    ) {}

    /**
     * @throws InsufficientFundsException
     * @throws SameAccountTransferException
     */
    public function transfer(
        Account $source,
        Account $destination,
        Money $amount
    ): void {
        if ($source->id()->equals($destination->id())) {
            throw new SameAccountTransferException();
        }

        if (!$source->canWithdraw($amount)) {
            throw new InsufficientFundsException($source->id(), $amount);
        }

        $source->withdraw($amount);
        $destination->deposit($amount);
    }
}
```

### Pricing Calculator Service

```php
<?php

declare(strict_types=1);

namespace Service;

use ValueObject\Money;
use ValueObject\Discount;
use ValueObject\TaxRate;
use Entity\Order;
use Entity\Customer;

final readonly class PricingCalculatorService
{
    public function calculateTotal(
        Order $order,
        Customer $customer,
        ?Discount $discount = null
    ): Money {
        $subtotal = $this->calculateSubtotal($order);
        $discounted = $this->applyDiscount($subtotal, $discount, $customer);
        $taxed = $this->applyTax($discounted, $order->shippingAddress());

        return $taxed;
    }

    private function calculateSubtotal(Order $order): Money
    {
        return $order->items()->reduce(
            fn(Money $total, OrderItem $item) => $total->add(
                $item->price()->multiply($item->quantity())
            ),
            Money::zero($order->currency())
        );
    }

    private function applyDiscount(
        Money $amount,
        ?Discount $discount,
        Customer $customer
    ): Money {
        if ($discount === null) {
            return $amount;
        }

        if (!$discount->isApplicableTo($customer)) {
            return $amount;
        }

        return $discount->apply($amount);
    }

    private function applyTax(Money $amount, Address $address): Money
    {
        $taxRate = TaxRate::forRegion($address->region());
        return $amount->add($amount->multiply($taxRate->value()));
    }
}
```

### Password Policy Service

```php
<?php

declare(strict_types=1);

namespace Service;

use ValueObject\Password;
use ValueObject\PasswordStrength;
use Exception\WeakPasswordException;

final readonly class PasswordPolicyService
{
    private const MIN_LENGTH = 8;
    private const REQUIRED_STRENGTH = PasswordStrength::Strong;

    public function validate(Password $password): void
    {
        $violations = [];

        if ($password->length() < self::MIN_LENGTH) {
            $violations[] = "Password must be at least " . self::MIN_LENGTH . " characters";
        }

        if (!$password->hasUppercase()) {
            $violations[] = "Password must contain uppercase letters";
        }

        if (!$password->hasLowercase()) {
            $violations[] = "Password must contain lowercase letters";
        }

        if (!$password->hasDigit()) {
            $violations[] = "Password must contain digits";
        }

        if (!$password->hasSpecialChar()) {
            $violations[] = "Password must contain special characters";
        }

        if ($password->strength()->isWeakerThan(self::REQUIRED_STRENGTH)) {
            $violations[] = "Password strength must be at least " . self::REQUIRED_STRENGTH->value;
        }

        if ($violations !== []) {
            throw new WeakPasswordException($violations);
        }
    }

    public function calculateStrength(Password $password): PasswordStrength
    {
        $score = 0;

        if ($password->length() >= 12) $score += 2;
        elseif ($password->length() >= 8) $score += 1;

        if ($password->hasUppercase()) $score += 1;
        if ($password->hasLowercase()) $score += 1;
        if ($password->hasDigit()) $score += 1;
        if ($password->hasSpecialChar()) $score += 2;

        return match (true) {
            $score >= 6 => PasswordStrength::Strong,
            $score >= 4 => PasswordStrength::Medium,
            default => PasswordStrength::Weak,
        };
    }
}
```

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\{BoundedContext}\Service;

use Service\{Name}Service;
use Entity\{Entity};
use ValueObject\{ValueObject};
use Exception\{DomainException};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Service::class)]
final class {Name}ServiceTest extends TestCase
{
    private {Name}Service $service;

    protected function setUp(): void
    {
        $this->service = new {Name}Service(
            {mockDependencies}
        );
    }

    public function test{Operation}Successfully(): void
    {
        {arrange}

        $result = $this->service->{operation}({parameters});

        {assert}
    }

    public function test{Operation}ThrowsOn{Condition}(): void
    {
        {arrange}

        $this->expectException({DomainException}::class);

        $this->service->{operation}({invalidParameters});
    }

    {additionalTests}
}
```

### Example Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Banking\Service;

use Service\MoneyTransferService;
use Entity\Account;
use ValueObject\AccountId;
use ValueObject\Money;
use Exception\InsufficientFundsException;
use Exception\SameAccountTransferException;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(MoneyTransferService::class)]
final class MoneyTransferServiceTest extends TestCase
{
    private MoneyTransferService $service;

    protected function setUp(): void
    {
        $this->service = new MoneyTransferService(
            $this->createMock(AccountRepositoryInterface::class)
        );
    }

    public function testTransfersMoneyBetweenAccounts(): void
    {
        $source = $this->createAccountWithBalance(Money::USD(1000));
        $destination = $this->createAccountWithBalance(Money::USD(500));
        $amount = Money::USD(300);

        $this->service->transfer($source, $destination, $amount);

        self::assertTrue($source->balance()->equals(Money::USD(700)));
        self::assertTrue($destination->balance()->equals(Money::USD(800)));
    }

    public function testThrowsOnInsufficientFunds(): void
    {
        $source = $this->createAccountWithBalance(Money::USD(100));
        $destination = $this->createAccountWithBalance(Money::USD(500));
        $amount = Money::USD(300);

        $this->expectException(InsufficientFundsException::class);

        $this->service->transfer($source, $destination, $amount);
    }

    public function testThrowsOnSameAccountTransfer(): void
    {
        $account = $this->createAccountWithBalance(Money::USD(1000));

        $this->expectException(SameAccountTransferException::class);

        $this->service->transfer($account, $account, Money::USD(100));
    }

    private function createAccountWithBalance(Money $balance): Account
    {
        $account = new Account(AccountId::generate());
        $account->deposit($balance);
        return $account;
    }
}
```

## Naming Conventions

| Pattern | Example |
|---------|---------|
| Service | `{Operation}Service` | `MoneyTransferService`, `PricingCalculatorService` |
| Method | `{verb}{noun}` | `transfer()`, `calculate()`, `validate()` |
| Exception | `{Condition}Exception` | `InsufficientFundsException` |
| Test | `{ServiceName}Test` | `MoneyTransferServiceTest` |

## File Placement

| Component | Path |
|-----------|------|
| Domain Service | `src/{architecture-path}/Service/{ServiceName}.php` |
| Exceptions | `src/{architecture-path}/Exception/{Condition}Exception.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Service/` |

> `{architecture-path}` represents your project's architecture-specific folders. Domain Services live alongside the domain code of the bounded context they belong to; their exceptions live in a sibling `Exception/` folder. Adjust to your project's layout.

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Anemic Service | Just delegates to entities | Move logic to entities |
| Infrastructure leaking in | DB/HTTP calls inside the service | Depend on repository abstractions; keep the service pure |
| Stateful Service | Maintains internal state | Make stateless |
| God Service | Too many responsibilities | Split into focused services |
| Business Logic in Constructors | Complex setup | Keep constructors simple |
