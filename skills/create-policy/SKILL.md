---
name: create-policy
description: Generates Policy pattern for PHP 8.4. Creates encapsulated business rules for authorization, validation, and domain constraints. Includes unit tests.
---

# Policy Pattern Generator

Creates Policy pattern infrastructure for encapsulating business rules and authorization logic.

## When to Use

| Scenario | Example |
|----------|---------|
| Authorization checks | Can user cancel order? |
| Business rule validation | Is discount applicable? |
| Complex conditions | Multiple rules combined |
| Auditable decisions | Log why access denied |

## Component Characteristics

### PolicyInterface
- Single responsibility rule
- Returns authorization result
- Provides denial reasons

### Policy Implementation
- Encapsulates one business rule
- Stateless evaluation
- Composable with other policies

### PolicyResult
- Success/failure status
- Denial reasons
- Metadata for logging

---

## Generation Process

### Step 1: Generate Shared Components

Place alongside other shared domain primitives.

1. `PolicyResult.php` — Result value object with and/or composition
2. `CompositionMode.php` — Enum for AllMustPass/AnyMustPass

### Step 2: Generate Policy Interface

Place alongside the bounded context's domain code.

1. `{Name}PolicyInterface.php` — Policy contract

### Step 3: Generate Concrete Policies

Co-located with the interface.

1. `{Rule1}Policy.php` — First rule implementation
2. `{Rule2}Policy.php` — Second rule implementation
3. `{Name}Policy.php` — Composite policy combining rules

### Step 4: Generate Exception

Place with other shared domain exceptions.

1. `PolicyViolationException.php` — Exception with policy context

### Step 5: Generate Tests

1. `{Rule}PolicyTest.php` — Individual rule tests
2. `{Name}PolicyTest.php` — Composite policy tests
3. `PolicyResultTest.php` — Result composition tests

---

## File Placement

| Component | Path |
|-----------|------|
| Policy Interface | `src/{architecture-path}/Policy/{Name}PolicyInterface.php` |
| Policy Implementation | `src/{architecture-path}/Policy/{Rule}Policy.php` |
| PolicyResult | `src/{architecture-path}/Policy/PolicyResult.php` |
| Exception | `src/{architecture-path}/Exception/PolicyViolationException.php` |
| Unit Tests | `tests/Unit/{architecture-path}/Policy/` |

> `{architecture-path}` represents your project's architecture-specific folders. The PolicyResult + composition types typically live with other shared domain primitives; per-context policies live with the bounded context's domain code. Adjust to your project's layout.

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Interface | `{Name}PolicyInterface` | `OrderCancellationPolicyInterface` |
| Implementation | `{Rule}Policy` | `OrderOwnershipPolicy` |
| Composite | `{Name}Policy` | `OrderCancellationPolicy` |
| Result | `PolicyResult` | `PolicyResult` |
| Exception | `PolicyViolationException` | `PolicyViolationException` |
| Test | `{ClassName}Test` | `OrderOwnershipPolicyTest` |

---

## Quick Template Reference

### PolicyInterface

```php
interface {Name}PolicyInterface
{
    public function evaluate({SubjectType} $subject, {ResourceType} $resource): PolicyResult;
    public function getRuleName(): string;
}
```

### PolicyResult

```php
final readonly class PolicyResult
{
    public static function allow(): self;
    public static function deny(string $reason, array $metadata = []): self;
    public function isAllowed(): bool;
    public function isDenied(): bool;
    public function and(self $other): self; // Both must pass
    public function or(self $other): self;  // Either can pass
}
```

### Policy Implementation

```php
final readonly class {Rule}Policy implements {Name}PolicyInterface
{
    public function evaluate({Subject} $subject, {Resource} $resource): PolicyResult
    {
        if ({condition}) {
            return PolicyResult::allow();
        }
        return PolicyResult::deny('{reason}', ['context' => 'data']);
    }

    public function getRuleName(): string
    {
        return '{rule_name}';
    }
}
```

### Composite Policy

```php
final readonly class {Name}Policy implements {Name}PolicyInterface
{
    public function evaluate({Subject} $subject, {Resource} $resource): PolicyResult
    {
        return $this->rule1Policy->evaluate($subject, $resource)
            ->and($this->rule2Policy->evaluate($subject, $resource))
            ->and($this->rule3Policy->evaluate($subject, $resource));
    }
}
```

---

## Usage Example

```php
// In UseCase
$result = $this->cancellationPolicy->evaluate($user, $order);

if ($result->isDenied()) {
    throw new PolicyViolationException(
        $this->cancellationPolicy->getRuleName(),
        $result->getReason(),
        $result->metadata
    );
}

$order->cancel($reason);
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| Side Effects | Policy modifies state | Keep evaluation pure |
| Boolean Returns | No denial reason | Use PolicyResult |
| Fat Policies | Too many rules | Split into composable policies |
| Hardcoded Values | Can't configure | Inject thresholds |
| No Logging Context | Can't debug | Include metadata |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Policy, composite, result templates
- `references/examples.md` — Order cancellation policies and tests
