# Application Exception (Layered Architecture)

In the 3-layer Domain-centric Layered Architecture this skill describes, the **Application layer** hosts exception classes that signal request-handling failures distinct from domain-rule violations. Examples: `InvalidRequestException`, `AccessDeniedException`, `RateLimitExceededException`.

The pattern is Layered-specific in naming and placement — MVC has no Application layer, and Clean Architecture distributes these differently. In Layered 3-tier (Domain-centric), these exceptions live under `Application/Exception/` and translate to HTTP via a subscriber.

## Folder layout

```
Application/Exception/
├── AccessDeniedException.php
├── InvalidRequestException.php
├── RateLimitExceededException.php
└── UnsupportedMediaTypeException.php
```

## Characteristics

- Request-handling failures, **not** business-rule violations (those go to `acc:create-domain-exception`).
- Extend `\RuntimeException` (or a project base).
- One class per failure category; static factories for specific cases.
- No domain knowledge in messages: "Required field missing", not "Order requires customer".
- HTTP-status-translatable, but the mapping itself lives in an exception subscriber (see `acc:create-event-subscriber`) — never in the exception class.
- Reusable across all Actions / Controllers in the project.

## When to use

| Scenario | Exception type |
|----------|----------------|
| Required input field missing or malformed | `InvalidRequestException` |
| Authentication missing or invalid | `AccessDeniedException` (translates to 401) |
| Authorization (authenticated but lacks permission) | `AccessDeniedException` (translates to 403) |
| Rate limit exceeded | `RateLimitExceededException` (translates to 429) |
| Unsupported media type or accept header | `UnsupportedMediaTypeException` (translates to 415) |
| Domain rule violation | NOT here — use `acc:create-domain-exception` |
| External service failure | Infrastructure exception (502/503/504) — see `acc:create-infrastructure-client` |

## Templates

### InvalidRequestException

```php
<?php

declare(strict_types=1);

namespace Exception;

final class InvalidRequestException extends \RuntimeException
{
    public static function missingField(string $field): self
    {
        return new self(sprintf('Required field "%s" is missing.', $field));
    }

    public static function invalidFormat(string $field, string $expected): self
    {
        return new self(sprintf(
            'Field "%s" has invalid format; expected %s.',
            $field,
            $expected,
        ));
    }

    public static function unsupportedValue(string $field, string $value, array $allowed): self
    {
        return new self(sprintf(
            'Field "%s" has unsupported value "%s"; allowed: %s.',
            $field,
            $value,
            implode(', ', $allowed),
        ));
    }

    /**
     * @param array<string, string> $errors map of field-name → error-message
     */
    public static function validationFailed(array $errors): self
    {
        $exception = new self('Request validation failed.');
        $exception->errors = $errors;

        return $exception;
    }

    /** @var array<string, string> */
    public array $errors = [];
}
```

### AccessDeniedException

```php
<?php

declare(strict_types=1);

namespace Exception;

final class AccessDeniedException extends \RuntimeException
{
    public static function notAuthenticated(): self
    {
        return new self('Authentication required.');
    }

    public static function insufficientPermissions(string $required): self
    {
        return new self(sprintf(
            'Insufficient permissions; "%s" required.',
            $required,
        ));
    }

    public static function tokenExpired(): self
    {
        return new self('Authentication token has expired.');
    }

    public static function tokenInvalid(): self
    {
        return new self('Authentication token is invalid.');
    }
}
```

### RateLimitExceededException

```php
<?php

declare(strict_types=1);

namespace Exception;

final class RateLimitExceededException extends \RuntimeException
{
    public readonly int $retryAfterSeconds;

    private function __construct(string $message, int $retryAfterSeconds)
    {
        parent::__construct($message);
        $this->retryAfterSeconds = $retryAfterSeconds;
    }

    public static function forKey(string $key, int $retryAfterSeconds): self
    {
        return new self(
            sprintf('Rate limit exceeded for "%s".', $key),
            $retryAfterSeconds,
        );
    }
}
```

### Exception subscriber translating to HTTP

The translation from Application exception → HTTP response lives in a subscriber (see `acc:create-event-subscriber`), not in the exception:

```php
<?php

declare(strict_types=1);

namespace Subscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;
use Symfony\Component\HttpKernel\KernelEvents;

final readonly class ApplicationExceptionSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::EXCEPTION => 'onKernelException',
        ];
    }

    public function onKernelException(ExceptionEvent $event): void
    {
        $exception = $event->getThrowable();

        $response = match (true) {
            $exception instanceof InvalidRequestException => new JsonResponse(
                ['error' => $exception->getMessage(), 'fields' => $exception->errors],
                400,
            ),
            $exception instanceof AccessDeniedException => new JsonResponse(
                ['error' => $exception->getMessage()],
                $this->isAuthIssue($exception->getMessage()) ? 401 : 403,
            ),
            $exception instanceof RateLimitExceededException => (new JsonResponse(
                ['error' => $exception->getMessage()],
                429,
            ))->headers->set('Retry-After', (string) $exception->retryAfterSeconds) ?: null,
            default => null,
        };

        if ($response !== null) {
            $event->setResponse($response);
        }
    }

    private function isAuthIssue(string $message): bool
    {
        return str_contains($message, 'Authentication')
            || str_contains($message, 'token');
    }
}
```

## Throwing from an Action / Controller

```php
<?php

declare(strict_types=1);

namespace Action\Create;

final readonly class CreateUserAction
{
    public function __construct(
        private CreateUserUseCase $useCase,
    ) {}

    public function __invoke(ServerRequestInterface $request): ResponseInterface
    {
        $body = (array) $request->getParsedBody();

        if (!isset($body['email'])) {
            throw InvalidRequestException::missingField('email');
        }

        $result = $this->useCase->execute(
            new CreateUserCommand(email: $body['email']),
        );

        return new JsonResponse(['id' => $result->userId()], 201);
    }
}
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| HTTP status code in the exception class | Couples exception to HTTP; can't reuse from CLI | Translate in a subscriber |
| One exception per specific failure (`MissingEmailException`, `MissingNameException`, …) | Class explosion | Single `InvalidRequestException` with factories |
| Domain exception thrown from Action / Controller | Mixes responsibilities | Throw an Application exception at the boundary; let domain throw domain exceptions |
| Application exception swallowed in middleware without logging | Hides bugs | Always log unexpected exceptions before translating |
| Generic `\Exception` thrown from Application code | Can't be caught by category | Use a typed Application exception |
