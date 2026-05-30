# DEPTRAC — N-Tier (4-tier Classical)

Aligned with `acc:n-tier-arch-knowledge`. Four layers: **Presentation**, **Application**, **Domain**, **Infrastructure**. Strict downward calls — each layer communicates with the layer directly below it.

## Defining trait

```
┌─────────────────────────────────────────────────────┐
│   Presentation                                      │
│   (Controllers, Views, API Endpoints, CLI)          │
└──────────────────────┬──────────────────────────────┘
                       │ calls
                       ▼
┌─────────────────────────────────────────────────────┐
│   Application                                       │
│   (Services, Use Cases, DTOs, Facades)              │
└──────────────────────┬──────────────────────────────┘
                       │ calls
                       ▼
┌─────────────────────────────────────────────────────┐
│   Domain                                            │
│   (Entities, Value Objects, Domain Services)        │
└──────────────────────┬──────────────────────────────┘
                       │ calls (via interfaces)
                       ▼
┌─────────────────────────────────────────────────────┐
│   Infrastructure                                    │
│   (Repository impls, External APIs, Database)       │
└─────────────────────────────────────────────────────┘
```

**Key rule:** each layer calls the layer DIRECTLY BELOW. Presentation cannot skip Application to reach Domain or Infrastructure. Application can call Domain and Infrastructure. Domain depends on Infrastructure only through abstractions (Repository interfaces in Domain, implementations in Infrastructure).

This differs from Clean: in N-Tier, Application IS allowed to depend on Infrastructure directly. The strictness lives in the cross-layer skipping rule (Presentation → Domain is forbidden), not in dependency inversion at the Application/Infrastructure boundary.

## Folder structure assumed

```
src/
├── Presentation/
│   ├── Api/{Context}/
│   ├── Web/{Context}/
│   └── Console/{Context}/
├── Application/
│   └── {Context}/
│       ├── UseCase/
│       ├── Service/
│       └── DTO/
├── Domain/
│   └── {Context}/
│       ├── Entity/
│       ├── ValueObject/
│       ├── Event/
│       ├── Repository/        # interfaces only
│       └── Service/
└── Infrastructure/
    ├── Persistence/            # Repository implementations
    ├── Messaging/
    └── External/
```

## deptrac.yaml

```yaml
deptrac:
  paths:
    - ./src

  layers:
    #############################################
    # Presentation
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

    #############################################
    # Application
    #############################################
    - name: Application
      collectors:
        - type: directory
          value: src/Application/.*

    - name: Application.UseCase
      collectors:
        - type: directory
          value: src/Application/.*/UseCase/.*

    - name: Application.Service
      collectors:
        - type: directory
          value: src/Application/.*/Service/.*

    - name: Application.DTO
      collectors:
        - type: directory
          value: src/Application/.*/DTO/.*

    #############################################
    # Domain
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

    - name: Domain.Event
      collectors:
        - type: directory
          value: src/Domain/.*/Event/.*

    - name: Domain.Repository
      collectors:
        - type: directory
          value: src/Domain/.*/Repository/.*

    - name: Domain.Service
      collectors:
        - type: directory
          value: src/Domain/.*/Service/.*

    #############################################
    # Infrastructure
    #############################################
    - name: Infrastructure
      collectors:
        - type: directory
          value: src/Infrastructure/.*

    - name: Infrastructure.Persistence
      collectors:
        - type: directory
          value: src/Infrastructure/Persistence/.*

    - name: Infrastructure.Messaging
      collectors:
        - type: directory
          value: src/Infrastructure/Messaging/.*

    - name: Infrastructure.External
      collectors:
        - type: directory
          value: src/Infrastructure/External/.*

  ruleset:
    # Domain — innermost
    Domain.Entity: []
    Domain.ValueObject: []
    Domain.Event: []
    Domain.Repository: []   # interface-only — no Infrastructure types in signature
    Domain.Service:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Event
      - Domain.Repository
    Domain:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Event
      - Domain.Repository
      - Domain.Service

    # Application depends on Domain AND Infrastructure (KEY N-Tier difference vs. Clean)
    Application:
      - Domain
      - Infrastructure
    Application.UseCase:
      - Domain
      - Application.DTO
      - Application.Service
    Application.Service:
      - Domain
      - Infrastructure
    Application.DTO:
      - Domain.ValueObject

    # Infrastructure implements Domain.Repository interfaces
    Infrastructure:
      - Domain
    Infrastructure.Persistence:
      - Domain.Entity
      - Domain.ValueObject
      - Domain.Repository
    Infrastructure.Messaging:
      - Domain.Event
    Infrastructure.External:
      - Domain

    # Presentation calls Application ONLY — cannot skip to Domain or Infrastructure
    Presentation:
      - Application
    Presentation.Api:
      - Application.UseCase
      - Application.DTO
    Presentation.Web:
      - Application.UseCase
      - Application.DTO
    Presentation.Console:
      - Application.UseCase
```

## Architecture-specific notes

1. **Application IS allowed to depend on Infrastructure.** This is the key distinguishing rule from Clean Architecture. In N-Tier, Application Services orchestrate domain operations AND coordinate persistence transactions, calling Infrastructure code directly when needed.

2. **Presentation cannot skip Application.** A Controller cannot inject a Repository or call Infrastructure directly. All Presentation → Domain access goes through an Application Use Case or Service.

3. **Repository interfaces live in Domain; implementations in Infrastructure.** This is the conventional N-Tier placement. The Domain code uses the abstraction; the Infrastructure provides the concrete (Doctrine, PDO, MongoDB) implementation.

4. **Anemic services are a smell.** If `Application\Order\Service\OrderService` is just thin delegation to `Domain\Order\Repository\OrderRepository`, the business logic is missing — likely it leaked into the Controller or the Repository. Move it back into the Domain.

## Common violation fixes

```
VIOLATION: Presentation\Api\Order\OrderController depends on
           Domain\Order\Repository\OrderRepository

FIX: Presentation cannot skip Application. Inject an Application Service
or call a Use Case instead:

  Presentation\Api\Order\OrderController
      uses Application\Order\Service\OrderService
  OR
      uses Application\Order\UseCase\GetOrderUseCase
```

```
VIOLATION: Domain\Order\Order depends on Doctrine\ORM\PersistentCollection

FIX: Domain must contain pure business logic. Replace
PersistentCollection with a plain PHP array of OrderLine value objects.
Doctrine attributes on the entity are conventional and OK; ORM runtime
types are not.
```

```
VIOLATION: Domain\Order\Repository\OrderRepository (interface) signature
           contains Doctrine\Common\Collections\Criteria

FIX: The Domain Repository interface must use only Domain types.
Introduce a Domain-level filter object or use named methods
(findByStatus, findShippableToday) instead of leaking Doctrine\Criteria.
```

```
VIOLATION: Application\Order\Service\OrderService directly executes SQL

FIX: Application cannot bypass Domain to talk to the database. Route
through a Domain.Repository interface; the Infrastructure.Persistence
implementation does the SQL.
```

## Bounded contexts

To enforce inter-context isolation on top of this architecture, see [bounded-contexts.md](bounded-contexts.md).
