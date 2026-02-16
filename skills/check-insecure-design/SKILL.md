---
name: acc-check-insecure-design
description: Detects OWASP A04:2021 Insecure Design vulnerabilities. Identifies missing rate limiting, account lockout, CAPTCHA, TOCTOU races, business logic flaws, and threat modeling gaps.
---

# Insecure Design Security Check (A04:2021)

Analyze PHP code for insecure design patterns — architectural and business logic security flaws that cannot be fixed by implementation alone.

## Detection Patterns

### 1. Missing Account Lockout

```php
// VULNERABLE: No brute-force protection
class LoginController
{
    public function login(Request $request): Response
    {
        $user = $this->userRepo->findByEmail($request->get('email'));
        if ($user && password_verify($request->get('password'), $user->passwordHash())) {
            return $this->createSession($user);
        }
        return new Response('Invalid credentials', 401);
        // No attempt tracking! Attacker can try unlimited passwords
    }
}

// CORRECT: Account lockout after N failures
class LoginController
{
    private const int MAX_ATTEMPTS = 5;
    private const int LOCKOUT_MINUTES = 15;

    public function login(Request $request): Response
    {
        $email = $request->get('email');

        if ($this->loginAttempts->isLocked($email)) {
            return new Response('Account temporarily locked', 429);
        }

        $user = $this->userRepo->findByEmail($email);
        if ($user && password_verify($request->get('password'), $user->passwordHash())) {
            $this->loginAttempts->reset($email);
            return $this->createSession($user);
        }

        $this->loginAttempts->record($email);
        if ($this->loginAttempts->count($email) >= self::MAX_ATTEMPTS) {
            $this->loginAttempts->lock($email, self::LOCKOUT_MINUTES);
        }
        return new Response('Invalid credentials', 401);
    }
}
```

### 2. Missing Rate Limiting on Sensitive Endpoints

```php
// VULNERABLE: No rate limiting on password reset
class PasswordResetController
{
    public function requestReset(Request $request): Response
    {
        $email = $request->get('email');
        $this->resetService->sendResetLink($email);
        return new Response('Reset link sent', 200);
        // Attacker can spam reset emails, enumerate users
    }
}

// VULNERABLE: No rate limiting on API key generation
class ApiKeyController
{
    public function generate(Request $request): Response
    {
        return new Response($this->apiKeyService->generate());
        // Unlimited key generation
    }
}
```

### 3. TOCTOU (Time-of-Check-Time-of-Use) Race Condition

```php
// VULNERABLE: Check and use are separate operations
class InventoryService
{
    public function purchase(ProductId $id, int $quantity): void
    {
        $stock = $this->inventory->getStock($id);
        if ($stock >= $quantity) {              // CHECK
            // Another request could reduce stock here!
            sleep(1); // Simulates processing time
            $this->inventory->reduce($id, $quantity); // USE — may oversell!
        }
    }
}

// CORRECT: Atomic check-and-reduce
class InventoryService
{
    public function purchase(ProductId $id, int $quantity): void
    {
        $reduced = $this->inventory->reduceIfAvailable($id, $quantity);
        // Atomic operation: UPDATE stock SET quantity = quantity - ? WHERE id = ? AND quantity >= ?
        if (!$reduced) {
            throw new InsufficientStockException();
        }
    }
}
```

### 4. Missing Business Logic Validation

```php
// VULNERABLE: No business rules on discount
class DiscountService
{
    public function applyDiscount(Order $order, int $percent): void
    {
        $order->setDiscount($percent); // No max limit! 100%? 200%?
    }
}

// VULNERABLE: Price manipulation
class CartController
{
    public function updateItem(Request $request): Response
    {
        $item = $this->cart->getItem($request->get('itemId'));
        $item->setPrice($request->get('price')); // Client sends price!
    }
}

// VULNERABLE: Negative quantity
class OrderService
{
    public function addItem(OrderId $id, int $quantity): void
    {
        $this->order->addItem($id, $quantity); // Negative = credit?
    }
}
```

### 5. Missing CAPTCHA on Automated Endpoints

```php
// VULNERABLE: Form without bot protection
class RegistrationController
{
    public function register(Request $request): Response
    {
        // No CAPTCHA — bots can mass-register
        $user = User::create(
            email: $request->get('email'),
            password: $request->get('password'),
        );
        $this->userRepo->save($user);
    }
}

// VULNERABLE: Contact form without protection
class ContactController
{
    public function submit(Request $request): Response
    {
        // No CAPTCHA — spam submissions
        $this->mailer->send($request->get('message'));
    }
}
```

### 6. Insecure Direct Object Reference by Design

```php
// VULNERABLE: Sequential IDs expose information
class UserController
{
    public function show(int $id): Response
    {
        // Enumerable: /users/1, /users/2, /users/3...
        return new Response($this->userRepo->find($id));
    }
}

// CORRECT: Use UUIDs
class UserController
{
    public function show(string $id): Response
    {
        return new Response($this->userRepo->find(new UserId($id)));
        // /users/550e8400-e29b-41d4-a716-446655440000
    }
}
```

## Grep Patterns

```bash
# Login without lockout
Grep: "password_verify|authenticate|login" --glob "**/*Controller*.php"
Grep: "loginAttempts|failedAttempts|lockout|isLocked" --glob "**/*.php"

# Password reset without rate limiting
Grep: "resetPassword|forgotPassword|sendResetLink" --glob "**/*.php"
Grep: "RateLimit|throttle|rateLimiter" --glob "**/*.php"

# TOCTOU patterns
Grep: "getStock|getBalance|checkAvailability" --glob "**/*.php"
Grep: "reduceIfAvailable|atomicDecrement|FOR UPDATE" --glob "**/*.php"

# Client-sent prices
Grep: "request->get\(['\"]price|request->get\(['\"]amount" --glob "**/*Controller*.php"

# Missing CAPTCHA
Grep: "captcha|recaptcha|hcaptcha|turnstile" --glob "**/*.php"
Grep: "register|signup|contact" --glob "**/*Controller*.php"

# Sequential IDs
Grep: "function show\(int \$id\)|function get\(int \$id\)" --glob "**/*Controller*.php"
```

## Severity Classification

| Pattern | Severity |
|---------|----------|
| Missing account lockout | 🔴 Critical |
| TOCTOU race condition | 🔴 Critical |
| Client-controlled pricing | 🔴 Critical |
| No rate limiting on auth endpoints | 🟠 Major |
| Missing CAPTCHA on registration | 🟠 Major |
| Sequential enumerable IDs | 🟡 Minor |

## Output Format

```markdown
### Insecure Design: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**CWE:** CWE-840 (Business Logic Errors)
**OWASP:** A04:2021 — Insecure Design

**Issue:**
[Description of the design-level security flaw]

**Attack Scenario:**
[How an attacker exploits this design flaw]

**Code:**
```php
// Insecure design
```

**Fix:**
```php
// Secure by design
```
```
