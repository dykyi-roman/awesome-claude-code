# Strategy Pattern Templates

## Strategy Interface

**File:** `src/{architecture-path}/Strategy/{Name}StrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

interface {Name}StrategyInterface
{
    public function execute({InputType} $input): {OutputType};

    public function supports({InputType} $input): bool;
}
```

---

## Abstract Strategy (Optional)

**File:** `src/{architecture-path}/Strategy/Abstract{Name}Strategy.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

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

**File:** `src/{architecture-path}/Strategy/{Variant}{Name}Strategy.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

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

**File:** `src/{architecture-path}/Strategy/{Name}Context.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

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

**File:** `src/{architecture-path}/Strategy/{Name}StrategyResolver.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

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

**File:** `src/{architecture-path}/Strategy/PricingStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

use ValueObject\Price;
use ValueObject\PricingContext;

interface PricingStrategyInterface
{
    public function calculatePrice(PricingContext $context): Price;

    public function supports(PricingContext $context): bool;
}
```

---

## Shipping Strategy Interface

**File:** `src/{architecture-path}/Strategy/ShippingCostStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

use ValueObject\ShippingCost;
use ValueObject\ShippingRequest;

interface ShippingCostStrategyInterface
{
    public function calculate(ShippingRequest $request): ShippingCost;

    public function supports(ShippingRequest $request): bool;

    public function getName(): string;
}
```

---

## Tax Strategy Interface

**File:** `src/{architecture-path}/Strategy/TaxStrategyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Strategy;

use ValueObject\TaxCalculation;
use ValueObject\TaxableItem;

interface TaxStrategyInterface
{
    public function calculate(TaxableItem $item): TaxCalculation;

    public function supports(TaxableItem $item): bool;

    public function getJurisdiction(): string;
}
```
