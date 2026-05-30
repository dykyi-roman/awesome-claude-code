# DEPTRAC — Layered (3-tier Domain-centric)

Aligned with `acc:layer-arch-knowledge`. Three layers: **Application** (entry-points), **Domain** (bounded contexts that own their persistence implementations), **Infrastructure** (generic, domain-agnostic clients).

## Defining trait

In this style **the Domain layer owns its persistence implementations**. The Repository abstraction and its concrete ORM implementation sit side-by-side under `Domain/{Context}/Repository/`:

```
Domain/Order/Repository/OrderRepositoryInterface.php
Domain/Order/Repository/Doctrine/OrderRepository.php
```

A Repository implementation under `Infrastructure/` would be a violation in this architecture. Infrastructure stays small — generic clients (Doctrine config, MessageBus, Redis, S3, GPT) with no knowledge of domain types.

## Folder structure assumed

```
src/
├── Application/
│   ├── Http/{Context}/Action/
│   ├── Http/{Context}/Request/
│   ├── Http/{Context}/Response/Transformer/
│   ├── Console/{Context}/
│   ├── DependencyInjection/{Context}/
│   ├── Security/{Authenticator|Voter|Provider}/
│   ├── Validator/
│   ├── Form/
│   ├── Twig/
│   ├── Subscriber/
│   └── Exception/
├── Domain/
│   ├── Shared/{Model|ValueObject|Enum|Exception}/
│   └── {Context}/
│       ├── Model/
│       ├── Handler/{UseCase}/
│       ├── Repository/                  # interface
│       ├── Repository/Doctrine/         # implementation (still in Domain)
│       ├── Service/
│       ├── Component/
│       ├── DAO/
│       ├── Enum/
│       ├── Event/
│       ├── ValueObject/
│       ├── Exception/
│       └── Subscriber/
└── Infrastructure/                      # generic, no domain types
    └── {GenericClient}/
```

## deptrac.yaml

```yaml
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Application — entry-points only
    #############################################
    - name: Application
      collectors:
        - type: directory
          value: src/Application/.*

    - name: Application.Http
      collectors:
        - type: directory
          value: src/Application/Http/.*

    - name: Application.Console
      collectors:
        - type: directory
          value: src/Application/Console/.*

    - name: Application.DI
      collectors:
        - type: directory
          value: src/Application/DependencyInjection/.*

    - name: Application.Security
      collectors:
        - type: directory
          value: src/Application/Security/.*

    - name: Application.Subscriber
      collectors:
        - type: directory
          value: src/Application/Subscriber/.*

    #############################################
    # Domain — bounded contexts + Shared
    #############################################
    - name: Domain
      collectors:
        - type: directory
          value: src/Domain/.*

    - name: Domain.Shared
      collectors:
        - type: directory
          value: src/Domain/Shared/.*

    # Repository interfaces (Domain/{Context}/Repository/*.php directly)
    - name: Domain.Repository.Interface
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Domain/.*/Repository/.*
          must_not:
            - type: directory
              value: src/Domain/.*/Repository/Doctrine/.*

    # Repository implementations — still INSIDE Domain (Doctrine subfolder)
    - name: Domain.Repository.Impl
      collectors:
        - type: directory
          value: src/Domain/.*/Repository/Doctrine/.*

    #############################################
    # Infrastructure — generic, domain-agnostic
    #############################################
    - name: Infrastructure
      collectors:
        - type: directory
          value: src/Infrastructure/.*

  ruleset:
    # Infrastructure is the leaf — extractable as a library
    Infrastructure: []

    # Domain depends on its own Shared subset and on Infrastructure interfaces
    Domain.Shared: []
    Domain:
      - Domain.Shared
      - Infrastructure
    Domain.Repository.Interface:
      - Domain
      - Domain.Shared
    # Doctrine impls live INSIDE Domain — they use Domain types and Infrastructure
    Domain.Repository.Impl:
      - Domain
      - Domain.Shared
      - Domain.Repository.Interface
      - Infrastructure

    # Application wires Domain + Infrastructure together
    Application:
      - Domain
      - Domain.Shared
      - Infrastructure
    Application.Http:
      - Domain
      - Domain.Shared
    Application.Console:
      - Domain
      - Domain.Shared
    Application.DI:
      - Domain
      - Infrastructure
    Application.Security:
      - Domain
      - Domain.Shared
    Application.Subscriber:
      - Domain
      - Domain.Shared
```

## Architecture-specific notes

1. **`Domain.Repository.Impl` is intentional.** It enforces the defining trait by making the Doctrine implementations a distinct layer with explicit allowed dependencies. A Repository implementation under `Infrastructure/Persistence/` would not match any layer in this config and would be flagged.

2. **Infrastructure cannot import Domain types.** The empty ruleset entry `Infrastructure: []` enforces that infrastructure clients stay generic. Domain-specific concerns (prompts, DTO transformation, business validation) must live inside the owning domain context's `Component/` or `Service/`.

3. **Application layer is thin.** It contains only entry-points (HTTP, Console, DI, Security, Form, Twig, Subscriber, Exception). Use Cases / Command Handlers belong inside `Domain/{Context}/Handler/{UseCase}/`, not in Application.

4. **Doctrine attributes on Domain entities are conventional** in this style. They are not a violation. ORM runtime types (`PersistentCollection`) still are, since they leak persistence concerns into the domain model.

## Common violation fixes

```
VIOLATION: Infrastructure\Persistence\OrderRepository found

FIX: In this architecture, Repository implementations live INSIDE Domain
alongside the abstraction. Move the implementation:

  src/Infrastructure/Persistence/OrderRepository.php
  → src/Domain/Order/Repository/Doctrine/OrderRepository.php
```

```
VIOLATION: Infrastructure\Order\OrderPdfRenderer depends on Domain\Order\Order

FIX: Infrastructure must stay domain-agnostic. Either:
- Move the PDF-rendering logic into Domain\Order\Component\ (the owning
  context's Component folder for rich business services), OR
- Generalize the infrastructure client so it doesn't know about Order
  (e.g. a generic PdfRenderer accepting a template + key/value pairs),
  and do the Order-specific assembly in Domain\Order\Component\.
```

```
VIOLATION: Application\Http\Action\Order\CreateOrderAction has an
           if/match on OrderStatus::Draft

FIX: Application Actions must be thin entry-points. Move business
state-checking into the CommandHandler at
Domain\Order\Handler\CreateOrder\CreateOrderCommandHandler.
```

## Bounded contexts

To enforce inter-context isolation on top of this architecture, see [bounded-contexts.md](bounded-contexts.md).
