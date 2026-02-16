# API Versioning Pattern Templates

## ApiVersion

**File:** `src/Domain/Shared/Api/ApiVersion.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Api;

final readonly class ApiVersion
{
    public function __construct(
        public int $major,
        public int $minor = 0
    ) {
        if ($this->major < 1) {
            throw new \InvalidArgumentException('Major version must be at least 1');
        }
        if ($this->minor < 0) {
            throw new \InvalidArgumentException('Minor version must be non-negative');
        }
    }

    public static function fromString(string $version): self
    {
        $version = ltrim($version, 'vV');

        if (preg_match('/^(\d+)(?:\.(\d+))?$/', $version, $matches) !== 1) {
            throw new \InvalidArgumentException(
                sprintf('Invalid version format: "%s". Expected "v1" or "v1.2"', $version)
            );
        }

        return new self(
            major: (int) $matches[1],
            minor: isset($matches[2]) ? (int) $matches[2] : 0
        );
    }

    public function toString(): string
    {
        return sprintf('v%d.%d', $this->major, $this->minor);
    }

    public function toMajorString(): string
    {
        return sprintf('v%d', $this->major);
    }

    public function equals(self $other): bool
    {
        return $this->major === $other->major && $this->minor === $other->minor;
    }

    public function greaterThan(self $other): bool
    {
        if ($this->major !== $other->major) {
            return $this->major > $other->major;
        }

        return $this->minor > $other->minor;
    }

    public function lessThan(self $other): bool
    {
        if ($this->major !== $other->major) {
            return $this->major < $other->major;
        }

        return $this->minor < $other->minor;
    }
}
```

---

## VersionResolverInterface

**File:** `src/Domain/Shared/Api/VersionResolverInterface.php`

```php
<?php

declare(strict_types=1);

namespace Domain\Shared\Api;

use Psr\Http\Message\ServerRequestInterface;

interface VersionResolverInterface
{
    public function resolve(ServerRequestInterface $request): ?ApiVersion;
}
```

---

## UriPrefixVersionResolver

**File:** `src/Presentation/Middleware/UriPrefixVersionResolver.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class UriPrefixVersionResolver implements VersionResolverInterface
{
    public function resolve(ServerRequestInterface $request): ?ApiVersion
    {
        $path = $request->getUri()->getPath();

        if (preg_match('#^/v(\d+)(?:\.(\d+))?/#', $path, $matches) !== 1) {
            return null;
        }

        return new ApiVersion(
            major: (int) $matches[1],
            minor: isset($matches[2]) ? (int) $matches[2] : 0
        );
    }
}
```

---

## AcceptHeaderVersionResolver

**File:** `src/Presentation/Middleware/AcceptHeaderVersionResolver.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class AcceptHeaderVersionResolver implements VersionResolverInterface
{
    public function __construct(
        private string $vendor = 'api'
    ) {}

    public function resolve(ServerRequestInterface $request): ?ApiVersion
    {
        $accept = $request->getHeaderLine('Accept');

        $pattern = sprintf(
            '#application/vnd\.%s\.v(\d+)(?:\.(\d+))?\+json#',
            preg_quote($this->vendor, '#')
        );

        if (preg_match($pattern, $accept, $matches) !== 1) {
            return null;
        }

        return new ApiVersion(
            major: (int) $matches[1],
            minor: isset($matches[2]) ? (int) $matches[2] : 0
        );
    }
}
```

---

## QueryParamVersionResolver

**File:** `src/Presentation/Middleware/QueryParamVersionResolver.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class QueryParamVersionResolver implements VersionResolverInterface
{
    public function __construct(
        private string $paramName = 'version'
    ) {}

    public function resolve(ServerRequestInterface $request): ?ApiVersion
    {
        $params = $request->getQueryParams();
        $version = $params[$this->paramName] ?? null;

        if ($version === null || $version === '') {
            return null;
        }

        try {
            return ApiVersion::fromString((string) $version);
        } catch (\InvalidArgumentException) {
            return null;
        }
    }
}
```

---

## CompositeVersionResolver

**File:** `src/Presentation/Middleware/CompositeVersionResolver.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Psr\Http\Message\ServerRequestInterface;

final readonly class CompositeVersionResolver implements VersionResolverInterface
{
    /**
     * @param list<VersionResolverInterface> $resolvers
     */
    public function __construct(
        private array $resolvers
    ) {}

    public function resolve(ServerRequestInterface $request): ?ApiVersion
    {
        foreach ($this->resolvers as $resolver) {
            $version = $resolver->resolve($request);

            if ($version !== null) {
                return $version;
            }
        }

        return null;
    }
}
```

---

## VersionMiddleware

**File:** `src/Presentation/Middleware/VersionMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Domain\Shared\Api\VersionResolverInterface;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class VersionMiddleware implements MiddlewareInterface
{
    public function __construct(
        private VersionResolverInterface $resolver,
        private ?ApiVersion $defaultVersion = null,
        private bool $required = false
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $version = $this->resolver->resolve($request);

        if ($version === null && $this->defaultVersion !== null) {
            $version = $this->defaultVersion;
        }

        if ($version === null && $this->required) {
            return $this->createErrorResponse($handler, $request);
        }

        if ($version !== null) {
            $request = $request->withAttribute('api_version', $version);
        }

        return $handler->handle($request);
    }

    private function createErrorResponse(RequestHandlerInterface $handler, ServerRequestInterface $request): ResponseInterface
    {
        $response = $handler->handle($request);

        return $response
            ->withStatus(400)
            ->withHeader('Content-Type', 'application/json');
    }
}
```

---

## DeprecationHeaderMiddleware

**File:** `src/Presentation/Middleware/DeprecationHeaderMiddleware.php`

```php
<?php

declare(strict_types=1);

namespace Presentation\Middleware;

use Domain\Shared\Api\ApiVersion;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class DeprecationHeaderMiddleware implements MiddlewareInterface
{
    /**
     * @param array<string, \DateTimeImmutable> $deprecatedVersions Version string => sunset date
     */
    public function __construct(
        private array $deprecatedVersions = []
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $response = $handler->handle($request);

        $version = $request->getAttribute('api_version');

        if (!$version instanceof ApiVersion) {
            return $response;
        }

        $versionKey = $version->toMajorString();
        $sunsetDate = $this->deprecatedVersions[$versionKey] ?? null;

        if ($sunsetDate === null) {
            return $response;
        }

        return $response
            ->withHeader('Deprecation', 'true')
            ->withHeader('Sunset', $sunsetDate->format(\DateTimeInterface::RFC7231));
    }
}
```
