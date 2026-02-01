# Action Patterns Reference

Detailed patterns and best practices for ADR Action classes.

## Action Interface

```php
<?php

declare(strict_types=1);

namespace Presentation\Shared\Action;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

interface ActionInterface
{
    public function __invoke(ServerRequestInterface $request): ResponseInterface;
}
```

## Base Action (Optional)

```php
<?php

declare(strict_types=1);

namespace Presentation\Shared\Action;

use Psr\Http\Message\ServerRequestInterface;

abstract readonly class AbstractAction implements ActionInterface
{
    protected function getAttribute(ServerRequestInterface $request, string $name, mixed $default = null): mixed
    {
        return $request->getAttribute($name, $default);
    }

    protected function getQueryParam(ServerRequestInterface $request, string $name, mixed $default = null): mixed
    {
        return $request->getQueryParams()[$name] ?? $default;
    }

    protected function getBodyParam(ServerRequestInterface $request, string $name, mixed $default = null): mixed
    {
        $body = (array) $request->getParsedBody();
        return $body[$name] ?? $default;
    }
}
```

## Action Patterns by HTTP Method

### GET Action (Read)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\GetById;

use Application\User\UseCase\GetUserById\GetUserByIdQuery;
use Application\User\UseCase\GetUserById\GetUserByIdHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class GetUserByIdAction
{
    public function __construct(
        private GetUserByIdHandler $handler,
        private GetUserByIdResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('id');

        $query = new GetUserByIdQuery(userId: $userId);
        $result = $this->handler->handle($query);

        return $this->responder->respond($result);
    }
}
```

### POST Action (Create)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Create;

use Application\User\UseCase\CreateUser\CreateUserCommand;
use Application\User\UseCase\CreateUser\CreateUserHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateUserAction
{
    public function __construct(
        private CreateUserHandler $handler,
        private CreateUserResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        $command = new CreateUserCommand(
            email: $body['email'] ?? '',
            name: $body['name'] ?? '',
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

### PUT/PATCH Action (Update)

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Update;

use Application\User\UseCase\UpdateUser\UpdateUserCommand;
use Application\User\UseCase\UpdateUser\UpdateUserHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class UpdateUserAction
{
    public function __construct(
        private UpdateUserHandler $handler,
        private UpdateUserResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('id');
        $body = (array) $request->getParsedBody();

        $command = new UpdateUserCommand(
            userId: $userId,
            name: $body['name'] ?? null,
            email: $body['email'] ?? null,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

### DELETE Action

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Delete;

use Application\User\UseCase\DeleteUser\DeleteUserCommand;
use Application\User\UseCase\DeleteUser\DeleteUserHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class DeleteUserAction
{
    public function __construct(
        private DeleteUserHandler $handler,
        private DeleteUserResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $userId = $request->getAttribute('id');

        $command = new DeleteUserCommand(userId: $userId);
        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Action with Request DTO

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Create;

use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderRequest
{
    public function __construct(
        public string $customerId,
        public array $items,
        public ?string $couponCode,
    ) {
    }

    public static function fromRequest(ServerRequestInterface $request): self
    {
        $body = (array) $request->getParsedBody();

        return new self(
            customerId: $body['customer_id'] ?? '',
            items: $body['items'] ?? [],
            couponCode: $body['coupon_code'] ?? null,
        );
    }
}
```

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Order\Create;

use Application\Order\UseCase\CreateOrder\CreateOrderCommand;
use Application\Order\UseCase\CreateOrder\CreateOrderHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderHandler $handler,
        private CreateOrderResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $input = CreateOrderRequest::fromRequest($request);

        $command = new CreateOrderCommand(
            customerId: $input->customerId,
            items: $input->items,
            couponCode: $input->couponCode,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Action with Validation

Validation should happen in Domain/Application layer, but input parsing can catch obvious issues:

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Create;

use Application\User\UseCase\CreateUser\CreateUserCommand;
use Application\User\UseCase\CreateUser\CreateUserHandler;
use Presentation\Shared\Exception\InvalidRequestException;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CreateUserAction
{
    public function __construct(
        private CreateUserHandler $handler,
        private CreateUserResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        // Only structural validation (required fields present)
        if (!isset($body['email'], $body['name'])) {
            throw new InvalidRequestException('email and name are required');
        }

        $command = new CreateUserCommand(
            email: $body['email'],
            name: $body['name'],
        );

        // Domain validation happens in handler
        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Action with File Upload

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Document\Upload;

use Application\Document\UseCase\UploadDocument\UploadDocumentCommand;
use Application\Document\UseCase\UploadDocument\UploadDocumentHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\UploadedFileInterface;

final readonly class UploadDocumentAction
{
    public function __construct(
        private UploadDocumentHandler $handler,
        private UploadDocumentResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $uploadedFiles = $request->getUploadedFiles();

        /** @var UploadedFileInterface|null $file */
        $file = $uploadedFiles['document'] ?? null;

        if ($file === null || $file->getError() !== UPLOAD_ERR_OK) {
            return $this->responder->respondWithError('No file uploaded');
        }

        $command = new UploadDocumentCommand(
            filename: $file->getClientFilename() ?? 'unnamed',
            mimeType: $file->getClientMediaType() ?? 'application/octet-stream',
            stream: $file->getStream(),
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Naming Conventions

| HTTP Method | Action Name | Example |
|-------------|-------------|---------|
| GET (single) | Get{Resource}ByIdAction | GetUserByIdAction |
| GET (list) | List{Resource}sAction | ListUsersAction |
| POST | Create{Resource}Action | CreateUserAction |
| PUT | Update{Resource}Action | UpdateUserAction |
| PATCH | Patch{Resource}Action | PatchUserAction |
| DELETE | Delete{Resource}Action | DeleteUserAction |

## Best Practices

1. **Single Responsibility**: One action = one HTTP endpoint
2. **Thin Actions**: Only input parsing and domain invocation
3. **No Response Building**: Delegate to Responder
4. **No Business Logic**: Delegate to Domain/Application
5. **Use DTOs**: Create Request DTOs for complex inputs
6. **Type Safety**: Use typed properties and return types
