# Visitor Pattern Examples

## Order Item Visitors

### Visitable Interface

**File:** `src/Domain/Order/VisitableInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order;

use Domain\Order\Visitor\OrderItemVisitorInterface;

interface VisitableInterface
{
    public function accept(OrderItemVisitorInterface $visitor): mixed;
}
```

---

### Product (Visitable Element)

**File:** `src/Domain/Order/ValueObject/Product.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

use Domain\Order\VisitableInterface;
use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Shared\ValueObject\Money;

final readonly class Product implements VisitableInterface
{
    public function __construct(
        private string $name,
        private Money $price,
        private int $quantity,
        private bool $taxable = true
    ) {}

    public function accept(OrderItemVisitorInterface $visitor): mixed
    {
        return $visitor->visitProduct($this);
    }

    public function name(): string
    {
        return $this->name;
    }

    public function price(): Money
    {
        return $this->price;
    }

    public function quantity(): int
    {
        return $this->quantity;
    }

    public function isTaxable(): bool
    {
        return $this->taxable;
    }
}
```

---

### Service (Visitable Element)

**File:** `src/Domain/Order/ValueObject/Service.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

use Domain\Order\VisitableInterface;
use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Shared\ValueObject\Money;

final readonly class Service implements VisitableInterface
{
    public function __construct(
        private string $name,
        private Money $price,
        private int $duration
    ) {}

    public function accept(OrderItemVisitorInterface $visitor): mixed
    {
        return $visitor->visitService($this);
    }

    public function name(): string
    {
        return $this->name;
    }

    public function price(): Money
    {
        return $this->price;
    }

    public function duration(): int
    {
        return $this->duration;
    }
}
```

---

### Discount (Visitable Element)

**File:** `src/Domain/Order/ValueObject/Discount.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\ValueObject;

use Domain\Order\VisitableInterface;
use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Shared\ValueObject\Money;

final readonly class Discount implements VisitableInterface
{
    public function __construct(
        private string $code,
        private Money $amount
    ) {}

    public function accept(OrderItemVisitorInterface $visitor): mixed
    {
        return $visitor->visitDiscount($this);
    }

    public function code(): string
    {
        return $this->code;
    }

    public function amount(): Money
    {
        return $this->amount;
    }
}
```

---

### PriceCalculatorVisitor

**File:** `src/Domain/Order/Visitor/PriceCalculatorVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Visitor;

use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final class PriceCalculatorVisitor implements OrderItemVisitorInterface
{
    private int $total = 0;

    public function visitProduct(Product $product): int
    {
        $price = $product->price()->cents() * $product->quantity();
        $this->total += $price;

        return $price;
    }

    public function visitService(Service $service): int
    {
        $price = $service->price()->cents() * $service->duration();
        $this->total += $price;

        return $price;
    }

    public function visitDiscount(Discount $discount): int
    {
        $amount = -$discount->amount()->cents();
        $this->total += $amount;

        return $amount;
    }

    public function getTotal(): int
    {
        return $this->total;
    }
}
```

---

### TaxCalculatorVisitor

**File:** `src/Domain/Order/Visitor/TaxCalculatorVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Visitor;

use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final class TaxCalculatorVisitor implements OrderItemVisitorInterface
{
    private int $totalTax = 0;

    public function __construct(
        private readonly float $taxRate = 0.2
    ) {}

    public function visitProduct(Product $product): int
    {
        if (!$product->isTaxable()) {
            return 0;
        }

        $price = $product->price()->cents() * $product->quantity();
        $tax = (int) ($price * $this->taxRate);

        $this->totalTax += $tax;

        return $tax;
    }

    public function visitService(Service $service): int
    {
        $price = $service->price()->cents() * $service->duration();
        $tax = (int) ($price * $this->taxRate);

        $this->totalTax += $tax;

        return $tax;
    }

    public function visitDiscount(Discount $discount): int
    {
        return 0;
    }

    public function getTotalTax(): int
    {
        return $this->totalTax;
    }
}
```

---

### JsonExportVisitor

**File:** `src/Application/Order/Visitor/JsonExportVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Visitor;

use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final class JsonExportVisitor implements OrderItemVisitorInterface
{
    private array $items = [];

    public function visitProduct(Product $product): array
    {
        $item = [
            'type' => 'product',
            'name' => $product->name(),
            'price' => $product->price()->cents(),
            'quantity' => $product->quantity(),
            'taxable' => $product->isTaxable(),
        ];

        $this->items[] = $item;

        return $item;
    }

    public function visitService(Service $service): array
    {
        $item = [
            'type' => 'service',
            'name' => $service->name(),
            'price' => $service->price()->cents(),
            'duration' => $service->duration(),
        ];

        $this->items[] = $item;

        return $item;
    }

    public function visitDiscount(Discount $discount): array
    {
        $item = [
            'type' => 'discount',
            'code' => $discount->code(),
            'amount' => $discount->amount()->cents(),
        ];

        $this->items[] = $item;

        return $item;
    }

    public function toJson(): string
    {
        return json_encode($this->items, JSON_PRETTY_PRINT);
    }
}
```

---

### XmlExportVisitor

**File:** `src/Application/Order/Visitor/XmlExportVisitor.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order\Visitor;

use Domain\Order\Visitor\OrderItemVisitorInterface;
use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;

final class XmlExportVisitor implements OrderItemVisitorInterface
{
    private string $xml = '';

    public function __construct()
    {
        $this->xml = '<?xml version="1.0" encoding="UTF-8"?>' . "\n<items>\n";
    }

    public function visitProduct(Product $product): string
    {
        $item = sprintf(
            "  <product>\n" .
            "    <name>%s</name>\n" .
            "    <price>%d</price>\n" .
            "    <quantity>%d</quantity>\n" .
            "    <taxable>%s</taxable>\n" .
            "  </product>\n",
            htmlspecialchars($product->name()),
            $product->price()->cents(),
            $product->quantity(),
            $product->isTaxable() ? 'true' : 'false'
        );

        $this->xml .= $item;

        return $item;
    }

    public function visitService(Service $service): string
    {
        $item = sprintf(
            "  <service>\n" .
            "    <name>%s</name>\n" .
            "    <price>%d</price>\n" .
            "    <duration>%d</duration>\n" .
            "  </service>\n",
            htmlspecialchars($service->name()),
            $service->price()->cents(),
            $service->duration()
        );

        $this->xml .= $item;

        return $item;
    }

    public function visitDiscount(Discount $discount): string
    {
        $item = sprintf(
            "  <discount>\n" .
            "    <code>%s</code>\n" .
            "    <amount>%d</amount>\n" .
            "  </discount>\n",
            htmlspecialchars($discount->code()),
            $discount->amount()->cents()
        );

        $this->xml .= $item;

        return $item;
    }

    public function toXml(): string
    {
        return $this->xml . "</items>";
    }
}
```

---

## Unit Tests

### PriceCalculatorVisitorTest

**File:** `tests/Unit/Domain/Order/Visitor/PriceCalculatorVisitorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Visitor;

use Domain\Order\Visitor\PriceCalculatorVisitor;
use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(PriceCalculatorVisitor::class)]
final class PriceCalculatorVisitorTest extends TestCase
{
    private PriceCalculatorVisitor $visitor;

    protected function setUp(): void
    {
        $this->visitor = new PriceCalculatorVisitor();
    }

    public function testCalculatesProductPrice(): void
    {
        $product = new Product(
            name: 'Laptop',
            price: Money::cents(100000),
            quantity: 2
        );

        $price = $product->accept($this->visitor);

        self::assertSame(200000, $price);
    }

    public function testCalculatesServicePrice(): void
    {
        $service = new Service(
            name: 'Consultation',
            price: Money::cents(5000),
            duration: 3
        );

        $price = $service->accept($this->visitor);

        self::assertSame(15000, $price);
    }

    public function testAppliesDiscount(): void
    {
        $discount = new Discount(
            code: 'SAVE20',
            amount: Money::cents(2000)
        );

        $amount = $discount->accept($this->visitor);

        self::assertSame(-2000, $amount);
    }

    public function testAccumulatesTotal(): void
    {
        $product = new Product(
            name: 'Laptop',
            price: Money::cents(100000),
            quantity: 1
        );

        $service = new Service(
            name: 'Setup',
            price: Money::cents(5000),
            duration: 2
        );

        $discount = new Discount(
            code: 'DISCOUNT',
            amount: Money::cents(10000)
        );

        $product->accept($this->visitor);
        $service->accept($this->visitor);
        $discount->accept($this->visitor);

        self::assertSame(100000, $this->visitor->getTotal());
    }
}
```

---

### TaxCalculatorVisitorTest

**File:** `tests/Unit/Domain/Order/Visitor/TaxCalculatorVisitorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Order\Visitor;

use Domain\Order\Visitor\TaxCalculatorVisitor;
use Domain\Order\ValueObject\Product;
use Domain\Order\ValueObject\Service;
use Domain\Order\ValueObject\Discount;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(TaxCalculatorVisitor::class)]
final class TaxCalculatorVisitorTest extends TestCase
{
    private TaxCalculatorVisitor $visitor;

    protected function setUp(): void
    {
        $this->visitor = new TaxCalculatorVisitor(taxRate: 0.2);
    }

    public function testCalculatesTaxForTaxableProduct(): void
    {
        $product = new Product(
            name: 'Laptop',
            price: Money::cents(100000),
            quantity: 1,
            taxable: true
        );

        $tax = $product->accept($this->visitor);

        self::assertSame(20000, $tax);
    }

    public function testSkipsTaxForNonTaxableProduct(): void
    {
        $product = new Product(
            name: 'Book',
            price: Money::cents(2000),
            quantity: 1,
            taxable: false
        );

        $tax = $product->accept($this->visitor);

        self::assertSame(0, $tax);
    }

    public function testCalculatesTaxForService(): void
    {
        $service = new Service(
            name: 'Consultation',
            price: Money::cents(10000),
            duration: 2
        );

        $tax = $service->accept($this->visitor);

        self::assertSame(4000, $tax);
    }

    public function testDiscountDoesNotAffectTax(): void
    {
        $discount = new Discount(
            code: 'SAVE50',
            amount: Money::cents(5000)
        );

        $tax = $discount->accept($this->visitor);

        self::assertSame(0, $tax);
    }

    public function testAccumulatesTotalTax(): void
    {
        $product = new Product(
            name: 'Laptop',
            price: Money::cents(50000),
            quantity: 2,
            taxable: true
        );

        $service = new Service(
            name: 'Setup',
            price: Money::cents(10000),
            duration: 1
        );

        $product->accept($this->visitor);
        $service->accept($this->visitor);

        self::assertSame(22000, $this->visitor->getTotalTax());
    }
}
```
