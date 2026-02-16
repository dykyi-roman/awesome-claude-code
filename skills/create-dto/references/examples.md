# DTO Pattern Examples

## Order Request DTO

**File:** `src/Presentation/Api/Order/Request/CreateOrderRequest.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Request;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class CreateOrderRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Uuid]
        public string $customerId,

        /** @var array<OrderItemRequest> */
        #[Assert\Valid]
        #[Assert\Count(min: 1, minMessage: 'Order must have at least one item')]
        public array $items,

        #[Assert\Valid]
        public AddressRequest $shippingAddress,

        #[Assert\Valid]
        public AddressRequest $billingAddress,

        #[Assert\Length(max: 500)]
        public ?string $notes = null
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            customerId: $data['customer_id'] ?? '',
            items: array_map(
                fn(array $item) => OrderItemRequest::fromArray($item),
                $data['items'] ?? []
            ),
            shippingAddress: AddressRequest::fromArray($data['shipping_address'] ?? []),
            billingAddress: AddressRequest::fromArray($data['billing_address'] ?? []),
            notes: $data['notes'] ?? null
        );
    }
}
```

---

## OrderItemRequest

**File:** `src/Presentation/Api/Order/Request/OrderItemRequest.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Request;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class OrderItemRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Uuid]
        public string $productId,

        #[Assert\NotBlank]
        #[Assert\Positive]
        public int $quantity,

        #[Assert\PositiveOrZero]
        public ?int $priceOverrideCents = null
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            productId: $data['product_id'] ?? '',
            quantity: (int) ($data['quantity'] ?? 0),
            priceOverrideCents: isset($data['price_override_cents'])
                ? (int) $data['price_override_cents']
                : null
        );
    }
}
```

---

## Order Response DTO

**File:** `src/Presentation/Api/Order/Response/OrderResponse.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Response;

use Domain\Order\Entity\Order;

final readonly class OrderResponse implements \JsonSerializable
{
    /**
     * @param array<OrderItemResponse> $items
     */
    public function __construct(
        public string $id,
        public string $customerId,
        public string $status,
        public int $totalCents,
        public string $currency,
        public AddressResponse $shippingAddress,
        public AddressResponse $billingAddress,
        public array $items,
        public string $createdAt,
        public ?string $updatedAt,
        public ?string $notes
    ) {}

    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->id()->toString(),
            customerId: $order->customerId()->toString(),
            status: $order->status()->value,
            totalCents: $order->total()->cents(),
            currency: $order->total()->currency()->value,
            shippingAddress: AddressResponse::fromValueObject($order->shippingAddress()),
            billingAddress: AddressResponse::fromValueObject($order->billingAddress()),
            items: array_map(
                fn($item) => OrderItemResponse::fromEntity($item),
                $order->items()
            ),
            createdAt: $order->createdAt()->format('c'),
            updatedAt: $order->updatedAt()?->format('c'),
            notes: $order->notes()
        );
    }

    public function jsonSerialize(): array
    {
        return [
            'id' => $this->id,
            'customer_id' => $this->customerId,
            'status' => $this->status,
            'total' => [
                'cents' => $this->totalCents,
                'currency' => $this->currency,
            ],
            'shipping_address' => $this->shippingAddress->jsonSerialize(),
            'billing_address' => $this->billingAddress->jsonSerialize(),
            'items' => array_map(
                fn($item) => $item->jsonSerialize(),
                $this->items
            ),
            'created_at' => $this->createdAt,
            'updated_at' => $this->updatedAt,
            'notes' => $this->notes,
        ];
    }
}
```

---

## User DTO (Application Layer)

**File:** `src/Application/User/DTO/UserDTO.php`

```php
<?php

declare(strict_types=1);

namespace Application\User\DTO;

use Domain\User\Entity\User;

final readonly class UserDTO
{
    public function __construct(
        public string $id,
        public string $email,
        public string $name,
        public string $role,
        public string $status,
        public ?string $avatarUrl
    ) {}

    public static function fromEntity(User $user): self
    {
        return new self(
            id: $user->id()->toString(),
            email: $user->email()->value(),
            name: $user->name()->full(),
            role: $user->role()->value,
            status: $user->status()->value,
            avatarUrl: $user->avatarUrl()?->toString()
        );
    }

    /**
     * @param array<User> $users
     * @return array<self>
     */
    public static function fromEntities(array $users): array
    {
        return array_map(fn(User $user) => self::fromEntity($user), $users);
    }
}
```

---

## Payment Gateway Integration DTO

**File:** `src/Infrastructure/ExternalApi/Payment/DTO/PaymentGatewayResponse.php`

```php
<?php

declare(strict_types=1);

namespace Infrastructure\ExternalApi\Payment\DTO;

final readonly class PaymentGatewayResponse
{
    public function __construct(
        public string $transactionId,
        public string $status,
        public int $amountCents,
        public string $currency,
        public ?string $errorCode,
        public ?string $errorMessage,
        public array $metadata
    ) {}

    public static function fromApiResponse(array $response): self
    {
        return new self(
            transactionId: $response['transaction_id'] ?? '',
            status: $response['status'] ?? 'unknown',
            amountCents: (int) ($response['amount']['cents'] ?? 0),
            currency: $response['amount']['currency'] ?? 'USD',
            errorCode: $response['error']['code'] ?? null,
            errorMessage: $response['error']['message'] ?? null,
            metadata: $response['metadata'] ?? []
        );
    }

    public function isSuccessful(): bool
    {
        return $this->status === 'succeeded';
    }

    public function isFailed(): bool
    {
        return $this->status === 'failed';
    }
}
```

---

## Unit Tests

### CreateOrderRequestTest

**File:** `tests/Unit/Presentation/Api/Order/Request/CreateOrderRequestTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\Order\Request;

use Presentation\Api\Order\Request\CreateOrderRequest;
use Presentation\Api\Order\Request\OrderItemRequest;
use Presentation\Api\Order\Request\AddressRequest;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(CreateOrderRequest::class)]
final class CreateOrderRequestTest extends TestCase
{
    public function testCreatesFromValidArray(): void
    {
        $data = [
            'customer_id' => '550e8400-e29b-41d4-a716-446655440000',
            'items' => [
                ['product_id' => 'prod-123', 'quantity' => 2],
            ],
            'shipping_address' => [
                'street' => '123 Main St',
                'city' => 'Test City',
                'postal_code' => '12345',
                'country' => 'US',
            ],
            'billing_address' => [
                'street' => '123 Main St',
                'city' => 'Test City',
                'postal_code' => '12345',
                'country' => 'US',
            ],
            'notes' => 'Please deliver before noon',
        ];

        $request = CreateOrderRequest::fromArray($data);

        self::assertSame('550e8400-e29b-41d4-a716-446655440000', $request->customerId);
        self::assertCount(1, $request->items);
        self::assertInstanceOf(AddressRequest::class, $request->shippingAddress);
        self::assertSame('Please deliver before noon', $request->notes);
    }

    public function testHandlesOptionalNotes(): void
    {
        $data = [
            'customer_id' => '550e8400-e29b-41d4-a716-446655440000',
            'items' => [['product_id' => 'prod-123', 'quantity' => 1]],
            'shipping_address' => ['street' => '123 Main St', 'city' => 'City', 'postal_code' => '12345', 'country' => 'US'],
            'billing_address' => ['street' => '123 Main St', 'city' => 'City', 'postal_code' => '12345', 'country' => 'US'],
        ];

        $request = CreateOrderRequest::fromArray($data);

        self::assertNull($request->notes);
    }
}
```

### OrderResponseTest

**File:** `tests/Unit/Presentation/Api/Order/Response/OrderResponseTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\Order\Response;

use Presentation\Api\Order\Response\OrderResponse;
use Presentation\Api\Order\Response\AddressResponse;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderResponse::class)]
final class OrderResponseTest extends TestCase
{
    public function testSerializesToJsonWithCorrectStructure(): void
    {
        $response = new OrderResponse(
            id: 'order-123',
            customerId: 'customer-456',
            status: 'confirmed',
            totalCents: 15000,
            currency: 'USD',
            shippingAddress: new AddressResponse(
                street: '123 Main St',
                city: 'Test City',
                postalCode: '12345',
                country: 'US'
            ),
            billingAddress: new AddressResponse(
                street: '456 Oak Ave',
                city: 'Other City',
                postalCode: '67890',
                country: 'US'
            ),
            items: [],
            createdAt: '2024-01-15T10:00:00+00:00',
            updatedAt: '2024-01-15T12:00:00+00:00',
            notes: 'Rush order'
        );

        $json = $response->jsonSerialize();

        self::assertSame('order-123', $json['id']);
        self::assertSame('customer-456', $json['customer_id']);
        self::assertSame('confirmed', $json['status']);
        self::assertSame(['cents' => 15000, 'currency' => 'USD'], $json['total']);
        self::assertArrayHasKey('shipping_address', $json);
        self::assertArrayHasKey('billing_address', $json);
        self::assertSame('Rush order', $json['notes']);
    }

    public function testHandlesNullableFields(): void
    {
        $response = new OrderResponse(
            id: 'order-123',
            customerId: 'customer-456',
            status: 'pending',
            totalCents: 5000,
            currency: 'EUR',
            shippingAddress: new AddressResponse('St', 'City', '123', 'DE'),
            billingAddress: new AddressResponse('St', 'City', '123', 'DE'),
            items: [],
            createdAt: '2024-01-15T10:00:00+00:00',
            updatedAt: null,
            notes: null
        );

        $json = $response->jsonSerialize();

        self::assertNull($json['updated_at']);
        self::assertNull($json['notes']);
    }
}
```

### UserDTOTest

**File:** `tests/Unit/Application/User/DTO/UserDTOTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Application\User\DTO;

use Application\User\DTO\UserDTO;
use Domain\User\Entity\User;
use Domain\User\ValueObject\UserId;
use Domain\User\ValueObject\Email;
use Domain\User\ValueObject\Name;
use Domain\User\Enum\UserRole;
use Domain\User\Enum\UserStatus;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(UserDTO::class)]
final class UserDTOTest extends TestCase
{
    public function testCreatesFromEntity(): void
    {
        $user = $this->createUser();

        $dto = UserDTO::fromEntity($user);

        self::assertSame($user->id()->toString(), $dto->id);
        self::assertSame($user->email()->value(), $dto->email);
        self::assertSame($user->name()->full(), $dto->name);
        self::assertSame($user->role()->value, $dto->role);
        self::assertSame($user->status()->value, $dto->status);
    }

    public function testCreatesFromEntitiesCollection(): void
    {
        $users = [
            $this->createUser('user-1'),
            $this->createUser('user-2'),
            $this->createUser('user-3'),
        ];

        $dtos = UserDTO::fromEntities($users);

        self::assertCount(3, $dtos);
        self::assertContainsOnlyInstancesOf(UserDTO::class, $dtos);
    }

    private function createUser(string $id = 'user-123'): User
    {
        return new User(
            id: new UserId($id),
            email: new Email('test@example.com'),
            name: new Name('John', 'Doe'),
            role: UserRole::Customer,
            status: UserStatus::Active,
            createdAt: new \DateTimeImmutable()
        );
    }
}
```
