# MVC vs ADR Comparison

Detailed comparison between traditional MVC and Action-Domain-Responder patterns.

## Structural Comparison

### MVC Controller

```php
<?php

declare(strict_types=1);

namespace App\Controller;

use App\Entity\User;
use App\Repository\UserRepository;
use Symfony\Bundle\FrameworkBundle\Controller\AbstractController;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;

class UserController extends AbstractController
{
    public function __construct(
        private UserRepository $userRepository,
    ) {
    }

    // Multiple actions in one class
    public function index(): JsonResponse
    {
        $users = $this->userRepository->findAll();
        return $this->json(['users' => $users]);
    }

    public function show(int $id): JsonResponse
    {
        $user = $this->userRepository->find($id);

        if (!$user) {
            return $this->json(['error' => 'Not found'], 404);
        }

        return $this->json(['user' => $user]);
    }

    public function create(Request $request): JsonResponse
    {
        $data = json_decode($request->getContent(), true);

        // Validation mixed with controller
        if (empty($data['email'])) {
            return $this->json(['error' => 'Email required'], 400);
        }

        // Business logic mixed with controller
        $user = new User();
        $user->setEmail($data['email']);
        $user->setName($data['name'] ?? '');

        $this->userRepository->save($user);

        // Response building in controller
        return $this->json([
            'id' => $user->getId(),
            'email' => $user->getEmail(),
        ], 201);
    }

    public function update(int $id, Request $request): JsonResponse
    {
        $user = $this->userRepository->find($id);

        if (!$user) {
            return $this->json(['error' => 'Not found'], 404);
        }

        $data = json_decode($request->getContent(), true);
        $user->setName($data['name'] ?? $user->getName());

        $this->userRepository->save($user);

        return $this->json(['user' => $user]);
    }

    public function delete(int $id): Response
    {
        $user = $this->userRepository->find($id);

        if (!$user) {
            return $this->json(['error' => 'Not found'], 404);
        }

        $this->userRepository->remove($user);

        return new Response(null, 204);
    }
}
```

### ADR Equivalent

```php
<?php
// CreateUserAction.php
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

```php
<?php
// CreateUserResponder.php
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
                'email_exists' => $this->conflict('Email already exists'),
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

```php
<?php
// CreateUserHandler.php (Application Layer)
declare(strict_types=1);

namespace Application\User\UseCase\CreateUser;

final readonly class CreateUserHandler
{
    public function __construct(
        private UserRepositoryInterface $userRepository,
    ) {
    }

    public function handle(CreateUserCommand $command): CreateUserResult
    {
        try {
            $email = new Email($command->email);
        } catch (InvalidArgumentException $e) {
            return CreateUserResult::failure('invalid_email', $e->getMessage());
        }

        if ($this->userRepository->existsByEmail($email)) {
            return CreateUserResult::failure('email_exists', 'Email already exists');
        }

        $user = new User(
            id: UserId::generate(),
            email: $email,
            name: $command->name,
        );

        $this->userRepository->save($user);

        return CreateUserResult::success($user);
    }
}
```

## Side-by-Side Comparison

| Aspect | MVC Controller | ADR |
|--------|---------------|-----|
| **Actions per class** | Multiple (5+) | One |
| **Responsibility** | Mixed (input, logic, output) | Separated |
| **Response building** | In controller | In Responder |
| **Business logic** | Often in controller | In Domain/Application |
| **Testability** | Harder (many concerns) | Easier (single concern) |
| **File count** | Fewer, larger files | More, smaller files |
| **Reusability** | Low (coupled to HTTP) | Higher (separated concerns) |

## Responsibility Distribution

### MVC

```
Controller
├── Parse request input
├── Validate input
├── Execute business logic
├── Handle errors
├── Build response
└── Return response
```

### ADR

```
Action
├── Parse request input
└── Invoke domain

Domain (Application/Domain Layer)
├── Validate business rules
├── Execute business logic
└── Return result

Responder
├── Handle result states
├── Build response
└── Return response
```

## Code Metrics Comparison

### Lines per File

| Component | MVC | ADR |
|-----------|-----|-----|
| Controller/Action | 150-300 | 20-40 |
| Responder | N/A | 30-60 |
| Handler | N/A | 30-50 |
| **Total** | 150-300 | 80-150 |

### Cyclomatic Complexity

| Pattern | Typical Complexity |
|---------|-------------------|
| MVC Controller method | 5-15 |
| ADR Action | 1-2 |
| ADR Responder | 2-5 |
| Handler | 3-8 |

## Testing Comparison

### MVC Testing

```php
<?php

class UserControllerTest extends WebTestCase
{
    public function testCreate(): void
    {
        // Need full HTTP stack
        $client = static::createClient();

        $client->request('POST', '/users', [], [], [
            'CONTENT_TYPE' => 'application/json',
        ], json_encode(['email' => 'test@example.com']));

        $this->assertResponseStatusCodeSame(201);
    }
}
```

### ADR Testing

```php
<?php

// Test Action in isolation
final class CreateUserActionTest extends TestCase
{
    public function testInvokesHandlerWithCommand(): void
    {
        $handler = $this->createMock(CreateUserHandler::class);
        $handler->expects($this->once())
            ->method('handle')
            ->with($this->callback(fn ($cmd) =>
                $cmd->email === 'test@example.com'
            ));

        $responder = $this->createMock(CreateUserResponder::class);
        $responder->method('respond')->willReturn($this->createMock(ResponseInterface::class));

        $action = new CreateUserAction($handler, $responder);
        $action($this->createRequest(['email' => 'test@example.com']));
    }
}

// Test Responder in isolation
final class CreateUserResponderTest extends TestCase
{
    public function testSuccessReturns201(): void
    {
        $responder = new CreateUserResponder(
            $this->responseFactory,
            $this->streamFactory,
        );

        $result = CreateUserResult::success($this->createUser());
        $response = $responder->respond($result);

        $this->assertEquals(201, $response->getStatusCode());
    }

    public function testEmailExistsReturns409(): void
    {
        $responder = new CreateUserResponder(
            $this->responseFactory,
            $this->streamFactory,
        );

        $result = CreateUserResult::failure('email_exists', 'Email exists');
        $response = $responder->respond($result);

        $this->assertEquals(409, $response->getStatusCode());
    }
}

// Test Handler in isolation
final class CreateUserHandlerTest extends TestCase
{
    public function testCreatesUser(): void
    {
        $repository = $this->createMock(UserRepositoryInterface::class);
        $repository->expects($this->once())->method('save');

        $handler = new CreateUserHandler($repository);
        $result = $handler->handle(new CreateUserCommand(
            email: 'test@example.com',
            name: 'Test User',
        ));

        $this->assertTrue($result->isSuccess());
    }
}
```

## When to Use Each

### Use MVC When

- Simple CRUD applications
- Small team with MVC experience
- Rapid prototyping
- Framework provides strong MVC support

### Use ADR When

- Complex domain logic
- High testability requirements
- Multiple response formats needed
- Clean separation of concerns is priority
- Working with DDD
- Large team with clear boundaries

## Migration Path: MVC → ADR

1. **Extract Responder**: Move response building to separate class
2. **Single Action**: Split controller into one action per class
3. **Extract Handler**: Move business logic to Application layer
4. **Add Result Objects**: Replace exceptions with Result objects
5. **Refactor Tests**: Test each component in isolation
