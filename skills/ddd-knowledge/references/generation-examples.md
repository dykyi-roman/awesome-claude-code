# DDD Generation Examples

Example commands and the files each one produces. Path examples below use the `{architecture-path}` placeholder for the architecture-specific folder portion — the literal value depends on the project's chosen architecture (Clean / Hexagonal / Layered 3-tier / N-Tier / Package-by-Feature / MVC). See [`layer-architecture.md`](layer-architecture.md) for the per-architecture placement table.

## Domain model components

### Entity
```bash
/acc:generate-ddd entity Order
/acc:generate-ddd ent User -- with soft delete
```

Generates:
```
src/{architecture-path}/Order/Entity/
├── Order.php
└── OrderId.php (Value Object)
tests/Unit/{architecture-path}/Order/Entity/
└── OrderTest.php
```

### Value Object
```bash
/acc:generate-ddd value-object Email
/acc:generate-ddd vo Money -- with currency support
```

Generates:
```
src/{architecture-path}/User/ValueObject/
├── Email.php
└── Exception/InvalidEmailException.php
tests/Unit/{architecture-path}/User/ValueObject/
└── EmailTest.php
```

### Aggregate
```bash
/acc:generate-ddd aggregate Order
/acc:generate-ddd agg ShoppingCart -- with CartItem child entity
```

Generates:
```
src/{architecture-path}/Order/Entity/
├── Order.php (Aggregate Root)
├── OrderLine.php (Child Entity)
├── OrderId.php
└── OrderStatus.php (Enum)
src/{architecture-path}/Order/Event/
└── OrderCreatedEvent.php
tests/Unit/{architecture-path}/Order/Entity/
├── OrderTest.php
└── OrderLineTest.php
```

### Domain Event
```bash
/acc:generate-ddd domain-event OrderConfirmed
/acc:generate-ddd event UserRegistered
```

Generates:
```
src/{architecture-path}/Order/Event/
└── OrderConfirmedEvent.php
tests/Unit/{architecture-path}/Order/Event/
└── OrderConfirmedEventTest.php
```

### Repository
```bash
/acc:generate-ddd repository Order
/acc:generate-ddd repo User -- Doctrine implementation
```

Generates (folder placement of the concrete class varies by architecture — see [`layer-architecture.md`](layer-architecture.md)):
```
src/{architecture-path}/Order/Repository/
└── OrderRepositoryInterface.php
src/{architecture-path-for-persistence}/Doctrine/
└── DoctrineOrderRepository.php
tests/Unit/{architecture-path}/Order/Repository/
└── InMemoryOrderRepository.php
```

In Layered 3-tier (Domain-centric) the Doctrine class lands at `src/{architecture-path}/Order/Repository/Doctrine/`; in Clean / Hexagonal / N-Tier it lands under `src/Infrastructure/Persistence/{Doctrine}/`. The `{architecture-path-for-persistence}` placeholder reflects that variation.

### Domain Service
```bash
/acc:generate-ddd domain-service MoneyTransfer
/acc:generate-ddd ds PriceCalculator -- with discount rules
```

Generates:
```
src/{architecture-path}/Payment/Service/
└── MoneyTransferService.php
tests/Unit/{architecture-path}/Payment/Service/
└── MoneyTransferServiceTest.php
```

### Factory
```bash
/acc:generate-ddd factory Order
/acc:generate-ddd fact User -- from external API
```

Generates:
```
src/{architecture-path}/Order/Factory/
└── OrderFactory.php
tests/Unit/{architecture-path}/Order/Factory/
└── OrderFactoryTest.php
```

### Specification
```bash
/acc:generate-ddd specification IsActiveCustomer
/acc:generate-ddd spec CanPlaceOrder -- composite
```

Generates:
```
src/{architecture-path}/Customer/Specification/
└── IsActiveCustomerSpecification.php
tests/Unit/{architecture-path}/Customer/Specification/
└── IsActiveCustomerSpecificationTest.php
```

## Orchestration components

### Command
```bash
/acc:generate-ddd command CreateOrder
/acc:generate-ddd cmd UpdateUserProfile
```

Generates:
```
src/{architecture-path}/Order/Command/
├── CreateOrderCommand.php
└── CreateOrderHandler.php
tests/Unit/{architecture-path}/Order/Command/
├── CreateOrderCommandTest.php
└── CreateOrderHandlerTest.php
```

### Query
```bash
/acc:generate-ddd query GetOrderDetails
/acc:generate-ddd qry ListUserOrders -- with pagination
```

Generates:
```
src/{architecture-path}/Order/Query/
├── GetOrderDetailsQuery.php
└── GetOrderDetailsHandler.php
tests/Unit/{architecture-path}/Order/Query/
├── GetOrderDetailsQueryTest.php
└── GetOrderDetailsHandlerTest.php
```

### Use Case
```bash
/acc:generate-ddd use-case ProcessPayment
/acc:generate-ddd uc RegisterUser -- with email verification
```

Generates:
```
src/{architecture-path}/Payment/UseCase/
└── ProcessPaymentUseCase.php
tests/Unit/{architecture-path}/Payment/UseCase/
└── ProcessPaymentUseCaseTest.php
```

### DTO
```bash
/acc:generate-ddd dto OrderRequest
/acc:generate-ddd data-transfer UserResponse -- for REST API
```

Generates:
```
src/{architecture-path}/Order/DTO/
└── OrderRequestDto.php
tests/Unit/{architecture-path}/Order/DTO/
└── OrderRequestDtoTest.php
```

## Integration components

### Anti-Corruption Layer
```bash
/acc:generate-ddd acl StripePayment
/acc:generate-ddd anti-corruption ExternalCrm -- translate to domain
```

Generates:
```
src/{architecture-path}/ACL/Stripe/
├── StripePaymentAdapter.php
├── StripePaymentTranslator.php
└── StripePaymentFacade.php
tests/Unit/{architecture-path}/ACL/Stripe/
└── StripePaymentAdapterTest.php
```

## Expected Output

### Generated Files Summary

```
Generated Entity: Order

Files created:
├── src/{architecture-path}/Order/Entity/
│   ├── Order.php
│   └── OrderId.php
├── src/{architecture-path}/Order/Exception/
│   └── InvalidOrderException.php
└── tests/Unit/{architecture-path}/Order/Entity/
    └── OrderTest.php
```

### Pattern markers (sub-folders inside the architecture path)

Independent of architecture, DDD components are named by their pattern marker. The placement of these sub-folders varies (per the [`layer-architecture.md`](layer-architecture.md) table) but the marker names are stable:

```
Domain-model markers:
├── Entity/         → Entities, Aggregates, Child Entities
├── ValueObject/    → Value Objects, IDs
├── Repository/     → Repositories (the pattern; concrete class
│                     placement varies by architecture)
├── Service/        → Domain Services
├── Factory/        → Domain Factories
├── Specification/  → Business Rules
├── Event/          → Domain Events
├── Enum/           → Status, Type enums
└── Exception/      → Domain Exceptions

Orchestration markers:
├── Command/        → Commands + Handlers
├── Query/          → Queries + Handlers
├── UseCase/        → Use Cases
├── DTO/            → Data Transfer Objects
├── Handler/        → Command / Query / Event Handlers
└── ReadModel/      → Read Model abstractions

Integration markers:
├── ACL/            → Anti-Corruption Layer adapters
├── Port/           → External-service interfaces (esp. Hexagonal)
└── Adapter/        → Concrete adapter classes
```

## Multiple Components

Generate related components together:

```bash
# Generate full aggregate
/acc:generate-ddd aggregate Order
/acc:generate-ddd command CreateOrder
/acc:generate-ddd query GetOrderById

# Generate CQRS stack
/acc:generate-ddd command UpdateOrder
/acc:generate-ddd query ListOrders -- with filters
```
