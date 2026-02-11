# Correlation Context — Templates

Complete PHP 8.5 implementations for all Correlation Context components.

---

## Domain Layer

### CorrelationId Value Object

```php
<?php

declare(strict_types=1);

namespace App\Domain\Shared\Correlation;

final readonly class CorrelationId implements \Stringable, \JsonSerializable
{
    public function __construct(
        public string $value,
    ) {
        if ($value === '') {
            throw new \InvalidArgumentException('Correlation ID cannot be empty.');
        }
    }

    public static function generate(): self
    {
        return new self(uuid_create(UUID_TYPE_RANDOM));
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }

    public function __toString(): string
    {
        return $this->value;
    }

    public function jsonSerialize(): string
    {
        return $this->value;
    }
}
```

### CorrelationContext

```php
<?php

declare(strict_types=1);

namespace App\Domain\Shared\Correlation;

use Psr\Http\Message\ServerRequestInterface;

final readonly class CorrelationContext
{
    private const string HEADER_CORRELATION_ID = 'X-Correlation-ID';
    private const string HEADER_CAUSATION_ID = 'X-Causation-ID';

    public function __construct(
        public CorrelationId $correlationId,
        public ?string $causationId = null,
        public ?string $userId = null,
    ) {
    }

    public static function create(): self
    {
        return new self(
            correlationId: CorrelationId::generate(),
        );
    }

    public static function fromRequest(ServerRequestInterface $request): self
    {
        $correlationHeader = $request->getHeaderLine(self::HEADER_CORRELATION_ID);
        $causationHeader = $request->getHeaderLine(self::HEADER_CAUSATION_ID);

        return new self(
            correlationId: $correlationHeader !== ''
                ? new CorrelationId($correlationHeader)
                : CorrelationId::generate(),
            causationId: $causationHeader !== '' ? $causationHeader : null,
        );
    }

    public function withCausationId(string $causationId): self
    {
        return new self(
            correlationId: $this->correlationId,
            causationId: $causationId,
            userId: $this->userId,
        );
    }

    public function withUserId(string $userId): self
    {
        return new self(
            correlationId: $this->correlationId,
            causationId: $this->causationId,
            userId: $userId,
        );
    }

    /** @return array{correlation_id: string, causation_id: ?string, user_id: ?string} */
    public function toArray(): array
    {
        return [
            'correlation_id' => $this->correlationId->value,
            'causation_id' => $this->causationId,
            'user_id' => $this->userId,
        ];
    }
}
```

---

## Presentation Layer

### CorrelationContextMiddleware (PSR-15)

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Middleware;

use App\Domain\Shared\Correlation\CorrelationContext;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CorrelationContextMiddleware implements MiddlewareInterface
{
    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        $context = CorrelationContext::fromRequest($request);

        $request = $request->withAttribute(CorrelationContext::class, $context);

        $response = $handler->handle($request);

        return $response->withHeader(
            'X-Correlation-ID',
            $context->correlationId->value,
        );
    }
}
```

---

## Infrastructure Layer

### CorrelationLogProcessor (Monolog)

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Logging;

use App\Domain\Shared\Correlation\CorrelationContext;
use Monolog\LogRecord;
use Monolog\Processor\ProcessorInterface;

final class CorrelationLogProcessor implements ProcessorInterface
{
    private ?CorrelationContext $context = null;

    public function setContext(CorrelationContext $context): void
    {
        $this->context = $context;
    }

    public function __invoke(LogRecord $record): LogRecord
    {
        if ($this->context === null) {
            return $record;
        }

        return $record->with(
            extra: array_merge($record->extra, [
                'correlation_id' => $this->context->correlationId->value,
                'causation_id' => $this->context->causationId,
            ]),
        );
    }
}
```

### CorrelationMessageStamp

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Messaging;

use App\Domain\Shared\Correlation\CorrelationId;
use Symfony\Component\Messenger\Stamp\StampInterface;

final readonly class CorrelationMessageStamp implements StampInterface
{
    public function __construct(
        public string $correlationId,
        public ?string $causationId = null,
    ) {
    }

    public static function fromContext(\App\Domain\Shared\Correlation\CorrelationContext $context): self
    {
        return new self(
            correlationId: $context->correlationId->value,
            causationId: $context->causationId,
        );
    }

    /** @return array{correlationId: string, causationId: ?string} */
    public function toAmqpHeaders(): array
    {
        return [
            'correlationId' => $this->correlationId,
            'causationId' => $this->causationId,
        ];
    }

    public static function fromAmqpHeaders(array $headers): self
    {
        return new self(
            correlationId: $headers['correlationId'] ?? CorrelationId::generate()->value,
            causationId: $headers['causationId'] ?? null,
        );
    }
}
```

---

## Tests

### CorrelationIdTest

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Correlation;

use App\Domain\Shared\Correlation\CorrelationId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CorrelationId::class)]
final class CorrelationIdTest extends TestCase
{
    public function testGenerate(): void
    {
        $id = CorrelationId::generate();

        self::assertNotEmpty($id->value);
    }

    public function testEquals(): void
    {
        $id1 = new CorrelationId('abc-123');
        $id2 = new CorrelationId('abc-123');
        $id3 = new CorrelationId('def-456');

        self::assertTrue($id1->equals($id2));
        self::assertFalse($id1->equals($id3));
    }

    public function testToString(): void
    {
        $id = new CorrelationId('abc-123');

        self::assertSame('abc-123', (string) $id);
    }

    public function testJsonSerialize(): void
    {
        $id = new CorrelationId('abc-123');

        self::assertSame('"abc-123"', json_encode($id, JSON_THROW_ON_ERROR));
    }

    public function testEmptyValueThrowsException(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new CorrelationId('');
    }
}
```

### CorrelationContextTest

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Correlation;

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Domain\Shared\Correlation\CorrelationId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CorrelationContext::class)]
final class CorrelationContextTest extends TestCase
{
    public function testCreate(): void
    {
        $context = CorrelationContext::create();

        self::assertNotEmpty($context->correlationId->value);
        self::assertNull($context->causationId);
        self::assertNull($context->userId);
    }

    public function testWithCausationIdReturnsNewInstance(): void
    {
        $context = CorrelationContext::create();
        $withCausation = $context->withCausationId('cmd-123');

        self::assertNull($context->causationId);
        self::assertSame('cmd-123', $withCausation->causationId);
        self::assertTrue($context->correlationId->equals($withCausation->correlationId));
    }

    public function testWithUserIdReturnsNewInstance(): void
    {
        $context = CorrelationContext::create();
        $withUser = $context->withUserId('user-42');

        self::assertNull($context->userId);
        self::assertSame('user-42', $withUser->userId);
    }

    public function testToArray(): void
    {
        $context = new CorrelationContext(
            correlationId: new CorrelationId('corr-1'),
            causationId: 'cause-1',
            userId: 'user-1',
        );

        self::assertSame([
            'correlation_id' => 'corr-1',
            'causation_id' => 'cause-1',
            'user_id' => 'user-1',
        ], $context->toArray());
    }
}
```

### CorrelationContextMiddlewareTest

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Middleware;

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Presentation\Middleware\CorrelationContextMiddleware;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

#[Group('unit')]
#[CoversClass(CorrelationContextMiddleware::class)]
final class CorrelationContextMiddlewareTest extends TestCase
{
    public function testGeneratesCorrelationIdWhenMissing(): void
    {
        $middleware = new CorrelationContextMiddleware();
        $request = $this->createMock(ServerRequestInterface::class);
        $response = $this->createMock(ResponseInterface::class);
        $handler = $this->createMock(RequestHandlerInterface::class);

        $request->method('getHeaderLine')
            ->willReturn('');
        $request->method('withAttribute')
            ->willReturnCallback(function (string $name, CorrelationContext $ctx) use ($request) {
                self::assertSame(CorrelationContext::class, $name);
                self::assertNotEmpty($ctx->correlationId->value);
                return $request;
            });
        $handler->method('handle')->willReturn($response);
        $response->method('withHeader')->willReturn($response);

        $middleware->process($request, $handler);
    }

    public function testPreservesExistingCorrelationId(): void
    {
        $middleware = new CorrelationContextMiddleware();
        $request = $this->createMock(ServerRequestInterface::class);
        $response = $this->createMock(ResponseInterface::class);
        $handler = $this->createMock(RequestHandlerInterface::class);

        $request->method('getHeaderLine')
            ->willReturnMap([
                ['X-Correlation-ID', 'existing-id'],
                ['X-Causation-ID', ''],
            ]);
        $request->method('withAttribute')
            ->willReturnCallback(function (string $name, CorrelationContext $ctx) use ($request) {
                self::assertSame('existing-id', $ctx->correlationId->value);
                return $request;
            });
        $handler->method('handle')->willReturn($response);
        $response->method('withHeader')
            ->with('X-Correlation-ID', 'existing-id')
            ->willReturn($response);

        $middleware->process($request, $handler);
    }
}
```

### CorrelationLogProcessorTest

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Logging;

use App\Domain\Shared\Correlation\CorrelationContext;
use App\Domain\Shared\Correlation\CorrelationId;
use App\Infrastructure\Logging\CorrelationLogProcessor;
use Monolog\Level;
use Monolog\LogRecord;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CorrelationLogProcessor::class)]
final class CorrelationLogProcessorTest extends TestCase
{
    public function testAddsCorrelationIdToLogRecord(): void
    {
        $processor = new CorrelationLogProcessor();
        $processor->setContext(new CorrelationContext(
            correlationId: new CorrelationId('test-corr-id'),
            causationId: 'test-cause-id',
        ));

        $record = new LogRecord(
            datetime: new \DateTimeImmutable(),
            channel: 'app',
            level: Level::Info,
            message: 'Test message',
        );

        $result = $processor($record);

        self::assertSame('test-corr-id', $result->extra['correlation_id']);
        self::assertSame('test-cause-id', $result->extra['causation_id']);
    }

    public function testSkipsWhenNoContext(): void
    {
        $processor = new CorrelationLogProcessor();

        $record = new LogRecord(
            datetime: new \DateTimeImmutable(),
            channel: 'app',
            level: Level::Info,
            message: 'Test message',
        );

        $result = $processor($record);

        self::assertArrayNotHasKey('correlation_id', $result->extra);
    }
}
```
