# DI Container Examples

## Complete Bounded Context Module

```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\DependencyInjection;

use App\Order\Application\Command\CancelOrderHandler;
use App\Order\Application\Command\CreateOrderHandler;
use App\Order\Application\Command\ShipOrderHandler;
use App\Order\Application\Query\GetOrderHandler;
use App\Order\Application\Query\ListOrdersHandler;
use App\Order\Domain\Factory\OrderFactory;
use App\Order\Domain\Repository\OrderRepository;
use App\Order\Domain\Service\OrderPricingService;
use App\Order\Infrastructure\Factory\DefaultOrderFactory;
use App\Order\Infrastructure\Persistence\DoctrineOrderRepository;
use App\Order\Infrastructure\Service\DefaultOrderPricingService;
use App\Shared\Application\Command\CommandBus;
use App\Shared\Application\Query\QueryBus;
use App\Shared\Domain\Event\EventDispatcher;

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

namespace App\Order\Infrastructure;

use App\Order\Infrastructure\DependencyInjection\Compiler\OrderHandlerPass;
use App\Order\Infrastructure\DependencyInjection\OrderExtension;
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

namespace App\Providers;

use App\Order\Infrastructure\DependencyInjection\OrderServiceProvider;
use App\Payment\Infrastructure\DependencyInjection\PaymentServiceProvider;
use App\Shipping\Infrastructure\DependencyInjection\ShippingServiceProvider;
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

use App\Order\Domain\Repository\OrderRepository;
use App\Order\Infrastructure\DependencyInjection\OrderModule;
use App\Order\Infrastructure\Persistence\DoctrineOrderRepository;
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
