# Routing and HTTP in CodeIgniter 4

Controllers, Filters, RESTful routing, input validation, and Request/Response objects.

## Controllers

### Base Controller

```php
<?php

declare(strict_types=1);

namespace App\Controllers;

use CodeIgniter\Controller;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;
use Psr\Log\LoggerInterface;

class BaseController extends Controller
{
    /** @var list<string> */
    protected $helpers = [];

    public function initController(
        RequestInterface $request,
        ResponseInterface $response,
        LoggerInterface $logger,
    ): void {
        parent::initController($request, $response, $logger);
    }
}
```

### Resource Controller (RESTful)

```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use CodeIgniter\HTTP\ResponseInterface;
use CodeIgniter\RESTful\ResourceController;

final class ProductController extends ResourceController
{
    protected $modelName = 'App\Models\ProductModel';
    protected $format    = 'json';

    public function index(): ResponseInterface
    {
        $products = $this->model->findAll();

        return $this->respond(['data' => $products]);
    }

    public function show(?string $id = null): ResponseInterface
    {
        $product = $this->model->find($id);

        if ($product === null) {
            return $this->failNotFound('Product not found');
        }

        return $this->respond(['data' => $product]);
    }

    public function create(): ResponseInterface
    {
        $data = $this->request->getJSON(assoc: true);

        if (!$this->validate($this->createRules())) {
            return $this->failValidationErrors($this->validator->getErrors());
        }

        $id = $this->model->insert($data);

        return $this->respondCreated(['id' => $id]);
    }

    /** @return array<string, string> */
    private function createRules(): array
    {
        return [
            'name'  => 'required|min_length[3]|max_length[255]',
            'price' => 'required|numeric|greater_than[0]',
            'sku'   => 'required|alpha_numeric|is_unique[products.sku]',
        ];
    }
}
```

## RESTful Routing

### Route Configuration

```php
<?php

declare(strict_types=1);

// app/Config/Routes.php
use CodeIgniter\Router\RouteCollection;

/** @var RouteCollection $routes */

// Resource routes (generates all CRUD routes)
$routes->resource('products', ['controller' => 'Api\ProductController']);

// API group with namespace and filter
$routes->group('api/v1', ['namespace' => 'App\Controllers\Api\V1', 'filter' => 'auth'], static function ($routes): void {
    $routes->get('orders', 'OrderController::index');
    $routes->get('orders/(:num)', 'OrderController::show/$1');
    $routes->post('orders', 'OrderController::create');
    $routes->put('orders/(:num)', 'OrderController::update/$1');
    $routes->delete('orders/(:num)', 'OrderController::delete/$1');
});

// Named routes
$routes->get('user/(:num)/profile', 'UserController::profile/$1', ['as' => 'user-profile']);

// Route with placeholder regex
$routes->get('product/(:segment)', 'ProductController::show/$1');
```

### Route Placeholders

| Placeholder | Matches | Example |
|-------------|---------|---------|
| `(:num)` | Numeric only | `/order/123` |
| `(:alpha)` | Alphabetic only | `/category/electronics` |
| `(:alphanum)` | Alphanumeric | `/slug/item42` |
| `(:segment)` | Any except `/` | `/product/blue-widget` |
| `(:any)` | Any characters | `/path/to/anything` |
| `(:hash)` | Hash string | `/verify/a1b2c3` |

## Filters (Middleware Equivalent)

### Filter Definition

```php
<?php

declare(strict_types=1);

namespace App\Filters;

use CodeIgniter\Filters\FilterInterface;
use CodeIgniter\HTTP\RequestInterface;
use CodeIgniter\HTTP\ResponseInterface;

final class AuthFilter implements FilterInterface
{
    public function before(RequestInterface $request, $arguments = null): RequestInterface|ResponseInterface|void
    {
        $token = $request->getHeaderLine('Authorization');

        if ($token === '') {
            return service('response')
                ->setStatusCode(401)
                ->setJSON(['error' => 'Unauthorized']);
        }

        $authService = service('authService');

        if (!$authService->validateToken($token)) {
            return service('response')
                ->setStatusCode(403)
                ->setJSON(['error' => 'Invalid token']);
        }
    }

    public function after(RequestInterface $request, ResponseInterface $response, $arguments = null): ResponseInterface|void
    {
        // Post-processing if needed
    }
}
```

### Filter Registration

```php
<?php

declare(strict_types=1);

// app/Config/Filters.php
namespace Config;

use App\Filters\AuthFilter;
use App\Filters\CorsFilter;
use App\Filters\RateLimitFilter;
use CodeIgniter\Config\Filters as BaseFilters;

final class Filters extends BaseFilters
{
    public array $aliases = [
        'auth'      => AuthFilter::class,
        'cors'      => CorsFilter::class,
        'ratelimit' => RateLimitFilter::class,
    ];

    public array $globals = [
        'before' => ['cors'],
        'after'  => [],
    ];

    public array $filters = [
        'auth'      => ['before' => ['api/*']],
        'ratelimit' => ['before' => ['api/v1/*']],
    ];
}
```

## Input Validation

### Inline Validation

```php
<?php

declare(strict_types=1);

public function store(): ResponseInterface
{
    $rules = [
        'email'    => 'required|valid_email|is_unique[users.email]',
        'password' => 'required|min_length[8]|max_length[255]',
        'name'     => 'required|min_length[2]|max_length[100]',
    ];

    $messages = [
        'email' => [
            'is_unique' => 'This email is already registered',
        ],
    ];

    if (!$this->validate($rules, $messages)) {
        return $this->response
            ->setStatusCode(422)
            ->setJSON(['errors' => $this->validator->getErrors()]);
    }

    $validData = $this->validator->getValidated();
    // Process validated data...
}
```

### Validation Config Class

```php
<?php

declare(strict_types=1);

// app/Config/Validation.php
namespace Config;

use CodeIgniter\Config\BaseConfig;

final class Validation extends BaseConfig
{
    /** @var array<string, array<string, string>> */
    public array $createOrder = [
        'customer_id' => 'required|integer',
        'items'       => 'required',
        'items.*.product_id' => 'required|integer',
        'items.*.quantity'   => 'required|integer|greater_than[0]',
    ];
}
```

## Request / Response Objects

### Working with Request

```php
<?php

declare(strict_types=1);

// GET parameters
$page = $this->request->getGet('page');

// POST data
$name = $this->request->getPost('name');

// JSON body
$data = $this->request->getJSON(assoc: true);

// Headers
$contentType = $this->request->getHeaderLine('Content-Type');
$bearerToken = $this->request->getHeaderLine('Authorization');

// File uploads
$file = $this->request->getFile('avatar');
if ($file !== null && $file->isValid() && !$file->hasMoved()) {
    $file->move(WRITEPATH . 'uploads');
}

// Client IP
$ip = $this->request->getIPAddress();
```

### Building Responses

```php
<?php

declare(strict_types=1);

// JSON response
return $this->response
    ->setStatusCode(200)
    ->setJSON(['data' => $result]);

// Created with location header
return $this->response
    ->setStatusCode(201)
    ->setHeader('Location', site_url("api/orders/{$id}"))
    ->setJSON(['id' => $id]);

// No content
return $this->response->setStatusCode(204);

// Error response
return $this->response
    ->setStatusCode(422)
    ->setJSON(['errors' => $errors]);
```

## Detection Patterns

```bash
# Find all controllers
Grep: "extends BaseController|extends ResourceController" --glob "app/Controllers/**/*.php"

# Find route definitions
Grep: "\\$routes->(get|post|put|delete|resource|group)" --glob "app/Config/Routes.php"

# Find filter definitions
Grep: "implements FilterInterface" --glob "app/Filters/**/*.php"

# Find validation rules
Grep: "\\$this->validate\(" --glob "app/Controllers/**/*.php"

# Controllers missing validation
Grep: "getPost\(|getJSON\(" --glob "app/Controllers/**/*.php"
# Cross-check with absence of validate()

# Find route groups with filters
Grep: "'filter'" --glob "app/Config/Routes.php"
```
