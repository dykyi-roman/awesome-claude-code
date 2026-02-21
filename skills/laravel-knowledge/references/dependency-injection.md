# Dependency Injection

Detailed patterns for Laravel Service Container, binding strategies, and avoiding Facade abuse.

## Service Container Internals

### Resolution Flow

```
1. Class requested (e.g., OrderRepositoryInterface)
2. Container checks bindings registry
3. If bound → resolve using registered factory/class
4. If not bound → attempt auto-resolution via reflection
5. Constructor dependencies recursively resolved
6. Instance returned (new or singleton)
```

### Binding Types

| Type | Method | Behavior |
|------|--------|----------|
| Transient | `bind()` | New instance every time |
| Singleton | `singleton()` | Same instance always |
| Scoped | `scoped()` | Same instance per request |
| Instance | `instance()` | Pre-built object |

## Auto-Injection via Constructor

### How It Works

```php
<?php

declare(strict_types=1);

namespace App\Application\Order\UseCase;

use App\Domain\Order\Repository\OrderRepositoryInterface;
use App\Domain\Shared\EventDispatcherInterface;

// Laravel auto-resolves constructor dependencies if:
// 1. Concrete class with type-hinted dependencies, OR
// 2. Interface bound in container
final readonly class CreateOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,   // Resolved via binding
        private EventDispatcherInterface $events,    // Resolved via binding
    ) {}

    public function execute(CreateOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: $this->orders->nextIdentity(),
            customerId: $command->customerId,
        );

        $this->orders->save($order);
        $this->events->dispatch($order->releaseEvents());

        return $order->id();
    }
}
```

### Detection Patterns

```bash
# Find classes with constructor injection (good)
Grep: "public function __construct" --glob "**/UseCase/**/*.php"
Grep: "public function __construct" --glob "**/Application/**/*.php"

# Find manual container resolution (code smell)
Grep: "app\(.*::class\)" --glob "**/*.php"
Grep: "resolve\(.*::class\)" --glob "**/*.php"
Grep: "\\$this->app->make\(" --glob "**/*.php"
```

## Contextual Binding

### When Different Implementations Needed

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Provider;

use App\Domain\Shared\EventDispatcherInterface;
use App\Infrastructure\Event\LaravelEventDispatcher;
use App\Infrastructure\Event\NullEventDispatcher;
use App\Application\Order\UseCase\CreateOrderUseCase;
use App\Application\Import\UseCase\BulkImportUseCase;
use Illuminate\Support\ServiceProvider;

final class EventServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Default binding
        $this->app->bind(
            EventDispatcherInterface::class,
            LaravelEventDispatcher::class,
        );

        // Contextual: BulkImport gets NullDispatcher (no events during import)
        $this->app->when(BulkImportUseCase::class)
            ->needs(EventDispatcherInterface::class)
            ->give(NullEventDispatcher::class);
    }
}
```

### Binding Primitives

```php
$this->app->when(PdfExportService::class)
    ->needs('$storagePath')
    ->give(storage_path('exports/pdf'));

$this->app->when(RateLimiterService::class)
    ->needs('$maxAttempts')
    ->give(fn () => (int) config('rate_limiter.max_attempts', 60));
```

## Interface to Implementation Binding

### Service Provider Pattern

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Provider;

use Illuminate\Support\ServiceProvider;

final class RepositoryServiceProvider extends ServiceProvider
{
    /** @var array<class-string, class-string> */
    public array $bindings = [
        OrderRepositoryInterface::class => EloquentOrderRepository::class,
        CustomerRepositoryInterface::class => EloquentCustomerRepository::class,
        ProductRepositoryInterface::class => EloquentProductRepository::class,
    ];

    /** @var array<class-string, class-string> */
    public array $singletons = [
        CacheInterface::class => RedisCacheAdapter::class,
        EventDispatcherInterface::class => LaravelEventDispatcher::class,
    ];
}
```

### Environment-Based Binding

```php
public function register(): void
{
    if ($this->app->environment('testing')) {
        $this->app->bind(
            PaymentGatewayInterface::class,
            FakePaymentGateway::class,
        );
    } else {
        $this->app->bind(
            PaymentGatewayInterface::class,
            StripePaymentGateway::class,
        );
    }
}
```

### Detection Patterns

```bash
# Find interface bindings
Grep: "->bind\(|->singleton\(|->scoped\(" --glob "**/*Provider.php"

# Find unbound interfaces (potential runtime error)
Grep: "interface.*Interface" --glob "**/Domain/**/*.php"
# Then check if bound:
Grep: "Interface::class" --glob "**/*Provider.php"

# Find $bindings and $singletons property
Grep: "public array \\\$bindings|public array \\\$singletons" --glob "**/*Provider.php"
```

## Deferred Providers

### When to Defer

| Defer When | Do Not Defer When |
|------------|-------------------|
| Service rarely used per request | Service used on every request |
| Heavy initialization | Lightweight binding |
| Only needed by specific routes | Registered globally |

### Implementation

```php
<?php

declare(strict_types=1);

namespace App\Infrastructure\Provider;

use App\Domain\Reporting\ReportGeneratorInterface;
use App\Infrastructure\Reporting\PdfReportGenerator;
use Illuminate\Contracts\Support\DeferrableProvider;
use Illuminate\Support\ServiceProvider;

final class ReportingServiceProvider extends ServiceProvider implements DeferrableProvider
{
    public function register(): void
    {
        $this->app->singleton(
            ReportGeneratorInterface::class,
            PdfReportGenerator::class,
        );
    }

    /** @return array<class-string> */
    public function provides(): array
    {
        return [ReportGeneratorInterface::class];
    }
}
```

## Avoiding Facade Abuse

### Facade vs Dependency Injection

**Bad -- Facade everywhere:**
```php
<?php

declare(strict_types=1);

namespace App\Application\Order\UseCase;

use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Event;

// BAD: Framework coupling in Application layer
final class ProcessOrderService
{
    public function process(string $orderId): void
    {
        $order = Cache::get("order:{$orderId}");
        Log::info("Processing order", ['id' => $orderId]);
        Event::dispatch(new OrderProcessed($orderId));
    }
}
```

**Good -- Injected interfaces:**
```php
<?php

declare(strict_types=1);

namespace App\Application\Order\UseCase;

use App\Domain\Shared\CacheInterface;
use App\Domain\Shared\EventDispatcherInterface;
use Psr\Log\LoggerInterface;

final readonly class ProcessOrderUseCase
{
    public function __construct(
        private OrderRepositoryInterface $orders,
        private CacheInterface $cache,
        private EventDispatcherInterface $events,
        private LoggerInterface $logger,
    ) {}

    public function execute(ProcessOrderCommand $command): void
    {
        $order = $this->orders->findById($command->orderId);
        $this->logger->info('Processing order', ['id' => $command->orderId->value()]);
        $order->process();
        $this->orders->save($order);
        $this->events->dispatch($order->releaseEvents());
    }
}
```

### Detection Patterns

```bash
# Facade usage in Application/Domain (should be zero)
Grep: "use Illuminate\\Support\\Facades" --glob "**/Application/**/*.php"
Grep: "use Illuminate\\Support\\Facades" --glob "**/Domain/**/*.php"

# Static calls to Facades (may hide in code)
Grep: "Cache::|Log::|Event::|DB::|Auth::|Queue::" --glob "**/Application/**/*.php"
Grep: "Cache::|Log::|Event::|DB::|Auth::|Queue::" --glob "**/Domain/**/*.php"

# Helper functions that wrap Facades
Grep: "\\bcache\(|\\blog\(|\\bevent\(|\\bapp\(|\\bconfig\(" --glob "**/Application/**/*.php"
```

### Facade Severity by Layer

| Layer | Facade Usage | Severity |
|-------|-------------|----------|
| Domain | Any Facade | Critical |
| Application | Any Facade | Critical |
| Infrastructure | Acceptable with caution | Info |
| Presentation | Acceptable | OK |
| Tests | Facade mocking | OK |
