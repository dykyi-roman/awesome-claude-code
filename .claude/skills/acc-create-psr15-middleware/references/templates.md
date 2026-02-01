# PSR-15 Middleware Templates

## JSON Body Parser Middleware

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

            if (json_last_error() === JSON_ERROR_NONE && is_array($data)) {
                $request = $request->withParsedBody($data);
            }
        }

        return $handler->handle($request);
    }
}
```

## Rate Limiting Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Psr\SimpleCache\CacheInterface;

final readonly class RateLimitMiddleware implements MiddlewareInterface
{
    public function __construct(
        private CacheInterface $cache,
        private int $maxRequests = 100,
        private int $windowSeconds = 60,
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $clientIp = $this->getClientIp($request);
        $key = 'rate_limit:' . md5($clientIp);

        $current = (int) ($this->cache->get($key) ?? 0);

        if ($current >= $this->maxRequests) {
            return (new Response(429))
                ->withHeader('Content-Type', 'application/json')
                ->withHeader('Retry-After', (string) $this->windowSeconds)
                ->withBody(new Stream(json_encode(['error' => 'Too Many Requests'])));
        }

        $this->cache->set($key, $current + 1, $this->windowSeconds);

        $response = $handler->handle($request);

        return $response
            ->withHeader('X-RateLimit-Limit', (string) $this->maxRequests)
            ->withHeader('X-RateLimit-Remaining', (string) ($this->maxRequests - $current - 1));
    }

    private function getClientIp(ServerRequestInterface $request): string
    {
        $serverParams = $request->getServerParams();

        return $serverParams['HTTP_X_FORWARDED_FOR']
            ?? $serverParams['REMOTE_ADDR']
            ?? 'unknown';
    }
}
```

## Content Negotiation Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class ContentNegotiationMiddleware implements MiddlewareInterface
{
    private const SUPPORTED_TYPES = [
        'application/json',
        'application/xml',
        'text/html',
    ];

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $accept = $request->getHeaderLine('Accept');
        $preferredType = $this->negotiate($accept);

        $request = $request->withAttribute('preferred_content_type', $preferredType);

        return $handler->handle($request);
    }

    private function negotiate(string $accept): string
    {
        if ($accept === '' || $accept === '*/*') {
            return self::SUPPORTED_TYPES[0];
        }

        $acceptedTypes = array_map('trim', explode(',', $accept));

        foreach ($acceptedTypes as $type) {
            $type = explode(';', $type)[0];

            if (in_array($type, self::SUPPORTED_TYPES, true)) {
                return $type;
            }
        }

        return self::SUPPORTED_TYPES[0];
    }
}
```

## Session Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final class SessionMiddleware implements MiddlewareInterface
{
    public function __construct(
        private readonly SessionManagerInterface $sessionManager,
        private readonly string $cookieName = 'PHPSESSID',
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $cookies = $request->getCookieParams();
        $sessionId = $cookies[$this->cookieName] ?? null;

        $session = $sessionId !== null
            ? $this->sessionManager->load($sessionId)
            : $this->sessionManager->create();

        $request = $request->withAttribute('session', $session);

        $response = $handler->handle($request);

        $this->sessionManager->save($session);

        if ($sessionId === null) {
            $response = $response->withHeader(
                'Set-Cookie',
                sprintf('%s=%s; HttpOnly; SameSite=Lax', $this->cookieName, $session->getId()),
            );
        }

        return $response;
    }
}
```

## Conditional Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class ConditionalMiddleware implements MiddlewareInterface
{
    /** @param callable(ServerRequestInterface): bool $condition */
    public function __construct(
        private MiddlewareInterface $middleware,
        private $condition,
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        if (($this->condition)($request)) {
            return $this->middleware->process($request, $handler);
        }

        return $handler->handle($request);
    }
}

// Usage
$apiOnlyAuth = new ConditionalMiddleware(
    new AuthenticationMiddleware($validator),
    fn($request) => str_starts_with($request->getUri()->getPath(), '/api/'),
);
```

## Routing Middleware

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class RoutingMiddleware implements MiddlewareInterface
{
    public function __construct(
        private RouterInterface $router,
    ) {
    }

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $route = $this->router->match($request);

        if ($route === null) {
            return $handler->handle($request);
        }

        $request = $request
            ->withAttribute('_route', $route->getName())
            ->withAttribute('_controller', $route->getController())
            ->withAttribute('_action', $route->getAction());

        foreach ($route->getParams() as $name => $value) {
            $request = $request->withAttribute($name, $value);
        }

        return $handler->handle($request);
    }
}
```
