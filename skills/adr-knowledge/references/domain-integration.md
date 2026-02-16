# Domain Integration Reference

How ADR integrates with DDD Domain and Application layers.

## ADR + DDD Layering

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
│  ┌─────────────┐              ┌─────────────────────┐   │
│  │   Action    │─────────────→│     Responder       │   │
│  │  (Input)    │              │     (Output)        │   │
│  └──────┬──────┘              └─────────────────────┘   │
│         │                               ↑                │
│         │ CreateUserCommand             │ CreateUserResult│
│         ↓                               │                │
├─────────────────────────────────────────────────────────┤
│                   APPLICATION LAYER                      │
│  ┌──────────────────────────────────────────────────┐   │
│  │                    UseCase                         │   │
│  │   (CreateUserHandler, GetUserByIdHandler)         │   │
│  └──────────────────────────────────────────────────┘   │
│         │                               ↑                │
│         │ Domain Objects                │ Domain Objects │
│         ↓                               │                │
├─────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                         │
│  ┌────────────┐  ┌────────────┐  ┌─────────────────┐   │
│  │  Entities  │  │   Value    │  │   Repository    │   │
│  │            │  │  Objects   │  │   Interfaces    │   │
│  └────────────┘  └────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## Command/Query Integration

### With CQRS Commands

```php
<?php

declare(strict_types=1);

namespace Application\User\UseCase\CreateUser;

// Command (Application Layer)
final readonly class CreateUserCommand
{
    public function __construct(
        public string $email,
        public string $name,
    ) {
    }
}

// Handler (Application Layer)
final readonly class CreateUserHandler
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private PasswordHasherInterface $passwordHasher,
        private EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function handle(CreateUserCommand $command): CreateUserResult
    {
        try {
            $email = new Email($command->email);
        } catch (InvalidArgumentException $e) {
            return CreateUserResult::failure('invalid_email', $e->getMessage());
        }

        if ($this->userRepository->existsByEmail($email)) {
            return CreateUserResult::failure('email_exists', 'Email already registered');
        }

        $user = new User(
            id: UserId::generate(),
            email: $email,
            name: $command->name,
        );

        $this->userRepository->save($user);
        $this->eventDispatcher->dispatch(new UserCreated($user->id()));

        return CreateUserResult::success($user);
    }
}

// Result (Application Layer)
final readonly class CreateUserResult
{
    private function __construct(
        private bool $success,
        private ?User $user,
        private ?string $failureReason,
        private ?string $errorMessage,
    ) {
    }

    public static function success(User $user): self
    {
        return new self(true, $user, null, null);
    }

    public static function failure(string $reason, string $message): self
    {
        return new self(false, null, $reason, $message);
    }

    public function isSuccess(): bool
    {
        return $this->success;
    }

    public function isFailure(): bool
    {
        return !$this->success;
    }

    public function user(): User
    {
        if ($this->user === null) {
            throw new LogicException('Cannot get user from failed result');
        }
        return $this->user;
    }

    public function userId(): string
    {
        return $this->user()->id()->toString();
    }

    public function email(): string
    {
        return $this->user()->email()->value();
    }

    public function failureReason(): ?string
    {
        return $this->failureReason;
    }

    public function errorMessage(): ?string
    {
        return $this->errorMessage;
    }
}
```

### With CQRS Queries

```php
<?php

declare(strict_types=1);

namespace Application\User\UseCase\GetUserById;

// Query (Application Layer)
final readonly class GetUserByIdQuery
{
    public function __construct(
        public string $userId,
    ) {
    }
}

// Handler (Application Layer)
final readonly class GetUserByIdHandler
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
    ) {
    }

    public function handle(GetUserByIdQuery $query): GetUserByIdResult
    {
        try {
            $userId = new UserId($query->userId);
        } catch (InvalidArgumentException) {
            return GetUserByIdResult::notFound();
        }

        $user = $this->userRepository->findById($userId);

        if ($user === null) {
            return GetUserByIdResult::notFound();
        }

        return GetUserByIdResult::found($user);
    }
}

// Result (Application Layer)
final readonly class GetUserByIdResult
{
    private function __construct(
        private bool $found,
        private ?User $user,
    ) {
    }

    public static function found(User $user): self
    {
        return new self(true, $user);
    }

    public static function notFound(): self
    {
        return new self(false, null);
    }

    public function isFound(): bool
    {
        return $this->found;
    }

    public function isNotFound(): bool
    {
        return !$this->found;
    }

    public function user(): User
    {
        if ($this->user === null) {
            throw new LogicException('Cannot get user from not found result');
        }
        return $this->user;
    }
}
```

## Domain Objects in Results

### Returning Domain Objects

```php
// Result exposes domain object
final readonly class GetUserByIdResult
{
    public function user(): User
    {
        return $this->user;
    }
}

// Responder accesses domain object
final readonly class GetUserByIdResponder
{
    public function respond(GetUserByIdResult $result): ResponseInterface
    {
        $user = $result->user();

        return $this->json([
            'id' => $user->id()->toString(),
            'email' => $user->email()->value(),
            'name' => $user->name(),
        ]);
    }
}
```

### Returning DTOs (Alternative)

```php
// DTO in Application Layer
final readonly class UserDto
{
    public function __construct(
        public string $id,
        public string $email,
        public string $name,
        public string $createdAt,
    ) {
    }

    public static function fromEntity(User $user): self
    {
        return new self(
            id: $user->id()->toString(),
            email: $user->email()->value(),
            name: $user->name(),
            createdAt: $user->createdAt()->format('c'),
        );
    }
}

// Handler returns DTO
final readonly class GetUserByIdHandler
{
    public function handle(GetUserByIdQuery $query): ?UserDto
    {
        $user = $this->userRepository->findById(new UserId($query->userId));

        return $user ? UserDto::fromEntity($user) : null;
    }
}

// Simpler Responder
final readonly class GetUserByIdResponder
{
    public function respond(?UserDto $user): ResponseInterface
    {
        if ($user === null) {
            return $this->notFound();
        }

        return $this->json([
            'id' => $user->id,
            'email' => $user->email,
            'name' => $user->name,
        ]);
    }
}
```

## Transaction Boundaries

Transactions are managed in Application layer, not in Action or Responder:

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase\CreateOrder;

final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository,
        private TransactionManagerInterface $transactionManager,
        private EventDispatcherInterface $eventDispatcher,
    ) {
    }

    public function handle(CreateOrderCommand $command): CreateOrderResult
    {
        return $this->transactionManager->transactional(function () use ($command) {
            $order = new Order(
                id: OrderId::generate(),
                customerId: new CustomerId($command->customerId),
            );

            foreach ($command->items as $item) {
                $order->addLine(
                    productId: new ProductId($item['product_id']),
                    quantity: $item['quantity'],
                );
            }

            $this->orderRepository->save($order);
            $this->eventDispatcher->dispatch(new OrderCreated($order->id()));

            return CreateOrderResult::success($order);
        });
    }
}
```

## Error Handling Flow

```
Action
  │
  │ Parse input
  │
  ↓
Handler (Application Layer)
  │
  │ Validate domain rules
  │ Execute business logic
  │ Return Result (success or failure)
  │
  ↓
Responder
  │
  │ Map Result to HTTP Response
  │ - Success → 2xx
  │ - Domain Error → 4xx
  │ - Not Found → 404
  │
  ↓
HTTP Response
```

## Best Practices

1. **Action → Application**: Use Commands/Queries as DTOs
2. **Application → Domain**: Use Domain objects internally
3. **Application → Presentation**: Use Result objects
4. **Result Objects**: Contain success/failure state and data
5. **No HTTP in Domain**: Domain layer is HTTP-agnostic
6. **Responder Mapping**: Map domain errors to HTTP status codes
