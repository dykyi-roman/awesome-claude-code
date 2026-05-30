---
name: create-response-transformer
description: Generates Response Transformer classes that turn domain objects into arrays / DTOs suitable for HTTP serialization. Universal pattern usable from any controller, action, or responder — keeps serialization concerns out of entities and away from controllers. Includes templates for single-object, collection, and nested-object transformations.
---

# Response Transformer Generator

Generate Response Transformer classes — objects that turn domain models into plain arrays (or DTOs) ready to be serialized as JSON / XML response bodies. Applicable from any controller, action, or responder regardless of architectural style.

## Response Transformer characteristics

- **Domain → array** (or → DTO): input is a domain object, output is plain data.
- **No serialization itself**: the transformer doesn't `json_encode` — the calling responder / controller does that. The transformer's job stops at "array shape".
- **One transformer per domain type**: `OrderTransformer` for `Order`, `UserTransformer` for `User`. Composable via injection.
- **Stateless**: `final readonly` by default; no per-call state.
- **Aware of API versioning when relevant**: a v1 transformer and a v2 transformer can produce different shapes from the same domain object.
- **No business logic**: just shape-mapping. If the response needs a computed value, the entity exposes it; the transformer reads it.

## When to use

| Scenario | Use a Response Transformer |
|----------|----------------------------|
| API endpoint returning a domain object | Yes |
| Endpoint returning a list/collection | Yes — transformer + `array_map` |
| Endpoint returning a single primitive (ID after create) | Skip — inline `['id' => $id]` is fine |
| Nested objects (Order with OrderItems) | Yes — compose transformers via injection |
| HTML view rendering | Maybe — usually a template engine handles this directly |

## Placement

Folder placement varies by your project's architecture; whatever folder hosts your HTTP response-shaping code (Responders, Resources, Presenters, Transformers) is where Response Transformers belong.

## Templates

### Single-object transformer

```php
<?php

declare(strict_types=1);

namespace Transformer;

final readonly class UserTransformer
{
    /**
     * @return array{id: string, email: string, name: string, created_at: string}
     */
    public function transform(User $user): array
    {
        return [
            'id' => $user->id()->toString(),
            'email' => $user->email()->value(),
            'name' => $user->name(),
            'created_at' => $user->createdAt()->format(\DateTimeInterface::ATOM),
        ];
    }
}
```

### Transformer with nested object (composed via injection)

```php
<?php

declare(strict_types=1);

namespace Transformer;

final readonly class OrderTransformer
{
    public function __construct(
        private OrderItemTransformer $itemTransformer,
    ) {}

    /**
     * @return array{
     *     id: string,
     *     status: string,
     *     total: int,
     *     currency: string,
     *     items: list<array<string, mixed>>,
     *     created_at: string,
     * }
     */
    public function transform(Order $order): array
    {
        return [
            'id' => $order->id()->toString(),
            'status' => $order->status()->value,
            'total' => $order->total()->cents(),
            'currency' => $order->total()->currency()->value,
            'items' => array_map(
                fn (OrderItem $item) => $this->itemTransformer->transform($item),
                $order->items(),
            ),
            'created_at' => $order->createdAt()->format(\DateTimeInterface::ATOM),
        ];
    }
}
```

### Collection transformer (when you want a dedicated class)

```php
<?php

declare(strict_types=1);

namespace Transformer;

final readonly class UserCollectionTransformer
{
    public function __construct(
        private UserTransformer $userTransformer,
    ) {}

    /**
     * @param list<User> $users
     * @return array{data: list<array<string, mixed>>, total: int}
     */
    public function transform(array $users, int $total): array
    {
        return [
            'data' => array_map(
                fn (User $user) => $this->userTransformer->transform($user),
                $users,
            ),
            'total' => $total,
        ];
    }
}
```

### Versioned transformers (v1 vs v2)

```php
<?php

declare(strict_types=1);

namespace Transformer\V1;

// V1 keeps the legacy field naming for backward compatibility
final readonly class UserTransformer
{
    public function transform(User $user): array
    {
        return [
            'id' => $user->id()->toString(),
            'username' => $user->name(),       // legacy field name
            'email_address' => $user->email()->value(),  // legacy field name
        ];
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Transformer\V2;

final readonly class UserTransformer
{
    public function transform(User $user): array
    {
        return [
            'id' => $user->id()->toString(),
            'name' => $user->name(),
            'email' => $user->email()->value(),
            'created_at' => $user->createdAt()->format(\DateTimeInterface::ATOM),
        ];
    }
}
```

### Usage from a Controller / Action

```php
<?php

declare(strict_types=1);

namespace Controller;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class GetUserController
{
    public function __construct(
        private GetUserUseCase $useCase,
        private UserTransformer $transformer,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('id');
        $user = $this->useCase->execute(new GetUserQuery($userId));

        if ($user === null) {
            return new JsonResponse(['error' => 'User not found'], 404);
        }

        return new JsonResponse($this->transformer->transform($user));
    }
}
```

### Usage from an MVC Controller (no Action separation)

```php
<?php

declare(strict_types=1);

namespace Controller;

final class UserController
{
    public function __construct(
        private UserRepository $users,
        private UserTransformer $transformer,
    ) {}

    public function show(int $id): JsonResponse
    {
        $user = $this->users->find($id);

        if (!$user) {
            return new JsonResponse(['error' => 'Not found'], 404);
        }

        return new JsonResponse($this->transformer->transform($user));
    }

    public function index(): JsonResponse
    {
        $users = $this->users->findAll();

        return new JsonResponse([
            'data' => array_map(
                fn (User $u) => $this->transformer->transform($u),
                $users,
            ),
        ]);
    }
}
```

### Unit test pattern

```php
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class UserTransformerTest extends TestCase
{
    public function testTransformsUserToArray(): void
    {
        $user = User::register(
            id: new UserId('USR-123'),
            email: new Email('alice@example.com'),
            name: 'Alice',
        );

        $transformer = new UserTransformer();
        $result = $transformer->transform($user);

        self::assertSame('USR-123', $result['id']);
        self::assertSame('alice@example.com', $result['email']);
        self::assertSame('Alice', $result['name']);
        self::assertArrayHasKey('created_at', $result);
    }
}

final class OrderTransformerTest extends TestCase
{
    public function testTransformsOrderWithNestedItems(): void
    {
        $order = $this->makeOrderWithItems(itemCount: 3);

        $transformer = new OrderTransformer(new OrderItemTransformer());
        $result = $transformer->transform($order);

        self::assertCount(3, $result['items']);
        self::assertSame($order->id()->toString(), $result['id']);
    }
}
```

## Generation steps

1. **Identify the domain type** the transformer covers. One transformer per domain type.
2. **Decide the output shape** — array (most common), or a typed Response DTO.
3. **List the fields** the API contract requires. Include `@return array{...}` annotation for static analyzers.
4. **Compose for nested types** via constructor injection (e.g. `OrderTransformer` accepts `OrderItemTransformer`).
5. **Generate unit tests** that verify field presence, value mapping, and nested composition.
6. **For versioned APIs**: keep transformers under `Transformer\V1\`, `Transformer\V2\` etc. and inject the right one per endpoint.

## Detection patterns

```bash
# Find transformers
Glob: **/*Transformer.php
Grep: "public function transform\(" --glob "**/*Transformer.php"

# Transformers calling repositories (likely a violation)
Grep: "Repository|EntityManager" --glob "**/*Transformer.php"

# Transformers with business logic (violation)
Grep: "if \(.*->can|->is[A-Z]|->should[A-Z]" --glob "**/*Transformer.php"

# Controllers doing inline transformation (could be extracted)
Grep: "->jsonSerialize\(\)|json_encode\(\\\$.+->" --glob "**/*Controller.php" --glob "**/*Action.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Transformer reaching for repositories / services to fetch missing data | Mixes orchestration with shape-mapping | Fetch data in the UseCase / Controller; pass the full object to the transformer |
| Computing business values inside the transformer | Duplicates logic that belongs in the entity | Add a method to the entity; transformer just reads it |
| Domain entity implementing `JsonSerializable` directly | Domain knows about JSON; couples shape to model | Move to a transformer |
| Single God-Transformer covering all domain types | Hard to test, hard to evolve per type | One transformer per domain type, composed via injection |
| Versioned transformers selected by `if ($version === 'v1')` inside one class | Branch explosion | Separate `V1\Transformer`, `V2\Transformer`; pick one per endpoint |
| Transformer returning a different shape based on caller flags | Output ambiguous | One transformer = one shape. Need a different shape? New transformer. |
