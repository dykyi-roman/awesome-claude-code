---
name: acc-check-nesting-depth
description: Analyzes PHP code for nesting depth issues. Detects deep nesting over 3 levels, complex conditionals, early return opportunities.
---

# Nesting Depth Check

Analyze PHP code for excessive nesting depth and complexity.

## Detection Thresholds

| Depth | Classification |
|-------|----------------|
| 1-2 | ✅ Ideal |
| 3 | ⚠️ Acceptable |
| 4 | 🟡 Deep - refactor recommended |
| 5+ | 🟠 Too deep - must refactor |

## Detection Patterns

### 1. Deep Nesting

```php
// DEPTH 5: Arrow code / pyramid of doom
public function process(Request $request): Response
{
    if ($request->isValid()) {                           // 1
        if ($user = $request->getUser()) {               // 2
            if ($user->hasPermission('edit')) {          // 3
                foreach ($request->getItems() as $item) { // 4
                    if ($item->isActive()) {              // 5
                        $this->handle($item);
                    }
                }
            }
        }
    }
}

// DEPTH 2: Using early returns
public function process(Request $request): Response
{
    if (!$request->isValid()) {
        return $this->badRequest();
    }

    $user = $request->getUser();
    if (!$user) {
        return $this->unauthorized();
    }

    if (!$user->hasPermission('edit')) {
        return $this->forbidden();
    }

    $activeItems = array_filter(
        $request->getItems(),
        fn($item) => $item->isActive()
    );

    foreach ($activeItems as $item) {
        $this->handle($item);
    }
}
```

### 2. Complex Conditionals

```php
// COMPLEX: Multiple nested conditions
if ($order->isPaid()) {
    if ($order->isShipped()) {
        if ($order->isDelivered()) {
            if (!$order->isReturned()) {
                $this->complete($order);
            }
        }
    }
}

// SIMPLIFIED: Combined condition
if ($order->canBeCompleted()) {
    $this->complete($order);
}

// Or with early return
if (!$order->isPaid()) return;
if (!$order->isShipped()) return;
if (!$order->isDelivered()) return;
if ($order->isReturned()) return;

$this->complete($order);
```

### 3. Nested Loops

```php
// DEEP: Triple nested loop
foreach ($categories as $category) {
    foreach ($category->getProducts() as $product) {
        foreach ($product->getVariants() as $variant) {
            foreach ($variant->getOptions() as $option) {
                $this->process($option);
            }
        }
    }
}

// BETTER: Extract methods
foreach ($categories as $category) {
    $this->processCategory($category);
}

private function processCategory(Category $category): void
{
    foreach ($category->getProducts() as $product) {
        $this->processProduct($product);
    }
}

private function processProduct(Product $product): void
{
    foreach ($product->getVariants() as $variant) {
        $this->processVariant($variant);
    }
}
```

### 4. Callback Nesting (Callback Hell)

```php
// DEEP: Nested callbacks
$this->service->fetch($id, function($result) {
    $this->processor->process($result, function($processed) {
        $this->sender->send($processed, function($sent) {
            $this->logger->log($sent, function($logged) {
                $this->cleanup($logged);
            });
        });
    });
});

// FLAT: Sequential or promise-based
$result = $this->service->fetch($id);
$processed = $this->processor->process($result);
$sent = $this->sender->send($processed);
$this->logger->log($sent);
$this->cleanup($sent);
```

### 5. Switch in If in Loop

```php
// DEEP: Mixed control structures
foreach ($items as $item) {
    if ($item->isActive()) {
        switch ($item->getType()) {
            case 'A':
                if ($item->hasFeature()) {
                    $this->handleTypeA($item);
                }
                break;
            case 'B':
                if ($item->isValid()) {
                    $this->handleTypeB($item);
                }
                break;
        }
    }
}

// BETTER: Strategy pattern + filter
$activeItems = array_filter($items, fn($i) => $i->isActive());
foreach ($activeItems as $item) {
    $handler = $this->handlerFactory->create($item->getType());
    $handler->handle($item);
}
```

## Refactoring Techniques

### Early Return / Guard Clauses

```php
// Before
function process($data) {
    if ($data !== null) {
        if ($data->isValid()) {
            if ($data->canProcess()) {
                // actual logic
            }
        }
    }
}

// After
function process($data) {
    if ($data === null) return;
    if (!$data->isValid()) return;
    if (!$data->canProcess()) return;

    // actual logic (no nesting)
}
```

### Extract Method

```php
// Before
foreach ($orders as $order) {
    if ($order->isPaid()) {
        foreach ($order->getItems() as $item) {
            if ($item->needsShipping()) {
                $this->ship($item);
            }
        }
    }
}

// After
foreach ($orders as $order) {
    $this->processOrder($order);
}

private function processOrder(Order $order): void
{
    if (!$order->isPaid()) return;
    $this->shipItems($order->getItems());
}

private function shipItems(array $items): void
{
    foreach ($items as $item) {
        if ($item->needsShipping()) {
            $this->ship($item);
        }
    }
}
```

### Replace Conditional with Polymorphism

```php
// Before: Deep switch
switch ($type) {
    case 'email':
        if ($config['html']) {
            // ...
        } else {
            // ...
        }
        break;
    case 'sms':
        // ...
}

// After: Strategy pattern
interface NotificationChannel {
    public function send(Notification $notification): void;
}

class EmailChannel implements NotificationChannel { }
class SmsChannel implements NotificationChannel { }
```

### Decompose Conditional

```php
// Before
if ($date->before($SUMMER_START) || $date->after($SUMMER_END)) {
    $charge = $quantity * $winterRate + $winterServiceCharge;
} else {
    $charge = $quantity * $summerRate;
}

// After
if ($this->isWinter($date)) {
    $charge = $this->winterCharge($quantity);
} else {
    $charge = $this->summerCharge($quantity);
}
```

## Grep Patterns

```bash
# Find nested if statements
Grep: "if\s*\([^)]+\)\s*\{[^}]*if\s*\(" --glob "**/*.php"

# Find nested foreach
Grep: "foreach.*foreach" --glob "**/*.php"

# Count indentation levels (manual analysis)
```

## Severity Classification

| Depth | Severity |
|-------|----------|
| 4 | 🟡 Minor |
| 5 | 🟠 Major |
| 6+ | 🔴 Critical |

## Output Format

```markdown
### Nesting Depth: [Description]

**Severity:** 🟠/🟡
**Location:** `file.php:line`
**Depth:** 5 levels

**Issue:**
Method `processOrder` has 5 levels of nesting, making it difficult to follow.

**Code Structure:**
```
if ($request->isValid())           // Level 1
  if ($user = getUser())           // Level 2
    if ($user->hasPermission())    // Level 3
      foreach ($items)              // Level 4
        if ($item->isActive())      // Level 5
```

**Suggested Refactoring:**
```php
// Use early returns to flatten
if (!$request->isValid()) return;
if (!$user = getUser()) return;
if (!$user->hasPermission()) return;

$activeItems = $this->filterActiveItems($items);
foreach ($activeItems as $item) {
    $this->handle($item);
}
```
```
