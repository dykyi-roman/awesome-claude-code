# DDD Antipatterns

Common DDD violations with detection patterns and fixes.

## Critical Violations

### 1. Domain → Infrastructure Dependency

**Description:** Domain layer imports Infrastructure classes.

**Why Critical:** Breaks the fundamental DDD rule. Domain becomes coupled to technical implementation.

**Detection:**
```bash
Grep: "use.*Infrastructure" --glob "**/Domain/**/*.php"
Grep: "use.*Persistence|use.*Repository\\\\Doctrine" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Infrastructure\Persistence\DoctrineOrderRepository;  // CRITICAL VIOLATION

class Order
{
    public function __construct(
        private DoctrineOrderRepository $repository  // Domain depends on Infra
    ) {}
}
```

**Good:**
```php
namespace Domain\Order\Entity;

// No infrastructure imports - domain is pure

class Order
{
    // Entity doesn't know about persistence
}

// Repository INTERFACE in Domain
namespace Domain\Order\Repository;

interface OrderRepositoryInterface
{
    public function save(Order $order): void;
}
```

### 2. Framework in Domain

**Description:** Domain uses framework-specific classes or annotations.

**Why Critical:** Couples domain to framework, making it untestable and non-portable.

**Detection:**
```bash
Grep: "use Doctrine\\\\|use Illuminate\\\\|use Symfony\\\\" --glob "**/Domain/**/*.php"
Grep: "@ORM\\\\|@Entity|@Column|@Id" --glob "**/Domain/**/*.php"
Grep: "extends Model|extends Eloquent" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'orders')]
class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;
}
```

**Good:**
```php
namespace Domain\Order\Entity;

// Plain PHP class - no framework dependencies
final class Order
{
    public function __construct(
        private readonly OrderId $id
    ) {}
}

// ORM mapping in Infrastructure (XML/YAML/PHP config)
```

### 3. Business Logic in Repository

**Description:** Repository implementations contain business logic.

**Why Critical:** Business rules scattered across layers, hard to test and maintain.

**Detection:**
```bash
Grep: "if \(.*->|switch|foreach.*calculate|validate|check" --glob "**/Infrastructure/**/*Repository*.php"
Grep: "private function (calculate|validate|check|process)" --glob "**/Infrastructure/**/*.php"
```

**Bad:**
```php
namespace Infrastructure\Persistence;

class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function save(Order $order): void
    {
        // VIOLATION: Business logic in repository
        if ($order->getTotal() > 10000) {
            $order->setRequiresApproval(true);
        }

        // VIOLATION: Validation in repository
        if (!$this->validateOrderLines($order)) {
            throw new InvalidOrderException();
        }

        $this->entityManager->persist($order);
    }
}
```

**Good:**
```php
namespace Infrastructure\Persistence;

class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function save(Order $order): void
    {
        // Only persistence, no logic
        $this->entityManager->persist($order);
        $this->entityManager->flush();
    }
}

// Business logic in Domain
namespace Domain\Order\Entity;

class Order
{
    public function requiresApproval(): bool
    {
        return $this->total()->isGreaterThan(Money::fromInt(10000, 'USD'));
    }
}
```

## Warnings

### 4. Anemic Domain Model

**Description:** Entities with only getters/setters, no behavior.

**Why Bad:** Business logic ends up in services, violating encapsulation.

**Detection:**
```bash
# Count methods - if mostly get/set, it's anemic
Grep: "public function (get|set|is|has)[A-Z]" --glob "**/Domain/**/Entity/**/*.php"

# Check for behavior methods
Grep: "public function [a-z][a-z]+" --glob "**/Domain/**/Entity/**/*.php" | grep -v "get\|set\|is\|has\|__"
```

**Anemic (Bad):**
```php
class Order
{
    private string $status;
    private array $lines;

    public function getStatus(): string { return $this->status; }
    public function setStatus(string $status): void { $this->status = $status; }
    public function getLines(): array { return $this->lines; }
    public function setLines(array $lines): void { $this->lines = $lines; }
}

// Logic in service
class OrderService
{
    public function confirm(Order $order): void
    {
        if ($order->getStatus() === 'draft' && count($order->getLines()) > 0) {
            $order->setStatus('confirmed');
        }
    }
}
```

**Rich (Good):**
```php
class Order
{
    private OrderStatus $status;
    private array $lines = [];

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidStateTransitionException();
        }
        if (empty($this->lines)) {
            throw new EmptyOrderException();
        }
        $this->status = OrderStatus::Confirmed;
    }

    public function addLine(OrderLine $line): void
    {
        $this->lines[] = $line;
    }
}
```

### 5. Primitive Obsession

**Description:** Using primitive types instead of Value Objects for domain concepts.

**Why Bad:** Validation scattered, no behavior, meaning lost.

**Detection:**
```bash
Grep: "string \$email|string \$phone|string \$currency|int \$amount|string \$status" --glob "**/Domain/**/*.php"
Grep: "function.*string \$id\)" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
class Customer
{
    public function __construct(
        private string $id,        // Should be CustomerId
        private string $email,     // Should be Email
        private string $phone,     // Should be Phone
        private int $balance,      // Should be Money
        private string $currency   // Part of Money
    ) {}
}
```

**Good:**
```php
class Customer
{
    public function __construct(
        private readonly CustomerId $id,
        private Email $email,
        private Phone $phone,
        private Money $balance
    ) {}
}
```

### 6. Magic Strings

**Description:** Using string literals for domain values.

**Why Bad:** No type safety, typos cause bugs, meaning unclear.

**Detection:**
```bash
Grep: "=== ['\"]pending['\"]|=== ['\"]active['\"]|=== ['\"]draft['\"]" --glob "**/Domain/**/*.php"
Grep: "== ['\"][a-z]+['\"]" --glob "**/*.php"
```

**Bad:**
```php
class Order
{
    private string $status = 'draft';

    public function confirm(): void
    {
        if ($this->status === 'draft') {  // Magic string
            $this->status = 'confirmed';   // Magic string
        }
    }

    public function canBeCancelled(): bool
    {
        return $this->status !== 'shipped';  // Magic string
    }
}
```

**Good:**
```php
enum OrderStatus: string
{
    case Draft = 'draft';
    case Confirmed = 'confirmed';
    case Shipped = 'shipped';
    case Cancelled = 'cancelled';

    public function canTransitionTo(self $target): bool
    {
        return match($this) {
            self::Draft => in_array($target, [self::Confirmed, self::Cancelled]),
            self::Confirmed => in_array($target, [self::Shipped, self::Cancelled]),
            default => false,
        };
    }
}

class Order
{
    private OrderStatus $status = OrderStatus::Draft;

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidStateTransitionException();
        }
        $this->status = OrderStatus::Confirmed;
    }
}
```

### 7. Public Setters

**Description:** Public setter methods that allow direct state modification.

**Why Bad:** Bypasses business rules, breaks encapsulation.

**Detection:**
```bash
Grep: "public function set[A-Z]" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
class Order
{
    public function setStatus(OrderStatus $status): void
    {
        $this->status = $status;  // No validation!
    }
}

// Anywhere in code
$order->setStatus(OrderStatus::Shipped);  // Bypasses rules
```

**Good:**
```php
class Order
{
    public function ship(TrackingNumber $tracking): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Shipped)) {
            throw new CannotShipOrderException();
        }
        if (!$this->isPaid()) {
            throw new UnpaidOrderCannotBeShippedException();
        }
        $this->status = OrderStatus::Shipped;
        $this->trackingNumber = $tracking;
    }
}
```

### 8. God Object

**Description:** Class with too many responsibilities.

**Why Bad:** Hard to understand, test, and maintain.

**Detection:**
```bash
# Check file line count
find . -name "*.php" -path "*/Domain/*" -exec wc -l {} \; | awk '$1 > 500 {print}'

# Check method count
Grep: "public function" --glob "**/Domain/**/*.php" -c
```

**Signs:**
- More than 500 lines
- More than 20 public methods
- "And" in class name (OrderAndPaymentProcessor)
- Injecting many dependencies (> 5)

### 9. Business Logic in Controller

**Description:** Controllers contain business decisions.

**Why Bad:** Logic not reusable, hard to test.

**Detection:**
```bash
Grep: "if \(.*->can|if \(.*->is[A-Z]|if \(.*->has[A-Z]" --glob "**/Controller/**/*.php" --glob "**/Action/**/*.php"
Grep: "foreach|while|switch" --glob "**/Presentation/**/*.php"
```

**Bad:**
```php
class OrderController
{
    public function confirm(Request $request): Response
    {
        $order = $this->repository->find($request->get('id'));

        // VIOLATION: Business logic in controller
        if ($order->getStatus() === 'draft') {
            if (count($order->getLines()) > 0) {
                if ($order->getCustomer()->canPlaceOrders()) {
                    $order->setStatus('confirmed');
                }
            }
        }

        return new JsonResponse(['status' => 'ok']);
    }
}
```

**Good:**
```php
class OrderController
{
    public function confirm(Request $request): Response
    {
        $command = new ConfirmOrderCommand(
            orderId: new OrderId($request->get('id'))
        );

        $result = $this->confirmOrderUseCase->execute($command);

        return new JsonResponse($result->toArray());
    }
}
```

### 10. Cyclic Dependencies

**Description:** Two classes/modules depend on each other.

**Why Bad:** Tight coupling, hard to change independently.

**Detection:**
```bash
# Check for bidirectional imports
Grep: "use.*Order" --glob "**/Customer/**/*.php"
Grep: "use.*Customer" --glob "**/Order/**/*.php"
```

**Bad:**
```php
// Domain/Order/Entity/Order.php
use Domain\Customer\Entity\Customer;

class Order
{
    private Customer $customer;  // Direct reference
}

// Domain/Customer/Entity/Customer.php
use Domain\Order\Entity\Order;

class Customer
{
    /** @var Order[] */
    private array $orders;  // Bidirectional!
}
```

**Good:**
```php
// Domain/Order/Entity/Order.php
class Order
{
    private CustomerId $customerId;  // Reference by ID
}

// Domain/Customer/Entity/Customer.php
class Customer
{
    // No reference to orders
    // Query orders through repository when needed
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Effort to Fix |
|-------------|----------|--------|---------------|
| Domain→Infra dependency | Critical | Architecture | High |
| Framework in Domain | Critical | Portability | High |
| Business logic in Repo | Critical | Testability | Medium |
| Anemic Domain | Warning | Maintainability | Medium |
| Primitive Obsession | Warning | Type Safety | Medium |
| Magic Strings | Warning | Reliability | Low |
| Public Setters | Warning | Encapsulation | Low |
| God Object | Warning | Complexity | High |
| Logic in Controller | Warning | Reusability | Medium |
| Cyclic Dependencies | Warning | Coupling | Medium |