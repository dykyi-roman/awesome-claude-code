# DI Container Templates

## Factory Registration

```php
<?php

declare(strict_types=1);

// Symfony factory service
// services.yaml
services:
  App\Order\Domain\OrderFactory:
    factory: ['@App\Order\Infrastructure\Factory\OrderFactoryImpl', 'create']

  App\Order\Infrastructure\Factory\OrderFactoryImpl:
    arguments:
      $idGenerator: '@id_generator'
      $clock: '@clock'
```

```php
<?php

declare(strict_types=1);

// Laravel factory binding
$this->app->bind(OrderFactory::class, function ($app) {
    return new OrderFactoryImpl(
        $app->make(IdGenerator::class),
        $app->make(Clock::class),
    );
});
```

## Decorator Chain

```php
<?php

declare(strict_types=1);

// Symfony decorator
services:
  App\Order\Infrastructure\Persistence\DoctrineOrderRepository: ~

  App\Order\Infrastructure\Persistence\CachingOrderRepository:
    decorates: App\Order\Infrastructure\Persistence\DoctrineOrderRepository
    arguments:
      $inner: '@.inner'
      $cache: '@cache.app'

  App\Order\Infrastructure\Persistence\LoggingOrderRepository:
    decorates: App\Order\Infrastructure\Persistence\CachingOrderRepository
    arguments:
      $inner: '@.inner'
      $logger: '@logger'
```

```php
<?php

declare(strict_types=1);

// Laravel decorator
$this->app->extend(OrderRepository::class, function ($repository, $app) {
    return new CachingOrderRepository(
        $repository,
        $app->make(CacheInterface::class),
    );
});

$this->app->extend(OrderRepository::class, function ($repository, $app) {
    return new LoggingOrderRepository(
        $repository,
        $app->make(LoggerInterface::class),
    );
});
```

## Conditional Registration

```php
<?php

declare(strict_types=1);

// Symfony conditional
services:
  App\Payment\Infrastructure\Adapter\StripeGateway:
    arguments:
      $apiKey: '%env(STRIPE_API_KEY)%'
    tags:
      - { name: app.payment_gateway, priority: 100 }

  App\Payment\Infrastructure\Adapter\PayPalGateway:
    arguments:
      $clientId: '%env(PAYPAL_CLIENT_ID)%'
    tags:
      - { name: app.payment_gateway, priority: 50 }

when@dev:
  services:
    App\Payment\Infrastructure\Adapter\FakeGateway:
      tags:
        - { name: app.payment_gateway, priority: 200 }
```

```php
<?php

declare(strict_types=1);

// Laravel conditional
public function register(): void
{
    if ($this->app->environment('local', 'testing')) {
        $this->app->bind(
            PaymentGateway::class,
            FakePaymentGateway::class,
        );
    } else {
        $this->app->bind(
            PaymentGateway::class,
            StripePaymentGateway::class,
        );
    }
}
```

## Named Services

```php
<?php

declare(strict_types=1);

// Symfony named services
services:
  app.payment.stripe:
    class: App\Payment\Infrastructure\Adapter\StripeGateway
    public: true

  app.payment.paypal:
    class: App\Payment\Infrastructure\Adapter\PayPalGateway
    public: true

  App\Payment\Application\PaymentService:
    arguments:
      $primaryGateway: '@app.payment.stripe'
      $fallbackGateway: '@app.payment.paypal'
```

```php
<?php

declare(strict_types=1);

// Laravel named bindings
$this->app->bind('payment.stripe', StripeGateway::class);
$this->app->bind('payment.paypal', PayPalGateway::class);

$this->app->when(PaymentService::class)
    ->needs('$primaryGateway')
    ->give(fn($app) => $app->make('payment.stripe'));
```

## Lazy Loading

```php
<?php

declare(strict_types=1);

// Symfony lazy service
services:
  App\Report\Infrastructure\HeavyReportGenerator:
    lazy: true
    tags: ['app.report_generator']
```

## Alias Registration

```php
<?php

declare(strict_types=1);

// Symfony aliases
services:
  App\Order\Domain\Repository\OrderRepository:
    alias: App\Order\Infrastructure\Persistence\DoctrineOrderRepository
    public: true

  order_repository:
    alias: App\Order\Domain\Repository\OrderRepository
```

## Parameter Injection

```php
<?php

declare(strict_types=1);

// Symfony parameters
parameters:
  order.max_items: 100
  order.default_currency: 'USD'

services:
  App\Order\Application\OrderValidator:
    arguments:
      $maxItems: '%order.max_items%'
      $defaultCurrency: '%order.default_currency%'
```

```php
<?php

declare(strict_types=1);

// Laravel config binding
$this->app->when(OrderValidator::class)
    ->needs('$maxItems')
    ->giveConfig('order.max_items');

$this->app->when(OrderValidator::class)
    ->needs('$defaultCurrency')
    ->giveConfig('order.default_currency');
```

## Autoconfiguration

```php
<?php

declare(strict_types=1);

// Symfony autoconfigure
services:
  _instanceof:
    App\Shared\Application\Command\CommandHandler:
      tags: ['messenger.message_handler']

    App\Shared\Application\Query\QueryHandler:
      tags: ['messenger.message_handler']

    App\Shared\Domain\Event\DomainEventSubscriber:
      tags: ['kernel.event_subscriber']
```

## Service Locator

```php
<?php

declare(strict_types=1);

// Symfony service locator
services:
  App\Payment\Infrastructure\PaymentGatewayLocator:
    class: Symfony\Component\DependencyInjection\ServiceLocator
    arguments:
      -
        stripe: '@App\Payment\Infrastructure\Adapter\StripeGateway'
        paypal: '@App\Payment\Infrastructure\Adapter\PayPalGateway'
    tags: ['container.service_locator']
```
