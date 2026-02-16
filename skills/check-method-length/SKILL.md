---
name: acc-check-method-length
description: Analyzes PHP code for method length issues. Detects methods exceeding 30 lines, single responsibility violations, extract method opportunities.
---

# Method Length Check

Analyze PHP code for method length and complexity issues.

## Detection Thresholds

| Lines | Classification |
|-------|----------------|
| 1-15 | ✅ Ideal |
| 16-30 | ⚠️ Acceptable |
| 31-50 | 🟡 Long - consider splitting |
| 51+ | 🟠 Too long - must split |

## Detection Patterns

### 1. Methods Over 30 Lines

```php
// TOO LONG: 50+ lines doing multiple things
public function processOrder(Order $order): void
{
    // Validate order (10 lines)
    if ($order->getItems()->isEmpty()) {
        throw new InvalidOrderException('Empty order');
    }
    // ... more validation

    // Calculate totals (15 lines)
    $subtotal = 0;
    foreach ($order->getItems() as $item) {
        $subtotal += $item->getPrice() * $item->getQuantity();
    }
    // ... more calculations

    // Apply discounts (10 lines)
    $discount = $this->calculateDiscount($order);
    // ... discount logic

    // Process payment (10 lines)
    $payment = $this->paymentGateway->charge($total);
    // ... payment logic

    // Send notifications (10 lines)
    $this->mailer->send($order->getCustomer(), 'order_confirmation');
    // ... notification logic
}

// GOOD: Split into focused methods
public function processOrder(Order $order): void
{
    $this->validateOrder($order);
    $totals = $this->calculateTotals($order);
    $this->processPayment($order, $totals);
    $this->sendNotifications($order);
}

private function validateOrder(Order $order): void
{
    // 10 lines of validation
}

private function calculateTotals(Order $order): OrderTotals
{
    // 15 lines of calculation
}
```

### 2. Single Responsibility Violations

```php
// BAD: Method does too many things
public function createUser(array $data): User
{
    // 1. Validate input
    // 2. Hash password
    // 3. Create user entity
    // 4. Save to database
    // 5. Send welcome email
    // 6. Create activity log
    // 7. Update statistics
}

// GOOD: Each method has one responsibility
public function createUser(array $data): User
{
    $validatedData = $this->validateUserData($data);
    $user = $this->buildUserEntity($validatedData);
    $this->userRepository->save($user);

    $this->eventDispatcher->dispatch(new UserCreatedEvent($user));

    return $user;
}
```

### 3. Extract Method Opportunities

```php
// BEFORE: Long conditional blocks
public function calculatePrice(Product $product, User $user): Money
{
    $basePrice = $product->getPrice();

    // Complex discount calculation (15 lines)
    $discount = 0;
    if ($user->isPremium()) {
        $discount += 10;
    }
    if ($user->getOrderCount() > 10) {
        $discount += 5;
    }
    if ($product->isOnSale()) {
        $discount += $product->getSaleDiscount();
    }
    if ($this->isHolidaySeason()) {
        $discount += 15;
    }
    $discount = min($discount, 50);
    // ...

    // Tax calculation (10 lines)
    $taxRate = $this->getTaxRate($user->getCountry());
    // ...

    return $finalPrice;
}

// AFTER: Extracted methods
public function calculatePrice(Product $product, User $user): Money
{
    $basePrice = $product->getPrice();
    $discount = $this->calculateDiscount($product, $user);
    $priceAfterDiscount = $basePrice->subtract($discount);
    $tax = $this->calculateTax($priceAfterDiscount, $user);

    return $priceAfterDiscount->add($tax);
}

private function calculateDiscount(Product $product, User $user): Money
{
    // Focused discount logic
}

private function calculateTax(Money $price, User $user): Money
{
    // Focused tax logic
}
```

### 4. Long Parameter Lists

```php
// BAD: Too many parameters (indicates method does too much)
public function createReport(
    string $title,
    DateTime $startDate,
    DateTime $endDate,
    array $filters,
    string $format,
    bool $includeCharts,
    bool $includeComments,
    string $outputPath
): Report {}

// GOOD: Parameter object
public function createReport(ReportRequest $request): Report
{
    // Method focuses on orchestration
}

final readonly class ReportRequest
{
    public function __construct(
        public string $title,
        public DateRange $dateRange,
        public array $filters,
        public ReportFormat $format,
        public ReportOptions $options,
    ) {}
}
```

## Counting Rules

- Count logical lines, not physical lines
- Exclude blank lines and comments from count
- Include all lines in method body (opening/closing braces not counted)
- One statement per line

## Refactoring Techniques

### Extract Method

```php
// Before
$validated = [];
foreach ($items as $item) {
    if ($item->isValid() && $item->isInStock()) {
        $validated[] = $item;
    }
}

// After
$validated = $this->filterValidItems($items);

private function filterValidItems(array $items): array
{
    return array_filter($items, fn($item) => $item->isValid() && $item->isInStock());
}
```

### Introduce Parameter Object

```php
// Before
function search($query, $page, $limit, $sort, $order, $filters) {}

// After
function search(SearchCriteria $criteria) {}
```

### Replace Method with Method Object

```php
// Before: Complex method with many local variables
public function calculate(): int
{
    $a = ...;
    $b = ...;
    $c = ...;
    // 50 lines using a, b, c
}

// After: Separate class
class PriceCalculator
{
    private int $a;
    private int $b;
    private int $c;

    public function calculate(): int
    {
        $this->initializeValues();
        return $this->computeResult();
    }
}
```

## Grep Patterns

```bash
# Find method signatures
Grep: "function\s+\w+\s*\(" --glob "**/*.php"

# Count lines between method start and end (manual analysis needed)
```

## Severity Classification

| Lines | Severity |
|-------|----------|
| 31-50 | 🟡 Minor |
| 51-80 | 🟠 Major |
| 81+ | 🔴 Critical |

## Output Format

```markdown
### Method Length: [MethodName] is too long

**Severity:** 🟠/🟡
**Location:** `file.php:line`
**Lines:** 65

**Issue:**
Method `processOrder` is 65 lines long (recommended: ≤30).

**Responsibilities Found:**
1. Order validation (lines 5-20)
2. Price calculation (lines 22-45)
3. Payment processing (lines 47-60)
4. Notification sending (lines 62-70)

**Suggested Refactoring:**
```php
public function processOrder(Order $order): void
{
    $this->validateOrder($order);
    $totals = $this->calculateTotals($order);
    $this->processPayment($order, $totals);
    $this->sendNotifications($order);
}
```
```

## When This Is Acceptable

- **CLI commands/migrations** — Long methods in console commands or database migrations are often unavoidable due to sequential operations
- **Test setup methods** — `setUp()` methods with extensive fixture creation may legitimately be long
- **Configuration methods** — Methods that configure framework services/routes often need many lines

### False Positive Indicators
- Method is in a `Command` or `Migration` class
- Method name starts with `setUp` or `configure`
- Method body is mostly configuration/declaration, not logic
