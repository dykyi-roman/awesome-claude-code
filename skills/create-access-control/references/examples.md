# Access Control Examples

## Role Hierarchy Setup

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security\AccessControl;

final readonly class RoleFactory
{
    public static function createHierarchy(): array
    {
        $viewer = new Role(
            name: 'viewer',
            permissions: [Permission::View]
        );

        $editor = new Role(
            name: 'editor',
            permissions: [Permission::Create, Permission::Edit],
            parents: [$viewer]
        );

        $admin = new Role(
            name: 'admin',
            permissions: [Permission::Manage],
            parents: [$editor]
        );

        return [
            'viewer' => $viewer,
            'editor' => $editor,
            'admin' => $admin,
        ];
    }
}
```

---

## Authorization in Use Case

**File:** `src/Application/Article/UpdateArticleUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Article;

use Infrastructure\Security\AccessControl\AccessDecisionManager;
use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\Permission;

final readonly class UpdateArticleUseCase
{
    public function __construct(
        private ArticleRepositoryInterface $articles,
        private AccessDecisionManager $accessManager
    ) {}

    public function execute(AccessSubject $subject, UpdateArticleRequest $request): void
    {
        $article = $this->articles->findById($request->articleId);

        if (!$this->accessManager->isGranted($subject, Permission::Edit, $article)) {
            throw new AccessDeniedException('You are not allowed to edit this article');
        }

        $article->update(
            title: $request->title,
            content: $request->content
        );

        $this->articles->save($article);
    }
}
```

---

## Middleware Authorization

**File:** `src/Infrastructure/Security/AuthorizationMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security;

use Infrastructure\Security\AccessControl\AccessDecisionManager;
use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\Permission;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class AuthorizationMiddleware implements MiddlewareInterface
{
    public function __construct(
        private AccessDecisionManager $accessManager,
        private Permission $requiredPermission
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        $subject = $request->getAttribute('access_subject');

        if (!$subject instanceof AccessSubject) {
            return new \Nyholm\Psr7\Response(401, [], '{"error":"Unauthorized"}');
        }

        if (!$this->accessManager->isGranted($subject, $this->requiredPermission)) {
            return new \Nyholm\Psr7\Response(403, [], '{"error":"Forbidden"}');
        }

        return $handler->handle($request);
    }
}
```

---

## Unit Tests

### RoleTest

**File:** `tests/Unit/Infrastructure/Security/AccessControl/RoleTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Security\AccessControl;

use Infrastructure\Security\AccessControl\Permission;
use Infrastructure\Security\AccessControl\Role;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(Role::class)]
final class RoleTest extends TestCase
{
    public function testHasDirectPermission(): void
    {
        $role = new Role('editor', [Permission::Edit]);

        self::assertTrue($role->hasPermission(Permission::Edit));
        self::assertFalse($role->hasPermission(Permission::Delete));
    }

    public function testInheritsParentPermissions(): void
    {
        $viewer = new Role('viewer', [Permission::View]);
        $editor = new Role('editor', [Permission::Edit], [$viewer]);

        self::assertTrue($editor->hasPermission(Permission::View));
    }

    public function testManageIncludesAllPermissions(): void
    {
        $admin = new Role('admin', [Permission::Manage]);

        self::assertTrue($admin->hasPermission(Permission::View));
        self::assertTrue($admin->hasPermission(Permission::Create));
        self::assertTrue($admin->hasPermission(Permission::Edit));
        self::assertTrue($admin->hasPermission(Permission::Delete));
    }

    public function testRejectsEmptyName(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new Role('');
    }

    public function testEquality(): void
    {
        $role1 = new Role('admin');
        $role2 = new Role('admin');

        self::assertTrue($role1->equals($role2));
    }
}
```

---

### AccessDecisionManagerTest

**File:** `tests/Unit/Infrastructure/Security/AccessControl/AccessDecisionManagerTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Security\AccessControl;

use Infrastructure\Security\AccessControl\AccessDecisionManager;
use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\DecisionStrategy;
use Infrastructure\Security\AccessControl\Permission;
use Infrastructure\Security\AccessControl\Role;
use Infrastructure\Security\AccessControl\Vote;
use Infrastructure\Security\AccessControl\VoterInterface;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(AccessDecisionManager::class)]
final class AccessDecisionManagerTest extends TestCase
{
    public function testAffirmativeGrantsOnFirstGrant(): void
    {
        $manager = new AccessDecisionManager(
            voters: [$this->createVoter(Vote::Grant), $this->createVoter(Vote::Abstain)],
            strategy: DecisionStrategy::Affirmative
        );

        $subject = new AccessSubject('user-1');

        self::assertTrue($manager->isGranted($subject, Permission::View));
    }

    public function testAffirmativeDeniesWhenNoneGrant(): void
    {
        $manager = new AccessDecisionManager(
            voters: [$this->createVoter(Vote::Abstain), $this->createVoter(Vote::Abstain)],
            strategy: DecisionStrategy::Affirmative
        );

        $subject = new AccessSubject('user-1');

        self::assertFalse($manager->isGranted($subject, Permission::View));
    }

    public function testUnanimousDeniesOnAnyDeny(): void
    {
        $manager = new AccessDecisionManager(
            voters: [$this->createVoter(Vote::Grant), $this->createVoter(Vote::Deny)],
            strategy: DecisionStrategy::Unanimous
        );

        $subject = new AccessSubject('user-1');

        self::assertFalse($manager->isGranted($subject, Permission::View));
    }

    public function testConsensusGrantsOnMajority(): void
    {
        $manager = new AccessDecisionManager(
            voters: [
                $this->createVoter(Vote::Grant),
                $this->createVoter(Vote::Grant),
                $this->createVoter(Vote::Deny),
            ],
            strategy: DecisionStrategy::Consensus
        );

        $subject = new AccessSubject('user-1');

        self::assertTrue($manager->isGranted($subject, Permission::View));
    }

    public function testRequiresAtLeastOneVoter(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new AccessDecisionManager(voters: []);
    }

    private function createVoter(Vote $result): VoterInterface
    {
        $voter = $this->createMock(VoterInterface::class);
        $voter->method('vote')->willReturn($result);
        return $voter;
    }
}
```

---

### RoleVoterTest

**File:** `tests/Unit/Infrastructure/Security/AccessControl/Voter/RoleVoterTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Security\AccessControl\Voter;

use Infrastructure\Security\AccessControl\AccessSubject;
use Infrastructure\Security\AccessControl\Permission;
use Infrastructure\Security\AccessControl\Role;
use Infrastructure\Security\AccessControl\Vote;
use Infrastructure\Security\AccessControl\Voter\RoleVoter;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(RoleVoter::class)]
final class RoleVoterTest extends TestCase
{
    public function testGrantsWhenRoleHasPermission(): void
    {
        $voter = new RoleVoter();
        $role = new Role('editor', [Permission::Edit]);
        $subject = new AccessSubject('user-1', [$role]);

        self::assertSame(Vote::Grant, $voter->vote($subject, Permission::Edit));
    }

    public function testAbstainsWhenRoleLacksPermission(): void
    {
        $voter = new RoleVoter();
        $role = new Role('viewer', [Permission::View]);
        $subject = new AccessSubject('user-1', [$role]);

        self::assertSame(Vote::Abstain, $voter->vote($subject, Permission::Delete));
    }
}
```
