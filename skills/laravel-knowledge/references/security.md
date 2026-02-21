# Laravel Security in DDD Context

Gates, Policies, authorization with domain Specifications, password hashing, and authentication patterns.

## Gates vs Policies

| Feature | Gates | Policies |
|---------|-------|----------|
| Scope | General actions not tied to a model | Model-specific CRUD operations |
| Definition | Closure in `AppServiceProvider` | Dedicated class per model |
| Discovery | Manual registration | Auto-discovered by convention |
| DDD Use | Cross-cutting admin checks | Aggregate-level authorization |
| Testability | Harder to isolate | Easy to unit test |

## Policies with Domain Specification Delegation

**Detection:**
```bash
# Policy classes
Grep: "extends.*Policy|class.*Policy" --glob "**/Policies/**/*.php"
Glob: **/Policies/**/*Policy.php

# Inline authorization in controllers (should use Policies)
Grep: "if.*->id ===|if.*->user_id ==" --glob "**/Controllers/**/*.php"
Grep: "->isAdmin\\(\\)|->hasRole\\(" --glob "**/Controllers/**/*.php"

# Business logic in Policies (should delegate to Specification)
Grep: "DB::|->where\\(|->count\\(" --glob "**/*Policy.php"
```

**Bad — authorization logic in controller:**
```php
<?php

declare(strict_types=1);

namespace App\Http\Controllers\Order;

final readonly class CancelOrderController
{
    public function __invoke(string $orderId): JsonResponse
    {
        $order = $this->orders->findById(new OrderId($orderId));
        $user = auth()->user();

        // VIOLATION: Authorization logic scattered in controller
        if ($order->customerId()->value() !== $user->id && !$user->is_admin) {
            abort(403);
        }

        // ...
    }
}
```

**Bad — business logic in Policy:**
```php
<?php

declare(strict_types=1);

namespace App\Policies;

class OrderPolicy
{
    public function cancel(User $user, Order $order): bool
    {
        // VIOLATION: Business rules coupled to Laravel Policy
        $hasOpenPayments = DB::table('payments')
            ->where('order_id', $order->id)
            ->where('status', 'pending')
            ->exists();

        return !$hasOpenPayments
            && ($order->customer_id === $user->id || $user->is_admin);
    }
}
```

**Good — Policy delegates to domain Specification:**
```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Policy;

use App\Domain\Order\Entity\Order;
use App\Domain\Order\Specification\CanCancelOrderSpecification;
use App\Infrastructure\Auth\UserModel;
use Illuminate\Auth\Access\Response;

final class OrderPolicy
{
    public function __construct(
        private readonly CanCancelOrderSpecification $specification,
    ) {}

    public function before(UserModel $user, string $ability): ?bool
    {
        if ($user->isAdministrator()) {
            return true;
        }

        return null;
    }

    public function cancel(UserModel $user, Order $order): Response
    {
        return $this->specification->isSatisfiedBy($order, $user)
            ? Response::allow()
            : Response::deny('Cannot cancel this order.');
    }

    public function update(UserModel $user, Order $order): bool
    {
        return $order->customerId()->value() === $user->id
            && $order->status()->isEditable();
    }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Specification;

use App\Domain\Order\Entity\Order;

// Pure domain specification — no framework dependency
final readonly class CanCancelOrderSpecification
{
    public function isSatisfiedBy(Order $order, mixed $user): bool
    {
        if ($order->isShipped()) {
            return false;
        }

        return $order->customerId()->value() === $user->id;
    }
}
```

## Gates for Cross-Cutting Concerns

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Provider;

use Illuminate\Support\Facades\Gate;
use Illuminate\Support\ServiceProvider;

final class AuthorizationServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        Gate::define('access-admin', function ($user): bool {
            return in_array($user->role, ['admin', 'super-admin'], true);
        });

        Gate::define('export-data', function ($user): bool {
            return $user->hasPermission('data.export');
        });
    }
}
```

**Usage via middleware:**
```php
// routes/api.php
Route::prefix('admin')
    ->middleware('can:access-admin')
    ->group(function () {
        Route::get('/dashboard', AdminDashboardController::class);
    });
```

## User Model as Infrastructure Adapter

Domain User aggregate stays pure; Laravel `UserModel` lives in Infrastructure.

**Bad — domain logic in Eloquent User model:**
```php
<?php

declare(strict_types=1);

namespace App\Models;

use Illuminate\Foundation\Auth\User as Authenticatable;

// VIOLATION: Eloquent model with domain logic
class User extends Authenticatable
{
    public function calculateDiscount(): float
    {
        return $this->orders()->count() > 10 ? 0.15 : 0.0;
    }
}
```

**Good — separated Domain entity and Infrastructure model:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Entity;

// Pure domain aggregate
final class User
{
    public function __construct(
        private readonly UserId $id,
        private readonly Email $email,
        private readonly string $role,
    ) {}

    public function id(): UserId { return $this->id; }
    public function email(): Email { return $this->email; }
    public function hasRole(string $role): bool { return $this->role === $role; }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Auth;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Foundation\Auth\User as Authenticatable;
use Illuminate\Notifications\Notifiable;
use Laravel\Sanctum\HasApiTokens;

// Infrastructure: authentication + persistence only
final class UserModel extends Authenticatable
{
    use HasApiTokens, HasUuids, Notifiable;

    protected $table = 'users';
    protected $fillable = ['id', 'email', 'password', 'role'];
    protected $hidden = ['password', 'remember_token'];

    public function isAdministrator(): bool
    {
        return $this->role === 'admin';
    }
}
```

## Password Hashing with Domain Port

```php
<?php

declare(strict_types=1);

namespace App\Domain\User\Service;

use App\Domain\User\ValueObject\HashedPassword;

// Domain port
interface PasswordHasherInterface
{
    public function hash(string $plainPassword): HashedPassword;
    public function verify(HashedPassword $hashed, string $plain): bool;
}
```

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Auth;

use App\Domain\User\Service\PasswordHasherInterface;
use App\Domain\User\ValueObject\HashedPassword;
use Illuminate\Hashing\HashManager;

final readonly class LaravelPasswordHasher implements PasswordHasherInterface
{
    public function __construct(
        private HashManager $hash,
    ) {}

    public function hash(string $plainPassword): HashedPassword
    {
        return new HashedPassword($this->hash->make($plainPassword));
    }

    public function verify(HashedPassword $hashed, string $plain): bool
    {
        return $this->hash->check($plain, $hashed->value);
    }
}
```

## Sanctum / JWT Token Authentication

| Feature | Sanctum | Passport (OAuth2) | JWT (tymon/jwt-auth) |
|---------|---------|-------------------|---------------------|
| Complexity | Low | High | Medium |
| Use Case | SPA + Mobile API | Third-party OAuth | Stateless API |
| Token Storage | Database | Database | Stateless |
| DDD Alignment | Infrastructure layer | Infrastructure layer | Infrastructure layer |

**Sanctum in DDD setup:**
```php
// config/auth.php
'guards' => [
    'api' => [
        'driver' => 'sanctum',
        'provider' => 'users',
    ],
],

'providers' => [
    'users' => [
        'driver' => 'eloquent',
        'model' => App\Infrastructure\Auth\UserModel::class,
    ],
],
```

## Summary

| Aspect | Recommendation |
|--------|---------------|
| Authorization | Policies for model actions, Gates for general checks |
| Business Rules | Delegate from Policies to domain Specifications |
| User Model | Infrastructure `UserModel` extends Authenticatable; Domain `User` is pure |
| Password Hashing | Domain port + `LaravelPasswordHasher` adapter |
| Controller Auth | `$this->authorize()` or `can:` middleware — never inline checks |
| Admin Bypass | `before()` method in Policies |
| Token Auth | Sanctum for SPA/API, Passport for third-party OAuth |
