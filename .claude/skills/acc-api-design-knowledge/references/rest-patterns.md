# REST Patterns Reference

## Richardson Maturity Model Detailed

### Level 0: Swamp of POX (Plain Old XML/JSON)

Single endpoint handling all operations via request body:

```
POST /api
{
    "action": "getOrder",
    "orderId": "123"
}
```

Problems: No use of HTTP semantics, no caching, no discoverability.

### Level 1: Resources

Individual endpoints per resource, but only POST:

```
POST /orders          → Create order
POST /orders/123      → Get order (action in body)
POST /orders/123      → Update order (action in body)
```

Improvement: Resource identification via URI.

### Level 2: HTTP Verbs

Proper use of HTTP methods and status codes:

```
GET    /orders         → 200 OK (list)
POST   /orders         → 201 Created
GET    /orders/123     → 200 OK (detail)
PUT    /orders/123     → 200 OK (replace)
PATCH  /orders/123     → 200 OK (partial update)
DELETE /orders/123     → 204 No Content
```

Most APIs stop here. This is the minimum acceptable level.

### Level 3: HATEOAS (Hypermedia As The Engine Of Application State)

Responses include links to available actions:

```json
{
    "id": "123",
    "status": "pending",
    "_links": {
        "self": {"href": "/orders/123"},
        "confirm": {"href": "/orders/123/confirm", "method": "POST"},
        "cancel": {"href": "/orders/123/cancel", "method": "POST"},
        "customer": {"href": "/customers/456"}
    }
}
```

## HATEOAS Implementations

### HAL (Hypertext Application Language)

```json
{
    "_links": {
        "self": {"href": "/orders/123"},
        "next": {"href": "/orders?page=2"}
    },
    "_embedded": {
        "items": [
            {"id": "item-1", "_links": {"self": {"href": "/items/1"}}}
        ]
    },
    "id": "123",
    "total": 5990
}
```

### JSON:API

```json
{
    "data": {
        "type": "orders",
        "id": "123",
        "attributes": {"total": 5990, "status": "pending"},
        "relationships": {
            "customer": {"data": {"type": "customers", "id": "456"}}
        },
        "links": {"self": "/orders/123"}
    },
    "included": [
        {"type": "customers", "id": "456", "attributes": {"name": "John"}}
    ]
}
```

## Pagination Patterns

### Offset-Based Pagination

```
GET /orders?page=2&per_page=25

Response:
{
    "data": [...],
    "meta": {
        "current_page": 2,
        "per_page": 25,
        "total": 150,
        "total_pages": 6
    },
    "links": {
        "first": "/orders?page=1&per_page=25",
        "prev": "/orders?page=1&per_page=25",
        "next": "/orders?page=3&per_page=25",
        "last": "/orders?page=6&per_page=25"
    }
}
```

| Pros | Cons |
|------|------|
| Simple to implement | Inconsistent with concurrent writes |
| Random page access | Slow on large offsets (OFFSET N) |
| Total count available | |

### Cursor-Based Pagination

```
GET /orders?after=eyJpZCI6MTAwfQ&limit=25

Response:
{
    "data": [...],
    "cursors": {
        "after": "eyJpZCI6MTI1fQ",
        "before": "eyJpZCI6MTAxfQ",
        "has_more": true
    }
}
```

| Pros | Cons |
|------|------|
| Consistent with concurrent writes | No random page access |
| Fast (no OFFSET) | No total count |
| Works with real-time data | Opaque cursors |

### Keyset Pagination

```
GET /orders?created_after=2025-01-01T00:00:00Z&limit=25

Response:
{
    "data": [...],
    "next": "/orders?created_after=2025-01-15T14:30:00Z&limit=25"
}
```

| Pros | Cons |
|------|------|
| Very fast (index scan) | Requires sortable column |
| No OFFSET performance issue | No random page access |
| Deterministic ordering | Complex with multi-column sort |

### PHP Pagination Implementation

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Response;

final readonly class PaginatedResponse
{
    /**
     * @param list<array<string, mixed>> $items
     */
    public function __construct(
        private array $items,
        private int $total,
        private int $page,
        private int $perPage,
        private string $baseUrl,
    ) {}

    public function toArray(): array
    {
        $totalPages = (int) ceil($this->total / $this->perPage);

        return [
            'data' => $this->items,
            'meta' => [
                'current_page' => $this->page,
                'per_page' => $this->perPage,
                'total' => $this->total,
                'total_pages' => $totalPages,
            ],
            'links' => [
                'first' => sprintf('%s?page=1&per_page=%d', $this->baseUrl, $this->perPage),
                'prev' => $this->page > 1
                    ? sprintf('%s?page=%d&per_page=%d', $this->baseUrl, $this->page - 1, $this->perPage)
                    : null,
                'next' => $this->page < $totalPages
                    ? sprintf('%s?page=%d&per_page=%d', $this->baseUrl, $this->page + 1, $this->perPage)
                    : null,
                'last' => sprintf('%s?page=%d&per_page=%d', $this->baseUrl, $totalPages, $this->perPage),
            ],
        ];
    }
}
```

## Filtering and Sorting

### Query Parameter Patterns

```
# Filtering
GET /orders?status=pending&customer_id=456
GET /orders?created_after=2025-01-01&total_min=1000

# Sorting
GET /orders?sort=created_at&direction=desc
GET /orders?sort=-created_at,+total    # prefix notation

# Sparse fieldsets (reduce payload)
GET /orders?fields=id,status,total
GET /orders?fields[orders]=id,status&fields[customer]=name

# Search
GET /orders?q=premium&search_in=notes,tags

# Combined
GET /orders?status=pending&sort=-created_at&page=1&per_page=25&fields=id,status,total
```

### Filter Implementation

```php
<?php

declare(strict_types=1);

namespace Application\Query;

final readonly class OrderFilter
{
    /**
     * @param list<string>|null $statuses
     * @param list<string>|null $fields
     */
    public function __construct(
        public ?array $statuses = null,
        public ?string $customerId = null,
        public ?\DateTimeImmutable $createdAfter = null,
        public ?\DateTimeImmutable $createdBefore = null,
        public ?int $totalMin = null,
        public ?int $totalMax = null,
        public string $sortBy = 'created_at',
        public string $sortDirection = 'desc',
        public ?array $fields = null,
    ) {}
}
```

## Versioning Strategies

### URI Prefix Versioning

```
GET /v1/orders/123
GET /v2/orders/123
```

| Pros | Cons |
|------|------|
| Explicit, visible in URL | Pollutes URI space |
| Easy to route | Hard to maintain multiple versions |
| Cache-friendly | Not RESTful (same resource, different URI) |

### Header Versioning

```
GET /orders/123
Accept: application/vnd.myapi.v2+json
```

| Pros | Cons |
|------|------|
| Clean URIs | Hidden version |
| RESTful (same resource URI) | Harder to test (need custom headers) |
| Allows content negotiation | Cache key must include header |

### Query Parameter Versioning

```
GET /orders/123?version=2
```

| Pros | Cons |
|------|------|
| Easy to test | Pollutes query string |
| Visible | Not RESTful |
| Easy to default | Cache key includes param |

### Versioning Best Practices

1. **Default version** — always have a default for versionless requests
2. **Additive changes** — add fields, never remove in same version
3. **Deprecation headers** — `Sunset: Sat, 01 Jan 2026 00:00:00 GMT`
4. **Version lifecycle** — support N and N-1 versions minimum
5. **Consumer-driven contracts** — test with Pact or similar tools

Cross-reference: `acc-create-api-versioning` skill for code generation.

## PHP PSR-7 Response Building

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Responder;

use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class JsonResponder
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {}

    public function success(array $data, int $status = 200): ResponseInterface
    {
        return $this->json($data, $status);
    }

    public function created(array $data, string $location): ResponseInterface
    {
        return $this->json($data, 201)
            ->withHeader('Location', $location);
    }

    public function noContent(): ResponseInterface
    {
        return $this->responseFactory->createResponse(204);
    }

    private function json(array $data, int $status): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($data, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE),
        );

        return $this->responseFactory
            ->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body);
    }
}
```
