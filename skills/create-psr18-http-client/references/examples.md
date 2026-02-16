# PSR-18 HTTP Client Examples

## External API Integration

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\External;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\StreamFactoryInterface;

final readonly class StripeClient
{
    private const BASE_URL = 'https://api.stripe.com/v1';

    public function __construct(
        private ClientInterface $httpClient,
        private RequestFactoryInterface $requestFactory,
        private StreamFactoryInterface $streamFactory,
        private string $apiKey,
    ) {
    }

    public function createPaymentIntent(int $amount, string $currency): array
    {
        $request = $this->requestFactory->createRequest('POST', self::BASE_URL . '/payment_intents')
            ->withHeader('Authorization', 'Bearer ' . $this->apiKey)
            ->withHeader('Content-Type', 'application/x-www-form-urlencoded')
            ->withBody($this->streamFactory->createStream(http_build_query([
                'amount' => $amount,
                'currency' => $currency,
            ])));

        $response = $this->httpClient->sendRequest($request);
        $body = (string) $response->getBody();

        if ($response->getStatusCode() !== 200) {
            throw new PaymentException("Stripe error: {$body}");
        }

        return json_decode($body, true);
    }
}
```

## Microservice Client

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Service;

use App\Infrastructure\Http\Client\ApiClientBuilder;

final readonly class UserServiceClient
{
    public function __construct(
        private ApiClientBuilder $client,
    ) {
    }

    public function findUser(string $id): ?array
    {
        $response = $this->client
            ->baseUrl('http://user-service:8080')
            ->bearerToken($this->getServiceToken())
            ->get("/api/users/{$id}");

        if ($response->getStatusCode() === 404) {
            return null;
        }

        return json_decode((string) $response->getBody(), true);
    }

    public function createUser(array $data): array
    {
        $response = $this->client
            ->baseUrl('http://user-service:8080')
            ->bearerToken($this->getServiceToken())
            ->post('/api/users', $data);

        return json_decode((string) $response->getBody(), true);
    }

    private function getServiceToken(): string
    {
        // Get service-to-service token
        return 'service-token';
    }
}
```

## Testing with Mock Client

```php
<?php

declare(strict_types=1);

namespace App\Tests\Unit\Infrastructure;

use PHPUnit\Framework\TestCase;
use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

final class MockHttpClient implements ClientInterface
{
    private array $responses = [];
    private array $requests = [];

    public function addResponse(ResponseInterface $response): void
    {
        $this->responses[] = $response;
    }

    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        $this->requests[] = $request;

        if (empty($this->responses)) {
            throw new \RuntimeException('No responses configured');
        }

        return array_shift($this->responses);
    }

    public function getLastRequest(): ?RequestInterface
    {
        return end($this->requests) ?: null;
    }

    public function getRequests(): array
    {
        return $this->requests;
    }
}

// Usage in test
$mockClient = new MockHttpClient();
$mockClient->addResponse(
    (new Response(200))
        ->withBody(new Stream(json_encode(['id' => '123'])))
);

$service = new UserServiceClient($mockClient);
$user = $service->findUser('123');

self::assertNotNull($user);
self::assertSame('123', $user['id']);
```
