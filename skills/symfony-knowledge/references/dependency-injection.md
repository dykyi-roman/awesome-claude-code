# Dependency Injection in Symfony

Service container configuration, auto-wiring, tagged services, compiler passes, and interface binding.

## services.yaml Configuration

### Basic Structure

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true
        public: false

    # Auto-register all classes in src/
    App\:
        resource: '../src/'
        exclude:
            - '../src/*/Domain/Entity/'
            - '../src/*/Domain/ValueObject/'
            - '../src/*/Domain/Event/'
            - '../src/Kernel.php'
```

### DDD-Aligned Configuration

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true

    # Per bounded context registration
    App\Order\:
        resource: '../src/Order/'
        exclude:
            - '../src/Order/Domain/Entity/'
            - '../src/Order/Domain/ValueObject/'
            - '../src/Order/Domain/Event/'

    App\Catalog\:
        resource: '../src/Catalog/'
        exclude:
            - '../src/Catalog/Domain/Entity/'

    # Interface bindings
    App\Order\Domain\Repository\OrderRepositoryInterface:
        class: App\Order\Infrastructure\Doctrine\DoctrineOrderRepository

    App\Shared\Domain\EventDispatcherInterface:
        class: App\Shared\Infrastructure\Symfony\SymfonyEventDispatcher
```

**Detection:**
```bash
# services.yaml exists and is configured
Glob: config/services.yaml
Glob: config/services/*.yaml

# Manual service definitions (may indicate poor auto-wiring)
Grep: "class:" --glob "config/services*.yaml"

# Public services (usually unnecessary with DI)
Grep: "public: true" --glob "config/services*.yaml"
```

## Auto-Wiring and Auto-Configuration

### How Auto-Wiring Works

Symfony resolves constructor dependencies by type. If an interface has exactly one implementation, it is auto-wired automatically.

```php
<?php

declare(strict_types=1);

namespace App\Order\Application\Handler;

use App\Order\Domain\Repository\OrderRepositoryInterface;

// Symfony auto-wires OrderRepositoryInterface if bound in services.yaml
final readonly class CreateOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
    ) {}
}
```

### Auto-Configuration

Auto-configure detects interfaces and applies tags automatically:

| Interface | Auto-Applied Tag |
|-----------|-----------------|
| `EventSubscriberInterface` | `kernel.event_subscriber` |
| `AsMessageHandler` (attribute) | `messenger.message_handler` |
| `CommandInterface` (console) | `console.command` |
| `TwigExtension` | `twig.extension` |
| `ValidatorConstraint` | `validator.constraint_validator` |
| `CompilerPassInterface` | Registered in Kernel |

**Bad — Manual tag when auto-configure handles it:**
```yaml
# Unnecessary when autoconfigure: true
services:
    App\Order\Infrastructure\Symfony\OrderEventSubscriber:
        tags: ['kernel.event_subscriber']
```

**Good — Auto-configured via interface:**
```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\Symfony;

use Symfony\Component\EventDispatcher\EventSubscriberInterface;

// Automatically tagged because it implements EventSubscriberInterface
final readonly class OrderEventSubscriber implements EventSubscriberInterface
{
    public static function getSubscribedEvents(): array
    {
        return [OrderCreatedEvent::class => 'onOrderCreated'];
    }
}
```

## Interface Binding

### Single Implementation Binding

```yaml
# config/services.yaml
services:
    App\Order\Domain\Repository\OrderRepositoryInterface:
        class: App\Order\Infrastructure\Doctrine\DoctrineOrderRepository

    App\Order\Domain\Service\PricingServiceInterface:
        class: App\Order\Domain\Service\DefaultPricingService
```

### Named Auto-Wiring (Multiple Implementations)

```yaml
# config/services.yaml
services:
    App\Shared\Domain\Cache\CacheInterface $productCache:
        class: App\Shared\Infrastructure\Cache\RedisCacheAdapter
        arguments:
            $prefix: 'product_'

    App\Shared\Domain\Cache\CacheInterface $orderCache:
        class: App\Shared\Infrastructure\Cache\RedisCacheAdapter
        arguments:
            $prefix: 'order_'
```

```php
<?php

declare(strict_types=1);

namespace App\Catalog\Application\Handler;

use App\Shared\Domain\Cache\CacheInterface;

final readonly class GetProductHandler
{
    public function __construct(
        private CacheInterface $productCache, // Matched by parameter name
    ) {}
}
```

**Detection:**
```bash
# Missing interface binding
Grep: "Interface" --glob "**/Domain/**/Repository/*.php" --output_mode files_with_matches
# Cross-reference with services.yaml bindings
Grep: "Interface:" --glob "config/services*.yaml"

# Named auto-wiring
Grep: "\\$\\w+:" --glob "config/services*.yaml"
```

## Tagged Services and Service Decoration

### Tagged Services

```yaml
# config/services.yaml
services:
    _instanceof:
        App\Order\Domain\Validator\OrderValidatorInterface:
            tags: ['app.order_validator']
```

```php
<?php

declare(strict_types=1);

namespace App\Order\Application\Service;

use App\Order\Domain\Validator\OrderValidatorInterface;
use Symfony\Component\DependencyInjection\Attribute\TaggedIterator;

final readonly class CompositeOrderValidator implements OrderValidatorInterface
{
    /** @param iterable<OrderValidatorInterface> $validators */
    public function __construct(
        #[TaggedIterator('app.order_validator')]
        private iterable $validators,
    ) {}

    public function validate(Order $order): ValidationResult
    {
        $errors = [];
        foreach ($this->validators as $validator) {
            $result = $validator->validate($order);
            if (!$result->isValid()) {
                $errors = [...$errors, ...$result->errors()];
            }
        }

        return new ValidationResult($errors);
    }
}
```

### Service Decoration

```yaml
# config/services.yaml
services:
    App\Order\Infrastructure\Cache\CachedOrderRepository:
        decorates: App\Order\Domain\Repository\OrderRepositoryInterface
        arguments:
            $inner: '@.inner'
```

```php
<?php

declare(strict_types=1);

namespace App\Order\Infrastructure\Cache;

use App\Order\Domain\Entity\Order;
use App\Order\Domain\Repository\OrderRepositoryInterface;
use App\Order\Domain\ValueObject\OrderId;
use Psr\Cache\CacheItemPoolInterface;

final readonly class CachedOrderRepository implements OrderRepositoryInterface
{
    public function __construct(
        private OrderRepositoryInterface $inner,
        private CacheItemPoolInterface $cache,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        $item = $this->cache->getItem('order_' . $id->value);
        if ($item->isHit()) {
            return $item->get();
        }

        $order = $this->inner->findById($id);
        if ($order !== null) {
            $item->set($order)->expiresAfter(3600);
            $this->cache->save($item);
        }

        return $order;
    }

    public function save(Order $order): void
    {
        $this->inner->save($order);
        $this->cache->deleteItem('order_' . $order->id()->value);
    }

    public function remove(Order $order): void
    {
        $this->inner->remove($order);
        $this->cache->deleteItem('order_' . $order->id()->value);
    }
}
```

## Compiler Passes

Compiler passes modify the container at build time for advanced wiring.

```php
<?php

declare(strict_types=1);

namespace App\Shared\Infrastructure\Symfony\DependencyInjection;

use Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Reference;

final readonly class OrderValidatorPass implements CompilerPassInterface
{
    public function process(ContainerBuilder $container): void
    {
        if (!$container->has(CompositeOrderValidator::class)) {
            return;
        }

        $definition = $container->findDefinition(CompositeOrderValidator::class);
        $taggedServices = $container->findTaggedServiceIds('app.order_validator');

        $validators = [];
        foreach (array_keys($taggedServices) as $id) {
            $validators[] = new Reference($id);
        }

        $definition->setArgument('$validators', $validators);
    }
}
```

### Register in Kernel

```php
<?php

declare(strict_types=1);

namespace App;

use App\Shared\Infrastructure\Symfony\DependencyInjection\OrderValidatorPass;
use Symfony\Bundle\FrameworkBundle\Kernel\MicroKernelTrait;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Kernel as BaseKernel;

final class Kernel extends BaseKernel
{
    use MicroKernelTrait;

    protected function build(ContainerBuilder $container): void
    {
        $container->addCompilerPass(new OrderValidatorPass());
    }
}
```

## Parameter Injection

```yaml
# config/services.yaml
parameters:
    app.order.max_items: 50
    app.order.default_currency: 'USD'

services:
    App\Order\Application\Service\OrderLimitChecker:
        arguments:
            $maxItems: '%app.order.max_items%'
            $defaultCurrency: '%app.order.default_currency%'
```

```php
<?php

declare(strict_types=1);

namespace App\Order\Application\Service;

final readonly class OrderLimitChecker
{
    public function __construct(
        private int $maxItems,
        private string $defaultCurrency,
    ) {}

    public function isWithinLimit(int $itemCount): bool
    {
        return $itemCount <= $this->maxItems;
    }
}
```

## DI Antipatterns Summary

| Antipattern | Detection | Fix |
|-------------|-----------|-----|
| Injecting ContainerInterface | `Grep: "ContainerInterface" --glob "src/**/*.php"` | Use constructor DI |
| Public services everywhere | `Grep: "public: true" --glob "config/**/*.yaml"` | Keep services private |
| Hard-coded service IDs | `Grep: "->get\\('" --glob "src/**/*.php"` | Use auto-wiring |
| God service (10+ dependencies) | Count constructor parameters | Split into smaller services |
| Circular dependency | Symfony throws RuntimeException | Introduce interface or event |
