# Structured Logger Examples

## Logger Factory Setup

**File:** `src/Infrastructure/Logging/LoggerFactory.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Logging;

use Infrastructure\Logging\Processor\CorrelationIdProcessor;
use Infrastructure\Logging\Processor\RequestContextProcessor;
use Monolog\Formatter\JsonFormatter;
use Monolog\Handler\StreamHandler;
use Monolog\Logger;
use Psr\Log\LoggerInterface;

final readonly class LoggerFactory
{
    public function __construct(
        private RequestContextProcessor $requestContextProcessor
    ) {}

    public function create(string $channel): LoggerInterface
    {
        $handler = new StreamHandler('php://stdout');
        $handler->setFormatter(new JsonFormatter());

        $logger = new Logger($channel);
        $logger->pushHandler($handler);
        $logger->pushProcessor(new CorrelationIdProcessor());
        $logger->pushProcessor($this->requestContextProcessor);

        return $logger;
    }
}
```

---

## Service Using Structured Logger

**File:** `src/Application/Order/CreateOrderUseCase.php`

```php
<?php

declare(strict_types=1);

namespace Application\Order;

use Psr\Log\LoggerInterface;

final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orderRepository,
        private LoggerInterface $logger
    ) {}

    public function execute(CreateOrderRequest $request): CreateOrderResponse
    {
        $this->logger->info('Creating order', [
            'customer_id' => $request->customerId,
            'item_count' => count($request->items),
        ]);

        $order = Order::create($request);
        $this->orderRepository->save($order);

        $this->logger->info('Order created', [
            'order_id' => $order->id()->toString(),
            'total' => $order->total()->amount(),
        ]);

        return new CreateOrderResponse($order->id()->toString());
    }
}
```

---

## Middleware Pipeline Registration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Logging\CorrelationIdMiddleware;
use Infrastructure\Logging\Processor\RequestContextProcessor;

final readonly class MiddlewarePipeline
{
    public static function configure(RequestContextProcessor $requestProcessor): array
    {
        return [
            new CorrelationIdMiddleware(headerName: 'X-Request-ID'),
            new RequestContextMiddleware($requestProcessor),
        ];
    }
}
```

---

## Unit Tests

### CorrelationIdTest

**File:** `tests/Unit/Infrastructure/Logging/CorrelationIdTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Logging;

use Infrastructure\Logging\CorrelationId;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CorrelationId::class)]
final class CorrelationIdTest extends TestCase
{
    public function testAcceptsValidUuidV4(): void
    {
        $id = new CorrelationId('550e8400-e29b-41d4-a716-446655440000');

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $id->value);
    }

    public function testRejectsInvalidFormat(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new CorrelationId('invalid-uuid');
    }

    public function testGeneratesValidUuid(): void
    {
        $id = CorrelationId::generate();

        self::assertMatchesRegularExpression(
            '/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i',
            $id->value
        );
    }

    public function testEquality(): void
    {
        $id1 = new CorrelationId('550e8400-e29b-41d4-a716-446655440000');
        $id2 = new CorrelationId('550e8400-e29b-41d4-a716-446655440000');

        self::assertTrue($id1->equals($id2));
    }

    public function testToString(): void
    {
        $id = new CorrelationId('550e8400-e29b-41d4-a716-446655440000');

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $id->toString());
    }
}
```

---

### CorrelationIdProcessorTest

**File:** `tests/Unit/Infrastructure/Logging/Processor/CorrelationIdProcessorTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Logging\Processor;

use Infrastructure\Logging\CorrelationId;
use Infrastructure\Logging\CorrelationIdHolder;
use Infrastructure\Logging\Processor\CorrelationIdProcessor;
use Monolog\Level;
use Monolog\LogRecord;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CorrelationIdProcessor::class)]
final class CorrelationIdProcessorTest extends TestCase
{
    protected function tearDown(): void
    {
        CorrelationIdHolder::reset();
    }

    public function testAddsCorrelationIdToRecord(): void
    {
        $correlationId = new CorrelationId('550e8400-e29b-41d4-a716-446655440000');
        CorrelationIdHolder::set($correlationId);

        $processor = new CorrelationIdProcessor();
        $record = new LogRecord(
            datetime: new \DateTimeImmutable(),
            channel: 'test',
            level: Level::Info,
            message: 'test message'
        );

        $result = $processor($record);

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $result->extra['correlation_id']);
    }

    public function testReturnsUnmodifiedRecordWhenNoCorrelationId(): void
    {
        $processor = new CorrelationIdProcessor();
        $record = new LogRecord(
            datetime: new \DateTimeImmutable(),
            channel: 'test',
            level: Level::Info,
            message: 'test message'
        );

        $result = $processor($record);

        self::assertArrayNotHasKey('correlation_id', $result->extra);
    }
}
```

---

### CorrelationIdMiddlewareTest

**File:** `tests/Unit/Infrastructure/Logging/CorrelationIdMiddlewareTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Logging;

use Infrastructure\Logging\CorrelationIdMiddleware;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

#[Group('unit')]
#[CoversClass(CorrelationIdMiddleware::class)]
final class CorrelationIdMiddlewareTest extends TestCase
{
    public function testUsesExistingRequestIdHeader(): void
    {
        $middleware = new CorrelationIdMiddleware();
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getHeaderLine')
            ->with('X-Request-ID')
            ->willReturn('550e8400-e29b-41d4-a716-446655440000');

        $response = $this->createMock(ResponseInterface::class);
        $response->method('withHeader')->willReturnSelf();

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($response);

        $result = $middleware->process($request, $handler);

        self::assertSame($response, $result);
    }

    public function testGeneratesCorrelationIdWhenMissing(): void
    {
        $middleware = new CorrelationIdMiddleware();
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getHeaderLine')->willReturn('');

        $response = $this->createMock(ResponseInterface::class);
        $response->expects(self::once())
            ->method('withHeader')
            ->with('X-Request-ID', self::matchesRegularExpression('/^[0-9a-f-]{36}$/'))
            ->willReturnSelf();

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($response);

        $middleware->process($request, $handler);
    }
}
```
