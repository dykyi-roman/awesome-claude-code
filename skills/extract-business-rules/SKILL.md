---
name: acc-extract-business-rules
description: Extracts validation rules, guards, business constraints, authorization rules, and invariants from domain code. Maps technical implementations to business terminology for non-technical stakeholders.
---

# Business Rules Extractor

## Overview

Identifies and catalogs business rules embedded in code — validation constraints, domain invariants, guards, authorization rules, and business policies. Translates technical implementations into business language.

## Rule Categories

| Category | Code Pattern | Business Meaning |
|----------|-------------|-----------------|
| Validation | Assert, validate, check | Input requirements |
| Invariant | Guard clause in constructor/method | Business constraint |
| Authorization | isAllowed, canPerform, Policy | Access control |
| Business Policy | If/match with domain logic | Business decision |
| State Guard | Status check before transition | Workflow rule |
| Limit/Threshold | Comparison with constant/config | Business limit |

## Detection Patterns

### Validation Rules

```bash
# Symfony validation attributes
Grep: "#\\[Assert\\\\" --glob "**/*.php"
Grep: "#\\[(NotBlank|NotNull|Length|Range|Email|Regex|Valid|Choice)" --glob "**/*.php"

# Laravel validation
Grep: "'required|'email|'min:|'max:|'unique:" --glob "**/*.php"
Grep: "\\$rules|->validate\\(" --glob "**/*.php"

# Custom validation
Grep: "function validate|function isValid|function check" --glob "**/Domain/**/*.php"
Grep: "throw.*Invalid|throw.*Validation" --glob "**/*.php"

# Value Object self-validation
Grep: "private function (validate|ensure|assert|guard)" --glob "**/*.php"
```

### Domain Invariants

```bash
# Guard clauses in constructors
Grep: "__construct" --glob "**/Domain/**/*.php" -A 20
# Look for: if (...) throw, match with exceptions

# Guard methods
Grep: "private function (ensure|guard|assert|verify)" --glob "**/Domain/**/*.php"

# Invariant enforcement
Grep: "throw new.*Exception" --glob "**/Domain/**/*.php"

# Business constraint patterns
Grep: "if.*<=.*0|if.*<.*0|if.*>.*MAX|if.*>=.*LIMIT" --glob "**/Domain/**/*.php"
Grep: "if.*empty|if.*null|if.*count.*==.*0" --glob "**/Domain/**/*.php"
```

### Authorization Rules

```bash
# Symfony voters
Grep: "extends Voter|implements VoterInterface" --glob "**/*.php"
Grep: "function voteOnAttribute" --glob "**/*.php"

# Laravel policies
Grep: "class.*Policy" --glob "**/*.php"
Grep: "function (view|create|update|delete|restore|forceDelete)" --glob "**/Policy/**/*.php"

# Custom authorization
Grep: "->isAllowed|->can\\(|->authorize\\(|->isGranted" --glob "**/*.php"
Grep: "#\\[IsGranted\\(|@IsGranted\\(" --glob "**/*.php"

# Role-based checks
Grep: "hasRole|isAdmin|isModerator|ROLE_" --glob "**/*.php"
```

### Business Policies

```bash
# Pricing rules
Grep: "discount|price|tax|fee|commission|markup" --glob "**/Domain/**/*.php"
Grep: "calculatePrice|calculateTotal|applyDiscount" --glob "**/*.php"

# Status/workflow transitions
Grep: "canTransitionTo|allowedTransitions|validTransitions" --glob "**/*.php"
Grep: "function (approve|reject|cancel|complete|archive|activate|deactivate)" --glob "**/Domain/**/*.php"

# Time-based rules
Grep: "isExpired|isActive|isWithin|deadline|expiresAt" --glob "**/*.php"
Grep: "new \\\\DateTimeImmutable|Carbon::" --glob "**/Domain/**/*.php"

# Quantity/limit rules
Grep: "MAX_|MIN_|LIMIT_|THRESHOLD" --glob "**/Domain/**/*.php"
Grep: "maxAttempts|maxRetries|maxItems|minAmount" --glob "**/*.php"
```

### State Guards

```bash
# Status checks before operations
Grep: "if.*status.*===|if.*state.*===" --glob "**/Domain/**/*.php"
Grep: "match.*status|match.*state" --glob "**/Domain/**/*.php"

# Enum-based state management
Grep: "enum.*Status|enum.*State" --glob "**/*.php"
Grep: "->status === |->getStatus\\(\\) ===" --glob "**/*.php"
```

## Analysis Process

1. **Scan** — Find all business rule patterns in code
2. **Extract** — Read each rule's implementation details
3. **Classify** — Categorize by type (validation, invariant, auth, policy)
4. **Translate** — Convert technical code to business language
5. **Map** — Connect rules to business entities/processes

### Translation Rules

| Technical Pattern | Business Translation |
|------------------|---------------------|
| `if ($amount <= 0) throw` | "Order amount must be positive" |
| `if ($user->getRole() !== 'admin')` | "Only administrators can perform this action" |
| `if ($order->status !== 'pending')` | "Order can only be modified while pending" |
| `if (count($items) > 100)` | "Maximum 100 items per order" |
| `if ($age < 18)` | "Customer must be at least 18 years old" |

## Output Format

```markdown
## Business Rules Catalog

### Summary
| Category | Count | Critical |
|----------|-------|----------|
| Validation Rules | 15 | 3 |
| Domain Invariants | 8 | 5 |
| Authorization Rules | 12 | 4 |
| Business Policies | 6 | 2 |
| State Guards | 4 | 3 |
| **Total** | **45** | **17** |

### Domain Invariants (Business Constraints)

| # | Rule (Business Language) | Location | Enforcement |
|---|--------------------------|----------|-------------|
| INV-1 | Order amount must be positive | Order.php:25 | Constructor guard |
| INV-2 | Order must have at least one item | Order.php:30 | Constructor guard |
| INV-3 | Customer email must be valid format | Email.php:15 | Value Object |
| INV-4 | Payment cannot exceed order total | Payment.php:22 | Method guard |

### Validation Rules (Input Requirements)

| # | Field | Rule | Location |
|---|-------|------|----------|
| VAL-1 | email | Required, valid format | CreateUserRequest.php |
| VAL-2 | name | Required, 2-100 chars | CreateUserRequest.php |
| VAL-3 | amount | Required, positive integer | CreateOrderDTO.php |

### Authorization Rules (Access Control)

| # | Action | Who Can | Where Enforced |
|---|--------|---------|----------------|
| AUTH-1 | View orders | Owner or Admin | OrderPolicy::view |
| AUTH-2 | Cancel order | Owner (if pending) | OrderPolicy::cancel |
| AUTH-3 | Manage users | Admin only | UserVoter |

### Business Policies

| # | Policy | Rule | Location |
|---|--------|------|----------|
| POL-1 | Free shipping | Orders over $100 | ShippingCalculator.php:45 |
| POL-2 | Loyalty discount | 10% for VIP customers | PriceCalculator.php:30 |
| POL-3 | Order expiry | Unpaid orders expire in 24h | OrderExpiryPolicy.php |

### State Transition Rules

| Entity | From State | To State | Condition |
|--------|-----------|----------|-----------|
| Order | pending | confirmed | Payment received |
| Order | confirmed | shipped | Items packed |
| Order | any | cancelled | By owner if not shipped |
```

## Integration

This skill is used by:
- `acc-business-logic-analyst` — catalogs all business rules
- `acc-explain-business-process` — references rules in process descriptions
- `acc-extract-domain-concepts` — connects rules to domain entities
