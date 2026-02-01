# Responder Patterns Reference

Detailed patterns and best practices for ADR Responder classes.

## Responder Interface

```php
<?php

declare(strict_types=1);

namespace Presentation\Shared\Responder;

use Psr\Http\Message\ResponseInterface;

interface ResponderInterface
{
    public function respond(mixed $result): ResponseInterface;
}
```

## Base JSON Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Shared\Responder;

use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

abstract readonly class AbstractJsonResponder implements ResponderInterface
{
    public function __construct(
        protected ResponseFactoryInterface $responseFactory,
        protected StreamFactoryInterface $streamFactory,
    ) {
    }

    protected function json(array $data, int $status = 200): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($data, JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE)
        );

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'application/json; charset=utf-8')
            ->withBody($body);
    }

    protected function noContent(): ResponseInterface
    {
        return $this->responseFactory->createResponse(204);
    }

    protected function created(array $data): ResponseInterface
    {
        return $this->json($data, 201);
    }

    protected function badRequest(string $message): ResponseInterface
    {
        return $this->json(['error' => $message], 400);
    }

    protected function notFound(string $message = 'Resource not found'): ResponseInterface
    {
        return $this->json(['error' => $message], 404);
    }

    protected function conflict(string $message): ResponseInterface
    {
        return $this->json(['error' => $message], 409);
    }

    protected function unprocessableEntity(array $errors): ResponseInterface
    {
        return $this->json(['errors' => $errors], 422);
    }
}
```

## Responder Patterns by Use Case

### Create Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Create;

use Application\User\UseCase\CreateUser\CreateUserResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class CreateUserResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof CreateUserResult);

        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'email_exists' => $this->conflict('User with this email already exists'),
                'invalid_email' => $this->badRequest('Invalid email format'),
                default => $this->badRequest($result->errorMessage()),
            };
        }

        return $this->created([
            'id' => $result->userId(),
            'email' => $result->email(),
        ]);
    }
}
```

### Get Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\GetById;

use Application\User\UseCase\GetUserById\GetUserByIdResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class GetUserByIdResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof GetUserByIdResult);

        if ($result->isNotFound()) {
            return $this->notFound('User not found');
        }

        $user = $result->user();

        return $this->json([
            'id' => $user->id(),
            'email' => $user->email(),
            'name' => $user->name(),
            'created_at' => $user->createdAt()->format('c'),
        ]);
    }
}
```

### List Responder with Pagination

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\ListAll;

use Application\User\UseCase\ListUsers\ListUsersResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class ListUsersResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof ListUsersResult);

        $users = array_map(
            fn ($user) => [
                'id' => $user->id(),
                'email' => $user->email(),
                'name' => $user->name(),
            ],
            $result->users()
        );

        return $this->json([
            'data' => $users,
            'meta' => [
                'total' => $result->total(),
                'page' => $result->page(),
                'per_page' => $result->perPage(),
                'total_pages' => $result->totalPages(),
            ],
            'links' => [
                'self' => $result->currentPageUrl(),
                'next' => $result->nextPageUrl(),
                'prev' => $result->previousPageUrl(),
            ],
        ]);
    }
}
```

### Update Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Update;

use Application\User\UseCase\UpdateUser\UpdateUserResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class UpdateUserResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof UpdateUserResult);

        if ($result->isNotFound()) {
            return $this->notFound('User not found');
        }

        if ($result->isFailure()) {
            return $this->badRequest($result->errorMessage());
        }

        $user = $result->user();

        return $this->json([
            'id' => $user->id(),
            'email' => $user->email(),
            'name' => $user->name(),
            'updated_at' => $user->updatedAt()->format('c'),
        ]);
    }
}
```

### Delete Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Delete;

use Application\User\UseCase\DeleteUser\DeleteUserResult;
use Presentation\Shared\Responder\AbstractJsonResponder;
use Psr\Http\Message\ResponseInterface;

final readonly class DeleteUserResponder extends AbstractJsonResponder
{
    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof DeleteUserResult);

        if ($result->isNotFound()) {
            return $this->notFound('User not found');
        }

        if ($result->isFailure()) {
            return $this->badRequest($result->errorMessage());
        }

        return $this->noContent();
    }
}
```

## HTML Responder (Web)

```php
<?php

declare(strict_types=1);

namespace Presentation\Web\User\Show;

use Application\User\UseCase\GetUserById\GetUserByIdResult;
use Presentation\Shared\Responder\ResponderInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class ShowUserResponder implements ResponderInterface
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
        private TemplateRendererInterface $templateRenderer,
    ) {
    }

    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof GetUserByIdResult);

        if ($result->isNotFound()) {
            return $this->renderError('User not found', 404);
        }

        $html = $this->templateRenderer->render('user/show', [
            'user' => $result->user(),
        ]);

        return $this->html($html);
    }

    private function html(string $content, int $status = 200): ResponseInterface
    {
        $body = $this->streamFactory->createStream($content);

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'text/html; charset=utf-8')
            ->withBody($body);
    }

    private function renderError(string $message, int $status): ResponseInterface
    {
        $html = $this->templateRenderer->render('error', [
            'message' => $message,
            'status' => $status,
        ]);

        return $this->html($html, $status);
    }
}
```

## Content Negotiation Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\GetById;

use Application\User\UseCase\GetUserById\GetUserByIdResult;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class GetUserByIdResponder
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {
    }

    public function respond(GetUserByIdResult $result, ServerRequestInterface $request): ResponseInterface
    {
        if ($result->isNotFound()) {
            return $this->notFound($request);
        }

        $accept = $request->getHeaderLine('Accept');

        return match (true) {
            str_contains($accept, 'application/xml') => $this->xml($result),
            default => $this->json($result),
        };
    }

    private function json(GetUserByIdResult $result): ResponseInterface
    {
        $user = $result->user();
        $body = json_encode([
            'id' => $user->id(),
            'email' => $user->email(),
        ], JSON_THROW_ON_ERROR);

        return $this->response($body, 'application/json');
    }

    private function xml(GetUserByIdResult $result): ResponseInterface
    {
        $user = $result->user();
        $body = sprintf(
            '<?xml version="1.0"?><user><id>%s</id><email>%s</email></user>',
            $user->id(),
            htmlspecialchars($user->email())
        );

        return $this->response($body, 'application/xml');
    }

    private function response(string $body, string $contentType, int $status = 200): ResponseInterface
    {
        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', $contentType)
            ->withBody($this->streamFactory->createStream($body));
    }
}
```

## Response DTO Pattern

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Create;

final readonly class CreateUserResponse
{
    public function __construct(
        public string $id,
        public string $email,
        public string $name,
        public string $createdAt,
    ) {
    }

    public static function fromResult(CreateUserResult $result): self
    {
        $user = $result->user();

        return new self(
            id: $user->id(),
            email: $user->email(),
            name: $user->name(),
            createdAt: $user->createdAt()->format('c'),
        );
    }

    public function toArray(): array
    {
        return [
            'id' => $this->id,
            'email' => $this->email,
            'name' => $this->name,
            'created_at' => $this->createdAt,
        ];
    }
}
```

## Best Practices

1. **Complete Response Building**: Set status, headers, and body
2. **No Business Logic**: Only format/transform data
3. **No Domain Dependencies**: Don't call repositories or services
4. **Content Type**: Always set appropriate Content-Type header
5. **Error Handling**: Map domain errors to HTTP status codes
6. **Immutability**: Use readonly classes
7. **PSR Compliance**: Use PSR-7 and PSR-17 interfaces
