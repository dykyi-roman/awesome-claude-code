# Common SOLID Violations (Antipatterns)

## Overview

This document catalogs common SOLID violations found in PHP codebases with detection patterns and remediation guidance.

## SRP Violations

### God Class

```php
<?php

// ANTIPATTERN: Class does everything
final class UserManager
{
    public function register(array $data): User { /* ... */ }
    public function login(string $email, string $password): Token { /* ... */ }
    public function logout(Token $token): void { /* ... */ }
    public function updateProfile(User $user, array $data): void { /* ... */ }
    public function changePassword(User $user, string $old, string $new): void { /* ... */ }
    public function resetPassword(string $email): void { /* ... */ }
    public function sendWelcomeEmail(User $user): void { /* ... */ }
    public function sendPasswordResetEmail(User $user): void { /* ... */ }
    public function validateEmail(User $user, string $token): void { /* ... */ }
    public function generateReport(): Report { /* ... */ }
    public function export(Format $format): string { /* ... */ }
    public function import(string $data): void { /* ... */ }
    // 500+ more lines...
}
```

**Detection:**
```bash
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 500'
grep -rn "class.*Manager\|class.*Helper\|class.*Util" --include="*.php"
```

**Fix:** Extract into focused classes (UserRegistration, UserAuthentication, UserExport, etc.)

### Feature Envy

```php
<?php

// ANTIPATTERN: Class uses other class's data more than its own
final class OrderPrinter
{
    public function print(Order $order): string
    {
        return sprintf(
            "Order: %s\nCustomer: %s %s\nEmail: %s\nTotal: %s %s",
            $order->getId(),
            $order->getCustomer()->getFirstName(),
            $order->getCustomer()->getLastName(),
            $order->getCustomer()->getEmail(),
            $order->getTotal()->getAmount(),
            $order->getTotal()->getCurrency(),
        );
    }
}
```

**Fix:** Move behavior to the class that owns the data
```php
<?php

final readonly class Order
{
    public function format(): string
    {
        return sprintf(
            "Order: %s\nCustomer: %s\nTotal: %s",
            $this->id->value,
            $this->customer->fullName(),
            $this->total->formatted(),
        );
    }
}
```

---

## OCP Violations

### Switch on Type

```php
<?php

// ANTIPATTERN: Must modify for new payment types
final class PaymentProcessor
{
    public function process(Payment $payment): Result
    {
        switch ($payment->type) {
            case 'credit_card':
                return $this->processCreditCard($payment);
            case 'paypal':
                return $this->processPaypal($payment);
            case 'bank_transfer':
                return $this->processBankTransfer($payment);
            // Must add case for every new type
            default:
                throw new UnsupportedPaymentException();
        }
    }
}
```

**Detection:**
```bash
grep -rn "switch.*\$.*type\|switch.*getType\|match.*::class" --include="*.php"
grep -rn "instanceof.*?.*:.*instanceof" --include="*.php"
```

**Fix:** Use Strategy pattern with interface

### Hardcoded Type Maps

```php
<?php

// ANTIPATTERN: Map requires modification
final class NotificationFactory
{
    private const HANDLERS = [
        'email' => EmailHandler::class,
        'sms' => SmsHandler::class,
        'push' => PushHandler::class,
        // Must add entry for new types
    ];

    public function create(string $type): Handler
    {
        return new self::HANDLERS[$type]();
    }
}
```

**Fix:** Use tagged services or registry pattern

---

## LSP Violations

### NotImplementedException

```php
<?php

// ANTIPATTERN: Subclass can't fulfill contract
interface Cache
{
    public function get(string $key): mixed;
    public function set(string $key, mixed $value, int $ttl): void;
    public function delete(string $key): void;
    public function clear(): void;
}

final class ReadOnlyCache implements Cache
{
    public function get(string $key): mixed { /* ... */ }

    public function set(string $key, mixed $value, int $ttl): void
    {
        throw new NotImplementedException(); // LSP VIOLATION
    }

    public function delete(string $key): void
    {
        throw new NotImplementedException(); // LSP VIOLATION
    }

    public function clear(): void
    {
        throw new NotImplementedException(); // LSP VIOLATION
    }
}
```

**Detection:**
```bash
grep -rn "NotImplemented\|NotSupported\|UnsupportedOperation" --include="*.php"
grep -rn "throw.*Exception.*//.*not.*implement" --include="*.php"
```

**Fix:** Split interface into CacheReader and CacheWriter

### Changed Postconditions

```php
<?php

// ANTIPATTERN: Subclass weakens return guarantee
abstract class Repository
{
    /** @return Entity[] Always returns array */
    abstract public function findAll(): array;
}

final class CachedRepository extends Repository
{
    public function findAll(): array
    {
        $cached = $this->cache->get('entities');
        if ($cached === null) {
            return []; // Parent never returned empty for existing data!
        }
        return $cached;
    }
}
```

**Fix:** Ensure consistent behavior across inheritance hierarchy

---

## ISP Violations

### Fat Interface

```php
<?php

// ANTIPATTERN: Interface too broad
interface Worker
{
    public function work(): void;
    public function eat(): void;
    public function sleep(): void;
    public function attendMeeting(): void;
    public function writeReport(): void;
    public function reviewCode(): void;
    public function deployApplication(): void;
    public function handleSupport(): void;
}

// Robot can't eat or sleep
final class Robot implements Worker
{
    public function work(): void { /* ... */ }
    public function eat(): void { throw new NotSupportedException(); }
    public function sleep(): void { throw new NotSupportedException(); }
    // ...
}
```

**Detection:**
```bash
# Count methods in interfaces
grep -rn "interface\s" --include="*.php" -A 50 | grep -c "public function"
# Find empty/throwing implementations
grep -rn "throw.*NotSupported\|return.*//.*unused" --include="*.php"
```

**Fix:** Split into Workable, Feedable, Sleepable interfaces

### Unused Dependencies

```php
<?php

// ANTIPATTERN: Client depends on unused methods
interface UserService
{
    public function find(UserId $id): ?User;
    public function findAll(): array;
    public function save(User $user): void;
    public function delete(User $user): void;
    public function export(): string;
    public function generateStats(): array;
}

final readonly class UserProfileController
{
    public function __construct(
        private UserService $users, // Uses only find()
    ) {}

    public function show(UserId $id): Response
    {
        $user = $this->users->find($id);
        // Never uses findAll, save, delete, export, generateStats
    }
}
```

**Fix:** Depend on focused interface (UserFinder)

---

## DIP Violations

### Hidden Dependencies

```php
<?php

// ANTIPATTERN: Dependencies created inside class
final class OrderService
{
    public function process(Order $order): void
    {
        $logger = Logger::getInstance();           // Hidden static
        $validator = new OrderValidator();          // Hidden new
        $db = Database::getConnection();            // Hidden static
        $config = config('orders.max_items');       // Hidden global

        // Business logic...
    }
}
```

**Detection:**
```bash
grep -rn "::getInstance\|::getConnection\|::get(" --include="*.php"
grep -rn "new\s\+[A-Z][a-z]*[A-Z]" --include="*.php" | grep -v "Exception\|DateTime"
```

**Fix:** Inject all dependencies through constructor

### Service Locator

```php
<?php

// ANTIPATTERN: Using service locator
final class OrderHandler
{
    public function __construct(
        private ContainerInterface $container,
    ) {}

    public function handle(Order $order): void
    {
        $repository = $this->container->get(OrderRepository::class);
        $mailer = $this->container->get(Mailer::class);
        // Hides real dependencies
    }
}
```

**Detection:**
```bash
grep -rn "container->get\|app()->make\|resolve(" --include="*.php"
```

**Fix:** Inject concrete dependencies

### Concrete Type Hints

```php
<?php

// ANTIPATTERN: Depending on concrete implementation
final readonly class PaymentProcessor
{
    public function __construct(
        private StripeClient $stripe,        // Concrete!
        private DoctrineRepository $orders,  // Concrete!
        private SwiftMailer $mailer,         // Concrete!
    ) {}
}
```

**Detection:**
```bash
# Find constructor dependencies without Interface/Abstract suffix
grep -rn "__construct" --include="*.php" -A 10 | grep "private\|readonly" | \
  grep -v "Interface\|Abstract\|Contract"
```

**Fix:** Create and depend on interfaces

---

## Combined Violations

### Anemic Domain Model (SRP + DIP)

```php
<?php

// ANTIPATTERN: No behavior, just data
final class User
{
    public ?int $id = null;
    public string $email;
    public string $password;
    public bool $active = false;
}

// All behavior in service
final class UserService
{
    public function activate(User $user): void
    {
        $user->active = true;
        $this->repository->save($user);
        $this->mailer->send(new ActivationEmail($user));
    }
}
```

**Fix:** Rich domain model with behavior
```php
<?php

final class User
{
    private array $events = [];

    public function activate(): void
    {
        if ($this->active) {
            throw new AlreadyActiveException();
        }
        $this->active = true;
        $this->events[] = new UserActivated($this->id);
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

---

## Quick Reference: Detection Commands

```bash
# SRP: God classes
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 500'

# OCP: Type switches
grep -rn "switch.*type\|match.*::class\|instanceof.*?" --include="*.php"

# LSP: Broken contracts
grep -rn "NotImplemented\|NotSupported\|throw.*//.*can't" --include="*.php"

# ISP: Fat interfaces
grep -rn "interface\s" --include="*.php" -A 50 | grep -c "public function"

# DIP: Hidden dependencies
grep -rn "new\s\+[A-Z]\|::getInstance\|::get(" --include="*.php"
```

## Severity Guide

| Severity | Description | Action |
|----------|-------------|--------|
| CRITICAL | Fundamental violation, affects entire module | Immediate refactoring |
| WARNING | Localized violation, affects maintainability | Plan refactoring |
| INFO | Minor issue, code smell | Consider in next iteration |
