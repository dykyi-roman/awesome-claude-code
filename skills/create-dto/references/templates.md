# DTO Pattern Templates

## Request DTO (API Input)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\{BoundedContext}\Request;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class {Name}Request
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Type('string')]
        public string $field1,

        #[Assert\NotBlank]
        #[Assert\Email]
        public string $email,

        #[Assert\NotBlank]
        #[Assert\Positive]
        public int $amount,

        #[Assert\Valid]
        public ?NestedRequest $nested = null,

        /** @var array<ItemRequest> */
        #[Assert\Valid]
        #[Assert\Count(min: 1)]
        public array $items = []
    ) {}

    public static function fromArray(array $data): self
    {
        return new self(
            field1: $data['field1'] ?? '',
            email: $data['email'] ?? '',
            amount: (int) ($data['amount'] ?? 0),
            nested: isset($data['nested'])
                ? NestedRequest::fromArray($data['nested'])
                : null,
            items: array_map(
                fn(array $item) => ItemRequest::fromArray($item),
                $data['items'] ?? []
            )
        );
    }
}
```

---

## Response DTO (API Output)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\{BoundedContext}\Response;

final readonly class {Name}Response implements \JsonSerializable
{
    public function __construct(
        public string $id,
        public string $name,
        public string $status,
        public int $amount,
        public string $createdAt,
        /** @var array<ItemResponse> */
        public array $items = []
    ) {}

    public static function fromEntity({Entity} $entity): self
    {
        return new self(
            id: $entity->id()->toString(),
            name: $entity->name()->value(),
            status: $entity->status()->value,
            amount: $entity->amount()->cents(),
            createdAt: $entity->createdAt()->format('c'),
            items: array_map(
                fn($item) => ItemResponse::fromEntity($item),
                $entity->items()
            )
        );
    }

    public function jsonSerialize(): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'status' => $this->status,
            'amount' => $this->amount,
            'created_at' => $this->createdAt,
            'items' => array_map(
                fn($item) => $item->jsonSerialize(),
                $this->items
            ),
        ];
    }
}
```

---

## Command/Query DTO (Application Layer)

```php
<?php

declare(strict_types=1);

namespace Application\{BoundedContext}\DTO;

final readonly class {Name}DTO
{
    public function __construct(
        public string $id,
        public string $field1,
        public int $field2,
        public ?string $optionalField = null
    ) {}

    public static function fromRequest({Name}Request $request): self
    {
        return new self(
            id: $request->id,
            field1: $request->field1,
            field2: $request->field2,
            optionalField: $request->optionalField
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'field1' => $this->field1,
            'field2' => $this->field2,
            'optional_field' => $this->optionalField,
        ];
    }
}
```

---

## Collection Response DTO

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\{BoundedContext}\Response;

final readonly class {Name}CollectionResponse implements \JsonSerializable
{
    /**
     * @param array<{Name}Response> $items
     */
    public function __construct(
        public array $items,
        public int $total,
        public int $page,
        public int $perPage
    ) {}

    /**
     * @param array<{Entity}> $entities
     */
    public static function fromEntities(
        array $entities,
        int $total,
        int $page,
        int $perPage
    ): self {
        return new self(
            items: array_map(
                fn($entity) => {Name}Response::fromEntity($entity),
                $entities
            ),
            total: $total,
            page: $page,
            perPage: $perPage
        );
    }

    public function jsonSerialize(): array
    {
        return [
            'items' => array_map(
                fn($item) => $item->jsonSerialize(),
                $this->items
            ),
            'meta' => [
                'total' => $this->total,
                'page' => $this->page,
                'per_page' => $this->perPage,
                'total_pages' => (int) ceil($this->total / $this->perPage),
            ],
        ];
    }
}
```

---

## Integration DTO (External API)

```php
<?php

declare(strict_types=1);

namespace Infrastructure\ExternalApi\{Service}\DTO;

final readonly class {Service}Response
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

## Test Templates

### Request DTO Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\{BoundedContext}\Request;

use Presentation\Api\{BoundedContext}\Request\{Name}Request;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Request::class)]
final class {Name}RequestTest extends TestCase
{
    public function testCreatesFromValidArray(): void
    {
        $data = [
            'field1' => 'value1',
            'email' => 'test@example.com',
            'amount' => 100,
        ];

        $request = {Name}Request::fromArray($data);

        self::assertSame('value1', $request->field1);
        self::assertSame('test@example.com', $request->email);
        self::assertSame(100, $request->amount);
    }

    public function testHandlesMissingOptionalFields(): void
    {
        $data = [
            'field1' => 'value1',
            'email' => 'test@example.com',
            'amount' => 100,
        ];

        $request = {Name}Request::fromArray($data);

        self::assertNull($request->optionalField);
    }

    public function testCreatesNestedObjects(): void
    {
        $data = [
            'field1' => 'value1',
            'email' => 'test@example.com',
            'amount' => 100,
            'nested' => ['nested_field' => 'nested_value'],
            'items' => [
                ['item_field' => 'item1'],
                ['item_field' => 'item2'],
            ],
        ];

        $request = {Name}Request::fromArray($data);

        self::assertNotNull($request->nested);
        self::assertCount(2, $request->items);
    }
}
```

### Response DTO Test

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\{BoundedContext}\Response;

use Presentation\Api\{BoundedContext}\Response\{Name}Response;
use Domain\{BoundedContext}\Entity\{Entity};
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass({Name}Response::class)]
final class {Name}ResponseTest extends TestCase
{
    public function testCreatesFromEntity(): void
    {
        $entity = $this->createEntity();

        $response = {Name}Response::fromEntity($entity);

        self::assertSame($entity->id()->toString(), $response->id);
        self::assertSame($entity->name()->value(), $response->name);
    }

    public function testSerializesToJson(): void
    {
        $response = new {Name}Response(
            id: 'uuid-123',
            name: 'Test Name',
            status: 'active',
            amount: 1000,
            createdAt: '2024-01-15T10:00:00+00:00',
            items: []
        );

        $json = $response->jsonSerialize();

        self::assertSame('uuid-123', $json['id']);
        self::assertSame('Test Name', $json['name']);
        self::assertSame('active', $json['status']);
        self::assertSame(1000, $json['amount']);
        self::assertArrayHasKey('created_at', $json);
    }

    private function createEntity(): {Entity}
    {
        return new {Entity}(
            {testConstructorArgs}
        );
    }
}
```
