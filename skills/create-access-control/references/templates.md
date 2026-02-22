# Access Control Templates

## Permission Enum

**File:** `src/Infrastructure/Security/AccessControl/Permission.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

enum Permission: string
{
    case View = 'view';
    case Create = 'create';
    case Edit = 'edit';
    case Delete = 'delete';
    case Manage = 'manage';

    /**
     * @return list<self>
     */
    public function includedPermissions(): array
    {
        return match ($this) {
            self::Manage => [self::View, self::Create, self::Edit, self::Delete],
            self::Edit => [self::View],
            self::Delete => [self::View],
            default => [],
        };
    }

    public function includes(self $permission): bool
    {
        return $this === $permission || in_array($permission, $this->includedPermissions(), true);
    }
}
```

---

## Role Value Object

**File:** `src/Infrastructure/Security/AccessControl/Role.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

final readonly class Role
{
    /**
     * @param list<Permission> $permissions
     * @param list<self> $parents
     */
    public function __construct(
        public string $name,
        private array $permissions = [],
        private array $parents = []
    ) {
        if ($this->name === '') {
            throw new \InvalidArgumentException('Role name cannot be empty');
        }
    }

    public function hasPermission(Permission $permission): bool
    {
        foreach ($this->permissions as $ownPermission) {
            if ($ownPermission->includes($permission)) {
                return true;
            }
        }

        foreach ($this->parents as $parent) {
            if ($parent->hasPermission($permission)) {
                return true;
            }
        }

        return false;
    }

    /**
     * @return list<Permission>
     */
    public function allPermissions(): array
    {
        $permissions = $this->permissions;

        foreach ($this->parents as $parent) {
            $permissions = array_merge($permissions, $parent->allPermissions());
        }

        return array_values(array_unique($permissions));
    }

    public function equals(self $other): bool
    {
        return $this->name === $other->name;
    }
}
```

---

## AccessSubject Value Object

**File:** `src/Infrastructure/Security/AccessControl/AccessSubject.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

final readonly class AccessSubject
{
    /**
     * @param list<Role> $roles
     */
    public function __construct(
        public string $userId,
        public array $roles = []
    ) {}

    public function hasRole(string $roleName): bool
    {
        foreach ($this->roles as $role) {
            if ($role->name === $roleName) {
                return true;
            }
        }

        return false;
    }

    public function hasPermission(Permission $permission): bool
    {
        foreach ($this->roles as $role) {
            if ($role->hasPermission($permission)) {
                return true;
            }
        }

        return false;
    }
}
```

---

## Vote Enum

**File:** `src/Infrastructure/Security/AccessControl/Vote.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

enum Vote: string
{
    case Grant = 'grant';
    case Deny = 'deny';
    case Abstain = 'abstain';
}
```

---

## DecisionStrategy Enum

**File:** `src/Infrastructure/Security/AccessControl/DecisionStrategy.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

enum DecisionStrategy: string
{
    case Affirmative = 'affirmative';
    case Unanimous = 'unanimous';
    case Consensus = 'consensus';
}
```

---

## VoterInterface

**File:** `src/Infrastructure/Security/AccessControl/VoterInterface.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

interface VoterInterface
{
    public function vote(AccessSubject $subject, Permission $permission, mixed $resource = null): Vote;
}
```

---

## AccessDecisionManager

**File:** `src/Infrastructure/Security/AccessControl/AccessDecisionManager.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

final readonly class AccessDecisionManager
{
    /**
     * @param list<VoterInterface> $voters
     */
    public function __construct(
        private array $voters,
        private DecisionStrategy $strategy = DecisionStrategy::Affirmative
    ) {
        if ($this->voters === []) {
            throw new \InvalidArgumentException('At least one voter is required');
        }
    }

    public function isGranted(AccessSubject $subject, Permission $permission, mixed $resource = null): bool
    {
        return match ($this->strategy) {
            DecisionStrategy::Affirmative => $this->decideAffirmative($subject, $permission, $resource),
            DecisionStrategy::Unanimous => $this->decideUnanimous($subject, $permission, $resource),
            DecisionStrategy::Consensus => $this->decideConsensus($subject, $permission, $resource),
        };
    }

    private function decideAffirmative(AccessSubject $subject, Permission $permission, mixed $resource): bool
    {
        foreach ($this->voters as $voter) {
            $vote = $voter->vote($subject, $permission, $resource);

            if ($vote === Vote::Grant) {
                return true;
            }

            if ($vote === Vote::Deny) {
                return false;
            }
        }

        return false;
    }

    private function decideUnanimous(AccessSubject $subject, Permission $permission, mixed $resource): bool
    {
        $hasGrant = false;

        foreach ($this->voters as $voter) {
            $vote = $voter->vote($subject, $permission, $resource);

            if ($vote === Vote::Deny) {
                return false;
            }

            if ($vote === Vote::Grant) {
                $hasGrant = true;
            }
        }

        return $hasGrant;
    }

    private function decideConsensus(AccessSubject $subject, Permission $permission, mixed $resource): bool
    {
        $grants = 0;
        $denies = 0;

        foreach ($this->voters as $voter) {
            $vote = $voter->vote($subject, $permission, $resource);

            if ($vote === Vote::Grant) {
                $grants++;
            } elseif ($vote === Vote::Deny) {
                $denies++;
            }
        }

        return $grants > $denies;
    }
}
```

---

## RoleVoter

**File:** `src/Infrastructure/Security/AccessControl/Voter/RoleVoter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl\Voter;

use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\Permission;
use Infrastructure\Security\AccessControl\Vote;
use Infrastructure\Security\AccessControl\VoterInterface;

final readonly class RoleVoter implements VoterInterface
{
    public function vote(AccessSubject $subject, Permission $permission, mixed $resource = null): Vote
    {
        if ($subject->hasPermission($permission)) {
            return Vote::Grant;
        }

        return Vote::Abstain;
    }
}
```

---

## ResourceOwnerVoter

**File:** `src/Infrastructure/Security/AccessControl/Voter/ResourceOwnerVoter.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl\Voter;

use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\Permission;
use Infrastructure\Security\AccessControl\Vote;
use Infrastructure\Security\AccessControl\VoterInterface;

interface OwnableInterface
{
    public function ownerId(): string;
}

final readonly class ResourceOwnerVoter implements VoterInterface
{
    private const OWNER_PERMISSIONS = [Permission::Edit, Permission::Delete, Permission::View];

    public function vote(AccessSubject $subject, Permission $permission, mixed $resource = null): Vote
    {
        if (!$resource instanceof OwnableInterface) {
            return Vote::Abstain;
        }

        if (!in_array($permission, self::OWNER_PERMISSIONS, true)) {
            return Vote::Abstain;
        }

        if ($resource->ownerId() === $subject->userId) {
            return Vote::Grant;
        }

        return Vote::Deny;
    }
}
```
