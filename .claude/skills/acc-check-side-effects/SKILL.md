---
name: acc-check-side-effects
description: Analyzes PHP code for side effect issues. Detects state mutation, global access, static method calls, I/O operations mixed with business logic.
---

# Side Effect Check

Analyze PHP code for side effects that reduce testability.

## Side Effect Types

1. **State mutation** — Changing object/array state
2. **Global access** — Reading/writing global variables
3. **I/O operations** — File, network, database
4. **Output** — echo, print, header
5. **External service calls** — API, queue, cache

## Detection Patterns

### 1. State Mutation

```php
// SIDE EFFECT: Mutates input
public function normalize(array &$data): void
{
    $data['name'] = trim($data['name']);
    $data['email'] = strtolower($data['email']);
}

// PURE: Returns new array
public function normalize(array $data): array
{
    return [
        'name' => trim($data['name']),
        'email' => strtolower($data['email']),
    ];
}

// SIDE EFFECT: Mutates object
public function complete(Order $order): void
{
    $order->setStatus('completed');
    $order->setCompletedAt(new DateTime());
}

// BETTER: Command pattern or event
public function complete(Order $order): OrderCompletedEvent
{
    return new OrderCompletedEvent($order->getId(), new DateTimeImmutable());
}
```

### 2. Global Variable Access

```php
// SIDE EFFECT: Reads global
function getUser(): ?User
{
    global $currentUser;
    return $currentUser;
}

// SIDE EFFECT: Superglobal access
public function handleRequest(): Response
{
    $userId = $_SESSION['user_id']; // Hidden dependency
    $data = $_POST; // Hidden input
}

// BETTER: Explicit parameters
public function handleRequest(Session $session, Request $request): Response
{
    $userId = $session->get('user_id');
    $data = $request->all();
}
```

### 3. Static Property Access

```php
// SIDE EFFECT: Static state
class Counter
{
    private static int $count = 0;

    public static function increment(): void
    {
        self::$count++; // Shared mutable state
    }

    public static function getCount(): int
    {
        return self::$count;
    }
}

// BETTER: Instance state
class Counter
{
    private int $count = 0;

    public function increment(): void
    {
        $this->count++;
    }
}
```

### 4. I/O in Business Logic

```php
// SIDE EFFECT: Mixed concerns
public function calculateDiscount(int $userId): float
{
    $user = $this->db->query("SELECT * FROM users WHERE id = ?", [$userId]); // I/O
    $orderCount = $this->db->query("SELECT COUNT(*) FROM orders WHERE user_id = ?", [$userId]); // I/O

    // Pure calculation
    if ($orderCount > 100) return 0.20;
    if ($orderCount > 50) return 0.15;
    return 0.10;
}

// BETTER: Separated concerns
// Pure function
public function calculateDiscountRate(int $orderCount): float
{
    return match(true) {
        $orderCount > 100 => 0.20,
        $orderCount > 50 => 0.15,
        default => 0.10,
    };
}

// I/O in service
public function getUserDiscountRate(int $userId): float
{
    $orderCount = $this->orderRepository->countByUser($userId);
    return $this->calculateDiscountRate($orderCount);
}
```

### 5. Output Operations

```php
// SIDE EFFECT: Direct output
public function render(array $data): void
{
    echo json_encode($data); // Side effect
    header('Content-Type: application/json'); // Side effect
}

// BETTER: Return value
public function render(array $data): JsonResponse
{
    return new JsonResponse($data);
}
```

### 6. Time and Random

```php
// SIDE EFFECT: Non-deterministic
public function createToken(): Token
{
    return new Token(
        bin2hex(random_bytes(32)), // Random
        new DateTime('+1 hour'), // Current time
    );
}

// BETTER: Inject dependencies
public function createToken(
    RandomGeneratorInterface $random,
    ClockInterface $clock,
): Token {
    return new Token(
        bin2hex($random->bytes(32)),
        $clock->now()->modify('+1 hour'),
    );
}
```

### 7. Logging and Metrics

```php
// SIDE EFFECT: Logging in calculation
public function calculate(Order $order): Money
{
    $this->logger->debug('Starting calculation'); // Side effect
    $total = $this->computeTotal($order);
    $this->metrics->increment('orders.calculated'); // Side effect
    $this->logger->info('Calculated', ['total' => $total]); // Side effect
    return $total;
}

// BETTER: Separate concerns
public function calculate(Order $order): Money
{
    return $this->computeTotal($order);
}

// Decorate for logging
class LoggingOrderCalculator implements OrderCalculatorInterface
{
    public function __construct(
        private OrderCalculatorInterface $inner,
        private LoggerInterface $logger,
    ) {}

    public function calculate(Order $order): Money
    {
        $this->logger->debug('Starting calculation');
        $total = $this->inner->calculate($order);
        $this->logger->info('Calculated', ['total' => $total]);
        return $total;
    }
}
```

## Grep Patterns

```bash
# Echo/print
Grep: "(echo|print)\s+" --glob "**/*.php"

# Header calls
Grep: "header\s*\(" --glob "**/*.php"

# Superglobals
Grep: "\$_(GET|POST|SESSION|COOKIE|SERVER|FILES)" --glob "**/*.php"

# Global keyword
Grep: "global\s+\\\$" --glob "**/*.php"

# Static property write
Grep: "(self|static)::\\\$\w+\s*[+\-*\/]?=" --glob "**/*.php"

# File operations
Grep: "(file_put_contents|fwrite|unlink|mkdir|chmod)\(" --glob "**/*.php"
```

## Severity Classification

| Side Effect | Severity |
|-------------|----------|
| Superglobal access | 🟠 Major |
| Static state mutation | 🟠 Major |
| I/O mixed with logic | 🟠 Major |
| Input mutation | 🟡 Minor |
| Logging in pure logic | 🟢 Suggestion |

## Refactoring Strategies

### Command/Query Separation

```php
// Query: No side effects
public function getTotalPrice(Order $order): Money;

// Command: Side effects
public function completeOrder(Order $order): void;
```

### Return vs Mutate

```php
// Before: Mutate
$order->applyDiscount($discount);

// After: Return new
$discountedOrder = $order->withDiscount($discount);
```

## Output Format

```markdown
### Side Effect: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`
**Type:** [State Mutation|Global Access|I/O|...]

**Issue:**
Method mixes business logic with database I/O.

**Current:**
```php
public function calculateDiscount(int $userId): float
{
    $user = $this->db->query(...); // I/O
    return $this->computeDiscount($user); // Logic
}
```

**Suggested:**
```php
public function calculateDiscount(User $user): float
{
    return $this->computeDiscount($user); // Pure
}
```

**Testing Impact:**
- Before: Need database or complex mocking
- After: Pass User object, test edge cases easily
```
