---
name: acc-suggest-testability-improvements
description: Suggests testability improvements for PHP code. Provides DI refactoring suggestions, mock opportunities, interface extraction, testing strategy recommendations.
---

# Testability Improvement Suggestions

Provide actionable suggestions to improve code testability.

## Improvement Categories

### 1. Extract Interface for Dependencies

```php
// BEFORE: Concrete dependency
class PaymentProcessor
{
    public function __construct(
        private StripeGateway $gateway, // Concrete class
    ) {}
}

// Test problem: Must mock StripeGateway internals

// AFTER: Interface dependency
interface PaymentGatewayInterface
{
    public function charge(Money $amount, PaymentMethod $method): PaymentResult;
}

class PaymentProcessor
{
    public function __construct(
        private PaymentGatewayInterface $gateway,
    ) {}
}

// Test benefit: Simple mock implementation
$mockGateway = $this->createMock(PaymentGatewayInterface::class);
$mockGateway->method('charge')->willReturn(PaymentResult::success());
```

### 2. Inject Time/Random Dependencies

```php
// BEFORE: Hard to test time-based logic
class TokenGenerator
{
    public function generate(): Token
    {
        return new Token(
            bin2hex(random_bytes(32)),
            new DateTime('+1 hour'),
        );
    }
}

// AFTER: Injectable dependencies
interface ClockInterface
{
    public function now(): DateTimeImmutable;
}

interface RandomGeneratorInterface
{
    public function bytes(int $length): string;
}

class TokenGenerator
{
    public function __construct(
        private ClockInterface $clock,
        private RandomGeneratorInterface $random,
    ) {}

    public function generate(): Token
    {
        return new Token(
            bin2hex($this->random->bytes(32)),
            $this->clock->now()->modify('+1 hour'),
        );
    }
}

// Test with frozen time
$clock = new FrozenClock(new DateTimeImmutable('2024-01-01 12:00:00'));
$random = new FixedRandom('0123456789abcdef...');
$generator = new TokenGenerator($clock, $random);
$token = $generator->generate();
// Now assertions are deterministic
```

### 3. Create Test Builders

```php
// BEFORE: Tedious test setup
public function testOrderProcessing(): void
{
    $customer = new Customer();
    $customer->setId(1);
    $customer->setName('John');
    $customer->setEmail('john@example.com');
    $customer->setStatus('active');

    $product = new Product();
    $product->setId(1);
    $product->setName('Widget');
    $product->setPrice(new Money(1000, 'USD'));

    $order = new Order();
    $order->setCustomer($customer);
    $order->addItem(new OrderItem($product, 2));
    // ... 20 more lines
}

// AFTER: Fluent builder
public function testOrderProcessing(): void
{
    $order = OrderBuilder::create()
        ->withCustomer(CustomerBuilder::active()->build())
        ->withItem('Widget', 1000, quantity: 2)
        ->build();

    $result = $this->processor->process($order);

    $this->assertTrue($result->isSuccessful());
}
```

### 4. Separate Pure Logic from I/O

```php
// BEFORE: Logic mixed with I/O
class PricingService
{
    public function calculateOrderPrice(int $orderId): Money
    {
        $order = $this->repository->find($orderId); // I/O
        $customer = $this->customerRepo->find($order->getCustomerId()); // I/O
        $rates = $this->taxApi->getRates($customer->getCountry()); // I/O

        // Business logic
        $subtotal = $this->calculateSubtotal($order);
        $discount = $this->applyDiscount($customer, $subtotal);
        $tax = $this->calculateTax($subtotal, $rates);

        return $subtotal->subtract($discount)->add($tax);
    }
}

// AFTER: Pure calculator
final readonly class OrderPriceCalculator
{
    public function calculate(
        Order $order,
        Customer $customer,
        TaxRates $taxRates,
    ): Money {
        $subtotal = $this->calculateSubtotal($order);
        $discount = $this->applyDiscount($customer, $subtotal);
        $tax = $this->calculateTax($subtotal, $taxRates);

        return $subtotal->subtract($discount)->add($tax);
    }
}

// I/O in thin service
final class PricingService
{
    public function __construct(
        private OrderRepository $orderRepo,
        private CustomerRepository $customerRepo,
        private TaxApiInterface $taxApi,
        private OrderPriceCalculator $calculator,
    ) {}

    public function calculateOrderPrice(int $orderId): Money
    {
        $order = $this->orderRepo->find($orderId);
        $customer = $this->customerRepo->find($order->getCustomerId());
        $rates = $this->taxApi->getRates($customer->getCountry());

        return $this->calculator->calculate($order, $customer, $rates);
    }
}

// Now calculator is easily testable without mocks
```

### 5. Use Repository Pattern for Data Access

```php
// BEFORE: Direct database access
class UserService
{
    public function __construct(private PDO $pdo) {}

    public function findActive(): array
    {
        $stmt = $this->pdo->query("SELECT * FROM users WHERE active = 1");
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }
}

// AFTER: Repository interface
interface UserRepositoryInterface
{
    /** @return User[] */
    public function findActive(): array;
    public function findById(int $id): ?User;
    public function save(User $user): void;
}

class UserService
{
    public function __construct(
        private UserRepositoryInterface $repository,
    ) {}

    public function findActive(): array
    {
        return $this->repository->findActive();
    }
}

// In-memory implementation for tests
class InMemoryUserRepository implements UserRepositoryInterface
{
    private array $users = [];

    public function findActive(): array
    {
        return array_filter($this->users, fn($u) => $u->isActive());
    }

    public function givenUser(User $user): void
    {
        $this->users[$user->getId()] = $user;
    }
}
```

### 6. Create Test Doubles

```php
// Fake implementation for testing
final class FakeEmailSender implements EmailSenderInterface
{
    private array $sentEmails = [];

    public function send(Email $email): void
    {
        $this->sentEmails[] = $email;
    }

    public function getSentEmails(): array
    {
        return $this->sentEmails;
    }

    public function assertEmailSentTo(string $address): void
    {
        foreach ($this->sentEmails as $email) {
            if ($email->getTo() === $address) {
                return;
            }
        }
        throw new AssertionError("No email sent to $address");
    }
}
```

### 7. Parameter Objects for Complex Methods

```php
// BEFORE: Many parameters, hard to mock
public function createOrder(
    int $customerId,
    array $items,
    string $shippingMethod,
    string $paymentMethod,
    ?string $couponCode,
    ?string $notes,
): Order {}

// AFTER: DTO with builder
final readonly class CreateOrderRequest
{
    public function __construct(
        public int $customerId,
        public array $items,
        public string $shippingMethod,
        public string $paymentMethod,
        public ?string $couponCode = null,
        public ?string $notes = null,
    ) {}
}

// Test with builder
$request = CreateOrderRequestBuilder::create()
    ->forCustomer(1)
    ->withItem('SKU-001', 2)
    ->withShipping('express')
    ->build();
```

## Implementation Priority

| Improvement | Impact | Effort |
|-------------|--------|--------|
| Extract interface | High | Low |
| Inject time/random | High | Medium |
| Create test builders | Medium | Medium |
| Separate pure logic | High | High |
| Repository pattern | High | Medium |

## Output Format

```markdown
### Testability Improvement: [Description]

**Location:** `file.php:line`
**Type:** [Extract Interface|Inject Dependency|Create Builder|...]
**Impact:** High/Medium/Low

**Current Problem:**
[Why current code is hard to test]

**Suggested Improvement:**
```php
// Improved code
```

**Implementation Steps:**
1. Create interface XxxInterface
2. Update class to depend on interface
3. Create test double/mock
4. Update test

**Testing Benefit:**
[How this makes testing easier]
```
