# Symfony Security in DDD Context

Authentication, authorization, voters, and firewall patterns aligned with Domain-Driven Design.

## UserInterface as Domain Aggregate

The `UserInterface` contract belongs to Symfony Security. Domain must not implement it directly.

**Detection:**
```bash
# UserInterface in Domain layer — violation
Grep: "use Symfony\\\\Component\\\\Security\\\\Core\\\\User\\\\UserInterface" --glob "**/Domain/**/*.php"
Grep: "implements.*UserInterface" --glob "**/Domain/**/*.php"

# PasswordAuthenticatedUserInterface in Domain — violation
Grep: "PasswordAuthenticatedUserInterface" --glob "**/Domain/**/*.php"
```

**Bad — Domain entity implements Symfony interface:**
```php
<?php

declare(strict_types=1);

namespace App\User\Domain\Entity;

use Symfony\Component\Security\Core\User\UserInterface;
use Symfony\Component\Security\Core\User\PasswordAuthenticatedUserInterface;

// VIOLATION: Domain coupled to Symfony Security
class User implements UserInterface, PasswordAuthenticatedUserInterface
{
    public function getRoles(): array { return $this->roles; }
    public function eraseCredentials(): void {}
    public function getUserIdentifier(): string { return $this->email; }
    public function getPassword(): ?string { return $this->hashedPassword; }
}
```

**Good — Infrastructure adapter wraps Domain aggregate:**
```php
<?php

declare(strict_types=1);

namespace App\User\Domain\Entity;

// Pure domain aggregate — no framework imports
final class User
{
    /** @var array<string> */
    private array $roles;

    public function __construct(
        private readonly UserId $id,
        private readonly Email $email,
        private HashedPassword $password,
    ) {
        $this->roles = ['ROLE_USER'];
    }

    public function id(): UserId { return $this->id; }
    public function email(): Email { return $this->email; }
    public function password(): HashedPassword { return $this->password; }

    /** @return array<string> */
    public function roles(): array { return $this->roles; }

    public function changePassword(HashedPassword $newPassword): void
    {
        $this->password = $newPassword;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace App\User\Infrastructure\Security;

use App\User\Domain\Entity\User as DomainUser;
use Symfony\Component\Security\Core\User\PasswordAuthenticatedUserInterface;
use Symfony\Component\Security\Core\User\UserInterface;

// Infrastructure adapter — implements Symfony interface, wraps Domain entity
final readonly class SecurityUser implements UserInterface, PasswordAuthenticatedUserInterface
{
    public function __construct(
        private DomainUser $user,
    ) {}

    public function getUserIdentifier(): string
    {
        return $this->user->email()->value;
    }

    public function getRoles(): array
    {
        return $this->user->roles();
    }

    public function getPassword(): ?string
    {
        return $this->user->password()->value;
    }

    public function eraseCredentials(): void {}

    public function domainUser(): DomainUser
    {
        return $this->user;
    }
}
```

## Custom Voters for Authorization

Voters implement authorization decisions. DDD approach: delegate business rules to domain Specifications.

**Detection:**
```bash
# Voters in project
Grep: "extends Voter|implements VoterInterface" --glob "src/**/*.php"

# Role checks scattered in controllers — should be Voters
Grep: "isGranted\\(|denyAccessUnlessGranted\\(" --glob "**/Controller/**/*.php"
Grep: "->isGranted\\(" --glob "**/Application/**/*.php"
```

**Bad — authorization logic in controller:**
```php
<?php

declare(strict_types=1);

namespace App\Order\Presentation\Api;

final readonly class CancelOrderAction
{
    public function __invoke(Request $request, Order $order): JsonResponse
    {
        // VIOLATION: Authorization logic in Presentation
        $user = $this->getUser();
        if ($order->customerId() !== $user->getId() && !in_array('ROLE_ADMIN', $user->getRoles())) {
            throw new AccessDeniedException();
        }

        // ...
    }
}
```

**Good — Voter delegates to domain Specification:**
```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\Security;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\Specification\CanCancelOrderSpecification;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

/** @extends Voter<string, Order> */
final class OrderCancelVoter extends Voter
{
    public function __construct(
        private readonly CanCancelOrderSpecification $specification,
    ) {}

    protected function supports(string $attribute, mixed $subject): bool
    {
        return $attribute === 'CANCEL' && $subject instanceof Order;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        $securityUser = $token->getUser();
        if (!$securityUser instanceof SecurityUser) {
            return false;
        }

        return $this->specification->isSatisfiedBy($subject, $securityUser->domainUser());
    }
}
```

```php
<?php

declare(strict_types=1);

namespace App\Order\Domain\Specification;

use App\Order\Domain\Entity\Order;
use App\User\Domain\Entity\User;

// Pure domain specification — no framework dependency
final readonly class CanCancelOrderSpecification
{
    public function isSatisfiedBy(Order $order, User $user): bool
    {
        if ($order->isShipped()) {
            return false;
        }

        return $order->customerId()->equals($user->id())
            || $user->hasRole('ROLE_ADMIN');
    }
}
```

## Firewall and Access Control

Security configuration lives in Infrastructure. Keep `security.yaml` aligned with DDD boundaries.

```yaml
# config/packages/security.yaml
security:
    password_hashers:
        App\User\Infrastructure\Security\SecurityUser: 'auto'

    providers:
        app_user_provider:
            id: App\User\Infrastructure\Security\UserProvider

    firewalls:
        dev:
            pattern: ^/(_(profiler|wdt)|css|images|js)/
            security: false

        api:
            pattern: ^/api
            stateless: true
            json_login:
                check_path: /api/login
                username_path: email
                password_path: password
                success_handler: App\User\Infrastructure\Security\LoginSuccessHandler
            jwt: ~

        main:
            lazy: true
            provider: app_user_provider

    access_control:
        - { path: ^/api/login, roles: PUBLIC_ACCESS }
        - { path: ^/api/admin, roles: ROLE_ADMIN }
        - { path: ^/api, roles: ROLE_USER }
```

## Password Hashing

Domain defines a port for password hashing; Infrastructure implements it via Symfony.

**Bad — Symfony hasher in Application layer:**
```php
<?php

declare(strict_types=1);

namespace App\User\Application\UseCase;

use Symfony\Component\PasswordHasher\Hasher\UserPasswordHasherInterface;

// VIOLATION: Symfony in Application layer
final readonly class RegisterUserUseCase
{
    public function __construct(
        private UserPasswordHasherInterface $hasher,
    ) {}
}
```

**Good — Domain port + Infrastructure adapter:**
```php
<?php

declare(strict_types=1);

namespace App\User\Domain\Service;

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

namespace App\User\Infrastructure\Security;

use App\User\Domain\Service\PasswordHasherInterface;
use App\User\Domain\ValueObject\HashedPassword;
use Symfony\Component\PasswordHasher\Hasher\UserPasswordHasherInterface;

final readonly class SymfonyPasswordHasher implements PasswordHasherInterface
{
    public function __construct(
        private UserPasswordHasherInterface $hasher,
        private SecurityUser $templateUser,
    ) {}

    public function hash(string $plainPassword): HashedPassword
    {
        return new HashedPassword(
            $this->hasher->hashPassword($this->templateUser, $plainPassword),
        );
    }

    public function verify(HashedPassword $hashedPassword, string $plainPassword): bool
    {
        return $this->hasher->isPasswordValid($this->templateUser, $plainPassword);
    }
}
```

## CSRF Protection

| Context | CSRF Needed | Approach |
|---------|-------------|----------|
| Traditional Forms | Yes | `CsrfTokenManagerInterface`, `{{ csrf_token() }}` |
| SPA + API (JWT) | No | Stateless tokens handle authentication |
| AJAX with Session | Yes | `X-CSRF-TOKEN` header from meta tag |

## Authentication Events

Listen to Symfony auth events in Infrastructure; dispatch domain events from listeners.

```php
<?php

declare(strict_types=1);

namespace App\User\Infrastructure\Security;

use App\User\Domain\Event\UserLoggedInEvent;
use App\Shared\Domain\EventDispatcherInterface;
use Symfony\Component\EventDispatcher\Attribute\AsEventListener;
use Symfony\Component\Security\Http\Event\LoginSuccessEvent;

#[AsEventListener(event: LoginSuccessEvent::class)]
final readonly class LoginSuccessListener
{
    public function __construct(
        private EventDispatcherInterface $domainEvents,
    ) {}

    public function __invoke(LoginSuccessEvent $event): void
    {
        $securityUser = $event->getAuthenticatedToken()->getUser();

        if ($securityUser instanceof SecurityUser) {
            $this->domainEvents->dispatch(
                new UserLoggedInEvent($securityUser->domainUser()->id()),
            );
        }
    }
}
```

## #[IsGranted] vs Custom Voters

| Feature | `#[IsGranted]` Attribute | Custom Voter |
|---------|-------------------------|--------------|
| Complexity | Simple role checks | Complex business rules |
| Location | Controller attribute | Infrastructure service |
| Domain Logic | None | Delegates to Specification |
| Testability | Hard to unit test | Fully testable |
| Use When | `ROLE_ADMIN`, `ROLE_USER` | Ownership, state-based, time-based rules |

**Guideline:** Use `#[IsGranted('ROLE_ADMIN')]` for simple role gates. Use Voters with domain Specifications for any rule involving entity state or ownership.

## Summary

| Aspect | Recommendation |
|--------|---------------|
| UserInterface | Infrastructure adapter wrapping Domain aggregate |
| Authorization | Voters delegating to domain Specifications |
| Password Hashing | Domain port + Symfony Infrastructure adapter |
| Firewall Config | Infrastructure layer (`config/packages/security.yaml`) |
| CSRF | Forms yes, JWT APIs no |
| Auth Events | Infrastructure listeners dispatching domain events |
| Role Checks | `#[IsGranted]` for simple roles, Voters for business rules |
