---
name: acc-suggest-simplification
description: Suggests code simplification opportunities. Identifies extract method candidates, complex expressions, redundant code, refactoring opportunities.
---

# Code Simplification Suggestions

Analyze PHP code for simplification and refactoring opportunities.

## Simplification Patterns

### 1. Extract Method

```php
// BEFORE: Long inline code block
public function processOrder(Order $order): void
{
    // Validate order (5 lines)
    if ($order->getItems()->isEmpty()) {
        throw new EmptyOrderException();
    }
    if ($order->getTotal()->isNegative()) {
        throw new InvalidTotalException();
    }

    // Process payment (10 lines)
    $payment = $this->paymentGateway->charge(
        $order->getTotal(),
        $order->getPaymentMethod()
    );
    if (!$payment->isSuccessful()) {
        throw new PaymentFailedException();
    }

    // Send notifications (5 lines)
    $this->mailer->send($order->getCustomer()->getEmail(), 'order_confirmed');
}

// AFTER: Extracted methods
public function processOrder(Order $order): void
{
    $this->validateOrder($order);
    $this->processPayment($order);
    $this->sendConfirmation($order);
}

private function validateOrder(Order $order): void {}
private function processPayment(Order $order): Payment {}
private function sendConfirmation(Order $order): void {}
```

### 2. Introduce Explaining Variable

```php
// BEFORE: Complex expression
if ($user->getSubscription()?->isActive()
    && $user->getCreatedAt() < new DateTime('-30 days')
    && !$user->hasUsedTrial()
    && $user->getOrderCount() > 0) {
    $this->offerUpgrade($user);
}

// AFTER: Named variables
$hasActiveSubscription = $user->getSubscription()?->isActive();
$isEstablishedUser = $user->getCreatedAt() < new DateTime('-30 days');
$eligibleForUpgrade = !$user->hasUsedTrial() && $user->getOrderCount() > 0;

if ($hasActiveSubscription && $isEstablishedUser && $eligibleForUpgrade) {
    $this->offerUpgrade($user);
}

// EVEN BETTER: Extract to method
if ($user->isEligibleForUpgrade()) {
    $this->offerUpgrade($user);
}
```

### 3. Remove Redundant Code

```php
// BEFORE: Redundant checks
if ($value !== null) {
    if ($value !== null) {  // Duplicate check
        $this->process($value);
    }
}

// BEFORE: Unnecessary else
if ($condition) {
    return $a;
} else {
    return $b;
}

// AFTER: Simplified
if ($condition) {
    return $a;
}
return $b;

// BEFORE: Redundant boolean
if ($condition === true) {}
return $value === true;

// AFTER: Simplified
if ($condition) {}
return $value;
```

### 4. Simplify Conditionals

```php
// BEFORE: Nested conditionals
if ($user !== null) {
    if ($user->isActive()) {
        if ($user->hasPermission('edit')) {
            return true;
        }
    }
}
return false;

// AFTER: Combined condition
return $user !== null
    && $user->isActive()
    && $user->hasPermission('edit');

// BEFORE: Negative condition
if (!$items->isEmpty()) {
    $this->process($items);
}

// AFTER: Positive condition
if ($items->isNotEmpty()) {
    $this->process($items);
}
```

### 5. Replace Temp with Query

```php
// BEFORE: Temporary variable used once
$basePrice = $order->getBasePrice();
$discount = $basePrice * 0.1;
return $basePrice - $discount;

// AFTER: Inline or method
return $order->getBasePrice() * 0.9;

// Or if complex:
return $order->getBasePrice() - $this->calculateDiscount($order);
```

### 6. Use Collection Methods

```php
// BEFORE: Manual loop
$active = [];
foreach ($users as $user) {
    if ($user->isActive()) {
        $active[] = $user;
    }
}

// AFTER: array_filter
$active = array_filter($users, fn($user) => $user->isActive());

// BEFORE: Manual map
$emails = [];
foreach ($users as $user) {
    $emails[] = $user->getEmail();
}

// AFTER: array_map
$emails = array_map(fn($user) => $user->getEmail(), $users);

// BEFORE: Manual find
$found = null;
foreach ($items as $item) {
    if ($item->getId() === $id) {
        $found = $item;
        break;
    }
}

// AFTER: Collection method
$found = $collection->first(fn($item) => $item->getId() === $id);
```

### 7. Replace Switch with Polymorphism

```php
// BEFORE: Switch on type
public function calculateShipping(Order $order): Money
{
    switch ($order->getShippingMethod()) {
        case 'standard':
            return $this->calculateStandardShipping($order);
        case 'express':
            return $this->calculateExpressShipping($order);
        case 'overnight':
            return $this->calculateOvernightShipping($order);
        default:
            throw new InvalidMethodException();
    }
}

// AFTER: Strategy pattern
interface ShippingCalculator {
    public function calculate(Order $order): Money;
}

class StandardShipping implements ShippingCalculator {}
class ExpressShipping implements ShippingCalculator {}

public function calculateShipping(Order $order): Money
{
    return $this->shippingCalculators
        ->get($order->getShippingMethod())
        ->calculate($order);
}
```

### 8. Null Object Pattern

```php
// BEFORE: Null checks everywhere
if ($user->getAddress() !== null) {
    echo $user->getAddress()->getCity();
} else {
    echo 'Unknown';
}

// AFTER: Null Object
class NullAddress implements AddressInterface
{
    public function getCity(): string
    {
        return 'Unknown';
    }
}

// Always safe to call
echo $user->getAddress()->getCity();
```

### 9. Guard Clauses

```php
// BEFORE: Deeply nested
public function process(Request $request): Response
{
    if ($request !== null) {
        if ($request->isValid()) {
            if ($this->canProcess($request)) {
                return $this->doProcess($request);
            } else {
                return $this->error('Cannot process');
            }
        } else {
            return $this->error('Invalid request');
        }
    } else {
        return $this->error('No request');
    }
}

// AFTER: Guard clauses
public function process(Request $request): Response
{
    if ($request === null) {
        return $this->error('No request');
    }

    if (!$request->isValid()) {
        return $this->error('Invalid request');
    }

    if (!$this->canProcess($request)) {
        return $this->error('Cannot process');
    }

    return $this->doProcess($request);
}
```

### 10. Use Modern PHP Features

```php
// BEFORE: Old syntax
$name = isset($data['name']) ? $data['name'] : 'default';

// AFTER: Null coalescing
$name = $data['name'] ?? 'default';

// BEFORE: Property assignment
$value = $object->getValue();
if ($value !== null) {
    echo $value;
}

// AFTER: Nullsafe operator
echo $object?->getValue();

// BEFORE: Match as if/else
if ($status === 'active') {
    $color = 'green';
} elseif ($status === 'pending') {
    $color = 'yellow';
} else {
    $color = 'red';
}

// AFTER: Match expression
$color = match($status) {
    'active' => 'green',
    'pending' => 'yellow',
    default => 'red',
};
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Deeply nested code | 🟠 Major |
| Repeated code blocks | 🟠 Major |
| Complex boolean expressions | 🟡 Minor |
| Old syntax available in modern PHP | 🟢 Suggestion |
| Verbose but clear code | 🟢 Suggestion |

## Output Format

```markdown
### Simplification: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`
**Type:** [Extract Method|Guard Clause|Collection Method|...]

**Issue:**
[Description of the complexity]

**Current:**
```php
// Complex code
```

**Suggested:**
```php
// Simplified code
```

**Benefits:**
- Improved readability
- Reduced cognitive load
- Easier testing
- Better reusability
```
