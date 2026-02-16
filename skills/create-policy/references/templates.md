# Policy Pattern Templates

## Policy Interface

**File:** `src/Domain/{BoundedContext}/Policy/{Name}PolicyInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Policy;

interface {Name}PolicyInterface
{
    public function evaluate({SubjectType} $subject, {ResourceType} $resource): PolicyResult;

    public function getRuleName(): string;
}
```

---

## Policy Result

**File:** `src/Domain/Shared/Policy/PolicyResult.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Policy;

final readonly class PolicyResult
{
    private function __construct(
        public bool $allowed,
        public ?string $reason = null,
        public array $metadata = []
    ) {}

    public static function allow(): self
    {
        return new self(true);
    }

    public static function deny(string $reason, array $metadata = []): self
    {
        return new self(false, $reason, $metadata);
    }

    public function isAllowed(): bool
    {
        return $this->allowed;
    }

    public function isDenied(): bool
    {
        return !$this->allowed;
    }

    public function getReason(): ?string
    {
        return $this->reason;
    }

    public function and(self $other): self
    {
        if ($this->isDenied()) {
            return $this;
        }
        return $other;
    }

    public function or(self $other): self
    {
        if ($this->isAllowed()) {
            return $this;
        }
        return $other;
    }
}
```

---

## Policy Implementation

**File:** `src/Domain/{BoundedContext}/Policy/{Name}Policy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Policy;

use Domain\Shared\Policy\PolicyResult;

final readonly class {Name}Policy implements {Name}PolicyInterface
{
    public function evaluate({SubjectType} $subject, {ResourceType} $resource): PolicyResult
    {
        if ({condition}) {
            return PolicyResult::allow();
        }

        return PolicyResult::deny('{denial_reason}', [
            'subject_id' => $subject->id()->toString(),
            'resource_id' => $resource->id()->toString(),
        ]);
    }

    public function getRuleName(): string
    {
        return '{rule_name}';
    }
}
```

---

## Composite Policy

**File:** `src/Domain/{BoundedContext}/Policy/Composite{Name}Policy.php`

```php
<?php

declare(strict_types=1);

namespace Domain\{BoundedContext}\Policy;

use Domain\Shared\Policy\PolicyResult;

final readonly class Composite{Name}Policy implements {Name}PolicyInterface
{
    /**
     * @param array<{Name}PolicyInterface> $policies
     */
    public function __construct(
        private array $policies,
        private CompositionMode $mode = CompositionMode::AllMustPass
    ) {}

    public function evaluate({SubjectType} $subject, {ResourceType} $resource): PolicyResult
    {
        return match ($this->mode) {
            CompositionMode::AllMustPass => $this->evaluateAll($subject, $resource),
            CompositionMode::AnyMustPass => $this->evaluateAny($subject, $resource),
        };
    }

    public function getRuleName(): string
    {
        return 'composite';
    }

    private function evaluateAll({SubjectType} $subject, {ResourceType} $resource): PolicyResult
    {
        foreach ($this->policies as $policy) {
            $result = $policy->evaluate($subject, $resource);
            if ($result->isDenied()) {
                return $result;
            }
        }
        return PolicyResult::allow();
    }

    private function evaluateAny({SubjectType} $subject, {ResourceType} $resource): PolicyResult
    {
        $reasons = [];
        foreach ($this->policies as $policy) {
            $result = $policy->evaluate($subject, $resource);
            if ($result->isAllowed()) {
                return PolicyResult::allow();
            }
            $reasons[] = $result->getReason();
        }
        return PolicyResult::deny(implode('; ', $reasons));
    }
}
```

---

## Composition Mode Enum

**File:** `src/Domain/Shared/Policy/CompositionMode.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Policy;

enum CompositionMode: string
{
    case AllMustPass = 'all';
    case AnyMustPass = 'any';
}
```

---

## Policy Violation Exception

**File:** `src/Domain/Shared/Exception/PolicyViolationException.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Exception;

final class PolicyViolationException extends \DomainException
{
    public function __construct(
        public readonly string $policyName,
        public readonly string $reason,
        public readonly array $metadata = []
    ) {
        parent::__construct(
            sprintf('Policy "%s" violation: %s', $policyName, $reason)
        );
    }
}
```
