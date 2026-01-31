# Layered Architecture Antipatterns

Common violations in Layered Architecture with detection patterns and fixes.

## Critical Violations

### 1. Layer Skipping

**Description:** A layer calls a layer that is not directly below it.

**Why Critical:** Breaks encapsulation, bypasses business logic, creates tight coupling.

**Detection:**
```bash
# Controller calling repository directly
Grep: "RepositoryInterface|Repository\$" --glob "**/Presentation/**/*.php"
Grep: "->findById|->save\(" --glob "**/Controller/**/*.php"

# Presentation calling Infrastructure
Grep: "use Infrastructure\\\\" --glob "**/Presentation/**/*.php"
```

**Bad:**
```php
namespace Presentation\Api\Order;

use Infrastructure\Persistence\DoctrineOrderRepository;  // VIOLATION!

final readonly class OrderController
{
    public function __construct(
        private DoctrineOrderRepository $orderRepository  // Skips Application layer!
    ) {}

    public function show(string $id): JsonResponse
    {
        $order = $this->orderRepository->findById($id);  // Direct DB access
        return new JsonResponse($order);
    }
}
```

**Good:**
```php
namespace Presentation\Api\Order;

use Application\Order\Service\OrderServiceInterface;

final readonly class OrderController
{
    public function __construct(
        private OrderServiceInterface $orderService  // Application layer
    ) {}

    public function show(string $id): JsonResponse
    {
        $order = $this->orderService->getOrder($id);  // Through Application
        return new JsonResponse(OrderResource::fromDTO($order)->toArray());
    }
}
```

### 2. Upward Dependency

**Description:** Lower layer depends on upper layer.

**Why Critical:** Inverts architecture, creates circular dependencies.

**Detection:**
```bash
# Domain depending on Application
Grep: "use Application\\\\" --glob "**/Domain/**/*.php"

# Infrastructure depending on Presentation
Grep: "use Presentation\\\\" --glob "**/Infrastructure/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Application\Order\Service\PricingService;  // VIOLATION!
use Presentation\Api\Order\Response\OrderResource;  // VIOLATION!

final class Order
{
    public function calculatePrice(PricingService $service): Money  // Depends on App layer!
    {
        return $service->calculate($this);
    }

    public function toResource(): OrderResource  // Depends on Presentation!
    {
        return OrderResource::fromEntity($this);
    }
}
```

**Good:**
```php
namespace Domain\Order\Entity;

use Domain\Order\ValueObject\Money;
use Domain\Pricing\Service\PricingStrategyInterface;  // Domain interface

final class Order
{
    public function calculatePrice(PricingStrategyInterface $strategy): Money
    {
        return $strategy->calculate($this->lines());
    }

    // No toResource() - mapping happens in Presentation layer
}
```

### 3. Business Logic in Controller

**Description:** Controller contains business rules or complex logic.

**Why Critical:** Logic scattered, not reusable, untestable.

**Detection:**
```bash
# Complex conditionals in controllers
Grep: "if \(.*->|switch \(" --glob "**/Controller/**/*.php"

# Calculations in controllers
Grep: "foreach.*->|array_reduce|array_map" --glob "**/Controller/**/*.php" -A 3
```

**Bad:**
```php
namespace Presentation\Api\Order;

final readonly class OrderController
{
    public function create(Request $request): JsonResponse
    {
        // VIOLATION: Business logic in controller
        $customer = $this->customerRepository->find($request->get('customer_id'));

        if (!$customer->isActive()) {
            throw new CustomerNotActiveException();
        }

        if ($customer->hasOutstandingDebt()) {
            throw new CustomerHasDebtException();
        }

        // VIOLATION: Price calculation in controller
        $total = 0;
        foreach ($request->get('lines') as $line) {
            $product = $this->productRepository->find($line['product_id']);
            $price = $product->price() * $line['quantity'];

            if ($line['quantity'] > 10) {
                $price *= 0.9;  // 10% bulk discount
            }

            $total += $price;
        }

        // More business logic...
    }
}
```

**Good:**
```php
namespace Presentation\Api\Order;

use Application\Order\Service\OrderServiceInterface;
use Application\Order\DTO\CreateOrderDTO;

final readonly class OrderController
{
    public function __construct(
        private OrderServiceInterface $orderService
    ) {}

    public function create(CreateOrderRequest $request): JsonResponse
    {
        // Controller only maps and delegates
        $dto = CreateOrderDTO::fromRequest($request);

        $result = $this->orderService->createOrder($dto);

        return new JsonResponse(
            OrderResource::fromDTO($result)->toArray(),
            201
        );
    }
}
```

### 4. Infrastructure in Domain

**Description:** Domain layer uses infrastructure components directly.

**Why Critical:** Domain becomes coupled to technology, untestable.

**Detection:**
```bash
# ORM in Domain
Grep: "Doctrine\\\\|Eloquent\\\\" --glob "**/Domain/**/*.php"

# Database in Domain
Grep: "PDO|mysqli|Connection" --glob "**/Domain/**/*.php"

# External services in Domain
Grep: "GuzzleHttp|HttpClient|Curl" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Doctrine\ORM\Mapping as ORM;  // VIOLATION!
use Doctrine\Common\Collections\ArrayCollection;

#[ORM\Entity]
#[ORM\Table(name: 'orders')]
final class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;

    #[ORM\OneToMany(mappedBy: 'order', targetEntity: OrderLine::class)]
    private ArrayCollection $lines;  // Doctrine type!

    public function __construct()
    {
        $this->lines = new ArrayCollection();  // Infrastructure leak!
    }
}
```

**Good:**
```php
namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;

final class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId
    ) {}

    public function addLine(OrderLine $line): void
    {
        $this->lines[] = $line;
    }

    /** @return array<OrderLine> */
    public function lines(): array
    {
        return $this->lines;
    }
}

// Doctrine mapping in Infrastructure
// infrastructure/persistence/doctrine/mapping/Order.orm.xml
```

## Warnings

### 5. Anemic Domain Model

**Description:** Domain entities have only getters/setters, no behavior.

**Why Bad:** Business logic ends up in services, violates OOP.

**Detection:**
```bash
# Entities with only getters
Grep: "public function (get|set|is)" --glob "**/Domain/**/Entity/**/*.php"

# No business methods
Grep: "final class.*Entity" --glob "**/Domain/**/*.php" -A 50 | grep -c "public function"
```

**Bad:**
```php
namespace Domain\Order\Entity;

final class Order
{
    private string $id;
    private string $status;
    private int $total;

    // Only getters and setters
    public function getId(): string { return $this->id; }
    public function getStatus(): string { return $this->status; }
    public function setStatus(string $status): void { $this->status = $status; }
    public function getTotal(): int { return $this->total; }
    public function setTotal(int $total): void { $this->total = $total; }
}

// Logic in service
namespace Application\Order\Service;

class OrderService
{
    public function confirmOrder(Order $order): void
    {
        if ($order->getStatus() !== 'draft') {
            throw new Exception('Can only confirm draft orders');
        }
        if ($order->getTotal() <= 0) {
            throw new Exception('Order must have items');
        }
        $order->setStatus('confirmed');
    }
}
```

**Good:**
```php
namespace Domain\Order\Entity;

use Domain\Order\Exception\CannotConfirmOrderException;

final class Order
{
    private OrderStatus $status;
    private array $lines = [];

    public function confirm(): void
    {
        if (!$this->canBeConfirmed()) {
            throw new CannotConfirmOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
    }

    private function canBeConfirmed(): bool
    {
        return $this->status === OrderStatus::Draft
            && !empty($this->lines);
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn (Money $sum, OrderLine $line) => $sum->add($line->total()),
            Money::zero('USD')
        );
    }
}
```

### 6. Fat Service

**Description:** Application service does too much, contains domain logic.

**Why Bad:** God class, hard to test, violates SRP.

**Detection:**
```bash
# Large service files
find . -name "*Service.php" -path "*/Application/*" | xargs wc -l | sort -n

# Many dependencies
Grep: "public function __construct" --glob "**/Application/**/*Service.php" -A 20
```

**Bad:**
```php
namespace Application\Order\Service;

final readonly class OrderService
{
    public function __construct(
        private OrderRepository $orders,
        private CustomerRepository $customers,
        private ProductRepository $products,
        private InventoryService $inventory,
        private PaymentService $payment,
        private ShippingService $shipping,
        private NotificationService $notifications,
        private DiscountCalculator $discounts,
        private TaxCalculator $taxes,
        private LoggerInterface $logger
        // 10+ dependencies = smell
    ) {}

    public function createOrder(CreateOrderDTO $dto): OrderDTO
    {
        // 200+ lines of logic mixing:
        // - Validation
        // - Domain logic
        // - Infrastructure calls
        // - Side effects
    }
}
```

**Good:**
```php
namespace Application\Order\Service;

final readonly class CreateOrderService
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private CustomerValidatorInterface $customerValidator,
        private OrderFactoryInterface $orderFactory,
        private EventDispatcherInterface $events
        // 3-5 focused dependencies
    ) {}

    public function execute(CreateOrderDTO $dto): OrderDTO
    {
        // Orchestration only, no business logic
        $this->customerValidator->validateCanOrder($dto->customerId);

        $order = $this->orderFactory->create($dto);

        $this->orders->save($order);

        $this->events->dispatch(...$order->releaseEvents());

        return OrderDTO::fromEntity($order);
    }
}
```

### 7. Leaky Abstraction

**Description:** Lower layer's implementation details leak to upper layers.

**Why Bad:** Changes in infrastructure require changes in application.

**Detection:**
```bash
# SQL in Application layer
Grep: "SELECT|INSERT|UPDATE|DELETE" --glob "**/Application/**/*.php"

# Doctrine QueryBuilder in Application
Grep: "createQueryBuilder|DQL" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Order\Service;

use Doctrine\ORM\EntityManagerInterface;

final readonly class OrderService
{
    public function __construct(
        private EntityManagerInterface $em  // Doctrine in Application!
    ) {}

    public function findHighValueOrders(): array
    {
        // Raw SQL in Application layer!
        return $this->em->createQuery('
            SELECT o FROM Domain\Order\Entity\Order o
            WHERE o.totalCents > 100000
            ORDER BY o.createdAt DESC
        ')->getResult();
    }
}
```

**Good:**
```php
namespace Application\Order\Service;

use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\ValueObject\Money;

final readonly class OrderService
{
    public function __construct(
        private OrderRepositoryInterface $orders
    ) {}

    public function findHighValueOrders(): array
    {
        $threshold = new Money(100000, 'USD');
        return array_map(
            fn ($order) => OrderDTO::fromEntity($order),
            $this->orders->findWithTotalAbove($threshold)
        );
    }
}

// SQL hidden in Infrastructure
namespace Infrastructure\Persistence;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function findWithTotalAbove(Money $threshold): array
    {
        return $this->em->createQuery('...')
            ->setParameter('threshold', $threshold->cents())
            ->getResult();
    }
}
```

### 8. Circular Dependencies Between Layers

**Description:** Two layers depend on each other.

**Why Bad:** Cannot compile/test independently, architectural smell.

**Detection:**
```bash
# Check for bidirectional dependencies
Grep: "use Application\\\\" --glob "**/Domain/**/*.php"
Grep: "use Domain\\\\" --glob "**/Application/**/*.php"
# Both having results = circular dependency
```

**Fix:** Use dependency inversion with interfaces in the lower layer.

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Layer skipping | Critical | Architecture | Medium |
| Upward dependency | Critical | Architecture | High |
| Business in controller | Critical | Maintainability | Medium |
| Infrastructure in domain | Critical | Testability | High |
| Anemic domain | Warning | Design | High |
| Fat service | Warning | Maintainability | Medium |
| Leaky abstraction | Warning | Coupling | Medium |
| Circular dependency | Warning | Architecture | Medium |

## Detection Summary

```bash
# Quick audit script

echo "=== Layer Skipping ==="
Grep: "use Infrastructure\\\\" --glob "**/Presentation/**/*.php"
Grep: "RepositoryInterface" --glob "**/Presentation/**/*.php"

echo "=== Upward Dependencies ==="
Grep: "use Application\\\\" --glob "**/Domain/**/*.php"
Grep: "use Presentation\\\\" --glob "**/Domain/**/*.php"
Grep: "use Presentation\\\\" --glob "**/Application/**/*.php"

echo "=== Infrastructure in Domain ==="
Grep: "Doctrine\\\\|Eloquent\\\\" --glob "**/Domain/**/*.php"
Grep: "PDO|Connection" --glob "**/Domain/**/*.php"

echo "=== Business Logic in Controllers ==="
Grep: "if \(.*->status|switch \(" --glob "**/Controller/**/*.php"
Grep: "foreach.*calculate" --glob "**/Controller/**/*.php"

echo "=== Anemic Domain ==="
Grep: "public function set" --glob "**/Domain/**/Entity/**/*.php"
```
