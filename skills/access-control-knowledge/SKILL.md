---
name: access-control-knowledge
description: Access Control knowledge base. Provides ACL, RBAC, ABAC, ReBAC models, multi-tenancy patterns, and PHP implementations (Symfony Voters, Laravel Gates) for security audits and generation.
---

# Access Control Knowledge Base

Quick reference for access control models, authorization patterns, and PHP implementations.

## Access Control Models Comparison

| Model | Full Name | Basis | Granularity | Scalability | Complexity |
|-------|-----------|-------|-------------|-------------|------------|
| **ACL** | Access Control List | Per-resource permissions | Fine | Poor at scale | Low |
| **RBAC** | Role-Based Access Control | Roles assigned to users | Medium | Good | Medium |
| **ABAC** | Attribute-Based Access Control | Policies over attributes | Very fine | Excellent | High |
| **ReBAC** | Relationship-Based Access Control | Object relationships | Very fine | Excellent | High |

## Decision Matrix: When to Use Which Model

| Scenario | Recommended | Why |
|----------|-------------|-----|
| Simple app, few resources | ACL | Direct, easy to implement |
| Enterprise, department-based access | RBAC | Maps to organizational roles |
| Complex policies, dynamic rules | ABAC | Flexible attribute evaluation |
| Social graphs, shared resources | ReBAC | Natural relationship modeling |
| Multi-tenant SaaS | RBAC + tenant scope | Roles per tenant |
| Healthcare, finance (compliance) | ABAC | Fine-grained audit trail |
| Document sharing (Google Docs style) | ReBAC | Owner/editor/viewer relations |
| Microservices with JWT | RBAC (claims) | Stateless, token-based |

## RBAC: Role-Based Access Control

### Role Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RBAC ROLE HIERARCHY                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│                        ┌──────────────┐                                      │
│                        │  SUPER_ADMIN │                                      │
│                        │  (all perms) │                                      │
│                        └──────┬───────┘                                      │
│                               │ inherits                                     │
│                        ┌──────▼───────┐                                      │
│                        │    ADMIN     │                                      │
│                        │  (manage)   │                                      │
│                        └──────┬───────┘                                      │
│                    ┌──────────┼──────────┐                                   │
│                    │ inherits │          │ inherits                           │
│             ┌──────▼───────┐  │  ┌───────▼──────┐                            │
│             │   MANAGER   │  │  │   EDITOR     │                            │
│             │ (approve)   │  │  │ (create/edit)│                            │
│             └──────┬───────┘  │  └───────┬──────┘                            │
│                    │          │          │                                    │
│                    └──────────┼──────────┘                                    │
│                        ┌──────▼───────┐                                      │
│                        │    USER      │                                      │
│                        │  (read)     │                                      │
│                        └──────┬───────┘                                      │
│                        ┌──────▼───────┐                                      │
│                        │    GUEST     │                                      │
│                        │  (limited)  │                                      │
│                        └──────────────┘                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Permission Inheritance

| Role | Own Permissions | Inherited From | Total Permissions |
|------|----------------|---------------|-------------------|
| GUEST | view_public | - | 1 |
| USER | view, create | GUEST | 3 |
| EDITOR | edit, publish | USER | 5 |
| MANAGER | approve, assign | USER | 5 |
| ADMIN | manage_users, configure | MANAGER, EDITOR | 10 |
| SUPER_ADMIN | all | ADMIN | all |

### RBAC PHP Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Authorization;

final readonly class Role
{
    /**
     * @param list<Permission> $permissions
     * @param list<self> $parents
     */
    public function __construct(
        private string $name,
        private array $permissions = [],
        private array $parents = [],
    ) {}

    public function hasPermission(Permission $permission): bool
    {
        if (in_array($permission, $this->permissions, true)) {
            return true;
        }

        foreach ($this->parents as $parent) {
            if ($parent->hasPermission($permission)) {
                return true;
            }
        }

        return false;
    }

    public function getName(): string
    {
        return $this->name;
    }

    /** @return list<Permission> */
    public function getAllPermissions(): array
    {
        $permissions = $this->permissions;

        foreach ($this->parents as $parent) {
            $permissions = array_merge($permissions, $parent->getAllPermissions());
        }

        return array_values(array_unique($permissions));
    }
}
```

## ABAC: Attribute-Based Access Control

### Core Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Subject** | Who is requesting access | User with attributes (role, department, clearance) |
| **Resource** | What is being accessed | Document with attributes (classification, owner) |
| **Action** | Operation being performed | read, write, delete, approve |
| **Environment** | Contextual conditions | Time of day, IP range, MFA status |

### Policy Evaluation

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ABAC POLICY EVALUATION                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Request(subject, resource, action, environment)                            │
│       │                                                                      │
│       ▼                                                                      │
│   ┌──────────────────────┐                                                   │
│   │  Policy Decision     │                                                   │
│   │  Point (PDP)         │ ◀── Policy Store (rules)                         │
│   └──────────┬───────────┘                                                   │
│              │                                                               │
│       ┌──────┼──────┐                                                        │
│       ▼      ▼      ▼                                                        │
│   Policy1  Policy2  PolicyN                                                  │
│    ALLOW    DENY    ALLOW                                                    │
│       │      │      │                                                        │
│       └──────┼──────┘                                                        │
│              ▼                                                               │
│   ┌──────────────────┐                                                       │
│   │ Combining Algo   │                                                       │
│   │ (deny-overrides) │                                                       │
│   └────────┬─────────┘                                                       │
│            ▼                                                                 │
│         DENY                                                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### ABAC Policy Implementation

```php
<?php

declare(strict_types=1);

namespace Domain\Authorization;

final readonly class AbacPolicy
{
    public function __construct(
        private string $name,
        private string $description,
        /** @var list<callable(AuthorizationContext): ?bool> */
        private array $rules,
    ) {}

    public function evaluate(AuthorizationContext $context): ?bool
    {
        foreach ($this->rules as $rule) {
            $result = $rule($context);
            if ($result === false) {
                return false;
            }
        }

        return true;
    }

    public function getName(): string
    {
        return $this->name;
    }
}

final readonly class AuthorizationContext
{
    public function __construct(
        private array $subjectAttributes,
        private array $resourceAttributes,
        private string $action,
        private array $environmentAttributes = [],
    ) {}

    public function getSubjectAttribute(string $key): mixed
    {
        return $this->subjectAttributes[$key] ?? null;
    }

    public function getResourceAttribute(string $key): mixed
    {
        return $this->resourceAttributes[$key] ?? null;
    }

    public function getAction(): string
    {
        return $this->action;
    }

    public function getEnvironmentAttribute(string $key): mixed
    {
        return $this->environmentAttributes[$key] ?? null;
    }
}
```

## ReBAC: Relationship-Based Access Control

### Google Zanzibar Model

Relationships are stored as tuples: `user:relation:object`

| Tuple | Meaning |
|-------|---------|
| `user:123#viewer@document:456` | User 123 is a viewer of document 456 |
| `group:eng#member@user:123` | User 123 is a member of group eng |
| `document:456#parent@folder:789` | Document 456 is in folder 789 |
| `folder:789#viewer@group:eng#member` | Members of eng group are viewers of folder 789 |

### Relationship Graph

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ReBAC RELATIONSHIP GRAPH                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   user:alice ──owner──▶ document:report                                     │
│       │                     │                                                │
│       │ member              │ parent                                         │
│       ▼                     ▼                                                │
│   group:engineering    folder:shared                                        │
│       │                     │                                                │
│       │ viewer              │ viewer                                         │
│       ▼                     ▼                                                │
│   folder:eng-docs      org:acme (all members can view)                     │
│                                                                              │
│   Check: Can alice view document:report?                                    │
│   Path:  alice ──owner──▶ document:report  ✓ (owner implies viewer)         │
│                                                                              │
│   Check: Can bob view folder:shared?                                        │
│   Path:  bob ──member──▶ org:acme ──viewer──▶ folder:shared  ✓             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Multi-Tenancy Authorization

| Pattern | Description | Isolation Level |
|---------|-------------|----------------|
| **Tenant-scoped roles** | User has different roles per tenant | Strong |
| **Shared roles, tenant filter** | Global roles, data filtered by tenant | Medium |
| **Tenant in JWT claims** | Tenant ID in authentication token | Medium |
| **Row-level security** | Database enforces tenant isolation | Strong |
| **Separate schemas** | Each tenant has own DB schema | Strongest |

### Tenant-Scoped Authorization

```php
<?php

declare(strict_types=1);

namespace Domain\Authorization;

final readonly class TenantPermissionChecker
{
    public function __construct(
        private TenantRoleRepositoryInterface $roleRepository,
    ) {}

    public function hasPermission(string $userId, string $tenantId, Permission $permission): bool
    {
        $roles = $this->roleRepository->findRolesForUserInTenant($userId, $tenantId);

        foreach ($roles as $role) {
            if ($role->hasPermission($permission)) {
                return true;
            }
        }

        return false;
    }

    public function assertPermission(string $userId, string $tenantId, Permission $permission): void
    {
        if (!$this->hasPermission($userId, $tenantId, $permission)) {
            throw new AccessDeniedException(
                sprintf('User %s lacks %s in tenant %s', $userId, $permission->value, $tenantId),
            );
        }
    }
}
```

## Symfony Voter Implementation

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\Voter;

use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

final class DocumentVoter extends Voter
{
    public const string VIEW = 'DOCUMENT_VIEW';
    public const string EDIT = 'DOCUMENT_EDIT';
    public const string DELETE = 'DOCUMENT_DELETE';

    protected function supports(string $attribute, mixed $subject): bool
    {
        return in_array($attribute, [self::VIEW, self::EDIT, self::DELETE], true)
            && $subject instanceof Document;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        $user = $token->getUser();
        if (!$user instanceof User) {
            return false;
        }

        /** @var Document $document */
        $document = $subject;

        return match ($attribute) {
            self::VIEW => $this->canView($document, $user),
            self::EDIT => $this->canEdit($document, $user),
            self::DELETE => $this->canDelete($document, $user),
            default => false,
        };
    }

    private function canView(Document $document, User $user): bool
    {
        if ($document->isPublic()) {
            return true;
        }

        return $document->getOwnerId() === $user->getId()
            || $user->hasRole('ROLE_ADMIN');
    }

    private function canEdit(Document $document, User $user): bool
    {
        return $document->getOwnerId() === $user->getId()
            || $user->hasRole('ROLE_EDITOR');
    }

    private function canDelete(Document $document, User $user): bool
    {
        return $document->getOwnerId() === $user->getId()
            || $user->hasRole('ROLE_ADMIN');
    }
}
```

## Laravel Gate/Policy

```php
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Models\Document;
use App\Models\User;

final class DocumentPolicy
{
    public function view(User $user, Document $document): bool
    {
        if ($document->is_public) {
            return true;
        }

        return $user->id === $document->owner_id
            || $user->hasRole('admin');
    }

    public function update(User $user, Document $document): bool
    {
        return $user->id === $document->owner_id
            || $user->hasRole('editor');
    }

    public function delete(User $user, Document $document): bool
    {
        return $user->id === $document->owner_id
            || $user->hasRole('admin');
    }
}
```

## Anti-Patterns

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| **Inline role checks** | `if ($user->role === 'admin')` scattered in code | Use Voter/Policy abstraction |
| **Hardcoded permissions** | Permissions compiled into code | Store in database/config |
| **Missing deny-by-default** | Forgetting to deny when no rule matches | Default to DENY |
| **Role explosion** | Too many roles (one per use case) | Switch to ABAC or group permissions |
| **Checking in views only** | No server-side enforcement | Always check in backend |
| **No audit logging** | Cannot trace who accessed what | Log every authorization decision |
| **Caching without invalidation** | Stale permission grants | Event-driven cache invalidation |
| **God role** | Single admin role with all permissions | Granular admin sub-roles |

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| No authorization on API endpoints | Controllers, routes | Critical |
| Hardcoded role names in business logic | Domain layer, services | Warning |
| Missing tenant isolation in queries | Repositories, query builders | Critical |
| No CSRF protection on state-changing forms | Form handlers, middleware | Critical |
| Permissions not cached | Voter/Policy implementations | Warning |
| No audit trail for access decisions | Authorization layer | Warning |
| Overly permissive default roles | Role configuration | Warning |

## Detection Patterns

```bash
# Authorization implementations
Grep: "Voter|VoterInterface|AbstractVoter" --glob "**/*.php"
Grep: "Gate::define|Gate::allows|Gate::denies|@can" --glob "**/*.php"
Grep: "Policy|AuthorizesRequests" --glob "**/*.php"

# Role checks
Grep: "hasRole|isGranted|->can\(|->cannot\(" --glob "**/*.php"
Grep: "ROLE_|Permission::|PermissionEnum" --glob "**/*.php"

# Inline role checks (anti-pattern)
Grep: "role\s*===?\s*['\"]admin|role\s*===?\s*['\"]user" --glob "**/*.php"

# Tenant isolation
Grep: "tenant_id|tenantId|getTenantId" --glob "**/*.php"
Grep: "TenantScope|MultiTenant|BelongsToTenant" --glob "**/*.php"

# Casbin
Grep: "Enforcer|casbin|model\.conf|policy\.csv" --glob "**/*.php"

# Security configuration
Grep: "security\.yaml|security\.php|access_control" --glob "**/*.{yaml,php}"
Grep: "#\[IsGranted|@IsGranted|@Security" --glob "**/*.php"

# Missing authorization
Grep: "class.*Controller" --glob "**/*.php"
Grep: "class.*Action" --glob "**/Action/**/*.php"
```

## References

For detailed information, load these reference files:

- `references/models.md` — Detailed ACL, RBAC, ABAC, ReBAC analysis with scalability comparisons and PHP examples
- `references/php-implementations.md` — Symfony Voters, Laravel Gates/Policies, Casbin PHP, permission caching strategies
