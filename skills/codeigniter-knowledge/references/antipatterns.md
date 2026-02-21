# CodeIgniter 4 Antipatterns

Common CI4 violations with detection patterns and fixes.

## Critical Violations

### 1. Business Logic in Controllers

**Description:** Controller contains domain logic instead of delegating to services or domain objects.

**Why Critical:** Untestable, duplicated logic, violates Single Responsibility.

**Detection:**
```bash
Grep: "if \(.*->status|switch \(.*->get|foreach.*calculate" --glob "app/Controllers/**/*.php"
Grep: "->where\(.*->update\(|->save\(" --glob "app/Controllers/**/*.php"
Grep: "function .*(calculate|validate|process|compute)" --glob "app/Controllers/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use App\Controllers\BaseController;
use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function confirm(string $id): ResponseInterface
    {
        $model = new \App\Models\OrderModel();
        $order = $model->find($id);

        // CRITICAL: Business logic in controller
        if ($order->status === 'draft') {
            if ($order->total > 0 && count($order->items) > 0) {
                $model->update($id, [
                    'status'       => 'confirmed',
                    'confirmed_at' => date('Y-m-d H:i:s'),
                ]);

                // Discount calculation in controller
                if ($order->total > 10000) {
                    $discount = $order->total * 0.1;
                    $model->update($id, ['discount' => $discount]);
                }
            }
        }

        return $this->response->setJSON(['ok' => true]);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use App\Controllers\BaseController;
use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function confirm(string $id): ResponseInterface
    {
        $useCase = service('confirmOrderUseCase');

        try {
            $useCase->execute($id);

            return $this->response
                ->setStatusCode(200)
                ->setJSON(['status' => 'confirmed']);
        } catch (\DomainException $e) {
            return $this->response
                ->setStatusCode(422)
                ->setJSON(['error' => $e->getMessage()]);
        }
    }
}
```

### 2. Direct Database Queries in Views

**Description:** Views contain database calls or model interactions.

**Why Critical:** Violates MVC separation, causes N+1 queries, untestable.

**Detection:**
```bash
Grep: "model\(|\\$db->|Database::connect|->find\(|->where\(" --glob "app/Views/**/*.php"
Grep: "service\(|Services::" --glob "app/Views/**/*.php"
Grep: "new .*Model" --glob "app/Views/**/*.php"
```

**Bad:**
```php
<!-- app/Views/orders/list.php -->
<?php
$model = new \App\Models\OrderModel();
$orders = $model->where('status', 'confirmed')->findAll();
?>
<?php foreach ($orders as $order): ?>
    <tr>
        <td><?= $order->id ?></td>
        <?php
        // N+1 query inside view!
        $customerModel = new \App\Models\CustomerModel();
        $customer = $customerModel->find($order->customer_id);
        ?>
        <td><?= $customer->name ?></td>
    </tr>
<?php endforeach; ?>
```

**Good:**
```php
<!-- app/Views/orders/list.php -->
<!-- Data passed from Controller via view('orders/list', $data) -->
<?php foreach ($orders as $order): ?>
    <tr>
        <td><?= esc($order['id']) ?></td>
        <td><?= esc($order['customer_name']) ?></td>
    </tr>
<?php endforeach; ?>
```

### 3. Bypassing CI4 Services

**Description:** Directly instantiating classes instead of using the Services container.

**Why Critical:** Breaks testability (cannot inject mocks), violates DI principle.

**Detection:**
```bash
Grep: "new .*Model\(\)|new .*Repository\(\)|new .*Service\(" --glob "app/Controllers/**/*.php"
Grep: "new .*Model\(\)" --glob "app/Libraries/**/*.php"
Grep: "\\\\Config\\\\Database::connect\(\)" --glob "app/Controllers/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use App\Controllers\BaseController;
use App\Infrastructure\Persistence\CIOrderRepository;
use App\Models\OrderModel;
use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function show(string $id): ResponseInterface
    {
        // BAD: Direct instantiation, cannot mock in tests
        $repo = new CIOrderRepository(new OrderModel());
        $order = $repo->findById($id);

        return $this->response->setJSON($order);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use App\Controllers\BaseController;
use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function show(string $id): ResponseInterface
    {
        // GOOD: Service container, testable via Services::injectMock
        $repo = service('orderRepository');
        $order = $repo->findById($id);

        return $this->response->setJSON($order);
    }
}
```

## Warnings

### 4. Mixing CI3 and CI4 Patterns

**Description:** Using CodeIgniter 3 patterns (no namespaces, `$this->load`, procedural style) in a CI4 project.

**Why Bad:** Defeats the purpose of CI4 modernization, confuses developers.

**Detection:**
```bash
Grep: "\\$this->load->model|\\$this->load->library|\\$this->load->helper" --glob "app/**/*.php"
Grep: "\\$this->input->post|\\$this->input->get" --glob "app/**/*.php"
Grep: "\\$this->db->get\(|\\$this->db->insert\(" --glob "app/Controllers/**/*.php"
Grep: "CI_Controller|CI_Model" --glob "app/**/*.php"
```

**Bad:**
```php
<?php

// CI3-style in a CI4 project
class Order_controller extends CI_Controller
{
    public function index()
    {
        $this->load->model('order_model');
        $data['orders'] = $this->order_model->get_all();
        $this->load->view('orders/list', $data);
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Controllers;

use CodeIgniter\HTTP\ResponseInterface;

final class OrderController extends BaseController
{
    public function index(): ResponseInterface
    {
        $orders = service('orderRepository')->findAll();

        return view('orders/list', ['orders' => $orders]);
    }
}
```

### 5. Missing Input Validation

**Description:** Controllers accepting user input without validation.

**Why Bad:** Security vulnerabilities (SQL injection, XSS), data integrity issues.

**Detection:**
```bash
Grep: "getPost\(|getJSON\(" --glob "app/Controllers/**/*.php"
# Cross-check files NOT containing validate():
Grep: "getPost\(|getJSON\(" --glob "app/Controllers/**/*.php"
Grep: "\\$this->validate\(" --glob "app/Controllers/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

public function create(): ResponseInterface
{
    $data = $this->request->getJSON(assoc: true);

    // NO validation! Directly using user input
    $model = new \App\Models\OrderModel();
    $model->insert($data);

    return $this->response->setStatusCode(201)->setJSON(['ok' => true]);
}
```

**Good:**
```php
<?php

declare(strict_types=1);

public function create(): ResponseInterface
{
    $rules = [
        'customer_id' => 'required|integer|is_not_unique[customers.id]',
        'total'       => 'required|numeric|greater_than[0]',
        'notes'       => 'permit_empty|max_length[1000]',
    ];

    if (!$this->validate($rules)) {
        return $this->response
            ->setStatusCode(422)
            ->setJSON(['errors' => $this->validator->getErrors()]);
    }

    $validData = $this->validator->getValidated();
    $useCase = service('createOrderUseCase');
    $orderId = $useCase->execute($validData);

    return $this->response->setStatusCode(201)->setJSON(['id' => $orderId]);
}
```

### 6. God Controller

**Description:** Single controller handling too many responsibilities (> 300 lines, > 10 methods).

**Why Bad:** Hard to maintain, impossible to test in isolation, violates SRP.

**Detection:**
```bash
# Find large controllers (line count)
Grep: "class.*Controller" --glob "app/Controllers/**/*.php"
# Then check line count of each file

# Count public methods in controllers
Grep: "public function" --glob "app/Controllers/**/*.php" --output_mode count
```

**Bad:**
```php
<?php

declare(strict_types=1);

// One controller for everything order-related: 500+ lines
final class OrderController extends BaseController
{
    public function list() { /* ... */ }
    public function show() { /* ... */ }
    public function create() { /* ... */ }
    public function update() { /* ... */ }
    public function delete() { /* ... */ }
    public function confirm() { /* ... */ }
    public function cancel() { /* ... */ }
    public function ship() { /* ... */ }
    public function refund() { /* ... */ }
    public function export() { /* ... */ }
    public function import() { /* ... */ }
    public function report() { /* ... */ }
    public function bulkUpdate() { /* ... */ }
    // ... 15+ more methods
}
```

**Good:**
```php
<?php

declare(strict_types=1);

// Split by responsibility
final class OrderController extends BaseController { /* CRUD only */ }
final class OrderFulfillmentController extends BaseController { /* confirm, ship, cancel */ }
final class OrderExportController extends BaseController { /* export, import */ }
final class OrderReportController extends BaseController { /* report, analytics */ }
```

### 7. Shield Auth Logic in Domain Layer

**Severity:** Warning

**Description:** Domain entities using Shield's `UserIdentity`, or authorization checks (`->can()`, `->inGroup()`) inside Domain or Application services.

**Detection:**
```bash
Grep: "use CodeIgniter\\Shield" --glob "**/Domain/**/*.php"
Grep: "->can\(|->inGroup\(|->hasPermission\(" --glob "**/Domain/**/*.php"
Grep: "auth\(\)" --glob "**/Domain/**/*.php"
Grep: "use CodeIgniter\\Shield" --glob "**/Application/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Service;

final readonly class OrderAuthorizationService
{
    public function canCancel($user, Order $order): bool
    {
        // VIOLATION: Shield authorization in Domain
        return $user->can('orders.manage') || $user->inGroup('admin');
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Domain\Order\Specification;

use App\Domain\Order\Entity\Order;
use App\Domain\User\Entity\User;

final readonly class CanCancelOrderSpecification
{
    public function isSatisfiedBy(Order $order, User $user): bool
    {
        return $order->isOwnedBy($user->id()) || $user->isAdmin();
    }
}
```

### 8. Missing Queue Resilience

**Severity:** Warning

**Description:** Queue job handlers without retry configuration, error handling, or logging.

**Detection:**
```bash
# Jobs without retry configuration
Grep: "extends BaseJob" --glob "app/Jobs/**/*.php"
Grep: "retryAfter|\\$tries" --glob "app/Jobs/**/*.php" --output_mode count

# Jobs without error handling
Grep: "try.*catch" --glob "app/Jobs/**/*.php" --output_mode count
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;

// VIOLATION: No retry, no error handling, no logging
final class ProcessPayment extends BaseJob
{
    public function process(): bool
    {
        $data = $this->data;
        // External API call with no resilience
        $client = service('curlrequest');
        $client->post('https://payment.example.com/charge', [
            'json' => $data,
        ]);

        return true;
    }
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace App\Jobs;

use CodeIgniter\Queue\BaseJob;

final class ProcessPayment extends BaseJob
{
    protected int $retryAfter = 60;
    protected int $tries = 3;

    public function process(): bool
    {
        $logger = service('logger');
        $logger->info('Processing payment', ['orderId' => $this->data['orderId']]);

        $useCase = service('processPaymentUseCase');
        $useCase->execute($this->data['orderId'], $this->data['amount']);

        return true;
    }
}
```

## Severity Matrix

| Antipattern | Severity | Impact | Fix Effort |
|-------------|----------|--------|------------|
| Business logic in Controller | Critical | Testability, duplication | Medium |
| DB queries in Views | Critical | N+1 queries, MVC violation | Low |
| Bypassing CI4 Services | Critical | Testability, coupling | Low |
| CI3 patterns in CI4 | Warning | Inconsistency, tech debt | Medium |
| Missing input validation | Warning | Security, data integrity | Low |
| God Controller | Warning | Maintainability, SRP | High |
| Shield auth in Domain | Warning | Separation of concerns | Medium |
| Missing queue resilience | Warning | Reliability | Low |
| Hardcoded config values | Info | Flexibility | Low |

## Full Detection Script

```bash
# Run all antipattern checks for a CI4 project

# Critical checks
Grep: "if \(.*->status|->save\(" --glob "app/Controllers/**/*.php"
Grep: "model\(|->find\(|->where\(" --glob "app/Views/**/*.php"
Grep: "new .*Model\(\)" --glob "app/Controllers/**/*.php"

# Warning checks
Grep: "\\$this->load->model|CI_Controller" --glob "app/**/*.php"
Grep: "getPost\(|getJSON\(" --glob "app/Controllers/**/*.php"

# Shield/Auth in Domain checks
Grep: "use CodeIgniter\\Shield" --glob "**/Domain/**/*.php"
Grep: "->can\(|->inGroup\(|auth\(\)" --glob "**/Domain/**/*.php"

# Queue in Domain checks
Grep: "service\('queue'\)" --glob "**/Domain/**/*.php"
Grep: "use CodeIgniter\\Queue" --glob "**/Domain/**/*.php"

# Missing queue resilience
Grep: "extends BaseJob" --glob "app/Jobs/**/*.php"
Grep: "retryAfter|\\$tries" --glob "app/Jobs/**/*.php" --output_mode count

# Info checks
Grep: "'localhost'|'127.0.0.1'|'password'" --glob "app/**/*.php"
Grep: "env\(" --glob "app/**/*.php" --output_mode count
```
