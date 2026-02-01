# Bus Patterns

Detailed patterns for Command Bus and Query Bus implementation in PHP.

## Bus Definition

### What is a Message Bus?

A Message Bus routes messages (Commands/Queries) to their handlers, providing decoupling and middleware support.

### Bus Types

| Bus | Purpose | Returns | Handlers |
|-----|---------|---------|----------|
| **CommandBus** | Dispatch commands | void or ID | One per command |
| **QueryBus** | Dispatch queries | Data | One per query |
| **EventBus** | Dispatch events | void | Zero or more per event |

## PHP 8.5 Implementation

### Command Bus Interface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Bus;

interface CommandBusInterface
{
    /**
     * @template T
     * @param object $command
     * @return T|void
     */
    public function dispatch(object $command): mixed;
}
```

### Query Bus Interface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Bus;

interface QueryBusInterface
{
    /**
     * @template T
     * @param object $query
     * @return T
     */
    public function dispatch(object $query): mixed;
}
```

### Simple In-Memory Command Bus

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus;

use Application\Shared\Bus\CommandBusInterface;
use Psr\Container\ContainerInterface;

final readonly class SimpleCommandBus implements CommandBusInterface
{
    public function __construct(
        private ContainerInterface $container,
        /** @var array<class-string, class-string> */
        private array $handlers = []
    ) {}

    public function dispatch(object $command): mixed
    {
        $commandClass = $command::class;

        if (!isset($this->handlers[$commandClass])) {
            throw new HandlerNotFoundException($commandClass);
        }

        $handler = $this->container->get($this->handlers[$commandClass]);

        return $handler($command);
    }
}
```

### Simple In-Memory Query Bus

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus;

use Application\Shared\Bus\QueryBusInterface;
use Psr\Container\ContainerInterface;

final readonly class SimpleQueryBus implements QueryBusInterface
{
    public function __construct(
        private ContainerInterface $container,
        /** @var array<class-string, class-string> */
        private array $handlers = []
    ) {}

    public function dispatch(object $query): mixed
    {
        $queryClass = $query::class;

        if (!isset($this->handlers[$queryClass])) {
            throw new HandlerNotFoundException($queryClass);
        }

        $handler = $this->container->get($this->handlers[$queryClass]);

        return $handler($query);
    }
}
```

## Middleware Pattern

### Middleware Interface

```php
<?php

declare(strict_types=1);

namespace Application\Shared\Bus;

interface MiddlewareInterface
{
    public function handle(object $message, callable $next): mixed;
}
```

### Command Bus with Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus;

final class MiddlewareCommandBus implements CommandBusInterface
{
    /** @var array<MiddlewareInterface> */
    private array $middlewares = [];

    public function __construct(
        private readonly ContainerInterface $container,
        private readonly array $handlers = []
    ) {}

    public function addMiddleware(MiddlewareInterface $middleware): void
    {
        $this->middlewares[] = $middleware;
    }

    public function dispatch(object $command): mixed
    {
        $handler = $this->resolveHandler($command);

        $chain = array_reduce(
            array_reverse($this->middlewares),
            fn (callable $next, MiddlewareInterface $middleware) =>
                fn (object $message) => $middleware->handle($message, $next),
            fn (object $message) => $handler($message)
        );

        return $chain($command);
    }

    private function resolveHandler(object $command): callable
    {
        $commandClass = $command::class;

        if (!isset($this->handlers[$commandClass])) {
            throw new HandlerNotFoundException($commandClass);
        }

        return $this->container->get($this->handlers[$commandClass]);
    }
}
```

## Common Middleware Implementations

### Transaction Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus\Middleware;

final readonly class TransactionMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TransactionManagerInterface $transactionManager
    ) {}

    public function handle(object $message, callable $next): mixed
    {
        return $this->transactionManager->transactional(
            fn () => $next($message)
        );
    }
}
```

### Logging Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus\Middleware;

use Psr\Log\LoggerInterface;

final readonly class LoggingMiddleware implements MiddlewareInterface
{
    public function __construct(
        private LoggerInterface $logger
    ) {}

    public function handle(object $message, callable $next): mixed
    {
        $messageClass = $message::class;

        $this->logger->info('Handling message', [
            'message' => $messageClass,
            'timestamp' => (new \DateTimeImmutable())->format('c'),
        ]);

        $start = microtime(true);

        try {
            $result = $next($message);

            $this->logger->info('Message handled successfully', [
                'message' => $messageClass,
                'duration_ms' => (microtime(true) - $start) * 1000,
            ]);

            return $result;
        } catch (\Throwable $e) {
            $this->logger->error('Message handling failed', [
                'message' => $messageClass,
                'exception' => $e::class,
                'error' => $e->getMessage(),
                'duration_ms' => (microtime(true) - $start) * 1000,
            ]);

            throw $e;
        }
    }
}
```

### Validation Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus\Middleware;

use Symfony\Component\Validator\Validator\ValidatorInterface;

final readonly class ValidationMiddleware implements MiddlewareInterface
{
    public function __construct(
        private ValidatorInterface $validator
    ) {}

    public function handle(object $message, callable $next): mixed
    {
        $violations = $this->validator->validate($message);

        if (count($violations) > 0) {
            throw new ValidationException($violations);
        }

        return $next($message);
    }
}
```

### Authorization Middleware

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus\Middleware;

final readonly class AuthorizationMiddleware implements MiddlewareInterface
{
    public function __construct(
        private AuthorizationCheckerInterface $authChecker,
        private SecurityContextInterface $securityContext
    ) {}

    public function handle(object $message, callable $next): mixed
    {
        if ($message instanceof AuthorizableCommandInterface) {
            $user = $this->securityContext->getCurrentUser();

            if (!$this->authChecker->isGranted($message->getRequiredPermission(), $user)) {
                throw new AccessDeniedException();
            }
        }

        return $next($message);
    }
}
```

## Symfony Messenger Integration

### Configuration

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        buses:
            command.bus:
                middleware:
                    - doctrine_transaction
                    - validation
            query.bus:
                middleware:
                    - validation

        transports:
            async:
                dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
                options:
                    queue_name: commands

        routing:
            'App\Application\*\Command\*Command': async
```

### Typed Bus Services

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Bus;

use Symfony\Component\Messenger\MessageBusInterface;
use Symfony\Component\Messenger\Stamp\HandledStamp;

final readonly class SymfonyCommandBus implements CommandBusInterface
{
    public function __construct(
        private MessageBusInterface $commandBus
    ) {}

    public function dispatch(object $command): mixed
    {
        $envelope = $this->commandBus->dispatch($command);

        $handledStamp = $envelope->last(HandledStamp::class);

        return $handledStamp?->getResult();
    }
}

final readonly class SymfonyQueryBus implements QueryBusInterface
{
    public function __construct(
        private MessageBusInterface $queryBus
    ) {}

    public function dispatch(object $query): mixed
    {
        $envelope = $this->queryBus->dispatch($query);

        $handledStamp = $envelope->last(HandledStamp::class);

        if ($handledStamp === null) {
            throw new QueryNotHandledException($query::class);
        }

        return $handledStamp->getResult();
    }
}
```

## Bus Usage in Application

### Controller Example

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Shared\Bus\CommandBusInterface;
use Application\Shared\Bus\QueryBusInterface;
use Application\Order\Command\CreateOrderCommand;
use Application\Order\Query\GetOrderDetailsQuery;

final readonly class OrderController
{
    public function __construct(
        private CommandBusInterface $commandBus,
        private QueryBusInterface $queryBus
    ) {}

    public function create(Request $request): JsonResponse
    {
        $command = new CreateOrderCommand(
            customerId: new CustomerId($request->get('customer_id')),
            lines: $request->get('lines')
        );

        $orderId = $this->commandBus->dispatch($command);

        return new JsonResponse(['order_id' => $orderId->value], 201);
    }

    public function show(string $id): JsonResponse
    {
        $query = new GetOrderDetailsQuery(
            orderId: new OrderId($id)
        );

        $order = $this->queryBus->dispatch($query);

        if ($order === null) {
            throw new NotFoundHttpException();
        }

        return new JsonResponse($order);
    }
}
```

## Anti-Patterns

### Mixed Bus

```php
// BAD - Single bus for commands and queries
final readonly class UnifiedBus
{
    public function dispatch(object $message): mixed
    {
        // Cannot enforce command/query separation
        return $this->handlers[$message::class]($message);
    }
}

// GOOD - Separate buses with different behaviors
final readonly class OrderController
{
    public function __construct(
        private CommandBusInterface $commandBus,  // Separate
        private QueryBusInterface $queryBus       // Separate
    ) {}
}
```

### Bus in Domain

```php
// BAD - Domain depends on bus
namespace Domain\Order\Entity;

class Order
{
    public function __construct(
        private CommandBusInterface $bus  // BAD: Domain->Application dependency
    ) {}

    public function confirm(): void
    {
        $this->bus->dispatch(new NotifyCustomerCommand(...));  // BAD
    }
}

// GOOD - Domain raises events, Application handles them
namespace Domain\Order\Entity;

class Order
{
    private array $events = [];

    public function confirm(): void
    {
        // Domain logic
        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id);
    }

    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];
        return $events;
    }
}
```

## Detection Patterns

```bash
# Good - Bus interfaces exist
Glob: **/Bus/*Interface.php
Grep: "interface (Command|Query)BusInterface" --glob "**/*.php"

# Good - Separate buses
Grep: "CommandBusInterface|QueryBusInterface" --glob "**/Controller/**/*.php"

# Warning - Unified bus
Grep: "MessageBusInterface \$bus" --glob "**/Controller/**/*.php"

# Bad - Bus in domain
Grep: "CommandBusInterface|QueryBusInterface|MessageBusInterface" --glob "**/Domain/**/*.php"

# Good - Middleware exists
Glob: **/Middleware/**/*Middleware.php
```

## Bus Configuration Summary

### Command Bus Middleware Stack

1. **LoggingMiddleware** — Log all commands
2. **ValidationMiddleware** — Validate command structure
3. **AuthorizationMiddleware** — Check permissions
4. **TransactionMiddleware** — Wrap in transaction

### Query Bus Middleware Stack

1. **LoggingMiddleware** — Log all queries
2. **ValidationMiddleware** — Validate query structure
3. **CachingMiddleware** — Cache query results (optional)

Note: Query bus should NOT have transaction middleware (queries don't modify state).
