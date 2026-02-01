# Interface Segregation Principle (ISP) Patterns

## Definition

Clients should not be forced to depend on interfaces they do not use. Many specific interfaces are better than one general-purpose interface.

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| Interface >5 methods | Interface analysis | WARNING |
| Empty implementations | Code search | CRITICAL |
| "Not supported" methods | Code search | CRITICAL |
| Generic interface names | Name analysis | WARNING |
| Unused injected methods | Usage analysis | WARNING |

### Compliance Signs

- Interfaces have 1-5 focused methods
- All methods used by all implementers
- Role-based interface names
- Clients only see methods they need

## Refactoring Patterns

### Split Fat Interface

```php
<?php

declare(strict_types=1);

// BEFORE: Fat interface
interface UserService
{
    public function find(UserId $id): ?User;
    public function findByEmail(Email $email): ?User;
    public function findAll(): array;
    public function save(User $user): void;
    public function delete(User $user): void;
    public function updatePassword(User $user, Password $password): void;
    public function resetPassword(Email $email): void;
    public function verifyEmail(User $user, Token $token): void;
    public function sendVerificationEmail(User $user): void;
    public function export(Format $format): string;
    public function import(string $data): void;
}

// Client only needs find - but depends on entire interface
final readonly class UserProfileController
{
    public function __construct(
        private UserService $userService, // Depends on 11 methods, uses 1
    ) {}

    public function show(UserId $id): Response
    {
        $user = $this->userService->find($id);
        // ...
    }
}

// AFTER: Segregated interfaces
interface UserReader
{
    public function find(UserId $id): ?User;
    public function findByEmail(Email $email): ?User;
}

interface UserWriter
{
    public function save(User $user): void;
    public function delete(User $user): void;
}

interface UserPasswordManager
{
    public function updatePassword(User $user, Password $password): void;
    public function resetPassword(Email $email): void;
}

interface UserEmailVerifier
{
    public function verifyEmail(User $user, Token $token): void;
    public function sendVerificationEmail(User $user): void;
}

interface UserDataExporter
{
    public function export(Format $format): string;
    public function import(string $data): void;
}

// Compose when needed
interface UserRepository extends UserReader, UserWriter {}

// Client depends only on what it needs
final readonly class UserProfileController
{
    public function __construct(
        private UserReader $users, // Depends on 2 methods, uses 1
    ) {}

    public function show(UserId $id): Response
    {
        $user = $this->users->find($id);
        // ...
    }
}
```

### Role Interfaces

```php
<?php

declare(strict_types=1);

// BEFORE: One interface, multiple roles
interface Document
{
    public function getContent(): string;
    public function setContent(string $content): void;
    public function print(): void;
    public function fax(): void;
    public function scan(): void;
}

// Read-only document can't implement all
final class ReadOnlyDocument implements Document
{
    public function setContent(string $content): void
    {
        throw new NotSupportedException(); // ISP VIOLATION
    }

    public function print(): void
    {
        throw new NotSupportedException(); // ISP VIOLATION
    }
    // ...
}

// AFTER: Role-based interfaces
interface Readable
{
    public function getContent(): string;
}

interface Writable
{
    public function setContent(string $content): void;
}

interface Printable
{
    public function print(): void;
}

interface Faxable
{
    public function fax(): void;
}

interface Scannable
{
    public function scan(): void;
}

// Compose only needed roles
final readonly class ReadOnlyDocument implements Readable
{
    public function getContent(): string
    {
        return $this->content;
    }
}

final class EditableDocument implements Readable, Writable, Printable
{
    public function getContent(): string { /* ... */ }
    public function setContent(string $content): void { /* ... */ }
    public function print(): void { /* ... */ }
}
```

### Command/Query Separation

```php
<?php

declare(strict_types=1);

// BEFORE: Mixed read/write interface
interface OrderRepository
{
    public function find(OrderId $id): ?Order;
    public function findByCustomer(CustomerId $id): array;
    public function findPending(): array;
    public function save(Order $order): void;
    public function delete(Order $order): void;
    public function count(): int;
    public function sumTotal(): Money;
}

// AFTER: Separated by intent
interface OrderReader
{
    public function find(OrderId $id): ?Order;
    public function findByCustomer(CustomerId $id): array;
    public function findPending(): array;
}

interface OrderWriter
{
    public function save(Order $order): void;
    public function delete(Order $order): void;
}

interface OrderStats
{
    public function count(): int;
    public function sumTotal(): Money;
}

// Query handler only needs reader
final readonly class GetPendingOrdersHandler
{
    public function __construct(
        private OrderReader $orders,
    ) {}

    public function __invoke(): array
    {
        return $this->orders->findPending();
    }
}

// Command handler only needs writer
final readonly class DeleteOrderHandler
{
    public function __construct(
        private OrderWriter $orders,
    ) {}

    public function __invoke(DeleteOrderCommand $command): void
    {
        $this->orders->delete($command->orderId);
    }
}
```

### Adapter Pattern for Legacy

```php
<?php

declare(strict_types=1);

// Legacy fat interface (cannot change)
interface LegacyPaymentGateway
{
    public function charge(array $data): array;
    public function refund(string $transactionId): array;
    public function void(string $transactionId): array;
    public function getBalance(): float;
    public function getTransactionHistory(): array;
    public function updateMerchantInfo(array $info): void;
    public function generateReport(string $format): string;
}

// Create focused interfaces
interface PaymentProcessor
{
    public function charge(PaymentRequest $request): PaymentResult;
    public function refund(TransactionId $id): RefundResult;
}

interface BalanceChecker
{
    public function getBalance(): Money;
}

// Adapter implements only what's needed
final readonly class PaymentProcessorAdapter implements PaymentProcessor
{
    public function __construct(
        private LegacyPaymentGateway $gateway,
    ) {}

    public function charge(PaymentRequest $request): PaymentResult
    {
        $result = $this->gateway->charge($request->toArray());
        return PaymentResult::fromArray($result);
    }

    public function refund(TransactionId $id): RefundResult
    {
        $result = $this->gateway->refund($id->value);
        return RefundResult::fromArray($result);
    }
}
```

## DDD Application

### Repository Interface Segregation

```php
<?php

declare(strict_types=1);

// Read-side (queries)
interface UserFinder
{
    public function find(UserId $id): ?User;
    public function findByEmail(Email $email): ?User;
}

// Write-side (commands)
interface UserStore
{
    public function save(User $user): void;
    public function remove(User $user): void;
}

// Event sourcing scenarios
interface UserEventStore
{
    public function append(UserId $id, DomainEvent ...$events): void;
    public function getEvents(UserId $id): array;
}

// Compose for full repository
interface UserRepository extends UserFinder, UserStore {}

// CQRS: Different implementations
final readonly class DoctrineUserFinder implements UserFinder { /* ... */ }
final readonly class DoctrineUserStore implements UserStore { /* ... */ }
final readonly class EventStoreUserRepository implements UserEventStore { /* ... */ }
```

### Domain Service Interfaces

```php
<?php

declare(strict_types=1);

// Focused domain service interfaces
interface PriceCalculator
{
    public function calculate(Order $order): Money;
}

interface DiscountApplier
{
    public function apply(Order $order, Discount $discount): Order;
}

interface TaxCalculator
{
    public function calculate(Money $amount, TaxRate $rate): Money;
}

// Application service composes what it needs
final readonly class OrderPricingService
{
    public function __construct(
        private PriceCalculator $priceCalculator,
        private DiscountApplier $discountApplier,
        private TaxCalculator $taxCalculator,
    ) {}

    public function calculateTotal(Order $order): Money
    {
        $basePrice = $this->priceCalculator->calculate($order);
        $discounted = $this->discountApplier->apply($order, $order->discount);
        $tax = $this->taxCalculator->calculate($discounted->total, $order->taxRate);

        return $discounted->total->add($tax);
    }
}
```

## Interface Design Guidelines

| Guideline | Description |
|-----------|-------------|
| Single purpose | Each interface represents one capability |
| Client-driven | Design interfaces from client perspective |
| Cohesive methods | All methods relate to same abstraction |
| Composable | Interfaces can extend other interfaces |
| Testable | Small interfaces are easier to mock |

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| Methods per interface | 1-5 | 6-7 | >7 |
| Empty implementations | 0 | 0 | >0 |
| NotSupportedException | 0 | 0 | >0 |
| Unused dependencies | 0 | 1-2 | >2 |
