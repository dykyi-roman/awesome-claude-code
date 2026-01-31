# Layer Architecture Rules

Detailed rules for DDD layer separation and boundaries.

## The Dependency Rule

```
┌─────────────────────────────────────────────────────────┐
│                    Presentation                          │
│  (Controllers, Actions, CLI Commands, Views)            │
├─────────────────────────────────────────────────────────┤
│                    Application                           │
│  (Use Cases, Application Services, DTOs)                │
├─────────────────────────────────────────────────────────┤
│                      Domain                              │
│  (Entities, Value Objects, Domain Services, Events)     │
├─────────────────────────────────────────────────────────┤
│                   Infrastructure                         │
│  (Repositories, External Services, DB, Cache, Queue)    │
└─────────────────────────────────────────────────────────┘

Dependencies flow INWARD → Domain is the center
```

## Domain Layer

### Purpose
Contains business logic and rules that are independent of any technical concerns.

### Contents
- **Entities** — Objects with identity and lifecycle
- **Value Objects** — Immutable objects defined by their attributes
- **Aggregates** — Clusters of entities with a root
- **Domain Services** — Stateless operations on domain objects
- **Repository Interfaces** — Contracts for persistence
- **Domain Events** — Notifications of domain state changes
- **Specifications** — Business rules as objects
- **Factories** — Complex object creation

### Rules

| Rule | Violation Example | Correct Approach |
|------|-------------------|------------------|
| No framework dependencies | `use Doctrine\ORM\Mapping as ORM` | Use plain PHP classes |
| No infrastructure imports | `use App\Infrastructure\...` | Define interfaces in Domain |
| No HTTP concerns | `use Symfony\Component\HttpFoundation\Request` | Use DTOs from Application |
| No persistence concerns | `$this->entityManager->persist()` | Use Repository interface |

### Allowed Dependencies
- PHP built-in classes only
- Other Domain classes within the same bounded context
- Shared Kernel (common Value Objects across contexts)

### Detection Patterns

```bash
# Critical violations - Domain importing Infrastructure
Grep: "use.*Infrastructure" --glob "**/Domain/**/*.php"

# Critical violations - Framework in Domain
Grep: "use Doctrine\\\\|use Illuminate\\\\|use Symfony\\\\" --glob "**/Domain/**/*.php"

# Warning - Potential persistence leakage
Grep: "@ORM\\\\|@Entity|@Column" --glob "**/Domain/**/*.php"
```

## Application Layer

### Purpose
Orchestrates domain objects to perform use cases. Thin layer that coordinates but doesn't contain business logic.

### Contents
- **Use Cases / Command Handlers** — Single operation orchestration
- **Query Handlers** — Read-side operations (CQRS)
- **Application Services** — Multi-step coordination
- **DTOs** — Data transfer between layers
- **Ports** — Interfaces for external services

### Rules

| Rule | Violation Example | Correct Approach |
|------|-------------------|------------------|
| No business logic | `if ($order->getStatus() === 'pending')` | Move decision to Domain |
| No direct DB access | `$this->connection->query()` | Use Repository |
| No HTTP concerns | `return new JsonResponse()` | Return DTO |
| Orchestrate only | Complex if/else chains | Delegate to Domain |

### Allowed Dependencies
- Domain layer
- Other Application layer classes
- Framework's transaction management (via abstraction)

### Detection Patterns

```bash
# Warning - Business logic in Application
Grep: "if \(.*->get.*Status|switch \(.*->get" --glob "**/Application/**/*.php"

# Warning - HTTP concerns in Application
Grep: "use.*HttpFoundation|use.*Response" --glob "**/Application/**/*.php"

# Check - UseCase structure
Glob: **/Application/**/*UseCase.php
Glob: **/Application/**/*Handler.php
```

## Infrastructure Layer

### Purpose
Implements technical concerns: persistence, external services, caching, messaging.

### Contents
- **Repository Implementations** — Persistence logic
- **External Service Adapters** — API clients
- **ORM Mappings** — Doctrine/Eloquent configurations
- **Cache Implementations** — Redis, Memcached adapters
- **Queue Implementations** — RabbitMQ, SQS adapters
- **Event Dispatchers** — Event publishing implementations

### Rules

| Rule | Violation Example | Correct Approach |
|------|-------------------|------------------|
| No business logic | `if ($this->isVipCustomer($order))` | Move to Domain |
| Implement interfaces | `class OrderRepository { }` | `implements OrderRepositoryInterface` |
| Technical mapping only | Calculate discounts in repo | Just map data |

### Allowed Dependencies
- Domain layer (implements interfaces)
- Application layer
- Frameworks, libraries, external services

### Detection Patterns

```bash
# Check - Repository implements interface
Grep: "implements.*Repository" --glob "**/Infrastructure/**/*.php"

# Warning - Business logic in Infrastructure
Grep: "private function calculate|private function validate|private function check" --glob "**/Infrastructure/**/*.php"
```

## Presentation Layer

### Purpose
Handles all input/output concerns: HTTP, CLI, WebSocket, etc.

### Contents
- **Controllers / Actions** — HTTP endpoint handlers
- **Request Objects** — Input validation
- **Response Objects** — Output formatting
- **CLI Commands** — Console handlers
- **View Models** — Data for templates
- **Middleware** — Cross-cutting concerns

### Rules

| Rule | Violation Example | Correct Approach |
|------|-------------------|------------------|
| No business logic | `if ($user->canAccess($resource))` | Call UseCase, check result |
| Validate input only | Check business rules | Delegate to Application/Domain |
| Transform data | Construct domain objects | Map Request → DTO |

### Allowed Dependencies
- Application layer
- Framework HTTP/CLI components
- Serialization libraries

### Detection Patterns

```bash
# Warning - Business logic in Presentation
Grep: "if \(.*->can|if \(.*->is[A-Z]|if \(.*->has[A-Z]" --glob "**/Presentation/**/*.php" --glob "**/Controller/**/*.php"

# Check - Controller complexity (should be simple)
Grep: "private function|protected function" --glob "**/Controller/**/*.php"
```

## Cross-Layer Communication

### Request Flow

```
HTTP Request
    ↓
Presentation (validate, map to DTO)
    ↓
Application (orchestrate use case)
    ↓
Domain (business logic, state changes)
    ↓
Infrastructure (persist, notify)
    ↓
Application (return result DTO)
    ↓
Presentation (format response)
    ↓
HTTP Response
```

### Data Objects

| Layer | Input | Output |
|-------|-------|--------|
| Presentation | Request Object | Response/View |
| Application | Command/Query DTO | Result DTO |
| Domain | Value Objects, Entities | Domain Events |
| Infrastructure | Domain Objects | Mapped Data |

## Bounded Context Boundaries

### Within Same Context
- Layers can reference each other following dependency rules
- Share domain model directly

### Between Contexts
- Communicate via Application layer
- Use Anti-Corruption Layer for translation
- Prefer async events over direct calls

```
Context A                    Context B
┌──────────┐                ┌──────────┐
│ Domain A │                │ Domain B │
└────┬─────┘                └────┬─────┘
     │                           │
┌────┴─────┐                ┌────┴─────┐
│   App A  │ ──── Event ───→│   App B  │
└──────────┘                └──────────┘
```