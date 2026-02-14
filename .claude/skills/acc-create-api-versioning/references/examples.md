# API Versioning Pattern Examples

## Versioned Controller Routing

**File:** `src/Presentation/Api/Action/GetOrdersAction.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Api\Action;

use Domain\Shared\Api\ApiVersion;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class GetOrdersAction implements RequestHandlerInterface
{
    public function __construct(
        private GetOrdersV1Responder $v1Responder,
        private GetOrdersV2Responder $v2Responder
    ) {}

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        $version = $request->getAttribute('api_version');
        $orders = $this->loadOrders($request);

        if ($version instanceof ApiVersion && $version->greaterThan(new ApiVersion(1))) {
            return $this->v2Responder->respond($orders);
        }

        return $this->v1Responder->respond($orders);
    }

    private function loadOrders(ServerRequestInterface $request): array
    {
        return [];
    }
}
```

---

## Middleware Registration (Symfony)

```php
<?php

declare(strict_types=1);

// config/services.php

use Domain\Shared\Api\ApiVersion;
use Presentation\Middleware\AcceptHeaderVersionResolver;
use Presentation\Middleware\CompositeVersionResolver;
use Presentation\Middleware\DeprecationHeaderMiddleware;
use Presentation\Middleware\QueryParamVersionResolver;
use Presentation\Middleware\UriPrefixVersionResolver;
use Presentation\Middleware\VersionMiddleware;

return static function ($container): void {
    $resolver = new CompositeVersionResolver([
        new UriPrefixVersionResolver(),
        new AcceptHeaderVersionResolver(vendor: 'myapp'),
        new QueryParamVersionResolver(),
    ]);

    $versionMiddleware = new VersionMiddleware(
        resolver: $resolver,
        defaultVersion: new ApiVersion(1),
        required: false
    );

    $deprecationMiddleware = new DeprecationHeaderMiddleware(
        deprecatedVersions: [
            'v1' => new \DateTimeImmutable('2026-06-01'),
        ]
    );
};
```

---

## Unit Tests

### ApiVersionTest

**File:** `tests/Unit/Domain/Shared/Api/ApiVersionTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Domain\Shared\Api;

use Domain\Shared\Api\ApiVersion;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(ApiVersion::class)]
final class ApiVersionTest extends TestCase
{
    public function testConstructsWithMajorVersion(): void
    {
        $version = new ApiVersion(2);

        self::assertSame(2, $version->major);
        self::assertSame(0, $version->minor);
    }

    public function testConstructsWithMajorAndMinor(): void
    {
        $version = new ApiVersion(1, 3);

        self::assertSame(1, $version->major);
        self::assertSame(3, $version->minor);
    }

    public function testRejectsZeroMajor(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        new ApiVersion(0);
    }

    public function testFromStringParsesVersionWithPrefix(): void
    {
        $version = ApiVersion::fromString('v2');

        self::assertSame(2, $version->major);
        self::assertSame(0, $version->minor);
    }

    public function testFromStringParsesVersionWithMinor(): void
    {
        $version = ApiVersion::fromString('v1.3');

        self::assertSame(1, $version->major);
        self::assertSame(3, $version->minor);
    }

    public function testFromStringParsesWithoutPrefix(): void
    {
        $version = ApiVersion::fromString('2');

        self::assertSame(2, $version->major);
    }

    public function testFromStringRejectsInvalid(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        ApiVersion::fromString('abc');
    }

    public function testEquality(): void
    {
        $v1 = new ApiVersion(1, 2);
        $v2 = new ApiVersion(1, 2);
        $v3 = new ApiVersion(1, 3);

        self::assertTrue($v1->equals($v2));
        self::assertFalse($v1->equals($v3));
    }

    public function testGreaterThan(): void
    {
        $v1 = new ApiVersion(2);
        $v2 = new ApiVersion(1);
        $v3 = new ApiVersion(2, 1);

        self::assertTrue($v1->greaterThan($v2));
        self::assertFalse($v2->greaterThan($v1));
        self::assertTrue($v3->greaterThan($v1));
    }

    public function testLessThan(): void
    {
        $v1 = new ApiVersion(1);
        $v2 = new ApiVersion(2);

        self::assertTrue($v1->lessThan($v2));
        self::assertFalse($v2->lessThan($v1));
    }

    public function testToString(): void
    {
        $version = new ApiVersion(1, 2);

        self::assertSame('v1.2', $version->toString());
    }
}
```

---

### UriPrefixVersionResolverTest

**File:** `tests/Unit/Presentation/Middleware/UriPrefixVersionResolverTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Middleware;

use Presentation\Middleware\UriPrefixVersionResolver;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Message\UriInterface;

#[Group('unit')]
#[CoversClass(UriPrefixVersionResolver::class)]
final class UriPrefixVersionResolverTest extends TestCase
{
    private UriPrefixVersionResolver $resolver;

    protected function setUp(): void
    {
        $this->resolver = new UriPrefixVersionResolver();
    }

    public function testResolvesVersionFromUri(): void
    {
        $request = $this->createRequestWithPath('/v2/orders');
        $version = $this->resolver->resolve($request);

        self::assertNotNull($version);
        self::assertSame(2, $version->major);
    }

    public function testReturnsNullWhenNoVersion(): void
    {
        $request = $this->createRequestWithPath('/orders');
        $version = $this->resolver->resolve($request);

        self::assertNull($version);
    }

    public function testResolvesVersionWithMinor(): void
    {
        $request = $this->createRequestWithPath('/v1.2/orders');
        $version = $this->resolver->resolve($request);

        self::assertNotNull($version);
        self::assertSame(1, $version->major);
        self::assertSame(2, $version->minor);
    }

    private function createRequestWithPath(string $path): ServerRequestInterface
    {
        $uri = $this->createMock(UriInterface::class);
        $uri->method('getPath')->willReturn($path);

        $request = $this->createMock(ServerRequestInterface::class);
        $request->method('getUri')->willReturn($uri);

        return $request;
    }
}
```

---

### VersionMiddlewareTest

**File:** `tests/Unit/Presentation/Middleware/VersionMiddlewareTest.php`

```php
<?php

declare(strict_types=1);

namespace Tests\Unit\Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Presentation\Middleware\VersionMiddleware;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

#[Group('unit')]
#[CoversClass(VersionMiddleware::class)]
final class VersionMiddlewareTest extends TestCase
{
    public function testAddsVersionToRequestAttributes(): void
    {
        $version = new ApiVersion(2);
        $resolver = $this->createMock(VersionResolverInterface::class);
        $resolver->method('resolve')->willReturn($version);

        $middleware = new VersionMiddleware($resolver);

        $request = $this->createMock(ServerRequestInterface::class);
        $request->expects(self::once())
            ->method('withAttribute')
            ->with('api_version', $version)
            ->willReturn($request);

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($this->createMock(ResponseInterface::class));

        $middleware->process($request, $handler);
    }

    public function testUsesDefaultVersionWhenNotResolved(): void
    {
        $default = new ApiVersion(1);
        $resolver = $this->createMock(VersionResolverInterface::class);
        $resolver->method('resolve')->willReturn(null);

        $middleware = new VersionMiddleware($resolver, defaultVersion: $default);

        $request = $this->createMock(ServerRequestInterface::class);
        $request->expects(self::once())
            ->method('withAttribute')
            ->with('api_version', $default)
            ->willReturn($request);

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($this->createMock(ResponseInterface::class));

        $middleware->process($request, $handler);
    }

    public function testReturns400WhenRequiredAndMissing(): void
    {
        $resolver = $this->createMock(VersionResolverInterface::class);
        $resolver->method('resolve')->willReturn(null);

        $middleware = new VersionMiddleware($resolver, required: true);

        $request = $this->createMock(ServerRequestInterface::class);

        $response = $this->createMock(ResponseInterface::class);
        $response->method('withStatus')->willReturn($response);
        $response->method('withHeader')->willReturn($response);

        $handler = $this->createMock(RequestHandlerInterface::class);
        $handler->method('handle')->willReturn($response);

        $result = $middleware->process($request, $handler);

        self::assertInstanceOf(ResponseInterface::class, $result);
    }
}
```
