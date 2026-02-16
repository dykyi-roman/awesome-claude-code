# Dependency Inversion Principle (DIP) Patterns

## Definition

High-level modules should not depend on low-level modules. Both should depend on abstractions. Abstractions should not depend on details. Details should depend on abstractions.

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| `new ConcreteClass()` in methods | Code search | CRITICAL |
| Static calls to concrete classes | Code search | CRITICAL |
| Type hints to concrete classes | Code search | WARNING |
| No constructor injection | Class analysis | WARNING |
| Service locator usage | Code search | WARNING |

### Compliance Signs

- Constructor injection only
- Interface/abstract type hints
- No `new` in business logic
- Factory pattern for object creation
- DI container configuration

## Refactoring Patterns

### Constructor Injection

```php
<?php

declare(strict_types=1);

// BEFORE: Direct dependencies
final class OrderService
{
    public function process(Order $order): void
    {
        $validator = new OrderValidator();           // DIP VIOLATION
        $repository = new DoctrineOrderRepository(); // DIP VIOLATION
        $mailer = Mailer::getInstance();             // DIP VIOLATION (static)

        $validator->validate($order);
        $repository->save($order);
        $mailer->send(new OrderConfirmation($order));
    }
}

// AFTER: Injected abstractions
final readonly class OrderService
{
    public function __construct(
        private OrderValidator $validator,
        private OrderRepository $orders,
        private Mailer $mailer,
    ) {}

    public function process(Order $order): void
    {
        $this->validator->validate($order);
        $this->orders->save($order);
        $this->mailer->send(new OrderConfirmation($order));
    }
}

// Abstractions
interface OrderRepository
{
    public function save(Order $order): void;
    public function find(OrderId $id): ?Order;
}

interface Mailer
{
    public function send(Email $email): void;
}
```

### Interface Extraction

```php
<?php

declare(strict_types=1);

// BEFORE: Depending on concrete class
final class ReportGenerator
{
    public function __construct(
        private PdfLibrary $pdf, // Concrete dependency
    ) {}

    public function generate(ReportData $data): string
    {
        return $this->pdf->render($data->toArray());
    }
}

// AFTER: Abstraction layer
interface DocumentRenderer
{
    public function render(array $data): string;
}

final readonly class PdfRenderer implements DocumentRenderer
{
    public function __construct(
        private PdfLibrary $pdf,
    ) {}

    public function render(array $data): string
    {
        return $this->pdf->render($data);
    }
}

final readonly class HtmlRenderer implements DocumentRenderer
{
    public function render(array $data): string
    {
        return $this->twig->render('report.html.twig', $data);
    }
}

final readonly class ReportGenerator
{
    public function __construct(
        private DocumentRenderer $renderer, // Abstraction
    ) {}

    public function generate(ReportData $data): string
    {
        return $this->renderer->render($data->toArray());
    }
}
```

### Factory for Complex Creation

```php
<?php

declare(strict_types=1);

// BEFORE: Complex object creation in business logic
final class OrderProcessor
{
    public function process(OrderData $data): Order
    {
        // DIP VIOLATION: Creating complex objects
        $order = new Order(
            new OrderId(Uuid::uuid4()->toString()),
            new CustomerId($data->customerId),
            new Money($data->amount, new Currency($data->currency)),
            new Address(/* ... */),
        );

        // ...
    }
}

// AFTER: Factory abstraction
interface OrderFactory
{
    public function create(OrderData $data): Order;
}

final readonly class DefaultOrderFactory implements OrderFactory
{
    public function __construct(
        private IdGenerator $idGenerator,
    ) {}

    public function create(OrderData $data): Order
    {
        return new Order(
            $this->idGenerator->generate(),
            new CustomerId($data->customerId),
            Money::fromArray($data->amount, $data->currency),
            Address::fromArray($data->address),
        );
    }
}

final readonly class OrderProcessor
{
    public function __construct(
        private OrderFactory $orderFactory,
        private OrderRepository $orders,
    ) {}

    public function process(OrderData $data): Order
    {
        $order = $this->orderFactory->create($data);
        $this->orders->save($order);

        return $order;
    }
}
```

### Port/Adapter Pattern

```php
<?php

declare(strict_types=1);

// Port (abstraction in Domain/Application layer)
namespace Domain\Port;

interface PaymentGateway
{
    public function charge(PaymentRequest $request): PaymentResult;
    public function refund(TransactionId $id): RefundResult;
}

// Adapter (implementation in Infrastructure layer)
namespace Infrastructure\Adapter;

use Domain\Port\PaymentGateway;

final readonly class StripePaymentGateway implements PaymentGateway
{
    public function __construct(
        private StripeClient $stripe,
    ) {}

    public function charge(PaymentRequest $request): PaymentResult
    {
        $stripeCharge = $this->stripe->charges->create([
            'amount' => $request->amount->cents,
            'currency' => $request->currency->code,
            'source' => $request->token,
        ]);

        return new PaymentResult(
            new TransactionId($stripeCharge->id),
            $stripeCharge->status === 'succeeded',
        );
    }

    public function refund(TransactionId $id): RefundResult
    {
        $refund = $this->stripe->refunds->create([
            'charge' => $id->value,
        ]);

        return new RefundResult(
            $refund->status === 'succeeded',
        );
    }
}

// Application layer depends on Port, not Adapter
final readonly class ProcessPaymentHandler
{
    public function __construct(
        private PaymentGateway $gateway, // Port interface
    ) {}

    public function __invoke(ProcessPaymentCommand $command): PaymentResult
    {
        return $this->gateway->charge($command->toPaymentRequest());
    }
}
```

### Removing Static Dependencies

```php
<?php

declare(strict_types=1);

// BEFORE: Static dependencies
final class UserService
{
    public function register(UserData $data): User
    {
        $id = Uuid::uuid4()->toString();    // Static call
        $now = Carbon::now();                // Static call
        $config = Config::get('users.max'); // Static call

        return new User($id, $data->email, $now);
    }
}

// AFTER: Injected services
interface IdGenerator
{
    public function generate(): string;
}

interface Clock
{
    public function now(): DateTimeImmutable;
}

interface ConfigReader
{
    public function get(string $key, mixed $default = null): mixed;
}

final readonly class UuidGenerator implements IdGenerator
{
    public function generate(): string
    {
        return Uuid::uuid4()->toString();
    }
}

final readonly class SystemClock implements Clock
{
    public function now(): DateTimeImmutable
    {
        return new DateTimeImmutable();
    }
}

final readonly class UserService
{
    public function __construct(
        private IdGenerator $idGenerator,
        private Clock $clock,
        private ConfigReader $config,
    ) {}

    public function register(UserData $data): User
    {
        return new User(
            new UserId($this->idGenerator->generate()),
            Email::fromString($data->email),
            $this->clock->now(),
        );
    }
}
```

## DDD Application

### Domain Layer Dependencies

```php
<?php

declare(strict_types=1);

// Domain defines the abstraction (Port)
namespace Domain\Repository;

interface OrderRepository
{
    public function find(OrderId $id): ?Order;
    public function save(Order $order): void;
    public function nextIdentity(): OrderId;
}

// Domain service depends on abstraction
namespace Domain\Service;

final readonly class OrderDomainService
{
    public function __construct(
        private OrderRepository $orders,
    ) {}

    public function placeOrder(CustomerId $customerId, Cart $cart): Order
    {
        $order = Order::place(
            $this->orders->nextIdentity(),
            $customerId,
            $cart->items(),
        );

        $this->orders->save($order);

        return $order;
    }
}

// Infrastructure provides implementation (Adapter)
namespace Infrastructure\Persistence;

use Domain\Repository\OrderRepository;

final readonly class DoctrineOrderRepository implements OrderRepository
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function find(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id->value);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    public function nextIdentity(): OrderId
    {
        return new OrderId(Uuid::uuid4()->toString());
    }
}
```

### Clean Architecture Dependency Flow

```
┌────────────────────────────────────────────────────────┐
│                    Frameworks & UI                      │
│                  (Controllers, CLI)                     │
├────────────────────────────────────────────────────────┤
│                      Adapters                           │
│         (Repositories, Gateways, Presenters)           │
├────────────────────────────────────────────────────────┤
│                   Application Layer                     │
│                (Use Cases, Services)                    │
├────────────────────────────────────────────────────────┤
│                    Domain Layer                         │
│        (Entities, Value Objects, Interfaces)           │
└────────────────────────────────────────────────────────┘

Dependencies point INWARD only:
- Frameworks depend on Adapters
- Adapters depend on Application
- Application depends on Domain
- Domain depends on NOTHING external
```

## DI Container Configuration

```php
<?php

// Symfony services.yaml
// services:
//   _defaults:
//     autowire: true
//     autoconfigure: true
//
//   App\Domain\Repository\OrderRepository:
//     class: App\Infrastructure\Persistence\DoctrineOrderRepository
//
//   App\Domain\Port\PaymentGateway:
//     class: App\Infrastructure\Adapter\StripePaymentGateway

// Laravel AppServiceProvider
final class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(
            OrderRepository::class,
            DoctrineOrderRepository::class,
        );

        $this->app->bind(
            PaymentGateway::class,
            StripePaymentGateway::class,
        );
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| `new` in business logic | 0 | 1-2 | >2 |
| Static calls | 0 | 1-2 | >2 |
| Concrete type hints | 0 | 1-3 | >3 |
| Missing DI | 0 | 0 | >0 |
