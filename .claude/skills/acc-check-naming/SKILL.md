---
name: acc-check-naming
description: Analyzes PHP code for naming convention issues. Detects non-descriptive names, abbreviations, inconsistent casing, misleading names.
---

# Naming Convention Check

Analyze PHP code for naming quality and consistency.

## Detection Patterns

### 1. Non-Descriptive Names

```php
// BAD: Single letter variables (except loop counters)
$x = $user->getAge();
$d = new DateTime();
$r = $repository->find($id);

// GOOD: Descriptive names
$userAge = $user->getAge();
$currentDate = new DateTime();
$foundUser = $repository->find($id);

// BAD: Generic names
$data = $service->process();
$result = $handler->handle();
$temp = $this->calculate();

// GOOD: Specific names
$orderSummary = $service->generateSummary();
$validationResult = $handler->validate();
$discountAmount = $this->calculateDiscount();
```

### 2. Abbreviations and Acronyms

```php
// BAD: Unclear abbreviations
$usrMgr = new UserManager();
$prodRepo = new ProductRepository();
$txnSvc = new TransactionService();

// GOOD: Full words
$userManager = new UserManager();
$productRepository = new ProductRepository();
$transactionService = new TransactionService();

// ACCEPTABLE: Common acronyms
$userId = $user->getId();  // ID is universally understood
$htmlContent = $this->render();  // HTML is common
$apiResponse = $client->get();  // API is common
```

### 3. Inconsistent Casing

```php
// BAD: Mixed casing styles
$user_name = 'John';  // snake_case
$userAge = 25;        // camelCase
$UserEmail = 'x@y';   // PascalCase

// GOOD: Consistent camelCase for variables
$userName = 'John';
$userAge = 25;
$userEmail = 'x@y';

// Constants should be UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 30;
```

### 4. Misleading Names

```php
// BAD: Name doesn't match behavior
function getUser(): void  // "get" implies return value
{
    $this->user = $this->repository->find($id);
}

// BAD: Boolean without is/has/can prefix
$active = $user->active;  // Unclear if boolean

// GOOD: Clear boolean naming
$isActive = $user->isActive();
$hasOrders = $user->hasOrders();
$canEdit = $user->canEditProfile();

// BAD: Negated boolean names
$isNotValid = false;  // Double negative confusion
$isInactive = true;

// GOOD: Positive boolean names
$isValid = true;
$isActive = false;
```

### 5. Class Naming

```php
// BAD: Generic class names
class Manager {}      // Manager of what?
class Processor {}    // Processes what?
class Handler {}      // Handles what?
class Helper {}       // Helps with what?

// GOOD: Specific class names
class OrderManager {}
class PaymentProcessor {}
class WebhookHandler {}
class DateTimeHelper {}

// BAD: Missing suffix for pattern
class User implements RepositoryInterface {}

// GOOD: Pattern-indicating suffix
class UserRepository implements RepositoryInterface {}
class OrderFactory {}
class PaymentService {}
```

### 6. Method Naming

```php
// BAD: Vague method names
function process() {}
function handle() {}
function execute() {}
function run() {}

// GOOD: Action-specific names
function processPayment() {}
function handleWebhook() {}
function executeQuery() {}
function runMigrations() {}

// BAD: Doesn't describe what it returns
function user(): User {}

// GOOD: Describes intent
function findUserById(int $id): User {}
function getCurrentUser(): User {}
function createGuestUser(): User {}
```

### 7. Parameter Naming

```php
// BAD: Type as name
function process(array $array, string $string): void {}

// GOOD: Descriptive parameter names
function processOrder(array $orderItems, string $currency): void {}

// BAD: Numbered parameters
function calculate(int $value1, int $value2): int {}

// GOOD: Meaningful parameter names
function calculateDiscount(int $originalPrice, int $discountPercent): int {}
```

### 8. Constant Naming

```php
// BAD: Lowercase or camelCase constants
const maxRetries = 3;
const defaultTimeout = 30;

// GOOD: UPPER_SNAKE_CASE
const MAX_RETRIES = 3;
const DEFAULT_TIMEOUT = 30;
const API_VERSION = 'v1';

// BAD: Non-descriptive
const VALUE = 100;
const LIMIT = 50;

// GOOD: Contextual
const PAGINATION_LIMIT = 50;
const MAX_UPLOAD_SIZE_MB = 100;
```

## Grep Patterns

```bash
# Single letter variables
Grep: "\\\$[a-z]\s*=" --glob "**/*.php"

# Common abbreviations
Grep: "\\\$(mgr|svc|repo|impl|util)\w*\s*=" -i --glob "**/*.php"

# Generic class names
Grep: "class\s+(Manager|Processor|Handler|Helper)\s" --glob "**/*.php"

# Boolean without prefix
Grep: "private\s+(bool|\?bool)\s+\\\$[^is|has|can|should|was|will]" --glob "**/*.php"
```

## Naming Conventions Summary

| Element | Convention | Example |
|---------|------------|---------|
| Variables | camelCase | $userName |
| Constants | UPPER_SNAKE_CASE | MAX_RETRIES |
| Functions | camelCase | getUserById() |
| Classes | PascalCase | UserService |
| Interfaces | PascalCase + Interface | UserRepositoryInterface |
| Traits | PascalCase + Trait | TimestampableTrait |

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Misleading names | 🟠 Major |
| Single letter (non-loop) | 🟡 Minor |
| Inconsistent casing | 🟡 Minor |
| Abbreviations | 🟢 Suggestion |

## Output Format

```markdown
### Naming Issue: [Description]

**Severity:** 🟠/🟡/🟢
**Location:** `file.php:line`

**Issue:**
[Description of the naming problem]

**Current:**
```php
$x = $service->getData();
```

**Suggested:**
```php
$orderData = $service->getOrderData();
```

**Rationale:**
Descriptive names reduce cognitive load and improve maintainability.
```
