# Symfony Architecture

Bundle system, Flex recipes, and directory layout patterns for Symfony projects.

## Bundle vs Bounded Context

| Concept | Bundle | Bounded Context |
|---------|--------|----------------|
| Purpose | Reusable library/plugin | Domain boundary |
| Scope | Technical (logging, mailer) | Business (Order, Catalog) |
| Coupling | May share services | Strict isolation |
| Communication | Direct service calls | Events, shared kernel |
| When to use | Third-party integrations | Domain decomposition |

**Rule:** Do not use bundles to model bounded contexts. Use directory-based bounded contexts inside `src/`.

## Symfony Flex Recipes and Directory Structure

Flex manages `symfony.lock` and applies recipes that auto-configure packages:

```bash
# Install a package with Flex
composer require symfony/messenger
# Flex creates config/packages/messenger.yaml automatically
```

### Standard Symfony Directory Layout

```
src/
├── Controller/
├── Entity/
├── Repository/
├── Service/
├── EventListener/
├── Form/
├── Command/              # Console commands
└── Kernel.php
```

### DDD-Aligned Directory Layout

```
src/
├── Shared/                          # Shared Kernel
│   ├── Domain/
│   │   ├── ValueObject/
│   │   └── Event/
│   └── Infrastructure/
│       ├── Doctrine/
│       │   └── Type/                # Custom Doctrine types for VOs
│       └── Symfony/
│           └── Kernel.php
├── Order/                           # Bounded Context
│   ├── Domain/
│   │   ├── Entity/
│   │   │   └── Order.php            # Pure PHP, no Doctrine attributes
│   │   ├── ValueObject/
│   │   │   └── OrderId.php
│   │   ├── Event/
│   │   │   └── OrderConfirmedEvent.php
│   │   ├── Repository/
│   │   │   └── OrderRepositoryInterface.php
│   │   └── Service/
│   │       └── OrderPricingService.php
│   ├── Application/
│   │   ├── Command/
│   │   │   └── CreateOrderCommand.php
│   │   ├── Query/
│   │   │   └── GetOrderQuery.php
│   │   ├── Handler/
│   │   │   ├── CreateOrderHandler.php
│   │   │   └── GetOrderHandler.php
│   │   └── DTO/
│   │       └── OrderDTO.php
│   ├── Infrastructure/
│   │   ├── Doctrine/
│   │   │   ├── Mapping/             # XML mapping files
│   │   │   └── DoctrineOrderRepository.php
│   │   └── Messenger/
│   │       └── OrderEventSubscriber.php
│   └── Presentation/
│       └── Api/
│           ├── CreateOrderAction.php
│           └── GetOrderAction.php
└── Catalog/                         # Another Bounded Context
    ├── Domain/
    ├── Application/
    ├── Infrastructure/
    └── Presentation/
```

## Detection Patterns

```bash
# Standard vs DDD layout detection
Glob: src/Entity/*.php
Glob: src/*/Domain/Entity/*.php

# Bundle-based bounded contexts (antipattern)
Glob: src/*Bundle/Domain/*.php
Grep: "extends Bundle" --glob "src/**/*Bundle.php"

# Shared kernel detection
Glob: src/Shared/**/*.php
Grep: "namespace App\\\\Shared\\\\" --glob "src/**/*.php"

# Missing DDD structure
Grep: "namespace App\\\\Entity\\\\" --glob "src/Entity/**/*.php"
Grep: "namespace App\\\\Repository\\\\" --glob "src/Repository/**/*.php"
```

## Configuring Symfony for DDD Layout

### Doctrine Mapping Configuration

```yaml
# config/packages/doctrine.yaml
doctrine:
    orm:
        mappings:
            Order:
                type: xml
                dir: '%kernel.project_dir%/src/Order/Infrastructure/Doctrine/Mapping'
                prefix: 'App\Order\Domain\Entity'
                alias: Order
            Catalog:
                type: xml
                dir: '%kernel.project_dir%/src/Catalog/Infrastructure/Doctrine/Mapping'
                prefix: 'App\Catalog\Domain\Entity'
                alias: Catalog
```

### Service Auto-Wiring per Bounded Context

```yaml
# config/services.yaml
services:
    _defaults:
        autowire: true
        autoconfigure: true

    App\Order\:
        resource: '../src/Order/'
        exclude:
            - '../src/Order/Domain/Entity/'
            - '../src/Order/Domain/Event/'

    App\Order\Domain\Repository\OrderRepositoryInterface:
        class: App\Order\Infrastructure\Doctrine\DoctrineOrderRepository
```

### Messenger Routing per Context

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        buses:
            command.bus:
                middleware:
                    - doctrine_transaction
            query.bus: ~
        transports:
            async:
                dsn: '%env(MESSENGER_TRANSPORT_DSN)%'
        routing:
            'App\Order\Application\Command\*': async
            'App\Catalog\Application\Command\*': async
```

## When to Use Bundles vs Bounded Contexts

| Scenario | Use Bundle | Use Bounded Context |
|----------|-----------|-------------------|
| Third-party integration (Mailer, Logger) | Yes | No |
| Reusable across projects | Yes | No |
| Business domain modeling | No | Yes |
| Team ownership boundary | No | Yes |
| Independent deployment candidate | No | Yes |
| Shared technical concern (Auth, CORS) | Yes | No |

### Migration from Bundle to Bounded Context

```php
<?php

declare(strict_types=1);

// BEFORE: Bundle-based (antipattern for domain code)
// src/OrderBundle/Entity/Order.php
namespace App\OrderBundle\Entity;

// AFTER: DDD-aligned
// src/Order/Domain/Entity/Order.php
namespace App\Order\Domain\Entity;

final class Order
{
    // Pure domain logic, no framework dependencies
}
```

## Auto-Configuration for Controllers

```yaml
# config/services.yaml
services:
    App\Order\Presentation\Api\:
        resource: '../src/Order/Presentation/Api/'
        tags: ['controller.service_arguments']
```

This ensures invokable controllers in each bounded context are registered automatically.
