# Strategy Pattern Templates

## Strategy Interface

**File:** `src/Domain/{BoundedContext}/Strategy/{Name}StrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Strategy;

interface {Name}StrategyInterface
{
    public function execute({InputType} $input): {OutputType};

    public function supports({InputType} $input): bool;
}
```

---

## Abstract Strategy (Optional)

**File:** `src/Domain/{BoundedContext}/Strategy/Abstract{Name}Strategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Strategy;

abstract readonly class Abstract{Name}Strategy implements {Name}StrategyInterface
{
    public function supports({InputType} $input): bool
    {
        return true;
    }

    protected function validate({InputType} $input): void
    {
        // Override in subclass if needed
    }
}
```

---

## Concrete Strategy

**File:** `src/Domain/{BoundedContext}/Strategy/{Variant}{Name}Strategy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Strategy;

final readonly class {Variant}{Name}Strategy implements {Name}StrategyInterface
{
    public function execute({InputType} $input): {OutputType}
    {
        {algorithmImplementation}
    }

    public function supports({InputType} $input): bool
    {
        return {condition};
    }
}
```

---

## Strategy Context

**File:** `src/Domain/{BoundedContext}/Strategy/{Name}Context.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Strategy;

final class {Name}Context
{
    public function __construct(
        private {Name}StrategyInterface $strategy
    ) {}

    public function setStrategy({Name}StrategyInterface $strategy): void
    {
        $this->strategy = $strategy;
    }

    public function execute({InputType} $input): {OutputType}
    {
        return $this->strategy->execute($input);
    }
}
```

---

## Strategy Resolver

**File:** `src/Domain/{BoundedContext}/Strategy/{Name}StrategyResolver.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Strategy;

final readonly class {Name}StrategyResolver
{
    /**
     * @param iterable<{Name}StrategyInterface> $strategies
     */
    public function __construct(
        private iterable $strategies,
        private {Name}StrategyInterface $defaultStrategy
    ) {}

    public function resolve({InputType} $input): {Name}StrategyInterface
    {
        foreach ($this->strategies as $strategy) {
            if ($strategy->supports($input)) {
                return $strategy;
            }
        }

        return $this->defaultStrategy;
    }
}
```

---

## Pricing Strategy Interface

**File:** `src/Domain/Pricing/Strategy/PricingStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Pricing\Strategy;

use Domain\Pricing\ValueObject\Price;
use Domain\Pricing\ValueObject\PricingContext;

interface PricingStrategyInterface
{
    public function calculatePrice(PricingContext $context): Price;

    public function supports(PricingContext $context): bool;
}
```

---

## Shipping Strategy Interface

**File:** `src/Domain/Shipping/Strategy/ShippingCostStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shipping\Strategy;

use Domain\Shipping\ValueObject\ShippingCost;
use Domain\Shipping\ValueObject\ShippingRequest;

interface ShippingCostStrategyInterface
{
    public function calculate(ShippingRequest $request): ShippingCost;

    public function supports(ShippingRequest $request): bool;

    public function getName(): string;
}
```

---

## Tax Strategy Interface

**File:** `src/Domain/Tax/Strategy/TaxStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Tax\Strategy;

use Domain\Tax\ValueObject\TaxCalculation;
use Domain\Tax\ValueObject\TaxableItem;

interface TaxStrategyInterface
{
    public function calculate(TaxableItem $item): TaxCalculation;

    public function supports(TaxableItem $item): bool;

    public function getJurisdiction(): string;
}
```
