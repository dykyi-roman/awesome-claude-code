# Clean Architecture Antipatterns

Common Clean Architecture violations with detection patterns and fixes.

## Critical Violations

### 1. Dependency Rule Violation (Inward → Outward)

**Description:** Inner layer imports from outer layer.

**Why Critical:** Breaks the fundamental principle. Makes core untestable and coupled.

**Detection:**
```bash
# Domain importing Infrastructure
Grep: "use Infrastructure\\\\|use Persistence\\\\|use Database\\\\" --glob "**/Domain/**/*.php"

# Domain importing Presentation
Grep: "use Presentation\\\\|use Controller\\\\|use Api\\\\" --glob "**/Domain/**/*.php"

# Application importing Infrastructure
Grep: "use Infrastructure\\\\" --glob "**/Application/**/*.php"

# Application importing Presentation
Grep: "use Presentation\\\\" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Infrastructure\Persistence\DoctrineOrderRepository;  // VIOLATION!
use Presentation\Api\Order\OrderResponse;                 // VIOLATION!

class Order
{
    private DoctrineOrderRepository $repository;  // Domain depends on Infrastructure
}
```

**Good:**
```php
namespace Domain\Order\Entity;

// No imports from outer layers
// Domain defines interface, Infrastructure implements

class Order
{
    // Pure domain logic
}

// Domain/Order/Repository/OrderRepositoryInterface.php
interface OrderRepositoryInterface
{
    public function save(Order $order): void;
}
```

### 2. Framework in Domain/Application

**Description:** Framework-specific code in core layers.

**Why Critical:** Core becomes coupled to framework, losing portability and testability.

**Detection:**
```bash
# Doctrine in Domain
Grep: "use Doctrine\\\\" --glob "**/Domain/**/*.php"
Grep: "@ORM\\\\|@Entity|#\\[ORM\\\\" --glob "**/Domain/**/*.php"

# Symfony in Application
Grep: "use Symfony\\\\Component\\\\HttpFoundation" --glob "**/Application/**/*.php"
Grep: "use Symfony\\\\Component\\\\Routing" --glob "**/Application/**/*.php"

# Laravel in Domain
Grep: "use Illuminate\\\\" --glob "**/Domain/**/*.php"
Grep: "extends Model|extends Eloquent" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

#[ORM\Entity]
#[ORM\Table(name: 'orders')]
class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;

    #[Assert\NotBlank]
    #[ORM\Column(type: 'string')]
    private string $status;
}
```

**Good:**
```php
namespace Domain\Order\Entity;

// Pure PHP, no framework
final class Order
{
    private OrderStatus $status;

    public function __construct(
        private readonly OrderId $id
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidStateTransitionException();
        }
        $this->status = OrderStatus::Confirmed;
    }
}

// Mapping in Infrastructure (XML/YAML/PHP config outside Domain)
```

### 3. HTTP in Application Layer

**Description:** Application layer knows about HTTP concepts.

**Why Critical:** Application layer should be usable from any interface (HTTP, CLI, Message Queue).

**Detection:**
```bash
Grep: "Request|Response|JsonResponse|HttpException" --glob "**/Application/**/*.php"
Grep: "getMethod\(\)|getUri\(\)|getHeader" --glob "**/Application/**/*.php"
Grep: "HTTP_|status.*[245][0-9][0-9]" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Order\UseCase;

use Symfony\Component\HttpFoundation\Request;   // VIOLATION!
use Symfony\Component\HttpFoundation\Response;  // VIOLATION!

final readonly class CreateOrderUseCase
{
    public function execute(Request $request): Response  // HTTP in Application
    {
        $data = json_decode($request->getContent(), true);

        // Process...

        return new Response(json_encode(['id' => $orderId]), 201);
    }
}
```

**Good:**
```php
// Application layer - framework agnostic
namespace Application\Order\UseCase;

use Application\Order\Command\CreateOrderCommand;
use Domain\Order\ValueObject\OrderId;

final readonly class CreateOrderUseCase
{
    public function execute(CreateOrderCommand $command): OrderId
    {
        // Pure application logic, no HTTP
        $order = Order::create($command->customerId, $command->lines);
        $this->repository->save($order);
        return $order->id();
    }
}

// Presentation layer handles HTTP
namespace Presentation\Api\Order;

final readonly class CreateOrderController
{
    public function __invoke(Request $request): Response
    {
        $command = CreateOrderCommand::fromArray($request->toArray());
        $orderId = $this->useCase->execute($command);
        return new JsonResponse(['id' => $orderId->value], 201);
    }
}
```

### 4. Business Logic in Adapter

**Description:** Adapter contains domain/application logic instead of just translating.

**Why Critical:** Logic becomes hidden in infrastructure, hard to test, duplicated.

**Detection:**
```bash
Grep: "if \(.*->|switch|foreach.*calculate|validate" --glob "**/Infrastructure/**/*Repository*.php"
Grep: "if \(.*->|switch|foreach.*calculate|validate" --glob "**/Infrastructure/**/*Gateway*.php"
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
        if ($order->getTotal()->isGreaterThan(Money::fromInt(10000))) {
            $order->markAsHighValue();
        }

        // VIOLATION: Validation in repository
        if (!$this->isValidOrder($order)) {
            throw new InvalidOrderException();
        }

        // VIOLATION: Notification in repository
        $this->notifier->notify($order->getCustomer(), 'Order saved');

        $this->em->persist($order);
    }
}
```

**Good:**
```php
namespace Infrastructure\Persistence;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function save(Order $order): void
    {
        // Only persistence, no logic
        $this->em->persist($order);
        $this->em->flush();
    }
}

// Business logic stays in Domain/Application
namespace Domain\Order\Entity;

final class Order
{
    public function markAsHighValueIfNeeded(): void
    {
        if ($this->total->isGreaterThan(Money::fromInt(10000))) {
            $this->highValue = true;
        }
    }
}
```

## Warnings

### 5. Missing Port (Direct External Call)

**Description:** Application layer directly calls external service without port abstraction.

**Why Bad:** Tight coupling, hard to test, no clear contract.

**Detection:**
```bash
# Direct Stripe calls in Application
Grep: "new Stripe|StripeClient|Stripe\\\\Charge" --glob "**/Application/**/*.php"

# Direct AWS calls in Application
Grep: "new S3Client|new SqsClient|Aws\\\\" --glob "**/Application/**/*.php"

# Direct HTTP calls in Application
Grep: "new GuzzleHttp|new Client\(\)|curl_" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Order\UseCase;

use Stripe\StripeClient;  // Direct dependency on Stripe

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private StripeClient $stripe  // VIOLATION: No port abstraction
    ) {}

    public function execute(ProcessPaymentCommand $command): void
    {
        // Directly calling Stripe
        $this->stripe->charges->create([
            'amount' => $command->amount,
            'currency' => 'usd',
        ]);
    }
}
```

**Good:**
```php
// Port in Application
namespace Application\Order\Port;

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;
}

// UseCase uses port
namespace Application\Order\UseCase;

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private PaymentGatewayInterface $paymentGateway  // Port
    ) {}

    public function execute(ProcessPaymentCommand $command): void
    {
        $this->paymentGateway->charge(
            new PaymentRequest($command->amount, $command->currency)
        );
    }
}

// Adapter in Infrastructure
namespace Infrastructure\Payment;

final readonly class StripePaymentGateway implements PaymentGatewayInterface
{
    public function __construct(
        private StripeClient $stripe
    ) {}

    public function charge(PaymentRequest $request): PaymentResponse
    {
        $result = $this->stripe->charges->create([...]);
        return PaymentResponse::from($result);
    }
}
```

### 6. Anemic Use Case

**Description:** Use Case is just a pass-through with no orchestration.

**Why Bad:** Adds indirection without value. May indicate anemic domain model.

**Detection:**
```bash
# Use Cases with very few lines (heuristic)
# Manually review Use Cases that are suspiciously simple
Grep: "function execute" --glob "**/UseCase/*.php" -A 5 | grep -B5 "return \$this->repository"
```

**Bad:**
```php
final readonly class GetOrderUseCase
{
    public function execute(GetOrderCommand $command): Order
    {
        return $this->repository->findById($command->orderId);  // Just delegates
    }
}

final readonly class SaveOrderUseCase
{
    public function execute(Order $order): void
    {
        $this->repository->save($order);  // Just delegates
    }
}
```

**Good:**
```php
final readonly class ConfirmOrderUseCase
{
    public function execute(ConfirmOrderCommand $command): OrderConfirmedResult
    {
        // Orchestration with multiple steps
        $order = $this->orders->findById($command->orderId);

        if ($order === null) {
            throw new OrderNotFoundException($command->orderId);
        }

        $order->confirm();

        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }

        return new OrderConfirmedResult($order->id(), $order->total());
    }
}
```

### 7. Entity Returning Infrastructure Types

**Description:** Domain entity exposes infrastructure types.

**Why Bad:** Leaks infrastructure into domain consumers.

**Detection:**
```bash
Grep: "Doctrine\\\\Common\\\\Collections" --glob "**/Domain/**/*.php"
Grep: "ArrayCollection|PersistentCollection" --glob "**/Domain/**/*.php"
Grep: "function get.*\(\): Collection" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;

class Order
{
    private Collection $lines;

    public function __construct()
    {
        $this->lines = new ArrayCollection();  // Doctrine in Domain
    }

    public function getLines(): Collection  // Returns Doctrine type
    {
        return $this->lines;
    }
}
```

**Good:**
```php
namespace Domain\Order\Entity;

final class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];

    public function addLine(OrderLine $line): void
    {
        $this->lines[] = $line;
    }

    /**
     * @return array<OrderLine>
     */
    public function lines(): array
    {
        return $this->lines;
    }
}
```

### 8. Circular Layer Dependencies

**Description:** Layers have bidirectional dependencies.

**Why Bad:** Breaks clean separation, creates tight coupling.

**Detection:**
```bash
# Check if Application imports Presentation
Grep: "use Presentation\\\\" --glob "**/Application/**/*.php"

# Check if Domain imports Application
Grep: "use Application\\\\" --glob "**/Domain/**/*.php"
```

### 9. Service Locator in Core

**Description:** Using container/service locator in Domain or Application.

**Why Bad:** Hides dependencies, makes testing harder, violates DI principle.

**Detection:**
```bash
Grep: "Container|ServiceLocator|->get\(" --glob "**/Domain/**/*.php"
Grep: "Container|ServiceLocator|->get\(" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Order\UseCase;

use Psr\Container\ContainerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private ContainerInterface $container  // VIOLATION!
    ) {}

    public function execute(CreateOrderCommand $command): void
    {
        // Getting dependencies dynamically - hidden dependencies
        $repository = $this->container->get(OrderRepositoryInterface::class);
        $eventDispatcher = $this->container->get(EventDispatcherInterface::class);

        // ...
    }
}
```

**Good:**
```php
namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,        // Explicit dependency
        private EventDispatcherInterface $events         // Explicit dependency
    ) {}

    public function execute(CreateOrderCommand $command): void
    {
        // Dependencies are clear and testable
    }
}
```

### 10. Presentation Logic in Application

**Description:** Application layer formats data for specific presentation.

**Why Bad:** Ties application to specific UI, breaks reusability.

**Detection:**
```bash
Grep: "toJson|toArray|toHtml|format" --glob "**/Application/**/*UseCase*.php"
Grep: "'id'.*=>|'name'.*=>" --glob "**/Application/**/*UseCase*.php"
```

**Bad:**
```php
namespace Application\Order\UseCase;

final readonly class GetOrderUseCase
{
    public function execute(GetOrderQuery $query): array  // Returns presentation format
    {
        $order = $this->repository->findById($query->orderId);

        // VIOLATION: Formatting for specific presentation
        return [
            'id' => $order->id()->value,
            'customer_name' => $order->customer()->fullName(),
            'formatted_total' => '$' . number_format($order->total()->amount / 100, 2),
            'status_label' => ucfirst($order->status()->value),
        ];
    }
}
```

**Good:**
```php
// Application returns DTO
namespace Application\Order\UseCase;

final readonly class GetOrderUseCase
{
    public function execute(GetOrderQuery $query): OrderDTO
    {
        $order = $this->repository->findById($query->orderId);

        return new OrderDTO(
            id: $order->id()->value,
            customerId: $order->customerId()->value,
            totalCents: $order->total()->cents(),
            currency: $order->total()->currency(),
            status: $order->status()->value
        );
    }
}

// Presentation layer formats
namespace Presentation\Api\Order;

final readonly class GetOrderController
{
    public function __invoke(string $id): JsonResponse
    {
        $order = $this->getOrder->execute(new GetOrderQuery($id));

        return new JsonResponse([
            'id' => $order->id,
            'formatted_total' => '$' . number_format($order->totalCents / 100, 2),
            'status_label' => ucfirst($order->status),
        ]);
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Dependency Rule Violation | Critical | Architecture | High |
| Framework in Domain | Critical | Portability | High |
| HTTP in Application | Critical | Reusability | Medium |
| Business Logic in Adapter | Critical | Testability | Medium |
| Missing Port | Warning | Testability | Medium |
| Anemic Use Case | Warning | Maintainability | Low |
| Entity with Infra Types | Warning | Coupling | Medium |
| Circular Dependencies | Warning | Maintainability | High |
| Service Locator | Warning | Testability | Medium |
| Presentation in Application | Warning | Reusability | Medium |
