# Responder Templates

Additional templates for Responder generation.

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

## Abstract JSON Responder

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

    protected function accepted(array $data = []): ResponseInterface
    {
        return $this->json($data, 202);
    }

    protected function badRequest(string $message): ResponseInterface
    {
        return $this->json(['error' => $message], 400);
    }

    protected function unauthorized(string $message = 'Unauthorized'): ResponseInterface
    {
        return $this->json(['error' => $message], 401);
    }

    protected function forbidden(string $message = 'Forbidden'): ResponseInterface
    {
        return $this->json(['error' => $message], 403);
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

    protected function tooManyRequests(int $retryAfter = 60): ResponseInterface
    {
        return $this->responseFactory->createResponse(429)
            ->withHeader('Content-Type', 'application/json')
            ->withHeader('Retry-After', (string) $retryAfter)
            ->withBody($this->streamFactory->createStream(
                json_encode(['error' => 'Too many requests'], JSON_THROW_ON_ERROR)
            ));
    }

    protected function internalError(string $message = 'Internal server error'): ResponseInterface
    {
        return $this->json(['error' => $message], 500);
    }
}
```

## Responder with Validation Errors

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

        if ($result->hasValidationErrors()) {
            return $this->unprocessableEntity($this->formatErrors($result->errors()));
        }

        if ($result->isFailure()) {
            return match ($result->failureReason()) {
                'email_exists' => $this->conflict('Email already registered'),
                default => $this->badRequest($result->errorMessage()),
            };
        }

        return $this->created([
            'id' => $result->userId(),
            'email' => $result->email(),
        ]);
    }

    private function formatErrors(array $errors): array
    {
        $formatted = [];

        foreach ($errors as $field => $messages) {
            $formatted[] = [
                'field' => $field,
                'messages' => (array) $messages,
            ];
        }

        return $formatted;
    }
}
```

## HTML Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Web\User\Show;

use Application\User\UseCase\GetUserById\GetUserByIdResult;
use Presentation\Shared\Responder\ResponderInterface;
use Presentation\Shared\Template\TemplateRendererInterface;
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

## File Download Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Report\Export;

use Application\Report\UseCase\ExportReport\ExportReportResult;
use Presentation\Shared\Responder\ResponderInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class ExportReportResponder implements ResponderInterface
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {
    }

    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof ExportReportResult);

        if ($result->isFailure()) {
            return $this->json(['error' => $result->errorMessage()], 400);
        }

        $contentType = match ($result->format()) {
            'csv' => 'text/csv',
            'xlsx' => 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'pdf' => 'application/pdf',
            default => 'application/octet-stream',
        };

        $filename = sprintf('report-%s.%s', date('Y-m-d'), $result->format());

        return $this->responseFactory->createResponse()
            ->withHeader('Content-Type', $contentType)
            ->withHeader('Content-Disposition', sprintf('attachment; filename="%s"', $filename))
            ->withHeader('Content-Length', (string) strlen($result->content()))
            ->withBody($this->streamFactory->createStream($result->content()));
    }

    private function json(array $data, int $status): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($data, JSON_THROW_ON_ERROR)
        );

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body);
    }
}
```

## Streaming Responder

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Event\Stream;

use Application\Event\UseCase\StreamEvents\StreamEventsResult;
use Presentation\Shared\Responder\ResponderInterface;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class StreamEventsResponder implements ResponderInterface
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
    ) {
    }

    public function respond(mixed $result): ResponseInterface
    {
        assert($result instanceof StreamEventsResult);

        $body = $this->streamFactory->createStream($result->stream());

        return $this->responseFactory->createResponse()
            ->withHeader('Content-Type', 'text/event-stream')
            ->withHeader('Cache-Control', 'no-cache')
            ->withHeader('Connection', 'keep-alive')
            ->withBody($body);
    }
}
```

## Response DTO Pattern

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\User\Create;

use Domain\User\Entity\User;

final readonly class CreateUserResponse
{
    public function __construct(
        public string $id,
        public string $email,
        public string $name,
        public string $createdAt,
    ) {
    }

    public static function fromEntity(User $user): self
    {
        return new self(
            id: $user->id()->toString(),
            email: $user->email()->value(),
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

## Test Template

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Api\User\Create;

use Application\User\UseCase\CreateUser\CreateUserResult;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\DataProvider;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Presentation\Api\User\Create\CreateUserResponder;
use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;
use Psr\Http\Message\StreamInterface;

#[Group('unit')]
#[CoversClass(CreateUserResponder::class)]
final class CreateUserResponderTest extends TestCase
{
    private CreateUserResponder $responder;
    private int $capturedStatus = 200;

    protected function setUp(): void
    {
        $stream = $this->createMock(StreamInterface::class);

        $streamFactory = $this->createMock(StreamFactoryInterface::class);
        $streamFactory->method('createStream')->willReturn($stream);

        $response = $this->createMock(ResponseInterface::class);
        $response->method('withHeader')->willReturnSelf();
        $response->method('withBody')->willReturnSelf();

        $responseFactory = $this->createMock(ResponseFactoryInterface::class);
        $responseFactory->method('createResponse')->willReturnCallback(
            function (int $status = 200) use ($response) {
                $this->capturedStatus = $status;
                $mock = clone $response;
                $mock->method('getStatusCode')->willReturn($status);
                return $mock;
            }
        );

        $this->responder = new CreateUserResponder($responseFactory, $streamFactory);
    }

    public function testSuccessReturns201(): void
    {
        $result = CreateUserResult::success('user-123', 'test@example.com');

        $response = $this->responder->respond($result);

        self::assertSame(201, $response->getStatusCode());
    }

    public function testEmailExistsReturns409(): void
    {
        $result = CreateUserResult::failure('email_exists', 'Email exists');

        $response = $this->responder->respond($result);

        self::assertSame(409, $response->getStatusCode());
    }

    public function testInvalidEmailReturns400(): void
    {
        $result = CreateUserResult::failure('invalid_email', 'Invalid email');

        $response = $this->responder->respond($result);

        self::assertSame(400, $response->getStatusCode());
    }

    #[DataProvider('failureProvider')]
    public function testFailureStatuses(string $reason, int $expectedStatus): void
    {
        $result = CreateUserResult::failure($reason, 'Error message');

        $response = $this->responder->respond($result);

        self::assertSame($expectedStatus, $response->getStatusCode());
    }

    public static function failureProvider(): array
    {
        return [
            'email_exists' => ['email_exists', 409],
            'invalid_email' => ['invalid_email', 400],
            'unknown' => ['unknown', 400],
        ];
    }
}
```
