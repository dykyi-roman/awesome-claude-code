# Access Control Models Reference

## ACL (Access Control List)

### How It Works

Each resource maintains a list of permissions for specific subjects (users or groups). The system checks the list for the target resource when access is requested.

| Component | Description | Example |
|-----------|-------------|---------|
| **Subject** | Who is granted access | User, Group |
| **Object** | What is protected | File, Record, Endpoint |
| **Permission** | What actions are allowed | Read, Write, Execute |

### ACL Implementation

```php
<?php

namespace Authorization;

final readonly class AccessControlList
{
    /** @var array<string, array<string, list<string>>> */
    private array $entries;

    /**
     * @param array<string, array<string, list<string>>> $entries
     */
    public function __construct(array $entries = [])
    {
        $this->entries = $entries;
    }

    public function isAllowed(string $subjectId, string $resourceId, string $permission): bool
    {
        return isset($this->entries[$resourceId][$subjectId])
            && in_array($permission, $this->entries[$resourceId][$subjectId], true);
    }

    public function withGrant(string $subjectId, string $resourceId, string $permission): self
    {
        $entries = $this->entries;
        $entries[$resourceId][$subjectId][] = $permission;
        $entries[$resourceId][$subjectId] = array_unique($entries[$resourceId][$subjectId]);

        return new self($entries);
    }

    public function withRevoke(string $subjectId, string $resourceId, string $permission): self
    {
        $entries = $this->entries;

        if (isset($entries[$resourceId][$subjectId])) {
            $entries[$resourceId][$subjectId] = array_values(
                array_diff($entries[$resourceId][$subjectId], [$permission]),
            );
        }

        return new self($entries);
    }
}
```

### ACL Limitations

| Limitation | Impact |
|-----------|--------|
| Per-resource storage | Grows with resources x users |
| No inheritance | Must duplicate entries |
| Hard to audit | Must scan all resources |
| Policy changes | Must update every affected resource |

## RBAC (Role-Based Access Control)

### RBAC Variants

| Variant | Description | Features |
|---------|-------------|----------|
| **Flat RBAC** | Users assigned to roles, roles have permissions | No hierarchy |
| **Hierarchical RBAC** | Roles inherit from parent roles | Role trees |
| **Constrained RBAC** | Adds separation of duties constraints | Mutual exclusion, cardinality |
| **Symmetric RBAC** | Permission-to-role review (reverse lookup) | Audit-friendly |

### Hierarchical RBAC with Enums

```php
<?php

namespace Authorization;

enum Permission: string
{
    case ViewPublic = 'view_public';
    case ViewOwn = 'view_own';
    case ViewAll = 'view_all';
    case Create = 'create';
    case Edit = 'edit';
    case EditAll = 'edit_all';
    case Delete = 'delete';
    case DeleteAll = 'delete_all';
    case ManageUsers = 'manage_users';
    case ManageRoles = 'manage_roles';
    case Configure = 'configure';
}

enum RoleType: string
{
    case Guest = 'guest';
    case User = 'user';
    case Editor = 'editor';
    case Manager = 'manager';
    case Admin = 'admin';
    case SuperAdmin = 'super_admin';

    /** @return list<Permission> */
    public function permissions(): array
    {
        return match ($this) {
            self::Guest => [Permission::ViewPublic],
            self::User => [
                ...self::Guest->permissions(),
                Permission::ViewOwn,
                Permission::Create,
            ],
            self::Editor => [
                ...self::User->permissions(),
                Permission::Edit,
                Permission::ViewAll,
            ],
            self::Manager => [
                ...self::User->permissions(),
                Permission::EditAll,
                Permission::DeleteAll,
            ],
            self::Admin => [
                ...self::Manager->permissions(),
                ...self::Editor->permissions(),
                Permission::ManageUsers,
                Permission::Configure,
            ],
            self::SuperAdmin => Permission::cases(),
        };
    }

    public function hasPermission(Permission $permission): bool
    {
        return in_array($permission, $this->permissions(), true);
    }
}
```

### RBAC Authorization Service

```php
<?php

namespace Authorization;

final readonly class RbacAuthorizationService
{
    public function __construct(
        private UserRoleRepositoryInterface $userRoleRepository,
    ) {}

    public function isAllowed(string $userId, Permission $permission): bool
    {
        $roles = $this->userRoleRepository->findRolesForUser($userId);

        foreach ($roles as $role) {
            if ($role->hasPermission($permission)) {
                return true;
            }
        }

        return false;
    }

    public function assertAllowed(string $userId, Permission $permission): void
    {
        if (!$this->isAllowed($userId, $permission)) {
            throw new AccessDeniedException(
                sprintf('User %s lacks permission %s', $userId, $permission->value),
            );
        }
    }
}
```

## ABAC (Attribute-Based Access Control)

### XACML Architecture

| Component | Abbreviation | Responsibility |
|-----------|-------------|----------------|
| Policy Administration Point | PAP | Create and manage policies |
| Policy Decision Point | PDP | Evaluate policies against requests |
| Policy Enforcement Point | PEP | Enforce PDP decisions |
| Policy Information Point | PIP | Provide attribute values |

### Policy Engine

```php
<?php

namespace Authorization;

final readonly class PolicyEngine
{
    /** @param list<PolicyInterface> $policies */
    public function __construct(
        private array $policies,
        private CombiningAlgorithm $algorithm = CombiningAlgorithm::DenyOverrides,
    ) {}

    public function evaluate(AuthorizationRequest $request): AuthorizationDecision
    {
        $decisions = [];

        foreach ($this->policies as $policy) {
            if ($policy->isApplicable($request)) {
                $decisions[] = $policy->evaluate($request);
            }
        }

        if ($decisions === []) {
            return AuthorizationDecision::NotApplicable;
        }

        return $this->combine($decisions);
    }

    private function combine(array $decisions): AuthorizationDecision
    {
        return match ($this->algorithm) {
            CombiningAlgorithm::DenyOverrides => in_array(AuthorizationDecision::Deny, $decisions, true)
                ? AuthorizationDecision::Deny
                : AuthorizationDecision::Permit,
            CombiningAlgorithm::PermitOverrides => in_array(AuthorizationDecision::Permit, $decisions, true)
                ? AuthorizationDecision::Permit
                : AuthorizationDecision::Deny,
            CombiningAlgorithm::FirstApplicable => $decisions[0],
        };
    }
}

enum CombiningAlgorithm
{
    case DenyOverrides;
    case PermitOverrides;
    case FirstApplicable;
}

enum AuthorizationDecision
{
    case Permit;
    case Deny;
    case NotApplicable;
    case Indeterminate;
}
```

## ReBAC (Relationship-Based Access Control)

### Zanzibar Tuple Model

The core data model is a set of relationship tuples:

```
<object>#<relation>@<user>
<object>#<relation>@<userset>
```

| Tuple Example | Meaning |
|--------------|---------|
| `doc:readme#viewer@user:alice` | Alice is a viewer of doc readme |
| `doc:readme#owner@user:bob` | Bob is the owner of doc readme |
| `folder:root#viewer@group:eng#member` | eng group members are viewers of root folder |
| `doc:readme#parent@folder:root` | doc readme is in folder root |

### Permission Check (Expand Algorithm)

```php
<?php

namespace Authorization;

final readonly class RelationshipChecker
{
    public function __construct(
        private TupleStoreInterface $store,
        private RelationshipConfig $config,
    ) {}

    public function check(string $object, string $relation, string $user): bool
    {
        if ($this->store->exists($object, $relation, $user)) {
            return true;
        }

        $impliedRelations = $this->config->getImpliedRelations($relation);
        foreach ($impliedRelations as $implied) {
            if ($this->store->exists($object, $implied, $user)) {
                return true;
            }
        }

        $parentRelation = $this->config->getParentRelation($object);
        if ($parentRelation !== null) {
            $parents = $this->store->findRelated($object, $parentRelation);
            foreach ($parents as $parent) {
                if ($this->check($parent, $relation, $user)) {
                    return true;
                }
            }
        }

        $groups = $this->store->findGroupsForUser($user);
        foreach ($groups as $group) {
            if ($this->store->exists($object, $relation, $group)) {
                return true;
            }
        }

        return false;
    }
}
```

## Model Comparison

| Aspect | ACL | RBAC | ABAC | ReBAC |
|--------|-----|------|------|-------|
| **Scalability** | Poor | Good | Excellent | Excellent |
| **Maintainability** | Poor at scale | Good | Medium | Good |
| **Granularity** | Per-object | Per-role | Per-attribute | Per-relationship |
| **Dynamic rules** | No | Limited | Yes | Yes |
| **Audit** | Difficult | Easy | Easy | Easy |
| **Learning curve** | Low | Low | High | Medium |
| **Performance** | O(1) lookup | O(roles) | O(policies) | O(graph depth) |
| **Delegation** | Manual | Role assignment | Policy rules | Relationship tuples |
| **External context** | No | No | Yes (environment) | Limited |
| **Best for** | Small systems | Enterprise apps | Complex compliance | Social/sharing |
