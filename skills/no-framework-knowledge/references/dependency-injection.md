# Dependency Injection in No-Framework PHP

PSR-11 containers, PHP-DI, League Container, manual wiring, and compiled containers for production.

## Detection Patterns

```bash
# Check for PSR-11 container usage
Grep: "ContainerInterface|Psr\\\\Container" --glob "**/*.php"

# Check for PHP-DI
Grep: "php-di/php-di|DI\\\\Container|DI\\\\ContainerBuilder" --glob "**/*.php"
Grep: "php-di/php-di" --glob "**/composer.json"

# Check for League Container
Grep: "league/container|League\\\\Container" --glob "**/*.php"
Grep: "league/container" --glob "**/composer.json"

# Detect Service Locator antipattern
Grep: "->get\(.*::class\)" --glob "**/src/Application/**/*.php"
Grep: "ContainerInterface" --glob "**/src/Domain/**/*.php"

# Find manual new instantiations in wrong places
Grep: "new [A-Z].*Repository\(|new [A-Z].*Service\(" --glob "**/src/Presentation/**/*.php"

# Find container configuration
Glob: **/config/container*.php
Glob: **/config/definitions*.php
```

## PHP-DI Container Setup

**Good — explicit definitions with autowiring:**

```php
declare(strict_types=1);

// config/container.php

use DI\ContainerBuilder;
use Psr\Container\ContainerInterface;
use Psr\Log\LoggerInterface;
use Monolog\Logger;
use Monolog\Handler\StreamHandler;

$builder = new ContainerBuilder();

$builder->addDefinitions([
    // Infrastructure bindings
    LoggerInterface::class => static function (): LoggerInterface {
        $logger = new Logger('app');
        $logger->pushHandler(new StreamHandler(
            dirname(__DIR__) . '/var/log/app.log',
            Logger::DEBUG,
        ));

        return $logger;
    },

    // Repository bindings (Domain interface -> Infrastructure implementation)
    Domain\Order\Repository\OrderRepositoryInterface::class => DI\autowire(
        Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository::class,
    ),

    // Event dispatcher
    Domain\Shared\Event\EventDispatcherInterface::class => DI\autowire(
        Infrastructure\EventDispatcher\InMemoryEventDispatcher::class,
    ),

    // Doctrine EntityManager
    Doctrine\ORM\EntityManagerInterface::class => static function (): Doctrine\ORM\EntityManagerInterface {
        return (require dirname(__DIR__) . '/config/doctrine.php')();
    },

    // Application
    Infrastructure\Http\Application::class => static function (ContainerInterface $c): Infrastructure\Http\Application {
        $pipeline = $c->get(Infrastructure\Http\MiddlewarePipeline::class);
        $router = $c->get(Infrastructure\Http\Router::class);

        return new Infrastructure\Http\Application($pipeline, $router);
    },
]);

if ($_ENV['APP_ENV'] === 'prod') {
    $builder->enableCompilation(dirname(__DIR__) . '/var/cache/container');
    $builder->writeProxiesToFile(true, dirname(__DIR__) . '/var/cache/proxies');
}

return $builder->build();
```

## League Container Setup

```php
declare(strict_types=1);

// config/container.php

use League\Container\Container;
use League\Container\ReflectionContainer;
use Psr\Log\LoggerInterface;

$container = new Container();
$container->delegate(new ReflectionContainer(cacheResolutions: true));

// Repository bindings
$container->add(
    Domain\Order\Repository\OrderRepositoryInterface::class,
    Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository::class,
)->addArgument(Doctrine\ORM\EntityManagerInterface::class);

// Logger
$container->addShared(LoggerInterface::class, static function (): LoggerInterface {
    $logger = new Monolog\Logger('app');
    $logger->pushHandler(
        new Monolog\Handler\StreamHandler(dirname(__DIR__) . '/var/log/app.log'),
    );

    return $logger;
});

return $container;
```

## PSR-11 Container Interface

All containers must implement `Psr\Container\ContainerInterface`:

```php
interface ContainerInterface
{
    public function get(string $id): mixed;
    public function has(string $id): bool;
}
```

**Usage in bootstrap only — never in Domain or Application:**

```php
declare(strict_types=1);

// config/middleware.php
// Container usage is acceptable here (bootstrap/wiring layer)

use Psr\Container\ContainerInterface;

return static function (ContainerInterface $container): Infrastructure\Http\MiddlewarePipeline {
    $pipeline = new Infrastructure\Http\MiddlewarePipeline(
        $container->get(Infrastructure\Http\Router::class),
    );

    $pipeline->pipe($container->get(Infrastructure\Http\Middleware\ErrorHandlerMiddleware::class));
    $pipeline->pipe($container->get(Infrastructure\Http\Middleware\CorsMiddleware::class));
    $pipeline->pipe($container->get(Infrastructure\Http\Middleware\JsonBodyParserMiddleware::class));

    return $pipeline;
};
```

## Manual Wiring vs Auto-Wiring

### Manual Wiring

**When to use:** small projects, need full control, no container library.

```php
declare(strict_types=1);

// config/container-manual.php

$pdo = new PDO(
    dsn: sprintf('pgsql:host=%s;port=%s;dbname=%s', $_ENV['DB_HOST'], $_ENV['DB_PORT'], $_ENV['DB_NAME']),
    username: $_ENV['DB_USER'],
    password: $_ENV['DB_PASSWORD'],
    options: [PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION],
);

$orderRepository = new Infrastructure\Persistence\Pdo\Repository\PdoOrderRepository($pdo);
$eventDispatcher = new Infrastructure\EventDispatcher\InMemoryEventDispatcher();

$createOrderUseCase = new Application\Order\UseCase\CreateOrderUseCase(
    orders: $orderRepository,
    events: $eventDispatcher,
);

$createOrderAction = new Presentation\Api\Order\CreateOrderAction(
    createOrder: $createOrderUseCase,
    validator: new Infrastructure\Http\Validation\RequestValidator(),
);
```

### Auto-Wiring (PHP-DI)

**When to use:** medium-to-large projects, reduced boilerplate.

```php
declare(strict_types=1);

use DI\ContainerBuilder;

$builder = new ContainerBuilder();
$builder->useAutowiring(true);

// Only define bindings for interfaces and factories
$builder->addDefinitions([
    Domain\Order\Repository\OrderRepositoryInterface::class => DI\autowire(
        Infrastructure\Persistence\Doctrine\Repository\DoctrineOrderRepository::class,
    ),
]);

return $builder->build();
```

## Compiled Containers for Production

**PHP-DI compilation:**

```php
declare(strict_types=1);

$builder = new DI\ContainerBuilder();
$builder->addDefinitions(require __DIR__ . '/definitions.php');

if ($_ENV['APP_ENV'] === 'prod') {
    $builder->enableCompilation(__DIR__ . '/../var/cache/container');
    $builder->writeProxiesToFile(true, __DIR__ . '/../var/cache/proxies');
}

return $builder->build();
```

**Warm-up script (bin/warm-cache):**

```php
#!/usr/bin/env php
<?php

declare(strict_types=1);

require dirname(__DIR__) . '/vendor/autoload.php';

$dotenv = Dotenv\Dotenv::createImmutable(dirname(__DIR__));
$dotenv->load();

$_ENV['APP_ENV'] = 'prod';
$container = require dirname(__DIR__) . '/config/container.php';

echo "Container compiled successfully.\n";
```

## Service Locator Antipattern

**Bad — container injected into application service:**

```php
declare(strict_types=1);

namespace UseCase;

use Psr\Container\ContainerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private ContainerInterface $container,  // VIOLATION!
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        // Hidden dependencies — impossible to know without reading the body
        $repository = $this->container->get(OrderRepositoryInterface::class);
        $events = $this->container->get(EventDispatcherInterface::class);

        // ...
    }
}
```

**Good — explicit constructor injection:**

```php
declare(strict_types=1);

namespace UseCase;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        // Dependencies are clear and testable
    }
}
```

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| Container in Domain layer | Critical | Architecture purity |
| Service Locator in Application | Critical | Testability, readability |
| No DI container at all (new chains) | Warning | Scalability |
| No compiled container in production | Warning | Performance |
| Auto-wiring without explicit interfaces | Info | Clarity |
| Missing PSR-11 compliance | Info | Interoperability |
