# Refactoring for Testability

Patterns for improving code testability when smells are detected.

## 1. Extract Interface (Seam)

**Problem:** Class depends on concrete implementation, impossible to substitute mock.

**Before:**
```php
final class OrderService
{
    public function __construct(
        private readonly DoctrineOrderRepository $repository // ❌ Concrete
    ) {}
}
```

**After:**
```php
final class OrderService
{
    public function __construct(
        private readonly OrderRepositoryInterface $repository // ✅ Interface
    ) {}
}
```

**Apply when:** Mock Overuse, Mocking Final Classes

---

## 2. Constructor Injection

**Problem:** Dependencies created inside class, impossible to control.

**Before:**
```php
final class PaymentService
{
    public function charge(Money $amount): void
    {
        $gateway = new StripeGateway(); // ❌ Hidden dependency
        $gateway->charge($amount);
    }
}
```

**After:**
```php
final class PaymentService
{
    public function __construct(
        private readonly PaymentGatewayInterface $gateway // ✅ Injected
    ) {}

    public function charge(Money $amount): void
    {
        $this->gateway->charge($amount);
    }
}
```

**Apply when:** Mystery Guest, Slow Test, Test Interdependence

---

## 3. Replace Singleton with DI

**Problem:** Singleton creates global state, tests affect each other.

**Before:**
```php
final class Logger
{
    private static ?self $instance = null;

    public static function getInstance(): self // ❌ Singleton
    {
        return self::$instance ??= new self();
    }
}

// Usage
Logger::getInstance()->log($message);
```

**After:**
```php
interface LoggerInterface
{
    public function log(string $message): void;
}

final class Logger implements LoggerInterface { ... }

// Injected via DI container
public function __construct(
    private readonly LoggerInterface $logger // ✅ DI
) {}
```

**Apply when:** Test Interdependence, Fragile Test

---

## 4. Break Temporal Coupling

**Problem:** Methods must be called in specific order.

**Before:**
```php
$service->init();        // Must call first
$service->configure();   // Must call second
$service->execute();     // ❌ Temporal coupling
```

**After:**
```php
// Option A: Builder
$service = ServiceBuilder::create()
    ->withConfig($config)
    ->build();
$service->execute();

// Option B: Constructor
$service = new Service($config);
$service->execute(); // ✅ Ready to use
```

**Apply when:** Fragile Test, Test Interdependence

---

## 5. Extract Pure Function

**Problem:** Business logic mixed with side effects.

**Before:**
```php
public function processOrder(Order $order): void
{
    $total = 0;
    foreach ($order->items as $item) {
        $total += $item->price * $item->quantity;
        if ($item->quantity > 10) {
            $total -= $item->price * 0.1; // Discount
        }
    }
    $this->repository->save($order); // ❌ Side effect mixed
    $this->mailer->send($order);      // ❌ with logic
}
```

**After:**
```php
// Pure function - easy to test
public function calculateTotal(array $items): Money
{
    return array_reduce($items, fn($total, $item) =>
        $total + $this->calculateItemPrice($item),
        Money::zero()
    );
}

// Orchestration with side effects
public function processOrder(Order $order): void
{
    $total = $this->calculateTotal($order->items);
    $order->setTotal($total);
    $this->repository->save($order);
    $this->mailer->send($order);
}
```

**Apply when:** Logic in Test, Eager Test

---

## 6. Replace new with Factory

**Problem:** `new` inside method creates tight coupling.

**Before:**
```php
public function createNotification(): void
{
    $notification = new EmailNotification(); // ❌ Hard-coded
    $notification->send();
}
```

**After:**
```php
public function __construct(
    private readonly NotificationFactoryInterface $factory
) {}

public function createNotification(): void
{
    $notification = $this->factory->create(); // ✅ Flexible
    $notification->send();
}
```

**Apply when:** Mocking Final Classes, Mock Overuse

---

## Testability Score Checklist

| Factor | Score | Description |
|--------|-------|-------------|
| All dependencies via constructor | +2 | Easy to mock |
| Depends on interfaces, not concretes | +2 | Substitutable |
| No static calls | +1 | No hidden coupling |
| No global state | +1 | Isolated tests |
| Pure business logic separated | +2 | Unit testable |
| No temporal coupling | +1 | Simple setup |
| Small, focused class | +1 | Few test cases |

**Score interpretation:**
- 8-10: Excellent testability
- 5-7: Good, minor improvements possible
- 3-4: Poor, refactoring recommended before writing tests
- 0-2: Very poor, significant design issues

---

## Smell → Refactoring Matrix

| Smell | Refactoring Pattern |
|-------|---------------------|
| Mock Overuse | Extract Interface, Replace new with Factory |
| Mocking Final Classes | Extract Interface |
| Test Interdependence | Replace Singleton with DI, Break Temporal Coupling |
| Mystery Guest | Constructor Injection |
| Fragile Test | Extract Pure Function, Break Temporal Coupling |
| Slow Test | Constructor Injection (mock external deps) |
| Logic in Test | Extract Pure Function |
