# Serialization Secure Patterns

## Use DTOs for API Responses

```php
// SECURE: Dedicated response DTO
final readonly class UserResponse implements JsonSerializable
{
    public function __construct(
        public int $id,
        public string $name,
        public string $email,
        public string $createdAt,
    ) {}

    public static function fromEntity(User $user): self
    {
        return new self(
            id: $user->getId(),
            name: $user->getName(),
            email: $user->getEmail(),
            createdAt: $user->getCreatedAt()->format('c'),
        );
    }

    public function jsonSerialize(): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'created_at' => $this->createdAt,
        ];
    }
}
```

## Eager Load for Serialization

```php
// SECURE: Eager load relations before serialization
$users = $this->em->createQueryBuilder()
    ->select('u', 'o', 'p')
    ->from(User::class, 'u')
    ->leftJoin('u.orders', 'o')
    ->leftJoin('u.profile', 'p')
    ->getQuery()
    ->getResult();

// Relations already loaded, no N+1
foreach ($users as $user) {
    $data[] = UserResponse::fromEntity($user);
}
```

## Handle Circular References

```php
// SECURE: Break circular references in serialization
final readonly class OrderResponse implements JsonSerializable
{
    public function __construct(
        public int $id,
        public int $userId, // Just ID, not full User
        public float $total,
    ) {}

    public static function fromEntity(Order $order): self
    {
        return new self(
            id: $order->getId(),
            userId: $order->getUser()->getId(), // Reference, not object
            total: $order->getTotal(),
        );
    }

    public function jsonSerialize(): array
    {
        return get_object_vars($this);
    }
}
```

## Streaming Large Responses

```php
// SECURE: Stream large JSON responses
final class StreamingJsonResponse
{
    public function stream(iterable $items): void
    {
        header('Content-Type: application/json');

        echo '[';
        $first = true;

        foreach ($items as $item) {
            if (!$first) {
                echo ',';
            }
            echo json_encode($item->toArray());
            $first = false;

            // Flush periodically
            if (ob_get_level() > 0) {
                ob_flush();
            }
            flush();
        }

        echo ']';
    }
}
```

## Cache Serialized Responses

```php
// SECURE: Cache serialized JSON
final class CachedJsonResponder
{
    public function respond(string $cacheKey, callable $dataProvider): JsonResponse
    {
        $cached = $this->cache->get($cacheKey);

        if ($cached !== null) {
            return JsonResponse::fromJsonString($cached);
        }

        $data = $dataProvider();
        $json = json_encode($data);

        $this->cache->set($cacheKey, $json, 3600);

        return JsonResponse::fromJsonString($json);
    }
}
```

## Optimize DateTime Handling

```php
// SECURE: Pre-format dates in query
$results = $this->em->createQueryBuilder()
    ->select(
        'e.id',
        'e.name',
        "DATE_FORMAT(e.createdAt, '%Y-%m-%dT%H:%i:%sZ') as created_at"
    )
    ->from(Event::class, 'e')
    ->getQuery()
    ->getArrayResult();

// Already formatted, no DateTime objects
```

## Pagination for Large Collections

```php
// SECURE: Always paginate large collections
final class PaginatedResponse implements JsonSerializable
{
    public function __construct(
        private readonly array $items,
        private readonly int $total,
        private readonly int $page,
        private readonly int $perPage,
    ) {}

    public function jsonSerialize(): array
    {
        return [
            'data' => $this->items,
            'meta' => [
                'total' => $this->total,
                'page' => $this->page,
                'per_page' => $this->perPage,
                'last_page' => (int) ceil($this->total / $this->perPage),
            ],
        ];
    }
}
```
