# Routing and HTTP in No-Framework PHP

PSR-7/PSR-15 HTTP handling, routing configuration, middleware pipeline, and input validation.

## Detection Patterns

```bash
# Check for PSR-7 usage
Grep: "ServerRequestInterface|ResponseInterface" --glob "**/*.php"

# Check for PSR-15 middleware
Grep: "MiddlewareInterface|RequestHandlerInterface" --glob "**/*.php"

# Detect raw superglobals (violation)
Grep: "\\\$_GET|\\\$_POST|\\\$_REQUEST|\\\$_SESSION|\\\$_COOKIE" --glob "**/src/**/*.php"

# Detect raw header/echo output (violation)
Grep: "\\bheader\(|^\\s*echo\\b" --glob "**/src/**/*.php"

# Find routing configuration
Grep: "addRoute|->get\(|->post\(|->put\(|->delete\(" --glob "**/config/routes*.php"

# Check for proper middleware pipeline
Grep: "MiddlewarePipeline|pipe\(|middleware" --glob "**/config/middleware*.php"
```

## Router Configuration with FastRoute

**Good — centralized route definitions:**

```php
declare(strict_types=1);

// config/routes.php

use FastRoute\RouteCollector;
use Presentation\Api\Order\CreateOrderAction;
use Presentation\Api\Order\GetOrderAction;
use Presentation\Api\Order\ListOrdersAction;
use Presentation\Api\HealthCheck\HealthCheckAction;

return static function (RouteCollector $r): void {
    $r->addGroup('/api/v1', static function (RouteCollector $r): void {
        $r->get('/health', HealthCheckAction::class);

        $r->addGroup('/orders', static function (RouteCollector $r): void {
            $r->get('', ListOrdersAction::class);
            $r->post('', CreateOrderAction::class);
            $r->get('/{id:[a-f0-9-]+}', GetOrderAction::class);
        });
    });
};
```

**Bad — inline routing in index.php:**

```php
$uri = $_SERVER['REQUEST_URI'];
if ($uri === '/orders') {
    include 'controllers/orders.php';
} elseif (preg_match('#^/orders/(\d+)$#', $uri, $matches)) {
    include 'controllers/order-detail.php';
}
```

## Custom Router with FastRoute and PSR-15

```php
declare(strict_types=1);

namespace Infrastructure\Http;

use FastRoute\Dispatcher;
use FastRoute\RouteCollector;
use Psr\Container\ContainerInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Nyholm\Psr7\Response;

use function FastRoute\simpleDispatcher;

final readonly class Router implements RequestHandlerInterface
{
    private Dispatcher $dispatcher;

    public function __construct(
        private ContainerInterface $container,
        callable $routeDefinition,
    ) {
        $this->dispatcher = simpleDispatcher(
            static fn(RouteCollector $r) => $routeDefinition($r),
        );
    }

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $routeInfo = $this->dispatcher->dispatch(
            $request->getMethod(),
            $request->getUri()->getPath(),
        );

        return match ($routeInfo[0]) {
            Dispatcher::NOT_FOUND => new Response(404, body: '{"error":"Not Found"}'),
            Dispatcher::METHOD_NOT_ALLOWED => new Response(405, body: '{"error":"Method Not Allowed"}'),
            Dispatcher::FOUND => $this->dispatchRoute($request, $routeInfo[1], $routeInfo[2]),
        };
    }

    private function dispatchRoute(
        ServerRequestInterface $request,
        string $handlerClass,
        array $vars,
    ): ResponseInterface {
        foreach ($vars as $key => $value) {
            $request = $request->withAttribute($key, $value);
        }

        $handler = $this->container->get($handlerClass);

        return $handler->handle($request);
    }
}
```

## Middleware Pipeline

```php
declare(strict_types=1);

namespace Infrastructure\Http;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final class MiddlewarePipeline implements RequestHandlerInterface
{
    /** @var array<MiddlewareInterface> */
    private array $middlewares = [];
    private int $index = 0;

    public function __construct(
        private readonly RequestHandlerInterface $fallbackHandler,
    ) {}

    public function pipe(MiddlewareInterface $middleware): self
    {
        $this->middlewares[] = $middleware;

        return $this;
    }

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        if (!isset($this->middlewares[$this->index])) {
            return $this->fallbackHandler->handle($request);
        }

        $middleware = $this->middlewares[$this->index];
        $next = clone $this;
        $next->index++;

        return $middleware->process($request, $next);
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        return $this->handle($request);
    }
}
```

## PSR-15 Action (Presentation Layer)

**Good — thin action delegating to Use Case:**

```php
declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\Command\CreateOrderCommand;
use Application\Order\UseCase\CreateOrderUseCase;
use Nyholm\Psr7\Response;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CreateOrderAction implements RequestHandlerInterface
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
        private RequestValidator $validator,
    ) {}

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();
        $errors = $this->validator->validate($body, CreateOrderRequest::rules());

        if ($errors !== []) {
            return new Response(
                status: 422,
                body: json_encode(['errors' => $errors], JSON_THROW_ON_ERROR),
            );
        }

        $command = new CreateOrderCommand(
            customerId: $body['customer_id'],
            lines: $body['lines'],
        );

        $orderId = $this->createOrder->execute($command);

        return new Response(
            status: 201,
            headers: ['Content-Type' => 'application/json'],
            body: json_encode(['id' => $orderId->value], JSON_THROW_ON_ERROR),
        );
    }
}
```

## Input Validation Without Framework

```php
declare(strict_types=1);

namespace Infrastructure\Http\Validation;

final readonly class RequestValidator
{
    /** @return array<string, string[]> */
    public function validate(array $data, array $rules): array
    {
        $errors = [];

        foreach ($rules as $field => $fieldRules) {
            foreach ($fieldRules as $rule) {
                $error = match (true) {
                    $rule === 'required' && !isset($data[$field])
                        => sprintf('Field "%s" is required', $field),
                    $rule === 'string' && isset($data[$field]) && !is_string($data[$field])
                        => sprintf('Field "%s" must be a string', $field),
                    $rule === 'uuid' && isset($data[$field]) && !$this->isUuid((string) $data[$field])
                        => sprintf('Field "%s" must be a valid UUID', $field),
                    $rule === 'array' && isset($data[$field]) && !is_array($data[$field])
                        => sprintf('Field "%s" must be an array', $field),
                    default => null,
                };

                if ($error !== null) {
                    $errors[$field][] = $error;
                }
            }
        }

        return $errors;
    }

    private function isUuid(string $value): bool
    {
        return preg_match(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i',
            $value,
        ) === 1;
    }
}
```

## Error Handling Middleware

```php
declare(strict_types=1);

namespace Infrastructure\Http\Middleware;

use Nyholm\Psr7\Response;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Psr\Log\LoggerInterface;

final readonly class ErrorHandlerMiddleware implements MiddlewareInterface
{
    public function __construct(
        private LoggerInterface $logger,
        private bool $debug = false,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        try {
            return $handler->handle($request);
        } catch (\Throwable $e) {
            $this->logger->error($e->getMessage(), [
                'exception' => $e::class,
                'file' => $e->getFile(),
                'line' => $e->getLine(),
                'uri' => (string) $request->getUri(),
            ]);

            $body = ['error' => 'Internal Server Error'];
            if ($this->debug) {
                $body['message'] = $e->getMessage();
                $body['trace'] = $e->getTraceAsString();
            }

            return new Response(
                status: 500,
                headers: ['Content-Type' => 'application/json'],
                body: json_encode($body, JSON_THROW_ON_ERROR),
            );
        }
    }
}
```

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| Raw superglobals (`$_GET`, `$_POST`) | Critical | Testability, security |
| Raw `header()` / `echo` in source | Critical | PSR compliance |
| No routing — if/switch on URI | Critical | Maintainability |
| Missing error handling middleware | Warning | Reliability |
| Business logic in Action/Controller | Warning | Separation of concerns |
| No input validation | Warning | Security |
| Missing CORS middleware | Info | API usability |
