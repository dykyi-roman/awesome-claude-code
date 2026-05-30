---
name: check-context-communication
description: Audits Bounded Context communication patterns. Checks Context Map relationships (Shared Kernel, ACL, Open Host), event vs direct calls, and anti-corruption layer usage.
---

# Context Communication Audit

Analyze PHP code for proper Bounded Context communication following DDD Context Map patterns.

## Detection Patterns

### 1. Direct Cross-Context Dependency

```php
// CRITICAL: Order context directly uses User context internals
namespace Order\Application;

use App\User\Domain\User;           // Cross-context import!
use App\User\Domain\UserRepository;  // Cross-context import!

final readonly class CreateOrderUseCase
{
    public function __construct(
        private UserRepository $userRepo, // Depends on another context's repository
    ) {}

    public function execute(CreateOrderCommand $command): void
    {
        $user = $this->userRepo->find($command->userId());
        $order = Order::create($user->email(), $user->shippingAddress());
        // Tight coupling — if User changes, Order breaks
    }
}

// CORRECT: Anti-Corruption Layer
namespace ACL;

final readonly class UserProfileAdapter implements OrderContext\UserProfilePort
{
    public function __construct(
        private UserContextApi $userApi, // Interface, not concrete
    ) {}

    public function getShippingInfo(UserId $userId): ShippingInfo
    {
        $userData = $this->userApi->getUserProfile($userId);
        return new ShippingInfo(  // Map to Order context's own model
            address: Address::fromArray($userData['address']),
            name: $userData['name'],
        );
    }
}
```

### 2. Shared Kernel Misuse

```php
// ANTIPATTERN: Too much shared between contexts
namespace Domain;

class User { }         // Full entity in Shared — too much!
class Order { }        // Full entity in Shared — too much!
class Money { }        // OK — genuine shared concept
class Currency { }     // OK — genuine shared concept
class EventId { }      // OK — infrastructure concern

// CORRECT: Minimal Shared Kernel
namespace Domain;

// Only truly shared, stable concepts
final readonly class Money { }
final readonly class Currency { }
final readonly class EventId { }
final readonly class AggregateId { }
```

### 3. Synchronous Cross-Context Call

```php
// ANTIPATTERN: Synchronous call between contexts
namespace Order\Application;

final readonly class CompleteOrderUseCase
{
    public function execute(CompleteOrderCommand $command): void
    {
        $order = $this->orderRepo->find($command->orderId());
        $order->complete();
        $this->orderRepo->save($order);

        // Synchronous cross-context calls!
        $this->inventoryService->reserve($order->items());     // Inventory context
        $this->paymentService->capture($order->paymentId());   // Payment context
        $this->shippingService->schedule($order->address());   // Shipping context
        // If any fails → partial state + coupling
    }
}

// CORRECT: Event-driven cross-context communication
final readonly class CompleteOrderUseCase
{
    public function execute(CompleteOrderCommand $command): void
    {
        $order = $this->orderRepo->find($command->orderId());
        $order->complete(); // Records OrderCompleted domain event
        $this->orderRepo->save($order);
        // Events dispatched asynchronously:
        // OrderCompleted → InventoryContext (reserve)
        // OrderCompleted → PaymentContext (capture)
        // OrderCompleted → ShippingContext (schedule)
    }
}
```

### 4. Missing Anti-Corruption Layer

```php
// ANTIPATTERN: External API model used directly in domain
namespace Order\Domain;

use Stripe\PaymentIntent;  // External API model in domain!

final class Payment
{
    public function __construct(
        private PaymentIntent $stripePayment, // Stripe model in domain
    ) {}

    public function isSuccessful(): bool
    {
        return $this->stripePayment->status === 'succeeded'; // Coupled to Stripe
    }
}

// CORRECT: ACL translates external to domain
namespace ACL;

final readonly class StripePaymentAdapter implements PaymentGateway
{
    public function charge(Money $amount): PaymentResult
    {
        $intent = $this->stripe->paymentIntents->create([...]);
        return PaymentResult::from(   // Domain model
            status: $this->mapStatus($intent->status),
            transactionId: new TransactionId($intent->id),
        );
    }

    private function mapStatus(string $stripeStatus): PaymentStatus
    {
        return match ($stripeStatus) {
            'succeeded' => PaymentStatus::COMPLETED,
            'requires_action' => PaymentStatus::PENDING,
            default => PaymentStatus::FAILED,
        };
    }
}
```

### 5. Event Leaking Internal State

```php
// ANTIPATTERN: Domain event exposes aggregate internals
final readonly class OrderCompleted implements DomainEvent
{
    public function __construct(
        public Order $order,  // Full aggregate in event!
        // Other contexts can access all internal state
    ) {}
}

// CORRECT: Event contains only necessary data
final readonly class OrderCompleted implements DomainEvent
{
    public function __construct(
        public OrderId $orderId,
        public UserId $userId,
        public Money $total,
        public \DateTimeImmutable $occurredAt,
    ) {}
}
```

### 6. No Context Boundary in Namespace

```php
// ANTIPATTERN: Flat structure without context boundaries
src/
├── Entity/
│   ├── User.php
│   ├── Order.php
│   └── Product.php     // All entities mixed together!
├── Repository/
│   ├── UserRepository.php
│   └── OrderRepository.php

// CORRECT: Bounded Context boundaries in namespace
src/
├── UserManagement/     // Bounded Context
│   ├── Domain/
│   ├── Application/
│   └── Infrastructure/
├── OrderProcessing/    // Bounded Context
│   ├── Domain/
│   ├── Application/
│   └── Infrastructure/
```

## Grep Patterns

```bash
# Cross-context imports
Grep: "use App\\\\[A-Z][a-z]+\\\\Domain" --glob "**/Application/**/*.php"
# Check if import is from different context than file's context

# Direct service calls across contexts
Grep: "Service->|Client->|Api->" --glob "**/Application/**/*UseCase.php"

# External models in domain
Grep: "use Stripe\\\\|use Twilio\\\\|use AWS\\\\|use Google\\\\" --glob "**/Domain/**/*.php"

# Full aggregate in events
Grep: "public.*Entity.*\$|public.*Aggregate.*\$" --glob "**/Domain/**/*Event*.php"

# Shared Kernel size
Glob: **/Shared/Domain/**/*.php
# Count files — if > 10, probably too much shared

# Missing ACL
Grep: "implements.*Port|implements.*Gateway" --glob "**/Infrastructure/ACL/**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Direct cross-context domain dependency | 🔴 Critical |
| External model in domain layer | 🔴 Critical |
| Synchronous cross-context calls | 🟠 Major |
| Oversized Shared Kernel | 🟠 Major |
| Event leaking aggregate internals | 🟠 Major |
| Missing ACL for external service | 🟡 Minor |

## Context Map Patterns Reference

| Pattern | When to Use |
|---------|------------|
| **Shared Kernel** | Two teams co-own small shared model (Money, EventId) |
| **Anti-Corruption Layer** | Protect domain from external/legacy models |
| **Open Host Service** | Provide well-defined API for consumers |
| **Published Language** | Shared event schema (JSON Schema, Protobuf) |
| **Customer/Supplier** | Upstream provides, downstream consumes |
| **Conformist** | Downstream adopts upstream model (not recommended) |

## Output Format

```markdown
### Context Communication: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Contexts:** [Source Context] → [Target Context]
**Pattern Violated:** [Context Map pattern]

**Issue:**
[Description of the communication violation]

**Impact:**
- Coupling between bounded contexts
- Cannot deploy/evolve contexts independently

**Code:**
```php
// Cross-context violation
```

**Fix:**
```php
// Proper context communication
```
```
