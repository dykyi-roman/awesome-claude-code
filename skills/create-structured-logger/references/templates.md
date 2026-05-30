# Structured Logger Templates

## CorrelationId Value Object

**File:** `src/{architecture-path}/Logging/CorrelationId.php`

```php
<?php

declare(strict_types=1);

namespace Logging;

final readonly class CorrelationId
{
    private const UUID_PATTERN = '/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i';

    public function __construct(
        public string $value
    ) {
        if (!preg_match(self::UUID_PATTERN, $this->value)) {
            throw new \InvalidArgumentException(
                sprintf('Correlation ID must be a valid UUID v4, got "%s"', $this->value)
            );
        }
    }

    public static function generate(): self
    {
        return new self(sprintf(
            '%04x%04x-%04x-%04x-%04x-%04x%04x%04x',
            random_int(0, 0xffff), random_int(0, 0xffff),
            random_int(0, 0xffff),
            random_int(0, 0x0fff) | 0x4000,
            random_int(0, 0x3fff) | 0x8000,
            random_int(0, 0xffff), random_int(0, 0xffff), random_int(0, 0xffff)
        ));
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

## CorrelationIdHolder

**File:** `src/{architecture-path}/Logging/CorrelationIdHolder.php`

```php
<?php

declare(strict_types=1);

namespace Logging;

final class CorrelationIdHolder
{
    private static ?CorrelationId $current = null;

    public static function set(CorrelationId $correlationId): void
    {
        self::$current = $correlationId;
    }

    public static function get(): ?CorrelationId
    {
        return self::$current;
    }

    public static function getOrGenerate(): CorrelationId
    {
        if (self::$current === null) {
            self::$current = CorrelationId::generate();
        }

        return self::$current;
    }

    public static function reset(): void
    {
        self::$current = null;
    }
}
```

---

## CorrelationIdProcessor

**File:** `src/{architecture-path}/Logging/Processor/CorrelationIdProcessor.php`

```php
<?php

declare(strict_types=1);

namespace Logging\Processor;

use Logging\CorrelationIdHolder;
use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

final readonly class CorrelationIdProcessor implements ProcessorInterface
{
    public function __invoke(LogRecord $record): LogRecord
    {
        $correlationId = CorrelationIdHolder::get();

        if ($correlationId === null) {
            return $record;
        }

        return $record->with(
            extra: array_merge($record->extra, [
                'correlation_id' => $correlationId->toString(),
            ])
        );
    }
}
```

---

## RequestContextProcessor

**File:** `src/{architecture-path}/Logging/Processor/RequestContextProcessor.php`

```php
<?php

declare(strict_types=1);

namespace Logging\Processor;

use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;
use Psr\Http\Message\ServerRequestInterface;

final class RequestContextProcessor implements ProcessorInterface
{
    private ?ServerRequestInterface $request = null;

    public function setRequest(ServerRequestInterface $request): void
    {
        $this->request = $request;
    }

    public function __invoke(LogRecord $record): LogRecord
    {
        if ($this->request === null) {
            return $record;
        }

        $serverParams = $this->request->getServerParams();

        return $record->with(
            extra: array_merge($record->extra, [
                'http_method' => $this->request->getMethod(),
                'uri' => (string) $this->request->getUri(),
                'ip' => $serverParams['REMOTE_ADDR'] ?? 'unknown',
                'user_agent' => $this->request->getHeaderLine('User-Agent'),
            ])
        );
    }

    public function reset(): void
    {
        $this->request = null;
    }
}
```

---

## CorrelationIdMiddleware

**File:** `src/{architecture-path}/Logging/CorrelationIdMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Logging;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CorrelationIdMiddleware implements MiddlewareInterface
{
    public function __construct(
        private string $headerName = 'X-Request-ID'
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler
    ): ResponseInterface {
        $headerValue = $request->getHeaderLine($this->headerName);

        $correlationId = $headerValue !== ''
            ? new CorrelationId($headerValue)
            : CorrelationId::generate();

        CorrelationIdHolder::set($correlationId);

        try {
            $response = $handler->handle($request);

            return $response->withHeader(
                $this->headerName,
                $correlationId->toString()
            );
        } finally {
            CorrelationIdHolder::reset();
        }
    }
}
```
