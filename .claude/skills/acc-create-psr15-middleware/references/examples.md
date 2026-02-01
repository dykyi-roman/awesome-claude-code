# PSR-15 Middleware Examples

## Application Bootstrap

```php
<?php

declare(strict_types=1);

use App\Infrastructure\Http\MiddlewarePipeline;
use App\Infrastructure\Http\Middleware\AuthenticationMiddleware;
use App\Infrastructure\Http\Middleware\CorsMiddleware;
use App\Infrastructure\Http\Middleware\ErrorHandlingMiddleware;
use App\Infrastructure\Http\Middleware\JsonBodyParserMiddleware;
use App\Infrastructure\Http\Middleware\LoggingMiddleware;
use App\Infrastructure\Http\Middleware\RateLimitMiddleware;
use App\Infrastructure\Http\Middleware\RoutingMiddleware;

// Bootstrap
$container = require __DIR__ . '/bootstrap/container.php';

// Build middleware pipeline
$pipeline = (new MiddlewarePipeline(new NotFoundHandler()))
    // Error handling (first - catches all exceptions)
    ->pipe(new ErrorHandlingMiddleware(
        $container->get(LoggerInterface::class),
        debug: getenv('APP_DEBUG') === 'true',
    ))
    // CORS (before authentication)
    ->pipe(new CorsMiddleware(
        allowedOrigins: ['https://example.com'],
    ))
    // Rate limiting
    ->pipe(new RateLimitMiddleware(
        $container->get(CacheInterface::class),
        maxRequests: 100,
    ))
    // Logging
    ->pipe(new LoggingMiddleware(
        $container->get(LoggerInterface::class),
    ))
    // Body parsing
    ->pipe(new JsonBodyParserMiddleware())
    // Routing
    ->pipe(new RoutingMiddleware(
        $container->get(RouterInterface::class),
    ))
    // Authentication (after routing, before dispatch)
    ->pipe(new AuthenticationMiddleware(
        $container->get(TokenValidatorInterface::class),
    ))
    // Controller dispatch
    ->pipe(new DispatcherMiddleware(
        $container,
    ));

// Handle request
$request = ServerRequest::fromGlobals();
$response = $pipeline->handle($request);

// Send response
(new ResponseEmitter())->emit($response);
```

## Controller Dispatcher Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Container\ContainerInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class DispatcherMiddleware implements MiddlewareInterface
{
    public function __construct(
        private ContainerInterface $container,
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $controller = $request->getAttribute('_controller');
        $action = $request->getAttribute('_action', '__invoke');

        if ($controller === null) {
            return $handler->handle($request);
        }

        $instance = $this->container->get($controller);

        return $instance->$action($request);
    }
}
```

## Route-Specific Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final class RouteMiddlewareResolver implements MiddlewareInterface
{
    /** @var array<string, MiddlewareInterface[]> */
    private array $routeMiddleware = [];

    public function addRouteMiddleware(string $routeName, MiddlewareInterface $middleware): void
    {
        $this->routeMiddleware[$routeName][] = $middleware;
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $routeName = $request->getAttribute('_route');

        if ($routeName === null || !isset($this->routeMiddleware[$routeName])) {
            return $handler->handle($request);
        }

        $pipeline = new MiddlewarePipeline($handler);

        foreach ($this->routeMiddleware[$routeName] as $middleware) {
            $pipeline = $pipeline->pipe($middleware);
        }

        return $pipeline->handle($request);
    }
}

// Usage
$resolver = new RouteMiddlewareResolver();
$resolver->addRouteMiddleware('admin.dashboard', new AdminOnlyMiddleware());
$resolver->addRouteMiddleware('api.users.create', new ValidateUserMiddleware());
```

## Testing Middleware

```php
<?php

declare(strict_types=1);

namespace App\Tests\Functional;

use App\Infrastructure\Http\Middleware\AuthenticationMiddleware;
use App\Infrastructure\Http\Middleware\CorsMiddleware;
use App\Infrastructure\Http\MiddlewarePipeline;
use PHPUnit\Framework\TestCase;

final class MiddlewarePipelineTest extends TestCase
{
    public function test_full_pipeline(): void
    {
        $logger = new ArrayLogger();
        $cache = new ArrayCache();

        $pipeline = (new MiddlewarePipeline(new OkHandler()))
            ->pipe(new LoggingMiddleware($logger))
            ->pipe(new CorsMiddleware(['http://localhost:3000']))
            ->pipe(new RateLimitMiddleware($cache, 10, 60));

        $request = (new ServerRequest('GET', '/api/users'))
            ->withHeader('Origin', 'http://localhost:3000');

        $response = $pipeline->handle($request);

        self::assertSame(200, $response->getStatusCode());
        self::assertSame('http://localhost:3000', $response->getHeaderLine('Access-Control-Allow-Origin'));
        self::assertSame('10', $response->getHeaderLine('X-RateLimit-Limit'));
        self::assertTrue($logger->hasLoggedLevel('info'));
    }
}

final class OkHandler implements RequestHandlerInterface
{
    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        return new Response(200);
    }
}
```
