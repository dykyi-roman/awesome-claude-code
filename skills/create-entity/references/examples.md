# Entity Generator Examples

## Order Entity

**File:** `src/Domain/Order/Entity/Order.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\CustomerId;
use Domain\Order\ValueObject\Money;
use Domain\Order\Enum\OrderStatus;
use Domain\Order\Exception\CannotModifyConfirmedOrderException;
use Domain\Order\Exception\CannotConfirmEmptyOrderException;
use Domain\Order\Exception\InvalidStateTransitionException;

final class Order
{
    private OrderStatus $status;
    /** @var array<OrderLine> */
    private array $lines = [];
    private DateTimeImmutable $createdAt;
    private ?DateTimeImmutable $confirmedAt = null;

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId
    ) {
        $this->status = OrderStatus::Draft;
        $this->createdAt = new DateTimeImmutable();
    }

    public function id(): OrderId
    {
        return $this->id;
    }

    public function customerId(): CustomerId
    {
        return $this->customerId;
    }

    public function status(): OrderStatus
    {
        return $this->status;
    }

    public function addLine(Product $product, int $quantity): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotModifyConfirmedOrderException($this->id);
        }

        $this->lines[] = new OrderLine(
            product: $product,
            quantity: $quantity,
            unitPrice: $product->price()
        );
    }

    public function removeLine(int $index): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotModifyConfirmedOrderException($this->id);
        }

        if (!isset($this->lines[$index])) {
            return;
        }

        unset($this->lines[$index]);
        $this->lines = array_values($this->lines);
    }

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new InvalidStateTransitionException(
                $this->status,
                OrderStatus::Confirmed
            );
        }

        if (empty($this->lines)) {
            throw new CannotConfirmEmptyOrderException($this->id);
        }

        $this->status = OrderStatus::Confirmed;
        $this->confirmedAt = new DateTimeImmutable();
    }

    public function cancel(): void
    {
        if (!$this->status->canBeCancelled()) {
            throw new InvalidStateTransitionException(
                $this->status,
                OrderStatus::Cancelled
            );
        }

        $this->status = OrderStatus::Cancelled;
    }

    public function total(): Money
    {
        return array_reduce(
            $this->lines,
            fn (Money $carry, OrderLine $line) => $carry->add($line->total()),
            Money::zero('USD')
        );
    }

    /**
     * @return array<OrderLine>
     */
    public function lines(): array
    {
        return $this->lines;
    }

    public function lineCount(): int
    {
        return count($this->lines);
    }

    public function isEmpty(): bool
    {
        return empty($this->lines);
    }

    public function createdAt(): DateTimeImmutable
    {
        return $this->createdAt;
    }

    public function confirmedAt(): ?DateTimeImmutable
    {
        return $this->confirmedAt;
    }
}
```

## User Entity

**File:** `src/Domain/User/Entity/User.php`

```php
<?php

declare(strict_types=1);

namespace Domain\User\Entity;

use Domain\User\ValueObject\UserId;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\HashedPassword;
use Domain\User\Enum\UserStatus;
use Domain\User\Exception\UserAlreadyActivatedException;
use Domain\User\Exception\UserDeactivatedException;

final class User
{
    private UserStatus $status;
    private DateTimeImmutable $createdAt;
    private ?DateTimeImmutable $lastLoginAt = null;

    public function __construct(
        private readonly UserId $id,
        private Email $email,
        private HashedPassword $password,
        private string $name
    ) {
        if (empty(trim($name))) {
            throw new InvalidUserNameException();
        }

        $this->status = UserStatus::Pending;
        $this->createdAt = new DateTimeImmutable();
    }

    public function id(): UserId
    {
        return $this->id;
    }

    public function email(): Email
    {
        return $this->email;
    }

    public function name(): string
    {
        return $this->name;
    }

    public function status(): UserStatus
    {
        return $this->status;
    }

    public function activate(): void
    {
        if ($this->status === UserStatus::Active) {
            throw new UserAlreadyActivatedException($this->id);
        }

        $this->status = UserStatus::Active;
    }

    public function deactivate(): void
    {
        $this->status = UserStatus::Deactivated;
    }

    public function changeEmail(Email $newEmail): void
    {
        $this->ensureActive();
        $this->email = $newEmail;
    }

    public function changePassword(HashedPassword $newPassword): void
    {
        $this->ensureActive();
        $this->password = $newPassword;
    }

    public function changeName(string $newName): void
    {
        $this->ensureActive();

        if (empty(trim($newName))) {
            throw new InvalidUserNameException();
        }

        $this->name = $newName;
    }

    public function recordLogin(): void
    {
        $this->ensureActive();
        $this->lastLoginAt = new DateTimeImmutable();
    }

    public function verifyPassword(string $plainPassword, PasswordHasherInterface $hasher): bool
    {
        return $hasher->verify($this->password, $plainPassword);
    }

    public function isActive(): bool
    {
        return $this->status === UserStatus::Active;
    }

    private function ensureActive(): void
    {
        if ($this->status === UserStatus::Deactivated) {
            throw new UserDeactivatedException($this->id);
        }
    }
}
```
