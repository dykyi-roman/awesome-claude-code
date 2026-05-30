# Yii3 Architecture

Yii3 modular architecture, middleware pipeline, config system, and package-based design.

## Modular Package Architecture

### Core Packages

| Package | Purpose | PSR |
|---------|---------|-----|
| `yiisoft/di` | Dependency injection container | PSR-11 |
| `yiisoft/router` | HTTP routing | — |
| `yiisoft/middleware-dispatcher` | Middleware pipeline | PSR-15 |
| `yiisoft/http-message` | HTTP messages and factories | PSR-7, PSR-17 |
| `yiisoft/event-dispatcher` | Event dispatching | PSR-14 |
| `yiisoft/log` | Logging | PSR-3 |
| `yiisoft/active-record` | Database ORM | — |
| `yiisoft/db` | Database abstraction | — |
| `yiisoft/db-migration` | Database migrations | — |
| `yiisoft/view` | Template rendering | — |
| `yiisoft/validator` | Data validation | — |
| `yiisoft/rbac` | Role-based access control | — |
| `yiisoft/cache` | Caching | PSR-6, PSR-16 |

### Package Installation

```bash
# Install only what you need — no monolith
composer require yiisoft/di yiisoft/router yiisoft/middleware-dispatcher
composer require yiisoft/active-record yiisoft/db-mysql
composer require yiisoft/validator yiisoft/event-dispatcher
```

## Application Template Structure

```
config/
├── common/                 # Shared definitions (services, params)
│   ├── di/                 # DI container definitions
│   │   ├── order.php       # Order module bindings
│   │   └── payment.php     # Payment module bindings
│   ├── params.php          # Application parameters
│   └── providers.php       # Service providers list
├── web/                    # Web-specific config
│   ├── di/                 # Web DI overrides
│   ├── params.php          # Web params
│   └── routes.php          # Route definitions
├── console/                # Console-specific config
│   └── params.php          # Console params
└── environments/           # Environment-specific overrides
    ├── dev/
    └── prod/

src/
├── Domain/                 # Pure domain (no Yii dependencies)
├── Application/            # Use cases, DTOs
├── Infrastructure/         # Yii implementations (AR, adapters)
└── Presentation/           # Actions, middleware, views
```

## Config System

### Parameters (params.php)

```php
<?php

declare(strict_types=1);

return [
    'app' => [
        'name' => 'My Application',
        'charset' => 'UTF-8',
    ],
    'mailer' => [
        'host' => 'smtp.example.com',
        'port' => 587,
    ],
    'yiisoft/aliases' => [
        '@root' => dirname(__DIR__),
        '@runtime' => '@root/runtime',
        '@views' => '@root/views',
    ],
];
```

### DI Definitions (di/*.php)

```php
<?php

declare(strict_types=1);

use Repository\OrderRepositoryInterface;
use Persistence\ActiveRecordOrderRepository;
use Yiisoft\Definitions\Reference;

return [
    OrderRepositoryInterface::class => ActiveRecordOrderRepository::class,
    PaymentGatewayInterface::class => [
        'class' => StripePaymentGateway::class,
        '__construct()' => [
            Reference::to('stripe.apiKey'),
        ],
    ],
];
```

### Service Providers

```php
<?php

declare(strict_types=1);

namespace Provider;

use Yiisoft\Di\ServiceProviderInterface;
use Repository\OrderRepositoryInterface;
use Persistence\ActiveRecordOrderRepository;

final class OrderServiceProvider implements ServiceProviderInterface
{
    public function getDefinitions(): array
    {
        return [
            OrderRepositoryInterface::class => ActiveRecordOrderRepository::class,
        ];
    }

    public function getExtensions(): array
    {
        return [];
    }
}
```

## Middleware Pipeline

### Pipeline Configuration

```php
<?php

declare(strict_types=1);

use Yiisoft\ErrorHandler\Middleware\ErrorCatcher;
use Yiisoft\Router\Middleware\Router;
use Yiisoft\Session\SessionMiddleware;

return [
    'middlewares' => [
        ErrorCatcher::class,
        SessionMiddleware::class,
        CorsMiddleware::class,
        AuthenticationMiddleware::class,
        Router::class, // Must be last — dispatches to route handler
    ],
];
```

### Request Lifecycle

```
Client Request
    │
    ▼
ErrorCatcher          ← Catches exceptions, formats error responses
    │
    ▼
SessionMiddleware     ← Starts/commits session
    │
    ▼
CorsMiddleware        ← Cross-origin headers
    │
    ▼
AuthMiddleware        ← Authentication check
    │
    ▼
Router                ← Matches route, dispatches to Action
    │
    ▼
Action (Controller)   ← Maps input, calls UseCase, returns Response
    │
    ▼
Client Response
```

## Detection Patterns

```bash
# Verify modular package usage (no monolith)
Grep: "yiisoft/yii2" --glob "composer.json"
Grep: "yiisoft/yii-" --glob "composer.lock"

# Check config structure
Glob: config/common/di/*.php
Glob: config/web/routes.php

# Verify middleware pipeline order
Grep: "Router::class" --glob "config/**/*.php"
Grep: "middlewares" --glob "config/**/*.php"

# Find service provider registrations
Grep: "ServiceProviderInterface" --glob "**/*.php"
```

## Best Practices

| Practice | Description |
|----------|-------------|
| Install only needed packages | Avoid `yiisoft/app` if you need custom structure |
| Use config for wiring | All DI definitions in `config/common/di/` |
| Environment-specific overrides | `config/environments/dev/` and `config/environments/prod/` |
| Service providers for modules | One provider per bounded context |
| Middleware order matters | ErrorCatcher first, Router last |
| Aliases for paths | Use `@root`, `@runtime` instead of hardcoded paths |
