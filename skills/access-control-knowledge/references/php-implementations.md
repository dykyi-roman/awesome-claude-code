# PHP Access Control Implementations Reference

## Symfony Security Voters

### VoterInterface

Symfony Voters implement `VoterInterface` and are registered as services. The `AccessDecisionManager` collects votes from all voters and applies a strategy.

### Custom Voter Pattern

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\Voter;

use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

final class ProjectVoter extends Voter
{
    public const string VIEW = 'PROJECT_VIEW';
    public const string EDIT = 'PROJECT_EDIT';
    public const string DELETE = 'PROJECT_DELETE';
    public const string MANAGE_MEMBERS = 'PROJECT_MANAGE_MEMBERS';

    public function __construct(
        private readonly ProjectMembershipRepositoryInterface $membershipRepository,
    ) {}

    protected function supports(string $attribute, mixed $subject): bool
    {
        return in_array($attribute, [
            self::VIEW,
            self::EDIT,
            self::DELETE,
            self::MANAGE_MEMBERS,
        ], true) && $subject instanceof Project;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        $user = $token->getUser();
        if (!$user instanceof User) {
            return false;
        }

        /** @var Project $project */
        $project = $subject;

        return match ($attribute) {
            self::VIEW => $this->canView($project, $user),
            self::EDIT => $this->canEdit($project, $user),
            self::DELETE => $this->canDelete($project, $user),
            self::MANAGE_MEMBERS => $this->canManageMembers($project, $user),
            default => false,
        };
    }

    private function canView(Project $project, User $user): bool
    {
        if ($project->isPublic()) {
            return true;
        }

        return $this->isMember($project, $user);
    }

    private function canEdit(Project $project, User $user): bool
    {
        $membership = $this->membershipRepository->findByProjectAndUser(
            $project->getId(),
            $user->getId(),
        );

        if ($membership === null) {
            return false;
        }

        return in_array($membership->getRole(), [
            ProjectRole::Owner,
            ProjectRole::Admin,
            ProjectRole::Editor,
        ], true);
    }

    private function canDelete(Project $project, User $user): bool
    {
        return $project->getOwnerId() === $user->getId();
    }

    private function canManageMembers(Project $project, User $user): bool
    {
        $membership = $this->membershipRepository->findByProjectAndUser(
            $project->getId(),
            $user->getId(),
        );

        if ($membership === null) {
            return false;
        }

        return in_array($membership->getRole(), [
            ProjectRole::Owner,
            ProjectRole::Admin,
        ], true);
    }

    private function isMember(Project $project, User $user): bool
    {
        return $this->membershipRepository->findByProjectAndUser(
            $project->getId(),
            $user->getId(),
        ) !== null;
    }
}
```

### AccessDecisionManager Strategy

| Strategy | Behavior | Default |
|----------|----------|---------|
| **affirmative** | Grants if ANY voter grants | Yes |
| **consensus** | Grants if majority grants | No |
| **unanimous** | Grants only if ALL grant | No |
| **priority** | Uses first non-abstain vote | No |

### Using Voters in Controllers

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Action;

use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Security\Http\Attribute\IsGranted;

final class ProjectAction extends AbstractController
{
    #[Route('/api/projects/{id}', methods: ['GET'])]
    public function view(Project $project): JsonResponse
    {
        $this->denyAccessUnlessGranted(ProjectVoter::VIEW, $project);

        return $this->json($project);
    }

    #[Route('/api/projects/{id}', methods: ['PUT'])]
    #[IsGranted(ProjectVoter::EDIT, subject: 'project')]
    public function update(Project $project): JsonResponse
    {
        return $this->json($project);
    }
}
```

## Laravel Gates and Policies

### Gate::define

Gates are closure-based authorization checks, defined in `AuthServiceProvider`:

```php
<?php

declare(strict_types=1);

namespace App\Providers;

use Illuminate\Foundation\Support\Providers\AuthServiceProvider as ServiceProvider;
use Illuminate\Support\Facades\Gate;

final class AuthServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Gate::define('view-dashboard', function (User $user): bool {
            return $user->hasRole('admin') || $user->hasRole('manager');
        });

        Gate::define('manage-settings', function (User $user): bool {
            return $user->hasRole('admin');
        });

        Gate::before(function (User $user, string $ability): ?bool {
            if ($user->isSuperAdmin()) {
                return true;
            }

            return null;
        });
    }
}
```

### Policy Classes

Policies group authorization logic per model:

```php
<?php

declare(strict_types=1);

namespace App\Policies;

use App\Models\Project;
use App\Models\User;

final class ProjectPolicy
{
    public function viewAny(User $user): bool
    {
        return true;
    }

    public function view(User $user, Project $project): bool
    {
        if ($project->is_public) {
            return true;
        }

        return $project->members()->where('user_id', $user->id)->exists();
    }

    public function create(User $user): bool
    {
        return $user->hasVerifiedEmail();
    }

    public function update(User $user, Project $project): bool
    {
        return $project->members()
            ->where('user_id', $user->id)
            ->whereIn('role', ['owner', 'admin', 'editor'])
            ->exists();
    }

    public function delete(User $user, Project $project): bool
    {
        return $project->owner_id === $user->id;
    }

    public function restore(User $user, Project $project): bool
    {
        return $project->owner_id === $user->id;
    }

    public function forceDelete(User $user, Project $project): bool
    {
        return $user->hasRole('admin') && $project->owner_id === $user->id;
    }
}
```

### Using Policies

```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers;

use App\Models\Project;
use Illuminate\Http\JsonResponse;

final class ProjectController extends Controller
{
    public function show(Project $project): JsonResponse
    {
        $this->authorize('view', $project);

        return response()->json($project);
    }

    public function update(UpdateProjectRequest $request, Project $project): JsonResponse
    {
        $this->authorize('update', $project);

        $project->update($request->validated());

        return response()->json($project);
    }
}
```

### Blade Authorization

```php
@can('update', $project)
    <a href="{{ route('projects.edit', $project) }}">Edit</a>
@endcan

@canany(['update', 'delete'], $project)
    <div class="actions">
        @can('update', $project) <button>Edit</button> @endcan
        @can('delete', $project) <button>Delete</button> @endcan
    </div>
@endcanany
```

## Casbin PHP

### Model Configuration

Casbin uses a model file (PERM metamodel) that defines the authorization structure:

```ini
# model.conf

[request_definition]
r = sub, obj, act

[policy_definition]
p = sub, obj, act

[role_definition]
g = _, _

[policy_effect]
e = some(where (p.eft == allow))

[matchers]
m = g(r.sub, p.sub) && r.obj == p.obj && r.act == p.act
```

### Casbin PHP Usage

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Authorization;

use Casbin\Enforcer;
use Casbin\Model\Model;

final readonly class CasbinAuthorizationService
{
    private Enforcer $enforcer;

    public function __construct(string $modelPath, string $policyPath)
    {
        $this->enforcer = new Enforcer($modelPath, $policyPath);
    }

    public function isAllowed(string $subject, string $object, string $action): bool
    {
        return $this->enforcer->enforce($subject, $object, $action);
    }

    public function addPolicy(string $subject, string $object, string $action): bool
    {
        return $this->enforcer->addPolicy($subject, $object, $action);
    }

    public function removePolicy(string $subject, string $object, string $action): bool
    {
        return $this->enforcer->removePolicy($subject, $object, $action);
    }

    public function addRoleForUser(string $user, string $role): bool
    {
        return $this->enforcer->addRoleForUser($user, $role);
    }

    /** @return list<string> */
    public function getRolesForUser(string $user): array
    {
        return $this->enforcer->getRolesForUser($user);
    }

    /** @return list<list<string>> */
    public function getPermissionsForUser(string $user): array
    {
        return $this->enforcer->getPermissionsForUser($user);
    }
}
```

### Policy Storage (Database Adapter)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Authorization;

use CasbinAdapter\Database\Adapter as DatabaseAdapter;
use Casbin\Enforcer;

final readonly class CasbinFactory
{
    public function createWithDatabase(string $modelPath, \PDO $pdo): Enforcer
    {
        $adapter = DatabaseAdapter::newAdapter([
            'type' => 'mysql',
            'hostname' => $_ENV['DB_HOST'],
            'database' => $_ENV['DB_NAME'],
            'username' => $_ENV['DB_USER'],
            'password' => $_ENV['DB_PASSWORD'],
            'hostport' => $_ENV['DB_PORT'] ?? '3306',
        ]);

        return new Enforcer($modelPath, $adapter);
    }
}
```

## Permission Caching

### Redis-Based Permission Cache

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Authorization;

use Psr\Log\LoggerInterface;

final class CachedPermissionChecker implements PermissionCheckerInterface
{
    private const string CACHE_PREFIX = 'perms:';
    private const int DEFAULT_TTL = 300;

    public function __construct(
        private readonly PermissionCheckerInterface $inner,
        private readonly \Redis $redis,
        private readonly LoggerInterface $logger,
        private readonly int $ttl = self::DEFAULT_TTL,
    ) {}

    public function hasPermission(string $userId, string $permission): bool
    {
        $cacheKey = sprintf('%s%s', self::CACHE_PREFIX, $userId);

        $cached = $this->redis->hGet($cacheKey, $permission);
        if ($cached !== false) {
            return $cached === '1';
        }

        $result = $this->inner->hasPermission($userId, $permission);

        $this->redis->hSet($cacheKey, $permission, $result ? '1' : '0');
        $this->redis->expire($cacheKey, $this->ttl);

        return $result;
    }

    public function invalidateUser(string $userId): void
    {
        $cacheKey = sprintf('%s%s', self::CACHE_PREFIX, $userId);
        $this->redis->del($cacheKey);

        $this->logger->info('Permission cache invalidated', ['user_id' => $userId]);
    }

    public function invalidateAll(): void
    {
        $keys = $this->redis->keys(self::CACHE_PREFIX . '*');
        if ($keys !== []) {
            $this->redis->del($keys);
        }

        $this->logger->info('All permission caches invalidated');
    }
}
```

### Event-Driven Cache Invalidation

```php
<?php

declare(strict_types=1);

namespace Application\EventHandler;

final readonly class InvalidatePermissionCacheHandler
{
    public function __construct(
        private CachedPermissionChecker $permissionChecker,
    ) {}

    public function handleRoleChanged(RoleChangedEvent $event): void
    {
        $this->permissionChecker->invalidateUser($event->getUserId());
    }

    public function handlePermissionUpdated(PermissionUpdatedEvent $event): void
    {
        foreach ($event->getAffectedUserIds() as $userId) {
            $this->permissionChecker->invalidateUser($userId);
        }
    }

    public function handleRoleDeleted(RoleDeletedEvent $event): void
    {
        $this->permissionChecker->invalidateAll();
    }
}
```

## Framework Comparison

| Feature | Symfony Voters | Laravel Gates/Policies | Casbin PHP |
|---------|---------------|----------------------|------------|
| Model | Voter classes | Closures + Policy classes | PERM metamodel |
| Registration | Auto (service tag) | AuthServiceProvider | Model + policy files |
| Strategy | Configurable | First match | Configurable matchers |
| RBAC | Via role hierarchy | Via roles | Built-in (g = _, _) |
| ABAC | Custom in Voter | Custom in Gate/Policy | With matchers |
| Caching | Manual | Manual | Adapter-dependent |
| Testing | Mock SecurityContext | `actingAs()` | Mock Enforcer |
| Multi-tenant | Custom Voter logic | Custom Gate/Policy logic | Filtered policies |
