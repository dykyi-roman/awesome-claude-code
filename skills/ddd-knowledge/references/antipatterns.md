# DDD Antipatterns

DDD-aligned antipatterns with detection patterns and fixes. These are violations of the DDD methodology — ubiquitous language, bounded contexts, aggregate consistency — not violations of Clean Architecture's dependency rule (which is a separate concern that varies by chosen style).

## Universal DDD Antipatterns

### 1. Anemic Domain Model

**Description:** Entities with only getters/setters, no behavior. Business logic ends up in services.

**Why Critical:** Violates the core DDD idea of putting business meaning in the model. The entity becomes a passive data bag.

**Detection:**
```bash
# Find entities with only get/set methods (anemic signal)
Grep: "public function (get|set|is|has)[A-Z]" --glob "**/*Entity.php" --glob "**/Entity/**/*.php"

# Find behavior methods (presence is good)
Grep: "public function [a-z][a-z]+" --glob "**/*Entity.php" --glob "**/Entity/**/*.php" | grep -v "get\|set\|is\|has\|__"
```

**Anemic (Bad):**
```php
final class Order
{
    private string $status;
    private array $lines;

    public function getStatus(): string { return $this->status; }
    public function setStatus(string $status): void { $this->status = $status; }
    public function getLines(): array { return $this->lines; }
    public function setLines(array $lines): void { $this->lines = $lines; }
}

// Logic in service — wrong place
final class OrderService
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
final class Order
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

### 2. Primitive Obsession

**Description:** Using primitive types (`string`, `int`) instead of Value Objects for domain concepts.

**Why Critical:** Validation scatters, no behavior on the concept, meaning lost. Two different `string` parameters can be mixed up at the call site.

**Detection:**
```bash
Grep: "string \$email|string \$phone|string \$currency|int \$amount|string \$status" --glob "**/Entity/**/*.php" --glob "**/*Entity.php"
Grep: "function.*string \$id\)" --glob "**/Entity/**/*.php" --glob "**/*Entity.php"
```

**Bad:**
```php
final class Customer
{
    public function __construct(
        private string $id,         // Should be CustomerId
        private string $email,      // Should be Email
        private string $phone,      // Should be Phone
        private int $balance,       // Should be Money
        private string $currency,   // Part of Money
    ) {}
}
```

**Good:**
```php
final class Customer
{
    public function __construct(
        private readonly CustomerId $id,
        private Email $email,
        private Phone $phone,
        private Money $balance,
    ) {}
}
```

### 3. Save-Side Mutation in Repository

**Description:** Repository `save()` methods that calculate, validate, or change entity state. Only persistence belongs there.

**Important distinction:** Query-side business intent on a Repository **is correct DDD**. A method like `findShippableOrdersForToday()` encodes domain knowledge in the Repository and is encouraged. The violation is mutation logic on the WRITE side.

**Why Critical:** Business rules scatter, the entity loses control of its invariants, and the same logic gets duplicated across every concrete Repository class (Doctrine variant, in-memory test double, etc.).

**Detection:**
```bash
# Mutation logic inside save()
Grep: "function save.*\{[\s\S]*if \(|function save.*\{[\s\S]*->set" --glob "**/*Repository.php"
Grep: "private function (calculate|validate|determineStatus)" --glob "**/*Repository.php"
```

**Bad (mutation on write):**
```php
final class OrderRepository
{
    public function save(Order $order): void
    {
        // VIOLATION: mutating state during save
        if ($order->total() > 10000) {
            $order->setRequiresApproval(true);
        }

        // VIOLATION: validation during save
        if (!$this->validateOrderLines($order)) {
            throw new InvalidOrderException();
        }

        $this->em->persist($order);
    }
}
```

**Good (persistence-only save + business-meaningful query):**
```php
final class OrderRepository
{
    public function save(Order $order): void
    {
        // Persistence only
        $this->em->persist($order);
        $this->em->flush();
    }

    /**
     * Business-meaningful query — CORRECT DDD.
     * The repository encodes domain intent in retrieval, not in mutation.
     *
     * @return list<Order>
     */
    public function findShippableOrdersForToday(): array
    {
        // domain-meaningful query
    }
}

// Business rule lives in the aggregate
final class Order
{
    public function requiresApproval(): bool
    {
        return $this->total()->isGreaterThan(Money::fromInt(10000, 'USD'));
    }
}
```

### 4. Aggregate Boundary Leakage

**Description:** Modifying child entities directly from outside the aggregate root, bypassing the root's invariants.

**Why Critical:** The aggregate root is the only thing that can enforce consistency rules across its children. Bypassing it lets the aggregate enter an invalid state.

**Detection:**
```bash
# Direct child mutation outside the root
Grep: "->getLines\(\)\[" --glob "**/*.php"
Grep: "->getItems\(\)->add\(" --glob "**/*.php"
Grep: "->getChildren\(\)\[" --glob "**/*.php"
```

**Bad:**
```php
// Outside code reaches into aggregate's children
$order->getLines()[0]->setQuantity(999);   // Bypasses Order's invariants
$order->getLines()->add(new OrderLine(...)); // Total isn't recalculated
```

**Good:**
```php
// Only the root has methods to change child state
$order->updateLineQuantity($lineId, 999);  // Order validates + recalculates total
$order->addLine($productId, $quantity);    // Order checks limits, updates total
```

### 5. Setter-Driven State Changes

**Description:** Public setters that allow direct state modification, bypassing business rules.

**Why Critical:** A `setStatus()` method names the *what* (changing a field) instead of the *why* (the business intent). Business rules tied to the transition are not enforced.

**Detection:**
```bash
Grep: "public function set[A-Z]" --glob "**/Entity/**/*.php" --glob "**/*Entity.php" --glob "**/Aggregate/**/*.php"
```

**Bad:**
```php
final class Order
{
    public function setStatus(OrderStatus $status): void
    {
        $this->status = $status;  // No validation!
    }
}

// Anywhere in code
$order->setStatus(OrderStatus::Shipped);  // Bypasses rules
```

**Good (intent-revealing methods):**
```php
final class Order
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

### 6. Ubiquitous Language Drift

**Description:** Code uses technical names that don't match the business vocabulary. Business says "confirm an order"; code says `setOrderStateValue(2)`.

**Why Critical:** Breaks the core DDD idea. When the model and the conversation use different words, the model decays — refactoring becomes guesswork because the link between "what the business means" and "what the code says" is broken.

**Detection:**
Subjective; compare class/method names against business vocabulary in conversations, docs, support tickets.

**Bad:**
```php
$user->process();
$order->updateState(2);
$invoice->handleAction('finalize');
$payment->doProcessing();
```

**Good:**
```php
$user->register();
$order->confirm();
$invoice->finalize();
$payment->capture();
```

### 7. Magic Strings

**Description:** String literals for domain values. No type safety, typos cause bugs, meaning unclear.

**Detection:**
```bash
Grep: "=== ['\"]pending['\"]|=== ['\"]active['\"]|=== ['\"]draft['\"]" --glob "**/*.php"
Grep: "== ['\"][a-z]+['\"]" --glob "**/Entity/**/*.php"
```

**Bad:**
```php
final class Order
{
    private string $status = 'draft';

    public function confirm(): void
    {
        if ($this->status === 'draft') {       // Magic string
            $this->status = 'confirmed';        // Magic string
        }
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
        return match ($this) {
            self::Draft => in_array($target, [self::Confirmed, self::Cancelled]),
            self::Confirmed => in_array($target, [self::Shipped, self::Cancelled]),
            default => false,
        };
    }
}

final class Order
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

### 8. Domain Service Holding State

**Description:** A Domain Service that keeps state between method calls. Domain Services are stateless coordinators of multiple aggregates.

**Why Critical:** State in a Domain Service breaks the conceptual model. State belongs in entities/aggregates; services should be operations.

**Detection:**
```bash
# Look for non-injected properties in Domain Services
Grep: "private (\\$|array|string|int|float|bool)" --glob "**/Service/**/*Service.php" --glob "**/*DomainService.php"
```

**Bad:**
```php
final class PricingService
{
    private array $cachedPrices = [];   // STATE — wrong place

    public function calculate(Order $order, Customer $customer): Money
    {
        if (isset($this->cachedPrices[$order->id()->value])) {
            return $this->cachedPrices[$order->id()->value];
        }
        $price = /* ... */;
        $this->cachedPrices[$order->id()->value] = $price;
        return $price;
    }
}
```

**Good (stateless):**
```php
final readonly class PricingService
{
    public function __construct(
        private DiscountPolicy $discountPolicy,
    ) {}

    public function calculate(Order $order, Customer $customer): Money
    {
        return $this->discountPolicy->apply($order->subtotal(), $customer);
    }
}
```

### 9. Shared Mutable State Across Bounded Contexts

**Description:** One context's aggregate exposed to another for direct modification, instead of communicating through events or context-specific anti-corruption layers.

**Why Critical:** Breaks bounded context isolation. Changes in one context invisibly couple to another.

**Detection:**
```bash
# Imports of one context's aggregate inside another
Grep: "use .+\\(Order|Payment|Inventory)\\.+Aggregate" --glob "**/*.php"
```

**Bad:**
```php
// Inventory context directly modifies Order
final class InventoryHandler
{
    public function onItemReserved(Order $order): void
    {
        $order->markItemReserved($itemId);  // Reaches into Order context
    }
}
```

**Good (events + ACL):**
```php
// Inventory raises an event, Order context decides what to do
final class InventoryService
{
    public function reserve(ItemId $itemId, int $quantity): void
    {
        // ...
        $this->eventDispatcher->dispatch(new ItemReserved($itemId, $quantity));
    }
}

// In Order context — own handler subscribes to the event
final class MarkOrderItemReservedHandler
{
    public function __invoke(ItemReserved $event): void
    {
        // Translate cross-context event into Order's vocabulary
    }
}
```

### 10. Business Logic in Controller

**Description:** Controllers/Actions make business decisions.

**Why Warning:** Logic isn't reusable across entry points (HTTP, CLI, async workers) and is hard to test in isolation.

**Detection:**
```bash
Grep: "if \(.*->can|if \(.*->is[A-Z]|if \(.*->has[A-Z]" --glob "**/*Controller.php" --glob "**/*Action.php"
Grep: "foreach|while|switch" --glob "**/*Controller.php"
```

**Bad:**
```php
final class OrderController
{
    public function confirm(Request $request): Response
    {
        $order = $this->repository->find($request->get('id'));

        // VIOLATION: business logic in controller
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
final class OrderController
{
    public function confirm(Request $request): Response
    {
        $command = new ConfirmOrderCommand(
            orderId: new OrderId($request->get('id')),
        );

        $result = $this->confirmOrderUseCase->execute($command);

        return new JsonResponse($result->toArray());
    }
}
```

### 11. Cyclic Dependencies Between Aggregates

**Description:** Two aggregates reference each other by entity, not by ID.

**Why Warning:** Tight coupling, hard to change independently, transactional boundaries become unclear (which one is the root?).

**Detection:**
```bash
# Bidirectional aggregate imports
Grep: "use .+\\Order\\.+Entity\\Order" --glob "**/*.php"
Grep: "use .+\\Customer\\.+Entity\\Customer" --glob "**/*.php"
```

**Bad:**
```php
final class Order
{
    private Customer $customer;  // Direct reference
}

final class Customer
{
    /** @var list<Order> */
    private array $orders;  // Bidirectional!
}
```

**Good:**
```php
final class Order
{
    private CustomerId $customerId;  // Reference by identity
}

final class Customer
{
    // No reference to orders
    // Query orders through repository when needed
}
```

## Architecture-Dependent Items

These are NOT universal DDD violations. They depend on the project's chosen architectural style.

### A. Framework Imports in Domain (Clean Architecture / Hexagonal)

**Description:** Domain code using framework-specific classes or attributes.

**Status by architecture:**
- **Clean Architecture / Hexagonal:** Critical violation — the dependency rule forbids Domain depending on Infrastructure-level types
- **Layered 3-tier (Domain-centric):** Not architecturally forbidden — whether to put Doctrine attributes on Domain entities (vs. using XML/YAML mapping or a separate mapping class) is a **project choice**. Check the project's own coding standard before flagging.
- **N-Tier (4-tier Classical):** Not architecturally forbidden — same as Layered 3-tier, it is a project choice
- **Package-by-Feature:** Follows the inner architecture chosen per feature
- **MVC:** Style-dependent

**Detection (use only in projects that enforce framework-isolation — Clean / Hexagonal / strict N-Tier):**
```bash
Grep: "use Doctrine\\\\|use Illuminate\\\\|use Symfony\\\\" --glob "**/Domain/**/*.php"
Grep: "@ORM\\\\|#\\[ORM\\\\" --glob "**/Domain/**/*.php"
```

**Bad (in Clean Architecture / Hexagonal):**
```php
namespace Entity;

use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity]
#[ORM\Table(name: 'orders')]
final class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;
}
```

**Good (in Clean Architecture / Hexagonal — mapping moves to XML/YAML config in Infrastructure):**
```php
namespace Entity;

final class Order
{
    public function __construct(
        private readonly OrderId $id,
    ) {}
}
```

**Not architecturally forbidden in Layered 3-tier (Domain-centric) or N-Tier** — whether to use Doctrine attributes on entities, XML/YAML mapping, or a dedicated mapping class is a project choice in either architecture. Check the project's own coding standard before flagging.

### B. Cross-Layer Imports (varies by architecture)

**Description:** Imports that cross the architectural boundary the project's style forbids.

**Status by architecture:**
- **Clean Architecture:** Domain importing Infrastructure is critical; Application importing Infrastructure is also critical (DIP).
- **Hexagonal:** Adapters depend on Ports — not the other way around. Domain may declare Driven Ports inside Domain itself; Application declares Driving Ports.
- **Layered 3-tier (Domain-centric):** Domain may use Infrastructure interfaces (no inversion required). Domain owns its own persistence implementations under `Domain/{Context}/Repository/Doctrine/`.
- **N-Tier (4-tier Classical):** Strict downward calls only. Application may depend on Infrastructure; Presentation may not skip Application.
- **Package-by-Feature:** Cross-feature imports are critical; inside each feature, the chosen inner architecture's rules apply.
- **MVC:** Controllers depend on Models and Views; the reverse is forbidden.

**Detection (adjust the layer names and target globs to the project's chosen style):**
```bash
# Clean Architecture: Domain importing Infrastructure (forbidden)
Grep: "use.+\\\\Infrastructure\\\\" --glob "**/Domain/**/*.php"

# Clean Architecture: Application importing Infrastructure (also forbidden — DIP)
Grep: "use.+\\\\Infrastructure\\\\" --glob "**/Application/**/*.php"

# Layered 3-tier / N-Tier: Domain importing Application/Presentation is forbidden in either
Grep: "use.+\\\\(Application|Presentation)\\\\" --glob "**/Domain/**/*.php"

# Package-by-Feature: cross-feature direct imports (replace Order/Payment with actual names)
Grep: "use.+\\\\Payment\\\\" --glob "**/Order/**/*.php"
```

## Severity Matrix

| Antipattern | Severity | Why |
|-------------|----------|-----|
| Anemic Domain Model | Critical | Core DDD violation |
| Primitive Obsession | Critical | Core DDD violation |
| Save-side mutation in Repository | Critical | Core DDD violation |
| Aggregate boundary leakage | Critical | Core DDD violation |
| Setter-driven state changes | Critical | Encapsulation broken |
| Ubiquitous language drift | Critical | Core DDD violation |
| Magic strings | Warning | Type safety |
| Domain Service holding state | Warning | Conceptual model |
| Shared mutable state across contexts | Critical | Bounded context isolation |
| Business logic in Controller | Warning | Reusability |
| Cyclic aggregate dependencies | Warning | Coupling |
| Framework imports in Domain | Critical (Clean / Hexagonal — architectural rule) / project-choice (Layered 3-tier, N-Tier, MVC) | Check project's coding standard |
| Cross-layer imports | Severity depends on the project's style | Architectural choice |
