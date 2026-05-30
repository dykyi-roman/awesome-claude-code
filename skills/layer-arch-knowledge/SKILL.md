---
name: layer-arch-knowledge
description: Domain-centric Layered Architecture knowledge base. 3 layers (Application, Domain, Infrastructure) where each bounded context inside Domain owns its model, handlers, AND repository implementations. The defining trait — repository implementation lives alongside the abstraction under `Domain/{Context}/Repository/{Doctrine}/` rather than in Infrastructure. Distinct from `n-tier-arch-knowledge` (classical 4-layer downward calls; repositories in Infrastructure) and `clean-arch-knowledge` (dependency inversion via ports/adapters).
---

# Layered Architecture Knowledge Base

Quick reference for the **3-layer Domain-centric Layered Architecture** commonly used in modern Symfony / PHP modular-monolith projects. This is one of several DDD-compatible architectural styles documented in this plugin.

## How this differs from sibling architectures

| Concern | Layered (this skill) | N-Tier (`n-tier-arch-knowledge`) | Clean / Hexagonal (`clean-arch-knowledge`, `hexagonal-knowledge`) |
|---|---|---|---|
| Layer count | 3 (Application, Domain, Infrastructure) | 4 (Presentation, Application, Domain, Infrastructure) | 4+ concentric (Frameworks, Adapters, App, Domain) |
| Repository class | Inside `Domain/{Context}/Repository/` with `Doctrine/` subfolder for ORM variant | `Domain/Repository/` interface + `Infrastructure/Persistence/` implementation | Domain interface + Infrastructure adapter (or Port + Adapter in Hexagonal) |
| CQRS handlers | Inside `Domain/{Context}/Handler/{UseCase}/` | `Application/UseCase/` or `Application/Service/` | `Application/UseCase/` |
| Application layer scope | Entry-points only (HTTP, Console, DI, Security) | Orchestration services + DTOs | Use Cases + Ports |
| Infrastructure scope | Generic domain-agnostic clients, no business code | Persistence + integrations + framework | Generic adapters implementing Ports |
| Doctrine attributes on Domain entities | Conventional and acceptable | Not allowed (Domain plain) | Not allowed (Domain plain) |

**Defining trait:** in this style **the Domain layer owns its persistence implementations**. Repository abstraction and `Doctrine/` implementation sit side-by-side under `Domain/{Context}/Repository/`. Infrastructure stays small and reusable — generic clients (Redis, GPT, S3) that know nothing about domain types.

## Core Principles

### Layer Overview

```
┌────────────────────────────────────────────────────────────────┐
│                       APPLICATION                              │
│   Entry-points: HTTP (Action/Controller), Console, DI,         │
│   Security (Authenticator, Voter, Provider), Validator, Form,  │
│   Twig, Subscriber, Application Exception                      │
│                                                                │
│   depends on: Domain, Infrastructure                           │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          DOMAIN                                │
│   Organized into bounded contexts. Each context owns:          │
│   - Model / Entity                                             │
│   - Handler / CQRS (one folder per use case)                   │
│   - Repository (interface + `Doctrine/` impl)                  │
│   - Service, Component, DAO                                    │
│   - Enum, Event, ValueObject, Exception, Subscriber            │
│   Plus `Shared/` for cross-context VOs, enums, exceptions.     │
│                                                                │
│   depends on: Infrastructure interfaces only                   │
└────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE                            │
│   Generic, reusable, domain-agnostic clients:                  │
│   Doctrine config, MessageBus, Redis, Filesystem, GPT,         │
│   external API clients, etc.                                   │
│                                                                │
│   depends on: nothing                                          │
└────────────────────────────────────────────────────────────────┘
```

### Dependency Rule

- **Application** depends on Domain and Infrastructure (it wires everything together).
- **Domain** depends only on Infrastructure interfaces (MessageBus, Storage, etc.) — never on concrete Infrastructure code.
- **Infrastructure** depends on nothing inside the project — it's extractable as a library.

### Infrastructure Abstraction Rule

Infrastructure must never know about domain-specific logic. It provides generic capabilities ("send a message and receive decoded JSON"). Domain-specific concerns — prompts, DTO transformation, business validation — live inside the owning domain context's `Component/` or `Service/`.

## Code Conventions

- Classes without mutable state are `final readonly` by default.
- Enum cases use `camelCase` (`pending`, `confirmed`), not `PENDING`.
- Entities and Command/Query DTOs are **not** `readonly` (they carry mutable state via setters like `setResult()`).

## Bounded Context Structure

```
Domain/
├── Shared/
│   ├── Model/         # AggregateRoot
│   ├── Enum/          # Currency, Status
│   ├── ValueObject/   # Money, Email, DateRange
│   └── Exception/     # DomainException
└── Order/
    ├── Model/         # Order, OrderLine
    ├── Handler/
    │   ├── CreateOrder/
    │   │   ├── CreateOrderCommand.php
    │   │   └── CreateOrderCommandHandler.php
    │   ├── ConfirmOrder/
    │   │   ├── ConfirmOrderCommand.php
    │   │   └── ConfirmOrderCommandHandler.php
    │   └── GetOrder/
    │       ├── GetOrderQuery.php
    │       ├── GetOrderQueryHandler.php
    │       └── Result/
    │           └── OrderResult.php
    ├── Repository/
    │   ├── OrderRepositoryInterface.php
    │   └── Doctrine/
    │       └── OrderRepository.php
    ├── Service/       # Public services for cross-context use
    ├── Component/     # Private internal services (rich business logic)
    ├── DAO/           # Read-side raw data / DTO returns
    ├── Enum/          # OrderStatus
    ├── Event/         # OrderConfirmed
    ├── ValueObject/   # OrderId, Money
    ├── Exception/     # OrderNotFoundException
    └── Subscriber/    # Domain event listeners
```

## Application Layer Structure

```
Application/
├── Http/
│   ├── Actions/{Context}/       # ADR-style (one class per endpoint)
│   ├── Controllers/{Context}/   # Or classic (multiple endpoints per class)
│   ├── Request/{Context}/       # Request DTOs with validation attributes
│   └── Response/Transformer/{Context}/
├── Console/{Context}/           # CLI commands
├── DependencyInjection/
│   ├── Extension/               # Per-context Extension class
│   ├── Configuration/           # Per-context Configuration class
│   └── CompilerPass/
├── Security/
│   ├── Authenticator/
│   ├── Token/
│   ├── Authorisation/Voter/
│   └── Provider/
├── Validator/                   # Custom constraints
├── Form/
├── Twig/
├── Subscriber/                  # System event subscribers
└── Exception/                   # Application-level exceptions
```

## Skills for component patterns

Component patterns referenced in this architecture map to existing or planned skills. Generate concrete code via these skills:

### Domain Layer patterns

| Pattern | Skill |
|---------|-------|
| Entity / Aggregate root | `acc:create-entity`, `acc:create-aggregate` |
| Value Object | `acc:create-value-object` |
| Domain Service | `acc:create-domain-service` |
| Domain Event | `acc:create-domain-event` |
| Domain Exception | `acc:create-domain-exception` |
| Repository (with `Doctrine/` impl alongside) | `acc:create-repository` |
| Specification | `acc:create-specification` |
| Factory | `acc:create-factory` |
| **Component** (private internal services for rich business logic) | `acc:create-component` |
| Event Subscriber (domain event handler) | `acc:create-event-subscriber` |
| Enum | PHP native (no skill needed) |

### Application Layer patterns

| Pattern | Skill |
|---------|-------|
| CQRS Command | `acc:create-command` |
| CQRS Query | `acc:create-query` |
| CQRS Handler (under `Domain/{Context}/Handler/{UseCase}/`) | (use `acc:create-command` / `acc:create-query` together) |
| HTTP Action (ADR) | `acc:create-action` |
| HTTP Responder (ADR) | `acc:create-responder` |
| Request DTO | `acc:create-dto` |
| Response Transformer | `acc:create-response-transformer` |
| Console Command | `acc:create-console-command` |
| Application Exception | see `references/application-exception.md` (Layered-specific naming + placement; pattern stays in this skill since "Application layer" is Layered-specific terminology) |
| Validator Constraint | (Symfony-specific; see `acc:symfony-knowledge` references) |
| Security Authenticator / Voter / Provider | (Symfony-specific; see `acc:symfony-knowledge` references) |
| DI Extension / Configuration / CompilerPass | (Symfony-specific; see `acc:symfony-knowledge` references) |

### Infrastructure Layer patterns

| Pattern | Skill |
|---------|-------|
| Generic infrastructure client | `acc:create-infrastructure-client` |
| Doctrine custom type | see `references/doctrine-type.md` (Doctrine-specific) |
| Message bus | `acc:create-psr14-event-dispatcher`, `acc:cqrs-knowledge` references/bus-patterns |
| Cache | `acc:create-psr6-cache`, `acc:create-psr16-simple-cache` |
| HTTP client | `acc:create-psr18-http-client` |

## Adding New Features — Checklists

### New API Endpoint

1. Create Request DTO via `acc:create-dto` (place under `Application/Http/Request/{Context}/`)
2. Create Action via `acc:create-action` (place under `Application/Http/Actions/{Context}/` with `#[Route]`)
3. Create CQRS Command via `acc:create-command` (place under `Domain/{Context}/Handler/{UseCaseName}/`)
4. Create CommandHandler — same folder as Command, with `#[AsMessageHandler]`
5. Create Response Transformer (place under `Application/Http/Response/Transformer/{Context}/`)
6. Check if endpoint requires authorization — add Voter or role check if needed
7. Check if `security.yaml` access control rules need updating for the new route
8. No manual route registration needed (auto-discovery via attributes)

### New Domain Entity

1. Generate entity via `acc:create-entity` (place under `Domain/{Context}/Model/`)
2. Generate Repository via `acc:create-repository` (interface under `Domain/{Context}/Repository/`, Doctrine impl under `Domain/{Context}/Repository/Doctrine/`)
3. Create migration: `php bin/console doctrine:migrations:diff`
4. Apply migration: `php bin/console doctrine:migrations:migrate`

### New Bounded Context

1. Create domain module under `Domain/{Context}/` with `Model/`, `Handler/`, `Repository/` folders
2. Create `{Context}Configuration` class (Symfony Config)
3. Create `{Context}Extension` class (Symfony DI Extension)
4. Register both in root orchestrator classes
5. Create service config YAML in `config/services/{context}.yaml`
6. Register the new YAML in the root services configuration
7. Create Actions, Requests, Transformers in Application layer as needed

### New Infrastructure Integration

1. Create module folder in `Infrastructure/{Module}/`
2. Implement the integration with generic, domain-agnostic interface
3. Wire services via DependencyInjection
4. Domain-specific usage (prompts, DTO mapping, business rules) goes into the owning domain `Component/` or `Service/`

## Common Violations Quick Reference

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Domain importing concrete Infrastructure class | `Domain/**/*.php` `use Infrastructure\\...` of concretes | Critical |
| Repository impl outside Domain (in Infrastructure) | `Infrastructure/**/*Repository.php` referencing Domain entities | Critical |
| Business logic in Application Action/Controller | `if`/`switch` on domain state in `Application/Http/Actions/` | Warning |
| Domain-specific code in Infrastructure | Prompts, DTO mapping, validation in `Infrastructure/` | Warning |
| Handler outside `Handler/{UseCase}/` folder | `Domain/**/Handler/*Handler.php` not nested in UseCase folder | Warning |
| Shared kernel pollution | `Domain/Shared/` containing context-specific entities | Warning |
| Component exposed across contexts | `use {OtherContext}\Component\` outside the owning context | Warning |
