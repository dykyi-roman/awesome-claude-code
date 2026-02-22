# Idempotency Handler Examples

## Order Creation with Idempotency

**File:** `src/Presentation/Api/Order/CreateOrderAction.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Application\Order\CreateOrderUseCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $data = $request->getParsedBody();

        $result = $this->createOrder->execute(
            new CreateOrderRequest(
                customerId: $data['customer_id'],
                items: $data['items'],
                total: $data['total']
            )
        );

        return new \Nyholm\Psr7\Response(
            201,
            ['Content-Type' => 'application/json'],
            json_encode(['order_id' => $result->orderId], JSON_THROW_ON_ERROR)
        );
    }
}
```

---

## Middleware Registration

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Http;

use Infrastructure\Idempotency\IdempotencyMiddleware;
use Infrastructure\Idempotency\RedisIdempotencyStorage;

final readonly class MiddlewarePipeline
{
    public static function configure(\Redis $redis): array
    {
        $storage = new RedisIdempotencyStorage($redis);

        return [
            new IdempotencyMiddleware(
                storage: $storage,
                ttlSeconds: 86400,
                headerName: 'Idempotency-Key'
            ),
        ];
    }
}
```

---

## Payment Webhook Deduplication

**File:** `src/Presentation/Api/Webhook/PaymentWebhookAction.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Webhook;

use Infrastructure\Idempotency\IdempotencyKey;
use Infrastructure\Idempotency\IdempotencyStorageInterface;
use Infrastructure\Idempotency\StoredResponse;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class PaymentWebhookAction
{
    public function __construct(
        private IdempotencyStorageInterface $storage,
        private PaymentWebhookHandler $handler
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $eventId = $request->getParsedBody()['event_id'] ?? '';
        $key = new IdempotencyKey($eventId);

        if ($this->storage->exists($key)) {
            return new \Nyholm\Psr7\Response(200, [], '{"status":"already_processed"}');
        }

        $result = $this->handler->handle($request);

        $this->storage->store(
            $key,
            new StoredResponse(200, [], json_encode($result, JSON_THROW_ON_ERROR)),
            ttlSeconds: 604800
        );

        return new \Nyholm\Psr7\Response(200, [], json_encode($result, JSON_THROW_ON_ERROR));
    }
}
```

---

## Unit Tests

### IdempotencyKeyTest

**File:** `tests/Unit/Infrastructure/Idempotency/IdempotencyKeyTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Idempotency;

use Infrastructure\Idempotency\IdempotencyKey;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(IdempotencyKey::class)]
final class IdempotencyKeyTest extends TestCase
{
    public function testAcceptsValidUuidV4(): void
    {
        $key = new IdempotencyKey('550e8400-e29b-41d4-a716-446655440000');

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $key->value);
    }

    public function testRejectsInvalidFormat(): void
    {
        $this->expectException(\InvalidArgumentException::class);

        new IdempotencyKey('not-a-uuid');
    }

    public function testFromHeaderTrimsWhitespace(): void
    {
        $key = IdempotencyKey::fromHeader('  550e8400-e29b-41d4-a716-446655440000  ');

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $key->value);
    }

    public function testEquality(): void
    {
        $key1 = new IdempotencyKey('550e8400-e29b-41d4-a716-446655440000');
        $key2 = new IdempotencyKey('550e8400-e29b-41d4-a716-446655440000');

        self::assertTrue($key1->equals($key2));
    }

    public function testToString(): void
    {
        $key = new IdempotencyKey('550e8400-e29b-41d4-a716-446655440000');

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $key->toString());
    }
}
```

---

### IdempotencyMiddlewareTest

**File:** `tests/Unit/Infrastructure/Idempotency/IdempotencyMiddlewareTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Infrastructure\Idempotency;

use Infrastructure\Idempotency\IdempotencyMiddleware;
use Infrastructure\Idempotency\IdempotencyStorageInterface;
use Infrastructure\Idempotency\StoredResponse;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

#[Group('unit')]
#[CoversClass(IdempotencyMiddleware::class)]
final class IdempotencyMiddlewareTest extends TestCase
{
    public function testSkipsSafeMethodsWithoutIdempotencyCheck(): void
    {
        $storage = $this->createMock(IdempotencyStorageInterface::class);
        $storage->expects(self::never())->method('exists');

        $middleware = new IdempotencyMiddleware($storage);
        $request = $this->createGetRequest();
        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->expects(self::once())->method('handle');

        $middleware->process($request, $handler);
    }

    public function testPassesThroughWhenNoIdempotencyHeader(): void
    {
        $storage = $this->createMock(IdempotencyStorageInterface::class);
        $middleware = new IdempotencyMiddleware($storage);

        $request = $this->createPostRequest('');
        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->expects(self::once())->method('handle');

        $middleware->process($request, $handler);
    }

    public function testReturnsCachedResponseOnDuplicate(): void
    {
        $stored = new StoredResponse(201, ['Content-Type' => ['application/json']], '{"id":1}');
        $storage = $this->createMock(IdempotencyStorageInterface::class);
        $storage->method('get')->willReturn($stored);

        $middleware = new IdempotencyMiddleware($storage);
        $request = $this->createPostRequest('550e8400-e29b-41d4-a716-446655440000');
        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->expects(self::never())->method('handle');

        $response = $middleware->process($request, $handler);

        self::assertSame(201, $response->getStatusCode());
    }

    private function createGetRequest(): ServerRequestInterface
    {
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getMethod')->willReturn('GET');
        return $request;
    }

    private function createPostRequest(string $idempotencyKey): ServerRequestInterface
    {
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getMethod')->willReturn('POST');
        $request->method('getHeaderLine')->willReturn($idempotencyKey);
        return $request;
    }
}
```
