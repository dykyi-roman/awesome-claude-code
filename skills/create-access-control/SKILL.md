---
name: create-access-control
description: Generates Access Control components for PHP 8.4. Creates RBAC/ABAC components with PermissionInterface, RoleInterface, VoterInterface, AccessDecisionManager. Includes unit tests.
---

# Access Control Generator

Creates access control infrastructure for RBAC/ABAC authorization patterns.

## When to Use

| Scenario | Example |
|----------|---------|
| Role-based access | Admin, editor, viewer roles |
| Resource ownership | Users can only edit own resources |
| Attribute-based rules | Access based on resource state or user attributes |
| Complex authorization | Multiple voters with different strategies |

## Component Characteristics

### Permission
- Enum defining available permissions
- Hierarchical: parent permissions include children
- Type-safe, no magic strings

### Role
- Value Object encapsulating role with permissions
- Supports role hierarchy (admin inherits editor permissions)
- Immutable, self-validating

### VoterInterface
- Symfony-style voter contract
- Returns GRANT, DENY, or ABSTAIN
- Single responsibility: one voter per concern

### AccessDecisionManager
- Aggregates multiple voters
- Strategies: affirmative (one grant), unanimous (all grant), consensus (majority grants)
- Configurable per security context

### ResourceOwnerVoter
- Checks if authenticated user owns the resource
- Works with any entity implementing OwnableInterface
- Returns ABSTAIN for non-ownable resources

### RoleVoter
- Checks if user has required role for the permission
- Supports role hierarchy traversal
- Returns ABSTAIN when permission not role-based

---

## Generation Process

### Step 1: Generate Core Components

**Path:** `src/Infrastructure/Security/AccessControl/`

1. `Permission.php` — Permission enum
2. `Role.php` — Role value object with hierarchy
3. `AccessSubject.php` — Value object wrapping the authenticated user context

### Step 2: Generate Voter System

**Path:** `src/Infrastructure/Security/AccessControl/`

1. `VoterInterface.php` — Voter contract with GRANT/DENY/ABSTAIN
2. `Vote.php` — Vote result enum
3. `AccessDecisionManager.php` — Voter aggregation with strategies
4. `DecisionStrategy.php` — Strategy enum (affirmative, unanimous, consensus)

### Step 3: Generate Concrete Voters

**Path:** `src/Infrastructure/Security/AccessControl/Voter/`

1. `RoleVoter.php` — Role hierarchy voter
2. `ResourceOwnerVoter.php` — Resource ownership voter

### Step 4: Generate Tests

1. `RoleTest.php` — Role hierarchy tests
2. `AccessDecisionManagerTest.php` — Strategy decision tests
3. `RoleVoterTest.php` — Role voter tests

---

## File Placement

| Component | Path |
|-----------|------|
| Core Classes | `src/Infrastructure/Security/AccessControl/` |
| Voters | `src/Infrastructure/Security/AccessControl/Voter/` |
| Unit Tests | `tests/Unit/Infrastructure/Security/AccessControl/` |

---

## Naming Conventions

| Component | Pattern | Example |
|-----------|---------|---------|
| Permission | `Permission` | `Permission::Edit` |
| Role | `Role` | `Role` |
| Voter Interface | `VoterInterface` | `VoterInterface` |
| Concrete Voter | `{Context}Voter` | `RoleVoter` |
| Decision Manager | `AccessDecisionManager` | `AccessDecisionManager` |
| Strategy Enum | `DecisionStrategy` | `DecisionStrategy::Affirmative` |
| Vote Enum | `Vote` | `Vote::Grant` |
| Test | `{ClassName}Test` | `AccessDecisionManagerTest` |

---

## Quick Template Reference

### Permission

```php
enum Permission: string
{
    case View = 'view';
    case Create = 'create';
    case Edit = 'edit';
    case Delete = 'delete';
    case Manage = 'manage';
}
```

### VoterInterface

```php
interface VoterInterface
{
    public function vote(AccessSubject $subject, Permission $permission, mixed $resource = null): Vote;
}
```

### AccessDecisionManager

```php
final readonly class AccessDecisionManager
{
    /** @param list<VoterInterface> $voters */
    public function __construct(
        private array $voters,
        private DecisionStrategy $strategy = DecisionStrategy::Affirmative
    ) {}

    public function isGranted(AccessSubject $subject, Permission $permission, mixed $resource = null): bool;
}
```

---

## Usage Example

```php
$manager = new AccessDecisionManager(
    voters: [new RoleVoter(), new ResourceOwnerVoter()],
    strategy: DecisionStrategy::Affirmative
);

$subject = new AccessSubject(userId: $user->id(), roles: $user->roles());

if ($manager->isGranted($subject, Permission::Edit, $article)) {
    $article->update($data);
}
```

---

## Decision Strategies

```
Affirmative: ANY voter grants → GRANTED   (default, most permissive)
Consensus:   MAJORITY grants → GRANTED    (balanced)
Unanimous:   ALL voters grant → GRANTED   (most restrictive)
```

---

## Anti-patterns to Avoid

| Anti-pattern | Problem | Solution |
|--------------|---------|----------|
| String permissions | Typos, no IDE support | Use Permission enum |
| Inline auth checks | Scattered, unmaintainable | Centralize in voters |
| God voter | Single voter with all logic | One voter per concern |
| No ABSTAIN support | Voter must decide everything | ABSTAIN when not applicable |
| Flat roles | No inheritance, duplication | Role hierarchy |
| Missing resource check | Only role-based, no ownership | Add ResourceOwnerVoter |

---

## References

For complete PHP templates and examples, see:
- `references/templates.md` — Permission, Role, VoterInterface, AccessDecisionManager, Voter templates
- `references/examples.md` — Authorization examples and tests
