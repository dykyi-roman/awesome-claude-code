# DEPTRAC — Hexagonal Architecture (Ports & Adapters)

Aligned with `acc:hexagonal-knowledge`. Three folders: **Domain**, **Application**, **Infrastructure**. The distinguishing trait is explicit **Port** subfolders defining how to interact with the application core, and **Adapters** under Infrastructure that implement or use them.

## Defining trait

```
              Driving Adapters
              (HTTP, CLI, Consumers)
                      │
                      ▼
              Driving Ports (Input)
              Application/{Context}/Port/Input/
                      │
                      ▼
              ┌──────────────────┐
              │  APPLICATION     │
              │  Use Cases       │
              └─────────┬────────┘
                        │
                        ▼
              ┌──────────────────┐
              │     DOMAIN       │
              │  Entities, VOs   │
              └─────────┬────────┘
                        │
                        ▼
              Driven Ports (Output)
              Domain/{Context}/Port/Output/
                      ▲
                      │
              Driven Adapters
              (DB, External APIs)
```

**Driving Ports** (Input) — how external actors invoke the application — live under `Application/{Context}/Port/Input/`.
**Driven Ports** (Output) — what the application needs from the outside — live under `Domain/{Context}/Port/Output/`.
**Driving Adapters** (HTTP controllers, CLI commands, message consumers) live under `Infrastructure/Http/`, `Infrastructure/Console/`, `Infrastructure/Messaging/`.
**Driven Adapters** (Repository implementations, external API clients) live under `Infrastructure/Persistence/`, `Infrastructure/External/`.

## Folder structure assumed

```
src/
├── Domain/
│   └── {Context}/
│       ├── Entity/
│       ├── ValueObject/
│       ├── Service/
│       └── Port/
│           └── Output/        # Driven Ports (Repository, external APIs)
├── Application/
│   └── {Context}/
│       ├── UseCase/
│       ├── DTO/
│       └── Port/
│           └── Input/         # Driving Ports (Use Case interfaces)
└── Infrastructure/
    ├── Http/                  # Driving Adapter — HTTP
    │   └── Controller/
    ├── Console/               # Driving Adapter — CLI
    ├── Messaging/             # Driving Adapter — message consumers
    ├── Persistence/           # Driven Adapter — DB
    │   └── Doctrine/
    └── External/              # Driven Adapter — external APIs
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
        - type: bool
          must:
            - type: directory
              value: src/Domain/.*
          must_not:
            - type: directory
              value: src/Domain/.*/Port/Output/.*

    # Driven Ports — interfaces the Domain/Application needs from outside
    - name: Port.Driven
      collectors:
        - type: directory
          value: src/Domain/.*/Port/Output/.*

    #############################################
    # Application
    #############################################
    - name: Application
      collectors:
        - type: bool
          must:
            - type: directory
              value: src/Application/.*
          must_not:
            - type: directory
              value: src/Application/.*/Port/Input/.*

    - name: Application.UseCase
      collectors:
        - type: directory
          value: src/Application/.*/UseCase/.*

    - name: Application.DTO
      collectors:
        - type: directory
          value: src/Application/.*/DTO/.*

    # Driving Ports — interfaces external actors use to invoke the application
    - name: Port.Driving
      collectors:
        - type: directory
          value: src/Application/.*/Port/Input/.*

    #############################################
    # Infrastructure adapters
    #############################################
    # Driving Adapters — implement entry mechanisms (HTTP, CLI, Consumers)
    - name: Adapter.Driving
      collectors:
        - type: directory
          value: src/Infrastructure/(Http|Console|Messaging)/.*

    # Driven Adapters — implement Driven Ports (DB, External APIs)
    - name: Adapter.Driven
      collectors:
        - type: directory
          value: src/Infrastructure/(Persistence|External)/.*

  ruleset:
    # Domain — innermost — no dependencies
    Domain: []

    # Driven Ports live in Domain and may use Domain types
    Port.Driven:
      - Domain

    # Application uses Domain and the Driven Ports
    Application:
      - Domain
      - Port.Driven
    Application.UseCase:
      - Domain
      - Application.DTO
      - Port.Driven
    Application.DTO:
      - Domain

    # Driving Ports describe Use Case entry interfaces
    Port.Driving:
      - Application
      - Application.DTO
      - Application.UseCase
      - Domain

    # Driving Adapters call Driving Ports (the application's entry interface)
    Adapter.Driving:
      - Port.Driving
      - Application.DTO
      - Domain

    # Driven Adapters implement Driven Ports
    Adapter.Driven:
      - Port.Driven
      - Domain
```

## Architecture-specific notes

1. **Symmetric Port structure.** Driving Ports describe how to USE the application (their signature is what callers see). Driven Ports describe what the application NEEDS from the outside (their signature reflects domain types).

2. **Port placement is deliberate.** Driving Ports live in Application because they describe Use Case boundaries. Driven Ports live in Domain because the contract is shaped by what the domain needs — not by what's available in any external system.

3. **`Adapter.Driven` cannot import `Application`.** A Driven Adapter (like a Doctrine repository) implements a Driven Port whose contract is in Domain. It must not reach into Application code — that would couple the storage adapter to use-case orchestration.

4. **`Adapter.Driving` does not import `Adapter.Driven` directly.** Driving Adapters call Driving Ports (the use-case interfaces). They never reach into Driven Adapters; the application core coordinates between them.

## Common violation fixes

```
VIOLATION: Infrastructure\Persistence\Doctrine\DoctrineOrderRepository
           depends on Application\Order\UseCase\CreateOrderUseCase

FIX: Driven Adapters must depend only on Driven Ports, not Use Cases.
Define the contract as a Driven Port in Domain:

  Domain\Order\Port\Output\OrderRepositoryInterface

The Driven Adapter implements that interface:

  Infrastructure\Persistence\Doctrine\DoctrineOrderRepository
      implements Domain\Order\Port\Output\OrderRepositoryInterface
```

```
VIOLATION: Infrastructure\Http\Controller\OrderController depends on
           Infrastructure\Persistence\Doctrine\DoctrineOrderRepository

FIX: A Driving Adapter (HTTP) must not call a Driven Adapter (DB) directly.
Inject a Driving Port (Use Case interface) into the controller:

  Infrastructure\Http\Controller\OrderController
      uses Application\Order\Port\Input\CreateOrderUseCaseInterface

The Use Case is implemented by Application code, and the Use Case itself
calls the Driven Port (which the Driven Adapter implements).
```

```
VIOLATION: Domain\Order\Port\Output\OrderRepositoryInterface signature
           contains Doctrine\ORM\Query\Expr\Comparison

FIX: Driven Ports must use only Domain types in their signatures. The
adapter translates between Domain types and external-system types
INSIDE the adapter, not at the port boundary.
```

## Bounded contexts

To enforce inter-context isolation on top of this architecture, see [bounded-contexts.md](bounded-contexts.md).
