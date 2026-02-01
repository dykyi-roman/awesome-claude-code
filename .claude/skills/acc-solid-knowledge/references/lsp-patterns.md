# Liskov Substitution Principle (LSP) Patterns

## Definition

Objects of a superclass should be replaceable with objects of its subclasses without breaking the application. Subtypes must honor the contract of their base types.

## Formal Rules

1. **Preconditions** cannot be strengthened in a subtype
2. **Postconditions** cannot be weakened in a subtype
3. **Invariants** of the supertype must be preserved
4. **History constraint**: Subtype cannot allow state changes supertype forbids

## Key Indicators

### Violation Signs

| Indicator | Detection | Severity |
|-----------|-----------|----------|
| NotImplementedException | Code search | CRITICAL |
| Empty method overrides | Code search | CRITICAL |
| Type checks in methods | instanceof usage | WARNING |
| Different exception types | Exception analysis | WARNING |
| Null returns where parent doesn't | Return analysis | WARNING |

### Compliance Signs

- All overrides maintain parent contract
- No type-specific handling of subtypes
- Same exceptions (or subtypes)
- Consistent null/non-null returns

## Refactoring Patterns

### Proper Hierarchy Design

```php
<?php

declare(strict_types=1);

// BEFORE: LSP violation - not all birds can fly
abstract class Bird
{
    abstract public function fly(): void;
}

final class Sparrow extends Bird
{
    public function fly(): void
    {
        // Can fly
    }
}

final class Penguin extends Bird
{
    public function fly(): void
    {
        throw new CannotFlyException(); // LSP VIOLATION!
    }
}

// AFTER: Proper abstraction hierarchy
interface Bird
{
    public function move(): void;
    public function eat(Food $food): void;
}

interface FlyingBird extends Bird
{
    public function fly(): void;
}

interface SwimmingBird extends Bird
{
    public function swim(): void;
}

final readonly class Sparrow implements FlyingBird
{
    public function move(): void
    {
        $this->fly();
    }

    public function fly(): void { /* ... */ }
    public function eat(Food $food): void { /* ... */ }
}

final readonly class Penguin implements SwimmingBird
{
    public function move(): void
    {
        $this->swim();
    }

    public function swim(): void { /* ... */ }
    public function eat(Food $food): void { /* ... */ }
}
```

### Composition Over Inheritance

```php
<?php

declare(strict_types=1);

// BEFORE: Inheritance with broken substitution
class Rectangle
{
    protected int $width;
    protected int $height;

    public function setWidth(int $width): void
    {
        $this->width = $width;
    }

    public function setHeight(int $height): void
    {
        $this->height = $height;
    }

    public function area(): int
    {
        return $this->width * $this->height;
    }
}

class Square extends Rectangle
{
    // LSP VIOLATION: Changes expected behavior
    public function setWidth(int $width): void
    {
        $this->width = $width;
        $this->height = $width; // Surprising side effect!
    }

    public function setHeight(int $height): void
    {
        $this->width = $height;
        $this->height = $height;
    }
}

// Client code breaks:
function resizeRectangle(Rectangle $r): void
{
    $r->setWidth(10);
    $r->setHeight(5);
    assert($r->area() === 50); // Fails for Square!
}

// AFTER: Immutable value objects
final readonly class Rectangle
{
    public function __construct(
        public int $width,
        public int $height,
    ) {}

    public function area(): int
    {
        return $this->width * $this->height;
    }

    public function withWidth(int $width): self
    {
        return new self($width, $this->height);
    }

    public function withHeight(int $height): self
    {
        return new self($this->width, $height);
    }
}

final readonly class Square
{
    public function __construct(
        public int $side,
    ) {}

    public function area(): int
    {
        return $this->side * $this->side;
    }

    public function withSide(int $side): self
    {
        return new self($side);
    }
}

// Shared interface if needed
interface Shape
{
    public function area(): int;
}
```

### Precondition Handling

```php
<?php

declare(strict_types=1);

// BEFORE: Strengthened precondition in subtype
class Account
{
    public function withdraw(Money $amount): void
    {
        if ($amount->isNegative()) {
            throw new InvalidArgumentException();
        }
        $this->balance = $this->balance->subtract($amount);
    }
}

class SavingsAccount extends Account
{
    public function withdraw(Money $amount): void
    {
        // LSP VIOLATION: Stronger precondition
        if ($amount->isGreaterThan(Money::fromCents(100000))) {
            throw new WithdrawalLimitExceededException();
        }
        parent::withdraw($amount);
    }
}

// AFTER: Type-appropriate abstraction
interface Withdrawable
{
    public function withdraw(Money $amount): void;
    public function canWithdraw(Money $amount): bool;
}

final readonly class CheckingAccount implements Withdrawable
{
    public function canWithdraw(Money $amount): bool
    {
        return !$amount->isNegative()
            && $this->balance->isGreaterThanOrEqual($amount);
    }

    public function withdraw(Money $amount): void
    {
        if (!$this->canWithdraw($amount)) {
            throw new InsufficientFundsException();
        }
        $this->balance = $this->balance->subtract($amount);
    }
}

final readonly class SavingsAccount implements Withdrawable
{
    private const DAILY_LIMIT = 100000;

    public function canWithdraw(Money $amount): bool
    {
        return !$amount->isNegative()
            && $this->balance->isGreaterThanOrEqual($amount)
            && $amount->cents <= self::DAILY_LIMIT;
    }

    public function withdraw(Money $amount): void
    {
        if (!$this->canWithdraw($amount)) {
            throw new WithdrawalNotAllowedException();
        }
        $this->balance = $this->balance->subtract($amount);
    }
}
```

### Contract Testing

```php
<?php

declare(strict_types=1);

// Contract test ensures LSP compliance
abstract class RepositoryContractTest extends TestCase
{
    abstract protected function createRepository(): Repository;

    public function testFindReturnsNullForNonExistentEntity(): void
    {
        $repository = $this->createRepository();

        $result = $repository->find(new EntityId('non-existent'));

        $this->assertNull($result);
    }

    public function testSaveAndFindReturnsEntity(): void
    {
        $repository = $this->createRepository();
        $entity = $this->createEntity();

        $repository->save($entity);
        $found = $repository->find($entity->id);

        $this->assertEquals($entity, $found);
    }

    public function testDeleteRemovesEntity(): void
    {
        $repository = $this->createRepository();
        $entity = $this->createEntity();
        $repository->save($entity);

        $repository->delete($entity);

        $this->assertNull($repository->find($entity->id));
    }
}

// All implementations must pass contract tests
final class DoctrineUserRepositoryTest extends RepositoryContractTest
{
    protected function createRepository(): Repository
    {
        return new DoctrineUserRepository($this->entityManager);
    }
}

final class InMemoryUserRepositoryTest extends RepositoryContractTest
{
    protected function createRepository(): Repository
    {
        return new InMemoryUserRepository();
    }
}
```

## DDD Application

### Value Object Substitutability

```php
<?php

declare(strict_types=1);

// All value objects of same type are substitutable
final readonly class Email
{
    private function __construct(
        private string $value,
    ) {}

    public static function fromString(string $email): self
    {
        if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidEmailException($email);
        }
        return new self(strtolower($email));
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function value(): string
    {
        return $this->value;
    }
}

// Any Email instance is substitutable for any other
$email1 = Email::fromString('user@example.com');
$email2 = Email::fromString('USER@EXAMPLE.COM');
$email1->equals($email2); // true
```

### Repository Interface Contracts

```php
<?php

declare(strict_types=1);

/**
 * Repository contract - all implementations must honor this
 */
interface UserRepository
{
    /**
     * @return User|null Returns null if not found (never throws)
     */
    public function find(UserId $id): ?User;

    /**
     * @throws UserNotFoundException If user not found
     */
    public function get(UserId $id): User;

    /**
     * Saves new or updates existing user
     */
    public function save(User $user): void;
}

// Implementations must honor the contract
final readonly class DoctrineUserRepository implements UserRepository
{
    public function find(UserId $id): ?User
    {
        // Returns null, never throws - per contract
        return $this->entityManager
            ->getRepository(User::class)
            ->find($id->value);
    }

    public function get(UserId $id): User
    {
        // Throws if not found - per contract
        return $this->find($id)
            ?? throw new UserNotFoundException($id);
    }

    public function save(User $user): void
    {
        $this->entityManager->persist($user);
        $this->entityManager->flush();
    }
}
```

## Metrics

| Metric | Good | Warning | Critical |
|--------|------|---------|----------|
| NotImplementedException | 0 | 0 | >0 |
| Empty overrides | 0 | 0 | >0 |
| Type checks in methods | 0 | 1-2 | >2 |
| Contract test failures | 0 | 0 | >0 |
