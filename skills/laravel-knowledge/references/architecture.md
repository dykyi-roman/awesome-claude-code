# Laravel Architecture

Detailed patterns for Laravel application architecture, Service Providers, Facades, and module organization.

## Service Providers and Bootstrapping

### Provider Lifecycle

| Phase | Method | Purpose |
|-------|--------|---------|
| Registration | `register()` | Bind classes into the container, no other services available |
| Booting | `boot()` | All providers registered, can use any service |

### Custom Service Provider

```php
<?php

declare(strict_types=1);

namespace Provider;

use Repository\OrderRepositoryInterface;
use Persistence\Eloquent\EloquentOrderRepository;
use Illuminate\Support\ServiceProvider;

final class OrderServiceProvider extends ServiceProvider
{
    /** @var array<class-string, class-string> */
    public array $bindings = [
        OrderRepositoryInterface::class => EloquentOrderRepository::class,
    ];

    public function register(): void
    {
        $this->app->singleton(
            OrderRepositoryInterface::class,
            EloquentOrderRepository::class,
        );
    }

    public function boot(): void
    {
        $this->loadMigrationsFrom(__DIR__ . '/../../database/migrations/order');
        $this->loadRoutesFrom(__DIR__ . '/../../routes/order.php');
    }
}
```

### Detection Patterns

```bash
# Find all Service Providers
Glob: **/Providers/**/*Provider.php
Glob: **/Provider/**/*Provider.php
Grep: "extends ServiceProvider" --glob "**/*.php"

# Check for register() doing too much (should only bind)
Grep: "function register\(\)" --glob "**/*Provider.php" -A 20
```

## Facades: When to Use, When to Avoid

### Facade Usage Matrix

| Context | Facade OK? | Reason |
|---------|------------|--------|
| Domain layer | Never | Must remain framework-free |
| Application layer | Never | Should depend on interfaces |
| Controller / Middleware | Acceptable | Presentation layer |
| Config / helpers | Acceptable | Infrastructure concern |
| Tests | Acceptable | Laravel provides test Facades |
| Blade templates | Acceptable | View layer |

### Detection Patterns

```bash
# Facade usage in Domain (CRITICAL violation)
Grep: "use Illuminate\\Support\\Facades" --glob "**/Domain/**/*.php"

# Facade usage in Application layer (WARNING)
Grep: "use Illuminate\\Support\\Facades" --glob "**/Application/**/*.php"

# Count total Facade usage
Grep: "Facades\\" --glob "**/*.php" --output_mode count
```

**Bad -- Facade in Domain:**
```php
<?php

declare(strict_types=1);

namespace Service;

use Illuminate\Support\Facades\Cache; // Critical in Clean/Onion; acceptable in Layered

final readonly class OrderPricingService
{
    public function calculateDiscount(Order $order): Money
    {
        $rate = Cache::get('discount_rate'); // Facade dependency
        return $order->total()->multiply($rate);
    }
}
```

**Good -- Interface injection:**
```php
<?php

declare(strict_types=1);

namespace Service;

final readonly class OrderPricingService
{
    public function __construct(
        private DiscountRateProviderInterface $discountProvider,
    ) {}

    public function calculateDiscount(Order $order): Money
    {
        $rate = $this->discountProvider->currentRate();
        return $order->total()->multiply($rate);
    }
}
```

## Default vs DDD-Aligned Directory Structure

### DDD-Aligned Module Structure

```
src/
├── Domain/
│   └── Order/
│       ├── Entity/
│       │   └── Order.php
│       ├── ValueObject/
│       │   ├── OrderId.php
│       │   ├── OrderStatus.php
│       │   └── Money.php
│       ├── Repository/
│       │   └── OrderRepositoryInterface.php
│       ├── Event/
│       │   ├── OrderCreatedEvent.php
│       │   └── OrderConfirmedEvent.php
│       └── Service/
│           └── OrderPricingService.php
├── Application/
│   └── Order/
│       ├── UseCase/
│       │   ├── CreateOrderUseCase.php
│       │   └── ConfirmOrderUseCase.php
│       ├── Command/
│       │   └── CreateOrderCommand.php
│       └── DTO/
│           └── OrderLineData.php
└── Infrastructure/
    └── Order/
        ├── Persistence/
        │   ├── EloquentOrderRepository.php
        │   └── OrderModel.php
        ├── Provider/
        │   └── OrderServiceProvider.php
        └── Http/
            ├── Controller/
            │   └── CreateOrderController.php
            ├── Request/
            │   └── CreateOrderRequest.php
            └── Resource/
                └── OrderResource.php
```

### Composer Autoloading for DDD Structure

```json
{
    "autoload": {
        "psr-4": {
            "App\\": "app/",
            "App\\Domain\\": "src/Domain/",
            "App\\Application\\": "src/Application/",
            "App\\Infrastructure\\": "src/Infrastructure/"
        }
    }
}
```

## Laravel Packages vs Bounded Contexts

### When to Use Packages

| Approach | Use When |
|----------|----------|
| Directory-based modules | Single-team, shared deployment |
| Laravel Packages | Reusable across projects, separate versioning |
| Microservices | Independent deployment, different scaling needs |

### Module Registration Pattern

```php
<?php

declare(strict_types=1);

namespace Provider;

use Illuminate\Support\ServiceProvider;

final class ModuleServiceProvider extends ServiceProvider
{
    /** @var array<class-string<ServiceProvider>> */
    private const MODULES = [
        OrderServiceProvider::class,
        CustomerServiceProvider::class,
        PaymentServiceProvider::class,
        InventoryServiceProvider::class,
    ];

    public function register(): void
    {
        foreach (self::MODULES as $provider) {
            $this->app->register($provider);
        }
    }
}
```

### Detection Patterns

```bash
# Find bounded context structure
Glob: src/Domain/*/
Glob: src/Application/*/
Glob: src/Infrastructure/*/

# Check cross-context dependencies (potential violation)
Grep: "use App\\Domain\\Order" --glob "**/Domain/Customer/**/*.php"
Grep: "use App\\Domain\\Customer" --glob "**/Domain/Order/**/*.php"
```

## Module Structure Patterns

### Anti-Corruption Layer Between Modules

```php
<?php

declare(strict_types=1);

namespace Adapter;

use Port\CustomerInfoProviderInterface;
use ValueObject\CustomerInfo;
use Repository\CustomerRepositoryInterface;

final readonly class CustomerInfoAdapter implements CustomerInfoProviderInterface
{
    public function __construct(
        private CustomerRepositoryInterface $customers,
    ) {}

    public function getCustomerInfo(string $customerId): CustomerInfo
    {
        $customer = $this->customers->findById($customerId);

        return new CustomerInfo(
            name: $customer->fullName(),
            email: $customer->email()->value(),
            tier: $customer->tier()->value,
        );
    }
}
```
