# Common GRASP Violations (Antipatterns)

## Overview

This document catalogs common GRASP violations found in PHP codebases with detection patterns and remediation guidance.

## Information Expert Violations

### Feature Envy

```php
<?php

// ANTIPATTERN: Method accesses other object's data more than its own
final class OrderReporter
{
    public function generateSummary(Order $order): string
    {
        // Accesses Order internals extensively
        $summary = sprintf(
            "Order: %s\n",
            $order->getId()->getValue(),
        );

        foreach ($order->getLines() as $line) {
            $summary .= sprintf(
                "- %s x%d @ %s = %s\n",
                $line->getProduct()->getName(),
                $line->getQuantity()->getValue(),
                $line->getProduct()->getPrice()->format(),
                $line->getProduct()->getPrice()
                    ->multiply($line->getQuantity()->getValue())
                    ->format(),
            );
        }

        return $summary;
    }
}
```

**Detection:**
```bash
grep -rn "->get.*()->get.*()->" --include="*.php"
```

**Fix:** Move logic to Order class
```php
final class Order
{
    public function toSummary(): string { /* ... */ }
}
```

### Anemic Domain Model

```php
<?php

// ANTIPATTERN: Entity has no behavior
final class User
{
    private ?int $id = null;
    private string $email;
    private string $password;
    private bool $active = false;

    public function getId(): ?int { return $this->id; }
    public function getEmail(): string { return $this->email; }
    public function setEmail(string $email): void { $this->email = $email; }
    // Only getters/setters, no behavior!
}

// All logic in service
final class UserService
{
    public function activate(User $user): void
    {
        $user->setActive(true);
        $this->repository->save($user);
        $this->mailer->send(new ActivationEmail($user));
    }
}
```

**Fix:** Rich domain model
```php
final class User
{
    public function activate(): void
    {
        if ($this->active) {
            throw new AlreadyActiveException();
        }
        $this->active = true;
        $this->events[] = new UserActivated($this->id);
    }
}
```

---

## Creator Violations

### Random Object Creation

```php
<?php

// ANTIPATTERN: Objects created in wrong places
final class EmailService
{
    public function sendOrderConfirmation(array $orderData): void
    {
        // EmailService shouldn't create Orders!
        $order = new Order(
            new OrderId($orderData['id']),
            new CustomerId($orderData['customer_id']),
        );

        foreach ($orderData['items'] as $item) {
            $order->addLine(
                new Product($item['product_id'], $item['name']),
                new Quantity($item['quantity']),
            );
        }

        $this->mailer->send(new OrderConfirmation($order));
    }
}
```

**Fix:** Use factory, inject created object
```php
final readonly class EmailService
{
    public function sendOrderConfirmation(Order $order): void
    {
        $this->mailer->send(new OrderConfirmation($order));
    }
}
```

---

## Controller Violations

### Fat Controller

```php
<?php

// ANTIPATTERN: Controller does too much
final class OrderController
{
    public function create(Request $request): Response
    {
        // Validation
        if (empty($request->get('items'))) {
            return new JsonResponse(['error' => 'Items required'], 400);
        }

        // Business logic
        $customer = $this->customers->find($request->get('customer_id'));
        $order = new Order($customer);

        foreach ($request->get('items') as $item) {
            $product = $this->products->find($item['id']);
            if ($product->getStock() < $item['quantity']) {
                return new JsonResponse(['error' => 'Insufficient stock'], 422);
            }
            $order->addLine($product, new Quantity($item['quantity']));
        }

        // Persistence
        $this->orders->save($order);

        // Side effects
        $this->mailer->send(new OrderConfirmation($order));
        $this->inventory->reserve($order);

        return new JsonResponse(['id' => $order->getId()]);
    }
}
```

**Detection:**
```bash
find . -path "*/Controller/*.php" -exec wc -l {} \; | awk '$1 > 100'
```

**Fix:** Delegate to handler
```php
final readonly class OrderController
{
    public function create(CreateOrderRequest $request): Response
    {
        $orderId = ($this->createOrderHandler)(
            new CreateOrderCommand($request->customerId(), $request->items()),
        );

        return new JsonResponse(['id' => $orderId->value]);
    }
}
```

---

## Low Coupling Violations

### Dependency Explosion

```php
<?php

// ANTIPATTERN: Too many dependencies
final class OrderService
{
    public function __construct(
        private OrderRepository $orders,
        private CustomerRepository $customers,
        private ProductRepository $products,
        private InventoryService $inventory,
        private PaymentGateway $payment,
        private TaxCalculator $tax,
        private ShippingCalculator $shipping,
        private DiscountService $discount,
        private Mailer $mailer,
        private SmsGateway $sms,
        private Logger $logger,
        private Cache $cache,
    ) {}
}
```

**Detection:**
```bash
grep -rn "__construct" --include="*.php" -A 15 | grep -c "private\|readonly"
```

**Fix:** Split into focused services

---

## High Cohesion Violations

### God Class

```php
<?php

// ANTIPATTERN: Class does everything
final class UserManager
{
    public function register(array $data): User { /* ... */ }
    public function login(string $email, string $password): Token { /* ... */ }
    public function logout(Token $token): void { /* ... */ }
    public function sendPasswordReset(string $email): void { /* ... */ }
    public function updateProfile(User $user, array $data): void { /* ... */ }
    public function uploadAvatar(User $user, File $file): void { /* ... */ }
    public function deleteUser(User $user): void { /* ... */ }
    public function exportUserData(User $user): string { /* ... */ }
    public function importUsers(string $csvPath): array { /* ... */ }
    public function generateReport(): Report { /* ... */ }
    public function sendNotification(User $user, Notification $n): void { /* ... */ }
}
```

**Detection:**
```bash
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 500'
grep -rn "class.*Manager\|class.*Handler" --include="*.php"
```

**Fix:** Extract focused classes

---

## Polymorphism Violations

### Type Switch

```php
<?php

// ANTIPATTERN: Type-based conditionals
final class DocumentProcessor
{
    public function process(Document $doc): void
    {
        match ($doc->getType()) {
            'pdf' => $this->processPdf($doc),
            'word' => $this->processWord($doc),
            'excel' => $this->processExcel($doc),
            'image' => $this->processImage($doc),
            // Must modify for new types!
        };
    }
}
```

**Detection:**
```bash
grep -rn "match.*getType\|switch.*->type\|instanceof.*?" --include="*.php"
```

**Fix:** Use polymorphism
```php
interface DocumentProcessor
{
    public function supports(Document $doc): bool;
    public function process(Document $doc): void;
}
```

---

## Pure Fabrication Violations

### Misplaced Logic

```php
<?php

// ANTIPATTERN: Infrastructure logic in domain
final class Order
{
    public function save(): void
    {
        // Domain object shouldn't know about persistence!
        $pdo = new PDO('mysql:host=localhost;dbname=app');
        $stmt = $pdo->prepare('INSERT INTO orders ...');
        $stmt->execute([/* ... */]);
    }

    public function sendConfirmation(): void
    {
        // Domain object shouldn't know about email!
        $mailer = new PHPMailer();
        $mailer->send(/* ... */);
    }
}
```

**Fix:** Use Repository and Domain Events
```php
final class Order
{
    private array $events = [];

    public function place(): void
    {
        $this->status = OrderStatus::Placed;
        $this->events[] = new OrderPlaced($this->id);
    }
}
```

---

## Indirection Violations

### Missing Abstraction

```php
<?php

// ANTIPATTERN: Direct external system coupling
final class OrderService
{
    public function process(Order $order): void
    {
        // Direct Stripe dependency!
        $stripe = new \Stripe\StripeClient('sk_test_xxx');
        $charge = $stripe->charges->create([
            'amount' => $order->getTotal()->getCents(),
            'currency' => 'usd',
        ]);

        // Direct AWS dependency!
        $s3 = new \Aws\S3\S3Client([/* ... */]);
        $s3->putObject([
            'Bucket' => 'invoices',
            'Key' => $order->getId() . '.pdf',
            'Body' => $this->generateInvoice($order),
        ]);
    }
}
```

**Detection:**
```bash
grep -rn "new.*\\\\Stripe\|new.*\\\\Aws\|new.*\\\\Google" --include="*.php"
```

**Fix:** Adapter pattern
```php
interface PaymentGateway
{
    public function charge(PaymentRequest $request): PaymentResult;
}

interface FileStorage
{
    public function store(string $path, string $content): void;
}
```

---

## Protected Variations Violations

### Hardcoded Variations

```php
<?php

// ANTIPATTERN: Hardcoded variation points
final class ShippingCalculator
{
    public function calculate(Order $order): Money
    {
        // Hardcoded carriers!
        return match ($order->getShippingMethod()) {
            'ups' => $this->calculateUps($order),
            'fedex' => $this->calculateFedex($order),
            'usps' => $this->calculateUsps($order),
        };
    }

    private function calculateUps(Order $order): Money
    {
        // Hardcoded API!
        $client = new \Ups\Rate('api-key-xxx');
        // ...
    }
}
```

**Fix:** Strategy pattern with interfaces
```php
interface ShippingCarrier
{
    public function getName(): string;
    public function calculateRate(Shipment $shipment): Money;
}
```

---

## Quick Reference: Detection Commands

```bash
# Information Expert: Feature Envy
grep -rn "->get.*()->get.*()->" --include="*.php"

# Creator: Random creation
grep -rn "new\s\+[A-Z][a-z]*[A-Z]" --include="*.php"

# Controller: Fat controllers
find . -path "*/Controller/*.php" -exec wc -l {} \; | awk '$1 > 100'

# Low Coupling: Many dependencies
grep -rn "__construct" --include="*.php" -A 15 | grep -c "private"

# High Cohesion: God classes
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 500'

# Polymorphism: Type switches
grep -rn "match.*type\|switch.*instanceof" --include="*.php"

# Indirection: Direct coupling
grep -rn "new.*\\\\Stripe\|new.*\\\\Aws" --include="*.php"
```

## Severity Guide

| Severity | Description | Action |
|----------|-------------|--------|
| CRITICAL | Fundamental violation | Immediate refactoring |
| WARNING | Localized violation | Plan refactoring |
| INFO | Minor issue | Consider in next iteration |
