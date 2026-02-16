# Visitor Pattern Templates

## Visitor Interface

**File:** `src/Domain/{BoundedContext}/Visitor/{Name}VisitorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Visitor;

use Domain\{BoundedContext}\{Element1};
use Domain\{BoundedContext}\{Element2};

interface {Name}VisitorInterface
{
    public function visit{Element1}({Element1} $element): mixed;

    public function visit{Element2}({Element2} $element): mixed;
}
```

---

## Concrete Visitor

**File:** `src/Domain/{BoundedContext}/Visitor/{Operation}Visitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Visitor;

use Domain\{BoundedContext}\{Element1};
use Domain\{BoundedContext}\{Element2};

final readonly class {Operation}Visitor implements {Name}VisitorInterface
{
    public function visit{Element1}({Element1} $element): mixed
    {
        // Element1-specific operation logic
        return {result};
    }

    public function visit{Element2}({Element2} $element): mixed
    {
        // Element2-specific operation logic
        return {result};
    }
}
```

---

## Stateful Visitor (with accumulator)

**File:** `src/Domain/{BoundedContext}/Visitor/{Operation}Visitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Visitor;

use Domain\{BoundedContext}\{Element1};
use Domain\{BoundedContext}\{Element2};

final class {Operation}Visitor implements {Name}VisitorInterface
{
    private mixed $accumulator;

    public function __construct()
    {
        $this->accumulator = {initialValue};
    }

    public function visit{Element1}({Element1} $element): mixed
    {
        $this->accumulator = {updateAccumulator};

        return $this->accumulator;
    }

    public function visit{Element2}({Element2} $element): mixed
    {
        $this->accumulator = {updateAccumulator};

        return $this->accumulator;
    }

    public function getResult(): mixed
    {
        return $this->accumulator;
    }
}
```

---

## Visitable Interface

**File:** `src/Domain/{BoundedContext}/VisitableInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

use Domain\{BoundedContext}\Visitor\{Name}VisitorInterface;

interface VisitableInterface
{
    public function accept({Name}VisitorInterface $visitor): mixed;
}
```

---

## Visitable Element

**File:** `src/Domain/{BoundedContext}/{Element}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext};

use Domain\{BoundedContext}\Visitor\{Name}VisitorInterface;

final readonly class {Element} implements VisitableInterface
{
    public function __construct(
        private {Type1} $property1,
        private {Type2} $property2
    ) {}

    public function accept({Name}VisitorInterface $visitor): mixed
    {
        return $visitor->visit{Element}($this);
    }

    public function property1(): {Type1}
    {
        return $this->property1;
    }

    public function property2(): {Type2}
    {
        return $this->property2;
    }
}
```

---

## Order Item Visitor Interface

**File:** `src/Domain/Order/Visitor/OrderItemVisitorInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Visitor;

use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

interface OrderItemVisitorInterface
{
    public function visitProduct(Product $product): int;

    public function visitService(Service $service): int;

    public function visitDiscount(Discount $discount): int;
}
```

---

## Price Calculator Visitor

**File:** `src/Domain/Order/Visitor/PriceCalculatorVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Visitor;

use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final readonly class PriceCalculatorVisitor implements OrderItemVisitorInterface
{
    public function visitProduct(Product $product): int
    {
        return $product->price()->cents() * $product->quantity();
    }

    public function visitService(Service $service): int
    {
        return $service->price()->cents() * $service->duration();
    }

    public function visitDiscount(Discount $discount): int
    {
        return -$discount->amount()->cents();
    }
}
```

---

## Tax Calculator Visitor

**File:** `src/Domain/Order/Visitor/TaxCalculatorVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Visitor;

use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final readonly class TaxCalculatorVisitor implements OrderItemVisitorInterface
{
    public function __construct(
        private float $taxRate = 0.2
    ) {}

    public function visitProduct(Product $product): int
    {
        if (!$product->isTaxable()) {
            return 0;
        }

        $price = $product->price()->cents() * $product->quantity();

        return (int) ($price * $this->taxRate);
    }

    public function visitService(Service $service): int
    {
        $price = $service->price()->cents() * $service->duration();

        return (int) ($price * $this->taxRate);
    }

    public function visitDiscount(Discount $discount): int
    {
        return 0;
    }
}
```

---

## Export Visitor

**File:** `src/Application/Order/Visitor/JsonExportVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Visitor;

use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final readonly class JsonExportVisitor implements OrderItemVisitorInterface
{
    public function visitProduct(Product $product): array
    {
        return [
            'type' => 'product',
            'name' => $product->name(),
            'price' => $product->price()->cents(),
            'quantity' => $product->quantity(),
        ];
    }

    public function visitService(Service $service): array
    {
        return [
            'type' => 'service',
            'name' => $service->name(),
            'price' => $service->price()->cents(),
            'duration' => $service->duration(),
        ];
    }

    public function visitDiscount(Discount $discount): array
    {
        return [
            'type' => 'discount',
            'code' => $discount->code(),
            'amount' => $discount->amount()->cents(),
        ];
    }
}
```
