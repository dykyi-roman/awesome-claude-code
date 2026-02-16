---
name: acc-check-pure-functions
description: Analyzes PHP code for pure function patterns. Detects side-effect-free methods, deterministic output, immutable inputs. Pure functions are easily testable.
---

# Pure Function Check

Analyze PHP code for pure function patterns that improve testability.

## Pure Function Characteristics

A **pure function**:
1. Returns the same output for the same input (deterministic)
2. Has no side effects
3. Doesn't depend on external state

## Detection Patterns

### 1. Non-Deterministic Methods

```php
// IMPURE: Depends on current time
public function isExpired(Token $token): bool
{
    return $token->getExpiresAt() < new DateTime(); // Non-deterministic
}

// PURE: Time is passed in
public function isExpired(Token $token, DateTimeInterface $now): bool
{
    return $token->getExpiresAt() < $now; // Deterministic
}

// IMPURE: Depends on random
public function generateCode(): string
{
    return bin2hex(random_bytes(16)); // Non-deterministic
}

// PURE: Random is injected
public function generateCode(RandomGeneratorInterface $random): string
{
    return bin2hex($random->bytes(16)); // Can be mocked
}
```

### 2. Methods with Side Effects

```php
// IMPURE: Modifies external state
public function calculate(Order $order): Money
{
    $total = $this->computeTotal($order);
    $this->logger->info('Calculated total'); // Side effect
    $this->cache->set($order->getId(), $total); // Side effect
    return $total;
}

// PURE: Only calculates
public function calculate(Order $order): Money
{
    return $this->computeTotal($order);
}

// Separate side effects
public function calculateAndLog(Order $order): Money
{
    $total = $this->calculate($order);
    $this->logger->info('Calculated total');
    return $total;
}
```

### 3. Methods Modifying Input

```php
// IMPURE: Modifies input object
public function process(Order $order): void
{
    $order->setStatus('processed'); // Modifies input
    $order->setProcessedAt(new DateTime());
}

// PURE: Returns new object
public function process(Order $order): Order
{
    return $order->withStatus('processed')
                 ->withProcessedAt(new DateTimeImmutable());
}
```

### 4. Methods Depending on Instance State

```php
// IMPURE: Depends on mutable instance state
class PriceCalculator
{
    private float $taxRate;

    public function setTaxRate(float $rate): void
    {
        $this->taxRate = $rate;
    }

    public function calculate(Money $price): Money
    {
        return $price->multiply(1 + $this->taxRate); // Depends on state
    }
}

// PURE: All dependencies as parameters
class PriceCalculator
{
    public function calculate(Money $price, float $taxRate): Money
    {
        return $price->multiply(1 + $taxRate);
    }
}
```

### 5. Static State Dependency

```php
// IMPURE: Depends on static state
class Config
{
    private static array $settings = [];

    public static function set(string $key, $value): void
    {
        self::$settings[$key] = $value;
    }
}

public function getDiscount(): float
{
    return Config::get('discount_rate'); // Global state
}

// PURE: Config injected
public function getDiscount(ConfigInterface $config): float
{
    return $config->get('discount_rate');
}
```

### 6. I/O in Business Logic

```php
// IMPURE: File I/O
public function loadUserPreferences(int $userId): array
{
    $path = "/config/users/{$userId}.json";
    return json_decode(file_get_contents($path), true); // I/O
}

// PURE: Data passed in
public function parseUserPreferences(string $json): array
{
    return json_decode($json, true);
}
```

## Pure Function Patterns

### Extract Pure Core

```php
// Before: Mixed logic and effects
public function processPayment(Order $order): PaymentResult
{
    $amount = $this->calculateTotal($order); // Pure
    $result = $this->gateway->charge($amount); // Impure
    $this->notifier->notify($order); // Impure
    return $result;
}

// After: Separated
// Pure function - easily testable
public function calculatePaymentAmount(Order $order): Money
{
    $subtotal = $this->calculateSubtotal($order);
    $tax = $this->calculateTax($subtotal);
    $discount = $this->calculateDiscount($order);
    return $subtotal->add($tax)->subtract($discount);
}

// Impure orchestration
public function processPayment(Order $order): PaymentResult
{
    $amount = $this->calculatePaymentAmount($order);
    return $this->gateway->charge($amount);
}
```

### Functional Core, Imperative Shell

```php
// Pure domain logic
final readonly class OrderCalculator
{
    public function calculateTotal(array $items, DiscountPolicy $policy): Money
    {
        $subtotal = array_reduce(
            $items,
            fn($sum, $item) => $sum->add($item->getLineTotal()),
            Money::zero()
        );
        return $policy->apply($subtotal);
    }
}

// Impure service (thin)
final class OrderService
{
    public function __construct(
        private OrderCalculator $calculator,
        private OrderRepository $repository,
    ) {}

    public function updateTotal(int $orderId): void
    {
        $order = $this->repository->find($orderId);
        $total = $this->calculator->calculateTotal(
            $order->getItems(),
            $order->getDiscountPolicy()
        );
        $order->setTotal($total);
        $this->repository->save($order);
    }
}
```

## Grep Patterns

```bash
# Random in methods
Grep: "(random_bytes|rand|mt_rand|shuffle)\(" --glob "**/*.php"

# DateTime construction
Grep: "new\s+DateTime\(|DateTime::now" --glob "**/*.php"

# File I/O
Grep: "(file_get_contents|file_put_contents|fopen|fwrite)\(" --glob "**/*.php"

# Global state
Grep: "(self|static)::\\\$|global\s+\\\$" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| I/O in calculation | 🟠 Major |
| Modifying input parameters | 🟠 Major |
| Non-deterministic (time/random) | 🟡 Minor |
| Depends on mutable state | 🟡 Minor |

## Output Format

```markdown
### Pure Function Issue: [Description]

**Severity:** 🟠/🟡
**Location:** `file.php:line`
**Type:** [Non-Deterministic|Side Effect|Mutable State|...]

**Issue:**
Method `calculate` depends on current time, making it non-deterministic.

**Current:**
```php
public function isExpired(Token $token): bool
{
    return $token->getExpiresAt() < new DateTime();
}
```

**Suggested:**
```php
public function isExpired(Token $token, DateTimeInterface $now): bool
{
    return $token->getExpiresAt() < $now;
}
```

**Testing Impact:**
- Before: Need to manipulate system time or accept flaky tests
- After: Pass any DateTime, test edge cases easily
```
