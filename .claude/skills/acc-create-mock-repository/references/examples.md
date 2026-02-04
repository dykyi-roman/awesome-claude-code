# Mock Repository Examples

Complete examples of InMemory repository implementations.

## User Repository

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use App\Domain\User\User;
use App\Domain\User\UserId;
use App\Domain\User\Email;
use App\Domain\User\UserRepositoryInterface;

final class InMemoryUserRepository implements UserRepositoryInterface
{
    /** @var array<string, User> */
    private array $users = [];

    public function save(User $user): void
    {
        $this->users[$user->id()->toString()] = $user;
    }

    public function findById(UserId $id): ?User
    {
        return $this->users[$id->toString()] ?? null;
    }

    public function findByEmail(Email $email): ?User
    {
        foreach ($this->users as $user) {
            if ($user->email()->equals($email)) {
                return $user;
            }
        }
        return null;
    }

    public function delete(User $user): void
    {
        unset($this->users[$user->id()->toString()]);
    }

    public function existsByEmail(Email $email): bool
    {
        return $this->findByEmail($email) !== null;
    }

    /** @return list<User> */
    public function findAll(): array
    {
        return array_values($this->users);
    }

    public function count(): int
    {
        return count($this->users);
    }

    public function clear(): void
    {
        $this->users = [];
    }
}
```

## Order Repository with Queries

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use App\Domain\Order\Order;
use App\Domain\Order\OrderId;
use App\Domain\Order\OrderStatus;
use App\Domain\Order\OrderRepositoryInterface;
use App\Domain\Customer\CustomerId;
use DateTimeImmutable;

final class InMemoryOrderRepository implements OrderRepositoryInterface
{
    /** @var array<string, Order> */
    private array $orders = [];

    public function save(Order $order): void
    {
        $this->orders[$order->id()->toString()] = $order;
    }

    public function findById(OrderId $id): ?Order
    {
        return $this->orders[$id->toString()] ?? null;
    }

    public function delete(Order $order): void
    {
        unset($this->orders[$order->id()->toString()]);
    }

    /** @return list<Order> */
    public function findByCustomer(CustomerId $customerId): array
    {
        return array_values(array_filter(
            $this->orders,
            fn(Order $order) => $order->customerId()->equals($customerId)
        ));
    }

    /** @return list<Order> */
    public function findByStatus(OrderStatus $status): array
    {
        return array_values(array_filter(
            $this->orders,
            fn(Order $order) => $order->status() === $status
        ));
    }

    /** @return list<Order> */
    public function findPending(): array
    {
        return $this->findByStatus(OrderStatus::Pending);
    }

    /** @return list<Order> */
    public function findCreatedBefore(DateTimeImmutable $date): array
    {
        return array_values(array_filter(
            $this->orders,
            fn(Order $order) => $order->createdAt() < $date
        ));
    }

    /** @return list<Order> */
    public function findAll(int $limit = 100, int $offset = 0): array
    {
        return array_slice(array_values($this->orders), $offset, $limit);
    }

    public function count(): int
    {
        return count($this->orders);
    }

    public function countByStatus(OrderStatus $status): int
    {
        return count($this->findByStatus($status));
    }

    public function clear(): void
    {
        $this->orders = [];
    }
}
```

## Repository with Specifications

```php
<?php

declare(strict_types=1);

namespace Tests\Fake;

use App\Domain\Product\Product;
use App\Domain\Product\ProductId;
use App\Domain\Product\ProductRepositoryInterface;
use App\Domain\Shared\Specification\SpecificationInterface;

final class InMemoryProductRepository implements ProductRepositoryInterface
{
    /** @var array<string, Product> */
    private array $products = [];

    public function save(Product $product): void
    {
        $this->products[$product->id()->toString()] = $product;
    }

    public function findById(ProductId $id): ?Product
    {
        return $this->products[$id->toString()] ?? null;
    }

    public function delete(Product $product): void
    {
        unset($this->products[$product->id()->toString()]);
    }

    /** @return list<Product> */
    public function findBySpecification(SpecificationInterface $spec): array
    {
        return array_values(array_filter(
            $this->products,
            fn(Product $product) => $spec->isSatisfiedBy($product)
        ));
    }

    /** @return list<Product> */
    public function findAll(): array
    {
        return array_values($this->products);
    }

    public function clear(): void
    {
        $this->products = [];
    }
}
```
