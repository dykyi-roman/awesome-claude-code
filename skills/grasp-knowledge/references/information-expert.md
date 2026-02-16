# Information Expert Pattern

## Definition

Assign responsibility to the class that has the information needed to fulfill it. The class with the data should have the behavior that operates on that data.

## When to Apply

- Deciding which class should have a method
- Choosing where to put calculation logic
- Determining behavior ownership

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Feature Envy | Multiple getter chains | CRITICAL |
| Data Class | Only getters/setters | CRITICAL |
| Train Wreck | `->get()->get()->get()` | WARNING |
| Anemic Model | Service does all logic | WARNING |

### Compliance Signs

- Data and behavior together
- Short method chains
- Rich domain objects
- Tell, don't ask

## Patterns

### Tell, Don't Ask

```php
<?php

declare(strict_types=1);

// BAD: Asking for data, then deciding
final class OrderService
{
    public function canShip(Order $order): bool
    {
        if ($order->getStatus() !== OrderStatus::Paid) {
            return false;
        }
        if ($order->getShippingAddress() === null) {
            return false;
        }
        foreach ($order->getLines() as $line) {
            if ($line->getProduct()->getStock() < $line->getQuantity()) {
                return false;
            }
        }
        return true;
    }
}

// GOOD: Telling the object what to do
final class Order
{
    public function canShip(): bool
    {
        return $this->status === OrderStatus::Paid
            && $this->shippingAddress !== null
            && $this->hasStock();
    }

    private function hasStock(): bool
    {
        return array_all(
            $this->lines,
            fn(OrderLine $line) => $line->hasStock(),
        );
    }
}

final readonly class OrderLine
{
    public function hasStock(): bool
    {
        return $this->product->hasStockFor($this->quantity);
    }
}
```

### Calculation in Owner

```php
<?php

declare(strict_types=1);

// BAD: External calculation
final class PriceCalculator
{
    public function calculateLineTotal(OrderLine $line): Money
    {
        $price = $line->getProduct()->getPrice();
        $quantity = $line->getQuantity()->getValue();
        $discount = $line->getDiscount()?->getPercentage() ?? 0;

        return $price
            ->multiply($quantity)
            ->multiply(1 - $discount / 100);
    }
}

// GOOD: Calculation where data lives
final readonly class OrderLine
{
    public function __construct(
        private Product $product,
        private Quantity $quantity,
        private ?Discount $discount = null,
    ) {}

    public function total(): Money
    {
        $linePrice = $this->product->price->multiply($this->quantity->value);

        return $this->discount?->apply($linePrice) ?? $linePrice;
    }
}

final readonly class Discount
{
    public function __construct(
        private Percentage $percentage,
    ) {}

    public function apply(Money $price): Money
    {
        return $price->multiply(1 - $this->percentage->value / 100);
    }
}
```

### Validation in Entity

```php
<?php

declare(strict_types=1);

// BAD: External validation
final class OrderValidator
{
    public function validate(Order $order): array
    {
        $errors = [];

        if (count($order->getLines()) === 0) {
            $errors[] = 'Order must have at least one line';
        }

        if ($order->getTotal()->isNegative()) {
            $errors[] = 'Order total cannot be negative';
        }

        return $errors;
    }
}

// GOOD: Self-validating entity
final class Order
{
    /** @var OrderLine[] */
    private array $lines = [];

    public function addLine(OrderLine $line): void
    {
        $this->lines[] = $line;
    }

    public function place(): void
    {
        $this->ensureHasLines();
        $this->ensurePositiveTotal();

        $this->status = OrderStatus::Placed;
        $this->placedAt = new DateTimeImmutable();
    }

    private function ensureHasLines(): void
    {
        if (count($this->lines) === 0) {
            throw new EmptyOrderException();
        }
    }

    private function ensurePositiveTotal(): void
    {
        if ($this->total()->isNegative()) {
            throw new InvalidOrderTotalException();
        }
    }
}
```

## DDD Application

### Aggregate Behavior

```php
<?php

declare(strict_types=1);

// Aggregate has all information for its invariants
final class Cart
{
    /** @var CartItem[] */
    private array $items = [];

    public function addItem(Product $product, Quantity $quantity): void
    {
        $existingItem = $this->findItem($product->id);

        if ($existingItem !== null) {
            $existingItem->increaseQuantity($quantity);
        } else {
            $this->items[] = new CartItem($product, $quantity);
        }
    }

    public function removeItem(ProductId $productId): void
    {
        $this->items = array_filter(
            $this->items,
            fn(CartItem $item) => !$item->productId->equals($productId),
        );
    }

    public function total(): Money
    {
        return array_reduce(
            $this->items,
            fn(Money $sum, CartItem $item) => $sum->add($item->subtotal()),
            Money::zero(),
        );
    }

    private function findItem(ProductId $id): ?CartItem
    {
        foreach ($this->items as $item) {
            if ($item->productId->equals($id)) {
                return $item;
            }
        }
        return null;
    }
}
```

## Anti-patterns

### Feature Envy

```php
<?php

// ANTIPATTERN: Method uses another object's data more
final class InvoiceGenerator
{
    public function generate(Order $order): Invoice
    {
        // Accesses Order's internal data extensively
        $invoice = new Invoice();
        $invoice->customerName = $order->getCustomer()->getName();
        $invoice->customerAddress = $order->getCustomer()->getAddress()->format();
        $invoice->customerEmail = $order->getCustomer()->getEmail();

        foreach ($order->getLines() as $line) {
            $invoice->addLine(
                $line->getProduct()->getName(),
                $line->getQuantity()->getValue(),
                $line->getProduct()->getPrice()->getValue(),
            );
        }

        return $invoice;
    }
}

// FIX: Move to Order
final class Order
{
    public function toInvoice(): Invoice
    {
        return new Invoice(
            $this->customer->toInvoiceRecipient(),
            $this->lines->toInvoiceLines(),
            $this->total(),
        );
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Method chain depth | ≤2 | 3 | >3 |
| Getters per entity | ≤5 | 6-8 | >8 |
| External calculations | 0 | 1-2 | >2 |
