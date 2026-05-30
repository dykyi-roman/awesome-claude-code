# Routing and HTTP Handling

Symfony routing, invokable controllers, EventSubscribers, and input validation patterns.

## Invokable Controllers (Single Action)

Each controller handles exactly one HTTP action via `__invoke()`.

**Detection:**
```bash
# Controllers with multiple public methods (antipattern)
Grep: "public function (?!__invoke|__construct)" --glob "**/Controller/**/*.php"
Grep: "public function (?!__invoke|__construct)" --glob "**/Action/**/*.php"

# Invokable controllers (good pattern)
Grep: "public function __invoke" --glob "**/Presentation/**/*.php"
```

**Bad — Fat controller with multiple actions:**
```php
<?php

declare(strict_types=1);

namespace Controller;

class OrderController
{
    public function index(): Response { /* ... */ }
    public function create(Request $request): Response { /* ... */ }
    public function show(int $id): Response { /* ... */ }
    public function update(int $id, Request $request): Response { /* ... */ }
    public function delete(int $id): Response { /* ... */ }
}
```

**Good — One action per class:**
```php
<?php

declare(strict_types=1);

namespace Api;

use Command\CreateOrderCommand;
use UseCase\CreateOrderUseCase;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

#[Route('/api/orders', name: 'api_order_create', methods: ['POST'])]
final readonly class CreateOrderAction
{
    public function __construct(
        private CreateOrderUseCase $createOrder,
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $data = $request->toArray();

        $command = new CreateOrderCommand(
            customerId: $data['customer_id'],
            items: $data['items'],
        );

        $orderId = $this->createOrder->execute($command);

        return new JsonResponse(
            data: ['id' => $orderId->value],
            status: Response::HTTP_CREATED,
        );
    }
}
```

## Attribute-Based Routing

### Route Attributes (PHP 8.4)

```php
<?php

declare(strict_types=1);

namespace Api;

use Symfony\Component\Routing\Attribute\Route;

// Basic route
#[Route('/api/orders/{id}', name: 'api_order_show', methods: ['GET'])]
final readonly class ShowOrderAction
{
    public function __invoke(string $id): JsonResponse { /* ... */ }
}

// Route with requirements and defaults
#[Route(
    path: '/api/orders/{id}',
    name: 'api_order_show',
    requirements: ['id' => '[0-9a-f\-]{36}'],
    methods: ['GET'],
    format: 'json',
)]
final readonly class ShowOrderAction
{
    public function __invoke(string $id): JsonResponse { /* ... */ }
}

// Route prefix via class-level attribute
#[Route('/api/v1/orders')]
final readonly class ListOrdersAction
{
    #[Route('', name: 'api_order_list', methods: ['GET'])]
    public function __invoke(): JsonResponse { /* ... */ }
}
```

**Detection:**
```bash
# Old annotation-based routing
Grep: "@Route" --glob "**/*.php"

# Modern attribute routing
Grep: "#\\[Route" --glob "**/Presentation/**/*.php"

# Missing methods constraint (risky)
Grep: "#\\[Route\\([^)]*\\)\\]" --glob "**/*.php" | grep -v "methods"
```

## EventSubscriber as Middleware

EventSubscribers intercept the request lifecycle without modifying controllers.

### Request Validation Subscriber

```php
<?php

declare(strict_types=1);

namespace EventSubscriber;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\RequestEvent;
use Symfony\Component\HttpKernel\KernelEvents;

final readonly class JsonRequestSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::REQUEST => ['onKernelRequest', 10],
        ];
    }

    public function onKernelRequest(RequestEvent $event): void
    {
        $request = $event->getRequest();

        if ($request->getContentTypeFormat() !== 'json') {
            return;
        }

        $content = $request->getContent();
        if ($content === '') {
            return;
        }

        $data = json_decode($content, true, 512, JSON_THROW_ON_ERROR);
        $request->request->replace($data);
    }
}
```

### Exception Handler Subscriber

```php
<?php

declare(strict_types=1);

namespace EventSubscriber;

use Exception\DomainException;
use Exception\EntityNotFoundException;
use Symfony\Component\EventDispatcher\EventSubscriberInterface;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\HttpKernel\Event\ExceptionEvent;
use Symfony\Component\HttpKernel\KernelEvents;

final readonly class DomainExceptionSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [
            KernelEvents::EXCEPTION => ['onKernelException', 0],
        ];
    }

    public function onKernelException(ExceptionEvent $event): void
    {
        $exception = $event->getThrowable();

        $response = match (true) {
            $exception instanceof EntityNotFoundException => new JsonResponse(
                data: ['error' => $exception->getMessage()],
                status: Response::HTTP_NOT_FOUND,
            ),
            $exception instanceof DomainException => new JsonResponse(
                data: ['error' => $exception->getMessage()],
                status: Response::HTTP_UNPROCESSABLE_ENTITY,
            ),
            default => null,
        };

        if ($response !== null) {
            $event->setResponse($response);
        }
    }
}
```

**Detection:**
```bash
# EventSubscribers with business logic (antipattern)
Grep: "implements EventSubscriberInterface" --glob "**/*.php"
Grep: "if.*->getStatus|->calculate|->validate" --glob "**/*Subscriber*.php"

# Correct usage — cross-cutting concerns only
Grep: "KernelEvents::" --glob "**/*Subscriber*.php"
```

## Input Validation with Symfony Validator

### DTO with Validation Attributes

```php
<?php

declare(strict_types=1);

namespace Request;

use Symfony\Component\Validator\Constraints as Assert;

final readonly class CreateOrderRequest
{
    public function __construct(
        #[Assert\NotBlank]
        #[Assert\Uuid]
        public string $customerId,

        #[Assert\NotBlank]
        #[Assert\Count(min: 1, minMessage: 'At least one item is required')]
        #[Assert\All([
            new Assert\Collection([
                'product_id' => [new Assert\NotBlank(), new Assert\Uuid()],
                'quantity' => [new Assert\NotBlank(), new Assert\Positive()],
            ]),
        ])]
        public array $items,
    ) {}

    public static function fromRequest(Request $request): self
    {
        $data = $request->toArray();

        return new self(
            customerId: $data['customer_id'] ?? '',
            items: $data['items'] ?? [],
        );
    }
}
```

### Validated Controller

```php
<?php

declare(strict_types=1);

namespace Api;

use Request\CreateOrderRequest;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Validator\Validator\ValidatorInterface;

#[Route('/api/orders', methods: ['POST'])]
final readonly class CreateOrderAction
{
    public function __construct(
        private ValidatorInterface $validator,
        private CreateOrderUseCase $createOrder,
    ) {}

    public function __invoke(Request $request): JsonResponse
    {
        $dto = CreateOrderRequest::fromRequest($request);
        $violations = $this->validator->validate($dto);

        if ($violations->count() > 0) {
            $errors = [];
            foreach ($violations as $violation) {
                $errors[$violation->getPropertyPath()] = $violation->getMessage();
            }

            return new JsonResponse(
                data: ['errors' => $errors],
                status: Response::HTTP_UNPROCESSABLE_ENTITY,
            );
        }

        $orderId = $this->createOrder->execute(
            new CreateOrderCommand(
                customerId: $dto->customerId,
                items: $dto->items,
            ),
        );

        return new JsonResponse(['id' => $orderId->value], Response::HTTP_CREATED);
    }
}
```

## Request/Response Best Practices

| Practice | Description |
|----------|-------------|
| Validate at boundary | Use Symfony Validator in Presentation layer only |
| Map to DTO | Convert Request to typed DTO before passing to Application |
| Use status codes | Return proper HTTP status (201, 404, 422) via `Response::HTTP_*` |
| Named arguments | Use named arguments in JsonResponse for clarity |
| Single action | One `__invoke()` method per controller class |
| No business logic | Controllers map HTTP to commands/queries, nothing more |
