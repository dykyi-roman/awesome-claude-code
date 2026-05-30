---
name: create-facade
description: Generates Facade pattern for PHP 8.4. Creates simplified interface to complex subsystems. Includes unit tests.
---

# Facade Pattern Generator

Creates Facade pattern infrastructure for providing simplified access to complex subsystems.

## When to Use

| Scenario | Example |
|----------|---------|
| Complex subsystem simplification | Order facade combining inventory, payment, shipping |
| Multiple service orchestration | Notification facade coordinating email, SMS, push |
| Legacy system wrapping | Facade hiding complex legacy APIs |
| Layered system access | Application layer facade for domain services |

## Component Characteristics

### Facade
- Simple unified interface
- Delegates to subsystem classes
- No business logic, only orchestration
- Lives at the coordination layer that wires the subsystems together

### Subsystem Classes
- Independent complex operations
- Can be used directly or through facade
- Domain services / infrastructure adapters / external clients

---

## Generation Process

### Step 1: Generate Facade

Place at the coordination layer that wires together the subsystems.

1. `{Name}Facade.php` — Unified interface to subsystem

### Step 2: Identify Subsystem Classes (Existing)

These can be domain services, persistence adapters, or external API clients — wherever the related functionality lives in your project.

1. Services, Repositories, External APIs
2. Multiple components with related functionality

### Step 3: Generate Tests

1. `{FacadeName}Test.php` — Facade orchestration verification

---

## File Placement

| Component | Path |
|-----------|------|
| Facade | `src/{architecture-path}/Facade/{Name}Facade.php` |
| Subsystem Classes | Wherever the related functionality already lives in your project |
| Unit Tests | `tests/Unit/{architecture-path}/Facade/` |

> `{architecture-path}` represents your project's architecture-specific folders. The facade typically lives at the coordination layer (Application in Clean/Layered, the hexagon in Hexagonal, the feature folder in Package-by-Feature). Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Facade | `{Name}Facade` | `OrderFacade` |
| Test | `{ClassName}Test` | `OrderFacadeTest` |

---

## Quick Template Reference

### Facade

```php
final readonly class {Name}Facade
{
    public function __construct(
        private {SubsystemA} $subsystemA,
        private {SubsystemB} $subsystemB,
        private {SubsystemC} $subsystemC
    ) {}

    public function {complexOperation}({params}): {returnType}
    {
        $stepA = $this->subsystemA->{methodA}({params});
        $stepB = $this->subsystemB->{methodB}($stepA);
        $stepC = $this->subsystemC->{methodC}($stepB);

        return $stepC;
    }
}
```

---

## Usage Example

```php
// Without facade - complex coordination
$inventory = $inventoryService->reserve($productId, $quantity);
$payment = $paymentService->charge($amount, $token);
$shipment = $shippingService->schedule($address, $inventory);
$order = $orderRepository->save(new Order(...));
$notificationService->sendConfirmation($order);

// With facade - simple call
$order = $orderFacade->placeOrder($command);
```

---

## Common Facades

| Facade | Purpose |
|--------|---------|
| OrderFacade | Coordinate inventory, payment, shipping, notifications |
| NotificationFacade | Send via email, SMS, push, Slack |
| ReportFacade | Generate PDF, Excel, CSV reports |
| UserRegistrationFacade | Validate, create account, send welcome email |
| PaymentFacade | Authorize, charge, record, notify |
| ExportFacade | Fetch data, transform, format, save file |

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| God Facade | Facade does too much | Split into focused facades |
| Business Logic in Facade | Facade makes decisions | Move logic to domain services |
| Tight Coupling | Facade depends on concrete classes | Inject interfaces |
| No Subsystem Access | Clients can't bypass facade | Allow direct subsystem use |
| Stateful Facade | Facade holds state between calls | Keep facades stateless |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Facade templates for order, notification, report systems
- `references/examples.md` — OrderFacade, NotificationFacade, ReportFacade with unit tests
