# Symfony Security — Voter

Voters answer the authorization question "can this user do X with this thing?". One Voter per `(attribute, subject)` pair; Symfony aggregates Voter results via the access decision strategy.

See `security.md` in this folder for broader Symfony Security coverage. This file focuses on the Voter class itself and the DDD-aligned pattern of delegating to domain Specifications.

## When to write a Voter

| Scenario | Use a Voter |
|----------|-------------|
| Per-resource authorization ("can this user edit THIS Order?") | Yes |
| Role-based access (`ROLE_ADMIN`) | No — `is_granted('ROLE_ADMIN')` already works via `RoleVoter` |
| Business rule decides access | Yes — Voter delegates to a domain Specification |
| Static rule for all users | No — firewall + access control suffices |

## Voter characteristics

- **Two methods**: `supports()` (does this Voter handle this attribute/subject?) and `voteOnAttribute()` (yes/no decision).
- **One Voter per attribute family** typically — `OrderVoter` handles `VIEW`/`EDIT`/`CANCEL` on `Order`.
- **No business logic in `voteOnAttribute()` directly** — delegate to a domain Specification when business rules are non-trivial.
- **Stateless**: dependencies via constructor; no per-call state.

## Template — Simple Voter (ownership check)

```php
<?php

declare(strict_types=1);

namespace Security\Voter;

use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

/** @extends Voter<string, Order> */
final class OrderVoter extends Voter
{
    public const VIEW = 'VIEW';
    public const EDIT = 'EDIT';
    public const CANCEL = 'CANCEL';

    protected function supports(string $attribute, mixed $subject): bool
    {
        return in_array($attribute, [self::VIEW, self::EDIT, self::CANCEL], true)
            && $subject instanceof Order;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        \assert($subject instanceof Order);

        $user = $token->getUser();
        if (!$user instanceof UserInterface) {
            return false;
        }

        return match ($attribute) {
            self::VIEW => $this->canView($subject, $user),
            self::EDIT => $this->canEdit($subject, $user),
            self::CANCEL => $this->canCancel($subject, $user),
        };
    }

    private function canView(Order $order, UserInterface $user): bool
    {
        return $order->customerId()->equals($user->id());
    }

    private function canEdit(Order $order, UserInterface $user): bool
    {
        return $order->customerId()->equals($user->id())
            && $order->status()->isDraft();
    }

    private function canCancel(Order $order, UserInterface $user): bool
    {
        return $order->customerId()->equals($user->id())
            && $order->status()->canBeCancelled();
    }
}
```

## Template — Voter delegating to a domain Specification (DDD-aligned)

When the rule is non-trivial, factor it into a domain Specification (see `acc:create-specification`) and have the Voter call it. This keeps business rules in the domain and reusable from non-HTTP contexts.

```php
<?php

declare(strict_types=1);

namespace Security\Voter;

use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Authorization\Voter\Voter;

/** @extends Voter<string, Order> */
final class OrderCancelVoter extends Voter
{
    public function __construct(
        private readonly CanCancelOrderSpecification $canCancel,
    ) {}

    protected function supports(string $attribute, mixed $subject): bool
    {
        return $attribute === 'CANCEL' && $subject instanceof Order;
    }

    protected function voteOnAttribute(string $attribute, mixed $subject, TokenInterface $token): bool
    {
        \assert($subject instanceof Order);

        $user = $token->getUser();
        if (!$user instanceof UserInterface) {
            return false;
        }

        // Domain Specification encodes the rule once; reusable from CLI / async / tests.
        return $this->canCancel->isSatisfiedBy($subject, $user->id());
    }
}
```

## Usage from a controller / action

```php
<?php

declare(strict_types=1);

namespace Action\Cancel;

use Symfony\Component\Security\Http\Attribute\IsGranted;

#[\Symfony\Component\Routing\Attribute\Route('/orders/{id}/cancel', methods: ['POST'])]
final readonly class CancelOrderAction
{
    public function __construct(
        private CancelOrderUseCase $useCase,
    ) {}

    #[IsGranted('CANCEL', 'order')]
    public function __invoke(Order $order): Response
    {
        $this->useCase->execute(new CancelOrderCommand($order->id()));

        return new JsonResponse(['status' => 'cancelled']);
    }
}
```

Or imperatively in the action body:

```php
if (!$this->security->isGranted('CANCEL', $order)) {
    throw new AccessDeniedException();
}
```

## Wiring in `services.yaml`

Voters are auto-tagged by Symfony when `autoconfigure: true`. No manual tag needed unless you opt out of auto-config.

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Voter loads from a repository | N+1 queries on list endpoints | Pass the loaded entity as subject; don't reload |
| Business rule inlined in Voter | Same rule duplicated in CLI / async | Move to a domain Specification; Voter calls it |
| One mega Voter handling 5+ unrelated subjects | Hard to reason about; `supports()` becomes a switch | One Voter per subject family |
| Voter throws on bad subject | Should return false from `supports()` | `supports()` is the type guard; never throw |
| Voter querying user properties directly via `$token->getUser()->getEmail()->raw()` | Domain leak | Use a `UserId` / specification |
