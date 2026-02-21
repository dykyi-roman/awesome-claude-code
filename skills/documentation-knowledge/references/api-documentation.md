# API Documentation

## OpenAPI/Swagger for PHP

### OpenAPI Specification Structure

```yaml
openapi: 3.1.0
info:
  title: Order Service API
  version: 2.0.0
  description: DDD-based order management service
  contact:
    name: API Support
    email: api@example.com

servers:
  - url: https://api.example.com/v2
    description: Production
  - url: https://staging-api.example.com/v2
    description: Staging

paths:
  /orders:
    post:
      operationId: createOrder
      summary: Create a new order
      tags: [Orders]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateOrderRequest'
      responses:
        '201':
          description: Order created
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderResponse'
        '422':
          $ref: '#/components/responses/ValidationError'

components:
  schemas:
    CreateOrderRequest:
      type: object
      required: [customer_id, lines]
      properties:
        customer_id:
          type: string
          format: uuid
        lines:
          type: array
          minItems: 1
          items:
            $ref: '#/components/schemas/OrderLineRequest'

    OrderResponse:
      type: object
      properties:
        id:
          type: string
          format: uuid
        status:
          type: string
          enum: [draft, confirmed, shipped, delivered, cancelled]
        total:
          type: integer
          description: Total amount in cents

  responses:
    ValidationError:
      description: Validation failed
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
```

## PHP Attribute-Based Documentation

### zircote/swagger-php

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use OpenApi\Attributes as OA;
use Symfony\Component\HttpFoundation\JsonResponse;

#[OA\Tag(name: 'Orders', description: 'Order management')]
final readonly class CreateOrderAction
{
    #[OA\Post(
        path: '/api/v2/orders',
        operationId: 'createOrder',
        summary: 'Create a new order',
        tags: ['Orders'],
        requestBody: new OA\RequestBody(
            required: true,
            content: new OA\JsonContent(
                ref: '#/components/schemas/CreateOrderRequest'
            )
        ),
        responses: [
            new OA\Response(
                response: 201,
                description: 'Order created successfully',
                content: new OA\JsonContent(
                    ref: '#/components/schemas/OrderResponse'
                )
            ),
            new OA\Response(
                response: 422,
                description: 'Validation failed',
                content: new OA\JsonContent(
                    ref: '#/components/schemas/ErrorResponse'
                )
            ),
        ]
    )]
    public function __invoke(CreateOrderRequest $request): JsonResponse
    {
        // handler logic
    }
}
```

### nelmio/api-doc-bundle (Symfony)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order;

use Nelmio\ApiDocBundle\Annotation\Model;
use OpenApi\Attributes as OA;

final readonly class OrderController
{
    #[OA\Post(
        requestBody: new OA\RequestBody(
            content: new OA\JsonContent(
                ref: new Model(type: CreateOrderRequest::class)
            )
        ),
        responses: [
            new OA\Response(
                response: 201,
                description: 'Order created',
                content: new OA\JsonContent(
                    ref: new Model(type: OrderResponse::class, groups: ['order:read'])
                )
            ),
        ]
    )]
    public function create(CreateOrderRequest $request): JsonResponse
    {
        // handler logic
    }
}
```

### Schema Definitions with Attributes

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Response;

use OpenApi\Attributes as OA;

#[OA\Schema(
    schema: 'OrderResponse',
    title: 'Order',
    description: 'Order resource representation',
    required: ['id', 'status', 'total', 'created_at']
)]
final readonly class OrderResponse
{
    public function __construct(
        #[OA\Property(type: 'string', format: 'uuid', example: '550e8400-e29b-41d4-a716-446655440000')]
        public string $id,

        #[OA\Property(type: 'string', enum: ['draft', 'confirmed', 'shipped', 'delivered', 'cancelled'])]
        public string $status,

        #[OA\Property(type: 'integer', description: 'Total in cents', example: 4999)]
        public int $total,

        #[OA\Property(type: 'string', format: 'date-time')]
        public string $createdAt,

        /** @var array<OrderLineResponse> */
        #[OA\Property(type: 'array', items: new OA\Items(ref: '#/components/schemas/OrderLineResponse'))]
        public array $lines = [],
    ) {}
}
```

## API Versioning Documentation

### URI Versioning

```markdown
## API Versioning

This API uses URI-based versioning:

| Version | Base URL | Status |
|---------|----------|--------|
| v2 | `https://api.example.com/v2` | **Current** |
| v1 | `https://api.example.com/v1` | Deprecated (sunset: 2026-06-01) |

### Migration Guide (v1 to v2)

#### Breaking Changes
- `POST /orders` request body: `amount` renamed to `total_cents` (integer, cents)
- `GET /orders/{id}` response: `customer` field changed from string to object

#### New Endpoints
- `GET /orders/{id}/events` — order event history (Event Sourcing)
```

## Error Response Documentation

### Standard Error Format

```markdown
## Error Responses

All errors follow RFC 7807 Problem Details format:

```json
{
  "type": "https://api.example.com/errors/validation",
  "title": "Validation Error",
  "status": 422,
  "detail": "Request body contains invalid data",
  "errors": [
    {
      "field": "customer_id",
      "message": "Invalid UUID format",
      "code": "INVALID_FORMAT"
    }
  ]
}
```

### HTTP Status Codes

| Code | Meaning | When |
|------|---------|------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST creating resource |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Malformed JSON, invalid content type |
| 401 | Unauthorized | Missing or invalid auth token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource does not exist |
| 409 | Conflict | Duplicate resource, version conflict |
| 422 | Unprocessable | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Unhandled exception |
```

## Detection Patterns

```bash
# Find OpenAPI attributes
Grep: "OA\\\\(Post|Get|Put|Delete|Patch)" --glob "src/**/*.php"

# Find API doc configuration
Glob: config/packages/nelmio_api_doc.yaml
Glob: config/packages/api_platform.yaml

# Find OpenAPI spec files
Glob: **/openapi.{yaml,yml,json}
Glob: **/swagger.{yaml,yml,json}

# Find undocumented endpoints
Grep: "#\[Route\(" --glob "src/**/*.php"
# Compare with: Grep: "#\[OA\\" --glob "src/**/*.php"
```

## Summary

| Approach | Pros | Cons |
|----------|------|------|
| **OpenAPI YAML** | Language-agnostic, tooling ecosystem, single source | Separate from code, can drift |
| **PHP Attributes (swagger-php)** | Co-located with code, type-safe | Verbose attributes, PHP-only |
| **Nelmio ApiDocBundle** | Symfony integration, auto-discovers | Symfony-only, slower generation |
| **API Platform** | Auto-generates from entities, HATEOAS | Opinionated, heavy framework |
| **PHPDoc + Generator** | Minimal annotations, familiar | Limited expressiveness |
