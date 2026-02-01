# PSR-18 HTTP Client Templates

## Stream HTTP Client

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Client;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

final readonly class StreamHttpClient implements ClientInterface
{
    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        $context = $this->buildContext($request);
        $url = (string) $request->getUri();

        $response = @file_get_contents($url, false, $context);

        if ($response === false) {
            $error = error_get_last();

            throw new NetworkException(
                $request,
                $error['message'] ?? 'Unknown error',
            );
        }

        return $this->buildResponse($response, $http_response_header ?? []);
    }

    private function buildContext(RequestInterface $request): mixed
    {
        $headers = [];
        foreach ($request->getHeaders() as $name => $values) {
            $headers[] = $name . ': ' . implode(', ', $values);
        }

        $options = [
            'http' => [
                'method' => $request->getMethod(),
                'header' => implode("\r\n", $headers),
                'content' => (string) $request->getBody(),
                'ignore_errors' => true,
                'timeout' => 30,
            ],
        ];

        return stream_context_create($options);
    }

    private function buildResponse(string $body, array $headers): ResponseInterface
    {
        $statusCode = 200;
        $parsedHeaders = [];

        foreach ($headers as $header) {
            if (preg_match('/^HTTP\/\d\.\d (\d{3})/', $header, $matches)) {
                $statusCode = (int) $matches[1];
            } elseif (str_contains($header, ':')) {
                [$name, $value] = explode(':', $header, 2);
                $parsedHeaders[trim($name)] = [trim($value)];
            }
        }

        return (new Response($statusCode))
            ->withBody(new Stream($body))
            ->withHeaders($parsedHeaders);
    }
}
```

## Retry HTTP Client

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Client;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;

final readonly class RetryHttpClient implements ClientInterface
{
    public function __construct(
        private ClientInterface $client,
        private int $maxRetries = 3,
        private int $baseDelayMs = 100,
        private array $retryStatusCodes = [429, 500, 502, 503, 504],
    ) {
    }

    public function sendRequest(RequestInterface $request): ResponseInterface
    {
        $attempt = 0;
        $lastException = null;

        while ($attempt <= $this->maxRetries) {
            try {
                $response = $this->client->sendRequest($request);

                if (!in_array($response->getStatusCode(), $this->retryStatusCodes, true)) {
                    return $response;
                }

                if ($attempt === $this->maxRetries) {
                    return $response;
                }
            } catch (NetworkException $e) {
                $lastException = $e;

                if ($attempt === $this->maxRetries) {
                    throw $e;
                }
            }

            $this->delay($attempt);
            $attempt++;
        }

        throw $lastException ?? new ClientException('Max retries exceeded');
    }

    private function delay(int $attempt): void
    {
        $delayMs = $this->baseDelayMs * (2 ** $attempt);
        $jitter = random_int(0, (int) ($delayMs * 0.1));

        usleep(($delayMs + $jitter) * 1000);
    }
}
```

## API Client Builder

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Http\Client;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\RequestInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\StreamFactoryInterface;

final class ApiClientBuilder
{
    private string $baseUrl = '';
    private array $defaultHeaders = [];
    private ?string $bearerToken = null;

    public function __construct(
        private readonly ClientInterface $httpClient,
        private readonly RequestFactoryInterface $requestFactory,
        private readonly StreamFactoryInterface $streamFactory,
    ) {
    }

    public function baseUrl(string $url): self
    {
        $clone = clone $this;
        $clone->baseUrl = rtrim($url, '/');

        return $clone;
    }

    public function header(string $name, string $value): self
    {
        $clone = clone $this;
        $clone->defaultHeaders[$name] = $value;

        return $clone;
    }

    public function bearerToken(string $token): self
    {
        $clone = clone $this;
        $clone->bearerToken = $token;

        return $clone;
    }

    public function get(string $path, array $query = []): ResponseInterface
    {
        $url = $this->buildUrl($path, $query);

        return $this->send($this->createRequest('GET', $url));
    }

    public function post(string $path, array $data = []): ResponseInterface
    {
        return $this->sendJson('POST', $path, $data);
    }

    public function put(string $path, array $data = []): ResponseInterface
    {
        return $this->sendJson('PUT', $path, $data);
    }

    public function delete(string $path): ResponseInterface
    {
        return $this->send($this->createRequest('DELETE', $this->buildUrl($path)));
    }

    private function sendJson(string $method, string $path, array $data): ResponseInterface
    {
        $request = $this->createRequest($method, $this->buildUrl($path))
            ->withHeader('Content-Type', 'application/json')
            ->withBody($this->streamFactory->createStream(json_encode($data)));

        return $this->send($request);
    }

    private function createRequest(string $method, string $url): RequestInterface
    {
        $request = $this->requestFactory->createRequest($method, $url);

        foreach ($this->defaultHeaders as $name => $value) {
            $request = $request->withHeader($name, $value);
        }

        if ($this->bearerToken !== null) {
            $request = $request->withHeader('Authorization', 'Bearer ' . $this->bearerToken);
        }

        return $request;
    }

    private function buildUrl(string $path, array $query = []): string
    {
        $url = $this->baseUrl . '/' . ltrim($path, '/');

        if (!empty($query)) {
            $url .= '?' . http_build_query($query);
        }

        return $url;
    }

    private function send(RequestInterface $request): ResponseInterface
    {
        return $this->httpClient->sendRequest($request);
    }
}
```
