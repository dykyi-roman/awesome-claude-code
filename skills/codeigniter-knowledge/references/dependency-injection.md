# Dependency Injection in CodeIgniter 4

Services class, custom registration, DI patterns, and replacing core services.

## Services Class (Static Factory)

CI4 uses a `Config\Services` class as a centralized service locator and factory. Unlike a full DI container (such as Symfony's), CI4 relies on explicit static factory methods.

### How Services Work

```php
<?php

declare(strict_types=1);

// Getting a shared (singleton) instance
$logger = \Config\Services::logger();

// Getting a new instance each time
$logger = \Config\Services::logger(getShared: false);

// Using the service() helper
$session = service('session');
```

### Core Services

| Service | Method | Description |
|---------|--------|-------------|
| `request` | `Services::request()` | Current IncomingRequest |
| `response` | `Services::response()` | Response object |
| `logger` | `Services::logger()` | PSR-3 Logger |
| `session` | `Services::session()` | Session handler |
| `validation` | `Services::validation()` | Validation service |
| `cache` | `Services::cache()` | Cache handler |
| `email` | `Services::email()` | Email service |
| `router` | `Services::router()` | Router instance |
| `security` | `Services::security()` | CSRF / security |

## Custom Service Registration

### Defining Custom Services

```php
<?php

declare(strict_types=1);

// app/Config/Services.php
namespace Config;

use App\Application\Order\ConfirmOrderUseCase;
use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Shared\EventDispatcherInterface;
use App\Infrastructure\Event\CIEventDispatcher;
use App\Infrastructure\Persistence\CIOrderRepository;
use App\Models\OrderModel;
use CodeIgniter\Config\BaseService;

final class Services extends BaseService
{
    public static function orderRepository(bool $getShared = true): OrderRepositoryInterface
    {
        if ($getShared) {
            return static::getSharedInstance('orderRepository');
        }

        return new CIOrderRepository(new OrderModel());
    }

    public static function eventDispatcher(bool $getShared = true): EventDispatcherInterface
    {
        if ($getShared) {
            return static::getSharedInstance('eventDispatcher');
        }

        return new CIEventDispatcher();
    }

    public static function confirmOrderUseCase(bool $getShared = true): ConfirmOrderUseCase
    {
        if ($getShared) {
            return static::getSharedInstance('confirmOrderUseCase');
        }

        return new ConfirmOrderUseCase(
            orders: static::orderRepository(),
            events: static::eventDispatcher(),
        );
    }
}
```

### Usage in Controllers

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

## Dependency Injection Patterns in CI4

### Constructor Injection via Services

```php
<?php

declare(strict_types=1);

namespace App\Application\Order;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Shared\EventDispatcherInterface;

final readonly class ConfirmOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private EventDispatcherInterface $events,
    ) {}

    public function execute(string $orderId): void
    {
        $order = $this->orders->findById(new \App\Domain\Order\ValueObject\OrderId($orderId))
            ?? throw new \App\Domain\Order\Exception\OrderNotFoundException($orderId);

        $order->confirm();
        $this->orders->save($order);

        foreach ($order->releaseEvents() as $event) {
            $this->events->dispatch($event);
        }
    }
}
```

### Controller with Injected Dependencies

```php
<?php

declare(strict_types=1);

namespace App\Controllers\Api;

use App\Application\Order\ConfirmOrderUseCase;
use App\Application\Order\CreateOrderUseCase;
use App\Controllers\BaseController;

final class OrderController extends BaseController
{
    private readonly ConfirmOrderUseCase $confirmOrder;
    private readonly CreateOrderUseCase $createOrder;

    public function __construct()
    {
        $this->confirmOrder = service('confirmOrderUseCase');
        $this->createOrder = service('createOrderUseCase');
    }
}
```

### Interface-Based Wiring

```php
<?php

declare(strict_types=1);

// app/Config/Services.php

// Step 1: Define interface in Domain
// App\Domain\Notification\NotifierInterface

// Step 2: Create implementations in Infrastructure
// App\Infrastructure\Notification\EmailNotifier
// App\Infrastructure\Notification\SmsNotifier

// Step 3: Wire in Services
public static function notifier(bool $getShared = true): NotifierInterface
{
    if ($getShared) {
        return static::getSharedInstance('notifier');
    }

    $channel = config('Notification')->defaultChannel;

    return match ($channel) {
        'email' => new EmailNotifier(static::email()),
        'sms'   => new SmsNotifier(config('Sms')),
        default => throw new \RuntimeException("Unknown channel: {$channel}"),
    };
}
```

## Replacing Core Services

### Overriding Built-in Services

```php
<?php

declare(strict_types=1);

// app/Config/Services.php
namespace Config;

use App\Infrastructure\Logging\StructuredLogger;
use CodeIgniter\Config\BaseService;
use Psr\Log\LoggerInterface;

final class Services extends BaseService
{
    // Override the built-in logger service
    public static function logger(bool $getShared = true): LoggerInterface
    {
        if ($getShared) {
            return static::getSharedInstance('logger');
        }

        return new StructuredLogger(
            config('Logger'),
            WRITEPATH . 'logs/',
        );
    }
}
```

### Replacing Services in Tests

```php
<?php

declare(strict_types=1);

namespace Tests\Feature;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use CodeIgniter\Test\CIUnitTestCase;
use Config\Services;

final class OrderControllerTest extends CIUnitTestCase
{
    protected function setUp(): void
    {
        parent::setUp();

        // Replace service with mock for testing
        $mockRepo = $this->createMock(OrderRepositoryInterface::class);
        $mockRepo->method('findById')->willReturn($this->createTestOrder());

        Services::injectMock('orderRepository', $mockRepo);
    }

    protected function tearDown(): void
    {
        parent::tearDown();
        Services::reset();
    }
}
```

## Service Discovery

CI4 can auto-discover services from third-party packages:

```php
<?php

declare(strict_types=1);

// vendor/acme/payment/src/Config/Services.php
namespace Acme\Payment\Config;

use Acme\Payment\PaymentGateway;
use CodeIgniter\Config\BaseService;

final class Services extends BaseService
{
    public static function paymentGateway(bool $getShared = true): PaymentGateway
    {
        if ($getShared) {
            return static::getSharedInstance('paymentGateway');
        }

        return new PaymentGateway(config('Payment'));
    }
}
```

Enable discovery in `app/Config/Modules.php`:

```php
<?php

declare(strict_types=1);

public bool $discoverInComposer = true;
```

## Detection Patterns

```bash
# Find all custom services
Grep: "public static function" --glob "app/Config/Services.php"

# Find service() helper usage
Grep: "service\(" --glob "app/**/*.php"

# Find Services:: direct calls
Grep: "Services::" --glob "app/**/*.php"

# Find service overrides
Grep: "Services::injectMock\(" --glob "tests/**/*.php"

# Services without interface (potential coupling)
Grep: "return new [A-Z]" --glob "app/Config/Services.php"

# Controllers creating dependencies directly (violation)
Grep: "new .*Model\(\)|new .*Repository\(\)|new .*Service\(" --glob "app/Controllers/**/*.php"
```

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| `new Model()` in Controller | Tight coupling | Use `service()` or Services class |
| Calling `service()` in Domain | Framework dependency in Domain | Inject via constructor |
| Missing `getShared` check | Multiple instances when singleton expected | Always include `getShared` pattern |
| No interface for service | Cannot swap implementation | Define interface in Domain/Application |
| Service with side effects | Hard to test | Keep service construction pure |
