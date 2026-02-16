# GRASP Audit Report Template

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
| Information Expert | {status} | {count} | {count} | {count} |
| Creator | {status} | {count} | {count} | {count} |
| Controller | {status} | {count} | {count} | {count} |
| Low Coupling | {status} | {count} | {count} | {count} |
| High Cohesion | {status} | {count} | {count} | {count} |
| Polymorphism | {status} | {count} | {count} | {count} |
| Pure Fabrication | {status} | {count} | {count} | {count} |
| Indirection | {status} | {count} | {count} | {count} |
| Protected Variations | {status} | {count} | {count} | {count} |

**Overall Score:** {score}/100

---

## Critical Violations

### IE-001: Feature Envy Detected

| Field | Value |
|-------|-------|
| File | `src/Service/OrderReporter.php:45` |
| Principle | Information Expert |
| Severity | CRITICAL |

**Description:**
Method `generateSummary` accesses `Order` internal data extensively instead of delegating to Order.

**Evidence:**
```php
foreach ($order->getLines() as $line) {
    $line->getProduct()->getName();
    $line->getProduct()->getPrice()->format();
    $line->getQuantity()->getValue();
    // ...
}
```

**Recommendation:**
Move summary generation to Order class. Use skill: `acc-create-entity`

---

### CTRL-001: Fat Controller

| Field | Value |
|-------|-------|
| File | `src/Controller/OrderController.php` |
| Lines | 245 |
| Principle | Controller |
| Severity | CRITICAL |

**Description:**
Controller contains business logic, validation, persistence, and side effects.

**Recommendation:**
Extract to use case handler. Use skill: `acc-create-use-case`

---

### LC-001: High Coupling

| Field | Value |
|-------|-------|
| File | `src/Service/OrderService.php` |
| Dependencies | 12 |
| Principle | Low Coupling |
| Severity | CRITICAL |

**Description:**
Class has 12 constructor dependencies, indicating too many responsibilities.

**Recommendation:**
Split into focused services with 3-5 dependencies each.

---

## Warning Violations

### POLY-001: Type Switch

| Field | Value |
|-------|-------|
| File | `src/Payment/PaymentProcessor.php:78` |
| Principle | Polymorphism |
| Severity | WARNING |

**Description:**
Match statement on payment type requires modification for new types.

**Evidence:**
```php
match ($payment->type) {
    'card' => $this->processCard($payment),
    'paypal' => $this->processPaypal($payment),
};
```

**Recommendation:**
Apply Strategy pattern. Use skill: `acc-create-strategy`

---

### IND-001: Missing Indirection

| Field | Value |
|-------|-------|
| File | `src/Service/NotificationService.php:23` |
| Principle | Indirection |
| Severity | WARNING |

**Description:**
Direct instantiation of external service client without adapter.

**Evidence:**
```php
$twilio = new \Twilio\Rest\Client($sid, $token);
```

**Recommendation:**
Create adapter interface. Use skill: `acc-create-anti-corruption-layer`

---

## Info Items

### HC-INFO-001: Consider Extraction

| Field | Value |
|-------|-------|
| File | `src/Domain/Entity/Order.php` |
| Lines | 320 |
| Principle | High Cohesion |
| Severity | INFO |

**Description:**
Entity approaching size limit. Monitor for cohesion degradation.

---

## Recommendations Summary

### Immediate Actions (Critical)

1. **Move feature envy logic** to domain entities
2. **Extract fat controller** logic to handlers
3. **Split high-coupling services** into focused classes

### Planned Actions (Warning)

1. **Replace type switches** with Strategy pattern
2. **Add adapters** for external system integration
3. **Review object creation** locations

### Future Considerations (Info)

1. **Monitor class sizes** for cohesion
2. **Consider Pure Fabrication** for cross-cutting concerns

---

## Metrics

| Metric | Current | Target | Status |
|--------|---------|--------|--------|
| Average class size | 280 LOC | <200 LOC | WARNING |
| Max dependencies | 12 | ≤7 | CRITICAL |
| Type switches | 5 | 0 | WARNING |
| Direct external calls | 8 | 0 | WARNING |
| Fat controllers | 3 | 0 | CRITICAL |

---

## Skills for Remediation

| Violation Type | Recommended Skill |
|----------------|-------------------|
| Feature Envy | `acc-create-entity`, `acc-create-value-object` |
| Fat Controller | `acc-create-use-case`, `acc-create-command` |
| Type Switch | `acc-create-strategy` |
| Missing Indirection | `acc-create-anti-corruption-layer` |
| Low Cohesion | `acc-create-domain-service` |
| Object Creation | `acc-create-factory` |

---

## Appendix: Detection Commands Used

```bash
# Information Expert: Feature Envy
grep -rn "->get.*()->get.*()->" --include="*.php"

# Creator: Random creation
grep -rn "new\s\+[A-Z][a-z]*[A-Z]" --include="*.php"

# Controller: Fat controllers
find . -path "*/Controller/*.php" -exec wc -l {} \;

# Low Coupling: Dependency count
grep -rn "__construct" --include="*.php" -A 15

# High Cohesion: Large classes
find . -name "*.php" -exec wc -l {} \; | awk '$1 > 400'

# Polymorphism: Type switches
grep -rn "match.*type\|switch.*instanceof" --include="*.php"

# Indirection: Direct external
grep -rn "new.*\\\\Stripe\|new.*\\\\Aws" --include="*.php"
```
