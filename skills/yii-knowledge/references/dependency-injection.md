# Dependency Injection in Yii3

yiisoft/di container, yiisoft/injector, PSR-11 compliance, definition configuration, and service providers.

## yiisoft/di Container

### Core Features

| Feature | Description |
|---------|-------------|
| PSR-11 compliant | `ContainerInterface::get()` and `has()` |
| Auto-wiring | Resolves constructor dependencies automatically |
| Definitions | Array-based configuration for bindings |
| Service providers | Modular registration via `ServiceProviderInterface` |
| Deferred providers | Lazy-load definitions on first use |
| Tags | Group services by tag for batch retrieval |
| Delegates | Hierarchical container composition |

### Container Initialization

```php
<?php

declare(strict_types=1);

use Yiisoft\Di\Container;
use Yiisoft\Di\ContainerConfig;

$config = ContainerConfig::create()
    ->withDefinitions([
        OrderRepositoryInterface::class => ActiveRecordOrderRepository::class,
        PaymentGatewayInterface::class => StripePaymentGateway::class,
    ])
    ->withProviders([
        OrderServiceProvider::class,
        PaymentServiceProvider::class,
    ]);

$container = new Container($config);
```

## Definition Configuration

### Simple Bindings

```php
<?php

declare(strict_types=1);

// config/common/di/order.php

use Domain\Order\Repository\OrderRepositoryInterface;
use Infrastructure\Persistence\ActiveRecord\ActiveRecordOrderRepository;
use Application\Order\UseCase\CreateOrderUseCase;

return [
    // Interface -> Implementation (auto-wired)
    OrderRepositoryInterface::class => ActiveRecordOrderRepository::class,

    // Class with explicit constructor arguments
    CreateOrderUseCase::class => [
        'class' => CreateOrderUseCase::class,
        '__construct()' => [
            'maxOrderLines' => 100,
        ],
    ],
];
```

### Factory Definitions

```php
<?php

declare(strict_types=1);

use Yiisoft\Definitions\Reference;
use Psr\Log\LoggerInterface;

return [
    // Closure factory
    OrderRepositoryInterface::class => static function (
        ConnectionInterface $db,
        LoggerInterface $logger,
    ): OrderRepositoryInterface {
        return new ActiveRecordOrderRepository(
            new ActiveQuery(OrderActiveRecord::class, $db),
            new OrderEntityMapper(),
        );
    },

    // Reference to another service
    'order.repository' => Reference::to(OrderRepositoryInterface::class),

    // Dynamic reference with parameters
    PaymentGatewayInterface::class => [
        'class' => StripePaymentGateway::class,
        '__construct()' => [
            'apiKey' => Reference::to('params.stripe.apiKey'),
        ],
    ],
];
```

### Advanced Definitions

```php
<?php

declare(strict_types=1);

use Yiisoft\Definitions\DynamicReference;
use Yiisoft\Definitions\Reference;

return [
    // Method calls after construction
    LoggerInterface::class => [
        'class' => FileLogger::class,
        'setLevel()' => ['debug'],
        'setPath()' => [Reference::to('params.log.path')],
    ],

    // Tagged services
    'tag@event-listeners' => [
        Reference::to(OrderEventListener::class),
        Reference::to(PaymentEventListener::class),
        Reference::to(NotificationEventListener::class),
    ],

    // Dynamic reference (resolved at call time)
    OrderProcessorInterface::class => DynamicReference::to(
        static fn (ContainerInterface $container) => $container->get(
            match (getenv('ORDER_PROCESSOR')) {
                'async' => AsyncOrderProcessor::class,
                default => SyncOrderProcessor::class,
            }
        ),
    ),
];
```

## yiisoft/injector

### Auto-Injection in Actions

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

// Injector resolves all constructor dependencies automatically
final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,         // Auto-injected
        private DataResponseFactoryInterface $response,  // Auto-injected
        private OrderRequestValidator $validator,        // Auto-injected
    ) {}

    // Method injection also supported via Injector
    public function __invoke(
        ServerRequestInterface $request,  // Injected by middleware
    ): ResponseInterface {
        // ...
    }
}
```

### Manual Injector Usage

```php
<?php

declare(strict_types=1);

use Yiisoft\Injector\Injector;

$injector = new Injector($container);

// Invoke callable with auto-resolved parameters
$result = $injector->invoke([$service, 'process'], [
    'orderId' => new OrderId('abc-123'),  // Explicit parameter
    // Other parameters auto-resolved from container
]);

// Create instance with auto-resolved constructor
$action = $injector->make(CreateOrderAction::class, [
    'maxRetries' => 3,  // Explicit parameter
]);
```

## PSR-11 Compliance

### Interface Usage

```php
<?php

declare(strict_types=1);

namespace Application\Order\UseCase;

use Psr\Container\ContainerInterface;

// BAD: Service Locator pattern — injecting container
final readonly class BadCreateOrderUseCase
{
    public function __construct(
        private ContainerInterface $container,  // ANTIPATTERN!
    ) {}

    public function execute(CreateOrderDTO $dto): OrderResultDTO
    {
        $repository = $this->container->get(OrderRepositoryInterface::class);
        // ...
    }
}

// GOOD: Direct dependency injection
final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,   // Concrete dependency
        private EventDispatcherInterface $events,   // Concrete dependency
    ) {}

    public function execute(CreateOrderDTO $dto): OrderResultDTO
    {
        // Use injected dependencies directly
        $order = Order::create(...);
        $this->orders->save($order);
        $this->events->dispatch(...$order->releaseEvents());

        return OrderResultDTO::fromEntity($order);
    }
}
```

## Service Providers

### Basic Provider

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Provider;

use Yiisoft\Di\ServiceProviderInterface;
use Domain\Order\Repository\OrderRepositoryInterface;
use Infrastructure\Persistence\ActiveRecord\ActiveRecordOrderRepository;
use Application\Order\UseCase\CreateOrderUseCase;

final class OrderServiceProvider implements ServiceProviderInterface
{
    public function getDefinitions(): array
    {
        return [
            OrderRepositoryInterface::class => ActiveRecordOrderRepository::class,
            CreateOrderUseCase::class => CreateOrderUseCase::class,
        ];
    }

    public function getExtensions(): array
    {
        return [];
    }
}
```

### Deferred Provider (Lazy Loading)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Provider;

use Yiisoft\Di\ServiceProviderInterface;

final class PaymentServiceProvider implements ServiceProviderInterface
{
    public function getDefinitions(): array
    {
        return [
            PaymentGatewayInterface::class => static function (
                ConnectionInterface $db,
            ): PaymentGatewayInterface {
                // Only instantiated when PaymentGatewayInterface is first requested
                return new StripePaymentGateway(
                    apiKey: getenv('STRIPE_API_KEY'),
                    db: $db,
                );
            },
        ];
    }

    public function getExtensions(): array
    {
        return [];
    }
}
```

### Provider Registration

```php
<?php

declare(strict_types=1);

// config/common/providers.php

return [
    'providers' => [
        Infrastructure\Provider\OrderServiceProvider::class,
        Infrastructure\Provider\PaymentServiceProvider::class,
        Infrastructure\Provider\NotificationServiceProvider::class,
    ],
];
```

## Detection Patterns

```bash
# Service Locator antipattern
Grep: "ContainerInterface" --glob "**/Application/**/*.php"
Grep: "\$container->get\(" --glob "**/*.php"
Grep: "Yii::\\\$app->|Yii::getContainer" --glob "**/*.php"

# Verify DI definitions exist
Glob: config/common/di/*.php
Glob: config/web/di/*.php

# Find service providers
Grep: "ServiceProviderInterface" --glob "**/*.php"

# Check for proper constructor injection
Grep: "public function __construct" --glob "**/Application/**/*.php"

# New operator in Application layer (missing DI)
Grep: "new [A-Z].*Repository\|new [A-Z].*Gateway\|new [A-Z].*Client" --glob "**/Application/**/*.php"
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Constructor injection | Always prefer over service locator |
| Interface bindings | Bind interfaces, not concrete classes |
| One provider per context | Group related bindings in one provider |
| Config for wiring | All definitions in `config/common/di/` |
| Avoid container injection | Never inject `ContainerInterface` into services |
| Auto-wiring first | Only define explicit bindings when auto-wiring fails |
| Deferred for heavy deps | Use closures for expensive-to-create services |
