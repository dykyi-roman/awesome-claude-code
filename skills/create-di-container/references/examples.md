# DI Container Examples

## Complete Bounded Context Module

```php
<?php

declare(strict_types=1);

namespace DependencyInjection;

use Command\CancelOrderHandler;
use Command\CreateOrderHandler;
use Command\ShipOrderHandler;
use Query\GetOrderHandler;
use Query\ListOrdersHandler;
use Factory\OrderFactory;
use Repository\OrderRepository;
use Service\OrderPricingService;
use Factory\DefaultOrderFactory;
use Persistence\DoctrineOrderRepository;
use Service\DefaultOrderPricingService;
use Command\CommandBus;
use Query\QueryBus;
use Event\EventDispatcher;

final readonly class OrderModule
{
    public function getRepositoryBindings(): array
    {
        return [
            OrderRepository::class => DoctrineOrderRepository::class,
        ];
    }

    public function getFactoryBindings(): array
    {
        return [
            OrderFactory::class => DefaultOrderFactory::class,
        ];
    }

    public function getServiceBindings(): array
    {
        return [
            OrderPricingService::class => DefaultOrderPricingService::class,
        ];
    }

    public function getCommandHandlers(): array
    {
        return [
            CreateOrderHandler::class => [
                'arguments' => [
                    OrderRepository::class,
                    OrderFactory::class,
                    EventDispatcher::class,
                ],
            ],
            CancelOrderHandler::class => [
                'arguments' => [
                    OrderRepository::class,
                    EventDispatcher::class,
                ],
            ],
            ShipOrderHandler::class => [
                'arguments' => [
                    OrderRepository::class,
                    ShippingService::class,
                    EventDispatcher::class,
                ],
            ],
        ];
    }

    public function getQueryHandlers(): array
    {
        return [
            GetOrderHandler::class => [
                'arguments' => [OrderReadRepository::class],
            ],
            ListOrdersHandler::class => [
                'arguments' => [OrderReadRepository::class],
            ],
        ];
    }
}
```

## Symfony Bundle Registration

```php
<?php

declare(strict_types=1);

namespace Order\Infrastructure;

use Compiler\OrderHandlerPass;
use DependencyInjection\OrderExtension;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Bundle\Bundle;

final class OrderBundle extends Bundle
{
    public function build(ContainerBuilder $container): void
    {
        parent::build($container);

        $container->addCompilerPass(new OrderHandlerPass());
    }

    public function getContainerExtension(): OrderExtension
    {
        return new OrderExtension();
    }
}
```

## Laravel Module Registration

```php
<?php

declare(strict_types=1);

namespace Providers;

use DependencyInjection\OrderServiceProvider;
use DependencyInjection\PaymentServiceProvider;
use DependencyInjection\ShippingServiceProvider;
use Illuminate\Support\AggregateServiceProvider;

final class ModuleServiceProvider extends AggregateServiceProvider
{
    protected $providers = [
        OrderServiceProvider::class,
        PaymentServiceProvider::class,
        ShippingServiceProvider::class,
    ];
}
```

## CQRS Handler Registration

```yaml
# Symfony services.yaml

services:
  # Command handlers auto-registration
  App\:
    resource: '../src/**/Application/Command/*Handler.php'
    autoconfigure: true

  # Query handlers auto-registration
  App\:
    resource: '../src/**/Application/Query/*Handler.php'
    autoconfigure: true

  # Command bus
  App\Shared\Infrastructure\Bus\SymfonyCommandBus:
    arguments:
      $messageBus: '@command.bus'

  App\Shared\Application\Command\CommandBus:
    alias: App\Shared\Infrastructure\Bus\SymfonyCommandBus

  # Query bus
  App\Shared\Infrastructure\Bus\SymfonyQueryBus:
    arguments:
      $messageBus: '@query.bus'

  App\Shared\Application\Query\QueryBus:
    alias: App\Shared\Infrastructure\Bus\SymfonyQueryBus
```

## Strategy Pattern Registration

```php
<?php

declare(strict_types=1);

// Laravel
final class PaymentServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        // Register all payment gateways
        $this->app->singleton(StripeGateway::class);
        $this->app->singleton(PayPalGateway::class);
        $this->app->singleton(BraintreeGateway::class);

        // Tag them for collection
        $this->app->tag([
            StripeGateway::class,
            PayPalGateway::class,
            BraintreeGateway::class,
        ], 'payment.gateways');

        // Register selector that uses tagged gateways
        $this->app->singleton(PaymentGatewaySelector::class, function ($app) {
            return new PaymentGatewaySelector(
                iterator_to_array($app->tagged('payment.gateways')),
            );
        });

        // Bind interface to primary gateway
        $this->app->bind(PaymentGateway::class, function ($app) {
            $selector = $app->make(PaymentGatewaySelector::class);
            return $selector->selectDefault();
        });
    }
}
```

```yaml
# Symfony services.yaml

services:
  # Tag all gateways
  App\Payment\Infrastructure\Adapter\:
    resource: '../src/Payment/Infrastructure/Adapter/*Gateway.php'
    tags:
      - { name: app.payment_gateway }

  # Selector receives tagged gateways
  App\Payment\Infrastructure\PaymentGatewaySelector:
    arguments:
      $gateways: !tagged_iterator app.payment_gateway

  # Alias for default gateway
  App\Payment\Domain\Gateway\PaymentGateway:
    factory: ['@App\Payment\Infrastructure\PaymentGatewaySelector', 'selectDefault']
```

## Event Subscriber Registration

```yaml
# Symfony services.yaml

services:
  # Auto-register event subscribers
  _instanceof:
    App\Shared\Domain\Event\DomainEventSubscriber:
      tags:
        - { name: kernel.event_subscriber }

  # Domain event dispatcher
  App\Shared\Infrastructure\Event\SymfonyEventDispatcher:
    arguments:
      $eventDispatcher: '@event_dispatcher'

  App\Shared\Domain\Event\EventDispatcher:
    alias: App\Shared\Infrastructure\Event\SymfonyEventDispatcher
```

## Testing Module

```php
<?php

declare(strict_types=1);

namespace Tests\Order\Infrastructure\DependencyInjection;

use Repository\OrderRepository;
use DependencyInjection\OrderModule;
use Persistence\DoctrineOrderRepository;
use PHPUnit\Framework\Attributes\CoversClass;
use PHPUnit\Framework\Attributes\Group;
use PHPUnit\Framework\TestCase;

#[Group('unit')]
#[CoversClass(OrderModule::class)]
final class OrderModuleTest extends TestCase
{
    public function testBindsOrderRepositoryInterface(): void
    {
        $module = new OrderModule();
        $bindings = $module->getRepositoryBindings();

        $this->assertSame(
            DoctrineOrderRepository::class,
            $bindings[OrderRepository::class],
        );
    }

    public function testRegistersAllCommandHandlers(): void
    {
        $module = new OrderModule();
        $handlers = $module->getCommandHandlers();

        $this->assertArrayHasKey(CreateOrderHandler::class, $handlers);
        $this->assertArrayHasKey(CancelOrderHandler::class, $handlers);
        $this->assertArrayHasKey(ShipOrderHandler::class, $handlers);
    }

    public function testCommandHandlersHaveRequiredDependencies(): void
    {
        $module = new OrderModule();
        $handlers = $module->getCommandHandlers();

        foreach ($handlers as $handler => $config) {
            $this->assertArrayHasKey('arguments', $config);
            $this->assertNotEmpty($config['arguments']);
        }
    }
}
```
