# Security in No-Framework PHP

JWT authentication, RBAC authorization, password hashing, CSRF protection, and security middleware using standalone Composer packages with DDD integration.

## Authentication

### JWT Authentication (lcobucci/jwt)

No-framework projects typically use JWT for stateless API authentication. The `lcobucci/jwt` library provides a robust, standards-compliant implementation.

```bash
composer require lcobucci/jwt
```

### JWT Middleware (PSR-15)

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Lcobucci\JWT\Configuration;
use Lcobucci\JWT\Validation\RequiredConstraints;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;
use Nyholm\Psr7\Response;

final readonly class JwtAuthMiddleware implements MiddlewareInterface
{
    public function __construct(
        private Configuration $jwtConfig,
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $header = $request->getHeaderLine('Authorization');

        if (!str_starts_with($header, 'Bearer ')) {
            return new Response(401, body: json_encode(['error' => 'Missing token'], JSON_THROW_ON_ERROR));
        }

        $tokenString = substr($header, 7);

        try {
            $token = $this->jwtConfig->parser()->parse($tokenString);
            $constraints = $this->jwtConfig->validationConstraints();
            $this->jwtConfig->validator()->assert($token, ...$constraints);
        } catch (\Throwable) {
            return new Response(401, body: json_encode(['error' => 'Invalid token'], JSON_THROW_ON_ERROR));
        }

        $userId = $token->claims()->get('sub');
        $request = $request->withAttribute('userId', $userId);

        return $handler->handle($request);
    }
}
```

### JWT Configuration

```php
<?php

declare(strict_types=1);

// config/jwt.php
use Lcobucci\JWT\Configuration;
use Lcobucci\JWT\Signer\Hmac\Sha256;
use Lcobucci\JWT\Signer\Key\InMemory;
use Lcobucci\JWT\Validation\Constraint\IssuedBy;
use Lcobucci\JWT\Validation\Constraint\PermittedFor;
use Lcobucci\JWT\Validation\Constraint\SignedWith;

$config = Configuration::forSymmetricSigner(
    new Sha256(),
    InMemory::plainText($_ENV['JWT_SECRET']),
);

$config->setValidationConstraints(
    new IssuedBy('https://api.example.com'),
    new PermittedFor('https://api.example.com'),
    new SignedWith($config->signer(), $config->signingKey()),
);

return $config;
```

### Token Generation (Infrastructure)

```php
<?php

declare(strict_types=1);

namespace Security;

use ValueObject\UserId;
use Lcobucci\JWT\Configuration;

final readonly class JwtTokenGenerator
{
    public function __construct(
        private Configuration $config,
    ) {}

    public function generate(UserId $userId, array $roles = []): string
    {
        $now = new \DateTimeImmutable();

        $token = $this->config->builder()
            ->issuedBy('https://api.example.com')
            ->permittedFor('https://api.example.com')
            ->issuedAt($now)
            ->expiresAt($now->modify('+1 hour'))
            ->relatedTo($userId->value)
            ->withClaim('roles', $roles)
            ->getToken($this->config->signer(), $this->config->signingKey());

        return $token->toString();
    }
}
```

### DDD: Authentication Service Port

```php
<?php

declare(strict_types=1);

namespace Service;

use ValueObject\UserId;

interface TokenGeneratorInterface
{
    public function generate(UserId $userId, array $roles = []): string;
}
```

## Authorization (RBAC)

### Custom RBAC Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Nyholm\Psr7\Response;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class RoleAuthorizationMiddleware implements MiddlewareInterface
{
    /** @param array<string> $requiredRoles */
    public function __construct(
        private array $requiredRoles,
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        $userRoles = $request->getAttribute('roles', []);

        foreach ($this->requiredRoles as $role) {
            if (in_array($role, $userRoles, true)) {
                return $handler->handle($request);
            }
        }

        return new Response(403, body: json_encode(['error' => 'Forbidden'], JSON_THROW_ON_ERROR));
    }
}
```

### DDD: Authorization via Domain Specifications

**Bad: RBAC checks in Domain**
```php
<?php

declare(strict_types=1);

namespace Service;

final readonly class OrderService
{
    public function cancel(Order $order, array $userRoles): void
    {
        // VIOLATION: Authorization logic in Domain
        if (!in_array('admin', $userRoles, true)) {
            throw new \RuntimeException('Not authorized');
        }
        $order->cancel();
    }
}
```

**Good: Domain Specification + Middleware authorization**
```php
<?php

declare(strict_types=1);

namespace Specification;

use Entity\Order;
use Entity\User;

final readonly class CanCancelOrderSpecification
{
    public function isSatisfiedBy(Order $order, User $user): bool
    {
        return $order->isOwnedBy($user->id()) || $user->hasRole(UserRole::Admin);
    }
}
```

## Password Hashing

### Domain Port

```php
<?php

declare(strict_types=1);

namespace Service;

interface PasswordHasherInterface
{
    public function hash(string $plainPassword): string;
    public function verify(string $plainPassword, string $hash): bool;
}
```

### Infrastructure: Native PHP password_hash

```php
<?php

declare(strict_types=1);

namespace Security;

use Service\PasswordHasherInterface;

final readonly class NativePasswordHasher implements PasswordHasherInterface
{
    public function __construct(
        private string $algo = PASSWORD_ARGON2ID,
    ) {}

    public function hash(string $plainPassword): string
    {
        return password_hash($plainPassword, $this->algo);
    }

    public function verify(string $plainPassword, string $hash): bool
    {
        return password_verify($plainPassword, $hash);
    }
}
```

## CSRF Protection (for Form-Based Apps)

### CSRF Token Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Nyholm\Psr7\Response;
use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class CsrfMiddleware implements MiddlewareInterface
{
    private const HEADER = 'X-CSRF-Token';
    private const METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

    public function __construct(
        private CsrfTokenManager $tokenManager,
    ) {}

    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        if (!in_array($request->getMethod(), self::METHODS, true)) {
            return $handler->handle($request);
        }

        $token = $request->getHeaderLine(self::HEADER)
            ?: ((array) $request->getParsedBody())['_csrf_token'] ?? '';

        if (!$this->tokenManager->isValid($token)) {
            return new Response(403, body: json_encode(['error' => 'Invalid CSRF token'], JSON_THROW_ON_ERROR));
        }

        return $handler->handle($request);
    }
}
```

### CSRF Token Manager

```php
<?php

declare(strict_types=1);

namespace Security;

final class CsrfTokenManager
{
    public function generate(): string
    {
        $token = bin2hex(random_bytes(32));
        $_SESSION['csrf_token'] = $token;

        return $token;
    }

    public function isValid(string $token): bool
    {
        return hash_equals($_SESSION['csrf_token'] ?? '', $token);
    }
}
```

## Security Headers Middleware

```php
<?php

declare(strict_types=1);

namespace Middleware;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\MiddlewareInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class SecurityHeadersMiddleware implements MiddlewareInterface
{
    public function process(ServerRequestInterface $request, RequestHandlerInterface $handler): ResponseInterface
    {
        return $handler->handle($request)
            ->withHeader('X-Content-Type-Options', 'nosniff')
            ->withHeader('X-Frame-Options', 'DENY')
            ->withHeader('X-XSS-Protection', '0')
            ->withHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
            ->withHeader('Content-Security-Policy', "default-src 'self'")
            ->withHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
    }
}
```

## DI Container Wiring

```php
<?php

declare(strict_types=1);

// config/container.php — security bindings
use Service\PasswordHasherInterface;
use Service\TokenGeneratorInterface;
use Security\NativePasswordHasher;
use Security\JwtTokenGenerator;

$builder->addDefinitions([
    PasswordHasherInterface::class => DI\autowire(NativePasswordHasher::class),
    TokenGeneratorInterface::class => DI\autowire(JwtTokenGenerator::class),
    Lcobucci\JWT\Configuration::class => DI\factory(require __DIR__ . '/jwt.php'),
]);
```

## Detection Patterns

```bash
# JWT/auth library in Domain (VIOLATION)
Grep: "use Lcobucci|use Firebase\\JWT" --glob "**/Domain/**/*.php"

# Password hashing in Domain (VIOLATION)
Grep: "password_hash\(|password_verify\(" --glob "**/Domain/**/*.php"

# Session in Domain (VIOLATION)
Grep: "\\\$_SESSION" --glob "**/Domain/**/*.php"

# Role checks in Domain (VIOLATION)
Grep: "in_array.*role|hasRole.*admin" --glob "**/Domain/**/*.php"

# Good: Domain ports exist
Grep: "PasswordHasherInterface|TokenGeneratorInterface" --glob "**/Domain/**/*.php"

# JWT middleware present
Grep: "JwtAuth|Authorization.*Bearer" --glob "**/Infrastructure/Http/Middleware/**/*.php"

# Security headers middleware
Grep: "SecurityHeaders|X-Content-Type-Options" --glob "**/Infrastructure/Http/Middleware/**/*.php"
```

## Summary Table

| Aspect | DDD Layer | Package | Integration Pattern |
|--------|-----------|---------|---------------------|
| JWT Auth | Infrastructure | `lcobucci/jwt` | PSR-15 middleware extracts userId |
| Token Generation | Domain: TokenGeneratorInterface port | `lcobucci/jwt` | Infrastructure JwtTokenGenerator adapter |
| RBAC | Presentation: middleware | Custom | Middleware checks roles from JWT claims |
| Domain Auth | Domain: Specifications | Pure PHP | Specification pattern for business rules |
| Password Hashing | Domain: PasswordHasherInterface port | PHP native | Infrastructure NativePasswordHasher |
| CSRF | Presentation: middleware | Custom | CsrfMiddleware + session token manager |
| Security Headers | Presentation: middleware | Custom | SecurityHeadersMiddleware on all routes |
