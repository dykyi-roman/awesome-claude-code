# Security in CodeIgniter 4

Shield authentication, Filters authorization, CSRF protection, and password hashing with DDD integration.

## Shield Authentication

### Overview

CodeIgniter Shield (`codeigniter4/shield`) is the official auth package providing:
- Session-based authentication (username/email + password)
- Access Token authentication (stateless API)
- HMAC SHA256 authentication (stateless API)
- JWT authentication (stateless API)
- Groups-based authorization (RBAC)
- User-level permissions

### Authentication Flow

```
Request -> Filter (shield) -> Authenticate
  | Session: cookie -> session store -> UserProvider -> UserIdentity
  | Token: Authorization header -> token store -> UserProvider -> UserIdentity
  | HMAC: Authorization + body hash -> key store -> UserProvider -> UserIdentity
  | JWT: Authorization header -> JWT decode -> UserProvider -> UserIdentity
```

### DDD Integration: User Identity Separation

Domain `User` aggregate stays pure PHP. Infrastructure `ShieldUserProvider` wraps domain entity.

**Detection:**
```bash
# Shield User model in Domain
Grep: "use CodeIgniter\\Shield" --glob "**/Domain/**/*.php"
Grep: "extends UserIdentity" --glob "**/Domain/**/*.php"
Grep: "HasAccessTokens|Authenticatable" --glob "**/Domain/**/*.php"
```

**Bad -- Shield UserIdentity as Domain Entity:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

use CodeIgniter\Shield\Entities\UserIdentity; // VIOLATION: Shield in Domain

final class User extends UserIdentity
{
    public function isAdmin(): bool
    {
        return $this->inGroup('admin'); // VIOLATION: Shield RBAC in Domain
    }
}
```

**Good -- Pure Domain Entity + Infrastructure Adapter:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

use App\Domain\User\ValueObject\UserId;
use App\Domain\User\ValueObject\Email;
use App\Domain\User\ValueObject\UserRole;

// Pure domain aggregate -- no framework imports
final class User
{
    public function __construct(
        private readonly UserId $id,
        private readonly Email $email,
        private UserRole $role,
    ) {}

    public function isAdmin(): bool
    {
        return $this->role === UserRole::Admin;
    }

    public function id(): UserId { return $this->id; }
    public function email(): Email { return $this->email; }
    public function role(): UserRole { return $this->role; }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Security;

use App\Domain\User\Entity\User;
use App\Domain\User\Repository\UserRepositoryInterface;
use CodeIgniter\Shield\Models\UserModel as ShieldUserModel;

// Infrastructure adapter -- maps Shield identity to Domain User
final readonly class ShieldUserProvider
{
    public function __construct(
        private ShieldUserModel $shieldModel,
        private UserRepositoryInterface $userRepository,
    ) {}

    public function findDomainUser(int $shieldUserId): ?User
    {
        return $this->userRepository->findByExternalId((string) $shieldUserId);
    }
}
```

## Authorization with Groups and Permissions

### Shield Groups Configuration

```php
<?php

declare(strict_types=1);

// app/Config/AuthGroups.php
namespace Config;

use CodeIgniter\Shield\Config\AuthGroups as ShieldAuthGroups;

final class AuthGroups extends ShieldAuthGroups
{
    public array $groups = [
        'superadmin' => ['title' => 'Super Admin', 'description' => 'Full access'],
        'admin'      => ['title' => 'Admin', 'description' => 'Admin panel access'],
        'user'       => ['title' => 'User', 'description' => 'Standard user'],
    ];

    public array $permissions = [
        'admin.access'  => 'Can access admin area',
        'users.create'  => 'Can create users',
        'users.edit'    => 'Can edit users',
        'users.delete'  => 'Can delete users',
        'orders.manage' => 'Can manage orders',
    ];

    public array $matrix = [
        'superadmin' => ['admin.*', 'users.*', 'orders.*'],
        'admin'      => ['admin.access', 'users.create', 'users.edit', 'orders.manage'],
        'user'       => [],
    ];
}
```

### DDD: Authorization via Domain Specifications

**Detection:**
```bash
# Shield permission checks in Domain -- violation
Grep: "->can\\(|->inGroup\\(|->hasPermission\\(" --glob "**/Domain/**/*.php"

# Shield auth helper in Domain -- violation
Grep: "auth\\(\\)" --glob "**/Domain/**/*.php"
```

**Bad -- Shield permission checks in Domain:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Service;

use App\Domain\Order\Entity\Order;

final readonly class OrderService
{
    public function cancel(Order $order, $user): void
    {
        // VIOLATION: Shield authorization in Domain
        if (!$user->can('orders.manage')) {
            throw new \RuntimeException('Not authorized');
        }

        $order->cancel();
    }
}
```

**Good -- Domain Specification + Filter authorization:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Specification;

use App\Domain\Order\Entity\Order;
use App\Domain\User\Entity\User;

// Pure domain specification -- no framework dependency
final readonly class CanCancelOrderSpecification
{
    public function isSatisfiedBy(Order $order, User $user): bool
    {
        return $order->isOwnedBy($user->id()) || $user->isAdmin();
    }
}
```

```php
<?php

declare(strict_types=1);

// Route-level authorization via Shield Filter
// app/Config/Routes.php
$routes->group('api/admin', ['filter' => 'group:admin,superadmin'], static function ($routes): void {
    $routes->group('', ['filter' => 'permission:orders.manage'], static function ($routes): void {
        $routes->put('orders/(:num)/cancel', 'Api\OrderController::cancel/$1');
    });
});
```

## Filters for Authorization

### Custom Authorization Filter

```php
<?php

declare(strict_types=1);

namespace App\Filters;

use App\Domain\Order\Specification\CanCancelOrderSpecification;
use CodeIgniter\Filters\FilterInterface;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;

final readonly class OrderOwnerFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null): RequestInterface|ResponseInterface|void
    {
        $user = auth()->user();
        if ($user === null) {
            return redirect()->to('/login');
        }

        $orderId = $request->getUri()->getSegment(3);
        $orderRepository = service('orderRepository');
        $order = $orderRepository->findById($orderId);

        if ($order === null) {
            return service('response')->setStatusCode(404);
        }

        $specification = new CanCancelOrderSpecification();
        $domainUser = service('shieldUserProvider')->findDomainUser((int) $user->id);

        if ($domainUser === null || !$specification->isSatisfiedBy($order, $domainUser)) {
            return service('response')
                ->setStatusCode(403)
                ->setJSON(['error' => 'Forbidden']);
        }
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null): ResponseInterface|void
    {
    }
}
```

### Registering Filters

```php
<?php

declare(strict_types=1);

// app/Config/Filters.php
namespace Config;

use App\Filters\OrderOwnerFilter;
use CodeIgniter\Config\Filters as BaseFilters;
use CodeIgniter\Filters\CSRF;
use CodeIgniter\Shield\Filters\SessionAuth;
use CodeIgniter\Shield\Filters\GroupFilter;
use CodeIgniter\Shield\Filters\PermissionFilter;

final class Filters extends BaseFilters
{
    public array $aliases = [
        'csrf'        => CSRF::class,
        'auth'        => SessionAuth::class,
        'group'       => GroupFilter::class,
        'permission'  => PermissionFilter::class,
        'orderOwner'  => OrderOwnerFilter::class,
    ];

    public array $globals = [
        'before' => ['csrf' => ['except' => 'api/*']],
        'after'  => [],
    ];

    public array $filters = [
        'auth' => ['before' => ['api/*']],
    ];
}
```

### Filter Execution Order

```
Request -> Global Before Filters -> Route Filters -> Controller
                                                         |
Response <- Global After Filters <- Route Filters <------+
```

| Filter Type | Scope | Configuration |
|-------------|-------|---------------|
| Global `before` | All requests | `$globals['before']` |
| Global `after` | All responses | `$globals['after']` |
| Route filter | Specific routes | `$routes->group(..., ['filter' => '...'])` |
| Alias filter | Pattern-based | `$filters['alias'] = ['before' => ['uri/*']]` |

## Password Hashing

### DDD: Password Hasher Port

Domain defines a port for password hashing; Infrastructure implements it via Shield.

**Detection:**
```bash
# Password hashing in Domain -- violation
Grep: "Passwords::" --glob "**/Domain/**/*.php"
Grep: "password_hash\\(|password_verify\\(" --glob "**/Domain/**/*.php"

# Shield Passwords in Application -- should use domain port
Grep: "use CodeIgniter\\Shield\\Authentication\\Passwords" --glob "**/Application/**/*.php"
```

**Bad -- Shield hasher in Domain:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

use CodeIgniter\Shield\Authentication\Passwords; // VIOLATION: Shield in Domain

final class User
{
    private string $passwordHash;

    public function changePassword(string $newPassword): void
    {
        $this->passwordHash = Passwords::hash($newPassword); // VIOLATION
    }
}
```

**Good -- Domain Port + Infrastructure Adapter:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Service;

use App\Domain\User\ValueObject\HashedPassword;

// Domain port -- pure PHP interface
interface PasswordHasherInterface
{
    public function hash(string $plainPassword): HashedPassword;
    public function verify(string $plainPassword, HashedPassword $hash): bool;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Domain\User\ValueObject;

// Immutable value object for hashed passwords
final readonly class HashedPassword
{
    public function __construct(
        public string $value,
    ) {}
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Security;

use App\Domain\User\Service\PasswordHasherInterface;
use App\Domain\User\ValueObject\HashedPassword;
use CodeIgniter\Shield\Authentication\Passwords;

// Infrastructure adapter -- wraps Shield Passwords
final readonly class ShieldPasswordHasher implements PasswordHasherInterface
{
    public function __construct(
        private Passwords $passwords,
    ) {}

    public function hash(string $plainPassword): HashedPassword
    {
        return new HashedPassword(
            $this->passwords->hash($plainPassword),
        );
    }

    public function verify(string $plainPassword, HashedPassword $hash): bool
    {
        return $this->passwords->verify($plainPassword, $hash->value);
    }
}
```

### Password Change UseCase

```php
<?php

declare(strict_types=1);

namespace App\Application\User\UseCase;

use App\Domain\User\Repository\UserRepositoryInterface;
use App\Domain\User\Service\PasswordHasherInterface;
use App\Domain\User\ValueObject\UserId;

final readonly class ChangePasswordUseCase
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private PasswordHasherInterface $passwordHasher,
    ) {}

    public function execute(UserId $userId, string $currentPassword, string $newPassword): void
    {
        $user = $this->userRepository->findById($userId)
            ?? throw new \DomainException('User not found');

        if (!$this->passwordHasher->verify($currentPassword, $user->password())) {
            throw new \DomainException('Current password is incorrect');
        }

        $hashedPassword = $this->passwordHasher->hash($newPassword);
        $user->changePassword($hashedPassword);

        $this->userRepository->save($user);
    }
}
```

## CSRF Protection

### Configuration

```php
<?php

declare(strict_types=1);

// app/Config/Filters.php -- CSRF enabled globally except API routes
public array $globals = [
    'before' => [
        'csrf' => ['except' => ['api/*']],
    ],
];
```

### CSRF in Forms

```php
<!-- Blade-style view -->
<form method="post" action="/orders">
    <?= csrf_field() ?>
    <input type="text" name="product" />
    <button type="submit">Order</button>
</form>
```

### CSRF Configuration Options

```php
<?php

declare(strict_types=1);

// app/Config/Security.php
namespace Config;

use CodeIgniter\Config\BaseConfig;

final class Security extends BaseConfig
{
    public string $csrfProtection = 'session'; // 'cookie' or 'session'
    public string $tokenRandomize = true;
    public string $tokenName      = 'csrf_token_name';
    public string $headerName     = 'X-CSRF-TOKEN';
    public string $cookieName     = 'csrf_cookie_name';
    public int $expires           = 7200;
    public bool $regenerate       = true;
    public bool $redirect         = false;
    public string $samesite       = 'Lax';
}
```

### API Authentication (Stateless, No CSRF)

For API routes, use Shield's token or HMAC authenticator instead of CSRF:

```php
<?php

declare(strict_types=1);

// app/Config/Routes.php
$routes->group('api', ['filter' => 'tokens'], static function ($routes): void {
    $routes->resource('orders', ['controller' => 'Api\OrderController']);
});
```

| Context | CSRF Needed | Approach |
|---------|-------------|----------|
| Traditional Forms | Yes | `csrf_field()`, session-based token |
| SPA + API (JWT) | No | Stateless tokens handle authentication |
| SPA + API (Access Token) | No | Shield `tokens` filter |
| AJAX with Session | Yes | `X-CSRF-TOKEN` header from meta tag |

## Authentication Events

Listen to Shield auth events in Infrastructure; dispatch domain events from listeners.

**Detection:**
```bash
# Shield events usage
Grep: "use CodeIgniter\\Shield\\Events" --glob "app/**/*.php"

# Custom event listeners
Grep: "Events::on\\(" --glob "app/**/*.php"
```

```php
<?php

declare(strict_types=1);

// app/Config/Events.php
namespace Config;

use App\Infrastructure\Security\LoginEventHandler;
use CodeIgniter\Events\Events;
use CodeIgniter\Shield\Events as ShieldEvents;

Events::on('login', [LoginEventHandler::class, 'handle']);
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Security;

use App\Domain\User\Event\UserLoggedInEvent;
use App\Shared\Domain\EventDispatcherInterface;
use CodeIgniter\Shield\Entities\User as ShieldUser;

// Infrastructure listener -- translates Shield event to domain event
final readonly class LoginEventHandler
{
    public function __construct(
        private EventDispatcherInterface $domainEvents,
        private ShieldUserProvider $userProvider,
    ) {}

    public static function handle(ShieldUser $shieldUser): void
    {
        $handler = service('loginEventHandler');
        $domainUser = $handler->userProvider->findDomainUser((int) $shieldUser->id);

        if ($domainUser !== null) {
            $handler->domainEvents->dispatch(
                new UserLoggedInEvent($domainUser->id()),
            );
        }
    }
}
```

## Rate Limiting

### Rate Limit Filter

```php
<?php

declare(strict_types=1);

namespace App\Filters;

use CodeIgniter\Filters\FilterInterface;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;

final readonly class RateLimitFilter implements FilterInterface
{
    private const int MAX_REQUESTS = 60;
    private const int WINDOW_SECONDS = 60;

    public function before(RequestInterface $request, $arguments = null): RequestInterface|ResponseInterface|void
    {
        $cache = service('cache');
        $ip = $request->getIPAddress();
        $key = "rate_limit:{$ip}";

        $hits = (int) $cache->get($key);

        if ($hits >= self::MAX_REQUESTS) {
            return service('response')
                ->setStatusCode(429)
                ->setJSON(['error' => 'Too many requests']);
        }

        $cache->save($key, $hits + 1, self::WINDOW_SECONDS);
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null): ResponseInterface|void
    {
    }
}
```

## Detection Patterns

```bash
# Shield in Domain layer -- violation
Grep: "use CodeIgniter\\Shield" --glob "**/Domain/**/*.php"
Grep: "->can\\(|->inGroup\\(|->hasPermission\\(" --glob "**/Domain/**/*.php"

# Shield auth helper in Domain -- violation
Grep: "auth\\(\\)" --glob "**/Domain/**/*.php"

# Password hashing in Domain -- violation
Grep: "Passwords::" --glob "**/Domain/**/*.php"
Grep: "password_hash\\(|password_verify\\(" --glob "**/Domain/**/*.php"

# Shield in Application layer (should use domain port)
Grep: "use CodeIgniter\\Shield" --glob "**/Application/**/*.php"

# Missing CSRF on web routes
Grep: "csrf" --glob "app/Config/Filters.php" --output_mode count

# Find all filters
Grep: "implements FilterInterface" --glob "app/Filters/**/*.php"

# Find Shield filter registrations
Grep: "SessionAuth|GroupFilter|PermissionFilter|TokenFilter" --glob "app/Config/Filters.php"

# Find route-level authorization
Grep: "'filter'" --glob "app/Config/Routes.php"
```

## Summary Table

| Aspect | DDD Layer | CI4/Shield Component | Integration Pattern |
|--------|-----------|---------------------|---------------------|
| User Identity | Domain: pure User entity | Shield: UserIdentity | Infrastructure ShieldUserProvider adapter |
| Authorization | Domain: Specifications | Shield: Groups + Permissions | Filter delegates to Specification |
| Authentication | N/A (Infrastructure) | Shield: Session/Token/HMAC/JWT | Filter + `auth()` helper |
| Password Hashing | Domain: PasswordHasherInterface port | Shield: Passwords | Infrastructure ShieldPasswordHasher adapter |
| CSRF | N/A (Presentation) | CI4 CSRF Filter | Global filter, except API routes |
| Route Access | N/A (Presentation) | Shield: group/permission filters | Route-level filter configuration |
| Rate Limiting | N/A (Infrastructure) | Custom Filter + Cache | Filter with Redis/cache backend |
| Auth Events | Domain: domain events | Shield: Events system | Infrastructure listener dispatches domain events |
