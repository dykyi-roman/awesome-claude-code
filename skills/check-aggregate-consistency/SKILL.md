---
name: acc-check-aggregate-consistency
description: Audits DDD aggregate design rules. Checks single transaction boundary, identity by root, invariant enforcement, small aggregates, and consistency boundaries.
---

# Aggregate Consistency Audit

Analyze PHP code for DDD aggregate design compliance — ensuring proper boundaries, invariant enforcement, and transactional consistency.

## Detection Patterns

### 1. Cross-Aggregate Transaction

```php
// CRITICAL: Multiple aggregates modified in single transaction
class TransferUseCase
{
    public function execute(TransferCommand $command): void
    {
        $this->entityManager->beginTransaction();
        try {
            $source = $this->accountRepo->find($command->sourceId());
            $target = $this->accountRepo->find($command->targetId());

            $source->debit($command->amount());  // Aggregate 1
            $target->credit($command->amount()); // Aggregate 2 — violation!

            $this->accountRepo->save($source);
            $this->accountRepo->save($target);
            $this->entityManager->commit();
        } catch (\Throwable $e) {
            $this->entityManager->rollback();
            throw $e;
        }
    }
}

// CORRECT: One aggregate per transaction + eventual consistency
class DebitAccountUseCase
{
    public function execute(DebitCommand $command): void
    {
        $account = $this->accountRepo->find($command->accountId());
        $account->debit($command->amount());
        $this->accountRepo->save($account);
        // Domain event triggers CreditAccountUseCase asynchronously
    }
}
```

### 2. Missing Aggregate Root Identity

```php
// ANTIPATTERN: Child entity accessed directly (bypassing root)
class OrderItemRepository
{
    public function findById(OrderItemId $id): OrderItem
    {
        // Direct access to child entity — violates aggregate boundary!
        return $this->entityManager->find(OrderItem::class, $id);
    }
}

// CORRECT: Access child through aggregate root
class OrderRepository
{
    public function findById(OrderId $id): Order
    {
        return $this->entityManager->find(Order::class, $id);
    }
}

// Then: $order->getItem($itemId);
```

### 3. Invariant Not Enforced by Root

```php
// ANTIPATTERN: Business rule checked outside aggregate
class AddItemToOrderUseCase
{
    public function execute(AddItemCommand $command): void
    {
        $order = $this->orderRepo->find($command->orderId());
        $item = new OrderItem($command->productId(), $command->quantity());

        // Business rule in UseCase instead of Aggregate!
        if (count($order->items()) >= 50) {
            throw new TooManyItemsException();
        }

        $order->items()->add($item); // Direct collection manipulation
        $this->orderRepo->save($order);
    }
}

// CORRECT: Aggregate root enforces invariants
final class Order
{
    private const int MAX_ITEMS = 50;

    public function addItem(ProductId $productId, Quantity $quantity): void
    {
        if (count($this->items) >= self::MAX_ITEMS) {
            throw new TooManyItemsException(self::MAX_ITEMS);
        }

        if ($this->hasProduct($productId)) {
            throw new DuplicateProductException($productId);
        }

        $this->items[] = new OrderItem($this->id, $productId, $quantity);
        $this->recordEvent(new ItemAddedToOrder($this->id, $productId));
    }
}
```

### 4. Large Aggregate (God Aggregate)

```php
// ANTIPATTERN: Aggregate with too many children
final class User
{
    private Collection $orders;          // Large collection
    private Collection $notifications;   // Large collection
    private Collection $activityLog;     // Unbounded collection
    private Collection $preferences;
    private Collection $addresses;
    private Collection $paymentMethods;
    // Loading this aggregate loads ALL related data!
}

// CORRECT: Separate into smaller aggregates
final class User         { /* core identity, profile */ }
final class UserOrders   { /* reference User by ID, not object */ }
final class UserActivity { /* separate aggregate */ }
```

### 5. Public Setters on Aggregate

```php
// ANTIPATTERN: Public setters bypass invariants
final class Order
{
    public function setStatus(OrderStatus $status): void
    {
        $this->status = $status; // No validation! Can go from SHIPPED → DRAFT
    }

    public function setTotal(Money $total): void
    {
        $this->total = $total; // External code can set wrong total
    }
}

// CORRECT: Named methods enforcing state transitions
final class Order
{
    public function confirm(): void
    {
        if ($this->status !== OrderStatus::DRAFT) {
            throw new InvalidOrderTransitionException($this->status, OrderStatus::CONFIRMED);
        }
        if ($this->items->isEmpty()) {
            throw new EmptyOrderException();
        }
        $this->status = OrderStatus::CONFIRMED;
        $this->confirmedAt = new \DateTimeImmutable();
        $this->recordEvent(new OrderConfirmed($this->id));
    }
}
```

### 6. Reference by Object Instead of ID

```php
// ANTIPATTERN: Direct object reference between aggregates
final class Order
{
    private User $user;           // Object reference → tight coupling
    private Product $product;     // Object reference → loads entire aggregate
}

// CORRECT: Reference by identity
final class Order
{
    private UserId $userId;       // ID reference → loose coupling
    private ProductId $productId; // ID reference → load only when needed
}
```

## Grep Patterns

```bash
# Cross-aggregate transaction
Grep: "beginTransaction|->flush\(\)" --glob "**/UseCase/**/*.php"
Grep: "->save\(.*\n.*->save\(" --glob "**/UseCase/**/*.php"

# Direct child entity repository
Grep: "interface.*Item.*Repository|interface.*Line.*Repository" --glob "**/Domain/**/*.php"

# Public setters on aggregates
Grep: "public function set[A-Z]" --glob "**/Domain/**/*Entity*.php"
Grep: "public function set[A-Z]" --glob "**/Domain/**/*Aggregate*.php"

# Large collections in entity
Grep: "private.*Collection.*\$|OneToMany|ManyToMany" --glob "**/Domain/**/*.php"

# Object reference between aggregates
Grep: "private.*[A-Z][a-z]+Entity \$|private.*[A-Z][a-z]+Aggregate \$" --glob "**/Domain/**/*.php"

# Invariants outside aggregate
Grep: "count\(.*->items\(\)\)|->getTotal\(\).*>|->getStatus\(\).*===" --glob "**/UseCase/**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Cross-aggregate transaction | 🔴 Critical |
| Direct child entity access | 🔴 Critical |
| Invariant outside aggregate | 🟠 Major |
| Public setters on aggregate | 🟠 Major |
| Large aggregate (god object) | 🟠 Major |
| Object reference between aggregates | 🟡 Minor |

## Output Format

```markdown
### Aggregate Consistency: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Aggregate:** [Aggregate Root name]

**DDD Rule Violated:**
[Which aggregate design rule is broken]

**Issue:**
[Description of the consistency violation]

**Code:**
```php
// Violating code
```

**Fix:**
```php
// Compliant with aggregate rules
```
```
