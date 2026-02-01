# Strategy Pattern Examples

## Pricing Strategies

### RegularPricingStrategy

**File:** `src/Domain/Pricing/Strategy/RegularPricingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Strategy;

use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;

final readonly class RegularPricingStrategy implements PricingStrategyInterface
{
    public function calculatePrice(PricingContext $context): Price
    {
        return $context->basePrice();
    }

    public function supports(PricingContext $context): bool
    {
        return !$context->hasDiscount() && !$context->isBulkOrder();
    }
}
```

---

### BulkPricingStrategy

**File:** `src/Domain/Pricing/Strategy/BulkPricingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Strategy;

use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;

final readonly class BulkPricingStrategy implements PricingStrategyInterface
{
    private const BULK_DISCOUNT_PERCENT = 15;
    private const BULK_THRESHOLD = 100;

    public function calculatePrice(PricingContext $context): Price
    {
        $discountMultiplier = 1 - (self::BULK_DISCOUNT_PERCENT / 100);

        return $context->basePrice()->multiply($discountMultiplier);
    }

    public function supports(PricingContext $context): bool
    {
        return $context->quantity() >= self::BULK_THRESHOLD;
    }
}
```

---

### PromotionalPricingStrategy

**File:** `src/Domain/Pricing/Strategy/PromotionalPricingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Strategy;

use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;

final readonly class PromotionalPricingStrategy implements PricingStrategyInterface
{
    public function calculatePrice(PricingContext $context): Price
    {
        $discount = $context->promotion()->discountAmount();

        return $context->basePrice()->subtract($discount);
    }

    public function supports(PricingContext $context): bool
    {
        return $context->hasActivePromotion();
    }
}
```

---

### PricingService

**File:** `src/Domain/Pricing/Strategy/PricingService.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Strategy;

use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;

final readonly class PricingService
{
    public function __construct(
        private PricingStrategyResolver $resolver
    ) {}

    public function calculatePrice(PricingContext $context): Price
    {
        $strategy = $this->resolver->resolve($context);

        return $strategy->calculatePrice($context);
    }
}
```

---

## Shipping Strategies

### StandardShippingStrategy

**File:** `src/Domain/Shipping/Strategy/StandardShippingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shipping\Strategy;

use Domain\Shipping\ValueObject\ShippingCost;
use Domain\Shipping\ValueObject\ShippingRequest;
use Domain\Shared\ValueObject\Money;

final readonly class StandardShippingStrategy implements ShippingCostStrategyInterface
{
    private const BASE_COST = 500;
    private const COST_PER_KG = 100;

    public function calculate(ShippingRequest $request): ShippingCost
    {
        $weightCost = $request->weight()->inKilograms() * self::COST_PER_KG;
        $totalCost = self::BASE_COST + $weightCost;

        return new ShippingCost(
            amount: Money::cents((int) $totalCost, $request->currency()),
            estimatedDays: $request->isInternational() ? 14 : 5
        );
    }

    public function supports(ShippingRequest $request): bool
    {
        return $request->isStandard();
    }

    public function getName(): string
    {
        return 'standard';
    }
}
```

---

### ExpressShippingStrategy

**File:** `src/Domain/Shipping/Strategy/ExpressShippingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shipping\Strategy;

use Domain\Shipping\ValueObject\ShippingCost;
use Domain\Shipping\ValueObject\ShippingRequest;
use Domain\Shared\ValueObject\Money;

final readonly class ExpressShippingStrategy implements ShippingCostStrategyInterface
{
    private const BASE_COST = 1500;
    private const COST_PER_KG = 300;

    public function calculate(ShippingRequest $request): ShippingCost
    {
        $weightCost = $request->weight()->inKilograms() * self::COST_PER_KG;
        $totalCost = self::BASE_COST + $weightCost;

        return new ShippingCost(
            amount: Money::cents((int) $totalCost, $request->currency()),
            estimatedDays: $request->isInternational() ? 3 : 1
        );
    }

    public function supports(ShippingRequest $request): bool
    {
        return $request->isExpress();
    }

    public function getName(): string
    {
        return 'express';
    }
}
```

---

### FreeShippingStrategy

**File:** `src/Domain/Shipping/Strategy/FreeShippingStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shipping\Strategy;

use Domain\Shipping\ValueObject\ShippingCost;
use Domain\Shipping\ValueObject\ShippingRequest;
use Domain\Shared\ValueObject\Money;

final readonly class FreeShippingStrategy implements ShippingCostStrategyInterface
{
    private const FREE_SHIPPING_THRESHOLD = 5000;

    public function calculate(ShippingRequest $request): ShippingCost
    {
        return new ShippingCost(
            amount: Money::zero($request->currency()),
            estimatedDays: 7
        );
    }

    public function supports(ShippingRequest $request): bool
    {
        return $request->orderTotal()->cents() >= self::FREE_SHIPPING_THRESHOLD;
    }

    public function getName(): string
    {
        return 'free';
    }
}
```

---

## Unit Tests

### BulkPricingStrategyTest

**File:** `tests/Unit/Domain/Pricing/Strategy/BulkPricingStrategyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Pricing\Strategy;

use Domain\Pricing\Strategy\BulkPricingStrategy;
use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(BulkPricingStrategy::class)]
final class BulkPricingStrategyTest extends TestCase
{
    private BulkPricingStrategy $strategy;

    protected function setUp(): void
    {
        $this->strategy = new BulkPricingStrategy();
    }

    public function testApplies15PercentDiscount(): void
    {
        $context = new PricingContext(
            basePrice: Price::fromCents(10000),
            quantity: 100
        );

        $result = $this->strategy->calculatePrice($context);

        self::assertSame(8500, $result->cents());
    }

    public function testSupportsBulkOrders(): void
    {
        $bulkContext = new PricingContext(
            basePrice: Price::fromCents(1000),
            quantity: 100
        );

        $smallContext = new PricingContext(
            basePrice: Price::fromCents(1000),
            quantity: 5
        );

        self::assertTrue($this->strategy->supports($bulkContext));
        self::assertFalse($this->strategy->supports($smallContext));
    }
}
```

---

### PricingStrategyResolverTest

**File:** `tests/Unit/Domain/Pricing/Strategy/PricingStrategyResolverTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Pricing\Strategy;

use Domain\Pricing\Strategy\BulkPricingStrategy;
use Domain\Pricing\Strategy\PricingStrategyResolver;
use Domain\Pricing\Strategy\RegularPricingStrategy;
use Domain\Pricing\ValueObject\PricingContext;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(PricingStrategyResolver::class)]
final class PricingStrategyResolverTest extends TestCase
{
    public function testResolvesMatchingStrategy(): void
    {
        $bulkStrategy = new BulkPricingStrategy();
        $regularStrategy = new RegularPricingStrategy();

        $resolver = new PricingStrategyResolver(
            strategies: [$bulkStrategy, $regularStrategy],
            defaultStrategy: $regularStrategy
        );

        $bulkContext = new PricingContext(
            basePrice: Price::fromCents(1000),
            quantity: 150
        );

        $resolved = $resolver->resolve($bulkContext);

        self::assertInstanceOf(BulkPricingStrategy::class, $resolved);
    }

    public function testFallsBackToDefault(): void
    {
        $bulkStrategy = new BulkPricingStrategy();
        $regularStrategy = new RegularPricingStrategy();

        $resolver = new PricingStrategyResolver(
            strategies: [$bulkStrategy],
            defaultStrategy: $regularStrategy
        );

        $smallContext = new PricingContext(
            basePrice: Price::fromCents(1000),
            quantity: 5
        );

        $resolved = $resolver->resolve($smallContext);

        self::assertInstanceOf(RegularPricingStrategy::class, $resolved);
    }
}
```
