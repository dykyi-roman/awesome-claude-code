# PSR-17 HTTP Factory Templates

## Separate Factories

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Factory;

use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\RequestInterface;

final readonly class RequestFactory implements RequestFactoryInterface
{
    public function createRequest(string $method, $uri): RequestInterface
    {
        return new Request(
            $method,
            is_string($uri) ? Uri::fromString($uri) : $uri,
        );
    }
}

final readonly class ResponseFactory implements ResponseFactoryInterface
{
    public function createResponse(int $code = 200, string $reasonPhrase = ''): ResponseInterface
    {
        return new Response($code, $reasonPhrase);
    }
}

final readonly class StreamFactory implements StreamFactoryInterface
{
    public function createStream(string $content = ''): StreamInterface
    {
        return new Stream($content);
    }

    public function createStreamFromFile(string $filename, string $mode = 'r'): StreamInterface
    {
        $resource = fopen($filename, $mode);

        if ($resource === false) {
            throw new \RuntimeException("Cannot open file: {$filename}");
        }

        return $this->createStreamFromResource($resource);
    }

    public function createStreamFromResource($resource): StreamInterface
    {
        return new Stream(stream_get_contents($resource) ?: '');
    }
}

final readonly class UriFactory implements UriFactoryInterface
{
    public function createUri(string $uri = ''): UriInterface
    {
        return Uri::fromString($uri);
    }
}
```

## JSON Response Helper

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Factory;

use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class JsonResponseFactory
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {
    }

    public function create(
        array $data,
        int $status = 200,
        int $options = JSON_THROW_ON_ERROR,
    ): ResponseInterface {
        $json = json_encode($data, $options);

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($this->streamFactory->createStream($json));
    }

    public function success(array $data): ResponseInterface
    {
        return $this->create($data, 200);
    }

    public function created(array $data): ResponseInterface
    {
        return $this->create($data, 201);
    }

    public function error(string $message, int $status = 400): ResponseInterface
    {
        return $this->create(['error' => $message], $status);
    }

    public function notFound(string $message = 'Not Found'): ResponseInterface
    {
        return $this->error($message, 404);
    }
}
```

## Test Request Builder

```php
<?php

declare(strict_types=1);

namespace App\Tests\Support;

use Psr\Http\Message\ServerRequestFactoryInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamFactoryInterface;

final class TestRequestBuilder
{
    private string $method = 'GET';
    private string $uri = '/';
    private array $headers = [];
    private ?string $body = null;
    private array $queryParams = [];
    private array $parsedBody = [];
    private array $attributes = [];

    public function __construct(
        private readonly ServerRequestFactoryInterface $requestFactory,
        private readonly StreamFactoryInterface $streamFactory,
    ) {
    }

    public function method(string $method): self
    {
        $clone = clone $this;
        $clone->method = $method;

        return $clone;
    }

    public function uri(string $uri): self
    {
        $clone = clone $this;
        $clone->uri = $uri;

        return $clone;
    }

    public function header(string $name, string $value): self
    {
        $clone = clone $this;
        $clone->headers[$name] = $value;

        return $clone;
    }

    public function json(array $data): self
    {
        $clone = clone $this;
        $clone->body = json_encode($data);
        $clone->headers['Content-Type'] = 'application/json';
        $clone->parsedBody = $data;

        return $clone;
    }

    public function query(array $params): self
    {
        $clone = clone $this;
        $clone->queryParams = $params;

        return $clone;
    }

    public function attribute(string $name, mixed $value): self
    {
        $clone = clone $this;
        $clone->attributes[$name] = $value;

        return $clone;
    }

    public function build(): ServerRequestInterface
    {
        $request = $this->requestFactory->createServerRequest($this->method, $this->uri);

        foreach ($this->headers as $name => $value) {
            $request = $request->withHeader($name, $value);
        }

        if ($this->body !== null) {
            $request = $request->withBody($this->streamFactory->createStream($this->body));
        }

        if (!empty($this->queryParams)) {
            $request = $request->withQueryParams($this->queryParams);
        }

        if (!empty($this->parsedBody)) {
            $request = $request->withParsedBody($this->parsedBody);
        }

        foreach ($this->attributes as $name => $value) {
            $request = $request->withAttribute($name, $value);
        }

        return $request;
    }
}

// Usage in tests
$request = (new TestRequestBuilder($requestFactory, $streamFactory))
    ->method('POST')
    ->uri('/api/users')
    ->json(['name' => 'John', 'email' => 'john@example.com'])
    ->header('Authorization', 'Bearer token')
    ->build();
```
