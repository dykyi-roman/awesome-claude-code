# PSR-7 HTTP Message Templates

## Response

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamInterface;

final readonly class Response implements ResponseInterface
{
    private const PHRASES = [
        200 => 'OK',
        201 => 'Created',
        204 => 'No Content',
        301 => 'Moved Permanently',
        302 => 'Found',
        304 => 'Not Modified',
        400 => 'Bad Request',
        401 => 'Unauthorized',
        403 => 'Forbidden',
        404 => 'Not Found',
        405 => 'Method Not Allowed',
        422 => 'Unprocessable Entity',
        500 => 'Internal Server Error',
        502 => 'Bad Gateway',
        503 => 'Service Unavailable',
    ];

    /** @param array<string, string[]> $headers */
    public function __construct(
        private int $statusCode = 200,
        private string $reasonPhrase = '',
        private array $headers = [],
        private StreamInterface $body = new Stream(''),
        private string $protocolVersion = '1.1',
    ) {
        if ($this->reasonPhrase === '' && isset(self::PHRASES[$this->statusCode])) {
            $this->reasonPhrase = self::PHRASES[$this->statusCode];
        }
    }

    public function getProtocolVersion(): string
    {
        return $this->protocolVersion;
    }

    public function withProtocolVersion(string $version): static
    {
        return new self(
            $this->statusCode,
            $this->reasonPhrase,
            $this->headers,
            $this->body,
            $version,
        );
    }

    public function getHeaders(): array
    {
        return $this->headers;
    }

    public function hasHeader(string $name): bool
    {
        return isset($this->headers[strtolower($name)]);
    }

    public function getHeader(string $name): array
    {
        return $this->headers[strtolower($name)] ?? [];
    }

    public function getHeaderLine(string $name): string
    {
        return implode(', ', $this->getHeader($name));
    }

    public function withHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $headers[strtolower($name)] = is_array($value) ? $value : [$value];

        return new self(
            $this->statusCode,
            $this->reasonPhrase,
            $headers,
            $this->body,
            $this->protocolVersion,
        );
    }

    public function withAddedHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $key = strtolower($name);
        $existing = $headers[$key] ?? [];
        $headers[$key] = [...$existing, ...(is_array($value) ? $value : [$value])];

        return new self(
            $this->statusCode,
            $this->reasonPhrase,
            $headers,
            $this->body,
            $this->protocolVersion,
        );
    }

    public function withoutHeader(string $name): static
    {
        $headers = $this->headers;
        unset($headers[strtolower($name)]);

        return new self(
            $this->statusCode,
            $this->reasonPhrase,
            $headers,
            $this->body,
            $this->protocolVersion,
        );
    }

    public function getBody(): StreamInterface
    {
        return $this->body;
    }

    public function withBody(StreamInterface $body): static
    {
        return new self(
            $this->statusCode,
            $this->reasonPhrase,
            $this->headers,
            $body,
            $this->protocolVersion,
        );
    }

    public function getStatusCode(): int
    {
        return $this->statusCode;
    }

    public function withStatus(int $code, string $reasonPhrase = ''): static
    {
        return new self(
            $code,
            $reasonPhrase ?: (self::PHRASES[$code] ?? ''),
            $this->headers,
            $this->body,
            $this->protocolVersion,
        );
    }

    public function getReasonPhrase(): string
    {
        return $this->reasonPhrase;
    }
}
```

## Stream

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use Psr\Http\Message\StreamInterface;
use RuntimeException;

final class Stream implements StreamInterface
{
    /** @var resource|null */
    private $stream;
    private ?int $size = null;
    private bool $seekable = false;
    private bool $readable = false;
    private bool $writable = false;

    public function __construct(string $content = '')
    {
        $stream = fopen('php://temp', 'r+');

        if ($stream === false) {
            throw new RuntimeException('Cannot create stream');
        }

        $this->stream = $stream;
        fwrite($this->stream, $content);
        rewind($this->stream);

        $meta = stream_get_meta_data($this->stream);
        $this->seekable = $meta['seekable'];
        $this->readable = str_contains($meta['mode'], 'r') || str_contains($meta['mode'], '+');
        $this->writable = str_contains($meta['mode'], 'w') || str_contains($meta['mode'], '+');
    }

    public function __toString(): string
    {
        try {
            if ($this->isSeekable()) {
                $this->rewind();
            }

            return $this->getContents();
        } catch (\Throwable) {
            return '';
        }
    }

    public function close(): void
    {
        if ($this->stream !== null) {
            fclose($this->stream);
            $this->stream = null;
        }
    }

    public function detach()
    {
        $stream = $this->stream;
        $this->stream = null;
        $this->size = null;
        $this->seekable = false;
        $this->readable = false;
        $this->writable = false;

        return $stream;
    }

    public function getSize(): ?int
    {
        if ($this->stream === null) {
            return null;
        }

        if ($this->size !== null) {
            return $this->size;
        }

        $stats = fstat($this->stream);

        if ($stats !== false) {
            $this->size = $stats['size'];
        }

        return $this->size;
    }

    public function tell(): int
    {
        if ($this->stream === null) {
            throw new RuntimeException('Stream is detached');
        }

        $result = ftell($this->stream);

        if ($result === false) {
            throw new RuntimeException('Unable to determine stream position');
        }

        return $result;
    }

    public function eof(): bool
    {
        return $this->stream === null || feof($this->stream);
    }

    public function isSeekable(): bool
    {
        return $this->seekable;
    }

    public function seek(int $offset, int $whence = SEEK_SET): void
    {
        if (!$this->seekable) {
            throw new RuntimeException('Stream is not seekable');
        }

        if (fseek($this->stream, $offset, $whence) === -1) {
            throw new RuntimeException('Unable to seek stream');
        }
    }

    public function rewind(): void
    {
        $this->seek(0);
    }

    public function isWritable(): bool
    {
        return $this->writable;
    }

    public function write(string $string): int
    {
        if (!$this->writable) {
            throw new RuntimeException('Stream is not writable');
        }

        $result = fwrite($this->stream, $string);

        if ($result === false) {
            throw new RuntimeException('Unable to write to stream');
        }

        $this->size = null;

        return $result;
    }

    public function isReadable(): bool
    {
        return $this->readable;
    }

    public function read(int $length): string
    {
        if (!$this->readable) {
            throw new RuntimeException('Stream is not readable');
        }

        $result = fread($this->stream, $length);

        if ($result === false) {
            throw new RuntimeException('Unable to read from stream');
        }

        return $result;
    }

    public function getContents(): string
    {
        if (!$this->readable) {
            throw new RuntimeException('Stream is not readable');
        }

        $result = stream_get_contents($this->stream);

        if ($result === false) {
            throw new RuntimeException('Unable to read stream contents');
        }

        return $result;
    }

    public function getMetadata(?string $key = null): mixed
    {
        if ($this->stream === null) {
            return $key === null ? [] : null;
        }

        $meta = stream_get_meta_data($this->stream);

        return $key === null ? $meta : ($meta[$key] ?? null);
    }
}
```

## Uri

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use InvalidArgumentException;
use Psr\Http\Message\UriInterface;

final readonly class Uri implements UriInterface
{
    public function __construct(
        private string $scheme = '',
        private string $host = '',
        private ?int $port = null,
        private string $path = '',
        private string $query = '',
        private string $fragment = '',
        private string $userInfo = '',
    ) {
    }

    public static function fromString(string $uri): self
    {
        $parts = parse_url($uri);

        if ($parts === false) {
            throw new InvalidArgumentException("Invalid URI: {$uri}");
        }

        $userInfo = $parts['user'] ?? '';
        if (isset($parts['pass'])) {
            $userInfo .= ':' . $parts['pass'];
        }

        return new self(
            scheme: $parts['scheme'] ?? '',
            host: $parts['host'] ?? '',
            port: $parts['port'] ?? null,
            path: $parts['path'] ?? '',
            query: $parts['query'] ?? '',
            fragment: $parts['fragment'] ?? '',
            userInfo: $userInfo,
        );
    }

    public function getScheme(): string
    {
        return $this->scheme;
    }

    public function getAuthority(): string
    {
        if ($this->host === '') {
            return '';
        }

        $authority = $this->host;

        if ($this->userInfo !== '') {
            $authority = $this->userInfo . '@' . $authority;
        }

        if ($this->port !== null && !$this->isStandardPort()) {
            $authority .= ':' . $this->port;
        }

        return $authority;
    }

    public function getUserInfo(): string
    {
        return $this->userInfo;
    }

    public function getHost(): string
    {
        return $this->host;
    }

    public function getPort(): ?int
    {
        return $this->isStandardPort() ? null : $this->port;
    }

    public function getPath(): string
    {
        return $this->path;
    }

    public function getQuery(): string
    {
        return $this->query;
    }

    public function getFragment(): string
    {
        return $this->fragment;
    }

    public function withScheme(string $scheme): static
    {
        return new self($scheme, $this->host, $this->port, $this->path, $this->query, $this->fragment, $this->userInfo);
    }

    public function withUserInfo(string $user, ?string $password = null): static
    {
        $userInfo = $user;
        if ($password !== null) {
            $userInfo .= ':' . $password;
        }

        return new self($this->scheme, $this->host, $this->port, $this->path, $this->query, $this->fragment, $userInfo);
    }

    public function withHost(string $host): static
    {
        return new self($this->scheme, $host, $this->port, $this->path, $this->query, $this->fragment, $this->userInfo);
    }

    public function withPort(?int $port): static
    {
        return new self($this->scheme, $this->host, $port, $this->path, $this->query, $this->fragment, $this->userInfo);
    }

    public function withPath(string $path): static
    {
        return new self($this->scheme, $this->host, $this->port, $path, $this->query, $this->fragment, $this->userInfo);
    }

    public function withQuery(string $query): static
    {
        return new self($this->scheme, $this->host, $this->port, $this->path, $query, $this->fragment, $this->userInfo);
    }

    public function withFragment(string $fragment): static
    {
        return new self($this->scheme, $this->host, $this->port, $this->path, $this->query, $fragment, $this->userInfo);
    }

    public function __toString(): string
    {
        $uri = '';

        if ($this->scheme !== '') {
            $uri .= $this->scheme . ':';
        }

        $authority = $this->getAuthority();
        if ($authority !== '') {
            $uri .= '//' . $authority;
        }

        $uri .= $this->path;

        if ($this->query !== '') {
            $uri .= '?' . $this->query;
        }

        if ($this->fragment !== '') {
            $uri .= '#' . $this->fragment;
        }

        return $uri;
    }

    private function isStandardPort(): bool
    {
        $standardPorts = ['http' => 80, 'https' => 443];

        return $this->port === null
            || ($standardPorts[$this->scheme] ?? null) === $this->port;
    }
}
```

## Request

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UriInterface;

final readonly class Request implements RequestInterface
{
    private UriInterface $uri;

    /** @param array<string, string[]> $headers */
    public function __construct(
        private string $method = 'GET',
        UriInterface|string $uri = '',
        private array $headers = [],
        private StreamInterface $body = new Stream(''),
        private string $protocolVersion = '1.1',
        private string $requestTarget = '',
    ) {
        $this->uri = $uri instanceof UriInterface ? $uri : Uri::fromString($uri);
    }

    public function getRequestTarget(): string
    {
        if ($this->requestTarget !== '') {
            return $this->requestTarget;
        }

        $target = $this->uri->getPath();

        if ($target === '') {
            $target = '/';
        }

        $query = $this->uri->getQuery();
        if ($query !== '') {
            $target .= '?' . $query;
        }

        return $target;
    }

    public function withRequestTarget(string $requestTarget): static
    {
        return new self(
            $this->method,
            $this->uri,
            $this->headers,
            $this->body,
            $this->protocolVersion,
            $requestTarget,
        );
    }

    public function getMethod(): string
    {
        return $this->method;
    }

    public function withMethod(string $method): static
    {
        return new self(
            $method,
            $this->uri,
            $this->headers,
            $this->body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }

    public function getUri(): UriInterface
    {
        return $this->uri;
    }

    public function withUri(UriInterface $uri, bool $preserveHost = false): static
    {
        $headers = $this->headers;

        if (!$preserveHost || !$this->hasHeader('Host')) {
            $host = $uri->getHost();
            if ($host !== '') {
                $headers['host'] = [$host];
            }
        }

        return new self(
            $this->method,
            $uri,
            $headers,
            $this->body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }

    public function getProtocolVersion(): string
    {
        return $this->protocolVersion;
    }

    public function withProtocolVersion(string $version): static
    {
        return new self(
            $this->method,
            $this->uri,
            $this->headers,
            $this->body,
            $version,
            $this->requestTarget,
        );
    }

    public function getHeaders(): array
    {
        return $this->headers;
    }

    public function hasHeader(string $name): bool
    {
        return isset($this->headers[strtolower($name)]);
    }

    public function getHeader(string $name): array
    {
        return $this->headers[strtolower($name)] ?? [];
    }

    public function getHeaderLine(string $name): string
    {
        return implode(', ', $this->getHeader($name));
    }

    public function withHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $headers[strtolower($name)] = is_array($value) ? $value : [$value];

        return new self(
            $this->method,
            $this->uri,
            $headers,
            $this->body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }

    public function withAddedHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $key = strtolower($name);
        $existing = $headers[$key] ?? [];
        $headers[$key] = [...$existing, ...(is_array($value) ? $value : [$value])];

        return new self(
            $this->method,
            $this->uri,
            $headers,
            $this->body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }

    public function withoutHeader(string $name): static
    {
        $headers = $this->headers;
        unset($headers[strtolower($name)]);

        return new self(
            $this->method,
            $this->uri,
            $headers,
            $this->body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }

    public function getBody(): StreamInterface
    {
        return $this->body;
    }

    public function withBody(StreamInterface $body): static
    {
        return new self(
            $this->method,
            $this->uri,
            $this->headers,
            $body,
            $this->protocolVersion,
            $this->requestTarget,
        );
    }
}
```

## ServerRequest

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UploadedFileInterface;
use Psr\Http\Message\UriInterface;

final readonly class ServerRequest implements ServerRequestInterface
{
    private UriInterface $uri;

    /**
     * @param array<string, string[]> $headers
     * @param array<string, mixed> $serverParams
     * @param array<string, string> $cookieParams
     * @param array<string, mixed> $queryParams
     * @param array<string, UploadedFileInterface> $uploadedFiles
     * @param array<string, mixed> $parsedBody
     * @param array<string, mixed> $attributes
     */
    public function __construct(
        private string $method = 'GET',
        UriInterface|string $uri = '',
        private array $headers = [],
        private StreamInterface $body = new Stream(''),
        private string $protocolVersion = '1.1',
        private array $serverParams = [],
        private array $cookieParams = [],
        private array $queryParams = [],
        private array $uploadedFiles = [],
        private array|object|null $parsedBody = null,
        private array $attributes = [],
    ) {
        $this->uri = $uri instanceof UriInterface ? $uri : Uri::fromString($uri);
    }

    public static function fromGlobals(): self
    {
        $method = $_SERVER['REQUEST_METHOD'] ?? 'GET';
        $uri = self::buildUriFromGlobals();
        $headers = self::getHeadersFromGlobals();
        $body = new Stream(file_get_contents('php://input') ?: '');

        return new self(
            method: $method,
            uri: $uri,
            headers: $headers,
            body: $body,
            serverParams: $_SERVER,
            cookieParams: $_COOKIE,
            queryParams: $_GET,
            uploadedFiles: self::normalizeUploadedFiles($_FILES),
            parsedBody: $_POST ?: null,
        );
    }

    public function getServerParams(): array
    {
        return $this->serverParams;
    }

    public function getCookieParams(): array
    {
        return $this->cookieParams;
    }

    public function withCookieParams(array $cookies): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $cookies,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody,
            $this->attributes,
        );
    }

    public function getQueryParams(): array
    {
        return $this->queryParams;
    }

    public function withQueryParams(array $query): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $query, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getUploadedFiles(): array
    {
        return $this->uploadedFiles;
    }

    public function withUploadedFiles(array $uploadedFiles): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getParsedBody(): array|object|null
    {
        return $this->parsedBody;
    }

    public function withParsedBody($data): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $data, $this->attributes,
        );
    }

    public function getAttributes(): array
    {
        return $this->attributes;
    }

    public function getAttribute(string $name, $default = null): mixed
    {
        return $this->attributes[$name] ?? $default;
    }

    public function withAttribute(string $name, $value): static
    {
        $attributes = $this->attributes;
        $attributes[$name] = $value;

        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $attributes,
        );
    }

    public function withoutAttribute(string $name): static
    {
        $attributes = $this->attributes;
        unset($attributes[$name]);

        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $attributes,
        );
    }

    // ... inherit other methods from Request

    public function getRequestTarget(): string
    {
        $target = $this->uri->getPath() ?: '/';
        $query = $this->uri->getQuery();

        return $query !== '' ? $target . '?' . $query : $target;
    }

    public function withRequestTarget(string $requestTarget): static
    {
        return $this;
    }

    public function getMethod(): string
    {
        return $this->method;
    }

    public function withMethod(string $method): static
    {
        return new self(
            $method, $this->uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getUri(): UriInterface
    {
        return $this->uri;
    }

    public function withUri(UriInterface $uri, bool $preserveHost = false): static
    {
        return new self(
            $this->method, $uri, $this->headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getProtocolVersion(): string
    {
        return $this->protocolVersion;
    }

    public function withProtocolVersion(string $version): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $this->body,
            $version, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getHeaders(): array
    {
        return $this->headers;
    }

    public function hasHeader(string $name): bool
    {
        return isset($this->headers[strtolower($name)]);
    }

    public function getHeader(string $name): array
    {
        return $this->headers[strtolower($name)] ?? [];
    }

    public function getHeaderLine(string $name): string
    {
        return implode(', ', $this->getHeader($name));
    }

    public function withHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $headers[strtolower($name)] = is_array($value) ? $value : [$value];

        return new self(
            $this->method, $this->uri, $headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function withAddedHeader(string $name, $value): static
    {
        $headers = $this->headers;
        $key = strtolower($name);
        $existing = $headers[$key] ?? [];
        $headers[$key] = [...$existing, ...(is_array($value) ? $value : [$value])];

        return new self(
            $this->method, $this->uri, $headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function withoutHeader(string $name): static
    {
        $headers = $this->headers;
        unset($headers[strtolower($name)]);

        return new self(
            $this->method, $this->uri, $headers, $this->body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    public function getBody(): StreamInterface
    {
        return $this->body;
    }

    public function withBody(StreamInterface $body): static
    {
        return new self(
            $this->method, $this->uri, $this->headers, $body,
            $this->protocolVersion, $this->serverParams, $this->cookieParams,
            $this->queryParams, $this->uploadedFiles, $this->parsedBody, $this->attributes,
        );
    }

    private static function buildUriFromGlobals(): Uri
    {
        $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        $host = $_SERVER['HTTP_HOST'] ?? $_SERVER['SERVER_NAME'] ?? 'localhost';
        $port = isset($_SERVER['SERVER_PORT']) ? (int) $_SERVER['SERVER_PORT'] : null;
        $path = parse_url($_SERVER['REQUEST_URI'] ?? '/', PHP_URL_PATH) ?: '/';
        $query = $_SERVER['QUERY_STRING'] ?? '';

        return new Uri($scheme, $host, $port, $path, $query);
    }

    /** @return array<string, string[]> */
    private static function getHeadersFromGlobals(): array
    {
        $headers = [];

        foreach ($_SERVER as $key => $value) {
            if (str_starts_with($key, 'HTTP_')) {
                $name = str_replace('_', '-', strtolower(substr($key, 5)));
                $headers[$name] = [$value];
            }
        }

        return $headers;
    }

    /** @return array<string, UploadedFileInterface> */
    private static function normalizeUploadedFiles(array $files): array
    {
        $normalized = [];

        foreach ($files as $key => $value) {
            if (is_array($value['tmp_name'])) {
                $normalized[$key] = [];
                foreach ($value['tmp_name'] as $i => $tmpName) {
                    $normalized[$key][$i] = new UploadedFile(
                        $tmpName,
                        $value['size'][$i],
                        $value['error'][$i],
                        $value['name'][$i],
                        $value['type'][$i],
                    );
                }
            } else {
                $normalized[$key] = new UploadedFile(
                    $value['tmp_name'],
                    $value['size'],
                    $value['error'],
                    $value['name'],
                    $value['type'],
                );
            }
        }

        return $normalized;
    }
}
```

## UploadedFile

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Message;

use Psr\Http\Message\StreamInterface;
use Psr\Http\Message\UploadedFileInterface;
use RuntimeException;

final class UploadedFile implements UploadedFileInterface
{
    private bool $moved = false;

    public function __construct(
        private readonly string $tmpName,
        private readonly ?int $size,
        private readonly int $error,
        private readonly ?string $clientFilename = null,
        private readonly ?string $clientMediaType = null,
    ) {
    }

    public function getStream(): StreamInterface
    {
        if ($this->error !== UPLOAD_ERR_OK) {
            throw new RuntimeException('Cannot retrieve stream due to upload error');
        }

        if ($this->moved) {
            throw new RuntimeException('Cannot retrieve stream after file has been moved');
        }

        return new Stream(file_get_contents($this->tmpName));
    }

    public function moveTo(string $targetPath): void
    {
        if ($this->error !== UPLOAD_ERR_OK) {
            throw new RuntimeException('Cannot move file due to upload error');
        }

        if ($this->moved) {
            throw new RuntimeException('File has already been moved');
        }

        $dir = dirname($targetPath);
        if (!is_dir($dir)) {
            mkdir($dir, 0777, true);
        }

        if (!move_uploaded_file($this->tmpName, $targetPath)) {
            throw new RuntimeException('Failed to move uploaded file');
        }

        $this->moved = true;
    }

    public function getSize(): ?int
    {
        return $this->size;
    }

    public function getError(): int
    {
        return $this->error;
    }

    public function getClientFilename(): ?string
    {
        return $this->clientFilename;
    }

    public function getClientMediaType(): ?string
    {
        return $this->clientMediaType;
    }
}
```
