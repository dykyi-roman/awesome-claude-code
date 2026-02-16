# The Dependency Rule

The fundamental principle of Clean Architecture.

## Definition

> Source code dependencies must only point inward, toward higher-level policies.

Nothing in an inner circle can know anything about something in an outer circle. In particular, the name of something declared in an outer circle must not be mentioned by the code in an inner circle.

## Visualization

```
         External
            │
            ▼
    ┌───────────────┐
    │  Frameworks   │  ← Web, DB, UI
    │  & Drivers    │
    └───────┬───────┘
            │ depends on
            ▼
    ┌───────────────┐
    │   Interface   │  ← Controllers, Gateways, Presenters
    │   Adapters    │
    └───────┬───────┘
            │ depends on
            ▼
    ┌───────────────┐
    │  Application  │  ← Use Cases, Application Services
    │  Business     │
    │  Rules        │
    └───────┬───────┘
            │ depends on
            ▼
    ┌───────────────┐
    │  Enterprise   │  ← Entities, Domain Services, Value Objects
    │  Business     │
    │  Rules        │
    └───────────────┘
            ▲
            │
    NOTHING points outward from here
```

## Practical Implications

### Domain Layer (Enterprise Business Rules)

**Can depend on:** Nothing external

**Cannot depend on:**
- Framework classes (Doctrine, Eloquent, Symfony)
- Infrastructure (database, cache, queues)
- Application layer
- Presentation layer

```php
// CORRECT - Domain is pure PHP
namespace Domain\Order\Entity;

final class Order
{
    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
        private Money $total
    ) {}

    public function applyDiscount(Discount $discount): void
    {
        $this->total = $discount->applyTo($this->total);
    }
}
```

```php
// WRONG - Domain depends on Infrastructure
namespace Domain\Order\Entity;

use Doctrine\ORM\Mapping as ORM;  // VIOLATION!
use Infrastructure\Cache\Redis;    // VIOLATION!

#[ORM\Entity]  // VIOLATION!
class Order
{
    #[ORM\Id]  // VIOLATION!
    private string $id;
}
```

### Application Layer (Application Business Rules)

**Can depend on:** Domain layer only

**Cannot depend on:**
- Framework classes
- Infrastructure implementations
- Presentation layer

```php
// CORRECT - Application depends only on Domain
namespace Application\Order\UseCase;

use Domain\Order\Repository\OrderRepositoryInterface;  // Domain interface
use Domain\Order\Entity\Order;                         // Domain entity
use Domain\Order\ValueObject\OrderId;                  // Domain VO

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders  // Domain interface
    ) {}

    public function execute(ConfirmOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);
        $order->confirm();
        $this->orders->save($order);
    }
}
```

```php
// WRONG - Application depends on Infrastructure
namespace Application\Order\UseCase;

use Doctrine\ORM\EntityManagerInterface;  // VIOLATION!
use Infrastructure\Http\HttpClient;       // VIOLATION!

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private EntityManagerInterface $em  // VIOLATION!
    ) {}
}
```

### Interface Adapters Layer

**Can depend on:** Application layer, Domain layer

**Cannot depend on:** Frameworks (ideally), specific external libraries

```php
// CORRECT - Adapter implements Domain interface
namespace Infrastructure\Persistence;

use Domain\Order\Repository\OrderRepositoryInterface;
use Domain\Order\Entity\Order;
use Doctrine\ORM\EntityManagerInterface;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private EntityManagerInterface $em
    ) {}

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }
}
```

### Frameworks & Drivers Layer

**Can depend on:** All inner layers

This is the outermost layer where all the details live: database, web framework, UI, etc.

## Crossing Boundaries

### The Problem

How can an inner layer call code in an outer layer without depending on it?

```
Use Case needs to save Order
    │
    ▼
Repository Interface (in Domain)  ← Use Case depends on this
    │
    ▼ (at runtime)
Repository Implementation (in Infrastructure)  ← Implements the interface
```

### The Solution: Dependency Inversion

```php
// Domain Layer - defines interface
namespace Domain\Order\Repository;

interface OrderRepositoryInterface
{
    public function findById(OrderId $id): ?Order;
    public function save(Order $order): void;
}
```

```php
// Application Layer - uses interface
namespace Application\Order\UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders  // Depends on abstraction
    ) {}
}
```

```php
// Infrastructure Layer - implements interface
namespace Infrastructure\Persistence;

final readonly class DoctrineOrderRepository implements OrderRepositoryInterface
{
    // Implementation details here
}
```

```php
// Framework Layer - wires everything together
// config/services.yaml (Symfony)
services:
    Domain\Order\Repository\OrderRepositoryInterface:
        class: Infrastructure\Persistence\DoctrineOrderRepository
```

## Detection Patterns

### Checking for Violations

```bash
# Domain importing Infrastructure
Grep: "use Infrastructure\\\\|use Persistence\\\\|use Database\\\\" --glob "**/Domain/**/*.php"

# Domain importing Framework
Grep: "use Doctrine\\\\|use Illuminate\\\\|use Symfony\\\\" --glob "**/Domain/**/*.php"

# Domain importing Presentation
Grep: "use Presentation\\\\|use Controller\\\\|use Api\\\\" --glob "**/Domain/**/*.php"

# Application importing Infrastructure
Grep: "use Infrastructure\\\\|use Persistence\\\\" --glob "**/Application/**/*.php"

# Application importing Framework (except interfaces)
Grep: "use Doctrine\\\\ORM|use Illuminate\\\\Database" --glob "**/Application/**/*.php"

# Application importing Presentation
Grep: "use Presentation\\\\|use Controller\\\\" --glob "**/Application/**/*.php"
```

## Benefits of the Dependency Rule

1. **Testability**: Inner layers can be tested without outer layers
2. **Flexibility**: Outer layers can be replaced without changing inner layers
3. **Independence**: Business rules don't depend on UI, database, or frameworks
4. **Maintainability**: Changes in outer layers don't ripple inward

## Common Misconceptions

### "Domain can use Doctrine Collections"

**Wrong.** Even Doctrine Collections is an external dependency.

```php
// WRONG
namespace Domain\Order\Entity;

use Doctrine\Common\Collections\ArrayCollection;  // VIOLATION!

class Order
{
    private ArrayCollection $lines;  // Coupled to Doctrine
}
```

```php
// CORRECT
namespace Domain\Order\Entity;

class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];  // Pure PHP
}
```

### "It's okay to use Symfony Validator in Domain"

**Wrong.** Domain should validate itself using domain rules.

```php
// WRONG
namespace Domain\Order\ValueObject;

use Symfony\Component\Validator\Constraints as Assert;  // VIOLATION!

class Email
{
    #[Assert\Email]  // Framework in Domain!
    private string $value;
}
```

```php
// CORRECT
namespace Domain\Order\ValueObject;

final readonly class Email
{
    public function __construct(
        public string $value
    ) {
        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidEmailException($value);
        }
    }
}
```

### "Logging is okay in Domain"

**Wrong.** Domain should not know about logging. Use domain events instead.

```php
// WRONG
namespace Domain\Order\Entity;

use Psr\Log\LoggerInterface;  // VIOLATION!

class Order
{
    public function confirm(LoggerInterface $logger): void
    {
        $this->status = OrderStatus::Confirmed;
        $logger->info('Order confirmed');  // Infrastructure concern!
    }
}
```

```php
// CORRECT
namespace Domain\Order\Entity;

class Order
{
    private array $events = [];

    public function confirm(): void
    {
        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id);  // Domain event
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}

// Application layer handles logging via event subscriber
```
