---
name: acc-check-abstract-factory
description: Audits Abstract Factory pattern implementations. Checks family consistency, product hierarchy, factory method completeness, and cross-family compatibility.
---

# Abstract Factory Pattern Audit

Analyze PHP code for Abstract Factory pattern compliance — ensuring consistent object families and proper product hierarchies.

## Detection Patterns

### 1. Missing Abstract Factory (Direct Instantiation of Families)

```php
// ANTIPATTERN: Creating related objects without factory
class NotificationService
{
    public function send(string $type, string $message): void
    {
        if ($type === 'email') {
            $transport = new SmtpTransport();      // Family: Email
            $formatter = new HtmlFormatter();       // Family: Email
            $tracker = new EmailOpenTracker();       // Family: Email
        } elseif ($type === 'sms') {
            $transport = new TwilioTransport();     // Family: SMS
            $formatter = new PlainTextFormatter();  // Family: SMS
            $tracker = new SmsDeliveryTracker();    // Family: SMS
        }
    }
}

// CORRECT: Abstract Factory ensures family consistency
interface NotificationFactory
{
    public function createTransport(): TransportInterface;
    public function createFormatter(): FormatterInterface;
    public function createTracker(): TrackerInterface;
}
```

### 2. Incomplete Product Family

```php
// ANTIPATTERN: Factory missing products
final readonly class EmailNotificationFactory implements NotificationFactory
{
    public function createTransport(): TransportInterface
    {
        return new SmtpTransport();
    }

    public function createFormatter(): FormatterInterface
    {
        return new HtmlFormatter();
    }

    // MISSING: createTracker() — incomplete family!
}
```

### 3. Cross-Family Mixing

```php
// ANTIPATTERN: Products from different families mixed
final readonly class PushNotificationFactory implements NotificationFactory
{
    public function createTransport(): TransportInterface
    {
        return new FirebaseTransport(); // Push family
    }

    public function createFormatter(): FormatterInterface
    {
        return new HtmlFormatter(); // Email family! Wrong!
    }
}
```

### 4. No Interface Return Types

```php
// ANTIPATTERN: Factory returns concrete types
class DatabaseFactory
{
    public function createConnection(): MySqlConnection  // Concrete!
    {
        return new MySqlConnection();
    }

    public function createQueryBuilder(): MySqlQueryBuilder  // Concrete!
    {
        return new MySqlQueryBuilder();
    }
}

// CORRECT: Returns interfaces
interface DatabaseFactory
{
    public function createConnection(): ConnectionInterface;
    public function createQueryBuilder(): QueryBuilderInterface;
}
```

### 5. Factory Without Interface

```php
// ANTIPATTERN: Concrete factory without abstraction
class PaymentGatewayFactory
{
    public function createProcessor(): StripeProcessor { }
    public function createRefunder(): StripeRefunder { }
}
// Cannot swap to PayPal family!

// CORRECT: Abstract factory interface
interface PaymentGatewayFactory
{
    public function createProcessor(): PaymentProcessorInterface;
    public function createRefunder(): RefundProcessorInterface;
}

final readonly class StripeGatewayFactory implements PaymentGatewayFactory { }
final readonly class PayPalGatewayFactory implements PaymentGatewayFactory { }
```

## Grep Patterns

```bash
# Abstract Factory detection
Grep: "interface.*Factory" --glob "**/*.php"
Grep: "AbstractFactory|FactoryInterface" --glob "**/*.php"

# Multiple create methods in one class (potential Abstract Factory)
Grep: "function create[A-Z]" --glob "**/*Factory.php"

# Family instantiation without factory
Grep: "if.*===.*new.*\n.*new.*\n.*new" --glob "**/*.php"

# Type switch creating object families
Grep: "switch.*type|switch.*strategy|switch.*provider" --glob "**/*.php"

# Factory returning concrete types
Grep: "function create.*: [A-Z][a-zA-Z]+[^I](?!nterface)" --glob "**/*Factory.php"
```

## Audit Checklist

| Check | Severity | Description |
|-------|----------|-------------|
| Factory interface exists | 🔴 Critical | Each family must have abstract factory |
| All products defined | 🔴 Critical | Every family creates all required products |
| Interface return types | 🟠 Major | Factory methods return interfaces |
| No cross-family mixing | 🟠 Major | Products belong to same family |
| Family consistency | 🟠 Major | All factories create compatible products |
| Single Responsibility | 🟡 Minor | Factory only creates, no business logic |

## Correct Implementation

```php
// Product interfaces
interface ButtonInterface
{
    public function render(): string;
}

interface CheckboxInterface
{
    public function render(): string;
}

// Abstract Factory
interface UIComponentFactory
{
    public function createButton(): ButtonInterface;
    public function createCheckbox(): CheckboxInterface;
}

// Concrete Families
final readonly class MaterialUIFactory implements UIComponentFactory
{
    public function createButton(): ButtonInterface
    {
        return new MaterialButton();
    }

    public function createCheckbox(): CheckboxInterface
    {
        return new MaterialCheckbox();
    }
}

final readonly class BootstrapUIFactory implements UIComponentFactory
{
    public function createButton(): ButtonInterface
    {
        return new BootstrapButton();
    }

    public function createCheckbox(): CheckboxInterface
    {
        return new BootstrapCheckbox();
    }
}
```

## Output Format

```markdown
### Abstract Factory: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`

**Issue:**
[Description of the Abstract Factory violation]

**Impact:**
- Cross-family incompatibility possible
- Cannot swap implementations cleanly
- Violates Open/Closed Principle

**Code:**
```php
// Current code
```

**Fix:**
```php
// Abstract Factory refactored
```
```
