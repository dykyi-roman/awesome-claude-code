# SOLID Violations Analysis Report

## Project Information

| Field | Value |
|-------|-------|
| Project | `{project_name}` |
| Date | `{date}` |
| Scope | `{scope}` |
| Files Analyzed | `{file_count}` |
| Analyzer | Claude Code |

---

## Executive Summary

### Overall Score: {score}/100

| Principle | Status | Critical | Warning | Info | Score |
|-----------|--------|----------|---------|------|-------|
| **S** Single Responsibility | {emoji} | {count} | {count} | {count} | {score}/20 |
| **O** Open/Closed | {emoji} | {count} | {count} | {count} | {score}/20 |
| **L** Liskov Substitution | {emoji} | {count} | {count} | {count} | {score}/20 |
| **I** Interface Segregation | {emoji} | {count} | {count} | {count} | {score}/20 |
| **D** Dependency Inversion | {emoji} | {count} | {count} | {count} | {score}/20 |

### Key Findings

- **{X} Critical violations** requiring immediate attention
- **{X} Warning violations** for planned refactoring
- **{X} Info items** to monitor

---

## Critical Violations

### SRP-001: God Class Detected

| Field | Value |
|-------|-------|
| Severity | CRITICAL |
| File | `src/Service/UserManager.php` |
| Lines | 847 |
| Public Methods | 23 |
| Dependencies | 12 |

**Problem:**
Class handles user registration, authentication, profile management, email notifications, and reporting - multiple reasons to change.

**Evidence:**
```php
final class UserManager
{
    // Authentication (reason 1)
    public function login() { /* ... */ }
    public function logout() { /* ... */ }

    // Registration (reason 2)
    public function register() { /* ... */ }
    public function validateEmail() { /* ... */ }

    // Profile (reason 3)
    public function updateProfile() { /* ... */ }

    // Notifications (reason 4)
    public function sendWelcomeEmail() { /* ... */ }

    // Reporting (reason 5)
    public function generateReport() { /* ... */ }
}
```

**Recommendation:**
Extract into focused classes:

| New Class | Responsibility | Skill |
|-----------|----------------|-------|
| `RegisterUserHandler` | User registration | `acc-create-use-case` |
| `AuthenticationService` | Login/logout | `acc-create-domain-service` |
| `UserProfileService` | Profile management | `acc-create-domain-service` |
| `UserNotificationService` | Email notifications | `acc-create-domain-service` |
| `UserReportGenerator` | Reporting | `acc-create-read-model` |

---

### OCP-001: Type Switch Prevents Extension

| Field | Value |
|-------|-------|
| Severity | CRITICAL |
| File | `src/Payment/PaymentProcessor.php:45` |

**Problem:**
Adding new payment types requires modifying existing code.

**Evidence:**
```php
public function process(Payment $payment): Result
{
    return match ($payment->type) {
        'card' => $this->processCard($payment),
        'paypal' => $this->processPaypal($payment),
        'bank' => $this->processBankTransfer($payment),
        // Must add case for new types!
    };
}
```

**Recommendation:**
Apply Strategy pattern with polymorphic dispatch.

```php
interface PaymentGateway
{
    public function supports(Payment $payment): bool;
    public function process(Payment $payment): Result;
}
```

**Skill:** `acc-create-strategy`

---

### LSP-001: Contract Violation

| Field | Value |
|-------|-------|
| Severity | CRITICAL |
| File | `src/Cache/ReadOnlyCache.php:34` |

**Problem:**
`ReadOnlyCache` throws `NotImplementedException` for write methods, violating `Cache` interface contract.

**Evidence:**
```php
final class ReadOnlyCache implements Cache
{
    public function set(string $key, mixed $value): void
    {
        throw new NotImplementedException('Read-only cache');
    }
}
```

**Recommendation:**
Split interface:
- `CacheReader` - read operations
- `CacheWriter` - write operations
- `Cache extends CacheReader, CacheWriter`

---

## Warning Violations

### ISP-001: Fat Interface

| Field | Value |
|-------|-------|
| Severity | WARNING |
| File | `src/Repository/UserRepositoryInterface.php` |
| Methods | 12 |

**Problem:**
Interface has 12 methods. Most clients use only 2-3 methods.

**Evidence:**
```php
interface UserRepositoryInterface
{
    public function find(UserId $id): ?User;
    public function findByEmail(Email $email): ?User;
    public function findAll(): array;
    public function save(User $user): void;
    public function delete(User $user): void;
    public function count(): int;
    public function findActive(): array;
    public function findByRole(Role $role): array;
    public function export(): string;
    public function import(string $data): void;
    public function findRecent(int $days): array;
    public function purgeInactive(): int;
}
```

**Recommendation:**
Segregate into focused interfaces:

| Interface | Methods |
|-----------|---------|
| `UserReader` | find, findByEmail |
| `UserWriter` | save, delete |
| `UserQueryRepository` | findAll, findActive, findByRole, findRecent |
| `UserDataTransfer` | export, import |
| `UserMaintenance` | purgeInactive, count |

---

### DIP-001: Concrete Dependency

| Field | Value |
|-------|-------|
| Severity | WARNING |
| File | `src/Service/OrderService.php:15` |

**Problem:**
Constructor depends on concrete `DoctrineOrderRepository` instead of interface.

**Evidence:**
```php
public function __construct(
    private DoctrineOrderRepository $orders,  // Concrete!
    private StripePaymentGateway $payment,    // Concrete!
)
```

**Recommendation:**
- Create `OrderRepository` interface in Domain layer
- Create `PaymentGateway` interface
- Type hint interfaces instead of implementations

**Skill:** `acc-create-repository`

---

### DIP-002: Hidden Dependencies

| Field | Value |
|-------|-------|
| Severity | WARNING |
| File | `src/Service/NotificationService.php:28` |

**Problem:**
Static calls and direct instantiation hide dependencies.

**Evidence:**
```php
public function send(Notification $notification): void
{
    $logger = Logger::getInstance();     // Hidden static
    $mailer = new SmtpMailer();          // Hidden new
    $config = config('mail.from');       // Hidden global
}
```

**Recommendation:**
Inject all dependencies through constructor.

---

## Info Items

### SRP-INFO-001: Approaching Threshold

| Field | Value |
|-------|-------|
| Severity | INFO |
| File | `src/Domain/Order/Order.php` |
| Lines | 280 |

**Description:**
Entity approaching 300-line threshold. Monitor for SRP degradation.

**Recommendation:**
Consider extracting:
- Pricing logic to `OrderPricingService`
- Validation to `OrderSpecification`

---

### OCP-INFO-001: Minor Type Check

| Field | Value |
|-------|-------|
| Severity | INFO |
| File | `src/Notification/NotificationFactory.php:12` |

**Description:**
Single type check, but currently only 2 types.

**Recommendation:**
Monitor. Convert to strategy if >3 types added.

---

## Metrics Summary

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Max class size | 847 LOC | ≤200 LOC | CRITICAL |
| Max dependencies | 12 | ≤7 | CRITICAL |
| Type switches | 5 | 0 | WARNING |
| NotImplementedException | 3 | 0 | CRITICAL |
| Fat interfaces (>5 methods) | 8 | 0 | WARNING |
| Concrete dependencies | 23 | 0 | WARNING |
| Interface coverage | 45% | 100% | WARNING |

---

## Remediation Roadmap

### Phase 1: Critical (Immediate)

| Task | File | Effort | Skill |
|------|------|--------|-------|
| Split UserManager | `UserManager.php` | High | `acc-create-use-case` |
| Strategy for payments | `PaymentProcessor.php` | Medium | `acc-create-strategy` |
| Fix LSP violation | `ReadOnlyCache.php` | Low | Manual |

### Phase 2: Warning (Sprint 1-2)

| Task | File | Effort | Skill |
|------|------|--------|-------|
| Segregate UserRepository | `UserRepositoryInterface.php` | Medium | Manual |
| Extract interfaces | Multiple | Medium | `acc-create-repository` |
| Remove hidden deps | `NotificationService.php` | Low | Manual |

### Phase 3: Info (Backlog)

| Task | File | Effort |
|------|------|--------|
| Monitor Order entity | `Order.php` | - |
| Track type checks | `NotificationFactory.php` | - |

---

## Detection Commands Used

```bash
# SRP: Large classes
find . -name "*.php" -path "*/src/*" -exec wc -l {} \; | awk '$1 > 400'

# OCP: Type switches
grep -rn "switch.*type\|match.*::class" --include="*.php" src/

# LSP: Broken contracts
grep -rn "NotImplemented\|NotSupported" --include="*.php" src/

# ISP: Fat interfaces
for f in $(find . -name "*.php" -exec grep -l "^interface" {} \;); do
  c=$(grep -c "public function" "$f")
  [ $c -gt 5 ] && echo "$f: $c methods"
done

# DIP: Concrete dependencies
grep -rn "new\s\+[A-Z]" --include="*.php" src/ | grep -v "Exception\|DateTime"
```

---

## Appendix: Skills Reference

| Pattern | Skill | Use When |
|---------|-------|----------|
| Use Case | `acc-create-use-case` | Extracting application logic |
| Domain Service | `acc-create-domain-service` | Cross-entity domain logic |
| Strategy | `acc-create-strategy` | Replacing type switches |
| Repository | `acc-create-repository` | Creating persistence interfaces |
| Value Object | `acc-create-value-object` | Extracting data with behavior |
| Factory | `acc-create-factory` | Complex object creation |
| Decorator | `acc-create-decorator` | Adding behavior transparently |
| Chain of Responsibility | `acc-create-chain-of-responsibility` | Handler chains |
