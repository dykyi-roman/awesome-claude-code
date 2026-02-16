# PSR-17 HTTP Factory Examples

## Controller with Factory Injection

```php
<?php

declare(strict_types=1);

namespace App\Presentation\Api\Controller;

use Psr\Http\Message\ResponseFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class UserController
{
    public function __construct(
        private ResponseFactoryInterface $responseFactory,
        private StreamFactoryInterface $streamFactory,
        private UserServiceInterface $userService,
    ) {
    }

    public function index(ServerRequestInterface $request): ResponseInterface
    {
        $users = $this->userService->findAll();

        return $this->json(['users' => $users]);
    }

    public function show(ServerRequestInterface $request): ResponseInterface
    {
        $id = $request->getAttribute('id');
        $user = $this->userService->findById($id);

        if ($user === null) {
            return $this->json(['error' => 'User not found'], 404);
        }

        return $this->json(['user' => $user]);
    }

    private function json(array $data, int $status = 200): ResponseInterface
    {
        $body = $this->streamFactory->createStream(
            json_encode($data, JSON_THROW_ON_ERROR),
        );

        return $this->responseFactory->createResponse($status)
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body);
    }
}
```

## HTTP Client with Factory

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class ApiClient
{
    public function __construct(
        private ClientInterface $httpClient,
        private RequestFactoryInterface $requestFactory,
        private StreamFactoryInterface $streamFactory,
        private string $baseUrl,
        private string $apiKey,
    ) {
    }

    public function get(string $path, array $query = []): ResponseInterface
    {
        $uri = $this->baseUrl . $path;

        if (!empty($query)) {
            $uri .= '?' . http_build_query($query);
        }

        $request = $this->requestFactory->createRequest('GET', $uri)
            ->withHeader('Authorization', 'Bearer ' . $this->apiKey)
            ->withHeader('Accept', 'application/json');

        return $this->httpClient->sendRequest($request);
    }

    public function post(string $path, array $data): ResponseInterface
    {
        $request = $this->requestFactory->createRequest('POST', $this->baseUrl . $path)
            ->withHeader('Authorization', 'Bearer ' . $this->apiKey)
            ->withHeader('Content-Type', 'application/json')
            ->withHeader('Accept', 'application/json')
            ->withBody($this->streamFactory->createStream(json_encode($data)));

        return $this->httpClient->sendRequest($request);
    }
}
```

## Testing with Factories

```php
<?php

declare(strict_types=1);

namespace App\Tests\Functional;

use App\Infrastructure\Http\Factory\HttpFactory;
use PHPUnit\Framework\TestCase;

final class UserControllerTest extends TestCase
{
    private HttpFactory $factory;

    protected function setUp(): void
    {
        $this->factory = new HttpFactory();
    }

    public function test_create_user_returns_201(): void
    {
        $body = $this->factory->createStream(json_encode([
            'name' => 'John Doe',
            'email' => 'john@example.com',
        ]));

        $request = $this->factory->createServerRequest('POST', '/api/users')
            ->withHeader('Content-Type', 'application/json')
            ->withBody($body)
            ->withParsedBody([
                'name' => 'John Doe',
                'email' => 'john@example.com',
            ]);

        $response = $this->controller->create($request);

        self::assertSame(201, $response->getStatusCode());
    }
}
```
