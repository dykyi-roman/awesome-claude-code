# DEPTRAC — Clean Architecture

Aligned with `acc:clean-arch-knowledge`. Four folders: **Domain**, **Application**, **Infrastructure**, **Presentation**. The distinguishing rule is **the Dependency Rule** — source code dependencies point INWARD only.

## Defining trait

```
┌─────────────────────────────────────────────┐
│  Presentation     Infrastructure            │  outer rings
│  (Controllers,    (Adapters,                │
│   Views)          Frameworks, DB)           │
├─────────────────────────────────────────────┤
│              Application                    │  inner ring
│       (Use Cases, Ports/Interfaces)         │
├─────────────────────────────────────────────┤
│                 Domain                      │  innermost
│   (Entities, Value Objects, Services)       │
└─────────────────────────────────────────────┘
                     ▲
       Source code dependencies point INWARD
```

Key consequence: **Application does NOT depend on Infrastructure.** Application defines Ports (interfaces) for what it needs; Infrastructure implements those Ports. The flow of control may go outward (Use Case calls a DB adapter), but the source code dependency points inward (the adapter implements the Application Port interface, depending on Application — not the other way around).

This is what distinguishes Clean from N-Tier. Both use the same four folder names; only Clean enforces strict dependency inversion across the Application/Infrastructure boundary.

## Folder structure assumed

```
src/
├── Domain/
│   └── {Context}/
│       ├── Entity/
│       ├── ValueObject/
│       ├── Service/
│       └── Event/
├── Application/
│   └── {Context}/
│       ├── UseCase/
│       ├── Port/            # interfaces the Use Case needs
│       └── DTO/
├── Infrastructure/
│   ├── Persistence/         # implements Application Ports
│   ├── Messaging/
│   └── External/            # API clients, etc.
└── Presentation/
    ├── Api/{Context}/
    ├── Web/{Context}/
    └── Console/{Context}/
```

## deptrac.yaml

```yaml
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Domain — innermost
    #############################################
    - name: Domain
      collectors:
        - type: directory
          value: src/Domain/.*

    - name: Domain.Entity
      collectors:
        - type: directory
          value: src/Domain/.*/Entity/.*

    - name: Domain.ValueObject
      collectors:
        - type: directory
          value: src/Domain/.*/ValueObject/.*

    - name: Domain.Service
      collectors:
        - type: directory
          value: src/Domain/.*/Service/.*

    - name: Domain.Event
      collectors:
        - type: directory
          value: src/Domain/.*/Event/.*

    #############################################
    # Application — depends ONLY on Domain
    #############################################
    - name: Application
      collectors:
        - type: directory
          value: src/Application/.*

    - name: Application.UseCase
      collectors:
        - type: directory
          value: src/Application/.*/UseCase/.*

    - name: Application.Port
      collectors:
        - type: directory
          value: src/Application/.*/Port/.*

    - name: Application.DTO
      collectors:
        - type: directory
          value: src/Application/.*/DTO/.*

    #############################################
    # Infrastructure — outer ring; implements Application Ports
    #############################################
    - name: Infrastructure
      collectors:
        - type: directory
          value: src/Infrastructure/.*

    #############################################
    # Presentation — outer ring; calls Application Use Cases
    #############################################
    - name: Presentation
      collectors:
        - type: directory
          value: src/Presentation/.*

    - name: Presentation.Api
      collectors:
        - type: directory
          value: src/Presentation/Api/.*

    - name: Presentation.Web
      collectors:
        - type: directory
          value: src/Presentation/Web/.*

    - name: Presentation.Console
      collectors:
        - type: directory
          value: src/Presentation/Console/.*

  ruleset:
    # Domain — innermost — depends on nothing
    Domain.Entity: []
    Domain.ValueObject: []
    Domain.Event: []
    Domain.Service:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Event
    Domain:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Event
      - Domain.Service

    # Application — depends ONLY on Domain (KEY Clean Architecture rule)
    # Note: NO Application → Infrastructure dependency
    Application:
      - Domain
    Application.UseCase:
      - Domain
      - Application.Port
      - Application.DTO
    Application.Port:
      - Domain
    Application.DTO:
      - Domain.ValueObject

    # Infrastructure — outer ring — implements Application.Port interfaces
    # and may use Domain types directly
    Infrastructure:
      - Application
      - Domain

    # Presentation — outer ring — calls Application Use Cases
    Presentation:
      - Application
      - Domain
    Presentation.Api:
      - Application.UseCase
      - Application.DTO
      - Domain.ValueObject
    Presentation.Web:
      - Application.UseCase
      - Application.DTO
    Presentation.Console:
      - Application.UseCase
```

## Architecture-specific notes

1. **`Application` does NOT list Infrastructure as a dependency.** This is the defining Clean Architecture constraint. If a Use Case needs a database, it depends on an `Application.Port` interface, and the Infrastructure adapter implements that interface.

2. **Infrastructure depends on Application.** This looks backwards from a "control flow" perspective but is correct for source code dependencies — a `DoctrineOrderRepository` IMPLEMENTS `Application\Order\Port\OrderRepositoryInterface`, so it must import that interface.

3. **Presentation can use Domain types.** DTOs and Value Objects from Domain may appear in API request/response types directly; this is conventional for Clean implementations in PHP.

4. **No framework code in Domain or Application.** Doctrine attributes, Symfony annotations, Laravel facades — all of these belong in Infrastructure or Presentation only.

## Common violation fixes

```
VIOLATION: Application\Order\UseCase\CreateOrderUseCase depends on
           Infrastructure\Persistence\DoctrineOrderRepository

FIX: Apply Dependency Inversion. Define a Port in Application:

  Application\Order\Port\OrderRepositoryInterface

The Use Case depends on the Port. The Infrastructure adapter implements it:

  Infrastructure\Persistence\DoctrineOrderRepository
      implements Application\Order\Port\OrderRepositoryInterface

Now the Use Case has zero knowledge of Doctrine.
```

```
VIOLATION: Domain\Order\Order depends on Doctrine\ORM\EntityManagerInterface

FIX: Domain must contain pure business logic. Move persistence concerns
out — entities should be plain PHP objects. If Doctrine attributes are
required, prefer XML/YAML mapping configured in Infrastructure instead.
```

```
VIOLATION: Presentation\Api\Order\OrderController has business logic
           (if/switch on Order status, computing totals)

FIX: Presentation must be thin. Move the logic into a Use Case under
Application\Order\UseCase\. The controller's job is to translate HTTP
into a Command/Query and back.
```

## Bounded contexts

To enforce inter-context isolation on top of this architecture, see [bounded-contexts.md](bounded-contexts.md).
