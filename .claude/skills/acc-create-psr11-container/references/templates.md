# PSR-11 Container Templates

## Compiled Container

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Container;

use Psr\Container\ContainerInterface;

final class CompiledContainer implements ContainerInterface
{
    private array $services = [];

    public function get(string $id): mixed
    {
        if (isset($this->services[$id])) {
            return $this->services[$id];
        }

        $method = 'create' . str_replace(['\\', '.'], '_', $id);

        if (method_exists($this, $method)) {
            $this->services[$id] = $this->$method();

            return $this->services[$id];
        }

        throw new NotFoundException("Service not found: {$id}");
    }

    public function has(string $id): bool
    {
        if (isset($this->services[$id])) {
            return true;
        }

        $method = 'create' . str_replace(['\\', '.'], '_', $id);

        return method_exists($this, $method);
    }

    // Generated methods
    private function createApp_Domain_User_Repository_UserRepositoryInterface(): object
    {
        return new \App\Infrastructure\Persistence\DoctrineUserRepository(
            $this->get(\Doctrine\ORM\EntityManagerInterface::class),
        );
    }

    private function createPsr_Log_LoggerInterface(): object
    {
        return new \App\Infrastructure\Logger\FileLogger('/var/log/app.log');
    }
}
```

## Lazy Loading Container

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Container;

use Closure;
use Psr\Container\ContainerInterface;

final class LazyContainer implements ContainerInterface
{
    /** @var array<string, object> */
    private array $instances = [];

    /** @var array<string, Closure> */
    private array $factories = [];

    /** @var array<string, bool> */
    private array $shared = [];

    public function get(string $id): mixed
    {
        if (isset($this->instances[$id])) {
            return $this->instances[$id];
        }

        if (!isset($this->factories[$id])) {
            throw new NotFoundException("Service not found: {$id}");
        }

        $instance = ($this->factories[$id])($this);

        if ($this->shared[$id] ?? true) {
            $this->instances[$id] = $instance;
        }

        return $instance;
    }

    public function has(string $id): bool
    {
        return isset($this->instances[$id]) || isset($this->factories[$id]);
    }

    public function register(string $id, Closure $factory, bool $shared = true): void
    {
        $this->factories[$id] = $factory;
        $this->shared[$id] = $shared;
    }
}
```

## Service Provider Pattern

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Container;

interface ServiceProviderInterface
{
    public function register(ContainerInterface $container): void;
}

final readonly class LoggingServiceProvider implements ServiceProviderInterface
{
    public function register(ContainerInterface $container): void
    {
        if (!$container instanceof Container) {
            return;
        }

        $container->factory(
            LoggerInterface::class,
            fn($c) => new FileLogger($c->get('config')['log_path']),
        );
    }
}

final readonly class RepositoryServiceProvider implements ServiceProviderInterface
{
    public function register(ContainerInterface $container): void
    {
        if (!$container instanceof Container) {
            return;
        }

        $container->factory(
            UserRepositoryInterface::class,
            fn($c) => new DoctrineUserRepository($c->get(EntityManagerInterface::class)),
        );
    }
}

// Bootstrap
$container = new Container();
$providers = [
    new LoggingServiceProvider(),
    new RepositoryServiceProvider(),
];

foreach ($providers as $provider) {
    $provider->register($container);
}
```

## Decorator Container

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Container;

use Psr\Container\ContainerInterface;
use Psr\Log\LoggerInterface;

final readonly class LoggingContainer implements ContainerInterface
{
    public function __construct(
        private ContainerInterface $container,
        private LoggerInterface $logger,
    ) {
    }

    public function get(string $id): mixed
    {
        $this->logger->debug('Resolving service', ['id' => $id]);

        $startTime = microtime(true);
        $service = $this->container->get($id);
        $duration = microtime(true) - $startTime;

        $this->logger->debug('Service resolved', [
            'id' => $id,
            'duration_ms' => round($duration * 1000, 2),
        ]);

        return $service;
    }

    public function has(string $id): bool
    {
        return $this->container->has($id);
    }
}
```
