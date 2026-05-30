# Yii3 Security in DDD Context

Authentication, authorization (RBAC), password hashing, CSRF protection, and middleware patterns aligned with Domain-Driven Design.

## Authentication (yiisoft/auth + yiisoft/user)

### IdentityInterface as Domain Aggregate

Domain User aggregate is pure PHP — no auth interfaces. Infrastructure `SecurityIdentityAdapter` implements `IdentityInterface` and wraps the Domain entity.

**Detection:**
```bash
# IdentityInterface in Domain layer — violation (MUST be zero)
Grep: "IdentityInterface" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\Auth\\" --glob "**/Domain/**/*.php"

# CurrentUser service in Domain — violation (MUST be zero)
Grep: "use Yiisoft\\User\\" --glob "**/Domain/**/*.php"
```

**Bad — Domain entity implements IdentityInterface:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Yiisoft\Auth\IdentityInterface; // VIOLATION: Yii auth in Domain

final class User implements IdentityInterface
{
    public function __construct(
        private readonly string $id,
        private readonly string $email,
    ) {}

    public function getId(): ?string { return $this->id; }
}
```

**Good — Infrastructure adapter wraps Domain entity:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use ValueObject\UserId;
use ValueObject\Email;
use ValueObject\HashedPassword;

// Pure domain aggregate — no framework imports
final class User
{
    public function __construct(
        private readonly UserId $id,
        private readonly Email $email,
        private HashedPassword $password,
    ) {}

    public function id(): UserId { return $this->id; }
    public function email(): Email { return $this->email; }
    public function password(): HashedPassword { return $this->password; }

    public function changePassword(HashedPassword $newPassword): void
    {
        $this->password = $newPassword;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Security;

use Entity\User;
use Yiisoft\Auth\IdentityInterface;

// Infrastructure adapter — implements Yii interface, wraps Domain entity
final readonly class SecurityIdentityAdapter implements IdentityInterface
{
    public function __construct(private User $user) {}

    public function getId(): ?string
    {
        return $this->user->id()->value;
    }

    public function domainUser(): User
    {
        return $this->user;
    }
}
```

### IdentityRepositoryInterface

Domain defines `UserRepositoryInterface`. Infrastructure implements `IdentityRepositoryInterface` using the domain repository.

```php
<?php

declare(strict_types=1);

namespace Security;

use Repository\UserRepositoryInterface;
use ValueObject\UserId;
use Yiisoft\Auth\IdentityInterface;
use Yiisoft\Auth\IdentityRepositoryInterface;

// Infrastructure: delegates lookup to domain repository, wraps result
final readonly class IdentityRepository implements IdentityRepositoryInterface
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
    ) {}

    public function findIdentity(string $id): ?IdentityInterface
    {
        $user = $this->userRepository->findById(new UserId($id));

        return $user !== null ? new SecurityIdentityAdapter($user) : null;
    }
}
```

### CurrentUser Service

`Yiisoft\User\CurrentUser` provides access to the authenticated user. Inject via DI in Presentation and Application layers only.

| Method | Description |
|--------|-------------|
| `isGuest()` | Check if user is not authenticated |
| `getIdentity()` | Get current `IdentityInterface` instance |
| `login(IdentityInterface $identity)` | Authenticate user |
| `logout()` | End user session |

**Authentication events:** `BeforeLogin`, `AfterLogin`, `BeforeLogout`, `AfterLogout`.

### Authentication Middleware

`Yiisoft\Auth\Middleware\Authentication` protects routes. Configure at route level or group level.

| Method | Class | Use Case |
|--------|-------|----------|
| Bearer Token | `Yiisoft\Auth\Method\HttpBearer` | JWT / API tokens |
| API Key | `Yiisoft\Auth\Method\QueryParameter` | Simple API key via query string |
| Header Token | `Yiisoft\Auth\Method\HttpHeader` | Custom header authentication |
| Composite | `Yiisoft\Auth\Method\Composite` | Multiple methods combined |

**Route-level middleware configuration:**
```php
<?php

declare(strict_types=1);

// config/web/routes.php

use Yiisoft\Auth\Middleware\Authentication;
use Yiisoft\Router\Route;
use Yiisoft\Router\Group;

return [
    Route::get('/health')
        ->action([HealthAction::class, '__invoke'])
        ->name('health'),

    Group::create('/api/v1')
        ->middleware(Authentication::class)
        ->routes(
            Route::get('/orders')
                ->action([ListOrdersAction::class, '__invoke'])
                ->name('orders.list'),
            Route::post('/orders')
                ->action([CreateOrderAction::class, '__invoke'])
                ->name('orders.create'),
        ),

    // Public routes — no auth middleware
    Group::create('/api/public')
        ->routes(
            Route::post('/login')
                ->action([LoginAction::class, '__invoke'])
                ->name('auth.login'),
        ),
];
```

**DI configuration for authentication method:**
```php
<?php

declare(strict_types=1);

// config/common/di/auth.php

use Security\IdentityRepository;
use Yiisoft\Auth\IdentityRepositoryInterface;
use Yiisoft\Auth\Method\HttpBearer;
use Yiisoft\Auth\AuthenticationMethodInterface;

return [
    IdentityRepositoryInterface::class => IdentityRepository::class,
    AuthenticationMethodInterface::class => HttpBearer::class,
];
```

## Authorization (yiisoft/rbac)

### RBAC Architecture

| Concept | Description | Example |
|---------|-------------|---------|
| Permission | Granular access unit | `createPost`, `updatePost`, `deletePost` |
| Role | Groups permissions, supports inheritance | `author`, `editor`, `admin` |
| Rule | Dynamic context-aware check | `AuthorRule` checks post ownership |

**Detection:**
```bash
# RBAC in Domain layer — violation (MUST be zero)
Grep: "use Yiisoft\\Rbac\\" --glob "**/Domain/**/*.php"

# Access checks in presentation
Grep: "userHasPermission" --glob "**/Presentation/**/*.php"
Grep: "AccessCheckerInterface" --glob "**/*.php"
```

### Key Interfaces

| Interface | Responsibility |
|-----------|---------------|
| `AccessCheckerInterface` | Check if user has permission |
| `ManagerInterface` | Manage role/permission hierarchy |
| `ItemsStorageInterface` | Store permission and role definitions |
| `AssignmentsStorageInterface` | Map users to roles |

### Storage Strategies

```php
<?php

declare(strict_types=1);

// config/common/di/rbac.php — PHP file storage (semi-static roles)
use Yiisoft\Rbac\Php\AssignmentsStorage;
use Yiisoft\Rbac\Php\ItemsStorage;

return [
    \Yiisoft\Rbac\ItemsStorageInterface::class => [
        'class' => ItemsStorage::class,
        '__construct()' => ['directory' => '@runtime/rbac'],
    ],
    \Yiisoft\Rbac\AssignmentsStorageInterface::class => [
        'class' => AssignmentsStorage::class,
        '__construct()' => ['directory' => '@runtime/rbac'],
    ],
];

// Alternative: Database storage (dynamic assignments)
// Use Yiisoft\Rbac\Db\ItemsStorage and Yiisoft\Rbac\Db\AssignmentsStorage
```

### Rules for Domain Logic Delegation

RBAC Rules should not contain business logic. Delegate to domain Specifications.

**Bad — business logic in RBAC Rule:**
```php
<?php

declare(strict_types=1);

namespace Security\Rbac;

use Yiisoft\Rbac\Item;
use Yiisoft\Rbac\RuleContext;
use Yiisoft\Rbac\RuleInterface;
use Yiisoft\Db\Connection\ConnectionInterface;

// VIOLATION: Database query and business logic in RBAC Rule
final readonly class AuthorRule implements RuleInterface
{
    public function __construct(private ConnectionInterface $db) {}

    public function execute(?string $userId, Item $item, RuleContext $context): bool
    {
        $post = $context->getParameterValue('post');

        return $this->db->createCommand(
            'SELECT author_id FROM posts WHERE id = :id',
            ['id' => $post->id()],
        )->queryScalar() === $userId;
    }
}
```

**Good — Rule delegates to domain Specification:**
```php
<?php

declare(strict_types=1);

namespace Specification;

use Entity\Post;

// Pure domain specification — no framework dependency
final readonly class IsPostAuthorSpecification
{
    public function isSatisfiedBy(Post $post, string $userId): bool
    {
        return $post->authorId()->value === $userId;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Security\Rbac;

use Specification\IsPostAuthorSpecification;
use Yiisoft\Rbac\Item;
use Yiisoft\Rbac\RuleContext;
use Yiisoft\Rbac\RuleInterface;

// Infrastructure: Rule delegates to domain Specification
final readonly class AuthorRule implements RuleInterface
{
    public function __construct(
        private IsPostAuthorSpecification $specification,
    ) {}

    public function execute(?string $userId, Item $item, RuleContext $context): bool
    {
        $post = $context->getParameterValue('post');

        return $this->specification->isSatisfiedBy($post, $userId);
    }
}
```

### Access Checking in Actions

```php
<?php

declare(strict_types=1);

namespace Api\Post;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Yiisoft\DataResponse\DataResponseFactoryInterface;
use Yiisoft\Http\Status;
use Yiisoft\User\CurrentUser;
use Yiisoft\Rbac\AccessCheckerInterface;

final readonly class UpdatePostAction
{
    public function __construct(
        private CurrentUser $currentUser,
        private AccessCheckerInterface $accessChecker,
        private UpdatePostUseCase $updatePost,
        private DataResponseFactoryInterface $responseFactory,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $this->currentUser->getIdentity()->getId();
        $post = $this->findPost($request);

        if (!$this->accessChecker->userHasPermission($userId, 'updatePost', ['post' => $post])) {
            return $this->responseFactory
                ->createResponse(['error' => 'Forbidden'])
                ->withStatus(Status::FORBIDDEN);
        }

        $result = $this->updatePost->execute($post, $request->getParsedBody());

        return $this->responseFactory->createResponse($result->toArray());
    }
}
```

## Password Handling

### Domain Port Pattern

Domain defines `PasswordHasherInterface`. Infrastructure implements it with `yiisoft/security`.

```php
<?php

declare(strict_types=1);

namespace Service;

use ValueObject\HashedPassword;

// Domain port — pure PHP interface
interface PasswordHasherInterface
{
    public function hash(string $plainPassword): HashedPassword;
    public function verify(HashedPassword $hashedPassword, string $plainPassword): bool;
}
```

```php
<?php

declare(strict_types=1);

namespace Security;

use Service\PasswordHasherInterface;
use ValueObject\HashedPassword;
use Yiisoft\Security\PasswordHasher as YiiPasswordHasherLib;

// Infrastructure adapter — wraps Yii security package
final readonly class YiiPasswordHasher implements PasswordHasherInterface
{
    public function __construct(
        private YiiPasswordHasherLib $hasher,
    ) {}

    public function hash(string $plainPassword): HashedPassword
    {
        return new HashedPassword($this->hasher->hash($plainPassword));
    }

    public function verify(HashedPassword $hashedPassword, string $plainPassword): bool
    {
        return $this->hasher->validate($plainPassword, $hashedPassword->value);
    }
}
```

**DI wiring:**
```php
<?php

declare(strict_types=1);

// config/common/di/security.php
return [
    \Domain\User\Service\PasswordHasherInterface::class =>
        \Infrastructure\Security\YiiPasswordHasher::class,
];
```

## CSRF Protection

`yiisoft/csrf` provides `CsrfMiddleware` for form-based applications. Not needed for stateless JWT APIs.

| Context | CSRF Needed | Approach |
|---------|-------------|----------|
| Traditional Forms | Yes | `CsrfMiddleware` + hidden field |
| SPA + API (JWT) | No | Stateless tokens handle authentication |
| AJAX with Session | Yes | `X-CSRF-TOKEN` header |

**Selective CSRF — forms only, API excluded:**
```php
<?php

declare(strict_types=1);

// config/web/routes.php
use Yiisoft\Csrf\CsrfMiddleware;
use Yiisoft\Auth\Middleware\Authentication;
use Yiisoft\Router\Group;
use Yiisoft\Router\Route;

return [
    // Web routes — CSRF protected
    Group::create('')
        ->middleware(CsrfMiddleware::class)
        ->routes(
            Route::post('/contact')->action([ContactAction::class, '__invoke']),
        ),

    // API routes — no CSRF (stateless JWT)
    Group::create('/api')
        ->middleware(Authentication::class)
        ->routes(
            Route::post('/orders')->action([CreateOrderAction::class, '__invoke']),
        ),
];
```

## Detection Patterns

```bash
# Auth interfaces in Domain (MUST be zero)
Grep: "IdentityInterface" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\Auth\\" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\User\\" --glob "**/Domain/**/*.php"

# RBAC in Domain (MUST be zero)
Grep: "use Yiisoft\\Rbac\\" --glob "**/Domain/**/*.php"

# Security package in Domain (MUST be zero)
Grep: "use Yiisoft\\Security\\" --glob "**/Domain/**/*.php"

# Service Locator for auth — violation in Domain
Grep: "CurrentUser" --glob "**/Domain/**/*.php"

# Proper auth middleware usage
Grep: "Authentication::class" --glob "config/**/*.php"

# CSRF middleware registration
Grep: "CsrfMiddleware" --glob "config/**/*.php"

# Password hashing via domain port
Grep: "PasswordHasherInterface" --glob "**/Domain/**/*.php"

# Find identity repository implementations
Grep: "IdentityRepositoryInterface" --glob "**/Infrastructure/**/*.php"
Glob: **/Infrastructure/Security/**/*.php
```

## Summary

| Aspect | DDD Layer | Yii Package | Pattern |
|--------|-----------|-------------|---------|
| Auth Identity | Infrastructure | `yiisoft/auth` | Adapter wrapping Domain entity |
| Identity Repository | Infrastructure | `yiisoft/auth` | Delegates to domain `UserRepository` |
| Current User | Presentation | `yiisoft/user` | `CurrentUser` injected via DI |
| RBAC | Infrastructure | `yiisoft/rbac` | Rules delegate to Specifications |
| Password Hashing | Domain port | `yiisoft/security` | `PasswordHasherInterface` + adapter |
| CSRF | Infrastructure | `yiisoft/csrf` | Middleware for forms only |
| Route Protection | Presentation | `yiisoft/auth` | `Authentication` middleware |
| Auth Events | Infrastructure | `yiisoft/user` | BeforeLogin, AfterLogin, etc. |
