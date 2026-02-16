# Encapsulation Analyzer — Detection Patterns & Examples

## Detection Patterns

### Phase 1: Public Mutable State

```php
// BAD: Public mutable state
class User
{
    public string $email;      // Can be modified externally!
    public int $age;           // No validation!
    public array $permissions; // Collection exposed!
}

// GOOD: Encapsulated state
final class User
{
    private Email $email;
    private Age $age;
    private PermissionCollection $permissions;

    public function changeEmail(Email $newEmail): void { /* ... */ }
    public function grantPermission(Permission $permission): void { /* ... */ }
}
```

### Phase 2: Getter/Setter Abuse

```php
// BAD: Anemic entity
class Order
{
    public function getStatus(): string { return $this->status; }
    public function setStatus(string $status): void { $this->status = $status; }
}

// External code makes decisions
if ($order->getStatus() === 'pending') {
    $order->setStatus('confirmed');
}

// GOOD: Rich entity
final class Order
{
    public function confirm(): void
    {
        if ($this->status !== OrderStatus::PENDING) {
            throw new CannotConfirmOrderException();
        }
        $this->status = OrderStatus::CONFIRMED;
        $this->recordEvent(new OrderConfirmedEvent($this->id));
    }
}
```

### Phase 3: Tell Don't Ask Violations

```php
// BAD: Ask then act
if ($user->getBalance()->getAmount() >= $payment->getAmount()) {
    $user->setBalance(
        $user->getBalance()->subtract($payment->getAmount())
    );
}

// GOOD: Tell
$user->pay($payment);

// Inside User
public function pay(Payment $payment): void
{
    if (!$this->balance->canAfford($payment->amount())) {
        throw new InsufficientBalanceException();
    }
    $this->balance = $this->balance->subtract($payment->amount());
    $this->recordEvent(new PaymentMadeEvent($this->id, $payment->id()));
}
```

### Phase 4: Collection Exposure

```php
// BAD: Collection exposed
class Order
{
    /** @return OrderItem[] */
    public function getItems(): array
    {
        return $this->items; // Internal array exposed!
    }
}

// External modification
$order->getItems()[] = $newItem; // Bypasses validation!

// GOOD: Collection encapsulated
final class Order
{
    public function addItem(Product $product, Quantity $quantity): void
    {
        $this->validateCanAddItem($product);
        $this->items[] = new OrderItem($product, $quantity);
        $this->recalculateTotal();
    }

    /** @return OrderItem[] */
    public function items(): array
    {
        return [...$this->items]; // Return copy
    }
}
```

### Phase 5: Exposed Internals

Grep patterns for detection:

```bash
# Internal state returned
Grep: "return \$this->[a-z]+;" --glob "**/Domain/**/*.php"
# Check if returning mutable objects

# Private field via reflection
Grep: "ReflectionClass|ReflectionProperty|setAccessible" --glob "**/*.php"

# Debug/dump methods exposing state
Grep: "public function toArray\(\)|public function dump\(\)|public function debug\(\)" --glob "**/Domain/**/*.php"

# Serialization exposing internals
Grep: "__serialize|__sleep|jsonSerialize" --glob "**/Domain/**/*.php"
```

### Phase 6: Constructor Injection Issues

Grep patterns for detection:

```bash
# Too many dependencies (SRP violation indicator)
Grep: "__construct\(" --glob "**/Domain/**/*.php" -A 15
# Count parameters

# Public constructor with complex setup
Grep: "public function __construct" --glob "**/Domain/**/*.php" -A 20
# Check for business logic in constructor

# Missing factory for complex construction
Grep: "new [A-Z][a-z]+Entity\(|new [A-Z][a-z]+Aggregate\(" --glob "**/Application/**/*.php"
# Complex instantiation outside factory
```

## Report Format Examples

### Critical Issues

#### ENC-001: Public Mutable Properties
- **File:** `src/Domain/User/Entity/User.php:12`
- **Issue:** Public properties allow external modification
- **Code:**
  ```php
  public string $email;
  public string $name;
  public array $roles;
  ```
- **Expected:**
  ```php
  private Email $email;
  private Name $name;
  private RoleCollection $roles;

  public function changeEmail(Email $email): void { /* validate */ }
  ```
- **Skills:** `acc-create-entity`, `acc-create-value-object`

#### ENC-002: Anemic Entity
- **File:** `src/Domain/Order/Entity/Order.php`
- **Issue:** 15 getters, 12 setters, 0 behavior methods
- **Code:**
  ```php
  public function getStatus(): string { ... }
  public function setStatus(string $status): void { ... }
  ```
- **Expected:** Replace setters with behavior methods
  ```php
  public function confirm(): void { /* validate and transition */ }
  public function ship(TrackingNumber $tracking): void { /* ... */ }
  public function cancel(CancellationReason $reason): void { /* ... */ }
  ```
- **Skills:** `acc-create-entity`

#### ENC-003: Collection Mutated Externally
- **File:** `src/Application/Service/OrderService.php:45`
- **Issue:** Adding items bypasses entity validation
- **Code:**
  ```php
  $order->getItems()[] = $newItem;
  ```
- **Expected:**
  ```php
  $order->addItem($product, $quantity);
  ```

### Warning Issues

#### ENC-004: Tell Don't Ask Violation
- **File:** `src/Application/Handler/ConfirmOrderHandler.php:34`
- **Issue:** External logic should be in entity
- **Code:**
  ```php
  if ($order->getStatus() === 'pending' &&
      $order->getPayment()->getStatus() === 'completed') {
      $order->setStatus('confirmed');
  }
  ```
- **Expected:**
  ```php
  $order->confirm(); // Validation inside entity
  ```

#### ENC-005: Getter Chain
- **File:** `src/Application/Service/ReportService.php:78`
- **Issue:** Law of Demeter violation
- **Code:**
  ```php
  $country = $user->getAddress()->getCity()->getCountry()->getName();
  ```
- **Refactoring Options:**
  1. Add shortcut: `$user->countryName()`
  2. Pass needed data: `new Report($user->address()->countryName())`

#### ENC-006: Internal Array Returned
- **File:** `src/Domain/Order/Entity/Order.php:89`
- **Issue:** Internal array returned by reference
- **Code:**
  ```php
  public function getItems(): array
  {
      return $this->items;
  }
  ```
- **Expected:**
  ```php
  /** @return OrderItem[] */
  public function items(): array
  {
      return [...$this->items]; // Return copy
  }
  ```

## Metrics Examples

### Getter/Behavior Ratio

| Entity | Getters | Setters | Behavior | Ratio | Status |
|--------|---------|---------|----------|-------|--------|
| User | 8 | 5 | 3 | 4.3 | Poor |
| Order | 15 | 12 | 2 | 13.5 | Anemic |
| Product | 6 | 0 | 5 | 1.2 | Good |
| Payment | 4 | 2 | 4 | 1.5 | Good |

**Target:** Ratio < 2.0 (behaviors should outnumber getters)

### Public State Exposure

| Layer | Public Props | Readonly Props | Private Props |
|-------|--------------|----------------|---------------|
| Domain | 12 | 8 | 45 |
| Application | 0 | 23 | 15 |

## Rich Entity Example

```php
final class Order
{
    private OrderId $id;
    private CustomerId $customerId;
    private OrderStatus $status;
    private OrderItemCollection $items;
    private Money $total;
    private array $events = [];

    public static function create(CustomerId $customerId): self
    {
        $order = new self();
        $order->id = OrderId::generate();
        $order->customerId = $customerId;
        $order->status = OrderStatus::DRAFT;
        $order->items = new OrderItemCollection();
        $order->total = Money::zero();

        $order->recordEvent(new OrderCreatedEvent($order->id));

        return $order;
    }

    public function addItem(Product $product, Quantity $quantity): void
    {
        $this->assertDraft();

        $item = OrderItem::create($product, $quantity);
        $this->items = $this->items->add($item);
        $this->recalculateTotal();
    }

    public function submit(): void
    {
        $this->assertDraft();
        $this->assertHasItems();

        $this->status = OrderStatus::SUBMITTED;
        $this->recordEvent(new OrderSubmittedEvent($this->id));
    }

    // Query methods (no state exposure)
    public function id(): OrderId { return $this->id; }
    public function total(): Money { return $this->total; }
    public function isSubmitted(): bool { return $this->status->equals(OrderStatus::SUBMITTED); }

    private function assertDraft(): void
    {
        if (!$this->status->equals(OrderStatus::DRAFT)) {
            throw new OrderNotDraftException($this->id);
        }
    }
}
```

## Quick Analysis Commands

```bash
# Check encapsulation
echo "=== Public Properties ===" && \
grep -rn "public string\|public int\|public array" --include="*.php" src/Domain/ | grep -v "readonly" && \
echo "=== Setter Methods ===" && \
grep -rn "public function set[A-Z]" --include="*.php" src/Domain/ && \
echo "=== Getter Chains ===" && \
grep -rn "->get[A-Z].*->get[A-Z].*->get[A-Z]" --include="*.php" src/ && \
echo "=== Tell Don't Ask ===" && \
grep -rn "if (\$.*->get[A-Z].*===\|switch (\$.*->get[A-Z]" --include="*.php" src/Application/
```
