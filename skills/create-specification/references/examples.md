# Specification Pattern Examples

## Active Customer Specification

**File:** `src/Domain/Customer/Specification/IsActiveCustomerSpecification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Customer\Specification;

use Domain\Customer\Entity\Customer;
use Domain\Customer\Enum\CustomerStatus;
use Domain\Shared\Specification\AbstractSpecification;

/**
 * @extends AbstractSpecification<Customer>
 */
final readonly class IsActiveCustomerSpecification extends AbstractSpecification
{
    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Customer) {
            return false;
        }

        return $candidate->status() === CustomerStatus::Active
            && !$candidate->isDeleted()
            && $candidate->emailVerifiedAt() !== null;
    }
}
```

---

## Premium Product Specification

**File:** `src/Domain/Product/Specification/IsPremiumProductSpecification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Product\Specification;

use Domain\Product\Entity\Product;
use Domain\Product\ValueObject\Money;
use Domain\Shared\Specification\AbstractSpecification;

/**
 * @extends AbstractSpecification<Product>
 */
final readonly class IsPremiumProductSpecification extends AbstractSpecification
{
    public function __construct(
        private Money $priceThreshold
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Product) {
            return false;
        }

        return $candidate->price()->isGreaterThanOrEqual($this->priceThreshold)
            && $candidate->isPremiumBrand();
    }
}
```

---

## Overdue Invoice Specification

**File:** `src/Domain/Invoice/Specification/IsOverdueInvoiceSpecification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Invoice\Specification;

use Domain\Invoice\Entity\Invoice;
use Domain\Invoice\Enum\InvoiceStatus;
use Domain\Shared\Specification\AbstractSpecification;

/**
 * @extends AbstractSpecification<Invoice>
 */
final readonly class IsOverdueInvoiceSpecification extends AbstractSpecification
{
    public function __construct(
        private \DateTimeImmutable $asOf
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Invoice) {
            return false;
        }

        return $candidate->status() === InvoiceStatus::Unpaid
            && $candidate->dueDate() < $this->asOf;
    }

    public static function now(): self
    {
        return new self(new \DateTimeImmutable());
    }
}
```

---

## Eligible For Discount Specification

**File:** `src/Domain/Order/Specification/IsEligibleForDiscountSpecification.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Specification;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\Money;
use Domain\Customer\Entity\Customer;
use Domain\Customer\Enum\CustomerTier;
use Domain\Shared\Specification\AbstractSpecification;

/**
 * @extends AbstractSpecification<Order>
 */
final readonly class IsEligibleForDiscountSpecification extends AbstractSpecification
{
    public function __construct(
        private Customer $customer,
        private Money $minimumOrderValue
    ) {}

    public function isSatisfiedBy(mixed $candidate): bool
    {
        if (!$candidate instanceof Order) {
            return false;
        }

        $hasMinimumValue = $candidate->total()->isGreaterThanOrEqual($this->minimumOrderValue);
        $isPremiumCustomer = $this->customer->tier() === CustomerTier::Premium;
        $hasNoPreviousDiscount = !$candidate->hasAppliedDiscount();

        return $hasMinimumValue && ($isPremiumCustomer || $hasNoPreviousDiscount);
    }
}
```

---

## Composite Specification Usage

```php
<?php

// Create individual specifications
$isActive = new IsActiveCustomerSpecification();
$hasPurchaseHistory = new HasPurchaseHistorySpecification(minPurchases: 5);
$isNotBlacklisted = new IsBlacklistedSpecification()->not();

// Combine using AND/OR
$eligibleForPromotion = $isActive
    ->and($hasPurchaseHistory)
    ->and($isNotBlacklisted);

// Use for filtering
$eligibleCustomers = array_filter(
    $customers,
    fn(Customer $c) => $eligibleForPromotion->isSatisfiedBy($c)
);

// Use for validation
if (!$eligibleForPromotion->isSatisfiedBy($customer)) {
    throw new NotEligibleForPromotionException($customer->id());
}
```

---

## Unit Tests

### IsOverdueInvoiceSpecificationTest

**File:** `tests/Unit/Domain/Invoice/Specification/IsOverdueInvoiceSpecificationTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Invoice\Specification;

use Domain\Invoice\Specification\IsOverdueInvoiceSpecification;
use Domain\Invoice\Entity\Invoice;
use Domain\Invoice\Enum\InvoiceStatus;
use Domain\Invoice\ValueObject\InvoiceId;
use Domain\Customer\ValueObject\CustomerId;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(IsOverdueInvoiceSpecification::class)]
final class IsOverdueInvoiceSpecificationTest extends TestCase
{
    public function testUnpaidInvoicePastDueDateIsOverdue(): void
    {
        $specification = new IsOverdueInvoiceSpecification(
            new \DateTimeImmutable('2024-01-15')
        );

        $invoice = $this->createInvoice(
            status: InvoiceStatus::Unpaid,
            dueDate: new \DateTimeImmutable('2024-01-10')
        );

        self::assertTrue($specification->isSatisfiedBy($invoice));
    }

    public function testPaidInvoiceIsNotOverdue(): void
    {
        $specification = new IsOverdueInvoiceSpecification(
            new \DateTimeImmutable('2024-01-15')
        );

        $invoice = $this->createInvoice(
            status: InvoiceStatus::Paid,
            dueDate: new \DateTimeImmutable('2024-01-10')
        );

        self::assertFalse($specification->isSatisfiedBy($invoice));
    }

    public function testUnpaidInvoiceBeforeDueDateIsNotOverdue(): void
    {
        $specification = new IsOverdueInvoiceSpecification(
            new \DateTimeImmutable('2024-01-15')
        );

        $invoice = $this->createInvoice(
            status: InvoiceStatus::Unpaid,
            dueDate: new \DateTimeImmutable('2024-01-20')
        );

        self::assertFalse($specification->isSatisfiedBy($invoice));
    }

    public function testNowFactoryUsesCurrentDate(): void
    {
        $specification = IsOverdueInvoiceSpecification::now();

        $pastDueInvoice = $this->createInvoice(
            status: InvoiceStatus::Unpaid,
            dueDate: new \DateTimeImmutable('-1 day')
        );

        self::assertTrue($specification->isSatisfiedBy($pastDueInvoice));
    }

    public function testReturnsFalseForWrongType(): void
    {
        $specification = new IsOverdueInvoiceSpecification(
            new \DateTimeImmutable('2024-01-15')
        );

        self::assertFalse($specification->isSatisfiedBy(new \stdClass()));
    }

    private function createInvoice(
        InvoiceStatus $status,
        \DateTimeImmutable $dueDate
    ): Invoice {
        return new Invoice(
            id: InvoiceId::generate(),
            customerId: CustomerId::generate(),
            amount: Money::USD(1000),
            status: $status,
            dueDate: $dueDate,
            createdAt: new \DateTimeImmutable()
        );
    }
}
```

### CompositeSpecificationTest

**File:** `tests/Unit/Domain/Shared/Specification/CompositeSpecificationTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Specification;

use Domain\Shared\Specification\AndSpecification;
use Domain\Shared\Specification\OrSpecification;
use Domain\Shared\Specification\NotSpecification;
use Domain\Customer\Specification\IsActiveCustomerSpecification;
use Domain\Customer\Specification\HasPurchaseHistorySpecification;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(AndSpecification::class)]
#[CoversClass(OrSpecification::class)]
#[CoversClass(NotSpecification::class)]
final class CompositeSpecificationTest extends TestCase
{
    public function testAndSpecificationRequiresBothTrue(): void
    {
        $spec1 = new IsActiveCustomerSpecification();
        $spec2 = new HasPurchaseHistorySpecification(minPurchases: 1);

        $combined = $spec1->and($spec2);

        $activeWithPurchases = $this->createActiveCustomerWithPurchases(5);
        $activeNoPurchases = $this->createActiveCustomerWithPurchases(0);

        self::assertTrue($combined->isSatisfiedBy($activeWithPurchases));
        self::assertFalse($combined->isSatisfiedBy($activeNoPurchases));
    }

    public function testOrSpecificationRequiresEitherTrue(): void
    {
        $spec1 = new IsActiveCustomerSpecification();
        $spec2 = new HasPurchaseHistorySpecification(minPurchases: 10);

        $combined = $spec1->or($spec2);

        $activeNoPurchases = $this->createActiveCustomerWithPurchases(0);
        $inactiveWithPurchases = $this->createInactiveCustomerWithPurchases(15);

        self::assertTrue($combined->isSatisfiedBy($activeNoPurchases));
        self::assertTrue($combined->isSatisfiedBy($inactiveWithPurchases));
    }

    public function testNotSpecificationInvertsResult(): void
    {
        $spec = new IsActiveCustomerSpecification();
        $negated = $spec->not();

        $active = $this->createActiveCustomer();
        $inactive = $this->createInactiveCustomer();

        self::assertFalse($negated->isSatisfiedBy($active));
        self::assertTrue($negated->isSatisfiedBy($inactive));
    }

    public function testComplexComposition(): void
    {
        $isActive = new IsActiveCustomerSpecification();
        $hasPurchases = new HasPurchaseHistorySpecification(minPurchases: 5);
        $isNotBlacklisted = new IsBlacklistedSpecification()->not();

        $eligible = $isActive->and($hasPurchases)->and($isNotBlacklisted);

        $validCustomer = $this->createValidCustomer();
        self::assertTrue($eligible->isSatisfiedBy($validCustomer));
    }
}
```
