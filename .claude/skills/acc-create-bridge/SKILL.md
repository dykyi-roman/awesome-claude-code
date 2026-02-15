---
name: acc-create-bridge
description: Generates Bridge pattern for PHP 8.4. Decouples abstraction from implementation. Includes unit tests.
---

# Bridge Pattern Generator

Creates Bridge pattern infrastructure for separating abstraction from implementation.

## When to Use

| Scenario | Example |
|----------|---------|
| Multiple dimensions of variation | Notification types × channels |
| Avoid class explosion | Shape × rendering method |
| Runtime implementation switching | Database drivers |
| Platform independence | UI × OS |

## Component Characteristics

### Abstraction
- High-level interface
- Uses implementor
- Domain layer

### RefinedAbstraction
- Extends abstraction
- Adds specialized behavior

### Implementor Interface
- Low-level operations
- Multiple implementations

### ConcreteImplementor
- Actual implementation
- Platform-specific code

---

## Generation Process

### Step 1: Generate Implementor Interface

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}ImplementorInterface.php` — Low-level operations

### Step 2: Generate Abstraction

**Path:** `src/Domain/{BoundedContext}/`

1. `Abstract{Name}.php` — High-level interface

### Step 3: Generate RefinedAbstraction

**Path:** `src/Domain/{BoundedContext}/`

1. `{Type}{Name}.php` — Specialized abstractions

### Step 4: Generate ConcreteImplementors

**Path:** `src/Infrastructure/{BoundedContext}/`

1. `{Platform}{Name}Implementor.php` — Platform implementations

### Step 5: Generate Tests

1. `{ClassName}Test.php` — Bridge behavior verification

---

## File Placement

| Component | Path |
|-----------|------|
| Abstraction | `src/Domain/{BoundedContext}/` |
| RefinedAbstraction | `src/Domain/{BoundedContext}/` |
| Implementor Interface | `src/Domain/{BoundedContext}/` |
| ConcreteImplementor | `src/Infrastructure/{BoundedContext}/` |
| Unit Tests | `tests/Unit/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Abstraction | `Abstract{Name}` | `AbstractNotification` |
| RefinedAbstraction | `{Type}{Name}` | `UrgentNotification` |
| Implementor Interface | `{Name}ImplementorInterface` | `NotificationImplementorInterface` |
| ConcreteImplementor | `{Platform}{Name}Implementor` | `EmailNotificationImplementor` |

---

## Quick Template Reference

### Abstraction

```php
abstract readonly class Abstract{Name}
{
    public function __construct(
        protected {Name}ImplementorInterface $implementor
    ) {}

    abstract public function {operation}({params}): {returnType};
}
```

### RefinedAbstraction

```php
final readonly class {Type}{Name} extends Abstract{Name}
{
    public function {operation}({params}): {returnType}
    {
        {preprocessing}
        return $this->implementor->{implementorMethod}({params});
    }
}
```

---

## Usage Example

```php
$email = new EmailNotificationImplementor();
$urgent = new UrgentNotification($email);
$urgent->send($message);

// Switch implementation
$sms = new SmsNotificationImplementor();
$urgent = new UrgentNotification($sms);
$urgent->send($message);
```

---

## Common Bridges

| Bridge | Purpose |
|--------|---------|
| NotificationBridge | Type × Channel (Email/SMS/Push) |
| ReportBridge | Format × Generator (PDF/Excel/CSV) |
| DatabaseBridge | Query × Driver (MySQL/PostgreSQL) |
| PaymentBridge | Gateway × Provider (Stripe/PayPal) |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Missing Abstraction | Direct implementor use | Use abstraction layer |
| Tight Coupling | Abstraction knows concrete implementor | Depend on interface |
| Single Implementation | No variation | Use simple inheritance |
| Leaky Abstraction | Exposes implementor details | Hide implementation |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Abstraction, refined abstraction, implementor templates
- `references/examples.md` — Notification, report bridges with unit tests
