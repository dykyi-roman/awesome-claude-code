# PSR-11 Container Examples

## DDD Application Bootstrap

```php
<?php

declare(strict_types=1);

use App\Infrastructure\Container\AutowiringContainer;

$container = new AutowiringContainer();

// Configuration
$container->set('config', [
    'db' => [
        'host' => 'localhost',
        'name' => 'app',
    ],
    'log_path' => '/var/log/app.log',
]);

// Infrastructure
$container->factory(
    \PDO::class,
    fn($c) => new \PDO(
        sprintf(
            'mysql:host=%s;dbname=%s',
            $c->get('config')['db']['host'],
            $c->get('config')['db']['name'],
        ),
    ),
);

$container->factory(
    \Psr\Log\LoggerInterface::class,
    fn($c) => new \App\Infrastructure\Logger\FileLogger(
        $c->get('config')['log_path'],
    ),
);

// Repositories
$container->alias(
    \App\Domain\User\Repository\UserRepositoryInterface::class,
    \App\Infrastructure\Persistence\PdoUserRepository::class,
);

// Event Dispatcher
$container->factory(
    \Psr\EventDispatcher\EventDispatcherInterface::class,
    fn($c) => new \App\Infrastructure\Event\EventDispatcher(
        $c->get(\App\Infrastructure\Event\ListenerProvider::class),
    ),
);

// Application runs
$handler = $container->get(\App\Application\User\Handler\CreateUserHandler::class);
```

## Testing with Container

```php
<?php

declare(strict_types=1);

namespace App\Tests;

use App\Infrastructure\Container\Container;
use App\Infrastructure\Logger\NullLogger;
use PHPUnit\Framework\TestCase;
use Psr\Log\LoggerInterface;

abstract class IntegrationTestCase extends TestCase
{
    protected Container $container;

    protected function setUp(): void
    {
        $this->container = new Container();
        $this->configureContainer();
    }

    protected function configureContainer(): void
    {
        // Override with test doubles
        $this->container->set(LoggerInterface::class, new NullLogger());

        // Use in-memory implementations
        $this->container->factory(
            UserRepositoryInterface::class,
            fn() => new InMemoryUserRepository(),
        );
    }
}
```

## Controller Resolution

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use Psr\Container\ContainerInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class ControllerResolver
{
    public function __construct(
        private ContainerInterface $container,
    ) {
    }

    public function resolve(
        string $controllerClass,
        string $method,
        ServerRequestInterface $request,
    ): ResponseInterface {
        $controller = $this->container->get($controllerClass);

        return $controller->$method($request);
    }
}

// Usage in router
$response = $resolver->resolve(
    UserController::class,
    'show',
    $request->withAttribute('id', $routeParams['id']),
);
```

## Middleware Resolution

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use Psr\Container\ContainerInterface;
use Psr\Http\Server\MiddlewareInterface;

final readonly class MiddlewareFactory
{
    public function __construct(
        private ContainerInterface $container,
    ) {
    }

    /** @param array<class-string<MiddlewareInterface>> $middlewareClasses */
    public function createPipeline(array $middlewareClasses): array
    {
        return array_map(
            fn(string $class) => $this->container->get($class),
            $middlewareClasses,
        );
    }
}
```
