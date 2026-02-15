# PSR Compatibility and Relationships

## PSR Dependency Graph

```
                    PSR-1 (Basic Coding)
                         │
                         ▼
                    PSR-12 (Extended Style)


                    PSR-4 (Autoloading)
                    [Independent]


                    PSR-3 (Logging)
                    [Independent]


    PSR-7 (HTTP Message) ◄──────┬──────────────┐
           │                    │              │
           ▼                    │              │
    PSR-15 (Handlers)           │              │
           │                    │              │
           ▼                    ▼              ▼
    PSR-17 (Factories)    PSR-18 (Client)   PSR-13 (Links)


    PSR-6 (Cache Pool)
           │
           ▼
    PSR-16 (Simple Cache) [Simplified interface]


                    PSR-11 (Container)
                    [Independent]


                    PSR-14 (Events)
                    [Independent]


                    PSR-20 (Clock)
                    [Independent]
```

## Direct Dependencies

| PSR | Depends On |
|-----|------------|
| PSR-1 | None |
| PSR-3 | None |
| PSR-4 | None |
| PSR-6 | None |
| PSR-7 | None |
| PSR-11 | None |
| PSR-12 | PSR-1 |
| PSR-13 | None |
| PSR-14 | None |
| PSR-15 | PSR-7 |
| PSR-16 | None |
| PSR-17 | PSR-7 |
| PSR-18 | PSR-7 |
| PSR-20 | None |

## Complementary PSRs

### HTTP Stack
PSR-7 + PSR-15 + PSR-17 + PSR-18

```php
<?php

declare(strict_types=1);

use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Client\ClientInterface;

// PSR-17: Create request
final readonly class ApiClient
{
    public function __construct(
        private ClientInterface $httpClient,              // PSR-18
        private ResponseFactoryInterface $responseFactory, // PSR-17
    ) {
    }

    public function call(RequestInterface $request): ResponseInterface  // PSR-7
    {
        return $this->httpClient->sendRequest($request);
    }
}

// PSR-15: Middleware using PSR-7
final readonly class LoggingMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,  // PSR-7
        RequestHandlerInterface $handler  // PSR-15
    ): ResponseInterface {                // PSR-7
        // Log and delegate
        return $handler->handle($request);
    }
}
```

### Caching Stack
PSR-6 (or PSR-16) + PSR-3

```php
<?php

declare(strict_types=1);

use Psr\SimpleCache\CacheInterface;
use Psr\Log\LoggerInterface;

final readonly class CachedService
{
    public function __construct(
        private CacheInterface $cache,   // PSR-16
        private LoggerInterface $logger, // PSR-3
    ) {
    }

    public function getData(string $key): mixed
    {
        if ($this->cache->has($key)) {
            $this->logger->debug('Cache hit', ['key' => $key]);
            return $this->cache->get($key);
        }

        $this->logger->debug('Cache miss', ['key' => $key]);
        $data = $this->fetchData($key);
        $this->cache->set($key, $data, 3600);

        return $data;
    }
}
```

### Event-Driven Stack
PSR-14 + PSR-3 + PSR-11

```php
<?php

declare(strict_types=1);

use Psr\EventDispatcher\EventDispatcherInterface;
use Psr\Log\LoggerInterface;
use Psr\Container\ContainerInterface;

final readonly class EventDrivenService
{
    public function __construct(
        private EventDispatcherInterface $dispatcher, // PSR-14
        private LoggerInterface $logger,              // PSR-3
    ) {
    }

    public function performAction(): void
    {
        $this->logger->info('Action starting');

        $event = new ActionPerformed();
        $this->dispatcher->dispatch($event);

        $this->logger->info('Action completed');
    }
}

// Container-aware listener provider
final readonly class ContainerListenerProvider implements ListenerProviderInterface
{
    public function __construct(
        private ContainerInterface $container,  // PSR-11
    ) {
    }

    public function getListenersForEvent(object $event): iterable
    {
        // Resolve listeners from container
        return $this->container->get(ListenerRegistry::class)
            ->getListeners($event::class);
    }
}
```

## Framework Integration

### Symfony

| PSR | Symfony Package |
|-----|-----------------|
| PSR-3 | `symfony/monolog-bundle` |
| PSR-4 | Composer autoload |
| PSR-6 | `symfony/cache` |
| PSR-7 | `symfony/psr-http-message-bridge` |
| PSR-11 | `symfony/dependency-injection` |
| PSR-14 | `symfony/event-dispatcher` |
| PSR-15 | `symfony/http-kernel` (adapted) |
| PSR-16 | `symfony/cache` |
| PSR-17 | `nyholm/psr7` |
| PSR-18 | `symfony/http-client` |
| PSR-20 | `symfony/clock` |

### Laravel

| PSR | Laravel Package |
|-----|-----------------|
| PSR-3 | `illuminate/log` |
| PSR-4 | Composer autoload |
| PSR-6 | `illuminate/cache` (adapted) |
| PSR-7 | `laravel/lumen-framework` |
| PSR-11 | `illuminate/container` |
| PSR-14 | `illuminate/events` (adapted) |
| PSR-15 | Native middleware (adapted) |
| PSR-16 | `illuminate/cache` |
| PSR-17 | Third-party |
| PSR-18 | `illuminate/http` |
| PSR-20 | Third-party |

## Version Compatibility

### PHP Version Requirements

| PSR Package | PHP Version |
|-------------|-------------|
| `psr/log` 3.x | PHP 8.0+ |
| `psr/cache` 3.x | PHP 8.0+ |
| `psr/http-message` 2.x | PHP 8.0+ |
| `psr/http-factory` 1.x | PHP 7.0+ |
| `psr/http-client` 1.x | PHP 7.0+ |
| `psr/container` 2.x | PHP 8.0+ |
| `psr/event-dispatcher` 1.x | PHP 7.2+ |
| `psr/link` 2.x | PHP 8.0+ |
| `psr/simple-cache` 3.x | PHP 8.0+ |
| `psr/clock` 1.x | PHP 8.0+ |

### Recommended Versions for PHP 8.4+

```json
{
    "require": {
        "php": "^8.4",
        "psr/log": "^3.0",
        "psr/cache": "^3.0",
        "psr/http-message": "^2.0",
        "psr/http-factory": "^1.1",
        "psr/http-client": "^1.0",
        "psr/http-server-handler": "^1.0",
        "psr/http-server-middleware": "^1.0",
        "psr/container": "^2.0",
        "psr/event-dispatcher": "^1.0",
        "psr/link": "^2.0",
        "psr/simple-cache": "^3.0",
        "psr/clock": "^1.0"
    }
}
```

## Migration Paths

### PSR-0 to PSR-4

PSR-0 is deprecated. Migrate to PSR-4:

1. Update `composer.json` from `psr-0` to `psr-4`
2. Remove underscore-to-directory conversion
3. Flatten directory structure if needed
4. Run `composer dump-autoload`

### PSR-6 to PSR-16

Use bridge when both needed:

```php
<?php

use Psr\Cache\CacheItemPoolInterface;
use Psr\SimpleCache\CacheInterface;
use Symfony\Component\Cache\Psr16Cache;

// Convert PSR-6 pool to PSR-16 interface
$psr6Pool = new ArrayAdapter();
$psr16Cache = new Psr16Cache($psr6Pool);
```

## Conflict Resolution

### Multiple Logger Implementations

```php
<?php

// Use PSR-11 container to resolve
$container->set(LoggerInterface::class, function () {
    // Choose one implementation
    return new MonologLogger('app');
});
```

### Multiple HTTP Message Implementations

```php
<?php

// Standardize on one implementation via PSR-17 factories
$container->set(ResponseFactoryInterface::class, function () {
    return new NyholmResponseFactory();
});
```
