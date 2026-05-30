# Symfony Validator — Custom Constraint + ConstraintValidator

The Symfony Validator component is built around `Constraint` (the declarative annotation/attribute) + `ConstraintValidator` (the imperative checker). Custom constraints let you validate domain-aware rules — uniqueness, complex format rules, cross-field checks — while keeping the validation declarative at the call site.

## When to write a custom constraint

| Scenario | Need a custom constraint? |
|----------|---------------------------|
| Email format | No — `Symfony\Component\Validator\Constraints\Email` |
| Length / range / required | No — built-ins exist |
| Email must be unique in the database | Yes — needs repository access |
| Value must be one of an enum's cases | Maybe — `Choice` works if enum cases are listed |
| Cross-field rule ("end date after start date") | Yes — class-level constraint |
| Domain-aware rule ("customer must be in good standing") | Yes — but consider keeping it in the domain entity / Specification instead |

## Constraint characteristics

- **`Constraint`**: a value-object-like class annotated with `#[Attribute]`. Holds the violation message and any parameters (e.g. `max length`).
- **`ConstraintValidator`**: the validator. Receives the value and the constraint instance, optionally adds violations via `$this->context->buildViolation(...)`.
- **Constraint and Validator are paired by convention**: `UniqueEmail` → `UniqueEmailValidator` (suffix). Symfony auto-resolves the validator by class name unless `validatedBy()` is overridden.
- **Validator may depend on services** (repositories, etc.) — registered with `autoconfigure: true` works automatically.
- **Validator must return early on null / wrong type**: don't trigger violations for "not applicable" values.

## Template — Database-aware constraint (unique email)

### Constraint

```php
<?php

declare(strict_types=1);

namespace Validator\Constraint;

use Symfony\Component\Validator\Constraint;

#[\Attribute(\Attribute::TARGET_PROPERTY | \Attribute::TARGET_METHOD)]
final class UniqueEmail extends Constraint
{
    public string $message = 'Email "{{ value }}" is already registered.';
}
```

### Validator

```php
<?php

declare(strict_types=1);

namespace Validator;

use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\ConstraintValidator;
use Symfony\Component\Validator\Exception\UnexpectedTypeException;

final class UniqueEmailValidator extends ConstraintValidator
{
    public function __construct(
        private readonly UserRepositoryInterface $userRepository,
    ) {}

    public function validate(mixed $value, Constraint $constraint): void
    {
        if (!$constraint instanceof UniqueEmail) {
            throw new UnexpectedTypeException($constraint, UniqueEmail::class);
        }

        if ($value === null || $value === '') {
            return;  // Other constraints (NotBlank) handle these
        }

        if (!is_string($value)) {
            throw new UnexpectedTypeException($value, 'string');
        }

        if ($this->userRepository->existsByEmail(new Email($value))) {
            $this->context->buildViolation($constraint->message)
                ->setParameter('{{ value }}', $value)
                ->addViolation();
        }
    }
}
```

### Usage on a request DTO

```php
<?php

declare(strict_types=1);

namespace Request;

use Symfony\Component\Validator\Constraints as Assert;

final class CreateUserRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Email]
        #[UniqueEmail]
        public string $email,

        #[Assert\NotBlank]
        #[Assert\Length(min: 2, max: 100)]
        public string $name,
    ) {}
}
```

## Template — Class-level constraint (cross-field)

```php
<?php

declare(strict_types=1);

namespace Validator\Constraint;

use Symfony\Component\Validator\Constraint;

#[\Attribute(\Attribute::TARGET_CLASS)]
final class EndDateAfterStartDate extends Constraint
{
    public string $message = 'End date must be after start date.';

    public function getTargets(): string|array
    {
        return self::CLASS_CONSTRAINT;
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Validator;

use Symfony\Component\Validator\Constraint;
use Symfony\Component\Validator\ConstraintValidator;
use Symfony\Component\Validator\Exception\UnexpectedTypeException;

final class EndDateAfterStartDateValidator extends ConstraintValidator
{
    public function validate(mixed $value, Constraint $constraint): void
    {
        if (!$constraint instanceof EndDateAfterStartDate) {
            throw new UnexpectedTypeException($constraint, EndDateAfterStartDate::class);
        }

        if (!is_object($value) || !property_exists($value, 'startDate') || !property_exists($value, 'endDate')) {
            return;
        }

        if ($value->startDate instanceof \DateTimeInterface && $value->endDate instanceof \DateTimeInterface) {
            if ($value->endDate <= $value->startDate) {
                $this->context->buildViolation($constraint->message)
                    ->atPath('endDate')
                    ->addViolation();
            }
        }
    }
}
```

```php
#[EndDateAfterStartDate]
final class BookingRequest
{
    public function __construct(
        public \DateTimeImmutable $startDate,
        public \DateTimeImmutable $endDate,
    ) {}
}
```

## When to keep validation in the domain instead

Some rules belong in the entity or a Specification, not in a Symfony Constraint. Guidelines:

- **Symfony Constraint**: structural / format / repository-check rules at the request boundary.
- **Domain Specification / entity invariant**: business rules — "an Order with no lines cannot be confirmed", "a Customer in arrears cannot place an Order". These should fail in the domain even if HTTP validation is bypassed.

A common pattern: keep both — the constraint provides early HTTP feedback (400 with field errors); the entity enforces the invariant unconditionally (throws a Domain Exception).

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Business invariant only in a Constraint | Bypassed if input enters via CLI / async / direct repo write | Also enforce in the entity |
| Validator without `UnexpectedTypeException` checks | Confusing errors when used on the wrong target | Always validate `$constraint` and `$value` types |
| Validator that throws instead of adding a violation | Caller can't accumulate validation errors | Add violation; throw only on type misuse |
| Validator querying remote services for every field | Slow request validation | Move heavy checks behind a single domain-level validator |
| Constraint with hard-coded message in English | Hard to localize | Use translation domains; pass message via constraint property |
| Per-violation regex inside the validator | Hides intent | Extract to a Value Object or helper class |
