---
name: acc-create-adapter
description: Generates Adapter pattern for PHP 8.4. Converts incompatible interfaces, wraps legacy code and external libraries. Includes unit tests.
---

# Adapter Pattern Generator

Creates Adapter pattern infrastructure for converting incompatible interfaces into expected ones.

## When to Use

| Scenario | Example |
|----------|---------|
| Legacy code integration | Wrap old API with new interface |
| Third-party library wrapping | Stripe SDK, AWS SDK adapters |
| Interface standardization | Multiple payment gateways with unified interface |
| Backward compatibility | Support old and new interfaces |

## Component Characteristics

### Target Interface
- Defines expected operations
- Client code depends on this
- Domain layer contract

### Adapter
- Implements target interface
- Wraps adaptee (existing class)
- Translates calls between interfaces

### Adaptee
- Existing incompatible class
- Legacy code or external library
- Not modified by adapter

---

## Generation Process

### Step 1: Generate Target Interface

**Path:** `src/Domain/{BoundedContext}/`

1. `{Name}Interface.php` — Expected interface contract

### Step 2: Generate Adapter

**Path:** `src/Infrastructure/{BoundedContext}/Adapter/`

1. `{Provider}{Name}Adapter.php` — Converts adaptee to target interface
2. `{Legacy}{Name}Adapter.php` — Wraps legacy code
3. `{External}{Name}Adapter.php` — Wraps third-party library

### Step 3: Generate Tests

1. `{AdapterName}Test.php` — Adapter behavior verification

---

## File Placement

| Component | Path |
|-----------|------|
| Target Interface | `src/Domain/{BoundedContext}/` |
| Adapter | `src/Infrastructure/{BoundedContext}/Adapter/` |
| Adaptee (existing) | External library or legacy code |
| Unit Tests | `tests/Unit/Infrastructure/{BoundedContext}/Adapter/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Target Interface | `{Name}Interface` | `PaymentGatewayInterface` |
| Adapter | `{Provider}{Name}Adapter` | `StripePaymentGatewayAdapter` |
| Test | `{ClassName}Test` | `StripePaymentGatewayAdapterTest` |

---

## Quick Template Reference

### Target Interface

```php
interface {Name}Interface
{
    public function {operation}({params}): {returnType};
}
```

### Adapter

```php
final readonly class {Provider}{Name}Adapter implements {Name}Interface
{
    public function __construct(
        private {Adaptee} $adaptee
    ) {}

    public function {operation}({params}): {returnType}
    {
        // Translate params to adaptee format
        $adapteeResult = $this->adaptee->{adapteeMethod}({adapteeParams});

        // Convert result to target format
        return {convertedResult};
    }
}
```

---

## Usage Example

```php
// Stripe SDK is the adaptee
$stripeClient = new \Stripe\StripeClient($apiKey);

// Adapter makes it compatible with our interface
$paymentGateway = new StripePaymentGatewayAdapter($stripeClient);

// Use through our domain interface
$result = $paymentGateway->charge($amount, $token);
```

---

## Common Adapters

| Adapter | Purpose |
|---------|---------|
| PaymentGatewayAdapter | Wrap Stripe, PayPal, Square APIs |
| StorageAdapter | Wrap AWS S3, Google Cloud Storage |
| MessengerAdapter | Wrap Slack, Discord, Telegram APIs |
| EmailAdapter | Wrap SendGrid, Mailgun, AWS SES |
| CacheAdapter | Wrap Redis, Memcached, APCu |
| LoggerAdapter | Wrap Monolog, Syslog, custom loggers |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Leaky Adapter | Exposing adaptee details | Return only target interface types |
| Multiple Responsibilities | Adapter doing business logic | Keep adapters focused on translation |
| Tight Coupling | Adapter depends on concrete adaptee | Accept interface when possible |
| Heavy Translation | Complex conversions in adapter | Extract translator services |
| Missing Error Handling | Adaptee exceptions leak | Catch and convert to domain exceptions |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Target Interface, Adapter templates for payment, storage, messaging
- `references/examples.md` — Stripe, PayPal, AWS S3, legacy user adapters with unit tests
