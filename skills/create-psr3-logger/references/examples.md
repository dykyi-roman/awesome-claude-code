# PSR-3 Logger Examples

## DDD Integration

### Application Service with Logging

```php
<?php

declare(strict_types=1);

namespace Handler;

use Command\CreateUserCommand;
use Entity\User;
use Event\UserCreated;
use Repository\UserRepositoryInterface;
use Psr\EventDispatcher\EventDispatcherInterface;
use Psr\Log\LoggerInterface;

final readonly class CreateUserHandler
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
        private EventDispatcherInterface $eventDispatcher,
        private LoggerInterface $logger,
    ) {
    }

    public function __invoke(CreateUserCommand $command): void
    {
        $this->logger->info('Creating user', [
            'email' => $command->email,
            'name' => $command->name,
        ]);

        try {
            $user = User::create(
                $command->email,
                $command->name,
            );

            $this->userRepository->save($user);

            $this->logger->info('User created successfully', [
                'user_id' => $user->getId()->toString(),
            ]);

            $this->eventDispatcher->dispatch(new UserCreated($user->getId()));
        } catch (\Throwable $e) {
            $this->logger->error('Failed to create user', [
                'email' => $command->email,
                'error' => $e->getMessage(),
                'trace' => $e->getTraceAsString(),
            ]);

            throw $e;
        }
    }
}
```

### Domain Service with Contextual Logging

```php
<?php

declare(strict_types=1);

namespace Service;

use Entity\Order;
use ValueObject\OrderId;
use Psr\Log\LoggerInterface;

final readonly class OrderProcessingService
{
    public function __construct(
        private LoggerInterface $logger,
    ) {
    }

    public function process(Order $order): void
    {
        $context = [
            'order_id' => $order->getId()->toString(),
            'customer_id' => $order->getCustomerId()->toString(),
            'total' => $order->getTotal()->toString(),
        ];

        $this->logger->info('Processing order', $context);

        foreach ($order->getItems() as $item) {
            $this->logger->debug('Processing order item', [
                ...$context,
                'product_id' => $item->getProductId()->toString(),
                'quantity' => $item->getQuantity(),
            ]);
        }

        $this->logger->info('Order processed successfully', $context);
    }
}
```

## Infrastructure Integration

### HTTP Client with Logging

```php
<?php

declare(strict_types=1);

namespace Http;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Log\LoggerInterface;

final readonly class LoggingHttpClient implements ClientInterface
{
    public function __construct(
        private ClientInterface $client,
        private LoggerInterface $logger,
    ) {
    }

    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        $context = [
            'method' => $request->getMethod(),
            'uri' => (string) $request->getUri(),
        ];

        $this->logger->debug('Sending HTTP request', $context);

        $startTime = microtime(true);

        try {
            $response = $this->client->sendRequest($request);
            $duration = microtime(true) - $startTime;

            $this->logger->info('HTTP request completed', [
                ...$context,
                'status' => $response->getStatusCode(),
                'duration_ms' => round($duration * 1000, 2),
            ]);

            return $response;
        } catch (\Throwable $e) {
            $this->logger->error('HTTP request failed', [
                ...$context,
                'error' => $e->getMessage(),
            ]);

            throw $e;
        }
    }
}
```

### Repository with Logging

```php
<?php

declare(strict_types=1);

namespace Persistence;

use Entity\User;
use Repository\UserRepositoryInterface;
use ValueObject\UserId;
use Psr\Log\LoggerInterface;

final readonly class LoggingUserRepository implements UserRepositoryInterface
{
    public function __construct(
        private UserRepositoryInterface $repository,
        private LoggerInterface $logger,
    ) {
    }

    public function save(User $user): void
    {
        $this->logger->debug('Saving user', [
            'user_id' => $user->getId()->toString(),
        ]);

        $this->repository->save($user);

        $this->logger->info('User saved', [
            'user_id' => $user->getId()->toString(),
        ]);
    }

    public function findById(UserId $id): ?User
    {
        $this->logger->debug('Finding user by ID', [
            'user_id' => $id->toString(),
        ]);

        $user = $this->repository->findById($id);

        if ($user === null) {
            $this->logger->debug('User not found', [
                'user_id' => $id->toString(),
            ]);
        }

        return $user;
    }
}
```

## Testing

### Using ArrayLogger in Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\User;

use Command\CreateUserCommand;
use Handler\CreateUserHandler;
use Logger\ArrayLogger;
use PHPUnit\Framework\TestCase;

final class CreateUserHandlerTest extends TestCase
{
    private ArrayLogger $logger;
    private CreateUserHandler $handler;

    protected function setUp(): void
    {
        $this->logger = new ArrayLogger();
        $this->handler = new CreateUserHandler(
            $this->createMock(UserRepositoryInterface::class),
            $this->createMock(EventDispatcherInterface::class),
            $this->logger,
        );
    }

    public function test_it_logs_user_creation(): void
    {
        $command = new CreateUserCommand('test@example.com', 'John');

        ($this->handler)($command);

        self::assertTrue($this->logger->hasLoggedLevel('info'));
        self::assertTrue($this->logger->hasLoggedMessage('Creating user'));
    }
}
```

## Structured Logging

### With Request ID

```php
<?php

declare(strict_types=1);

namespace Logger;

use Psr\Log\LoggerInterface;
use Stringable;

final class ContextualLogger implements LoggerInterface
{
    public function __construct(
        private readonly LoggerInterface $logger,
        private readonly array $defaultContext = [],
    ) {
    }

    public function withContext(array $context): self
    {
        return new self($this->logger, [...$this->defaultContext, ...$context]);
    }

    public function log(mixed $level, string|Stringable $message, array $context = []): void
    {
        $this->logger->log($level, $message, [...$this->defaultContext, ...$context]);
    }

    // ... implement other methods delegating to log()
}

// Usage
$logger = new ContextualLogger($baseLogger, [
    'request_id' => $requestId,
    'user_id' => $userId,
]);

$logger->info('Processing request');  // Includes request_id and user_id
```
