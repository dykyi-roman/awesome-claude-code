---
name: acc-check-consistency
description: Analyzes PHP code for consistency issues. Detects mixed coding styles, inconsistent patterns, API inconsistencies, naming convention violations.
---

# Consistency Check

Analyze PHP code for consistency across the codebase.

## Detection Patterns

### 1. Mixed Coding Styles

```php
// INCONSISTENT: Different styles in same file/project
class UserService
{
    // camelCase method
    public function getUser() {}

    // snake_case method (inconsistent)
    public function get_orders() {}
}

// INCONSISTENT: Different array syntax
$items = array(1, 2, 3);  // Long syntax
$config = [4, 5, 6];       // Short syntax

// CONSISTENT: Choose one style
$items = [1, 2, 3];
$config = [4, 5, 6];
```

### 2. Inconsistent Return Patterns

```php
// INCONSISTENT: Mixed return types for similar operations
public function findUser(int $id): ?User
{
    return $this->repository->find($id); // Returns null if not found
}

public function findOrder(int $id): Order
{
    $order = $this->repository->find($id);
    if (!$order) {
        throw new NotFoundException(); // Throws if not found
    }
    return $order;
}

// CONSISTENT: Same pattern for similar operations
public function findUser(int $id): ?User {}
public function findOrder(int $id): ?Order {}

// Or all throwing:
public function getUser(int $id): User {}    // @throws
public function getOrder(int $id): Order {}  // @throws
```

### 3. Inconsistent Error Handling

```php
// INCONSISTENT: Different error handling strategies
class PaymentService
{
    public function charge(): bool
    {
        try {
            // ...
            return true;
        } catch (Exception $e) {
            return false; // Returns boolean
        }
    }

    public function refund(): void
    {
        // ...
        if ($error) {
            throw new RefundException(); // Throws exception
        }
    }
}

// CONSISTENT: Same strategy
class PaymentService
{
    public function charge(): PaymentResult {}  // Throws on error
    public function refund(): RefundResult {}   // Throws on error
}
```

### 4. API Inconsistencies

```php
// INCONSISTENT: Different parameter order
public function createUser(string $email, string $name): User {}
public function createProduct(string $name, string $sku): Product {}
// One is (email, name), other is (name, sku)

// INCONSISTENT: Different collection handling
public function getUsers(): array {}        // Returns array
public function getOrders(): Collection {}  // Returns Collection
public function getProducts(): iterable {}  // Returns iterable

// CONSISTENT: Same patterns
public function getUsers(): array {}
public function getOrders(): array {}
public function getProducts(): array {}
```

### 5. Inconsistent Naming Conventions

```php
// INCONSISTENT: Mixed naming for similar concepts
class Order
{
    private $customerId;      // camelCase
    private $shipping_address; // snake_case (inconsistent)
}

// INCONSISTENT: Different prefixes for similar things
interface UserRepository {}
interface IOrderRepository {}  // I prefix
interface ProductRepoInterface {} // Different suffix

// CONSISTENT: Same pattern
interface UserRepositoryInterface {}
interface OrderRepositoryInterface {}
interface ProductRepositoryInterface {}
```

### 6. Inconsistent Constructor Patterns

```php
// INCONSISTENT: Mix of property promotion and explicit
class UserService
{
    private OrderRepository $orderRepo;

    public function __construct(
        private UserRepository $userRepo,  // Promoted
        OrderRepository $orderRepo         // Not promoted
    ) {
        $this->orderRepo = $orderRepo;
    }
}

// CONSISTENT: All promoted
class UserService
{
    public function __construct(
        private UserRepository $userRepo,
        private OrderRepository $orderRepo,
    ) {}
}
```

### 7. Inconsistent Dependency Injection

```php
// INCONSISTENT: Mix of injection styles
class OrderService
{
    private $cache;

    public function __construct(
        private UserRepository $userRepo,  // Constructor injection
    ) {}

    public function setCache(CacheInterface $cache): void  // Setter injection
    {
        $this->cache = $cache;
    }

    public function process(): void
    {
        $logger = Container::get(LoggerInterface::class);  // Service locator
    }
}

// CONSISTENT: All constructor injection
class OrderService
{
    public function __construct(
        private UserRepository $userRepo,
        private CacheInterface $cache,
        private LoggerInterface $logger,
    ) {}
}
```

### 8. Inconsistent Null Handling

```php
// INCONSISTENT: Different null patterns
public function getUser(): ?User {}            // Nullable return
public function getOrder(): Order|null {}      // Union type null
public function findProduct(): false|Product {} // False for not found

// CONSISTENT: Choose one pattern
public function getUser(): ?User {}
public function getOrder(): ?Order {}
public function findProduct(): ?Product {}
```

### 9. Inconsistent Date/Time Handling

```php
// INCONSISTENT: Different date types
public function setCreatedAt(DateTime $date): void {}
public function setUpdatedAt(DateTimeImmutable $date): void {}
public function setDeletedAt(string $date): void {}

// CONSISTENT: Same type
public function setCreatedAt(DateTimeImmutable $date): void {}
public function setUpdatedAt(DateTimeImmutable $date): void {}
public function setDeletedAt(DateTimeImmutable $date): void {}
```

### 10. Inconsistent Response Patterns

```php
// INCONSISTENT: Different response structures
// Endpoint 1
{"data": {"user": {...}}}

// Endpoint 2
{"user": {...}}

// Endpoint 3
{"result": {"data": {...}}}

// CONSISTENT: Same envelope
{"data": {...}, "meta": {...}}
```

## Grep Patterns

```bash
# Mixed array syntax
Grep: "array\s*\(" --glob "**/*.php"
Grep: "\[.*\]" --glob "**/*.php"

# Interface naming
Grep: "interface\s+\w+" --glob "**/*.php"

# Return type patterns
Grep: ":\s*\?\w+|:\s*\w+\|null|:\s*false\|\w+" --glob "**/*.php"

# Constructor patterns
Grep: "public function __construct" --glob "**/*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| API inconsistency | 🟠 Major |
| Error handling mismatch | 🟠 Major |
| Naming convention mix | 🟡 Minor |
| Code style differences | 🟡 Minor |
| Formatting variations | 🟢 Suggestion |

## Best Practices

### Create Team Standards

```markdown
## Our Conventions

1. Always use short array syntax `[]`
2. Use nullable return types `?Type` not `Type|null`
3. All repositories extend `AbstractRepository`
4. All interfaces end with `Interface`
5. Use constructor property promotion
6. Prefer DateTimeImmutable over DateTime
```

### Use Static Analysis

```bash
# PHP-CS-Fixer for consistent formatting
php-cs-fixer fix --rules=@PSR12

# PHPStan for type consistency
phpstan analyze src/
```

## Output Format

```markdown
### Consistency Issue: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** Multiple files

**Issue:**
Inconsistent [pattern type] found across codebase.

**Found Variations:**
1. `UserRepository` - no Interface suffix
2. `IOrderRepository` - I prefix
3. `ProductRepositoryInterface` - Interface suffix

**Recommended Standard:**
```php
interface UserRepositoryInterface {}
interface OrderRepositoryInterface {}
interface ProductRepositoryInterface {}
```

**Files to Update:**
- `src/User/UserRepository.php`
- `src/Order/IOrderRepository.php`
```
