# PSR-7 HTTP Message Examples

## Creating Requests

```php
<?php

use App\Infrastructure\Http\Message\Request;
use App\Infrastructure\Http\Message\Stream;
use App\Infrastructure\Http\Message\Uri;

// Simple GET request
$request = new Request('GET', 'https://api.example.com/users');

// POST request with JSON body
$body = new Stream(json_encode(['name' => 'John', 'email' => 'john@example.com']));
$request = new Request('POST', 'https://api.example.com/users');
$request = $request
    ->withHeader('Content-Type', 'application/json')
    ->withHeader('Authorization', 'Bearer token123')
    ->withBody($body);

// Building URI
$uri = new Uri('https', 'api.example.com', null, '/users', 'page=1&limit=10');
$request = new Request('GET', $uri);
```

## Creating Responses

```php
<?php

use App\Infrastructure\Http\Message\Response;
use App\Infrastructure\Http\Message\Stream;

// Simple OK response
$response = new Response(200);

// JSON response
$response = (new Response(200))
    ->withHeader('Content-Type', 'application/json')
    ->withBody(new Stream(json_encode(['status' => 'success'])));

// Error response
$response = (new Response(404))
    ->withHeader('Content-Type', 'application/json')
    ->withBody(new Stream(json_encode(['error' => 'Not Found'])));

// Redirect response
$response = (new Response(302))
    ->withHeader('Location', 'https://example.com/new-location');
```

## Working with ServerRequest

```php
<?php

use App\Infrastructure\Http\Message\ServerRequest;

// From globals (in index.php)
$request = ServerRequest::fromGlobals();

// Get request data
$method = $request->getMethod();
$uri = $request->getUri();
$queryParams = $request->getQueryParams();
$body = $request->getParsedBody();
$headers = $request->getHeaders();

// Get specific query param
$page = $request->getQueryParams()['page'] ?? 1;

// Get uploaded files
$files = $request->getUploadedFiles();
foreach ($files as $file) {
    if ($file->getError() === UPLOAD_ERR_OK) {
        $file->moveTo('/uploads/' . $file->getClientFilename());
    }
}

// Add attributes (e.g., from routing)
$request = $request
    ->withAttribute('user_id', 123)
    ->withAttribute('role', 'admin');

$userId = $request->getAttribute('user_id');
```

## Controller Example

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Controller;

use App\Application\User\Query\GetUserQuery;
use App\Infrastructure\Http\Message\Response;
use App\Infrastructure\Http\Message\Stream;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class UserController
{
    public function __construct(
        private GetUserHandler $handler,
    ) {
    }

    public function show(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('id');

        if ($userId === null) {
            return $this->jsonResponse(['error' => 'User ID required'], 400);
        }

        try {
            $user = ($this->handler)(new GetUserQuery($userId));

            return $this->jsonResponse([
                'id' => $user->id,
                'name' => $user->name,
                'email' => $user->email,
            ]);
        } catch (UserNotFoundException) {
            return $this->jsonResponse(['error' => 'User not found'], 404);
        }
    }

    private function jsonResponse(array $data, int $status = 200): ResponseInterface
    {
        return (new Response($status))
            ->withHeader('Content-Type', 'application/json')
            ->withBody(new Stream(json_encode($data)));
    }
}
```

## Middleware Example

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class JsonBodyParserMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $contentType = $request->getHeaderLine('Content-Type');

        if (str_contains($contentType, 'application/json')) {
            $body = (string) $request->getBody();
            $data = json_decode($body, true);

            if (json_last_error() === JSON_ERROR_NONE) {
                $request = $request->withParsedBody($data);
            }
        }

        return $handler->handle($request);
    }
}
```

## Testing with PSR-7

```php
<?php

declare(strict_types=1);

namespace App\Tests\Functional;

use App\Infrastructure\Http\Message\ServerRequest;
use App\Infrastructure\Http\Message\Stream;
use PHPUnit\Framework\TestCase;

final class UserControllerTest extends TestCase
{
    public function test_create_user(): void
    {
        $body = new Stream(json_encode([
            'name' => 'John Doe',
            'email' => 'john@example.com',
        ]));

        $request = (new ServerRequest('POST', '/api/users'))
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body)
            ->withParsedBody([
                'name' => 'John Doe',
                'email' => 'john@example.com',
            ]);

        $response = $this->controller->create($request);

        self::assertSame(201, $response->getStatusCode());
    }
}
```

## Response Helpers

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use App\Infrastructure\Http\Message\Response;
use App\Infrastructure\Http\Message\Stream;
use Psr\Http\Message\ResponseInterface;

final readonly class ResponseFactory
{
    public function json(array $data, int $status = 200): ResponseInterface
    {
        return (new Response($status))
            ->withHeader('Content-Type', 'application/json')
            ->withBody(new Stream(json_encode($data, JSON_THROW_ON_ERROR)));
    }

    public function html(string $content, int $status = 200): ResponseInterface
    {
        return (new Response($status))
            ->withHeader('Content-Type', 'text/html; charset=utf-8')
            ->withBody(new Stream($content));
    }

    public function redirect(string $url, int $status = 302): ResponseInterface
    {
        return (new Response($status))
            ->withHeader('Location', $url);
    }

    public function noContent(): ResponseInterface
    {
        return new Response(204);
    }

    public function error(string $message, int $status = 500): ResponseInterface
    {
        return $this->json(['error' => $message], $status);
    }
}
```
