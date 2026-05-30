# Symfony DI — Configuration

`ConfigurationInterface` defines the structure (tree) of a config namespace, used by the matching Extension to read and validate values from YAML/PHP config files.

See `dependency-injection.md` in this folder for broader DI coverage. This file focuses on the per-context Configuration pattern used in modular-monolith setups.

## When to define a Configuration class

| Scenario | Need a Configuration class? |
|----------|------------------------------|
| Bundle / module with its own config namespace (`payment:`, `inventory:`) | Yes |
| Adding a few env-backed parameters | No — use `parameters:` directly in `services.yaml` |
| Validating shape of config (required, defaults, enums) | Yes |
| Single-app setup with all config in one `services.yaml` | No |

## Template — Per-context Configuration

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\Configuration;

use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface;

final class PaymentConfiguration implements ConfigurationInterface
{
    public function getConfigTreeBuilder(): TreeBuilder
    {
        $treeBuilder = new TreeBuilder('payment');

        $treeBuilder->getRootNode()
            ->children()
                ->scalarNode('gateway_url')->isRequired()->cannotBeEmpty()->end()
                ->scalarNode('api_key')->isRequired()->cannotBeEmpty()->end()
                ->integerNode('timeout')->defaultValue(30)->min(1)->end()
                ->arrayNode('retry')
                    ->addDefaultsIfNotSet()
                    ->children()
                        ->integerNode('max_attempts')->defaultValue(3)->end()
                        ->integerNode('initial_delay_ms')->defaultValue(100)->end()
                    ->end()
                ->end()
            ->end();

        return $treeBuilder;
    }
}
```

Corresponding YAML:

```yaml
# config/packages/payment.yaml
payment:
    gateway_url: '%env(PAYMENT_GATEWAY_URL)%'
    api_key: '%env(PAYMENT_API_KEY)%'
    timeout: 30
    retry:
        max_attempts: 5
        initial_delay_ms: 200
```

## Root Configuration orchestrator (modular monolith)

When each bounded context owns its own Configuration, a root orchestrator composes them into one tree under a common root key:

```php
<?php

declare(strict_types=1);

namespace DependencyInjection\Configuration;

use Symfony\Component\Config\Definition\Builder\TreeBuilder;
use Symfony\Component\Config\Definition\ConfigurationInterface as SymfonyConfigurationInterface;

final class Configuration implements SymfonyConfigurationInterface
{
    /** @param list<ConfigurationInterface> $configurations */
    public function __construct(
        private readonly array $configurations,
    ) {}

    public function getConfigTreeBuilder(): TreeBuilder
    {
        $treeBuilder = new TreeBuilder('app');
        $rootNode = $treeBuilder->getRootNode();

        foreach ($this->configurations as $configuration) {
            $rootNode->append($configuration->getConfigTreeBuilder()->getRootNode());
        }

        return $treeBuilder;
    }
}
```

Then per-context YAML lives at `config/app/{context}.yaml`:

```
config/
└── app/
    ├── payment.yaml
    ├── inventory.yaml
    └── notification.yaml
```

The Extension orchestrator (see `di-extension.md`) reads this combined tree and dispatches each section to the corresponding context's Extension.

## TreeBuilder cheat sheet

| Need | Use |
|------|-----|
| Required scalar | `->scalarNode('x')->isRequired()->cannotBeEmpty()->end()` |
| Optional with default | `->scalarNode('x')->defaultValue('foo')->end()` |
| Integer with range | `->integerNode('x')->min(1)->max(60)->end()` |
| Boolean default | `->booleanNode('x')->defaultFalse()->end()` |
| Enum of allowed values | `->enumNode('x')->values(['a', 'b'])->end()` |
| Nested object | `->arrayNode('x')->addDefaultsIfNotSet()->children()-> ... ->end()->end()` |
| List of strings | `->arrayNode('x')->scalarPrototype()->end()->end()` |
| List of nested objects | `->arrayNode('x')->arrayPrototype()->children()-> ... ->end()->end()->end()` |
| Validate value | `->scalarNode('x')->validate()->ifTrue(fn ($v) => ...)->thenInvalid('msg')->end()->end()` |

## Antipatterns

| Antipattern | Why it's bad | Fix |
|-------------|--------------|-----|
| One mega Configuration covering every context | Big tree, hard to evolve per module | Per-context Configuration + orchestrator |
| Skipping `isRequired()` on critical values | App boots with `null` and crashes mid-flight | Always require what's required |
| Hard-coded secrets as `defaultValue` | Secrets in git | Use `%env(...)%` substitution |
| Configuration with branching logic in `getConfigTreeBuilder()` | Hard to read | Move conditional shape into separate Configuration classes |
