# Symfony Antipatterns

Common Symfony antipatterns with detection patterns, bad/good examples, and severity ratings.

## 1. Fat Controllers

**Severity:** Warning

Controllers with multiple actions, business logic, or direct infrastructure calls.

**Detection:**
```bash
# Multiple public methods in controllers
Grep: "public function (?!__invoke|__construct)" --glob "**/Controller/**/*.php"
Grep: "public function (?!__invoke|__construct)" --glob "**/Action/**/*.php"

# Business logic in controllers
Grep: "if \\(.*->getStatus|->isValid|->calculate" --glob "**/Controller/**/*.php"
Grep: "EntityManagerInterface|\\$em->|\\$entityManager->" --glob "**/Controller/**/*.php"

# Direct repository calls with logic
Grep: "->findBy|->findOneBy|->createQueryBuilder" --glob "**/Controller/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Controller;

class OrderController
{
    public function create(Request $request, EntityManagerInterface $em): Response
    {
        $data = json_decode($request->getContent(), true);

        // Business logic in controller
        if (count($data['items']) > 50) {
            throw new \RuntimeException('Too many items');
        }

        $order = new Order();
        $order->setCustomerId($data['customer_id']);
        $total = 0;

        foreach ($data['items'] as $item) {
            $product = $em->find(Product::class, $item['product_id']);
            $total += $product->getPrice() * $item['quantity'];
        }

        $order->setTotal($total);
        $em->persist($order);
        $em->flush();

        return new JsonResponse(['id' => $order->getId()], 201);
    }

    public function show(int $id): Response { /* ... */ }
    public function list(): Response { /* ... */ }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Api;

use Command\CreateOrderCommand;
use UseCase\CreateOrderUseCase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/orders', methods: ['POST'])]
final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $data = $request->toArray();

        $orderId = $this->createOrder->execute(new CreateOrderCommand(
            customerId: $data['customer_id'],
            items: $data['items'],
        ));

        return new JsonResponse(['id' => $orderId->value], Response::HTTP_CREATED);
    }
}
```

## 2. Entity Used as DTO

**Severity:** Warning

Passing Doctrine entities directly to templates, serializers, or API responses.

**Detection:**
```bash
# Entity passed to JsonResponse or serializer
Grep: "JsonResponse\\(.*\\$order|->serialize\\(.*\\$order" --glob "**/*.php"
Grep: "->render\\(.*'order'.*=>.*\\$order" --glob "**/Controller/**/*.php"

# Entity with serialization groups (entity doing DTO work)
Grep: "#\\[Groups|@Groups" --glob "**/Entity/**/*.php"
Grep: "#\\[Groups|@Groups" --glob "**/Domain/**/*.php"

# Entity with JsonSerializable
Grep: "implements.*JsonSerializable" --glob "**/Entity/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Serializer\Attribute\Groups;

#[ORM\Entity]
class Order
{
    #[ORM\Id]
    #[Groups(['api'])]
    private string $id;

    #[ORM\Column]
    #[Groups(['api'])]
    private string $status;

    #[ORM\Column]
    private string $internalNote; // Accidentally exposed if Groups misconfigured
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace DTO;

// Explicit DTO for API response — no ORM coupling
final readonly class OrderResponseDTO
{
    public function __construct(
        public string $id,
        public string $status,
        public int $totalAmount,
        public string $currency,
    ) {}

    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->id()->value,
            status: $order->status()->value,
            totalAmount: $order->total()->cents(),
            currency: $order->total()->currency()->value,
        );
    }
}
```

## 3. Doctrine in Domain Layer

**Severity:** Critical

Doctrine ORM annotations, attributes, or classes used inside the Domain layer.

**Detection:**
```bash
# Doctrine imports in Domain
Grep: "use Doctrine\\\\" --glob "**/Domain/**/*.php"

# ORM attributes in Domain
Grep: "#\\[ORM\\\\" --glob "**/Domain/**/*.php"

# Doctrine Collections in Domain
Grep: "ArrayCollection|PersistentCollection|Collection" --glob "**/Domain/**/*.php"
Grep: "use Doctrine\\\\Common\\\\Collections" --glob "**/Domain/**/*.php"

# Doctrine repository base class in Domain
Grep: "extends ServiceEntityRepository" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Doctrine\Common\Collections\ArrayCollection;
use Doctrine\Common\Collections\Collection;
use Doctrine\ORM\Mapping as ORM;

#[ORM\Entity(repositoryClass: DoctrineOrderRepository::class)]
#[ORM\Table(name: 'orders')]
class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;

    #[ORM\OneToMany(targetEntity: OrderLine::class, mappedBy: 'order')]
    private Collection $lines;

    public function __construct()
    {
        $this->lines = new ArrayCollection();
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Entity;

// Pure PHP — mapping lives in Infrastructure as XML
final class Order
{
    /** @var array<OrderLine> */
    private array $lines = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
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
```

## 4. Service Locator Usage

**Severity:** Critical

Using `ContainerInterface::get()` to fetch services instead of constructor injection.

**Detection:**
```bash
# ContainerInterface in services
Grep: "ContainerInterface" --glob "src/**/*.php" | grep -v "Compiler"
Grep: "->get\\('" --glob "src/**/*.php"
Grep: "->get\\([A-Z]" --glob "src/**/*.php"

# ContainerAware base classes
Grep: "extends ContainerAware|ContainerAwareTrait" --glob "src/**/*.php"

# Direct container access
Grep: "\\$this->container->get" --glob "src/**/*.php"
Grep: "static::getContainer" --glob "src/**/*.php" | grep -v "Test"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Service;

use Psr\Container\ContainerInterface;

class OrderService
{
    public function __construct(
        private ContainerInterface $container,
    ) {}

    public function process(string $orderId): void
    {
        // Hidden dependencies — impossible to know from constructor
        $repo = $this->container->get(OrderRepositoryInterface::class);
        $mailer = $this->container->get(MailerInterface::class);
        $logger = $this->container->get(LoggerInterface::class);

        $order = $repo->findById($orderId);
        // ...
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace UseCase;

use Repository\OrderRepositoryInterface;
use Psr\Log\LoggerInterface;

final readonly class ProcessOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private MailerInterface $mailer,
        private LoggerInterface $logger,
    ) {}

    public function execute(ProcessOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);
        // All dependencies are explicit and testable
    }
}
```

## 5. Tight Coupling to Framework

**Severity:** Warning

Application or Domain code that cannot function without Symfony.

**Detection:**
```bash
# Symfony in Application layer
Grep: "use Symfony\\\\" --glob "**/Application/**/*.php" | grep -v "Messenger\\\\Attribute"

# Symfony in Domain layer
Grep: "use Symfony\\\\" --glob "**/Domain/**/*.php"

# AbstractController inheritance (couples to full Symfony stack)
Grep: "extends AbstractController" --glob "src/**/*.php"

# Framework-specific base classes
Grep: "extends Controller|extends AbstractController" --glob "src/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Service;

use Symfony\Component\HttpFoundation\RequestStack;
use Symfony\Component\Security\Core\Security;
use Symfony\Contracts\Cache\CacheInterface;

// Application service coupled to Symfony HTTP, Security, Cache
final readonly class OrderContextService
{
    public function __construct(
        private RequestStack $requestStack,
        private Security $security,
        private CacheInterface $cache,
    ) {}
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Service;

use Cache\CacheInterface;
use Security\CurrentUserProviderInterface;

// Application service depends on domain interfaces, not framework
final readonly class OrderContextService
{
    public function __construct(
        private CurrentUserProviderInterface $currentUser,
        private CacheInterface $cache,
    ) {}
}
```

## 6. Missing Input Validation at Boundaries

**Severity:** Warning

No validation on incoming request data before passing to Application layer.

**Detection:**
```bash
# Direct array access without validation
Grep: "\\$request->get\\(|\\$request->query->get\\(" --glob "**/Controller/**/*.php"
Grep: "\\['[a-z]" --glob "**/Controller/**/*.php" | grep "request->toArray"

# Missing Validator usage in Presentation
Grep: "ValidatorInterface" --glob "**/Presentation/**/*.php" --output_mode count
```

## 7. Workflow Logic in Entity

**Severity:** Warning

Manual `if/switch` chains on status strings instead of using Symfony Workflow component.

**Detection:**
```bash
# Manual status transitions
Grep: "->setStatus\\(|->status\\s*=" --glob "**/Domain/**/*.php"
Grep: "if.*->getStatus\\(\\).*===|switch.*->status" --glob "**/Domain/**/*.php"

# String status constants (should be enums)
Grep: "const STATUS_|const STATE_" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Entity;

// VIOLATION: Manual state machine with error-prone string matching
class Order
{
    private string $status = 'draft';

    public function ship(): void
    {
        if ($this->status !== 'confirmed' && $this->status !== 'paid') {
            throw new \RuntimeException('Cannot ship');
        }
        $this->status = 'shipped';
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use ValueObject\OrderStatus;

// Domain entity with enum status; transitions managed by Workflow component
final class Order
{
    private OrderStatus $status;

    public function __construct(
        private readonly OrderId $id,
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function status(): OrderStatus { return $this->status; }
    public function getStatus(): string { return $this->status->value; }
    public function setStatus(string $status): void { $this->status = OrderStatus::from($status); }
}
```

## 8. Security Logic in Domain

**Severity:** Critical

Domain entity implementing `Symfony\Component\Security\Core\User\UserInterface` directly.

**Detection:**
```bash
# Symfony Security in Domain
Grep: "use Symfony\\\\Component\\\\Security" --glob "**/Domain/**/*.php"
Grep: "implements.*UserInterface" --glob "**/Domain/**/*.php"
Grep: "PasswordAuthenticatedUserInterface" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Symfony\Component\Security\Core\User\UserInterface;
use Symfony\Component\Security\Core\User\PasswordAuthenticatedUserInterface;

// VIOLATION: Domain coupled to Symfony Security
class User implements UserInterface, PasswordAuthenticatedUserInterface
{
    public function getRoles(): array { return $this->roles; }
    public function eraseCredentials(): void {}
    public function getUserIdentifier(): string { return $this->email; }
    public function getPassword(): ?string { return $this->password; }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Entity;

// Pure domain aggregate — security adapter in Infrastructure
final class User
{
    public function __construct(
        private readonly UserId $id,
        private readonly Email $email,
        private HashedPassword $password,
    ) {}
}
```

See `security.md` for the full Infrastructure `SecurityUser` adapter pattern.

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Doctrine in Domain | Critical | Architecture | High |
| Service Locator | Critical | Testability | Medium |
| Security Logic in Domain | Critical | Architecture | Medium |
| Fat Controllers | Warning | Maintainability | Medium |
| Entity as DTO | Warning | Security, Coupling | Medium |
| Tight Framework Coupling | Warning | Portability | High |
| Missing Validation | Warning | Security | Low |
| Workflow Logic in Entity | Warning | Maintainability | Medium |

## Quick Detection Script

Run all checks at once:

```bash
# Critical violations
Grep: "use Doctrine\\\\" --glob "**/Domain/**/*.php"
Grep: "use Symfony\\\\" --glob "**/Domain/**/*.php"
Grep: "ContainerInterface" --glob "src/**/*.php"
Grep: "#\\[ORM\\\\" --glob "**/Domain/**/*.php"
Grep: "implements.*UserInterface" --glob "**/Domain/**/*.php"

# Warning violations
Grep: "public function (?!__invoke|__construct)" --glob "**/Controller/**/*.php"
Grep: "#\\[Groups" --glob "**/Entity/**/*.php"
Grep: "extends AbstractController" --glob "src/**/*.php"
Grep: "extends ServiceEntityRepository" --glob "**/Domain/**/*.php"
Grep: "->setStatus\\(" --glob "**/Domain/**/*.php"
```
