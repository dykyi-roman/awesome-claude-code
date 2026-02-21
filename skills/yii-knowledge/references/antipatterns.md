# Yii Antipatterns

Common antipatterns in Yii3 projects with detection patterns and fixes.

## Critical Violations

### 1. Yii2 Patterns in Yii3 Codebase

**Description:** Using Yii2 global state, helpers, and patterns in a Yii3 project.

**Why Critical:** Yii3 is a complete rewrite. Yii2 patterns break PSR compliance, DI, and testability.

**Detection:**
```bash
Grep: "Yii::\\\$app" --glob "**/*.php"
Grep: "use yii\\\\base\\\\|use yii\\\\db\\\\|use yii\\\\web\\\\" --glob "**/*.php"
Grep: "Yii::getLogger\|Yii::warning\|Yii::info" --glob "**/*.php"
Grep: "Yii::createObject" --glob "**/*.php"
Grep: "extends \\\\yii\\\\base\\\\Component" --glob "**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Controller;

use Yii;  // Yii2 global!

final class OrderController
{
    public function actionCreate(): string
    {
        $db = Yii::$app->db;                    // Yii2 service locator
        $cache = Yii::$app->cache;              // Yii2 global state
        $user = Yii::$app->user->identity;      // Yii2 user component
        Yii::info('Order created', 'orders');    // Yii2 logging

        $order = Yii::createObject(Order::class); // Yii2 factory

        return $this->render('create', ['order' => $order]);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\UseCase\CreateOrderUseCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Log\LoggerInterface;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,   // Yii3 DI injection
        private LoggerInterface $logger,           // PSR-3 logger
        private DataResponseFactoryInterface $responseFactory,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $this->logger->info('Creating order');

        $result = $this->createOrder->execute(/* ... */);

        return $this->responseFactory->createResponse($result->toArray(), 201);
    }
}
```

### 2. ActiveRecord in Domain Layer

**Description:** Domain entities extend ActiveRecord or use persistence methods.

**Why Critical:** Domain layer becomes coupled to database, untestable, violates DDD.

**Detection:**
```bash
Grep: "extends ActiveRecord" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\\\ActiveRecord" --glob "**/Domain/**/*.php"
Grep: "->save\(\)|->delete\(\)|->insert\(\)" --glob "**/Domain/**/*.php"
Grep: "ActiveQuery" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Yiisoft\ActiveRecord\ActiveRecord;

final class Order extends ActiveRecord  // CRITICAL: AR in Domain
{
    public function tableName(): string
    {
        return 'orders';
    }

    public function confirm(): void
    {
        $this->status = 'confirmed';
        $this->save();  // CRITICAL: Persistence in Domain
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Domain\Order\Entity;

use Domain\Order\ValueObject\OrderId;
use Domain\Order\ValueObject\OrderStatus;

final class Order  // Pure domain, no framework
{
    public function __construct(
        private readonly OrderId $id,
        private OrderStatus $status,
    ) {}

    public function confirm(): void
    {
        if ($this->status !== OrderStatus::Draft) {
            throw new CannotConfirmOrderException($this->id);
        }
        $this->status = OrderStatus::Confirmed;
    }
}
```

### 3. Fat Controllers / Actions

**Description:** Action classes contain business logic, validation, persistence, and formatting.

**Why Critical:** Logic scattered, untestable, not reusable.

**Detection:**
```bash
Grep: "->save\(|->delete\(|->insert\(" --glob "**/Presentation/**/*.php"
Grep: "if \(.*->status|switch \(" --glob "**/Presentation/**/*Action.php"
Grep: "new Query\|ActiveQuery" --glob "**/Presentation/**/*.php"
Grep: "foreach.*calculate\|array_reduce" --glob "**/Presentation/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderAction
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = $request->getParsedBody();

        // VIOLATION: Validation in action
        if (empty($body['customer_id'])) {
            throw new \InvalidArgumentException('Customer ID required');
        }

        // VIOLATION: Business logic in action
        $customer = $this->customerQuery->where(['id' => $body['customer_id']])->one();
        if ($customer->getAttribute('status') === 'suspended') {
            throw new \RuntimeException('Customer suspended');
        }

        // VIOLATION: Persistence in action
        $order = new OrderActiveRecord();
        $order->setAttribute('customer_id', $body['customer_id']);
        $order->setAttribute('status', 'draft');

        $total = 0;
        foreach ($body['lines'] as $line) {
            $product = $this->productQuery->where(['id' => $line['product_id']])->one();
            $total += $product->getAttribute('price') * $line['quantity'];
        }

        $order->setAttribute('total_cents', $total);
        $order->save();

        // 50+ more lines of mixed concerns...
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\UseCase\CreateOrderUseCase;
use Application\Order\DTO\CreateOrderDTO;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
        private DataResponseFactoryInterface $responseFactory,
        private OrderRequestValidator $validator,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = $request->getParsedBody();
        $violations = $this->validator->validate($body);

        if ($violations->count() > 0) {
            return $this->responseFactory->createResponse($violations->toArray(), 422);
        }

        $result = $this->createOrder->execute(CreateOrderDTO::fromArray($body));

        return $this->responseFactory->createResponse($result->toArray(), 201);
    }
}
```

## Warnings

### 4. Service Locator Usage

**Description:** Using `$container->get()` or `Yii::$app->` instead of constructor injection.

**Why Bad:** Hidden dependencies, harder to test, violates Dependency Inversion.

**Detection:**
```bash
Grep: "\\\$container->get\(" --glob "**/Application/**/*.php"
Grep: "\\\$container->get\(" --glob "**/Domain/**/*.php"
Grep: "ContainerInterface" --glob "**/Application/**/*.php"
Grep: "ContainerInterface" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Psr\Container\ContainerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private ContainerInterface $container,  // Service Locator!
    ) {}

    public function execute(CreateOrderDTO $dto): OrderResultDTO
    {
        $repository = $this->container->get(OrderRepositoryInterface::class);
        $events = $this->container->get(EventDispatcherInterface::class);
        // Hidden dependencies...
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Domain\Order\Repository\OrderRepositoryInterface;
use Psr\EventDispatcher\EventDispatcherInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(CreateOrderDTO $dto): OrderResultDTO
    {
        // Dependencies are explicit and testable
    }
}
```

### 5. Tight Coupling to Framework Components

**Description:** Application/Domain classes directly use Yii-specific types instead of PSR interfaces.

**Why Bad:** Cannot switch frameworks, harder to test, breaks portability.

**Detection:**
```bash
Grep: "use Yiisoft\\\\" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\\\" --glob "**/Application/**/*.php"
Grep: "Yiisoft\\\\Cache\\\\|Yiisoft\\\\Log\\\\|Yiisoft\\\\Db\\\\" --glob "**/Application/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Yiisoft\Cache\CacheInterface as YiiCache;       // Yii-specific
use Yiisoft\Log\Logger as YiiLogger;                 // Yii-specific
use Yiisoft\Db\Connection\ConnectionInterface;       // Yii-specific DB

final readonly class GetOrderUseCase
{
    public function __construct(
        private YiiCache $cache,
        private YiiLogger $logger,
        private ConnectionInterface $db,
    ) {}
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Psr\SimpleCache\CacheInterface;     // PSR-16
use Psr\Log\LoggerInterface;            // PSR-3
use Domain\Order\Repository\OrderRepositoryInterface;  // Domain interface

final readonly class GetOrderUseCase
{
    public function __construct(
        private CacheInterface $cache,
        private LoggerInterface $logger,
        private OrderRepositoryInterface $orders,
    ) {}
}
```

### 6. Missing Input Validation

**Description:** Actions accept raw input without validation before passing to use cases.

**Why Bad:** Invalid data reaches domain, causing unclear exceptions.

**Detection:**
```bash
Grep: "getParsedBody\(\)" --glob "**/Presentation/**/*Action.php" -A 5
# Check if followed by validation or direct usage

Grep: "CreateOrderDTO::fromArray\(\\\$request" --glob "**/Presentation/**/*.php"
# DTO created directly from request without validation
```

**Bad:**
```php
public function __invoke(ServerRequestInterface $request): ResponseInterface
{
    $body = $request->getParsedBody();
    // No validation! Directly to use case
    $result = $this->createOrder->execute(CreateOrderDTO::fromArray($body));
    return $this->responseFactory->createResponse($result->toArray());
}
```

**Good:**
```php
public function __invoke(ServerRequestInterface $request): ResponseInterface
{
    $body = $request->getParsedBody();

    $violations = $this->validator->validate($body);
    if ($violations->count() > 0) {
        return $this->responseFactory->createResponse($violations->toArray(), 422);
    }

    $result = $this->createOrder->execute(CreateOrderDTO::fromArray($body));
    return $this->responseFactory->createResponse($result->toArray(), 201);
}
```

### 7. RBAC / Auth Logic in Domain Layer

**Severity:** Warning

**Description:** Domain entities implementing `IdentityInterface`, or RBAC Rules containing business logic instead of delegating to domain Specifications.

**Detection:**
```bash
Grep: "IdentityInterface" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\Auth\\" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\Rbac\\" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\User\\" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Domain\User\Entity;

use Yiisoft\Auth\IdentityInterface; // VIOLATION: Auth in Domain

final readonly class User implements IdentityInterface
{
    public function getId(): string { return $this->id->value; }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Security;

use Yiisoft\Auth\IdentityInterface;
use Domain\User\Entity\User;

final readonly class SecurityIdentityAdapter implements IdentityInterface
{
    public function __construct(private User $user) {}
    public function getId(): string { return $this->user->id()->value; }
}
```

### 8. Missing Queue Resilience

**Severity:** Warning

**Description:** Queue handlers without failure middleware, retry strategy, or dead letter queue handling.

**Detection:**
```bash
# Handlers without failure middleware
Grep: "MessageInterface" --glob "**/Infrastructure/Queue/**/*.php"
Grep: "FailureMiddlewareInterface" --glob "**/*.php" --output_mode count

# Missing retry configuration
Grep: "RetryFailure\|maxRetries\|MAX_RETRIES" --glob "**/*.php" --output_mode count
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Handler;

use Yiisoft\Queue\Message\MessageInterface;

// VIOLATION: No error handling, no retry, no logging
final readonly class ProcessPaymentHandler
{
    public function __invoke(MessageInterface $message): void
    {
        $data = $message->getData();
        // External API call with no resilience
        $this->httpClient->post('/charges', $data);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Infrastructure\Queue\Handler;

use Psr\Log\LoggerInterface;
use Yiisoft\Queue\Message\MessageInterface;

final readonly class ProcessPaymentHandler
{
    public function __construct(
        private ProcessPaymentUseCase $useCase,
        private LoggerInterface $logger,
    ) {}

    public function __invoke(MessageInterface $message): void
    {
        $data = $message->getData();
        $this->logger->info('Processing payment', ['orderId' => $data['orderId']]);

        $this->useCase->execute(new OrderId($data['orderId']));
    }
}

// + Configure RetryFailureMiddleware in failure pipeline
// + Configure DLQ redirect after max retries
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Yii2 patterns in Yii3 | Critical | Architecture | High |
| ActiveRecord in Domain | Critical | Testability | High |
| Fat controllers/actions | Critical | Maintainability | Medium |
| Service Locator usage | Warning | Testability | Medium |
| Tight framework coupling | Warning | Portability | Medium |
| Missing input validation | Warning | Reliability | Low |
| RBAC/Auth in Domain | Warning | Separation of concerns | Medium |
| Missing queue resilience | Warning | Reliability | Low |

## Detection Summary

```bash
# Quick audit for Yii antipatterns

echo "=== Yii2 Remnants ==="
Grep: "Yii::\\\$app\|Yii::getLogger\|Yii::createObject" --glob "**/*.php"
Grep: "use yii\\\\" --glob "**/*.php"

echo "=== ActiveRecord in Domain ==="
Grep: "extends ActiveRecord" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\\\ActiveRecord" --glob "**/Domain/**/*.php"

echo "=== Service Locator ==="
Grep: "ContainerInterface" --glob "**/Application/**/*.php"
Grep: "\\\$container->get\(" --glob "**/*.php"

echo "=== Fat Actions ==="
Grep: "->save\(\)|->delete\(\)" --glob "**/Presentation/**/*.php"
Grep: "ActiveQuery\|new Query" --glob "**/Presentation/**/*.php"

echo "=== Framework in Domain ==="
Grep: "use Yiisoft\\\\" --glob "**/Domain/**/*.php"

echo "=== Framework in Application ==="
Grep: "use Yiisoft\\\\" --glob "**/Application/**/*.php"

echo "=== Auth/RBAC in Domain ==="
Grep: "IdentityInterface" --glob "**/Domain/**/*.php"
Grep: "use Yiisoft\\\\Auth\\\\|use Yiisoft\\\\Rbac\\\\|use Yiisoft\\\\User\\\\" --glob "**/Domain/**/*.php"

echo "=== Queue in Domain ==="
Grep: "QueueInterface\|MessageInterface" --glob "**/Domain/**/*.php"

echo "=== Missing Queue Resilience ==="
Grep: "FailureMiddlewareInterface" --glob "**/*.php" --output_mode count
```
