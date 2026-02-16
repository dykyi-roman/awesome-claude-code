# Responder Examples

Real-world Responder examples.

## E-Commerce: Order Responders

### CreateOrderResponder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Create;

use Application\Order\UseCase\CreateOrder\CreateOrderResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class CreateOrderResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof CreateOrderResult);

        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'empty_cart' => $this->badRequest('Cannot create order with empty cart'),
                'insufficient_stock' => $this->conflict('Some items are out of stock'),
                'invalid_coupon' => $this->unprocessableEntity([
                    ['field' => 'coupon_code', 'messages' => [$result->errorMessage()]],
                ]),
                'address_not_found' => $this->notFound('Shipping address not found'),
                default => $this->badRequest($result->errorMessage()),
            };
        }

        $order = $result->order();

        return $this->created([
            'id' => $order->id()->toString(),
            'status' => $order->status()->value,
            'total' => [
                'amount' => $order->total()->amount(),
                'currency' => $order->total()->currency(),
            ],
            'items' => array_map(
                fn ($item) => [
                    'product_id' => $item->productId()->toString(),
                    'quantity' => $item->quantity(),
                    'unit_price' => $item->unitPrice()->amount(),
                ],
                $order->items()
            ),
            'created_at' => $order->createdAt()->format('c'),
        ]);
    }
}
```

### GetOrderByIdResponder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\GetById;

use Application\Order\UseCase\GetOrderById\GetOrderByIdResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class GetOrderByIdResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof GetOrderByIdResult);

        if ($result->isNotFound()) {
            return $this->notFound('Order not found');
        }

        if ($result->isForbidden()) {
            return $this->forbidden('You do not have access to this order');
        }

        $order = $result->order();

        return $this->json([
            'id' => $order->id()->toString(),
            'status' => $order->status()->value,
            'customer' => [
                'id' => $order->customerId()->toString(),
                'name' => $order->customerName(),
            ],
            'items' => array_map(
                fn ($item) => [
                    'product' => [
                        'id' => $item->productId()->toString(),
                        'name' => $item->productName(),
                        'image' => $item->productImage(),
                    ],
                    'quantity' => $item->quantity(),
                    'unit_price' => $item->unitPrice()->amount(),
                    'total' => $item->total()->amount(),
                ],
                $order->items()
            ),
            'subtotal' => $order->subtotal()->amount(),
            'discount' => $order->discount()->amount(),
            'shipping' => $order->shippingCost()->amount(),
            'total' => $order->total()->amount(),
            'currency' => $order->total()->currency(),
            'shipping_address' => [
                'street' => $order->shippingAddress()->street(),
                'city' => $order->shippingAddress()->city(),
                'postal_code' => $order->shippingAddress()->postalCode(),
                'country' => $order->shippingAddress()->country(),
            ],
            'created_at' => $order->createdAt()->format('c'),
            'updated_at' => $order->updatedAt()?->format('c'),
        ]);
    }
}
```

## Authentication: Auth Responders

### LoginResponder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Auth\Login;

use Application\Auth\UseCase\Login\LoginResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class LoginResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof LoginResult);

        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'invalid_credentials' => $this->unauthorized('Invalid email or password'),
                'account_locked' => $this->forbidden('Account is locked. Please contact support.'),
                'account_inactive' => $this->forbidden('Account is not activated'),
                'too_many_attempts' => $this->tooManyRequests($result->retryAfter()),
                default => $this->unauthorized($result->errorMessage()),
            };
        }

        return $this->json([
            'token' => $result->accessToken(),
            'refresh_token' => $result->refreshToken(),
            'expires_in' => $result->expiresIn(),
            'token_type' => 'Bearer',
            'user' => [
                'id' => $result->userId(),
                'email' => $result->userEmail(),
                'name' => $result->userName(),
            ],
        ]);
    }
}
```

### RegisterResponder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Auth\Register;

use Application\Auth\UseCase\Register\RegisterResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class RegisterResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof RegisterResult);

        if ($result->hasValidationErrors()) {
            return $this->unprocessableEntity($this->formatErrors($result->errors()));
        }

        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'email_exists' => $this->conflict('Email already registered'),
                'terms_not_accepted' => $this->badRequest('You must accept the terms'),
                'weak_password' => $this->badRequest('Password does not meet requirements'),
                default => $this->badRequest($result->errorMessage()),
            };
        }

        return $this->created([
            'id' => $result->userId(),
            'email' => $result->email(),
            'message' => 'Registration successful. Please check your email to verify your account.',
        ]);
    }

    private function formatErrors(array $errors): array
    {
        $formatted = [];

        foreach ($errors as $field => $messages) {
            $formatted[] = [
                'field' => $field,
                'messages' => (array) $messages,
            ];
        }

        return $formatted;
    }
}
```

## Search: Product Search Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Product\Search;

use Application\Product\UseCase\SearchProducts\SearchProductsResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class SearchProductsResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof SearchProductsResult);

        $products = array_map(
            fn ($product) => [
                'id' => $product->id(),
                'name' => $product->name(),
                'slug' => $product->slug(),
                'description' => $product->shortDescription(),
                'price' => [
                    'amount' => $product->price()->amount(),
                    'currency' => $product->price()->currency(),
                    'formatted' => $product->price()->formatted(),
                ],
                'original_price' => $product->originalPrice() ? [
                    'amount' => $product->originalPrice()->amount(),
                    'formatted' => $product->originalPrice()->formatted(),
                ] : null,
                'discount_percentage' => $product->discountPercentage(),
                'image' => $product->thumbnailUrl(),
                'rating' => [
                    'average' => $product->averageRating(),
                    'count' => $product->reviewCount(),
                ],
                'in_stock' => $product->isInStock(),
            ],
            $result->products()
        );

        return $this->json([
            'data' => $products,
            'meta' => [
                'total' => $result->total(),
                'page' => $result->page(),
                'per_page' => $result->perPage(),
                'total_pages' => $result->totalPages(),
            ],
            'facets' => [
                'categories' => $result->categoryFacets(),
                'brands' => $result->brandFacets(),
                'price_ranges' => $result->priceRangeFacets(),
            ],
            'applied_filters' => $result->appliedFilters(),
        ]);
    }
}
```

## Webhook: Stripe Webhook Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Webhook\Stripe;

use Application\Payment\UseCase\ProcessStripeWebhook\ProcessStripeWebhookResult;
use Presentation\Shared\Responder\ResponderInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class StripeWebhookResponder implements ResponderInterface
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {
    }

    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof ProcessStripeWebhookResult);

        if ($result->isSignatureInvalid()) {
            return $this->json(['error' => 'Invalid signature'], 400);
        }

        if ($result->isUnhandledEvent()) {
            return $this->json(['received' => true, 'handled' => false], 200);
        }

        if ($result->isFailure()) {
            return $this->json(['error' => $result->errorMessage()], 500);
        }

        return $this->json(['received' => true, 'handled' => true], 200);
    }

    private function json(array $data, int $status): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($data, JSON_THROW_ON_ERROR)
        );

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body);
    }
}
```

## Bulk Operations: Bulk Delete Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\BulkDelete;

use Application\User\UseCase\BulkDeleteUsers\BulkDeleteUsersResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class BulkDeleteUsersResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof BulkDeleteUsersResult);

        if ($result->isEmpty()) {
            return $this->badRequest('No user IDs provided');
        }

        if ($result->isForbidden()) {
            return $this->forbidden('You do not have permission to delete users');
        }

        if ($result->hasFailures()) {
            return $this->json([
                'deleted' => $result->deletedCount(),
                'failed' => $result->failedCount(),
                'errors' => array_map(
                    fn ($error) => [
                        'user_id' => $error->userId(),
                        'reason' => $error->reason(),
                    ],
                    $result->errors()
                ),
            ], 207);
        }

        if ($result->deletedCount() === 0) {
            return $this->notFound('No users found with the provided IDs');
        }

        return $this->json([
            'deleted' => $result->deletedCount(),
            'message' => sprintf('%d user(s) deleted successfully', $result->deletedCount()),
        ]);
    }
}
```

## Full Test Example

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\Order\Create;

use Application\Order\UseCase\CreateOrder\CreateOrderResult;
use Domain\Order\Entity\Order;
use Domain\Order\ValueObject\OrderId;
use Domain\Shared\ValueObject\Money;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Presentation\Api\Order\Create\CreateOrderResponder;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;
use Psr\Http\Message\StreamInterface;

#[Group('unit')]
#[CoversClass(CreateOrderResponder::class)]
final class CreateOrderResponderTest extends TestCase
{
    private CreateOrderResponder $responder;
    private int $capturedStatus = 200;
    private string $capturedBody = '';

    protected function setUp(): void
    {
        $stream = $this->createMock(StreamInterface::class);

        $streamFactory = $this->createMock(StreamFactoryInterface::class);
        $streamFactory->method('createStream')->willReturnCallback(
            function (string $content) use ($stream) {
                $this->capturedBody = $content;
                return $stream;
            }
        );

        $response = $this->createMock(ResponseInterface::class);
        $response->method('withHeader')->willReturnSelf();
        $response->method('withBody')->willReturnSelf();

        $responseFactory = $this->createMock(ResponseFactoryInterface::class);
        $responseFactory->method('createResponse')->willReturnCallback(
            function (int $status = 200) use ($response) {
                $this->capturedStatus = $status;
                $mock = clone $response;
                $mock->method('getStatusCode')->willReturn($status);
                return $mock;
            }
        );

        $this->responder = new CreateOrderResponder($responseFactory, $streamFactory);
    }

    public function testSuccessReturns201WithOrderData(): void
    {
        $order = $this->createOrder();
        $result = CreateOrderResult::success($order);

        $response = $this->responder->respond($result);

        self::assertSame(201, $response->getStatusCode());

        $body = json_decode($this->capturedBody, true);
        self::assertArrayHasKey('id', $body);
        self::assertArrayHasKey('status', $body);
        self::assertArrayHasKey('total', $body);
    }

    #[DataProvider('failureProvider')]
    public function testFailureReturnsCorrectStatus(
        string $reason,
        string $message,
        int $expectedStatus
    ): void {
        $result = CreateOrderResult::failure($reason, $message);

        $response = $this->responder->respond($result);

        self::assertSame($expectedStatus, $response->getStatusCode());
    }

    public static function failureProvider(): array
    {
        return [
            'empty_cart' => ['empty_cart', 'Cart is empty', 400],
            'insufficient_stock' => ['insufficient_stock', 'Out of stock', 409],
            'invalid_coupon' => ['invalid_coupon', 'Invalid coupon', 422],
            'address_not_found' => ['address_not_found', 'Address not found', 404],
            'unknown' => ['unknown', 'Unknown error', 400],
        ];
    }

    private function createOrder(): Order
    {
        return Order::create(
            OrderId::generate(),
            Money::fromCents(10000, 'USD'),
        );
    }
}
```
