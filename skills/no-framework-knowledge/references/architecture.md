# No-Framework Architecture

Pure PHP project structure, PSR-4 autoloading, Composer dependency management, and bootstrap patterns.

## Project Directory Layout

```
project-root/
├── bin/
│   └── console               # CLI entry point
├── config/
│   ├── container.php          # DI container configuration
│   ├── routes.php             # Route definitions
│   ├── middleware.php          # Middleware pipeline
│   └── doctrine.php           # ORM configuration (if applicable)
├── migrations/                # Database migrations
├── public/
│   └── index.php              # HTTP front controller
├── src/
│   ├── Domain/
│   │   ├── Order/
│   │   │   ├── Entity/
│   │   │   ├── ValueObject/
│   │   │   ├── Event/
│   │   │   ├── Repository/    # Interfaces only
│   │   │   ├── Service/
│   │   │   └── Exception/
│   │   └── Shared/
│   │       ├── ValueObject/
│   │       └── Event/
│   ├── Application/
│   │   ├── Order/
│   │   │   ├── UseCase/
│   │   │   ├── Command/
│   │   │   ├── Query/
│   │   │   └── DTO/
│   │   └── Shared/
│   │       └── Service/
│   ├── Infrastructure/
│   │   ├── Persistence/
│   │   │   ├── Doctrine/
│   │   │   │   ├── Mapping/   # XML or PHP mapping files
│   │   │   │   └── Repository/
│   │   │   └── Migration/
│   │   ├── Http/
│   │   │   └── Middleware/
│   │   ├── EventDispatcher/
│   │   └── Cache/
│   └── Presentation/
│       ├── Api/
│       │   ├── Action/
│       │   ├── Request/
│       │   └── Response/
│       └── Console/
│           └── Command/
├── tests/
│   ├── Unit/
│   ├── Integration/
│   └── Functional/
├── var/
│   ├── cache/
│   └── log/
├── .env
├── .env.example
├── composer.json
└── phpunit.xml
```

## Detection Patterns

```bash
# Check for PSR-4 autoloading in composer.json
Grep: "psr-4" --glob "**/composer.json"

# Verify strict types in all PHP files
Grep: "declare\(strict_types=1\)" --glob "**/*.php"

# Find files missing strict types
Grep: "^<\?php" --glob "**/*.php" -A 2

# Check for proper namespace usage
Grep: "^namespace (Domain|Application|Infrastructure|Presentation)\\\\" --glob "**/src/**/*.php"

# Find direct require/include statements (should use autoloader)
Grep: "require[_once]*\s|include[_once]*\s" --glob "**/src/**/*.php"
```

## PSR-4 Autoloading Setup

**Good — clean composer.json autoloading:**

```json
{
    "autoload": {
        "psr-4": {
            "Domain\\": "src/Domain/",
            "Application\\": "src/Application/",
            "Infrastructure\\": "src/Infrastructure/",
            "Presentation\\": "src/Presentation/"
        }
    },
    "autoload-dev": {
        "psr-4": {
            "Tests\\": "tests/"
        }
    }
}
```

**Bad — monolithic namespace or no autoloading:**

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "src/"
        }
    }
}
```

## Minimal Composer Dependencies

```json
{
    "require": {
        "php": "^8.4",
        "psr/http-message": "^2.0",
        "psr/http-server-handler": "^1.0",
        "psr/http-server-middleware": "^1.0",
        "psr/container": "^2.0",
        "psr/log": "^3.0",
        "nyholm/psr7": "^1.8",
        "nyholm/psr7-server": "^1.1",
        "php-di/php-di": "^7.0",
        "nikic/fast-route": "^2.0",
        "monolog/monolog": "^3.0",
        "vlucas/phpdotenv": "^5.6",
        "doctrine/orm": "^3.0",
        "doctrine/migrations": "^3.8"
    },
    "require-dev": {
        "phpunit/phpunit": "^11.0",
        "phpstan/phpstan": "^1.12",
        "squizlabs/php_codesniffer": "^3.10"
    }
}
```

## Front Controller Pattern

**Good — clean bootstrap with DI container:**

```php
declare(strict_types=1);

// public/index.php
require dirname(__DIR__) . '/vendor/autoload.php';

use Dotenv\Dotenv;
use Nyholm\Psr7\Factory\Psr17Factory;
use Nyholm\Psr7Server\ServerRequestCreator;

$dotenv = Dotenv::createImmutable(dirname(__DIR__));
$dotenv->load();

$container = require dirname(__DIR__) . '/config/container.php';

$psr17Factory = new Psr17Factory();
$creator = new ServerRequestCreator($psr17Factory, $psr17Factory, $psr17Factory, $psr17Factory);
$request = $creator->fromGlobals();

$app = $container->get(Infrastructure\Http\Application::class);
$response = $app->handle($request);

(new Infrastructure\Http\SapiEmitter())->emit($response);
```

**Bad — logic directly in index.php:**

```php
<?php
// Missing strict_types!
require '../vendor/autoload.php';

$method = $_SERVER['REQUEST_METHOD'];  // Global state
$uri = $_SERVER['REQUEST_URI'];        // Global state

if ($uri === '/orders') {
    $repo = new DoctrineOrderRepository(/* ... */);  // Manual wiring
    $orders = $repo->findAll();
    header('Content-Type: application/json');  // Raw header calls
    echo json_encode($orders);                 // Raw echo
}
```

## Application Bootstrap Class

```php
declare(strict_types=1);

namespace Infrastructure\Http;

use Psr\Http\Message\ResponseInterface;
use Psr\Http\Message\ServerRequestInterface;
use Psr\Http\Server\RequestHandlerInterface;

final readonly class Application implements RequestHandlerInterface
{
    public function __construct(
        private MiddlewarePipeline $pipeline,
        private Router $router,
    ) {}

    public function handle(ServerRequestInterface $request): ResponseInterface
    {
        return $this->pipeline->process($request, $this->router);
    }
}
```

## SAPI Emitter

```php
declare(strict_types=1);

namespace Infrastructure\Http;

use Psr\Http\Message\ResponseInterface;

final class SapiEmitter
{
    public function emit(ResponseInterface $response): void
    {
        http_response_code($response->getStatusCode());

        foreach ($response->getHeaders() as $name => $values) {
            foreach ($values as $value) {
                header(sprintf('%s: %s', $name, $value), false);
            }
        }

        echo $response->getBody();
    }
}
```

## Severity Matrix

| Issue | Severity | Impact |
|-------|----------|--------|
| No PSR-4 autoloading | Critical | Maintainability |
| Missing `declare(strict_types=1)` | Critical | Type safety |
| Global state in bootstrap | Critical | Testability |
| No DI container | Warning | Scalability |
| Single `App\\` namespace | Warning | Architecture clarity |
| Logic in front controller | Warning | Separation of concerns |
| Missing `.env` management | Info | Configuration |
