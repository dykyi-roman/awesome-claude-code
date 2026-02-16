# Action Templates

Additional templates for Action generation.

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

## Abstract Action (Optional)

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

    protected function getBody(ServerRequestInterface $request): array
    {
        return (array) $request->getParsedBody();
    }
}
```

## Request DTO Template

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\{Context}\{Action};

use Psr\Http\Message\ServerRequestInterface;

final readonly class {Action}Request
{
    public function __construct(
        {properties}
    ) {
    }

    public static function fromRequest(ServerRequestInterface $request): self
    {
        $body = (array) $request->getParsedBody();

        return new self(
            {propertyMapping}
        );
    }
}
```

## Action with Request DTO

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

## Action with File Upload

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Document\Upload;

use Application\Document\UseCase\UploadDocument\UploadDocumentCommand;
use Application\Document\UseCase\UploadDocument\UploadDocumentHandler;
use Presentation\Shared\Exception\InvalidRequestException;
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
        $file = $this->extractFile($request);

        $command = new UploadDocumentCommand(
            filename: $file->getClientFilename() ?? 'unnamed',
            mimeType: $file->getClientMediaType() ?? 'application/octet-stream',
            stream: $file->getStream(),
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }

    private function extractFile(ServerRequestInterface $request): UploadedFileInterface
    {
        $uploadedFiles = $request->getUploadedFiles();

        /** @var UploadedFileInterface|null $file */
        $file = $uploadedFiles['document'] ?? null;

        if ($file === null || $file->getError() !== UPLOAD_ERR_OK) {
            throw new InvalidRequestException('No file uploaded or upload error');
        }

        return $file;
    }
}
```

## Action with Authentication

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Profile\Update;

use Application\User\UseCase\UpdateProfile\UpdateProfileCommand;
use Application\User\UseCase\UpdateProfile\UpdateProfileHandler;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class UpdateProfileAction
{
    public function __construct(
        private UpdateProfileHandler $handler,
        private UpdateProfileResponder $responder,
    ) {
    }

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        // User ID from authentication middleware
        $userId = $request->getAttribute('user_id');
        $body = (array) $request->getParsedBody();

        $command = new UpdateProfileCommand(
            userId: $userId,
            name: $body['name'] ?? null,
            avatar: $body['avatar'] ?? null,
        );

        $result = $this->handler->handle($command);

        return $this->responder->respond($result);
    }
}
```

## Test Template with Full Mocks

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\User\Create;

use Application\User\UseCase\CreateUser\CreateUserCommand;
use Application\User\UseCase\CreateUser\CreateUserHandler;
use Application\User\UseCase\CreateUser\CreateUserResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\MockObject\MockObject;
use PHPUnit\Framework\TestCase;
use Presentation\Api\User\Create\CreateUserAction;
use Presentation\Api\User\Create\CreateUserResponder;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamInterface;

#[Group('unit')]
#[CoversClass(CreateUserAction::class)]
final class CreateUserActionTest extends TestCase
{
    private CreateUserHandler&MockObject $handler;
    private CreateUserResponder&MockObject $responder;
    private CreateUserAction $action;

    protected function setUp(): void
    {
        $this->handler = $this->createMock(CreateUserHandler::class);
        $this->responder = $this->createMock(CreateUserResponder::class);
        $this->action = new CreateUserAction($this->handler, $this->responder);
    }

    public function testCreatesUserWithValidInput(): void
    {
        $request = $this->createRequest([
            'email' => 'test@example.com',
            'name' => 'Test User',
        ]);

        $result = CreateUserResult::success('user-123');
        $response = $this->createMock(ResponseInterface::class);

        $this->handler
            ->expects($this->once())
            ->method('handle')
            ->with($this->callback(fn (CreateUserCommand $cmd) =>
                $cmd->email === 'test@example.com' &&
                $cmd->name === 'Test User'
            ))
            ->willReturn($result);

        $this->responder
            ->expects($this->once())
            ->method('respond')
            ->with($result)
            ->willReturn($response);

        $actual = ($this->action)($request);

        self::assertSame($response, $actual);
    }

    public function testHandlesEmptyEmail(): void
    {
        $request = $this->createRequest([
            'name' => 'Test User',
        ]);

        $result = CreateUserResult::failure('invalid_email', 'Email required');
        $response = $this->createMock(ResponseInterface::class);

        $this->handler
            ->expects($this->once())
            ->method('handle')
            ->with($this->callback(fn (CreateUserCommand $cmd) =>
                $cmd->email === ''
            ))
            ->willReturn($result);

        $this->responder
            ->expects($this->once())
            ->method('respond')
            ->with($result)
            ->willReturn($response);

        ($this->action)($request);
    }

    private function createRequest(array $body): ServerRequestInterface&MockObject
    {
        $stream = $this->createMock(StreamInterface::class);
        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getParsedBody')->willReturn($body);
        $request->method('getBody')->willReturn($stream);

        return $request;
    }
}
```

## DI Container Configuration

### Symfony

```yaml
# config/services.yaml
services:
    Presentation\Api\User\Create\CreateUserAction:
        arguments:
            $handler: '@Application\User\UseCase\CreateUser\CreateUserHandler'
            $responder: '@Presentation\Api\User\Create\CreateUserResponder'
        tags: ['controller.service_arguments']
```

### PHP-DI

```php
<?php

use Presentation\Api\User\Create\CreateUserAction;
use Application\User\UseCase\CreateUser\CreateUserHandler;
use Presentation\Api\User\Create\CreateUserResponder;

return [
    CreateUserAction::class => function ($c) {
        return new CreateUserAction(
            $c->get(CreateUserHandler::class),
            $c->get(CreateUserResponder::class),
        );
    },
];
```

## Route Configuration

### Slim

```php
<?php

$app->post('/users', CreateUserAction::class);
$app->get('/users/{id}', GetUserByIdAction::class);
$app->put('/users/{id}', UpdateUserAction::class);
$app->delete('/users/{id}', DeleteUserAction::class);
```

### Symfony

```yaml
# config/routes.yaml
create_user:
    path: /users
    controller: Presentation\Api\User\Create\CreateUserAction
    methods: POST

get_user:
    path: /users/{id}
    controller: Presentation\Api\User\GetById\GetUserByIdAction
    methods: GET
```
