---
name: create-infrastructure-client
description: Generates Infrastructure Client classes — generic, domain-agnostic clients for external services (HTTP APIs, SDKs, queues, storage). The client speaks the external system's protocol and returns generic data (DTOs, arrays); domain-specific concerns (mapping to entities, business validation) live outside the client. Includes interface + concrete implementation + DTO templates.
---

# Infrastructure Client Generator

Generate Infrastructure Client classes — wrappers around external services (HTTP APIs, third-party SDKs, message queues, storage backends) that expose a clean interface to the rest of the application. The client knows the external protocol; it does NOT know domain entities or business rules.

## Infrastructure Client characteristics

- **Single external system per client class**: one for Stripe, one for Facebook OAuth, one for AWS S3, etc.
- **Interface-driven**: a focused interface that consumers depend on. The concrete implementation can be swapped (e.g. for testing).
- **Generic data in/out**: input/output uses primitives, arrays, or client-owned DTOs — never domain entities or value objects.
- **Stateless or connection-pooled**: `final readonly` for stateless clients; per-process for those that hold an HTTP/connection pool.
- **No business logic**: rate limits, retries, and parsing live here; "is the user authorized to do X" doesn't.
- **No domain mapping inside the client**: domain mapping (DTO → Entity, error → DomainException) lives in the caller (typically a `Service` or `Component` in the bounded context that uses this client).
- **Errors as exceptions** (client-specific exception class), not magic return codes or `false`.

## When to use

| Scenario | Use an Infrastructure Client |
|----------|------------------------------|
| Calling an external HTTP API | Yes |
| Sending email via a third-party SDK (SendGrid, Mailgun) | Yes |
| Reading/writing to S3, GCS, Azure Blob | Yes |
| Publishing to a message broker (RabbitMQ, Kafka) | Yes — though often a `MessagePublisherInterface` port is preferred |
| OAuth provider integration (Google, Facebook, Apple) | Yes |
| In-process domain logic | No — use a Service or Component |
| Database access | No — use a Repository (the persistence pattern that knows about domain entities) |

## Placement

Folder placement varies by your project's architecture; whatever folder hosts external integrations in your project is where Infrastructure Clients belong.

## Templates

### Interface

```php
<?php

declare(strict_types=1);

namespace Client\Facebook;

interface FacebookClientInterface
{
    public function getUser(string $accessToken): FacebookUser;

    /** @return list<FacebookFriend> */
    public function getFriends(string $accessToken, int $limit = 50): array;
}
```

### Concrete implementation (HTTP API)

```php
<?php

declare(strict_types=1);

namespace Client\Facebook;

use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;

final readonly class FacebookClient implements FacebookClientInterface
{
    public function __construct(
        private ClientInterface $http,
        private RequestFactoryInterface $requestFactory,
        private string $baseUrl = 'https://graph.facebook.com/v18.0',
    ) {}

    public function getUser(string $accessToken): FacebookUser
    {
        $response = $this->http->sendRequest(
            $this->requestFactory
                ->createRequest('GET', sprintf('%s/me', $this->baseUrl))
                ->withHeader('Authorization', sprintf('Bearer %s', $accessToken)),
        );

        if ($response->getStatusCode() !== 200) {
            throw FacebookClientException::fromResponse($response);
        }

        $data = json_decode((string) $response->getBody(), true, flags: JSON_THROW_ON_ERROR);

        return new FacebookUser(
            id: $data['id'],
            name: $data['name'] ?? '',
            email: $data['email'] ?? null,
        );
    }

    /** @return list<FacebookFriend> */
    public function getFriends(string $accessToken, int $limit = 50): array
    {
        $response = $this->http->sendRequest(
            $this->requestFactory
                ->createRequest('GET', sprintf('%s/me/friends?limit=%d', $this->baseUrl, $limit))
                ->withHeader('Authorization', sprintf('Bearer %s', $accessToken)),
        );

        if ($response->getStatusCode() !== 200) {
            throw FacebookClientException::fromResponse($response);
        }

        $data = json_decode((string) $response->getBody(), true, flags: JSON_THROW_ON_ERROR);

        return array_map(
            static fn (array $row) => new FacebookFriend(id: $row['id'], name: $row['name']),
            $data['data'] ?? [],
        );
    }
}
```

### Client-owned DTO

```php
<?php

declare(strict_types=1);

namespace Client\Facebook;

final readonly class FacebookUser
{
    public function __construct(
        public string $id,
        public string $name,
        public ?string $email,
    ) {}
}
```

### Client-owned exception

```php
<?php

declare(strict_types=1);

namespace Client\Facebook;

use Psr\Http\Message\ResponseInterface;

final class FacebookClientException extends \RuntimeException
{
    public static function fromResponse(ResponseInterface $response): self
    {
        return new self(sprintf(
            'Facebook API responded with status %d: %s',
            $response->getStatusCode(),
            (string) $response->getBody(),
        ));
    }

    public static function unauthorized(): self
    {
        return new self('Facebook API: access token rejected.');
    }
}
```

### Generic SDK wrapper (no HTTP)

```php
<?php

declare(strict_types=1);

namespace Client\Storage;

final readonly class S3StorageClient implements StorageClientInterface
{
    public function __construct(
        private \Aws\S3\S3Client $s3,
        private string $bucket,
    ) {}

    public function put(string $key, string $contents, string $contentType): void
    {
        try {
            $this->s3->putObject([
                'Bucket' => $this->bucket,
                'Key' => $key,
                'Body' => $contents,
                'ContentType' => $contentType,
            ]);
        } catch (\Aws\S3\Exception\S3Exception $e) {
            throw StorageClientException::putFailed($key, $e);
        }
    }

    public function get(string $key): string
    {
        try {
            return (string) $this->s3->getObject([
                'Bucket' => $this->bucket,
                'Key' => $key,
            ])['Body'];
        } catch (\Aws\S3\Exception\S3Exception $e) {
            throw StorageClientException::getFailed($key, $e);
        }
    }
}
```

### Unit test pattern (with mocked HTTP)

```php
<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Psr\Http\Client\ClientInterface;
use Psr\Http\Message\RequestFactoryInterface;
use Psr\Http\Message\ResponseInterface;

final class FacebookClientTest extends TestCase
{
    public function testGetUserParsesGraphApiResponse(): void
    {
        $http = $this->createMock(ClientInterface::class);
        $factory = $this->createMock(RequestFactoryInterface::class);

        $response = $this->createMock(ResponseInterface::class);
        $response->method('getStatusCode')->willReturn(200);
        $response->method('getBody')->willReturn(
            $this->createStreamWithContent('{"id":"123","name":"Alice","email":"a@example.com"}'),
        );
        $http->method('sendRequest')->willReturn($response);
        $factory->method('createRequest')->willReturn($this->createRequest());

        $client = new FacebookClient($http, $factory);
        $user = $client->getUser('token-xyz');

        self::assertSame('123', $user->id);
        self::assertSame('a@example.com', $user->email);
    }

    public function testThrowsOnNon200Response(): void
    {
        $http = $this->createMock(ClientInterface::class);
        $factory = $this->createMock(RequestFactoryInterface::class);

        $response = $this->createMock(ResponseInterface::class);
        $response->method('getStatusCode')->willReturn(401);
        $response->method('getBody')->willReturn(
            $this->createStreamWithContent('{"error":"invalid token"}'),
        );
        $http->method('sendRequest')->willReturn($response);
        $factory->method('createRequest')->willReturn($this->createRequest());

        $client = new FacebookClient($http, $factory);

        $this->expectException(FacebookClientException::class);
        $client->getUser('bad-token');
    }
}
```

## Domain integration (in the caller, NOT inside the client)

```php
<?php

declare(strict_types=1);

// Inside a Component or Service that owns the domain mapping:
namespace Component\OAuth;

final readonly class FacebookLoginComponent
{
    public function __construct(
        private FacebookClientInterface $facebook,
        private UserRepositoryInterface $users,
    ) {}

    public function loginOrRegister(string $accessToken): User
    {
        $fbUser = $this->facebook->getUser($accessToken);  // FacebookUser DTO

        // Domain mapping happens HERE, not inside the client
        $email = new Email($fbUser->email ?? throw UserException::emailRequired());

        $user = $this->users->findByEmail($email)
            ?? User::register($email, $fbUser->name);

        $this->users->save($user);

        return $user;
    }
}
```

## Generation steps

1. **Identify the external system** the client wraps. One class per system.
2. **Define the interface** with focused methods — one per external operation the application needs (not one per HTTP endpoint).
3. **Design client-owned DTOs**. Use primitives or DTOs scoped to the client; never expose domain entities.
4. **Implement the concrete client** using PSR-18 / PSR-17 for HTTP, or the vendor SDK directly.
5. **Define a client-specific exception class** with factory methods per failure category (auth failure, rate limit, generic API error, network timeout).
6. **Add unit tests** with mocked HTTP / SDK.
7. **Map at the boundary** — in a Component or Service that USES the client, translate DTOs to domain entities and client exceptions to domain exceptions.

## Detection patterns

```bash
# Find infrastructure clients
Glob: **/Client/**/*Client.php
Glob: **/*ClientInterface.php
Grep: "implements .*ClientInterface" --glob "**/*.php"

# Clients leaking domain types (violation)
Grep: "use .*\\Entity\\|use .*\\ValueObject\\|use .*\\Domain" --glob "**/Client/**/*.php"

# Clients with business logic (violation)
Grep: "if \(.*->is[A-Z]|->can[A-Z]|->should[A-Z]" --glob "**/Client/**/*Client.php"
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Domain entity / Value Object inside client signatures | Couples the client to one domain | Use client-owned DTOs; map in the caller |
| Business logic inside the client (authorization, validation) | Mixes infrastructure with domain | Move logic to a Component / Service that calls the client |
| Returning `null` / `false` for failures | Caller has no context | Throw a typed client exception |
| Concrete client without an interface | Hard to mock for tests | Always provide `{Name}ClientInterface` |
| Retries / circuit breakers hand-rolled in the client body | Tangled responsibilities | Use a decorator (see `acc:create-retry-pattern`, `acc:create-circuit-breaker`) |
| Hard-coded base URL / credentials | Can't switch envs or test | Inject via constructor; configure via env / DI |
| Single client wrapping multiple unrelated services | God-client | One client per external system |
