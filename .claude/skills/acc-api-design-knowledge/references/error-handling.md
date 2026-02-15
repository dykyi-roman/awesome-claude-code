# API Error Handling Reference

## RFC 7807 — Problem Details for HTTP APIs

### Standard Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | URI | No | Reference to error documentation |
| `title` | string | No | Short human-readable summary |
| `status` | integer | No | HTTP status code |
| `detail` | string | No | Human-readable explanation specific to this occurrence |
| `instance` | URI | No | Reference to this specific occurrence |

### Example Response

```json
HTTP/1.1 422 Unprocessable Entity
Content-Type: application/problem+json

{
    "type": "https://api.example.com/errors/validation",
    "title": "Validation Error",
    "status": 422,
    "detail": "The request body contains invalid data",
    "instance": "/orders/123",
    "errors": [
        {
            "field": "email",
            "message": "Must be a valid email address",
            "code": "INVALID_EMAIL"
        },
        {
            "field": "quantity",
            "message": "Must be greater than 0",
            "code": "MIN_VALUE"
        }
    ]
}
```

### Extension Fields

RFC 7807 allows custom fields alongside standard ones:

```json
{
    "type": "https://api.example.com/errors/insufficient-funds",
    "title": "Insufficient Funds",
    "status": 422,
    "detail": "Account balance is too low to process this payment",
    "balance": 3000,
    "required": 5000,
    "currency": "USD"
}
```

## Error Response Patterns

### Validation Errors (422)

```json
{
    "type": "https://api.example.com/errors/validation",
    "title": "Validation Error",
    "status": 422,
    "detail": "One or more fields failed validation",
    "errors": [
        {"field": "email", "message": "Invalid email format", "code": "INVALID_FORMAT"},
        {"field": "name", "message": "Required field", "code": "REQUIRED"}
    ]
}
```

### Business Logic Errors (409/422)

```json
{
    "type": "https://api.example.com/errors/order-already-confirmed",
    "title": "Order Already Confirmed",
    "status": 409,
    "detail": "Order ORD-123 has already been confirmed and cannot be modified",
    "order_id": "ORD-123",
    "current_status": "confirmed"
}
```

### Authentication Errors (401)

```json
{
    "type": "https://api.example.com/errors/authentication",
    "title": "Authentication Required",
    "status": 401,
    "detail": "The access token is expired or invalid"
}
```

### Authorization Errors (403)

```json
{
    "type": "https://api.example.com/errors/forbidden",
    "title": "Forbidden",
    "status": 403,
    "detail": "You do not have permission to access this resource"
}
```

### Not Found (404)

```json
{
    "type": "https://api.example.com/errors/not-found",
    "title": "Resource Not Found",
    "status": 404,
    "detail": "Order with ID ORD-999 was not found",
    "resource_type": "Order",
    "resource_id": "ORD-999"
}
```

### Rate Limiting (429)

```json
{
    "type": "https://api.example.com/errors/rate-limited",
    "title": "Too Many Requests",
    "status": 429,
    "detail": "Rate limit exceeded. Try again in 30 seconds",
    "retry_after": 30
}
```

Headers to include:
```
Retry-After: 30
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1706140800
```

### Server Errors (500)

```json
{
    "type": "https://api.example.com/errors/internal",
    "title": "Internal Server Error",
    "status": 500,
    "detail": "An unexpected error occurred. Please try again later",
    "trace_id": "abc-123-def-456"
}
```

Never expose stack traces, database errors, or internal details in production.

## Error Codes Strategy

### Domain-Specific Error Codes

```
ORDER_NOT_FOUND          → 404
ORDER_ALREADY_CONFIRMED  → 409
ORDER_TOTAL_EXCEEDED     → 422
PAYMENT_DECLINED         → 422
PAYMENT_GATEWAY_ERROR    → 502
INVENTORY_INSUFFICIENT   → 422
```

### Error Code Structure

```
{DOMAIN}_{ERROR_TYPE}

Examples:
AUTH_TOKEN_EXPIRED
AUTH_INVALID_CREDENTIALS
ORDER_INVALID_STATUS_TRANSITION
PAYMENT_CARD_DECLINED
INVENTORY_OUT_OF_STOCK
```

### Error Catalog

Maintain a central error catalog:

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Error;

enum ErrorCode: string
{
    // Authentication
    case AUTH_TOKEN_EXPIRED = 'AUTH_TOKEN_EXPIRED';
    case AUTH_INVALID_CREDENTIALS = 'AUTH_INVALID_CREDENTIALS';

    // Orders
    case ORDER_NOT_FOUND = 'ORDER_NOT_FOUND';
    case ORDER_ALREADY_CONFIRMED = 'ORDER_ALREADY_CONFIRMED';
    case ORDER_INVALID_TRANSITION = 'ORDER_INVALID_TRANSITION';

    // Payments
    case PAYMENT_DECLINED = 'PAYMENT_DECLINED';
    case PAYMENT_GATEWAY_ERROR = 'PAYMENT_GATEWAY_ERROR';

    // Inventory
    case INVENTORY_INSUFFICIENT = 'INVENTORY_INSUFFICIENT';

    public function httpStatus(): int
    {
        return match ($this) {
            self::AUTH_TOKEN_EXPIRED, self::AUTH_INVALID_CREDENTIALS => 401,
            self::ORDER_NOT_FOUND => 404,
            self::ORDER_ALREADY_CONFIRMED, self::ORDER_INVALID_TRANSITION => 409,
            self::PAYMENT_DECLINED, self::INVENTORY_INSUFFICIENT => 422,
            self::PAYMENT_GATEWAY_ERROR => 502,
        };
    }

    public function title(): string
    {
        return match ($this) {
            self::AUTH_TOKEN_EXPIRED => 'Token Expired',
            self::AUTH_INVALID_CREDENTIALS => 'Invalid Credentials',
            self::ORDER_NOT_FOUND => 'Order Not Found',
            self::ORDER_ALREADY_CONFIRMED => 'Order Already Confirmed',
            self::ORDER_INVALID_TRANSITION => 'Invalid Status Transition',
            self::PAYMENT_DECLINED => 'Payment Declined',
            self::PAYMENT_GATEWAY_ERROR => 'Payment Gateway Error',
            self::INVENTORY_INSUFFICIENT => 'Insufficient Inventory',
        };
    }
}
```

## GraphQL Error Patterns

### Standard GraphQL Errors

```json
{
    "data": null,
    "errors": [
        {
            "message": "Order not found",
            "locations": [{"line": 2, "column": 3}],
            "path": ["order"],
            "extensions": {
                "code": "ORDER_NOT_FOUND",
                "order_id": "ORD-999"
            }
        }
    ]
}
```

### Partial Response with Errors

```json
{
    "data": {
        "order": {
            "id": "ORD-123",
            "status": "pending",
            "customer": null
        }
    },
    "errors": [
        {
            "message": "Customer service temporarily unavailable",
            "path": ["order", "customer"],
            "extensions": {
                "code": "SERVICE_UNAVAILABLE",
                "service": "customer-service"
            }
        }
    ]
}
```

### GraphQL Error Categories

| Category | When | Example |
|----------|------|---------|
| Syntax Error | Invalid query | Missing closing brace |
| Validation Error | Schema mismatch | Unknown field |
| Execution Error | Runtime failure | Service unavailable |
| Business Error | Domain violation | Insufficient funds |

## PHP Problem Details Implementation

### ProblemDetails Value Object

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Error;

final readonly class ProblemDetails
{
    /**
     * @param array<string, mixed> $extensions
     */
    public function __construct(
        public int $status,
        public string $title,
        public string $detail,
        public ?string $type = null,
        public ?string $instance = null,
        public array $extensions = [],
    ) {}

    public function toArray(): array
    {
        return array_filter(
            [
                'type' => $this->type,
                'title' => $this->title,
                'status' => $this->status,
                'detail' => $this->detail,
                'instance' => $this->instance,
                ...$this->extensions,
            ],
            static fn(mixed $value): bool => $value !== null,
        );
    }
}
```

### Error Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Responder;

use Domain\Shared\Error\ProblemDetails;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class ErrorResponder
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {}

    public function respond(ProblemDetails $problem): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($problem->toArray(), JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE),
        );

        return $this->responseFactory
            ->createResponse($problem->status)
            ->withHeader('Content-Type', 'application/problem+json')
            ->withBody($body);
    }

    public function validationError(array $errors): ResponseInterface
    {
        $problem = new ProblemDetails(
            status: 422,
            title: 'Validation Error',
            detail: 'One or more fields failed validation',
            type: 'https://api.example.com/errors/validation',
            extensions: ['errors' => $errors],
        );

        return $this->respond($problem);
    }

    public function notFound(string $resourceType, string $resourceId): ResponseInterface
    {
        $problem = new ProblemDetails(
            status: 404,
            title: 'Resource Not Found',
            detail: sprintf('%s with ID %s was not found', $resourceType, $resourceId),
            type: 'https://api.example.com/errors/not-found',
            extensions: [
                'resource_type' => $resourceType,
                'resource_id' => $resourceId,
            ],
        );

        return $this->respond($problem);
    }
}
```

### Exception-to-Problem Mapping

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Middleware;

use Domain\Shared\Exception\DomainException;
use Domain\Shared\Exception\EntityNotFoundException;
use Domain\Shared\Exception\ValidationException;
use Domain\Shared\Error\ProblemDetails;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Psr\Log\LoggerInterface;

final readonly class ExceptionToProblemsMiddleware implements MiddlewareInterface
{
    public function __construct(
        private ErrorResponder $errorResponder,
        private LoggerInterface $logger,
    ) {}

    public function process(
        ServerRequestInterface $request,
        RequestHandlerInterface $handler,
    ): ResponseInterface {
        try {
            return $handler->handle($request);
        } catch (ValidationException $e) {
            return $this->errorResponder->validationError($e->errors());
        } catch (EntityNotFoundException $e) {
            return $this->errorResponder->notFound($e->entityType(), $e->entityId());
        } catch (DomainException $e) {
            $problem = new ProblemDetails(
                status: 422,
                title: $e->errorTitle(),
                detail: $e->getMessage(),
                type: $e->errorType(),
            );
            return $this->errorResponder->respond($problem);
        } catch (\Throwable $e) {
            $this->logger->error('Unhandled exception', [
                'exception' => $e,
                'request_uri' => (string) $request->getUri(),
            ]);

            $problem = new ProblemDetails(
                status: 500,
                title: 'Internal Server Error',
                detail: 'An unexpected error occurred',
            );
            return $this->errorResponder->respond($problem);
        }
    }
}
```
