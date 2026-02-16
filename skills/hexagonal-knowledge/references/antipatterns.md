# Hexagonal Architecture Antipatterns

Common Hexagonal Architecture violations with detection patterns and fixes.

## Critical Violations

### 1. Core Depends on Adapter

**Description:** Application core imports infrastructure code directly.

**Why Critical:** Breaks the fundamental principle. Core becomes coupled to technology choices.

**Detection:**
```bash
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"
Grep: "use Infrastructure\\\\" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Order\UseCase;

use Infrastructure\Persistence\DoctrineOrderRepository;  // VIOLATION!
use Infrastructure\ExternalService\StripePaymentAdapter; // VIOLATION!

final readonly class CreateOrderUseCase
{
    public function __construct(
        private DoctrineOrderRepository $orders  // Coupled to Doctrine!
    ) {}
}
```

**Good:**
```php
namespace Application\Order\UseCase;

use Domain\Order\Port\Output\OrderRepositoryInterface;  // Port
use Application\Payment\Port\Output\PaymentGatewayInterface;  // Port

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,        // Port - any impl
        private PaymentGatewayInterface $paymentGateway  // Port - any impl
    ) {}
}
```

### 2. Missing Port Abstraction

**Description:** Use case directly uses external service without port.

**Why Critical:** Tight coupling, untestable, can't swap implementations.

**Detection:**
```bash
Grep: "new StripeClient|new GuzzleHttp|new SqsClient" --glob "**/Application/**/*.php"
Grep: "new \\\\Stripe|new \\\\Aws|new \\\\Twilio" --glob "**/Application/**/*.php"
```

**Bad:**
```php
namespace Application\Payment\UseCase;

use Stripe\StripeClient;  // Direct dependency on Stripe!

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private StripeClient $stripe  // No port!
    ) {}

    public function execute(PaymentRequest $request): PaymentResponse
    {
        // Directly using Stripe SDK
        $charge = $this->stripe->charges->create([...]);
    }
}
```

**Good:**
```php
namespace Application\Payment\UseCase;

use Application\Payment\Port\Output\PaymentGatewayInterface;

final readonly class ProcessPaymentUseCase
{
    public function __construct(
        private PaymentGatewayInterface $paymentGateway  // Port
    ) {}

    public function execute(PaymentRequest $request): PaymentResponse
    {
        // Using port - implementation can be Stripe, PayPal, etc.
        return $this->paymentGateway->charge($request);
    }
}
```

### 3. Business Logic in Adapter

**Description:** Adapter contains domain/business logic.

**Why Critical:** Logic scattered, hard to test, duplicated across adapters.

**Detection:**
```bash
Grep: "if \(.*->|switch \(.*->|foreach.*->calculate" --glob "**/Infrastructure/**/*.php"
Grep: "private function (validate|calculate|check|process)" --glob "**/Infrastructure/**/*.php"
```

**Bad:**
```php
namespace Infrastructure\Http\Controller;

final readonly class CreateOrderController
{
    public function __invoke(Request $request): JsonResponse
    {
        // VIOLATION: Business logic in adapter
        $customerId = $request->get('customer_id');
        $customer = $this->customerRepository->find($customerId);

        if (!$customer->isActive()) {
            throw new InactiveCustomerException();
        }

        // VIOLATION: Discount calculation in adapter
        $lines = $request->get('lines');
        $total = 0;
        foreach ($lines as $line) {
            $total += $line['quantity'] * $line['price'];
        }

        if ($total > 10000) {
            $total *= 0.9;  // 10% discount
        }

        // ...
    }
}
```

**Good:**
```php
namespace Infrastructure\Http\Controller;

final readonly class CreateOrderController
{
    public function __construct(
        private CreateOrderUseCaseInterface $createOrder
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        // Adapter only translates and delegates
        $dto = CreateOrderRequest::fromArray($request->toArray());

        $response = $this->createOrder->execute($dto);

        return new JsonResponse($response->toArray(), 201);
    }
}

// Business logic in domain
namespace Domain\Order\Entity;

final class Order
{
    public function applyVolumeDiscount(): void
    {
        if ($this->total->isGreaterThan(Money::fromInt(10000))) {
            $this->discount = $this->total->multiply(0.1);
        }
    }
}
```

### 4. Port with Implementation Details

**Description:** Port interface exposes technology-specific types.

**Why Critical:** Port becomes coupled to specific implementation.

**Detection:**
```bash
Grep: "Doctrine\\\\|Eloquent\\\\|PDO|mysqli" --glob "**/Port/**/*.php"
Grep: "QueryBuilder|EntityManager|Connection" --glob "**/Port/**/*.php"
```

**Bad:**
```php
namespace Domain\Order\Port\Output;

use Doctrine\ORM\QueryBuilder;  // VIOLATION!

interface OrderRepositoryInterface
{
    public function findById(string $id): ?array;  // Returns array, not entity

    public function createQueryBuilder(): QueryBuilder;  // Doctrine-specific!

    public function executeRawSql(string $sql): array;  // Implementation detail!
}
```

**Good:**
```php
namespace Domain\Order\Port\Output;

use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;  // Domain types

    public function findByCustomerId(CustomerId $id): array;  // Domain types

    public function save(Order $order): void;  // Domain types
}
```

## Warnings

### 5. Controller Calling Repository Directly

**Description:** Driving adapter bypasses use case and calls driven port directly.

**Why Bad:** No place for application logic, breaks hexagonal flow.

**Detection:**
```bash
Grep: "RepositoryInterface|Repository\$" --glob "**/Infrastructure/Http/**/*.php"
Grep: "->findById|->save\(" --glob "**/Controller/**/*.php"
```

**Bad:**
```php
namespace Infrastructure\Http\Controller;

use Domain\Order\Port\Output\OrderRepositoryInterface;

final readonly class GetOrderController
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository  // Direct repo access
    ) {}

    public function __invoke(string $id): JsonResponse
    {
        $order = $this->orderRepository->findById(new OrderId($id));

        return new JsonResponse($order->toArray());
    }
}
```

**Good:**
```php
namespace Infrastructure\Http\Controller;

use Application\Order\Port\Input\GetOrderUseCaseInterface;

final readonly class GetOrderController
{
    public function __construct(
        private GetOrderUseCaseInterface $getOrder  // Use case
    ) {}

    public function __invoke(string $id): JsonResponse
    {
        $response = $this->getOrder->execute(new GetOrderRequest($id));

        return new JsonResponse($response->toArray());
    }
}
```

### 6. Driving Port with Framework Types

**Description:** Driving port interface uses framework-specific types.

**Why Bad:** Core becomes coupled to framework, can't use from different interfaces.

**Detection:**
```bash
Grep: "Symfony\\\\|Laravel\\\\|Request|Response" --glob "**/Port/Input/**/*.php"
```

**Bad:**
```php
namespace Application\Order\Port\Input;

use Symfony\Component\HttpFoundation\Request;   // VIOLATION!
use Symfony\Component\HttpFoundation\Response;  // VIOLATION!

interface CreateOrderUseCaseInterface
{
    public function execute(Request $request): Response;  // HTTP types!
}
```

**Good:**
```php
namespace Application\Order\Port\Input;

use Application\Order\DTO\CreateOrderRequest;
use Application\Order\DTO\CreateOrderResponse;

interface CreateOrderUseCaseInterface
{
    public function execute(CreateOrderRequest $request): CreateOrderResponse;
}
```

### 7. Monolithic Adapter

**Description:** Single adapter handles multiple unrelated responsibilities.

**Why Bad:** Violates SRP, hard to maintain and test.

**Detection:**
```bash
# Large adapter files
find . -name "*Adapter.php" -o -name "*Controller.php" | xargs wc -l | sort -n
```

**Bad:**
```php
namespace Infrastructure\ExternalService;

// One adapter for everything
final readonly class ExternalServicesAdapter
{
    public function chargePayment(...) { }
    public function sendEmail(...) { }
    public function sendSms(...) { }
    public function createShipment(...) { }
    public function uploadToS3(...) { }
}
```

**Good:**
```php
namespace Infrastructure\ExternalService\Payment;
final readonly class StripePaymentAdapter implements PaymentGatewayInterface { }

namespace Infrastructure\ExternalService\Notification;
final readonly class SendGridEmailAdapter implements EmailServiceInterface { }

namespace Infrastructure\ExternalService\Shipping;
final readonly class FedExShippingAdapter implements ShippingServiceInterface { }
```

### 8. Leaky Abstraction in Port

**Description:** Port returns types that reveal implementation details.

**Why Bad:** Consumers become coupled to implementation.

**Detection:**
```bash
Grep: "function.*\): \\\\Doctrine|function.*\): \\\\Stripe" --glob "**/Port/**/*.php"
```

**Bad:**
```php
namespace Application\Payment\Port\Output;

use Stripe\Charge;  // Leaking Stripe type!

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): Charge;  // Stripe type!
}
```

**Good:**
```php
namespace Application\Payment\Port\Output;

use Application\Payment\DTO\PaymentResponse;

interface PaymentGatewayInterface
{
    public function charge(PaymentRequest $request): PaymentResponse;  // App DTO
}
```

### 9. Bidirectional Port Dependencies

**Description:** Driving port depends on driven port or vice versa.

**Why Bad:** Creates coupling between ports, harder to evolve independently.

**Detection:**
```bash
Grep: "use.*Port\\\\Output" --glob "**/Port/Input/**/*.php"
Grep: "use.*Port\\\\Input" --glob "**/Port/Output/**/*.php"
```

**Bad:**
```php
namespace Application\Order\Port\Input;

use Domain\Order\Port\Output\OrderRepositoryInterface;  // Output port!

interface CreateOrderUseCaseInterface
{
    public function execute(
        CreateOrderRequest $request,
        OrderRepositoryInterface $repository  // Depending on output port!
    ): CreateOrderResponse;
}
```

**Good:**
```php
namespace Application\Order\Port\Input;

interface CreateOrderUseCaseInterface
{
    public function execute(CreateOrderRequest $request): CreateOrderResponse;
}

// Implementation receives repository via constructor
namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase implements CreateOrderUseCaseInterface
{
    public function __construct(
        private OrderRepositoryInterface $repository  // Injected
    ) {}
}
```

### 10. Missing Error Translation

**Description:** Adapter doesn't translate infrastructure errors to domain errors.

**Why Bad:** Infrastructure exceptions leak into core, tight coupling.

**Detection:**
```bash
Grep: "catch.*Exception.*throw \$" --glob "**/Infrastructure/**/*.php"
Grep: "catch \(" --glob "**/Infrastructure/**/*.php" -A 2 | grep -v "throw new"
```

**Bad:**
```php
namespace Infrastructure\Persistence;

final readonly class DoctrineOrderRepository
{
    public function save(Order $order): void
    {
        // Exception from Doctrine leaks to caller
        $this->em->persist($order);
        $this->em->flush();  // May throw ORMException
    }
}
```

**Good:**
```php
namespace Infrastructure\Persistence;

use Domain\Order\Exception\OrderPersistenceException;
use Doctrine\ORM\ORMException;

final readonly class DoctrineOrderRepository
{
    public function save(Order $order): void
    {
        try {
            $this->em->persist($order);
            $this->em->flush();
        } catch (ORMException $e) {
            throw new OrderPersistenceException(
                "Failed to save order {$order->id()->value}",
                previous: $e
            );
        }
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Core depends on adapter | Critical | Architecture | High |
| Missing port abstraction | Critical | Testability | Medium |
| Business logic in adapter | Critical | Maintainability | Medium |
| Port with impl details | Critical | Coupling | Medium |
| Controller calling repo | Warning | Architecture | Low |
| Framework types in port | Warning | Portability | Medium |
| Monolithic adapter | Warning | Maintainability | Medium |
| Leaky abstraction | Warning | Coupling | Low |
| Bidirectional port deps | Warning | Coupling | Medium |
| Missing error translation | Warning | Encapsulation | Low |

## Detection Summary

```bash
# Quick audit script

echo "=== Core depending on Infrastructure ==="
Grep: "use Infrastructure\\\\" --glob "**/Domain/**/*.php"
Grep: "use Infrastructure\\\\" --glob "**/Application/**/*.php"

echo "=== Missing port abstractions ==="
Grep: "new \\\\Stripe|new \\\\Aws|new \\\\Guzzle" --glob "**/Application/**/*.php"

echo "=== Business logic in adapters ==="
Grep: "if \(.*->|switch \(" --glob "**/Infrastructure/Http/**/*.php"

echo "=== Framework types in ports ==="
Grep: "Symfony\\\\|Laravel\\\\" --glob "**/Port/**/*.php"

echo "=== Leaky abstractions ==="
Grep: "\\\\Doctrine|\\\\Stripe|\\\\Aws" --glob "**/Port/**/*.php"
```
