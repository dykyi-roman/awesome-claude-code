# Idempotency Handler Templates

## IdempotencyKey Value Object

**File:** `src/{architecture-path}/Idempotency/IdempotencyKey.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

final readonly class IdempotencyKey
{
    private const UUID_PATTERN = '/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i';

    public function __construct(
        public string $value
    ) {
        if (!preg_match(self::UUID_PATTERN, $this->value)) {
            throw new \InvalidArgumentException(
                sprintf('Idempotency key must be a valid UUID v4, got "%s"', $this->value)
            );
        }
    }

    public static function fromHeader(string $headerValue): self
    {
        return new self(trim($headerValue));
    }

    public function toString(): string
    {
        return $this->value;
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

---

## StoredResponse

**File:** `src/{architecture-path}/Idempotency/StoredResponse.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

final readonly class StoredResponse
{
    /**
     * @param array<string, list<string>> $headers
     */
    public function __construct(
        public int $statusCode,
        public array $headers,
        public string $body
    ) {}

    public function serialize(): string
    {
        return json_encode([
            'status_code' => $this->statusCode,
            'headers' => $this->headers,
            'body' => $this->body,
        ], JSON_THROW_ON_ERROR);
    }

    public static function deserialize(string $data): self
    {
        $decoded = json_decode($data, true, 512, JSON_THROW_ON_ERROR);

        return new self(
            statusCode: $decoded['status_code'],
            headers: $decoded['headers'],
            body: $decoded['body']
        );
    }
}
```

---

## IdempotencyException

**File:** `src/{architecture-path}/Idempotency/IdempotencyException.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

final class IdempotencyException extends \RuntimeException
{
    public function __construct(
        public readonly IdempotencyKey $key
    ) {
        parent::__construct(
            sprintf('Duplicate request detected for idempotency key "%s"', $key->value)
        );
    }

    public static function duplicateRequest(IdempotencyKey $key): self
    {
        return new self($key);
    }
}
```

---

## IdempotencyStorageInterface

**File:** `src/{architecture-path}/Idempotency/IdempotencyStorageInterface.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

interface IdempotencyStorageInterface
{
    public function exists(IdempotencyKey $key): bool;

    public function store(IdempotencyKey $key, StoredResponse $response, int $ttlSeconds): void;

    public function get(IdempotencyKey $key): ?StoredResponse;

    public function remove(IdempotencyKey $key): void;
}
```

---

## RedisIdempotencyStorage

**File:** `src/{architecture-path}/Idempotency/RedisIdempotencyStorage.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

final readonly class RedisIdempotencyStorage implements IdempotencyStorageInterface
{
    private const KEY_PREFIX = 'idempotency:';

    public function __construct(
        private \Redis $redis
    ) {}

    public function exists(IdempotencyKey $key): bool
    {
        return (bool) $this->redis->exists($this->buildKey($key));
    }

    public function store(IdempotencyKey $key, StoredResponse $response, int $ttlSeconds): void
    {
        $this->redis->setex(
            $this->buildKey($key),
            $ttlSeconds,
            $response->serialize()
        );
    }

    public function get(IdempotencyKey $key): ?StoredResponse
    {
        $data = $this->redis->get($this->buildKey($key));

        if ($data === false) {
            return null;
        }

        return StoredResponse::deserialize($data);
    }

    public function remove(IdempotencyKey $key): void
    {
        $this->redis->del($this->buildKey($key));
    }

    private function buildKey(IdempotencyKey $key): string
    {
        return self::KEY_PREFIX . $key->value;
    }
}
```

---

## IdempotencyMiddleware

**File:** `src/{architecture-path}/Idempotency/IdempotencyMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Idempotency;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class IdempotencyMiddleware implements MiddlewareInterface
{
    private const SAFE_METHODS = ['GET', 'HEAD', 'OPTIONS'];

    public function __construct(
        private IdempotencyStorageInterface $storage,
        private int $ttlSeconds = 86400,
        private string $headerName = 'Idempotency-Key'
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        if (in_array($request->getMethod(), self::SAFE_METHODS, true)) {
            return $handler->handle($request);
        }

        $headerValue = $request->getHeaderLine($this->headerName);

        if ($headerValue === '') {
            return $handler->handle($request);
        }

        $key = IdempotencyKey::fromHeader($headerValue);

        $cached = $this->storage->get($key);
        if ($cached !== null) {
            return $this->buildResponse($cached);
        }

        $response = $handler->handle($request);

        $stored = new StoredResponse(
            statusCode: $response->getStatusCode(),
            headers: $response->getHeaders(),
            body: (string) $response->getBody()
        );

        $this->storage->store($key, $stored, $this->ttlSeconds);

        return $response;
    }

    private function buildResponse(StoredResponse $stored): ResponseInterface
    {
        $response = new \Nyholm\Psr7\Response(
            $stored->statusCode,
            $stored->headers,
            $stored->body
        );

        return $response;
    }
}
```
