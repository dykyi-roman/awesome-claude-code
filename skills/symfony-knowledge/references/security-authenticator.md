# Symfony Security — Authenticator

Custom Authenticators handle credential extraction from requests and the authentication contract that Symfony Security expects. Common cases: JWT/Bearer token, OAuth callback handling, username + password JSON login, API key in header.

See `security.md` in this folder for broader Symfony Security coverage (UserInterface design, firewalls, voters). This file focuses on the custom Authenticator class.

## When to write a custom Authenticator

| Scenario | Custom Authenticator? |
|----------|------------------------|
| JWT / Bearer token in `Authorization` header | Yes |
| OAuth provider callback (Google, Facebook, etc.) | Yes |
| Username + password from a JSON body (API login) | Yes (or use `JsonLoginAuthenticator`) |
| API key in custom header (`X-API-Key`) | Yes |
| Standard form login | No — use Symfony's `FormLoginAuthenticator` |
| HTTP Basic | No — Symfony provides `HttpBasicAuthenticator` |

## Authenticator characteristics

- **Stateless**: instance has no per-request state; dependencies via constructor.
- **`supports()` returns fast**: cheap predicate (path + method check, header presence).
- **`authenticate()` builds a `Passport`**: doesn't directly create a User — the Passport's badges (`UserBadge`, `PasswordCredentials`, etc.) tell Symfony how to load and verify.
- **No business logic**: authentication only. Authorization is a Voter's job.
- **Returns Response on success/failure** or `null` to let the request continue.

## Template — JSON username + password authenticator

```php
<?php

declare(strict_types=1);

namespace Security\Authenticator;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Http\Authenticator\AbstractAuthenticator;
use Symfony\Component\Security\Http\Authenticator\Passport\Badge\UserBadge;
use Symfony\Component\Security\Http\Authenticator\Passport\Credentials\PasswordCredentials;
use Symfony\Component\Security\Http\Authenticator\Passport\Passport;

final class UsernamePasswordAuthenticator extends AbstractAuthenticator
{
    public function __construct(
        private readonly TokenGeneratorInterface $tokenGenerator,
    ) {}

    public function supports(Request $request): ?bool
    {
        return $request->getPathInfo() === '/api/login' && $request->isMethod('POST');
    }

    public function authenticate(Request $request): Passport
    {
        $data = json_decode($request->getContent(), true, flags: JSON_THROW_ON_ERROR);

        if (!is_array($data) || !isset($data['username'], $data['password'])) {
            throw new AuthenticationException('Missing credentials.');
        }

        return new Passport(
            new UserBadge((string) $data['username']),
            new PasswordCredentials((string) $data['password']),
        );
    }

    public function onAuthenticationSuccess(
        Request $request,
        TokenInterface $token,
        string $firewallName,
    ): ?Response {
        $user = $token->getUser();
        $jwt = $this->tokenGenerator->generate($user);

        return new \Symfony\Component\HttpFoundation\JsonResponse([
            'token' => $jwt,
            'expires_in' => 3600,
        ]);
    }

    public function onAuthenticationFailure(
        Request $request,
        AuthenticationException $exception,
    ): ?Response {
        return new \Symfony\Component\HttpFoundation\JsonResponse(
            ['error' => 'Invalid credentials.'],
            Response::HTTP_UNAUTHORIZED,
        );
    }
}
```

## Template — JWT Bearer-token authenticator

```php
<?php

declare(strict_types=1);

namespace Security\Authenticator;

use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Security\Core\Authentication\Token\TokenInterface;
use Symfony\Component\Security\Core\Exception\AuthenticationException;
use Symfony\Component\Security\Http\Authenticator\AbstractAuthenticator;
use Symfony\Component\Security\Http\Authenticator\Passport\Badge\UserBadge;
use Symfony\Component\Security\Http\Authenticator\Passport\SelfValidatingPassport;

final class JwtAuthenticator extends AbstractAuthenticator
{
    public function __construct(
        private readonly JwtDecoderInterface $jwtDecoder,
    ) {}

    public function supports(Request $request): ?bool
    {
        return $request->headers->has('Authorization')
            && str_starts_with($request->headers->get('Authorization'), 'Bearer ');
    }

    public function authenticate(Request $request): SelfValidatingPassport
    {
        $token = substr($request->headers->get('Authorization'), 7);

        try {
            $claims = $this->jwtDecoder->decode($token);
        } catch (\Throwable $e) {
            throw new AuthenticationException('Invalid JWT.', previous: $e);
        }

        return new SelfValidatingPassport(new UserBadge($claims['sub']));
    }

    public function onAuthenticationSuccess(
        Request $request,
        TokenInterface $token,
        string $firewallName,
    ): ?Response {
        return null; // Let the request continue to the controller
    }

    public function onAuthenticationFailure(
        Request $request,
        AuthenticationException $exception,
    ): ?Response {
        return new \Symfony\Component\HttpFoundation\JsonResponse(
            ['error' => $exception->getMessage()],
            Response::HTTP_UNAUTHORIZED,
        );
    }
}
```

## Wiring in `security.yaml`

```yaml
security:
    firewalls:
        api_login:
            pattern: ^/api/login
            stateless: true
            custom_authenticators:
                - Security\Authenticator\UsernamePasswordAuthenticator

        api:
            pattern: ^/api
            stateless: true
            custom_authenticators:
                - Security\Authenticator\JwtAuthenticator
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Business logic in `authenticate()` | Mixes auth with domain rules | Authenticate only; let Voters/UseCases handle authorization and business decisions |
| Heavy work in `supports()` | Runs on every request | Cheap predicates only (path / method / header presence) |
| Creating User directly in `authenticate()` | Bypasses Symfony's User loading | Use `UserBadge` so the user provider handles loading |
| `onAuthenticationSuccess` issuing redirects on stateless API | Breaks API consumers | Return JSON; redirect only on web firewalls |
| Catching all exceptions to `false`/`null` | Swallows real bugs | Catch only auth-specific exceptions; let bugs propagate |
| Hard-coding token TTL or secret in the class | Untestable | Inject token generator / decoder |
