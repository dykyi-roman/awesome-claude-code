# CodeIgniter 4 Architecture

CI4 MVC structure, modules, directory layout, and namespace organization.

## Directory Layout

```
project-root/
├── app/                    # Application code
│   ├── Config/             # Configuration files (Services, Routes, App, Database, etc.)
│   ├── Controllers/        # HTTP Controllers
│   ├── Database/           # Migrations and Seeds
│   │   ├── Migrations/
│   │   └── Seeds/
│   ├── Entities/           # CI4 Entity classes (data hydration)
│   ├── Filters/            # HTTP Filters (middleware equivalent)
│   ├── Helpers/            # Global helper functions
│   ├── Language/           # Localization files
│   ├── Libraries/          # Custom libraries
│   ├── Models/             # CI4 Model classes (database interaction)
│   ├── ThirdParty/         # Third-party libraries
│   └── Views/              # View templates
├── public/                 # Document root (index.php, assets)
├── system/                 # CI4 framework core (DO NOT modify)
├── writable/               # Writable directories (logs, cache, uploads, sessions)
│   ├── cache/
│   ├── logs/
│   ├── session/
│   └── uploads/
├── tests/                  # Test files
├── .env                    # Environment configuration
└── spark                   # CLI tool
```

## HMVC Module Pattern

CI4 supports modular architecture via PSR-4 autoloading:

```
app/
├── Modules/
│   ├── Orders/
│   │   ├── Config/
│   │   │   ├── Routes.php
│   │   │   └── Services.php
│   │   ├── Controllers/
│   │   ├── Entities/
│   │   ├── Models/
│   │   └── Views/
│   ├── Users/
│   │   ├── Config/
│   │   ├── Controllers/
│   │   ├── Models/
│   │   └── Views/
│   └── Payment/
│       ├── Config/
│       ├── Controllers/
│       └── Models/
```

### Module Registration

```php
<?php

declare(strict_types=1);

// app/Config/Autoload.php
namespace Config;

use CodeIgniter\Config\AutoloadConfig;

final class Autoload extends AutoloadConfig
{
    public array $psr4 = [
        APP_NAMESPACE         => APPPATH,
        'App\\Modules\\Orders' => APPPATH . 'Modules/Orders',
        'App\\Modules\\Users'  => APPPATH . 'Modules/Users',
    ];
}
```

### Module Routes

```php
<?php

declare(strict_types=1);

// app/Modules/Orders/Config/Routes.php
use CodeIgniter\Router\RouteCollection;

/** @var RouteCollection $routes */
$routes->group('api/orders', ['namespace' => 'App\Modules\Orders\Controllers'], static function ($routes): void {
    $routes->get('/', 'OrderController::index');
    $routes->get('(:num)', 'OrderController::show/$1');
    $routes->post('/', 'OrderController::create');
});
```

## Namespace Organization

### Standard CI4 Namespaces

| Namespace | Purpose | Location |
|-----------|---------|----------|
| `App\Controllers` | HTTP Controllers | `app/Controllers/` |
| `App\Models` | Database Models | `app/Models/` |
| `App\Entities` | Entity classes | `app/Entities/` |
| `App\Filters` | HTTP Filters | `app/Filters/` |
| `App\Config` | Configuration | `app/Config/` |
| `App\Libraries` | Custom libraries | `app/Libraries/` |
| `App\Database\Migrations` | Migrations | `app/Database/Migrations/` |
| `App\Database\Seeds` | Seeders | `app/Database/Seeds/` |

### DDD-Extended Namespaces

```
app/
├── Domain/                           # Domain layer (pure PHP)
│   └── Order/
│       ├── Entity/Order.php
│       ├── ValueObject/OrderId.php
│       ├── Repository/OrderRepositoryInterface.php
│       └── Event/OrderConfirmedEvent.php
├── Application/                      # Application layer
│   └── Order/
│       └── UseCase/ConfirmOrderUseCase.php
├── Infrastructure/                   # Infrastructure layer
│   └── Persistence/
│       └── CIOrderRepository.php     # Implements domain interface via CI4 Model
├── Controllers/                      # Presentation layer
│   └── Api/OrderController.php
└── Config/
    └── Services.php                  # Wiring
```

## Config Management

### Environment-Based Configuration

```php
<?php

declare(strict_types=1);

// .env file
// CI_ENVIRONMENT = production
// database.default.hostname = localhost
// database.default.database = myapp
// database.default.username = root
// database.default.password = secret
```

### Custom Configuration Class

```php
<?php

declare(strict_types=1);

namespace Config;

use CodeIgniter\Config\BaseConfig;

final class Payment extends BaseConfig
{
    public string $gateway = 'stripe';
    public string $apiKey = '';
    public int $timeout = 30;

    public function __construct()
    {
        parent::__construct();

        $this->apiKey = env('PAYMENT_API_KEY', '');
    }
}
```

### Accessing Configuration

```php
<?php

declare(strict_types=1);

// Using config() helper
$paymentConfig = config('Payment');
$gateway = $paymentConfig->gateway;

// Using Config class directly
$dbConfig = new \Config\Database();
```

## Detection Patterns

```bash
# Find all Controllers
Glob: app/Controllers/**/*.php

# Find all Models
Glob: app/Models/**/*.php

# Find module structure
Glob: app/Modules/*/Controllers/*.php

# Check for HMVC modules
Glob: app/Modules/*/Config/Routes.php

# Find configuration classes
Grep: "extends BaseConfig" --glob "app/Config/*.php"

# Check namespace registration
Grep: "psr4" --glob "app/Config/Autoload.php"

# Find writable directory usage
Grep: "WRITEPATH" --glob "app/**/*.php"
```

## CI4 Lifecycle

```
1. public/index.php          → Bootstrap framework
2. Config/App.php             → Load application config
3. Config/Routes.php          → Match route to Controller
4. Filters (before)           → Run pre-controller filters
5. Controller::method()       → Execute controller action
6. Model / Service calls      → Business logic and data access
7. View rendering             → Generate response body
8. Filters (after)            → Run post-controller filters
9. Response sent              → Return to client
```

## Key Differences from CI3

| Feature | CI3 | CI4 |
|---------|-----|-----|
| PHP Version | 5.6+ | 8.1+ |
| Autoloading | Custom | PSR-4 |
| Namespaces | None | Full support |
| Architecture | MVC | MVC + HMVC |
| ORM | Active Record | Model + Entity |
| Middleware | Hooks | Filters |
| CLI | Limited | Spark CLI |
| Testing | Basic | PHPUnit integrated |
| Config | Arrays | Config classes |
