# Action Examples

Real-world Action examples.

## E-Commerce: Order Actions

### CreateOrderAction

```php
<?php

declare(strict_types=1);

namespace Action\Create;

use UseCase\CreateOrder\CreateOrderCommand;
use UseCase\CreateOrder\CreateOrderHandler;
use UseCase\CreateOrder\OrderItemDto;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderHandler $handler,
        private CreateOrderResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('user_id');
        $body = (array) $request->getParsedBody();

        $items = array_map(
            fn (array $item) => new OrderItemDto(
                productId: $item['product_id'] ?? '',
                quantity: (int) ($item['quantity'] ?? 0),
            ),
            $body['items'] ?? []
        );

        $command = new CreateOrderCommand(
            customerId: $userId,
            items: $items,
            shippingAddressId: $body['shipping_address_id'] ?? null,
            couponCode: $body['coupon_code'] ?? null,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

### CancelOrderAction

```php
<?php

declare(strict_types=1);

namespace Action\Cancel;

use UseCase\CancelOrder\CancelOrderCommand;
use UseCase\CancelOrder\CancelOrderHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CancelOrderAction
{
    public function __construct(
        private CancelOrderHandler $handler,
        private CancelOrderResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $orderId = $request->getAttribute('id');
        $userId = $request->getAttribute('user_id');
        $body = (array) $request->getParsedBody();

        $command = new CancelOrderCommand(
            orderId: $orderId,
            userId: $userId,
            reason: $body['reason'] ?? null,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Authentication: Login/Register

### RegisterAction

```php
<?php

declare(strict_types=1);

namespace Action\Register;

use UseCase\Register\RegisterCommand;
use UseCase\Register\RegisterHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class RegisterAction
{
    public function __construct(
        private RegisterHandler $handler,
        private RegisterResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        $command = new RegisterCommand(
            email: $body['email'] ?? '',
            password: $body['password'] ?? '',
            name: $body['name'] ?? '',
            acceptTerms: (bool) ($body['accept_terms'] ?? false),
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

### LoginAction

```php
<?php

declare(strict_types=1);

namespace Action\Login;

use UseCase\Login\LoginCommand;
use UseCase\Login\LoginHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class LoginAction
{
    public function __construct(
        private LoginHandler $handler,
        private LoginResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        $command = new LoginCommand(
            email: $body['email'] ?? '',
            password: $body['password'] ?? '',
            rememberMe: (bool) ($body['remember_me'] ?? false),
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Search with Filters

### SearchProductsAction

```php
<?php

declare(strict_types=1);

namespace Action\Search;

use UseCase\SearchProducts\SearchProductsQuery;
use UseCase\SearchProducts\SearchProductsHandler;
use UseCase\SearchProducts\PriceRange;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class SearchProductsAction
{
    public function __construct(
        private SearchProductsHandler $handler,
        private SearchProductsResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $params = $request->getQueryParams();

        $priceRange = isset($params['min_price'], $params['max_price'])
            ? new PriceRange(
                min: (float) $params['min_price'],
                max: (float) $params['max_price']
            )
            : null;

        $query = new SearchProductsQuery(
            keyword: $params['q'] ?? '',
            categoryId: $params['category'] ?? null,
            priceRange: $priceRange,
            sortBy: $params['sort'] ?? 'relevance',
            sortOrder: $params['order'] ?? 'desc',
            page: (int) ($params['page'] ?? 1),
            perPage: min((int) ($params['per_page'] ?? 20), 100),
        );

        $result = $this->handler->handle($query);

        return $this->responder->respond($result);
    }
}
```

## Webhook Handler

### StripeWebhookAction

```php
<?php

declare(strict_types=1);

namespace Action\Stripe;

use UseCase\ProcessStripeWebhook\ProcessStripeWebhookCommand;
use UseCase\ProcessStripeWebhook\ProcessStripeWebhookHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class StripeWebhookAction
{
    public function __construct(
        private ProcessStripeWebhookHandler $handler,
        private StripeWebhookResponder $responder,
        private string $webhookSecret,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $payload = (string) $request->getBody();
        $signature = $request->getHeaderLine('Stripe-Signature');

        $command = new ProcessStripeWebhookCommand(
            payload: $payload,
            signature: $signature,
            secret: $this->webhookSecret,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Bulk Operations

### BulkDeleteUsersAction

```php
<?php

declare(strict_types=1);

namespace Action\BulkDelete;

use UseCase\BulkDeleteUsers\BulkDeleteUsersCommand;
use UseCase\BulkDeleteUsers\BulkDeleteUsersHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class BulkDeleteUsersAction
{
    public function __construct(
        private BulkDeleteUsersHandler $handler,
        private BulkDeleteUsersResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();
        $adminId = $request->getAttribute('user_id');

        $userIds = array_filter(
            $body['user_ids'] ?? [],
            fn ($id) => is_string($id) && !empty($id)
        );

        $command = new BulkDeleteUsersCommand(
            userIds: $userIds,
            deletedBy: $adminId,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Export Action

### ExportReportAction

```php
<?php

declare(strict_types=1);

namespace Action\Export;

use UseCase\ExportReport\ExportReportQuery;
use UseCase\ExportReport\ExportReportHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class ExportReportAction
{
    public function __construct(
        private ExportReportHandler $handler,
        private ExportReportResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $params = $request->getQueryParams();

        $query = new ExportReportQuery(
            reportType: $params['type'] ?? 'sales',
            format: $params['format'] ?? 'csv',
            dateFrom: $params['from'] ?? null,
            dateTo: $params['to'] ?? null,
            filters: $params['filters'] ?? [],
        );

        $result = $this->handler->handle($query);

        return $this->responder->respond($result);
    }
}
```

## Full Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Action\Create;

use UseCase\CreateOrder\CreateOrderCommand;
use UseCase\CreateOrder\CreateOrderHandler;
use UseCase\CreateOrder\CreateOrderResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Action\Create\CreateOrderAction;
use Action\Create\CreateOrderResponder;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

#[Group('unit')]
#[CoversClass(CreateOrderAction::class)]
final class CreateOrderActionTest extends TestCase
{
    private CreateOrderHandler&MockObject $handler;
    private CreateOrderResponder&MockObject $responder;
    private CreateOrderAction $action;

    protected function setUp(): void
    {
        $this->handler = $this->createMock(CreateOrderHandler::class);
        $this->responder = $this->createMock(CreateOrderResponder::class);
        $this->action = new CreateOrderAction($this->handler, $this->responder);
    }

    public function testCreatesOrderWithItems(): void
    {
        $request = $this->createRequest(
            userId: 'user-123',
            body: [
                'items' => [
                    ['product_id' => 'prod-1', 'quantity' => 2],
                    ['product_id' => 'prod-2', 'quantity' => 1],
                ],
                'coupon_code' => 'SAVE10',
            ]
        );

        $result = CreateOrderResult::success('order-456');
        $response = $this->createMock(ResponseInterface::class);

        $this->handler
            ->expects($this->once())
            ->method('handle')
            ->with($this->callback(fn (CreateOrderCommand $cmd) =>
                $cmd->customerId === 'user-123' &&
                count($cmd->items) === 2 &&
                $cmd->couponCode === 'SAVE10'
            ))
            ->willReturn($result);

        $this->responder
            ->expects($this->once())
            ->method('respond')
            ->willReturn($response);

        ($this->action)($request);
    }

    public function testHandlesEmptyItems(): void
    {
        $request = $this->createRequest('user-123', []);

        $result = CreateOrderResult::failure('empty_cart', 'No items');
        $response = $this->createMock(ResponseInterface::class);

        $this->handler->method('handle')->willReturn($result);
        $this->responder->method('respond')->willReturn($response);

        ($this->action)($request);
    }

    private function createRequest(string $userId, array $body): ServerRequestInterface&MockObject
    {
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getAttribute')->with('user_id')->willReturn($userId);
        $request->method('getParsedBody')->willReturn($body);

        return $request;
    }
}
```
