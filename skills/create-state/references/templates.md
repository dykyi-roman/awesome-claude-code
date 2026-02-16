# State Pattern Templates

## State Interface (Domain Layer)

**File:** `src/Domain/{BoundedContext}/State/{Name}StateInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\State;

interface {Name}StateInterface
{
    public function getName(): string;

    public function {action1}({Context} $context): self;

    public function {action2}({Context} $context): self;

    public function canTransitionTo(self $state): bool;

    /** @return array<string> */
    public function allowedTransitions(): array;
}
```

---

## Abstract State

**File:** `src/Domain/{BoundedContext}/State/Abstract{Name}State.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\State;

abstract readonly class Abstract{Name}State implements {Name}StateInterface
{
    public function canTransitionTo({Name}StateInterface $state): bool
    {
        return in_array($state->getName(), $this->allowedTransitions(), true);
    }

    protected function invalidTransition(string $action): never
    {
        throw new InvalidStateTransitionException(
            sprintf('Cannot %s in %s state', $action, $this->getName())
        );
    }
}
```

---

## Concrete State

**File:** `src/Domain/{BoundedContext}/State/{StateName}State.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\State;

final readonly class {StateName}State extends Abstract{Name}State
{
    public function getName(): string
    {
        return '{state_name}';
    }

    public function {action1}({Context} $context): {Name}StateInterface
    {
        {action1Implementation}

        return new {NextState}State();
    }

    public function {action2}({Context} $context): {Name}StateInterface
    {
        $this->invalidTransition('{action2}');
    }

    public function allowedTransitions(): array
    {
        return ['{next_state_1}', '{next_state_2}'];
    }
}
```

---

## State Context

**File:** `src/Domain/{BoundedContext}/Entity/{Name}.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Entity;

use Domain\{BoundedContext}\State\{Name}StateInterface;

final class {Name}
{
    private {Name}StateInterface $state;

    public function __construct(
        private readonly {Name}Id $id,
        {Name}StateInterface $initialState
    ) {
        $this->state = $initialState;
    }

    public function {action1}(): void
    {
        $this->transitionTo($this->state->{action1}($this));
    }

    public function {action2}(): void
    {
        $this->transitionTo($this->state->{action2}($this));
    }

    public function getState(): {Name}StateInterface
    {
        return $this->state;
    }

    public function getStateName(): string
    {
        return $this->state->getName();
    }

    public function isInState(string $stateName): bool
    {
        return $this->state->getName() === $stateName;
    }

    private function transitionTo({Name}StateInterface $newState): void
    {
        if (!$this->state->canTransitionTo($newState)) {
            throw new InvalidStateTransitionException(
                sprintf(
                    'Cannot transition from %s to %s',
                    $this->state->getName(),
                    $newState->getName()
                )
            );
        }

        $this->state = $newState;
    }
}
```

---

## InvalidStateTransitionException

**File:** `src/Domain/{BoundedContext}/Exception/InvalidStateTransitionException.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Exception;

final class InvalidStateTransitionException extends \DomainException
{
    public function __construct(string $message)
    {
        parent::__construct($message);
    }

    public static function cannotTransition(string $from, string $to): self
    {
        return new self(sprintf('Cannot transition from %s to %s', $from, $to));
    }

    public static function actionNotAllowed(string $action, string $state): self
    {
        return new self(sprintf('Action "%s" not allowed in state "%s"', $action, $state));
    }
}
```

---

## State Factory for Reconstitution

**File:** `src/Domain/{BoundedContext}/State/{Name}StateFactory.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\State;

final class {Name}StateFactory
{
    public static function fromName(string $name): {Name}StateInterface
    {
        return match ($name) {
            'state_1' => new State1State(),
            'state_2' => new State2State(),
            'state_3' => new State3State(),
            default => throw new \InvalidArgumentException(
                sprintf('Unknown state: %s', $name)
            ),
        };
    }
}
```
