# Test Data Builder Examples

## Complete Example: Order

### OrderBuilder

```php
<?php

declare(strict_types=1);

namespace Tests\Builder;

use App\Domain\Order\Order;
use App\Domain\Order\OrderId;
use App\Domain\Order\OrderItem;
use App\Domain\Order\OrderStatus;
use App\Domain\Customer\CustomerId;
use App\Domain\Shared\Money;
use DateTimeImmutable;

final class OrderBuilder
{
    private OrderId $id;
    private CustomerId $customerId;
    /** @var list<OrderItem> */
    private array $items = [];
    private OrderStatus $status;
    private DateTimeImmutable $createdAt;

    private function __construct()
    {
        $this->id = OrderId::generate();
        $this->customerId = CustomerId::generate();
        $this->status = OrderStatus::Pending;
        $this->createdAt = new DateTimeImmutable();
    }

    public static function anOrder(): self
    {
        return new self();
    }

    public function withId(OrderId $id): self
    {
        $clone = clone $this;
        $clone->id = $id;
        return $clone;
    }

    public function forCustomer(CustomerId $customerId): self
    {
        $clone = clone $this;
        $clone->customerId = $customerId;
        return $clone;
    }

    public function withItem(Product $product, int $quantity = 1): self
    {
        $clone = clone $this;
        $clone->items[] = new OrderItem($product, $quantity);
        return $clone;
    }

    public function withItems(array $items): self
    {
        $clone = clone $this;
        $clone->items = $items;
        return $clone;
    }

    public function withTotal(Money $total): self
    {
        $clone = clone $this;
        $clone->items = [
            new OrderItem(ProductMother::withPrice($total), 1),
        ];
        return $clone;
    }

    public function pending(): self
    {
        $clone = clone $this;
        $clone->status = OrderStatus::Pending;
        return $clone;
    }

    public function confirmed(): self
    {
        $clone = clone $this;
        $clone->status = OrderStatus::Confirmed;
        // Add item if empty (can't confirm empty order)
        if (empty($clone->items)) {
            $clone->items[] = new OrderItem(ProductMother::book(), 1);
        }
        return $clone;
    }

    public function shipped(): self
    {
        $clone = clone $this;
        $clone->status = OrderStatus::Shipped;
        if (empty($clone->items)) {
            $clone->items[] = new OrderItem(ProductMother::book(), 1);
        }
        return $clone;
    }

    public function cancelled(): self
    {
        $clone = clone $this;
        $clone->status = OrderStatus::Cancelled;
        return $clone;
    }

    public function createdAt(DateTimeImmutable $createdAt): self
    {
        $clone = clone $this;
        $clone->createdAt = $createdAt;
        return $clone;
    }

    public function createdDaysAgo(int $days): self
    {
        return $this->createdAt(
            new DateTimeImmutable("-{$days} days")
        );
    }

    public function build(): Order
    {
        $order = new Order($this->id, $this->customerId, $this->createdAt);

        foreach ($this->items as $item) {
            $order->addItem($item->product(), $item->quantity());
        }

        // Apply status transitions
        if ($this->status === OrderStatus::Confirmed) {
            $order->confirm();
        } elseif ($this->status === OrderStatus::Shipped) {
            $order->confirm();
            $order->ship();
        } elseif ($this->status === OrderStatus::Cancelled) {
            $order->cancel();
        }

        return $order;
    }
}
```

### OrderMother

```php
<?php

declare(strict_types=1);

namespace Tests\Mother;

use App\Domain\Order\Order;
use App\Domain\Customer\CustomerId;
use App\Domain\Shared\Money;
use Tests\Builder\OrderBuilder;

final class OrderMother
{
    public static function pending(): Order
    {
        return OrderBuilder::anOrder()->pending()->build();
    }

    public static function confirmed(): Order
    {
        return OrderBuilder::anOrder()->confirmed()->build();
    }

    public static function shipped(): Order
    {
        return OrderBuilder::anOrder()->shipped()->build();
    }

    public static function cancelled(): Order
    {
        return OrderBuilder::anOrder()->cancelled()->build();
    }

    public static function forCustomer(CustomerId $customerId): Order
    {
        return OrderBuilder::anOrder()
            ->forCustomer($customerId)
            ->build();
    }

    public static function withTotal(Money $total): Order
    {
        return OrderBuilder::anOrder()
            ->withTotal($total)
            ->build();
    }

    public static function empty(): Order
    {
        return OrderBuilder::anOrder()->build();
    }

    public static function withItems(array $items): Order
    {
        return OrderBuilder::anOrder()
            ->withItems($items)
            ->build();
    }

    public static function expired(): Order
    {
        return OrderBuilder::anOrder()
            ->pending()
            ->createdDaysAgo(31)
            ->build();
    }
}
```

## Value Object Builders

```php
<?php

declare(strict_types=1);

namespace Tests\Builder;

use App\Domain\Shared\Money;

final class MoneyBuilder
{
    private int $amount;
    private string $currency;

    private function __construct()
    {
        $this->amount = 1000;
        $this->currency = 'EUR';
    }

    public static function money(): self
    {
        return new self();
    }

    public function withAmount(int $amount): self
    {
        $clone = clone $this;
        $clone->amount = $amount;
        return $clone;
    }

    public function inEUR(): self
    {
        $clone = clone $this;
        $clone->currency = 'EUR';
        return $clone;
    }

    public function inUSD(): self
    {
        $clone = clone $this;
        $clone->currency = 'USD';
        return $clone;
    }

    public function zero(): self
    {
        return $this->withAmount(0);
    }

    public function build(): Money
    {
        return new Money($this->amount, $this->currency);
    }
}

final class MoneyMother
{
    public static function eur(int $amount): Money
    {
        return Money::EUR($amount);
    }

    public static function usd(int $amount): Money
    {
        return Money::USD($amount);
    }

    public static function zero(): Money
    {
        return Money::EUR(0);
    }

    public static function oneHundred(): Money
    {
        return Money::EUR(10000); // cents
    }
}
```

## Usage in Tests

```php
// Builder - custom configuration
$order = OrderBuilder::anOrder()
    ->forCustomer($customerId)
    ->withItem($book, 2)
    ->withItem($pen, 5)
    ->confirmed()
    ->createdDaysAgo(7)
    ->build();

// Mother - common scenarios
$pendingOrder = OrderMother::pending();
$confirmedOrder = OrderMother::confirmed();
$expiredOrder = OrderMother::expired();
$customerOrder = OrderMother::forCustomer($customerId);
```
