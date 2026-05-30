# Symfony DI — Extension

Extensions load config values and register services into the container. They're the entry point Symfony calls during container build for each registered Extension.

See `dependency-injection.md` in this folder for broader DI coverage. This file focuses on the per-context Extension pattern used in modular-monolith setups.

## When to write a custom Extension

| Scenario | Need a custom Extension? |
|----------|--------------------------|
| Reusable bundle published to packagist | Yes |
| Modular monolith with per-context config namespaces | Yes (one Extension per context) |
| Simple app with all wiring in `services.yaml` | No — Symfony's auto-discovery is enough |
| Conditional service registration based on env | Maybe (use `when@` first) |

## Template — Per-context Extension

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\Extension;

use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Extension\ExtensionInterface;

final class PaymentExtension implements ExtensionInterface
{
    public function load(array $config, ContainerBuilder $container): void
    {
        $container->setParameter('payment.gateway_url', $config['payment']['gateway_url']);
        $container->setParameter('payment.api_key', $config['payment']['api_key']);
        $container->setParameter('payment.timeout', $config['payment']['timeout']);
        $container->setParameter('payment.retry', $config['payment']['retry']);
    }

    public function getNamespace(): string
    {
        return 'http://example.com/schema/dic/payment';
    }

    public function getXsdValidationBasePath(): string|false
    {
        return false;
    }

    public function getAlias(): string
    {
        return 'payment';
    }
}
```

## Root Extension orchestrator (modular monolith)

When each context owns its own Extension, a root Extension composes them. Symfony's `Extension` base class provides `processConfiguration()` which validates incoming configs against a `Configuration` tree.

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\Extension;

use Symfony\Component\Config\Definition\ConfigurationInterface as SymfonyConfigurationInterface;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Extension\Extension;

final class AppExtension extends Extension
{
    /**
     * @param list<ConfigurationInterface> $configurations  per-context configurations
     * @param list<ExtensionInterface> $extensions per-context extensions
     */
    public function __construct(
        private readonly array $configurations,
        private readonly array $extensions,
    ) {}

    public function load(array $configs, ContainerBuilder $container): void
    {
        $configuration = new Configuration($this->configurations);
        $config = $this->processConfiguration($configuration, $configs);

        foreach ($this->extensions as $extension) {
            $extension->load($config, $container);
        }
    }

    public function getAlias(): string
    {
        return 'app';
    }
}
```

## Wiring service definitions from an Extension

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\Extension;

use Symfony\Component\Config\FileLocator;
use Symfony\Component\DependencyInjection\ContainerBuilder;
use Symfony\Component\DependencyInjection\Loader\YamlFileLoader;
use Symfony\Component\DependencyInjection\Reference;

final class PaymentExtension implements ExtensionInterface
{
    public function load(array $config, ContainerBuilder $container): void
    {
        // Load services.yaml under config/services/payment.yaml
        $loader = new YamlFileLoader(
            $container,
            new FileLocator(__DIR__ . '/../../../config/services'),
        );
        $loader->load('payment.yaml');

        // Set parameters
        $container->setParameter('payment.gateway_url', $config['payment']['gateway_url']);

        // Wire a service that needs the parameter
        $container->getDefinition(PaymentGateway::class)
            ->setArgument('$gatewayUrl', $config['payment']['gateway_url']);
    }
}
```

Per-context service config typically lives at `config/services/{context}.yaml`:

```yaml
# config/services/payment.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true

    Payment\:
        resource: '../../src/Payment/'
        exclude:
            - '../../src/Payment/Domain/Entity/'
            - '../../src/Payment/Domain/ValueObject/'
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
        $container->registerExtension(new AppExtension(
            configurations: [
                new PaymentConfiguration(),
                new InventoryConfiguration(),
                new NotificationConfiguration(),
            ],
            extensions: [
                new PaymentExtension(),
                new InventoryExtension(),
                new NotificationExtension(),
            ],
        ));
    }
}
```

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| Hard-coded values inside `load()` instead of from `$config` | Defeats the Configuration tree | Read from validated `$config` |
| Custom Extension when `services.yaml` would do | Adds boilerplate without benefit | Use auto-discovery in `services.yaml` |
| One mega Extension covering all contexts | Tight coupling; hard to evolve per module | Per-context Extension + root orchestrator |
| `load()` throwing exceptions on missing optional config | Forces every consumer to configure everything | Use `defaultValue()` in Configuration |
