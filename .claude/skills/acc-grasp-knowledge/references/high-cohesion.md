# High Cohesion Pattern

## Definition

Assign responsibilities so that cohesion remains high. Cohesion is a measure of how strongly related and focused the responsibilities of an element are.

## When to Apply

- Evaluating class responsibilities
- Deciding if a class should be split
- Organizing related functionality

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Unrelated methods | Different domains in one class | CRITICAL |
| God class | >500 lines, many methods | CRITICAL |
| Multiple responsibilities | Class name with "And/Or" | WARNING |
| Low method relationship | Methods don't call each other | WARNING |

### Compliance Signs

- All methods relate to single purpose
- Class is easily named (noun)
- Methods call each other
- Fits in one screen (~200 lines)

## Types of Cohesion

| Type | Description | Quality |
|------|-------------|---------|
| Coincidental | Random grouping | BAD |
| Logical | Grouped by type, not function | BAD |
| Temporal | Grouped by when executed | POOR |
| Procedural | Grouped by execution order | POOR |
| Communicational | Operate on same data | GOOD |
| Sequential | Output of one is input of next | GOOD |
| Functional | All contribute to single task | BEST |

## Patterns

### Functional Cohesion

```php
<?php

declare(strict_types=1);

// HIGH COHESION: All methods support single responsibility
final class Order
{
    private OrderId $id;
    private CustomerId $customerId;
    /** @var OrderLine[] */
    private array $lines = [];
    private OrderStatus $status;
    private ?DateTimeImmutable $placedAt = null;

    // All methods relate to Order behavior
    public function addLine(Product $product, Quantity $quantity): void
    {
        $this->ensureNotPlaced();
        $this->lines[] = new OrderLine($product, $quantity);
    }

    public function removeLine(OrderLineId $lineId): void
    {
        $this->ensureNotPlaced();
        $this->lines = array_filter(
            $this->lines,
            fn(OrderLine $line) => !$line->id->equals($lineId),
        );
    }

    public function place(): void
    {
        $this->ensureHasLines();
        $this->status = OrderStatus::Placed;
        $this->placedAt = new DateTimeImmutable();
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn(Money $sum, OrderLine $line) => $sum->add($line->total()),
            Money::zero(),
        );
    }

    private function ensureNotPlaced(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new OrderAlreadyPlacedException($this->id);
        }
    }

    private function ensureHasLines(): void
    {
        if (empty($this->lines)) {
            throw new EmptyOrderException($this->id);
        }
    }
}
```

### Extract Class for Cohesion

```php
<?php

declare(strict_types=1);

// LOW COHESION: User class does too many things
final class User
{
    // Authentication
    public function login(): void { /* ... */ }
    public function logout(): void { /* ... */ }
    public function refreshToken(): void { /* ... */ }

    // Profile
    public function updateName(): void { /* ... */ }
    public function updateAvatar(): void { /* ... */ }
    public function updatePreferences(): void { /* ... */ }

    // Notifications
    public function enableEmailNotifications(): void { /* ... */ }
    public function disablePushNotifications(): void { /* ... */ }

    // Subscription
    public function subscribe(): void { /* ... */ }
    public function cancelSubscription(): void { /* ... */ }
    public function upgradeSubscription(): void { /* ... */ }
}

// HIGH COHESION: Split into focused classes
final class User
{
    private UserId $id;
    private Email $email;
    private UserProfile $profile;
    private UserPreferences $preferences;
    private ?Subscription $subscription = null;

    public function updateProfile(ProfileData $data): void
    {
        $this->profile = $this->profile->update($data);
    }

    public function subscribe(Plan $plan): void
    {
        $this->subscription = Subscription::create($this->id, $plan);
    }
}

final readonly class UserProfile
{
    public function __construct(
        private string $firstName,
        private string $lastName,
        private ?Avatar $avatar,
    ) {}

    public function update(ProfileData $data): self
    {
        return new self(
            $data->firstName ?? $this->firstName,
            $data->lastName ?? $this->lastName,
            $data->avatar ?? $this->avatar,
        );
    }

    public function fullName(): string
    {
        return "{$this->firstName} {$this->lastName}";
    }
}

final readonly class UserPreferences
{
    public function __construct(
        private bool $emailNotifications,
        private bool $pushNotifications,
        private string $locale,
        private string $timezone,
    ) {}

    public function withEmailNotifications(bool $enabled): self
    {
        return new self(
            $enabled,
            $this->pushNotifications,
            $this->locale,
            $this->timezone,
        );
    }
}

final class Subscription
{
    public static function create(UserId $userId, Plan $plan): self { /* ... */ }
    public function upgrade(Plan $newPlan): void { /* ... */ }
    public function cancel(): void { /* ... */ }
    public function renew(): void { /* ... */ }
}
```

### Service with Single Purpose

```php
<?php

declare(strict_types=1);

// LOW COHESION: Service does too many things
final class OrderService
{
    public function createOrder(array $data): Order { /* ... */ }
    public function processPayment(Order $order): void { /* ... */ }
    public function sendConfirmation(Order $order): void { /* ... */ }
    public function generateInvoice(Order $order): Invoice { /* ... */ }
    public function updateInventory(Order $order): void { /* ... */ }
    public function calculateShipping(Order $order): Money { /* ... */ }
    public function applyDiscount(Order $order, Coupon $coupon): void { /* ... */ }
}

// HIGH COHESION: Each service has single responsibility
final readonly class CreateOrderHandler
{
    public function __invoke(CreateOrderCommand $command): Order { /* ... */ }
}

final readonly class ProcessPaymentHandler
{
    public function __invoke(ProcessPaymentCommand $command): void { /* ... */ }
}

final readonly class OrderPricingService
{
    public function calculateTotal(Order $order): Money { /* ... */ }
    public function applyDiscount(Order $order, Discount $discount): Money { /* ... */ }
}

final readonly class ShippingCalculator
{
    public function calculate(Shipment $shipment): Money { /* ... */ }
}

final readonly class InvoiceGenerator
{
    public function generate(Order $order): Invoice { /* ... */ }
}
```

### Value Object Cohesion

```php
<?php

declare(strict_types=1);

// HIGH COHESION: Value object with related operations
final readonly class Money
{
    public function __construct(
        private int $cents,
        private Currency $currency,
    ) {}

    public function add(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->cents + $other->cents, $this->currency);
    }

    public function subtract(self $other): self
    {
        $this->ensureSameCurrency($other);
        return new self($this->cents - $other->cents, $this->currency);
    }

    public function multiply(float $factor): self
    {
        return new self((int) round($this->cents * $factor), $this->currency);
    }

    public function isPositive(): bool
    {
        return $this->cents > 0;
    }

    public function isNegative(): bool
    {
        return $this->cents < 0;
    }

    public function isGreaterThan(self $other): bool
    {
        $this->ensureSameCurrency($other);
        return $this->cents > $other->cents;
    }

    public function formatted(): string
    {
        return $this->currency->format($this->cents);
    }

    private function ensureSameCurrency(self $other): void
    {
        if (!$this->currency->equals($other->currency)) {
            throw new CurrencyMismatchException();
        }
    }
}
```

## DDD Application

### Aggregate Cohesion

```php
<?php

declare(strict_types=1);

// Aggregate maintains cohesion around consistency boundary
final class ShoppingCart
{
    private CartId $id;
    private CustomerId $customerId;
    /** @var CartItem[] */
    private array $items = [];
    private ?Coupon $appliedCoupon = null;

    // All methods relate to cart operations
    public function addItem(ProductId $productId, Quantity $quantity, Money $price): void
    {
        $existingItem = $this->findItem($productId);

        if ($existingItem !== null) {
            $existingItem->adjustQuantity($quantity);
        } else {
            $this->items[] = new CartItem($productId, $quantity, $price);
        }
    }

    public function removeItem(ProductId $productId): void
    {
        $this->items = array_filter(
            $this->items,
            fn(CartItem $item) => !$item->productId->equals($productId),
        );
    }

    public function applyCoupon(Coupon $coupon): void
    {
        if (!$coupon->isApplicableTo($this)) {
            throw new CouponNotApplicableException();
        }
        $this->appliedCoupon = $coupon;
    }

    public function subtotal(): Money
    {
        return array_reduce(
            $this->items,
            fn(Money $sum, CartItem $item) => $sum->add($item->total()),
            Money::zero(),
        );
    }

    public function total(): Money
    {
        $subtotal = $this->subtotal();
        return $this->appliedCoupon?->apply($subtotal) ?? $subtotal;
    }

    private function findItem(ProductId $productId): ?CartItem
    {
        foreach ($this->items as $item) {
            if ($item->productId->equals($productId)) {
                return $item;
            }
        }
        return null;
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Lines of code | <200 | 200-400 | >400 |
| Public methods | ≤7 | 8-12 | >12 |
| LCOM (Lack of Cohesion) | <0.3 | 0.3-0.7 | >0.7 |
| Related method calls | High | Medium | Low |
