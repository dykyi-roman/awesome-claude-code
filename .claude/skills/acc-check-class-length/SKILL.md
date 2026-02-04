---
name: acc-check-class-length
description: Analyzes PHP code for class length issues. Detects classes exceeding 300 lines, God class indicators, cohesion issues, SRP violations.
---

# Class Length Check

Analyze PHP code for class size and cohesion issues.

## Detection Thresholds

| Lines | Classification |
|-------|----------------|
| 1-100 | ✅ Ideal |
| 101-200 | ⚠️ Acceptable |
| 201-300 | 🟡 Large - review needed |
| 301-500 | 🟠 Too large - split |
| 501+ | 🔴 God class - urgent refactoring |

## Detection Patterns

### 1. God Class Indicators

```php
// GOD CLASS: Does everything
class OrderManager
{
    // Handles orders
    public function createOrder() {}
    public function updateOrder() {}
    public function cancelOrder() {}

    // Handles payments
    public function processPayment() {}
    public function refundPayment() {}

    // Handles shipping
    public function createShipment() {}
    public function trackShipment() {}

    // Handles inventory
    public function reserveStock() {}
    public function releaseStock() {}

    // Handles notifications
    public function sendOrderConfirmation() {}
    public function sendShippingNotification() {}

    // Handles reporting
    public function generateOrderReport() {}
    public function exportToExcel() {}

    // 50+ more methods...
}

// GOOD: Split by responsibility
class OrderService {}
class PaymentService {}
class ShippingService {}
class InventoryService {}
class NotificationService {}
class ReportingService {}
```

### 2. Low Cohesion Signs

```php
// LOW COHESION: Methods don't use same properties
class UserService
{
    private $userRepository;
    private $emailService;
    private $paymentGateway;
    private $logService;
    private $cacheService;

    // User methods use $userRepository
    public function findUser() {}
    public function updateUser() {}

    // Email methods use $emailService (unrelated)
    public function sendEmail() {}
    public function validateEmail() {}

    // Payment methods use $paymentGateway (unrelated)
    public function processPayment() {}
    public function checkBalance() {}
}

// HIGH COHESION: All methods use same core dependencies
class UserService
{
    public function __construct(
        private UserRepository $userRepository,
        private PasswordHasher $hasher,
    ) {}

    public function findUser(int $id): User {}
    public function createUser(UserData $data): User {}
    public function updateUser(User $user, UserData $data): void {}
    public function changePassword(User $user, string $password): void {}
}
```

### 3. Too Many Dependencies

```php
// TOO MANY DEPENDENCIES: Indicates SRP violation
class OrderProcessor
{
    public function __construct(
        private OrderRepository $orderRepository,
        private ProductRepository $productRepository,
        private UserRepository $userRepository,
        private PaymentGateway $paymentGateway,
        private ShippingService $shippingService,
        private InventoryService $inventoryService,
        private EmailService $emailService,
        private SmsService $smsService,
        private PushNotificationService $pushService,
        private LoggerInterface $logger,
        private CacheInterface $cache,
        private EventDispatcher $eventDispatcher,
        // 10+ more...
    ) {}
}

// GUIDELINE: Max 5-7 dependencies
class OrderProcessor
{
    public function __construct(
        private OrderRepository $orderRepository,
        private PaymentProcessor $paymentProcessor,
        private NotificationService $notificationService,
        private EventDispatcher $eventDispatcher,
    ) {}
}
```

### 4. Feature Envy

```php
// FEATURE ENVY: Class manipulates other class's data extensively
class OrderPrinter
{
    public function print(Order $order): string
    {
        $output = "Order: " . $order->getId() . "\n";
        $output .= "Customer: " . $order->getCustomer()->getName() . "\n";
        $output .= "Address: " . $order->getCustomer()->getAddress()->getStreet() . "\n";
        $output .= "City: " . $order->getCustomer()->getAddress()->getCity() . "\n";

        $total = 0;
        foreach ($order->getItems() as $item) {
            $output .= $item->getProduct()->getName() . ": ";
            $output .= $item->getQuantity() . " x " . $item->getPrice() . "\n";
            $total += $item->getQuantity() * $item->getPrice();
        }
        // Many more lines accessing Order internals...
    }
}

// BETTER: Move logic to Order class
class Order
{
    public function format(): string
    {
        // Order knows how to format itself
    }
}
```

### 5. Too Many Public Methods

```php
// TOO MANY PUBLIC METHODS: API surface too large
class UserService
{
    public function findById() {}
    public function findByEmail() {}
    public function findByPhone() {}
    public function findByUsername() {}
    public function findActive() {}
    public function findInactive() {}
    public function create() {}
    public function update() {}
    public function delete() {}
    public function activate() {}
    public function deactivate() {}
    public function ban() {}
    public function unban() {}
    public function verify() {}
    // 20+ more public methods
}

// BETTER: Split into focused classes
class UserFinder {}
class UserModifier {}
class UserStatusManager {}
```

## Metrics

### LCOM (Lack of Cohesion of Methods)

- LCOM = 0: Perfect cohesion
- LCOM < 0.5: Good cohesion
- LCOM > 0.8: Poor cohesion

### Class Complexity Indicators

- Lines of code > 300
- Methods > 20
- Properties > 10
- Dependencies > 7
- Cyclomatic complexity > 50

## Refactoring Strategies

### Extract Class

```php
// Before: One large class
class Order
{
    // Order data and methods (30 methods)
    // Pricing logic (10 methods)
    // Shipping logic (8 methods)
    // Notification logic (5 methods)
}

// After: Multiple focused classes
class Order {} // Core order data
class OrderPricing {} // Price calculation
class OrderShipping {} // Shipping logic
class OrderNotifier {} // Notifications
```

### Introduce Domain Events

```php
// Before: Class does everything
class OrderService
{
    public function complete(Order $order): void
    {
        $order->complete();
        $this->updateInventory($order);
        $this->sendEmail($order);
        $this->createInvoice($order);
        $this->notifyWarehouse($order);
    }
}

// After: Event-driven
class OrderService
{
    public function complete(Order $order): void
    {
        $order->complete();
        $this->eventDispatcher->dispatch(new OrderCompletedEvent($order));
    }
}

// Separate listeners handle each concern
class UpdateInventoryListener {}
class SendConfirmationEmailListener {}
class CreateInvoiceListener {}
```

## Severity Classification

| Lines | Severity |
|-------|----------|
| 201-300 | 🟡 Minor |
| 301-500 | 🟠 Major |
| 501+ | 🔴 Critical |

## Output Format

```markdown
### Class Length: [ClassName] is too large

**Severity:** 🟠/🔴
**Location:** `file.php`
**Lines:** 450
**Methods:** 35
**Dependencies:** 12

**Issue:**
Class `OrderManager` is 450 lines with 35 methods, indicating multiple responsibilities.

**Responsibilities Detected:**
1. Order CRUD operations
2. Payment processing
3. Shipping management
4. Email notifications
5. Reporting

**Suggested Split:**
```
OrderService (100 lines)
├── OrderRepository
PaymentProcessor (80 lines)
ShippingManager (70 lines)
OrderNotifier (50 lines)
OrderReporter (60 lines)
```
```
