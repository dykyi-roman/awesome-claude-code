# SOLID Audit Report Template

## Project Information

| Field | Value |
|-------|-------|
| Project | `{project_name}` |
| Date | `{date}` |
| Scope | `{scope}` |
| Auditor | Claude Code |

---

## Executive Summary

| Principle | Status | Critical | Warning | Info |
|-----------|--------|----------|---------|------|
| **S** - Single Responsibility | {status} | {count} | {count} | {count} |
| **O** - Open/Closed | {status} | {count} | {count} | {count} |
| **L** - Liskov Substitution | {status} | {count} | {count} | {count} |
| **I** - Interface Segregation | {status} | {count} | {count} | {count} |
| **D** - Dependency Inversion | {status} | {count} | {count} | {count} |

**Overall Score:** {score}/100

---

## Critical Violations

### SRP-001: God Class Detected

| Field | Value |
|-------|-------|
| File | `src/Service/UserManager.php` |
| Lines | 847 |
| Dependencies | 12 |
| Severity | CRITICAL |

**Description:**
Class has multiple responsibilities: authentication, registration, email, reporting.

**Evidence:**
```php
final class UserManager
{
    public function register() { /* ... */ }
    public function login() { /* ... */ }
    public function sendEmail() { /* ... */ }
    public function generateReport() { /* ... */ }
}
```

**Recommendation:**
Extract into focused classes:
- `UserRegistrationHandler` - Use skill: `acc-create-use-case`
- `UserAuthenticationService` - Use skill: `acc-create-domain-service`
- `UserEmailNotifier` - Use skill: `acc-create-domain-service`
- `UserReportGenerator` - Use skill: `acc-create-read-model`

---

### OCP-001: Type Switch Detected

| Field | Value |
|-------|-------|
| File | `src/Payment/PaymentProcessor.php:45` |
| Severity | CRITICAL |

**Description:**
Switch statement on payment type requires modification for new payment methods.

**Evidence:**
```php
match ($payment->type) {
    'card' => $this->processCard($payment),
    'paypal' => $this->processPaypal($payment),
    // Must modify for new types
};
```

**Recommendation:**
Apply Strategy pattern:
- Create `PaymentGateway` interface - Use skill: `acc-create-strategy`
- Implement per-type strategies
- Use DI container tags for auto-registration

---

### LSP-001: Contract Violation

| Field | Value |
|-------|-------|
| File | `src/Cache/ReadOnlyCache.php:23` |
| Severity | CRITICAL |

**Description:**
`ReadOnlyCache` throws `NotImplementedException` for write methods, violating `Cache` interface contract.

**Evidence:**
```php
public function set(string $key, mixed $value): void
{
    throw new NotImplementedException();
}
```

**Recommendation:**
Split interface:
- `CacheReader` for read operations
- `CacheWriter` for write operations
- `Cache extends CacheReader, CacheWriter` for full implementation

---

## Warning Violations

### ISP-001: Fat Interface

| Field | Value |
|-------|-------|
| File | `src/Repository/UserRepository.php` |
| Methods | 12 |
| Severity | WARNING |

**Description:**
Interface has 12 methods. Clients depend on more methods than they use.

**Recommendation:**
Segregate into:
- `UserReader` (find, findByEmail, findAll)
- `UserWriter` (save, delete)
- `UserStats` (count, sum)

---

### DIP-001: Concrete Dependency

| Field | Value |
|-------|-------|
| File | `src/Service/OrderService.php:15` |
| Severity | WARNING |

**Description:**
Constructor depends on concrete `DoctrineOrderRepository` instead of interface.

**Evidence:**
```php
public function __construct(
    private DoctrineOrderRepository $orders,
)
```

**Recommendation:**
- Create `OrderRepository` interface in Domain layer
- Type hint interface instead of implementation
- Use skill: `acc-create-repository`

---

## Info Items

### SRP-INFO-001: Consider Extraction

| Field | Value |
|-------|-------|
| File | `src/Entity/Order.php` |
| Lines | 280 |
| Severity | INFO |

**Description:**
Class approaching complexity threshold. Monitor for SRP violation.

---

## Recommendations Summary

### Immediate Actions (Critical)

1. **Refactor `UserManager`** into focused handlers
2. **Apply Strategy pattern** to `PaymentProcessor`
3. **Split `Cache` interface** for read/write separation

### Planned Actions (Warning)

1. **Segregate `UserRepository`** interface
2. **Extract interface** for `DoctrineOrderRepository`
3. **Review constructor dependencies** for concrete types

### Future Considerations (Info)

1. **Monitor `Order` class** size
2. **Consider extracting** pricing logic from Order

---

## Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Average class size | 320 LOC | <200 LOC | WARNING |
| Max dependencies | 12 | ≤7 | CRITICAL |
| Interface method average | 8 | ≤5 | WARNING |
| Concrete dependencies | 23% | 0% | WARNING |

---

## Skills for Remediation

| Violation Type | Recommended Skill |
|----------------|-------------------|
| God Class | `acc-create-use-case`, `acc-create-domain-service` |
| Type Switch | `acc-create-strategy` |
| Interface Split | Manual refactoring |
| Repository Interface | `acc-create-repository` |
| Domain Service | `acc-create-domain-service` |
| Value Object Extraction | `acc-create-value-object` |

---

## Appendix: Detection Commands Used

```bash
# SRP: God classes
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 500'

# OCP: Type switches
grep -rn "switch.*type\|match.*::class" --include="*.php"

# LSP: Contract violations
grep -rn "NotImplemented\|NotSupported" --include="*.php"

# ISP: Fat interfaces
grep -rn "^interface\s" --include="*.php" -A 30 | grep -c "function"

# DIP: Concrete dependencies
grep -rn "__construct" --include="*.php" -A 10 | grep -v "Interface"
```
