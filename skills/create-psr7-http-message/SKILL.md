---
name: create-psr7-http-message
description: Generates PSR-7 HTTP Message implementations for PHP 8.4. Creates Request, Response, Stream, Uri, and ServerRequest classes with immutability. Includes unit tests.
---

# PSR-7 HTTP Message Generator

## Overview

Generates PSR-7 compliant HTTP message implementations following `Psr\Http\Message` interfaces.

## When to Use

- Building custom HTTP framework
- Creating lightweight HTTP message handling
- Need for immutable request/response objects
- Testing HTTP interactions

## Generated Components

| Component | Interface | Location |
|-----------|-----------|----------|
| Request | `RequestInterface` | `src/{architecture-path}/Http/Message/` |
| Response | `ResponseInterface` | `src/{architecture-path}/Http/Message/` |
| ServerRequest | `ServerRequestInterface` | `src/{architecture-path}/Http/Message/` |
| Stream | `StreamInterface` | `src/{architecture-path}/Http/Message/` |
| Uri | `UriInterface` | `src/{architecture-path}/Http/Message/` |
| UploadedFile | `UploadedFileInterface` | `src/{architecture-path}/Http/Message/` |

> `{architecture-path}` represents your project's architecture-specific folders. PSR-7 HTTP message implementations typically live with other HTTP infrastructure. Adjust to your project's layout.

## Quick Template: Response

```php
<?php

declare(strict_types=1);

namespace Http\Message;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamInterface;

final readonly class Response implements ResponseInterface
{
    private const PHRASES = [
        200 => 'OK', 201 => 'Created', 204 => 'No Content',
        400 => 'Bad Request', 401 => 'Unauthorized', 403 => 'Forbidden',
        404 => 'Not Found', 500 => 'Internal Server Error',
    ];

    public function __construct(
        private int $statusCode = 200,
        private string $reasonPhrase = '',
        private array $headers = [],
        private StreamInterface $body = new Stream(''),
        private string $protocolVersion = '1.1',
    ) {}

    public function getStatusCode(): int { return $this->statusCode; }
    public function getReasonPhrase(): string { return $this->reasonPhrase; }
    public function getHeaders(): array { return $this->headers; }
    public function getBody(): StreamInterface { return $this->body; }

    public function withStatus(int $code, string $reasonPhrase = ''): static
    {
        return new self($code, $reasonPhrase ?: (self::PHRASES[$code] ?? ''),
            $this->headers, $this->body, $this->protocolVersion);
    }

    public function withHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $headers[strtolower($name)] = is_array($value) ? $value : [$value];
        return new self($this->statusCode, $this->reasonPhrase, $headers,
            $this->body, $this->protocolVersion);
    }

    public function withBody(StreamInterface $body): static
    {
        return new self($this->statusCode, $this->reasonPhrase,
            $this->headers, $body, $this->protocolVersion);
    }

    // ... other MessageInterface methods
}
```

## Usage Example

```php
<?php

use Http\Message\Response;
use Http\Message\Stream;

// Create response
$response = new Response(200);
$response = $response
    ->withHeader('Content-Type', 'application/json')
    ->withBody(new Stream(json_encode(['status' => 'ok'])));

// Read response
echo $response->getStatusCode();           // 200
echo $response->getHeaderLine('Content-Type'); // application/json
echo (string) $response->getBody();        // {"status":"ok"}
```

## Requirements

```json
{
    "require": {
        "psr/http-message": "^2.0"
    }
}
```

## See Also

- `references/templates.md` - Full Response, Stream, Uri, Request, ServerRequest, UploadedFile templates
- `references/examples.md` - Integration examples
