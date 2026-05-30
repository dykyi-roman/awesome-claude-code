---
name: ddd-knowledge
description: DDD knowledge base. Provides patterns, antipatterns, and PHP-specific guidelines for Domain-Driven Design audits.
---

# DDD Knowledge Base

Quick reference for Domain-Driven Design. DDD is a methodology for modeling complex domains, centered on ubiquitous language and bounded contexts. It is not an architecture — its patterns apply across the architectural styles the plugin supports (Clean Architecture, Hexagonal, Layered 3-tier (Domain-centric), N-Tier 4-tier (Classical), Package-by-Feature, MVC). See [`references/layer-architecture.md`](references/layer-architecture.md) for the per-architecture placement table.

## Core Ideas

DDD rests on a small set of central ideas. Get these right before worrying about folders.

### Ubiquitous Language

A shared vocabulary between developers and domain experts, used in conversations, documentation, and code. If the business says "confirm an order", the method is `confirm()` — not `setStatus()`, `process()`, or `updateOrderState()`. Drift between business language and code language is a signal the model is decaying.

### Bounded Contexts

An explicit boundary inside which a model has one consistent meaning. "Customer" in Sales and "Customer" in Support may be the same word but different models, with different invariants and lifecycles. Bounded contexts make those differences explicit instead of forcing one bloated model.

### Aggregate Consistency

An aggregate is a cluster of objects treated as a unit for data changes. The aggregate root enforces the invariants. Changes inside the aggregate are transactional and immediate; references between aggregates are by identity, and consistency between aggregates is eventual.

### Conceptual Isolation of the Domain

The domain model — entities, value objects, aggregates, domain services, domain events — is the heart of the software. It should be possible to reason about it without simultaneously reasoning about HTTP, ORM internals, or message brokers. Domain code expresses business meaning; other code handles technical concerns. How strictly this isolation is enforced (e.g. whether framework imports are forbidden inside Domain) is **architecture-dependent**: Clean Architecture and Hexagonal forbid it by rule; Layered 3-tier, N-Tier, and MVC leave it as a project choice.

## DDD's conceptual responsibilities

DDD's canonical vocabulary names four responsibilities. These are conceptual buckets — how they map to physical folders depends entirely on the chosen architecture. **DDD does not prescribe a folder layout.**

| Responsibility | Contains | Purpose |
|---|---|---|
| **Entry-points** | Controllers, Actions, CLI commands, message consumers, view models | Translate input from the outside world into orchestration calls; format output |
| **Orchestration** | Use Cases, Application Services, Command/Query Handlers, DTOs, Ports | Coordinate the domain to do work; manage transactions; dispatch events |
| **Domain model** | Entities, Value Objects, Aggregates, Domain Services, Repositories (the pattern), Domain Events, Specifications, Factories | Express the business model and its invariants |
| **Technical capabilities** | External-service adapters, framework integrations, message brokers, caches, queues, DB clients | Provide generic technical capabilities |

> **Folder placement is architectural, not DDD-prescribed.** The placement of every responsibility — including Repository concrete classes — varies by architecture. See [`references/layer-architecture.md`](references/layer-architecture.md) for the full per-architecture table.

How each supported architecture maps these responsibilities to folders:

| Architecture | Knowledge skill | Physical shape |
|---|---|---|
| **Clean Architecture** | `acc:clean-arch-knowledge` | 4 folders: `Domain/`, `Application/`, `Infrastructure/`, `Presentation/`. INWARD dependency rule. Application does NOT depend on Infrastructure (DIP via Ports). |
| **Hexagonal (Ports & Adapters)** | `acc:hexagonal-knowledge` | 3 folders: `Domain/`, `Application/`, `Infrastructure/`. Driving Ports under `Application/{Context}/Port/Input/`; Driven Ports under `Domain/{Context}/Port/Output/`; Adapters in `Infrastructure/`. |
| **Layered (3-tier Domain-centric)** | `acc:layer-arch-knowledge` | 3 folders: `Application/`, `Domain/`, `Infrastructure/`. Entry-points live INSIDE `Application/Http/`, `Application/Console/`, etc. (no separate Presentation layer). Domain owns its Repository implementations under `Domain/{Context}/Repository/Doctrine/`. |
| **N-Tier (4-tier Classical)** | `acc:n-tier-arch-knowledge` | 4 folders: `Presentation/`, `Application/`, `Domain/`, `Infrastructure/`. Strict downward calls — Presentation can only call Application; Application can call Domain or Infrastructure. |
| **Package-by-Feature** | wraps any of the above | `{Feature}/` outermost; the chosen inner architecture is applied INSIDE each feature folder. |
| **MVC** | — | 3 folders: `Model/`, `View/`, `Controller/`. DDD's domain model lives in `Model/`; orchestration may not exist as a distinct layer. |

When auditing, identify the architecture first, then apply the rules of that specific architecture. Don't assert one architecture's rules across all of them.

## Quick Checklists

These checklists are organized by **responsibility**, not by physical layer — the responsibility names map onto different folder structures in different architectures. Some architectures merge responsibilities (e.g. Layered 3-tier merges entry-points into Application; MVC may have no distinct Orchestration layer at all) — apply the merged checklists to the merged folder.

### Domain model

- [ ] Entities have behavior and intent-revealing methods, not just getters/setters
- [ ] Value Objects for domain concepts (`Email`, `Money`, `OrderId`)
- [ ] Aggregates enforce their invariants through the root
- [ ] Aggregates reference other aggregates by ID only
- [ ] The Repository pattern is used for aggregate access (the abstraction exists; placement of the concrete class varies by architecture)
- [ ] Enums or value objects instead of magic strings
- [ ] Domain Events for things that happened in the business
- [ ] No `public function set*()` for state changes — use intent-revealing methods
- [ ] Framework-isolation in Domain code: **Clean Architecture / Hexagonal — required by the architecture**; **Layered 3-tier / N-Tier / MVC — project choice (check the project's coding standard)**

### Orchestration (Use Cases / Application Services / Handlers)

- [ ] Use Cases orchestrate; they don't decide (business decisions go to the entity / domain service)
- [ ] DTOs / Commands / Queries for input and output
- [ ] No domain decisions in `if`/`switch` over entity state
- [ ] Transaction boundaries here
- [ ] HTTP/CLI concerns kept out: **Clean / Hexagonal / N-Tier** — must live in a separate layer. **Layered 3-tier** — HTTP/Console entry-points live INSIDE the Application layer (`Application/Http/`, `Application/Console/`), but inside their own files (`OrderAction.php`), separate from Use Case files (`CreateOrderHandler.php`). **MVC** — orchestration is usually inside the Controller.

### Technical capabilities (Infrastructure / persistence adapters / external clients)

- [ ] External-service adapters, caches, queues, dispatchers, framework integrations are isolated from Domain
- [ ] No business decisions in Repository `save()` — only persistence
- [ ] Repository queries CAN encode business intent (`findShippableOrdersForToday()`) — that's not a violation
- [ ] Repository concrete class placement: **Clean / Hexagonal / N-Tier — in Infrastructure**; **Layered 3-tier — inside Domain alongside the abstraction under `Domain/{Context}/Repository/Doctrine/`**

### Entry-points (Controllers / Actions / CLI commands / consumers)

- [ ] Validates input format only (business rules belong in Domain)
- [ ] Maps requests to Commands/Queries/DTOs
- [ ] Calls orchestration code (Use Case / Handler / Application Service)
- [ ] Formats responses
- [ ] No business logic
- [ ] Physical placement: **Clean / N-Tier — dedicated `Presentation/` folder**; **Hexagonal — `Infrastructure/Http/`, `Infrastructure/Console/` (Driving Adapters)**; **Layered 3-tier — `Application/Http/`, `Application/Console/`**; **PBF — per inner architecture, scoped to `{Feature}/`**; **MVC — `Controller/`**

## Common Violations Quick Reference

Detection globs use suffix-based matching since folder layout varies by architecture.

| Violation | Where to Look | Severity |
|-----------|---------------|----------|
| Anemic entity (only get/set, no behavior) | `**/*Entity.php`, `**/Entity/**/*.php` | Warning |
| Primitive obsession (`string $email`, `string $status`) | `**/*Entity.php`, `**/Entity/**/*.php` | Warning |
| Public setters bypassing invariants | `**/*Entity.php` | Warning |
| Magic strings instead of enums/VOs | Any PHP file | Warning |
| Save-side mutation in Repository (`save()` calculating/validating) | `**/*Repository.php` | Warning |
| Aggregate boundary leakage (child mutated from outside root) | aggregate files | Warning |
| Domain Service holding state | `**/*Service.php` in domain code | Warning |
| Ubiquitous language drift (technical names instead of business language) | All domain code | Warning |
| Business logic in Controller | `**/*Controller.php`, `**/*Action.php` | Warning |
| Framework imports in Domain (architectural rule — check architecture before flagging) | `**/*Entity.php`, `**/Entity/**/*.php` | Critical in Clean / Hexagonal (architectural rule); project-choice in Layered 3-tier / N-Tier / MVC |

## PHP 8.4 DDD Patterns

### Value Object

```php
<?php

declare(strict_types=1);

namespace ValueObject;

final readonly class Email
{
    public function __construct(
        public string $value,
    ) {
        if (!filter_var($value, FILTER_VALIDATE_EMAIL)) {
            throw new InvalidArgumentException('Invalid email');
        }
    }

    public function equals(self $other): bool
    {
        return $this->value === $other->value;
    }
}
```

### Entity with Behavior

```php
<?php

declare(strict_types=1);

namespace Entity;

final class Order
{
    private OrderStatus $status;

    public function __construct(
        private readonly OrderId $id,
        private readonly CustomerId $customerId,
    ) {
        $this->status = OrderStatus::Pending;
    }

    public function confirm(): void
    {
        if (!$this->status->canTransitionTo(OrderStatus::Confirmed)) {
            throw new DomainException('Cannot confirm order');
        }
        $this->status = OrderStatus::Confirmed;
    }
}
```

### Repository

A Repository represents a collection of aggregates and encapsulates retrieval logic. The Repository is a single domain pattern (DDD does not divide it into interface vs implementation — that split is a Clean Architecture convention). Query-side business intent on a Repository is correct DDD; `save()`-side business logic (calculation, validation, state changes) is not.

```php
<?php

declare(strict_types=1);

namespace Repository;

use Doctrine\ORM\EntityManagerInterface;

final readonly class OrderRepository
{
    public function __construct(
        private EntityManagerInterface $em,
    ) {}

    public function findById(OrderId $id): ?Order
    {
        return $this->em->find(Order::class, $id);
    }

    public function save(Order $order): void
    {
        $this->em->persist($order);
        $this->em->flush();
    }

    /**
     * Query-side business intent — finding what the domain calls
     * "shippable today" — is correct Repository content.
     *
     * @return list<Order>
     */
    public function findShippableOrdersForToday(): array
    {
        // domain-meaningful query
    }
}
```

Folder placement of the Repository class is an architectural choice and is not prescribed by DDD.

## References

For detailed information, load these reference files:

- `references/layer-architecture.md` — DDD's conceptual responsibilities and how each supported architecture arranges them physically (the per-architecture placement table)
- `references/domain-patterns.md` — Entity, VO, Aggregate, Repository patterns + per-architecture Repository placement
- `references/application-patterns.md` — Use Case, DTO, Command/Query, Port patterns
- `references/antipatterns.md` — DDD antipatterns with per-architecture qualifiers
- `references/php-specific.md` — PHP 8.4 specific implementations
- `references/generation-examples.md` — example commands and the files they produce (uses `{architecture-path}` placeholders)

## Assets

- `assets/report-template.md` — Structured audit report template
