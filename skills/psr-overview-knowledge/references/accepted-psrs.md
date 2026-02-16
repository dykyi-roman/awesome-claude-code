# Accepted PSR Standards

## PSR-1: Basic Coding Standard

**Purpose:** Ensures a high level of technical interoperability between shared PHP code.

**Key Points:**
- Files MUST use `<?php` or `<?=` tags only
- Files MUST use UTF-8 without BOM
- Files SHOULD declare symbols OR execute logic, not both
- Namespaces and classes MUST follow PSR-4
- Class names MUST be `StudlyCaps`
- Class constants MUST be `UPPER_CASE_WITH_UNDERSCORES`
- Method names MUST be `camelCase`

**Package:** Built into PHP_CodeSniffer

---

## PSR-3: Logger Interface

**Purpose:** Describes a common interface for logging libraries.

**Key Interfaces:**
```php
interface LoggerInterface {
    public function emergency(string|\Stringable $message, array $context = []): void;
    public function alert(string|\Stringable $message, array $context = []): void;
    public function critical(string|\Stringable $message, array $context = []): void;
    public function error(string|\Stringable $message, array $context = []): void;
    public function warning(string|\Stringable $message, array $context = []): void;
    public function notice(string|\Stringable $message, array $context = []): void;
    public function info(string|\Stringable $message, array $context = []): void;
    public function debug(string|\Stringable $message, array $context = []): void;
    public function log(mixed $level, string|\Stringable $message, array $context = []): void;
}

interface LoggerAwareInterface {
    public function setLogger(LoggerInterface $logger): void;
}
```

**Log Levels (RFC 5424):**
1. Emergency - System is unusable
2. Alert - Action must be taken immediately
3. Critical - Critical conditions
4. Error - Error conditions
5. Warning - Warning conditions
6. Notice - Normal but significant
7. Info - Informational messages
8. Debug - Debug-level messages

**Package:** `psr/log`

---

## PSR-4: Autoloader

**Purpose:** Describes a specification for autoloading classes from file paths.

**Key Rules:**
- FQCN = `\<Namespace>\(<SubNamespace>)*\<ClassName>`
- Namespace prefix maps to base directory
- Subsequent namespace maps to subdirectories
- Class name maps to filename.php

**Example:**
```
Namespace Prefix    Base Directory    FQCN                         File Path
App\               src/              App\Domain\User\Entity\User  src/Domain/User/Entity/User.php
```

**Package:** Composer built-in

---

## PSR-6: Caching Interface

**Purpose:** Describes a common interface for caching systems with cache pools.

**Key Interfaces:**
```php
interface CacheItemPoolInterface {
    public function getItem(string $key): CacheItemInterface;
    public function getItems(array $keys = []): iterable;
    public function hasItem(string $key): bool;
    public function clear(): bool;
    public function deleteItem(string $key): bool;
    public function deleteItems(array $keys): bool;
    public function save(CacheItemInterface $item): bool;
    public function saveDeferred(CacheItemInterface $item): bool;
    public function commit(): bool;
}

interface CacheItemInterface {
    public function getKey(): string;
    public function get(): mixed;
    public function isHit(): bool;
    public function set(mixed $value): static;
    public function expiresAt(?DateTimeInterface $expiration): static;
    public function expiresAfter(int|DateInterval|null $time): static;
}
```

**Package:** `psr/cache`

---

## PSR-7: HTTP Message Interface

**Purpose:** Describes common interfaces for representing HTTP messages.

**Key Interfaces:**
```php
interface MessageInterface {
    public function getProtocolVersion(): string;
    public function withProtocolVersion(string $version): static;
    public function getHeaders(): array;
    public function hasHeader(string $name): bool;
    public function getHeader(string $name): array;
    public function getHeaderLine(string $name): string;
    public function withHeader(string $name, $value): static;
    public function withAddedHeader(string $name, $value): static;
    public function withoutHeader(string $name): static;
    public function getBody(): StreamInterface;
    public function withBody(StreamInterface $body): static;
}

interface RequestInterface extends MessageInterface {
    public function getRequestTarget(): string;
    public function withRequestTarget(string $requestTarget): static;
    public function getMethod(): string;
    public function withMethod(string $method): static;
    public function getUri(): UriInterface;
    public function withUri(UriInterface $uri, bool $preserveHost = false): static;
}

interface ResponseInterface extends MessageInterface {
    public function getStatusCode(): int;
    public function withStatus(int $code, string $reasonPhrase = ''): static;
    public function getReasonPhrase(): string;
}
```

**Package:** `psr/http-message`

---

## PSR-11: Container Interface

**Purpose:** Describes a common interface for dependency injection containers.

**Key Interfaces:**
```php
interface ContainerInterface {
    public function get(string $id): mixed;
    public function has(string $id): bool;
}

interface ContainerExceptionInterface extends Throwable { }
interface NotFoundExceptionInterface extends ContainerExceptionInterface { }
```

**Package:** `psr/container`

---

## PSR-12: Extended Coding Style

**Purpose:** Extends PSR-1 with more detailed formatting rules.

**Key Points:**
- 4 spaces for indentation (no tabs)
- Line length SHOULD be ≤120 characters
- Keywords MUST be lowercase (`true`, `false`, `null`)
- Type declarations MUST be short form (`int`, `bool`)
- Opening brace for classes on new line
- Opening brace for methods on new line
- Opening brace for control structures on same line
- One blank line before `return` statements (optional)

**Package:** Built into PHP_CodeSniffer, PHP-CS-Fixer

---

## PSR-13: Hypermedia Links

**Purpose:** Describes common interfaces for representing hypermedia links.

**Key Interfaces:**
```php
interface LinkInterface {
    public function getHref(): string;
    public function isTemplated(): bool;
    public function getRels(): array;
    public function getAttributes(): array;
}

interface EvolvableLinkInterface extends LinkInterface {
    public function withHref(string|\Stringable $href): static;
    public function withRel(string $rel): static;
    public function withoutRel(string $rel): static;
    public function withAttribute(string $attribute, string|\Stringable $value): static;
    public function withoutAttribute(string $attribute): static;
}

interface LinkProviderInterface {
    public function getLinks(): iterable;
    public function getLinksByRel(string $rel): iterable;
}
```

**Package:** `psr/link`

---

## PSR-14: Event Dispatcher

**Purpose:** Describes a common mechanism for event dispatching.

**Key Interfaces:**
```php
interface EventDispatcherInterface {
    public function dispatch(object $event): object;
}

interface ListenerProviderInterface {
    public function getListenersForEvent(object $event): iterable;
}

interface StoppableEventInterface {
    public function isPropagationStopped(): bool;
}
```

**Package:** `psr/event-dispatcher`

---

## PSR-15: HTTP Server Request Handlers

**Purpose:** Describes common interfaces for HTTP server request handlers.

**Key Interfaces:**
```php
interface RequestHandlerInterface {
    public function handle(ServerRequestInterface $request): ResponseInterface;
}

interface MiddlewareInterface {
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface;
}
```

**Package:** `psr/http-server-handler`, `psr/http-server-middleware`

---

## PSR-16: Simple Cache

**Purpose:** Describes a simple interface for caching libraries.

**Key Interfaces:**
```php
interface CacheInterface {
    public function get(string $key, mixed $default = null): mixed;
    public function set(string $key, mixed $value, null|int|DateInterval $ttl = null): bool;
    public function delete(string $key): bool;
    public function clear(): bool;
    public function getMultiple(iterable $keys, mixed $default = null): iterable;
    public function setMultiple(iterable $values, null|int|DateInterval $ttl = null): bool;
    public function deleteMultiple(iterable $keys): bool;
    public function has(string $key): bool;
}
```

**Package:** `psr/simple-cache`

---

## PSR-17: HTTP Factories

**Purpose:** Describes a common standard for factories that create PSR-7 objects.

**Key Interfaces:**
```php
interface RequestFactoryInterface {
    public function createRequest(string $method, $uri): RequestInterface;
}

interface ResponseFactoryInterface {
    public function createResponse(int $code = 200, string $reasonPhrase = ''): ResponseInterface;
}

interface ServerRequestFactoryInterface {
    public function createServerRequest(string $method, $uri, array $serverParams = []): ServerRequestInterface;
}

interface StreamFactoryInterface {
    public function createStream(string $content = ''): StreamInterface;
    public function createStreamFromFile(string $filename, string $mode = 'r'): StreamInterface;
    public function createStreamFromResource($resource): StreamInterface;
}

interface UploadedFileFactoryInterface {
    public function createUploadedFile(
        StreamInterface $stream,
        ?int $size = null,
        int $error = UPLOAD_ERR_OK,
        ?string $clientFilename = null,
        ?string $clientMediaType = null
    ): UploadedFileInterface;
}

interface UriFactoryInterface {
    public function createUri(string $uri = ''): UriInterface;
}
```

**Package:** `psr/http-factory`

---

## PSR-18: HTTP Client

**Purpose:** Describes a common interface for sending HTTP requests.

**Key Interfaces:**
```php
interface ClientInterface {
    public function sendRequest(RequestInterface $request): ResponseInterface;
}

interface ClientExceptionInterface extends Throwable { }
interface RequestExceptionInterface extends ClientExceptionInterface {
    public function getRequest(): RequestInterface;
}
interface NetworkExceptionInterface extends ClientExceptionInterface {
    public function getRequest(): RequestInterface;
}
```

**Package:** `psr/http-client`

---

## PSR-20: Clock

**Purpose:** Describes a common interface for reading the system clock.

**Key Interfaces:**
```php
interface ClockInterface {
    public function now(): DateTimeImmutable;
}
```

**Use Cases:**
- Testing time-dependent code
- Mocking current time
- Consistent time across application

**Package:** `psr/clock`
