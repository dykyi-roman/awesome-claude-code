# DDD Integration with Symfony

Patterns for keeping the Domain layer pure while leveraging Symfony infrastructure.

## Domain Layer Without Framework Dependencies

### The Rule

Domain classes must never import Symfony or Doctrine namespaces. The domain defines interfaces; infrastructure implements them.

**Detection:**
```bash
# Symfony in Domain
Grep: "use Symfony\\\\" --glob "**/Domain/**/*.php"

# Doctrine in Domain
Grep: "use Doctrine\\\\" --glob "**/Domain/**/*.php"
Grep: "#\\[ORM\\\\" --glob "**/Domain/**/*.php"

# Infrastructure in Domain
Grep: "use.*Infrastructure\\\\" --glob "**/Domain/**/*.php"
```

**Bad:**
```php
<?php

declare(strict_types=1);

namespace Entity;

use Doctrine\ORM\Mapping as ORM;
use Symfony\Component\Validator\Constraints as Assert;

#[ORM\Entity]
class Order
{
    #[ORM\Id]
    #[ORM\Column(type: 'uuid')]
    private string $id;

    #[Assert\NotBlank]
    #[ORM\Column(type: 'string')]
    private string $status;
}
```

**Good:**
```php
<?php

declare(strict_types=1);

namespace Entity;

final class Order
{
    private OrderStatus $status;
    /** @var array<DomainEvent> */
    private array $events = [];

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
    ) {
        $this->status = OrderStatus::Draft;
    }

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new InvalidOrderStateException($this->status, OrderStatus::Confirmed);
        }

        $this->status = OrderStatus::Confirmed;
        $this->events[] = new OrderConfirmedEvent($this->id);
    }

    /** @return array<DomainEvent> */
    public function releaseEvents(): array
    {
        $events = $this->events;
        $this->events = [];

        return $events;
    }
}
```

## Symfony Messenger for CQRS

Messenger provides separate buses for commands and queries.

### Bus Configuration

```yaml
# config/packages/messenger.yaml
framework:
    messenger:
        default_bus: command.bus
        buses:
            command.bus:
                middleware:
                    - validation
                    - doctrine_transaction
            query.bus: ~
```

### Command (Write Side)

```php
<?php

declare(strict_types=1);

namespace Command;

final readonly class PlaceOrderCommand
{
    public function __construct(
        public string $customerId,
        /** @var array<array{product_id: string, quantity: int}> */
        public array $items,
    ) {}
}
```

### Command Handler

```php
<?php

declare(strict_types=1);

namespace Handler;

use Command\PlaceOrderCommand;
use Entity\Order;
use Repository\OrderRepositoryInterface;
use ValueObject\CustomerId;
use ValueObject\OrderId;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler(bus: 'command.bus')]
final readonly class PlaceOrderHandler
{
    public function __construct(
        private OrderRepositoryInterface $orders,
    ) {}

    public function __invoke(PlaceOrderCommand $command): OrderId
    {
        $order = Order::create(
            id: OrderId::generate(),
            customerId: new CustomerId($command->customerId),
            items: $command->items,
        );

        $this->orders->save($order);

        return $order->id();
    }
}
```

### Query (Read Side)

```php
<?php

declare(strict_types=1);

namespace Query;

final readonly class GetOrderQuery
{
    public function __construct(
        public string $orderId,
    ) {}
}
```

### Query Handler

```php
<?php

declare(strict_types=1);

namespace Handler;

use DTO\OrderDTO;
use Query\GetOrderQuery;
use Repository\OrderReadRepositoryInterface;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler(bus: 'query.bus')]
final readonly class GetOrderHandler
{
    public function __construct(
        private OrderReadRepositoryInterface $orders,
    ) {}

    public function __invoke(GetOrderQuery $query): OrderDTO
    {
        return $this->orders->findById($query->orderId)
            ?? throw new OrderNotFoundException($query->orderId);
    }
}
```

## Doctrine Events vs Domain Events

| Aspect | Doctrine Lifecycle Events | Domain Events |
|--------|--------------------------|---------------|
| Trigger | ORM operations (persist, flush) | Business operations |
| Location | Infrastructure | Domain |
| Coupling | Tied to Doctrine | Framework-agnostic |
| Testing | Requires EntityManager | Pure unit test |
| Use for | DB sync, audit logging | Business workflows |

**Detection of misuse:**
```bash
# Doctrine lifecycle events with business logic
Grep: "prePersist|postPersist|preUpdate|postUpdate" --glob "**/Domain/**/*.php"
Grep: "HasLifecycleCallbacks" --glob "**/Domain/**/*.php"

# Domain events dispatched correctly
Grep: "releaseEvents|domainEvents|recordedEvents" --glob "**/Domain/**/Entity/*.php"
```

**Bad — Doctrine listener with business logic:**
```php
<?php

declare(strict_types=1);

namespace Order\Infrastructure\Doctrine;

use Doctrine\ORM\Event\PostPersistEventArgs;

final readonly class OrderListener
{
    public function postPersist(PostPersistEventArgs $args): void
    {
        $entity = $args->getObject();
        if ($entity instanceof Order) {
            // VIOLATION: Business logic in Doctrine listener
            $this->mailer->sendOrderConfirmation($entity);
            $this->inventory->reserveStock($entity);
        }
    }
}
```

**Good — Domain events dispatched from Application layer:**
```php
<?php

declare(strict_types=1);

namespace Order\Infrastructure\Messenger;

use Event\OrderConfirmedEvent;
use Symfony\Component\Messenger\Attribute\AsMessageHandler;

#[AsMessageHandler]
final readonly class SendOrderConfirmationOnOrderConfirmed
{
    public function __construct(
        private MailerInterface $mailer,
    ) {}

    public function __invoke(OrderConfirmedEvent $event): void
    {
        $this->mailer->sendOrderConfirmation($event->orderId);
    }
}
```

## Value Objects with Doctrine Custom Types

### Custom Doctrine Type

```php
<?php

declare(strict_types=1);

namespace Infrastructure\Doctrine\Type;

use ValueObject\OrderId;
use Doctrine\DBAL\Platforms\AbstractPlatform;
use Doctrine\DBAL\Types\Type;

final class OrderIdType extends Type
{
    public const string NAME = 'order_id';

    public function getSQLDeclaration(array $column, AbstractPlatform $platform): string
    {
        return $platform->getGuidTypeDeclarationSQL($column);
    }

    public function convertToPHPValue(mixed $value, AbstractPlatform $platform): ?OrderId
    {
        return $value !== null ? new OrderId((string) $value) : null;
    }

    public function convertToDatabaseValue(mixed $value, AbstractPlatform $platform): ?string
    {
        return $value instanceof OrderId ? $value->value : null;
    }

    public function getName(): string
    {
        return self::NAME;
    }
}
```

### Register the Type

```yaml
# config/packages/doctrine.yaml
doctrine:
    dbal:
        types:
            order_id: App\Shared\Infrastructure\Doctrine\Type\OrderIdType
```

### XML Mapping with Custom Type

```xml
<!-- src/Order/Infrastructure/Doctrine/Mapping/Order.orm.xml -->
<doctrine-mapping xmlns="http://doctrine-project.org/schemas/orm/doctrine-mapping">
    <entity name="App\Order\Domain\Entity\Order" table="orders">
        <id name="id" type="order_id" column="id"/>
        <field name="status" type="string" column="status"/>
        <field name="createdAt" type="datetime_immutable" column="created_at"/>
    </entity>
</doctrine-mapping>
```

## Security in DDD Context

The Security component requires special DDD treatment since `UserInterface` is deeply integrated into Symfony's authentication system.

**Key patterns:**
- Domain `User` aggregate stays pure PHP — no `UserInterface` implementation
- Infrastructure `SecurityUser` adapter wraps Domain `User` and implements `UserInterface`
- Authorization uses Voters that delegate to domain Specifications
- Password hashing uses a domain `PasswordHasherInterface` port

See `security.md` for full implementation details with detection patterns and code examples.

## Advanced Messenger Patterns

The basic CQRS setup above covers bus configuration and handlers. For production systems, additional patterns are critical:
- **Retry strategy** with exponential backoff for transient failures
- **Failed transport** (Dead Letter Queue) for messages that exhaust retries
- **Custom middleware** for logging, correlation, domain event dispatching
- **Worker management** with Supervisor for graceful shutdown

See `messenger-advanced.md` for transport configuration, retry strategies, middleware pipeline, and worker setup.

## Workflow for Aggregate Lifecycle

Symfony Workflow component manages aggregate state transitions declaratively instead of manual `if/switch` chains:
- **StateMachine** type for single-state aggregate lifecycle (e.g., Order: draft → confirmed → shipped)
- **Guard events** delegate to domain Specifications for business rule validation
- **Transition events** dispatch domain events on state changes

See `workflow.md` for full configuration, enum-backed places, and DDD-aligned guard patterns.

## Keeping Domain Pure — Summary

| Layer | Allowed Dependencies | Forbidden |
|-------|---------------------|-----------|
| Domain | Pure PHP, own Value Objects | Symfony, Doctrine, any framework |
| Application | Domain interfaces, Messenger attributes | HTTP classes, Doctrine ORM |
| Infrastructure | Doctrine, Symfony components, Domain interfaces | Business logic |
| Presentation | Symfony HTTP, Application DTOs | Domain entities directly |

| DDD Aspect | Symfony Component | Integration Pattern |
|------------|-------------------|---------------------|
| User Aggregate | Security (`UserInterface`) | Infrastructure adapter wrapping Domain entity |
| Authorization | Security (Voters) | Voter delegates to domain Specification |
| State Lifecycle | Workflow (StateMachine) | YAML config + guard listeners with Specifications |
| Domain Events | Messenger (event.bus) | Domain `EventDispatcherInterface` + Messenger adapter |
| Caching | Cache (PSR-6/16) | Domain port + Infrastructure adapter |
| External APIs | HTTP Client | Domain port + scoped client adapter |
