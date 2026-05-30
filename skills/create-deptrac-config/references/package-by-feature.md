# DEPTRAC — Package-by-Feature

Package-by-Feature is an **organizational principle**, not a standalone architecture. The codebase is partitioned by **bounded context (feature)** at the top level; the chosen architectural style — Clean, Layered 3-tier, Hexagonal, or N-Tier — is applied **inside** each feature folder.

## Defining trait

The same architectural style can be expressed two ways at the file-system level:

```
Layer-first (NOT PBF):                    Feature-first (PBF):
src/                                       src/
├── Domain/                                ├── Order/
│   ├── Order/                             │   ├── Domain/
│   └── Payment/                           │   ├── Application/
├── Application/                           │   └── Infrastructure/
│   ├── Order/                             ├── Payment/
│   └── Payment/                           │   ├── Domain/
└── Infrastructure/                        │   ├── Application/
    ├── Order/                             │   └── Infrastructure/
    └── Payment/                           └── Shared/
```

Both layouts can use the SAME architectural rules. The choice is about folder organization (which is the outermost grouping — layer or feature), not about layer dependencies. PBF picks the right column.

## When to choose PBF

- **Deletability.** Removing a feature should touch one folder, not many. Drop `src/Order/`; the Order feature is gone.
- **Feature-team isolation.** Per-feature git diffs stay localized; cross-team PR conflicts shrink.
- **Visibility.** Top-level `src/` lists business capabilities (Order, Payment, Shipping), not technical concerns.
- **Internal flexibility.** Each feature is free to use the architecture that fits its complexity — a CRUDdy feature can stay flat; a complex one can use full Layered / Clean / Hexagonal internally.

## PBF + Layered 3-tier (Domain-centric)

Architecture: `acc:layer-arch-knowledge`. Each feature contains Application / Domain / Infrastructure subfolders; Domain owns its persistence implementations under `Domain/Repository/Doctrine/`.

```
src/
├── Shared/                  # cross-feature primitives (Money, Email)
└── Order/
    ├── Application/
    │   ├── Http/
    │   ├── Console/
    │   ├── DependencyInjection/
    │   └── Security/
    ├── Domain/
    │   ├── Model/
    │   ├── Handler/{UseCase}/
    │   ├── Repository/                       # interface
    │   ├── Repository/Doctrine/              # implementation (still inside Domain)
    │   ├── Service/
    │   ├── Component/
    │   ├── ValueObject/
    │   └── Event/
    └── Infrastructure/                       # generic, no domain types
```

```yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Shared
      collectors:
        - type: directory
          value: src/Shared/.*

    ### Feature: Order
    - name: Order.Application
      collectors:
        - type: directory
          value: src/Order/Application/.*

    - name: Order.Domain
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Order/Domain/.*
          must_not:
            - type: directory
              value: src/Order/Domain/.*/Repository/Doctrine/.*

    - name: Order.Domain.Repository.Impl
      collectors:
        - type: directory
          value: src/Order/Domain/.*/Repository/Doctrine/.*

    - name: Order.Infrastructure
      collectors:
        - type: directory
          value: src/Order/Infrastructure/.*

    ### Feature: Payment (mirror the Order block)
    - name: Payment.Application
      collectors:
        - type: directory
          value: src/Payment/Application/.*

    - name: Payment.Domain
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Payment/Domain/.*
          must_not:
            - type: directory
              value: src/Payment/Domain/.*/Repository/Doctrine/.*

    - name: Payment.Domain.Repository.Impl
      collectors:
        - type: directory
          value: src/Payment/Domain/.*/Repository/Doctrine/.*

    - name: Payment.Infrastructure
      collectors:
        - type: directory
          value: src/Payment/Infrastructure/.*

  ruleset:
    Shared: []

    # Internal Layered 3-tier rules per feature
    Order.Infrastructure: []
    Order.Domain:
      - Order.Infrastructure
      - Shared
    Order.Domain.Repository.Impl:
      - Order.Domain
      - Order.Infrastructure
      - Shared
    Order.Application:
      - Order.Domain
      - Order.Infrastructure
      - Shared

    Payment.Infrastructure: []
    Payment.Domain:
      - Payment.Infrastructure
      - Shared
    Payment.Domain.Repository.Impl:
      - Payment.Domain
      - Payment.Infrastructure
      - Shared
    Payment.Application:
      - Payment.Domain
      - Payment.Infrastructure
      - Shared
```

> **Cross-feature isolation is enforced by omission.** `Order.Application` is allowed to depend on `Order.Domain`, `Order.Infrastructure`, `Shared` — and nothing else. Any import from Order code into Payment code is automatically a violation.

## PBF + Clean Architecture

Architecture: `acc:clean-arch-knowledge`. Each feature contains Domain / Application / Infrastructure / Presentation. KEY rule: `{Feature}.Application` does NOT depend on `{Feature}.Infrastructure` (Dependency Inversion).

```
src/
├── Shared/
└── Order/
    ├── Domain/
    │   ├── Entity/
    │   ├── Aggregate/
    │   ├── ValueObject/
    │   └── Service/
    ├── Application/
    │   ├── UseCase/
    │   ├── Command/
    │   ├── Handler/
    │   ├── Port/                  # interfaces the Use Case needs
    │   └── DTO/
    ├── Infrastructure/
    │   └── Persistence/
    │       └── Doctrine/
    │           └── OrderRepository.php   # implements Order/Application/Port interface
    └── Presentation/
        ├── Http/
        ├── Console/
        └── Twig/
```

```yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Shared
      collectors:
        - type: directory
          value: src/Shared/.*

    ### Feature: Order
    - name: Order.Domain
      collectors:
        - type: directory
          value: src/Order/Domain/.*

    - name: Order.Application
      collectors:
        - type: directory
          value: src/Order/Application/.*

    - name: Order.Application.Port
      collectors:
        - type: directory
          value: src/Order/Application/Port/.*

    - name: Order.Infrastructure
      collectors:
        - type: directory
          value: src/Order/Infrastructure/.*

    - name: Order.Presentation
      collectors:
        - type: directory
          value: src/Order/Presentation/.*

    ### Feature: Payment (mirror)
    # ... same shape as Order

  ruleset:
    Shared: []

    # Domain — innermost
    Order.Domain:
      - Shared

    # Application — depends ONLY on Domain (Clean rule: no Application → Infrastructure)
    Order.Application:
      - Order.Domain
      - Order.Application.Port
      - Shared
    Order.Application.Port:
      - Order.Domain
      - Shared

    # Infrastructure — implements Application.Port; outer ring
    Order.Infrastructure:
      - Order.Application
      - Order.Application.Port
      - Order.Domain
      - Shared

    # Presentation — calls Application Use Cases
    Order.Presentation:
      - Order.Application
      - Order.Domain
      - Shared
```

## PBF + Hexagonal (Ports & Adapters)

Architecture: `acc:hexagonal-knowledge`. Driving Ports inside `{Feature}/Application/Port/Input/`; Driven Ports inside `{Feature}/Domain/Port/Output/`; Adapters under `{Feature}/Infrastructure/{Http,Persistence,...}/`.

```
src/
├── Shared/
└── Order/
    ├── Domain/
    │   ├── Entity/
    │   ├── ValueObject/
    │   └── Port/
    │       └── Output/             # Driven Ports
    ├── Application/
    │   ├── UseCase/
    │   ├── DTO/
    │   └── Port/
    │       └── Input/              # Driving Ports
    └── Infrastructure/
        ├── Http/                   # Driving Adapter
        ├── Console/                # Driving Adapter
        ├── Persistence/
        │   └── Doctrine/           # Driven Adapter
        └── External/               # Driven Adapter
```

```yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Shared
      collectors:
        - type: directory
          value: src/Shared/.*

    ### Feature: Order
    - name: Order.Domain
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Order/Domain/.*
          must_not:
            - type: directory
              value: src/Order/Domain/Port/Output/.*

    - name: Order.Port.Driven
      collectors:
        - type: directory
          value: src/Order/Domain/Port/Output/.*

    - name: Order.Application
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Order/Application/.*
          must_not:
            - type: directory
              value: src/Order/Application/Port/Input/.*

    - name: Order.Port.Driving
      collectors:
        - type: directory
          value: src/Order/Application/Port/Input/.*

    - name: Order.Adapter.Driving
      collectors:
        - type: directory
          value: src/Order/Infrastructure/(Http|Console|Messaging)/.*

    - name: Order.Adapter.Driven
      collectors:
        - type: directory
          value: src/Order/Infrastructure/(Persistence|External)/.*

    ### Feature: Payment (mirror)

  ruleset:
    Shared: []

    Order.Domain:
      - Shared
    Order.Port.Driven:
      - Order.Domain
      - Shared

    Order.Application:
      - Order.Domain
      - Order.Port.Driven
      - Shared
    Order.Port.Driving:
      - Order.Application
      - Order.Domain
      - Shared

    Order.Adapter.Driving:
      - Order.Port.Driving
      - Order.Domain
      - Shared
    Order.Adapter.Driven:
      - Order.Port.Driven
      - Order.Domain
      - Shared
```

## PBF + N-Tier (4-tier Classical)

Architecture: `acc:n-tier-arch-knowledge`. Each feature contains Presentation / Application / Domain / Infrastructure with strict downward calls. Application IS allowed to depend on Infrastructure (key diff vs. Clean).

```
src/
├── Shared/
└── Order/
    ├── Presentation/
    │   ├── Api/
    │   ├── Web/
    │   └── Console/
    ├── Application/
    │   ├── UseCase/
    │   ├── Service/
    │   └── DTO/
    ├── Domain/
    │   ├── Entity/
    │   ├── ValueObject/
    │   ├── Event/
    │   ├── Repository/            # interfaces only
    │   └── Service/
    └── Infrastructure/
        ├── Persistence/           # Repository implementations
        ├── Messaging/
        └── External/
```

```yaml
deptrac:
  paths:
    - ./src

  layers:
    - name: Shared
      collectors:
        - type: directory
          value: src/Shared/.*

    ### Feature: Order
    - name: Order.Domain
      collectors:
        - type: directory
          value: src/Order/Domain/.*

    - name: Order.Domain.Repository
      collectors:
        - type: directory
          value: src/Order/Domain/Repository/.*

    - name: Order.Application
      collectors:
        - type: directory
          value: src/Order/Application/.*

    - name: Order.Infrastructure
      collectors:
        - type: directory
          value: src/Order/Infrastructure/.*

    - name: Order.Presentation
      collectors:
        - type: directory
          value: src/Order/Presentation/.*

    ### Feature: Payment (mirror)

  ruleset:
    Shared: []

    Order.Domain:
      - Shared
    Order.Domain.Repository:
      - Order.Domain
      - Shared

    # Application depends on Domain AND Infrastructure (N-Tier key rule)
    Order.Application:
      - Order.Domain
      - Order.Infrastructure
      - Shared

    # Infrastructure implements Domain.Repository
    Order.Infrastructure:
      - Order.Domain
      - Order.Domain.Repository
      - Shared

    # Presentation calls Application only — cannot skip to Domain/Infrastructure
    Order.Presentation:
      - Order.Application
      - Shared
```

## Cross-feature communication

The configs above enforce **strict feature isolation** — `Order` code cannot reach inside `Payment` code at all. Real systems need cross-feature interaction; PBF doesn't mandate a single mechanism. Common choices:

1. **Domain events.** Order publishes `OrderPlaced`; Payment subscribes via an event bus. The event class itself can live in `Shared/Events/` or be duplicated in each subscriber (decoupled).

2. **Anti-corruption layer.** One feature exposes a stable interface (`PaymentGatewayInterface`); the consuming feature writes its own adapter that translates between the two domain models. The adapter lives in the consumer's `Infrastructure/`.

3. **Shared kernel.** For genuinely cross-cutting primitives (`Money`, `Email`, `Clock`), extract to `Shared/`. Resist the temptation to push feature-specific types here; the kernel should stay small.

If you want deptrac to ALLOW a specific cross-feature dependency (e.g., Order can use a published Payment interface), add an explicit allowance:

```yaml
ruleset:
  Order.Application:
    - Order.Domain
    - Order.Infrastructure
    - Shared
    - Payment.PublishedInterface   # explicit, narrow exception
```

— and declare `Payment.PublishedInterface` as a layer matching the exact directory you want to expose (e.g. `src/Payment/Application/PublishedInterface/.*`).

## Common violation fixes

```
VIOLATION: src/Order/Application/CreateOrderHandler.php depends on
           src/Payment/Domain/Payment.php

FIX: Direct cross-feature import is not allowed. Choose one of:
- Publish an OrderPlaced event from Order; Payment subscribes.
- Define a stable contract in Payment that Order is allowed to use,
  and add an explicit allowance in deptrac.yaml.
- If the shared concept is truly universal (Money, OrderId-like
  cross-cutting), move it into Shared/.
```

```
VIOLATION: src/Order/Infrastructure/Persistence/Doctrine/OrderRepository.php
           (with PBF + Clean rule set)
           depends on src/Order/Domain/Entity/Order.php — ALLOWED

VIOLATION: src/Order/Application/CreateOrderUseCase.php depends on
           src/Order/Infrastructure/Persistence/Doctrine/OrderRepository.php

FIX: This is the Clean violation INSIDE PBF — Application must not
depend on Infrastructure. Define a Port in Order/Application/Port/ and
have the Use Case depend on the Port; the Infrastructure adapter
implements that Port.
```

```
VIOLATION (PBF + Layered): src/Order/Infrastructure/Persistence/OrderRepository.php found

FIX: Layered 3-tier Domain-centric keeps Repository implementations
INSIDE Domain. Move:
  src/Order/Infrastructure/Persistence/OrderRepository.php
  → src/Order/Domain/Repository/Doctrine/OrderRepository.php
```

## Not the same as bounded-contexts.md

The [bounded-contexts.md](bounded-contexts.md) reference describes the **layer-first** multi-context layout (`src/Domain/Order/`, `src/Application/Order/`, ...). It's the OPPOSITE column from PBF. Pick one or the other for any given project; mixing them inside a single project is confusing.
