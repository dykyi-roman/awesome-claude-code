# DDD Across Architectures

DDD identifies a set of conceptual responsibilities — modeling the business, orchestrating use cases, providing technical capabilities, accepting input from the outside world. Different architectural styles arrange these responsibilities into different numbers of physical layers, with different folder structures and different dependency rules.

This reference describes the responsibilities themselves, then how each supported architecture arranges them. Use the per-architecture placement table to audit prose to the project's actual style — don't assert one layout as universal DDD.

## DDD's conceptual responsibilities

| Responsibility | Contents | Examples |
|---|---|---|
| **Domain model** | Entities, Value Objects, Aggregates, Domain Services, Domain Events, the Repository pattern, Specifications, Factories | `Order`, `OrderId`, `Money`, `OrderConfirmed`, `OrderRepository` |
| **Orchestration** (use cases) | Use Cases, Application Services, Command/Query Handlers, DTOs, Event Handlers, Ports for external services | `CreateOrderUseCase`, `OrderResult`, `PaymentGatewayInterface` |
| **Technical capabilities** | Persistence adapters, external API clients, message brokers, caches, queues, event dispatchers, framework integrations | `DoctrineOrderRepository`, `StripePaymentGateway`, `RedisCache` |
| **Entry-points** | HTTP controllers/actions, CLI commands, message consumers, request/response objects | `OrderController`, `OrderAction`, `ImportOrdersCommand` |

These are conceptual buckets, not necessarily four separate folders. How they map to physical layers depends on the chosen architecture.

## Per-architecture placement

| Architecture | Skill | Physical layout | Where entry-points live | Where Repository impls live |
|---|---|---|---|---|
| **Clean Architecture** | `acc:clean-arch-knowledge` | `Domain/`, `Application/`, `Infrastructure/`, `Presentation/` (4 folders) | `Presentation/` | `Infrastructure/` |
| **Hexagonal (Ports & Adapters)** | `acc:hexagonal-knowledge` | `Domain/`, `Application/`, `Infrastructure/` (3 folders) | `Infrastructure/Http/`, `Infrastructure/Console/`, `Infrastructure/Messaging/` (Driving Adapters) | `Infrastructure/Persistence/` (Driven Adapters) |
| **Layered (3-tier Domain-centric)** | `acc:layer-arch-knowledge` | `Application/`, `Domain/`, `Infrastructure/` (3 folders) | Inside `Application/Http/`, `Application/Console/`, `Application/Subscriber/` (no separate Presentation layer) | Inside `Domain/{Context}/Repository/Doctrine/` (Domain owns persistence) |
| **N-Tier (4-tier Classical)** | `acc:n-tier-arch-knowledge` | `Presentation/`, `Application/`, `Domain/`, `Infrastructure/` (4 folders) | `Presentation/` | `Infrastructure/Persistence/` |
| **Package-by-Feature** | wraps any of the above | `{Feature}/` outermost, the chosen inner architecture applied inside | per inner architecture, scoped to `{Feature}/` | per inner architecture, scoped to `{Feature}/` |
| **MVC** | — | `Model/`, `View/`, `Controller/` (3 folders) | `Controller/` | inside `Model/` (or a separate persistence folder if added) |

## Dependency direction varies by architecture

There is no universal "inward dependency" rule in DDD. The inward rule is **Clean Architecture's** rule; each architecture has its own direction:

- **Clean:** outer rings depend on inner rings. Application does NOT depend on Infrastructure (DIP via Ports).
- **Hexagonal:** Application Core (Domain + Application) defines Ports. Adapters implement Ports — Adapters depend on Ports, not the other way around.
- **Layered (3-tier Domain-centric):** Application → Domain + Infrastructure. Domain → Infrastructure interfaces. Domain owns its Repository implementations.
- **N-Tier (4-tier Classical):** strict downward calls — each layer talks to the layer directly below. Application CAN depend on Infrastructure.
- **PBF:** the inner architecture's direction, scoped per feature.
- **MVC:** Controller → Model + View; View → Model; Model → nothing UI-related.

When auditing dependency violations, match prose to the project's chosen architecture.

---

## Domain model

### Contents

- **Entities** — objects with identity and lifecycle
- **Value Objects** — immutable, defined by attributes; equality by value
- **Aggregates** — clusters of entities with a root that enforces invariants
- **Domain Services** — stateless operations spanning multiple aggregates
- **The Repository pattern** — collection-like access to aggregates (a domain pattern; the abstraction always exists, but its folder placement varies by architecture)
- **Domain Events** — notifications of business state changes
- **Specifications** — business rules as objects
- **Factories** — complex object construction

### Rules

| Rule | Applies in | Notes |
|---|---|---|
| Entities have behavior, not just getters/setters | Universal | Anemic Domain Model is a smell everywhere |
| Aggregate root enforces invariants | Universal | Foundational DDD principle |
| Ubiquitous language in method names | Universal | `confirm()` not `setStatus()` |
| Value Objects for domain concepts | Universal | `Email`, `Money`, `OrderId` instead of primitives |
| No framework imports in Domain code | **Clean, Hexagonal** — architectural rule (Domain cannot depend on outer rings) | In **Layered 3-tier** and **N-Tier**, the architecture does not forbid framework imports in Domain; whether to use Doctrine attributes on entities vs. XML/YAML mapping vs. a separate mapping class is a **project choice**, not a convention |
| Repository as an abstraction (interface or abstract class) | Universal | The pattern is a domain concept |
| Repository concrete class in a particular folder | **Architecture-specific** | Clean / Hexagonal / N-Tier: in Infrastructure. Layered 3-tier: inside Domain. Don't enforce a single placement. |
| Save-side mutation in Repository (`save()` doing validation / calculation) | Universal smell | Query-side business intent (`findShippableOrdersForToday()`) is correct content |

### Detection patterns

Use class-name suffix matching first — it works across architectures:

```bash
# Entities — any architecture
Glob: **/*Entity.php
Glob: **/Entity/**/*.php

# Repository (abstraction OR concrete; suffix-based works everywhere)
Glob: **/*Repository.php
Glob: **/*RepositoryInterface.php

# Value Objects
Glob: **/*ValueObject.php
Glob: **/ValueObject/**/*.php

# Aggregates
Glob: **/*Aggregate.php
Glob: **/*AggregateRoot.php

# Domain Services (suffix-based; filter by context if needed)
Glob: **/*DomainService.php
```

Architecture-specific dependency-direction checks:

```bash
# CLEAN / N-TIER only: Domain importing Infrastructure
# (In Layered 3-tier this can be legitimate — Domain owns persistence)
Grep: "use.+\\\\Infrastructure\\\\" --glob "**/Domain/**/*.php"

# CLEAN / HEXAGONAL: framework imports in Domain (architectural rule)
# (In Layered 3-tier / N-Tier / MVC this is a project-choice question,
#  not an architecture rule — only flag if the project's own coding
#  standard forbids it.)
Grep: "use Doctrine|use Illuminate|use Symfony" --glob "**/Domain/**/*.php"

# CLEAN: Application importing Infrastructure (DIP violation)
# (In N-Tier this is allowed)
Grep: "use.+\\\\Infrastructure\\\\" --glob "**/Application/**/*.php"
```

---

## Orchestration (use cases)

### Contents

- Use Cases / Command Handlers — single-operation orchestration
- Query Handlers — read-side operations
- Application Services — multi-step coordination
- DTOs — input/output data structures
- Event Handlers — application-level reactions to domain events
- Ports — interfaces for external services (explicit in Hexagonal; implicit DIP elsewhere)

### Rules

| Rule | Applies in | Notes |
|---|---|---|
| No business logic — delegate to Domain | Universal | If/switch over entity state belongs in the entity |
| Transaction boundaries here | Universal | Use Case decides commit/rollback |
| Returns DTOs, not entities | Universal | Or returns nothing if write-only |
| Cannot use HTTP/CLI types | **Clean, Hexagonal, N-Tier** (typical) | In **Layered 3-tier**, the Application layer hosts entry-points (`Application/Http/`...) so HTTP types appear in the layer — but inside Action files, not Use Case files |
| Cannot reach into Infrastructure | **Clean** | Application defines Ports; Infrastructure implements them |
| May call Infrastructure directly | **N-Tier**, **Layered 3-tier** | These architectures allow Application → Infrastructure interfaces |

### Detection patterns

```bash
# Use Cases / Handlers (class-name suffix)
Glob: **/*UseCase.php
Glob: **/*Handler.php
Glob: **/UseCase/**/*.php
Glob: **/Handler/**/*.php

# Application Services
Glob: **/Application/**/*Service.php

# Ports (explicit Hexagonal naming; also used in Clean for DIP)
Glob: **/Port/**/*.php
Glob: **/Port/Input/**/*.php
Glob: **/Port/Output/**/*.php

# Anti-pattern: business logic in Use Case (if/switch on entity state)
Grep: "if \(.*->get.*Status|switch \(.*->get" --glob "**/UseCase/**/*.php"
```

---

## Technical capabilities (Infrastructure)

### Contents

These are architecture-agnostic — always Infrastructure-shaped:
- External service adapters / API clients
- Cache, queue, message-broker clients
- Event dispatchers
- ORM connection / configuration
- Framework integrations

This is architecture-specific:
- **Repository implementations** — In **Clean / Hexagonal / N-Tier**, they live in Infrastructure. In **Layered 3-tier**, they live inside Domain alongside the abstraction. In **MVC**, they're usually folded into the Model.

### Rules

| Rule | Applies in | Notes |
|---|---|---|
| No business logic — only technical translation | Universal | If/switch on domain state belongs in Domain |
| Implements an abstraction defined by the layer above | Universal | The abstraction lives where the consumer is |
| Domain types in signatures only, not framework types | **Clean, Hexagonal, N-Tier** | In Layered 3-tier, Repository impls inside Domain naturally use Doctrine types — that's the trade-off |

### Detection patterns

```bash
# External-service adapters (suffix-based)
Glob: **/*Gateway.php
Glob: **/*Adapter.php
Glob: **/*Client.php

# Repository concrete classes (works across architectures)
Glob: **/Doctrine/*Repository.php
Glob: **/Persistence/**/*Repository.php
Glob: **/Infrastructure/**/*Repository.php

# Anti-pattern: business logic in a Repository class
Grep: "private function calculate|private function validate" --glob "**/*Repository.php"
```

---

## Entry-points

### Contents

- HTTP controllers, Actions, Responders
- CLI commands / console handlers
- Message consumers
- Request / response objects
- View models, templates
- Middleware

### Per-architecture placement

| Architecture | Folder |
|---|---|
| Clean | `Presentation/` |
| Hexagonal | `Infrastructure/{Http,Console,Messaging}/` (Driving Adapters) |
| **Layered (3-tier Domain-centric)** | **Inside Application/ — `Application/Http/`, `Application/Console/`, `Application/Subscriber/`. No separate Presentation layer.** |
| N-Tier | `Presentation/` |
| PBF | per inner architecture, inside `{Feature}/` |
| MVC | `Controller/` |

### Rules

| Rule | Applies in | Notes |
|---|---|---|
| Validates input format | Universal | Not business rules — just shape |
| Maps requests to Commands/Queries/DTOs | Universal | Don't construct domain objects directly |
| No business logic | Universal | Delegate to Use Cases or Domain |
| Lives in a dedicated top-level folder | **Clean, Hexagonal, N-Tier** | Layered 3-tier merges into Application |

### Detection patterns

```bash
# HTTP entry-points (suffix-based — works regardless of folder)
Glob: **/*Controller.php
Glob: **/*Action.php
Glob: **/*Responder.php

# CLI commands
Glob: **/Console/**/*Command.php

# Anti-pattern: business logic in a controller
Grep: "if \(.*->can|if \(.*->is[A-Z]|if \(.*->has[A-Z]" --glob "**/*Controller.php" --glob "**/*Action.php"
```

---

## Bounded contexts

Bounded contexts are a DDD concept independent of architecture. They partition the model by business capability so the same word ("Customer" in Sales vs. Support) can mean different things in different parts of the system.

### Within a single context

Components reference each other following the architecture's own dependency rules. The domain model is shared directly.

### Across contexts

Cross-context calls must go through a stable channel:

| Channel | When | Notes |
|---|---|---|
| **Domain Events** | Preferred | One context publishes; the other subscribes. Async, loose coupling. |
| **Anti-Corruption Layer** | When sync coordination is needed | One context exposes a stable interface; the consumer writes an adapter translating between the two domain models. |
| **Shared Kernel** | For truly cross-cutting primitives (`Money`, `Email`, `Clock`) | Resist pulling context-specific types in here. |

Direct imports of one context's internal domain types from another context are a violation regardless of architecture.

```
Context A                    Context B
┌──────────┐                ┌──────────┐
│  Domain  │                │  Domain  │
│    +     │                │    +     │
│ Orchestr.│ ──── Event ───→│ Orchestr.│
└──────────┘                └──────────┘
                  OR
              ACL adapter implementing
              a stable Port published by A
```

### Detection

```bash
# Cross-context imports (replace Order/Payment with actual context names)
Grep: "use.+\\\\Payment\\\\" --glob "**/Order/**/*.php"
Grep: "use.+\\\\Order\\\\" --glob "**/Payment/**/*.php"

# Shared Kernel scope creep — anything context-specific landing in Shared/
Glob: **/Shared/**/Order*.php
Glob: **/Shared/**/Payment*.php
```

---

## Auditing checklist — adapting to the project's architecture

1. **Identify the architecture first.** Read `composer.json` `autoload.psr-4` paths or scan top-level `src/` folders against the placement table above. If unsure, ask before auditing.

2. **Pick the right rule set.** Use the architecture's column in the per-rule tables above. Don't assert Clean Arch rules in a Layered 3-tier audit.

3. **Use suffix-based detection patterns by default.** `**/*Entity.php` works everywhere; `**/Domain/**/*.php` only works in 4-folder layouts.

4. **Repository placement.** Don't flag Domain-internal Repository implementations as violations if the project is Layered 3-tier; don't flag Infrastructure Repository implementations if the project is Clean / Hexagonal / N-Tier. The pattern is universal; the placement is architectural.

5. **Bounded contexts.** Apply context-isolation checks regardless of architecture — direct cross-context imports are always violations.
