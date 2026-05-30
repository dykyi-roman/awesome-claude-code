# Symfony DI — CompilerPass

CompilerPasses run during the container build to manipulate the service graph. Common uses: collect services tagged with the same string and register them with a central registry; decorate services dynamically; resolve cross-cutting wiring that auto-wiring can't.

See `dependency-injection.md` in this folder for broader DI coverage (services.yaml, auto-wiring, tagged services). This file focuses on the per-context CompilerPass pattern used in modular-monolith setups.

## When to use a CompilerPass

| Scenario | CompilerPass? |
|----------|---------------|
| Collect all `payment.gateway`-tagged services into a registry | Yes |
| Decorate every command-bus handler with a logger | Yes — `setDecoratedService()` |
| Conditional wiring based on env / kernel.environment | Yes (or use `when@`) |
| Replace a third-party bundle's service implementation | Yes — `setDefinition()` |
| Standard service definition | No — `services.yaml` is simpler |

## Template — Tagged-service registry

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\CompilerPass;

use Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Reference;

final class PaymentGatewayCompilerPass implements CompilerPassInterface
{
    public function process(ContainerBuilder $container): void
    {
        if (!$container->has(PaymentGatewayRegistry::class)) {
            return;
        }

        $definition = $container->findDefinition(PaymentGatewayRegistry::class);
        $taggedServices = $container->findTaggedServiceIds('app.payment_gateway');

        foreach ($taggedServices as $id => $tags) {
            $definition->addMethodCall('register', [new Reference($id)]);
        }
    }
}
```

## Template — Decorator wiring at build time

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\CompilerPass;

use Symfony\Component\DependencyInjection\Compiler\CompilerPassInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Reference;

final class WrapHandlersWithLoggerCompilerPass implements CompilerPassInterface
{
    public function process(ContainerBuilder $container): void
    {
        foreach ($container->findTaggedServiceIds('messenger.message_handler') as $id => $tags) {
            $original = $container->getDefinition($id);
            $decoratorId = $id . '.logger';

            $container->register($decoratorId, LoggingHandlerDecorator::class)
                ->setDecoratedService($id)
                ->setArguments([new Reference($decoratorId . '.inner'), new Reference('logger')]);
        }
    }
}
```

## Registration in the Kernel

```php
<?php

declare(strict_types=1);

namespace App;

use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\HttpKernel\Kernel as BaseKernel;

final class Kernel extends BaseKernel
{
    protected function build(ContainerBuilder $container): void
    {
        $container->addCompilerPass(new PaymentGatewayCompilerPass());
        $container->addCompilerPass(new WrapHandlersWithLoggerCompilerPass());
    }
}
```

## Per-context orchestrator pattern (modular monolith)

In modular-monolith projects where each bounded context owns its own Extension + Configuration + CompilerPass, a root orchestrator collects per-context CompilerPasses and registers them in one place. See `di-extension.md` for the matching Extension orchestrator and `di-configuration.md` for the Configuration orchestrator.

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| CompilerPass that mutates user-defined service order | Order changes break consumer assumptions | Add explicit priority via tag attributes |
| CompilerPass without `if (!$container->has(...))` guard | Crashes on minimal setups | Always guard for optional target |
| Heavy logic inside `process()` | Slows every container build | Move logic to a helper class; CompilerPass orchestrates only |
| Using a CompilerPass when `services.yaml` would do | Hides wiring from `bin/console debug:container` | Prefer YAML config when possible |
