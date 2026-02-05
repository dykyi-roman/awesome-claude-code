---
name: acc-check-serialization
description: Analyzes PHP code for serialization overhead. Detects inefficient JSON encoding, large object hydration, missing JsonSerializable, circular reference issues.
---

# Serialization Performance Analysis

Analyze PHP code for serialization/deserialization performance issues.

## Detection Patterns

### 1. Large Object Serialization

```php
// PROBLEMATIC: Serializing entire entity with relations
$users = $this->userRepository->findAll();
return json_encode($users); // Includes all properties, relations, metadata

// PROBLEMATIC: Full Doctrine entity serialization
$response = new JsonResponse($this->em->find(User::class, $id));
// Serializes proxy objects, lazy-loaded relations, internal state

// PROBLEMATIC: Large collection in single response
$orders = $this->orderRepository->findByUser($userId);
return json_encode($orders); // Thousands of objects
```

### 2. N+1 During Serialization

```php
// PROBLEMATIC: Lazy loading triggered during serialization
class UserResource
{
    public function toArray(User $user): array
    {
        return [
            'id' => $user->getId(),
            'name' => $user->getName(),
            'orders' => $user->getOrders()->toArray(), // Lazy load!
            'profile' => $user->getProfile()->toArray(), // Another query!
        ];
    }
}

// PROBLEMATIC: Multiple users with relations
$users = $repository->findAll();
foreach ($users as $user) {
    $data[] = [
        'user' => $user->getName(),
        'department' => $user->getDepartment()->getName(), // N+1
    ];
}
```

### 3. Missing JsonSerializable

```php
// PROBLEMATIC: Public properties exposed
class User
{
    public int $id;
    public string $email;
    public string $passwordHash; // Exposed!
    public ?string $apiToken; // Exposed!
}

// Becomes {"id":1,"email":"...","passwordHash":"...","apiToken":"..."}

// FIXED: Implement JsonSerializable
class User implements JsonSerializable
{
    public function jsonSerialize(): array
    {
        return [
            'id' => $this->id,
            'email' => $this->email,
            // Sensitive fields excluded
        ];
    }
}
```

### 4. Circular Reference Issues

```php
// PROBLEMATIC: Circular reference causes error/infinite loop
class Order
{
    public User $user;
}

class User
{
    public array $orders; // Contains Order objects
}

json_encode($user); // Error: circular reference

// PROBLEMATIC: Doctrine bidirectional relations
/**
 * @ORM\OneToMany(targetEntity=Order::class, mappedBy="user")
 */
private Collection $orders;

/**
 * @ORM\ManyToOne(targetEntity=User::class, inversedBy="orders")
 */
private User $user;
```

### 5. DateTime Serialization Overhead

```php
// PROBLEMATIC: DateTime as object
$data = [
    'created' => $entity->getCreatedAt(), // DateTime object
];
json_encode($data);
// {"created":{"date":"2024-01-01 00:00:00.000000","timezone_type":3,"timezone":"UTC"}}

// PROBLEMATIC: Multiple DateTime conversions
foreach ($events as $event) {
    $data[] = [
        'start' => $event->getStart()->format('Y-m-d H:i:s'),
        'end' => $event->getEnd()->format('Y-m-d H:i:s'),
        'created' => $event->getCreated()->format('Y-m-d H:i:s'),
    ];
}
```

### 6. Binary Data in JSON

```php
// PROBLEMATIC: Binary data base64 encoded in JSON
$response = [
    'image' => base64_encode($imageData), // 33% size increase
    'file' => base64_encode($fileContent),
];
json_encode($response);

// PROBLEMATIC: Large file content in response
$data = [
    'attachment' => base64_encode(file_get_contents($path)),
];
// Should be streamed or served separately
```

### 7. Deep Nested Structures

```php
// PROBLEMATIC: Deeply nested JSON
$data = [
    'user' => [
        'profile' => [
            'settings' => [
                'preferences' => [
                    'notifications' => [...],
                ],
            ],
        ],
    ],
];
// Deep recursion during serialize/deserialize

// PROBLEMATIC: Recursive tree serialization
public function toArray(): array
{
    return [
        'id' => $this->id,
        'children' => array_map(
            fn($child) => $child->toArray(), // Unlimited depth
            $this->children
        ),
    ];
}
```

### 8. Hydration Overhead

```php
// PROBLEMATIC: Full object hydration for read-only display
$users = $this->em->createQueryBuilder()
    ->select('u')
    ->from(User::class, 'u')
    ->getQuery()
    ->getResult(); // Full entity hydration

// Full objects just to extract a few fields
foreach ($users as $user) {
    $data[] = ['id' => $user->getId(), 'name' => $user->getName()];
}

// BETTER: Scalar hydration
$users = $this->em->createQueryBuilder()
    ->select('u.id', 'u.name')
    ->from(User::class, 'u')
    ->getQuery()
    ->getScalarResult(); // Just arrays
```

### 9. Inefficient Collection Serialization

```php
// PROBLEMATIC: Converting entire collection multiple times
$users = $repository->findAll();
$mapped = array_map(fn($u) => $u->toArray(), $users->toArray());
$json = json_encode($mapped);

// PROBLEMATIC: Multiple iterations
$data = $collection->toArray();
$filtered = array_filter($data, fn($item) => $item->isActive());
$mapped = array_map(fn($item) => $item->toArray(), $filtered);
// 3 full iterations

// BETTER: Single pass with generators
function toJson(iterable $items): string
{
    $data = [];
    foreach ($items as $item) {
        if ($item->isActive()) {
            $data[] = $item->toArray();
        }
    }
    return json_encode($data);
}
```

### 10. Missing Response Caching

```php
// PROBLEMATIC: Serializing same data repeatedly
public function getConfig(): JsonResponse
{
    $config = $this->configService->getAll();
    return new JsonResponse($config); // Serialized every request
}

// PROBLEMATIC: User data serialized each time
public function getCurrentUser(): JsonResponse
{
    $user = $this->userService->getCurrent();
    return new JsonResponse($user->toArray()); // No caching
}
```

## Grep Patterns

```bash
# json_encode on entities
Grep: "json_encode\s*\(\s*\\\$this->(em|repository|entityManager)" --glob "**/*.php"

# Large array serialization
Grep: "json_encode\s*\([^)]*findAll|json_encode\s*\([^)]*getResult" --glob "**/*.php"

# Missing JsonSerializable
Grep: "class.*\{" --glob "**/*.php" # Then check for JsonSerializable

# base64_encode in JSON context
Grep: "base64_encode.*json_encode|json_encode.*base64_encode" --glob "**/*.php"

# DateTime in response
Grep: "->format\s*\(" --glob "**/*.php"
```

## Secure Patterns

### Use DTOs for API Responses

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

### Eager Load for Serialization

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

### Handle Circular References

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

### Streaming Large Responses

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

### Cache Serialized Responses

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

### Optimize DateTime Handling

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

### Pagination for Large Collections

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

## Severity Classification

| Pattern | Severity |
|---------|----------|
| N+1 during serialization | 🔴 Critical |
| Full entity in JSON response | 🔴 Critical |
| Circular reference without handling | 🔴 Critical |
| Large binary data in JSON | 🟠 Major |
| Missing JsonSerializable (sensitive data) | 🟠 Major |
| Deep nested structures | 🟠 Major |
| Full hydration for read-only | 🟡 Minor |
| DateTime objects in response | 🟡 Minor |

## Output Format

```markdown
### Serialization Issue: [Description]

**Severity:** 🔴/🟠/🟡
**Location:** `file.php:line`
**Impact:** [Response size, CPU overhead, memory usage]

**Issue:**
[Description of the serialization problem]

**Code:**
```php
// Problematic code
```

**Fix:**
```php
// Optimized serialization
```

**Expected Improvement:**
- Response size: 50KB → 2KB (DTO instead of entity)
- Query count: N+1 → 1 (eager loading)
- CPU time: -60% (cached serialization)
```
