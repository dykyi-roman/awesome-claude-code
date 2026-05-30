# Routing and HTTP in Yii3

Yii3 routing via `yiisoft/router`, Actions, PSR-7 Request/Response, PSR-15 middleware pipeline, and input validation.

## Yii3 Routing (yiisoft/router)

### Route Definitions

```php
<?php

declare(strict_types=1);

// config/web/routes.php

use Yiisoft\Router\Route;
use Yiisoft\Router\Group;

return [
    Route::get('/health')
        ->action([HealthAction::class, '__invoke'])
        ->name('health'),

    Group::create('/api/v1')
        ->middleware(AuthenticationMiddleware::class)
        ->routes(
            Route::get('/orders')
                ->action([ListOrdersAction::class, '__invoke'])
                ->name('orders.list'),

            Route::post('/orders')
                ->action([CreateOrderAction::class, '__invoke'])
                ->name('orders.create'),

            Route::get('/orders/{id}')
                ->action([GetOrderAction::class, '__invoke'])
                ->name('orders.show'),

            Route::put('/orders/{id}')
                ->action([UpdateOrderAction::class, '__invoke'])
                ->name('orders.update'),

            Route::delete('/orders/{id}')
                ->action([DeleteOrderAction::class, '__invoke'])
                ->name('orders.delete'),
        ),
];
```

### Route Groups with Middleware

```php
<?php

declare(strict_types=1);

return [
    Group::create('/api')
        ->middleware(CorsMiddleware::class)
        ->middleware(JsonContentTypeMiddleware::class)
        ->routes(
            Group::create('/admin')
                ->middleware(AdminAuthMiddleware::class)
                ->routes(
                    Route::get('/users')->action([AdminListUsersAction::class, '__invoke']),
                ),
            Group::create('/public')
                ->routes(
                    Route::get('/catalog')->action([CatalogAction::class, '__invoke']),
                ),
        ),
];
```

## Actions (Controllers)

### Single Action Controller Pattern

```php
<?php

declare(strict_types=1);

namespace Order;

use UseCase\CreateOrderUseCase;
use DTO\CreateOrderDTO;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Yiisoft\Http\Status;
use Yiisoft\DataResponse\DataResponseFactoryInterface;

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
            return $this->responseFactory
                ->createResponse($violations->toArray())
                ->withStatus(Status::UNPROCESSABLE_ENTITY);
        }

        $dto = CreateOrderDTO::fromArray($body);
        $result = $this->createOrder->execute($dto);

        return $this->responseFactory
            ->createResponse($result->toArray())
            ->withStatus(Status::CREATED);
    }
}
```

### Reading Route Parameters

```php
<?php

declare(strict_types=1);

namespace Order;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Yiisoft\Router\CurrentRoute;

final readonly class GetOrderAction
{
    public function __construct(
        private GetOrderUseCase $getOrder,
        private DataResponseFactoryInterface $responseFactory,
        private CurrentRoute $currentRoute,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $id = $this->currentRoute->getArgument('id');

        if ($id === null) {
            return $this->responseFactory
                ->createResponse(['error' => 'Missing order ID'])
                ->withStatus(Status::BAD_REQUEST);
        }

        $result = $this->getOrder->execute(new OrderId($id));

        if ($result === null) {
            return $this->responseFactory
                ->createResponse(['error' => 'Order not found'])
                ->withStatus(Status::NOT_FOUND);
        }

        return $this->responseFactory->createResponse($result->toArray());
    }
}
```

## PSR-7 Request/Response

### Request Handling

```php
<?php

declare(strict_types=1);

// Reading request data (PSR-7)
$body       = $request->getParsedBody();           // POST body (array)
$query      = $request->getQueryParams();           // GET parameters
$headers    = $request->getHeaders();               // All headers
$authHeader = $request->getHeaderLine('Authorization');
$attribute  = $request->getAttribute('userId');     // Set by middleware
$method     = $request->getMethod();                // GET, POST, etc.
$uri        = $request->getUri()->getPath();        // /api/v1/orders
```

### Response Building

```php
<?php

declare(strict_types=1);

use Yiisoft\DataResponse\DataResponseFactoryInterface;
use Yiisoft\Http\Status;

final readonly class OrderAction
{
    public function __construct(
        private DataResponseFactoryInterface $responseFactory,
    ) {}

    public function success(array $data): ResponseInterface
    {
        return $this->responseFactory
            ->createResponse($data)
            ->withStatus(Status::OK);
    }

    public function created(array $data): ResponseInterface
    {
        return $this->responseFactory
            ->createResponse($data)
            ->withStatus(Status::CREATED)
            ->withHeader('Location', '/api/v1/orders/' . $data['id']);
    }

    public function noContent(): ResponseInterface
    {
        return $this->responseFactory
            ->createResponse()
            ->withStatus(Status::NO_CONTENT);
    }
}
```

## PSR-15 Middleware Pipeline

### Custom Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class JsonContentTypeMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $response = $handler->handle($request);

        if (!$response->hasHeader('Content-Type')) {
            return $response->withHeader('Content-Type', 'application/json; charset=UTF-8');
        }

        return $response;
    }
}
```

### Authentication Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Yiisoft\Http\Status;

final readonly class BearerAuthMiddleware implements MiddlewareInterface
{
    public function __construct(
        private TokenValidatorInterface $tokenValidator,
        private DataResponseFactoryInterface $responseFactory,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $token = $this->extractBearerToken($request);

        if ($token === null) {
            return $this->responseFactory
                ->createResponse(['error' => 'Missing authentication token'])
                ->withStatus(Status::UNAUTHORIZED);
        }

        $userId = $this->tokenValidator->validate($token);

        if ($userId === null) {
            return $this->responseFactory
                ->createResponse(['error' => 'Invalid token'])
                ->withStatus(Status::UNAUTHORIZED);
        }

        return $handler->handle(
            $request->withAttribute('userId', $userId),
        );
    }

    private function extractBearerToken(ServerRequestInterface $request): ?string
    {
        $header = $request->getHeaderLine('Authorization');

        if (!str_starts_with($header, 'Bearer ')) {
            return null;
        }

        return substr($header, 7);
    }
}
```

## Input Validation

### Using yiisoft/validator

```php
<?php

declare(strict_types=1);

namespace Order;

use Yiisoft\Validator\Rule\Required;
use Yiisoft\Validator\Rule\Length;
use Yiisoft\Validator\Rule\Number;
use Yiisoft\Validator\Rule\Each;
use Yiisoft\Validator\ValidatorInterface;
use Yiisoft\Validator\Result;

final readonly class OrderRequestValidator
{
    public function __construct(
        private ValidatorInterface $validator,
    ) {}

    public function validate(array $data): Result
    {
        return $this->validator->validate($data, [
            'customer_id' => [new Required(), new Length(min: 1, max: 36)],
            'lines' => [new Required(), new Each([
                'product_id' => [new Required()],
                'quantity' => [new Required(), new Number(min: 1, max: 9999)],
            ])],
        ]);
    }
}
```

## Detection Patterns

```bash
# Find route definitions
Grep: "Route::get\|Route::post\|Route::put\|Route::delete" --glob "config/**/*.php"

# Find actions/controllers
Grep: "ServerRequestInterface" --glob "**/Presentation/**/*.php"
Glob: **/Presentation/**/*Action.php

# Middleware registration
Grep: "->middleware\(" --glob "config/**/*.php"
Grep: "MiddlewareInterface" --glob "**/*.php"

# Business logic in actions (violation)
Grep: "if \(.*->status|switch \(" --glob "**/Presentation/**/*Action.php"
Grep: "->save\(|->persist\(" --glob "**/Presentation/**/*Action.php"

# PSR-7 request usage
Grep: "getParsedBody\|getQueryParams\|getHeaderLine" --glob "**/Presentation/**/*.php"
```
