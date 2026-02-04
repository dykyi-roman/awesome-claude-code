# Skills

Knowledge bases and code generators. Skills provide domain expertise and code generation templates for agents.

## Skill Types

| Type | Count | Purpose | Example |
|------|-------|---------|---------|
| **Knowledge** | 21 | Provide expertise and best practices | `acc-ddd-knowledge` |
| **Analyzer** | 46 | Detect violations and antipatterns | `acc-analyze-solid-violations` |
| **Generator** | 48 | Generate PHP code with tests | `acc-create-entity` |
| **Template** | 9 | Documentation templates | `acc-readme-template` |
| **Other** | 3 | Estimation and suggestions | `acc-estimate-complexity` |

## How Skills Work

1. **Loading**: Skills are loaded by agents via `skills:` frontmatter
2. **Activation**: Triggered by keywords in user request or agent decision
3. **Execution**: Skill provides templates, rules, or generates code
4. **Output**: Generated code follows PHP 8.5, DDD, and PSR standards

---

## Knowledge Skills

Knowledge bases for architecture audits and best practices.

| Skill | Path | Description |
|-------|------|-------------|
| `acc-claude-code-knowledge` | `skills/acc-claude-code-knowledge/` | Claude Code formats and patterns |
| `acc-ddd-knowledge` | `skills/acc-ddd-knowledge/` | DDD patterns, antipatterns |
| `acc-cqrs-knowledge` | `skills/acc-cqrs-knowledge/` | CQRS command/query patterns |
| `acc-clean-arch-knowledge` | `skills/acc-clean-arch-knowledge/` | Clean Architecture patterns |
| `acc-hexagonal-knowledge` | `skills/acc-hexagonal-knowledge/` | Hexagonal/Ports & Adapters |
| `acc-layer-arch-knowledge` | `skills/acc-layer-arch-knowledge/` | Layered Architecture patterns |
| `acc-event-sourcing-knowledge` | `skills/acc-event-sourcing-knowledge/` | Event Sourcing patterns |
| `acc-eda-knowledge` | `skills/acc-eda-knowledge/` | Event-Driven Architecture |
| `acc-outbox-pattern-knowledge` | `skills/acc-outbox-pattern-knowledge/` | Transactional Outbox pattern |
| `acc-saga-pattern-knowledge` | `skills/acc-saga-pattern-knowledge/` | Saga/distributed transactions |
| `acc-stability-patterns-knowledge` | `skills/acc-stability-patterns-knowledge/` | Circuit Breaker, Retry, Rate Limiter, Bulkhead |
| `acc-adr-knowledge` | `skills/acc-adr-knowledge/` | Action-Domain-Responder pattern (MVC alternative) |
| `acc-solid-knowledge` | `skills/acc-solid-knowledge/` | SOLID principles (SRP, OCP, LSP, ISP, DIP) |
| `acc-grasp-knowledge` | `skills/acc-grasp-knowledge/` | GRASP patterns (9 responsibility assignment principles) |
| `acc-psr-coding-style-knowledge` | `skills/acc-psr-coding-style-knowledge/` | PSR-1/PSR-12 coding standards |
| `acc-psr-autoloading-knowledge` | `skills/acc-psr-autoloading-knowledge/` | PSR-4 autoloading standard |
| `acc-psr-overview-knowledge` | `skills/acc-psr-overview-knowledge/` | All PSR standards overview |
| `acc-documentation-knowledge` | `skills/acc-documentation-knowledge/` | Documentation types, audiences, best practices |
| `acc-diagram-knowledge` | `skills/acc-diagram-knowledge/` | Mermaid syntax, C4 model, diagram types |
| `acc-documentation-qa-knowledge` | `skills/acc-documentation-qa-knowledge/` | Quality checklists, audit criteria |
| `acc-testing-knowledge` | `skills/acc-testing-knowledge/` | Testing pyramid, AAA, naming, isolation, DDD testing |

## Analyzer Skills

### Architecture Analyzers

| Skill | Path | Description |
|-------|------|-------------|
| `acc-analyze-solid-violations` | `skills/acc-analyze-solid-violations/` | SOLID violations analyzer with reports |
| `acc-analyze-test-coverage` | `skills/acc-analyze-test-coverage/` | Detects untested classes, methods, branches |
| `acc-detect-test-smells` | `skills/acc-detect-test-smells/` | Detects 15 test antipatterns |
| `acc-detect-code-smells` | `skills/acc-detect-code-smells/` | Detects God Class, Feature Envy, Data Clumps, etc. |
| `acc-check-bounded-contexts` | `skills/acc-check-bounded-contexts/` | Analyzes DDD bounded context boundaries |
| `acc-check-immutability` | `skills/acc-check-immutability/` | Checks Value Objects, Events, DTOs immutability |
| `acc-check-leaky-abstractions` | `skills/acc-check-leaky-abstractions/` | Detects leaky abstractions, framework leakage |
| `acc-check-encapsulation` | `skills/acc-check-encapsulation/` | Detects public state, Tell Don't Ask violations |
| `acc-analyze-coupling-cohesion` | `skills/acc-analyze-coupling-cohesion/` | Coupling/cohesion metrics (Ca/Ce, LCOM) |

### Bug Detection Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-find-logic-errors` | `skills/acc-find-logic-errors/` | Detects incorrect conditions, wrong operators, missing cases |
| `acc-find-null-pointer-issues` | `skills/acc-find-null-pointer-issues/` | Detects null access, missing checks, nullable returns |
| `acc-find-boundary-issues` | `skills/acc-find-boundary-issues/` | Detects off-by-one, array bounds, empty collections |
| `acc-find-race-conditions` | `skills/acc-find-race-conditions/` | Detects shared mutable state, concurrent access |
| `acc-find-resource-leaks` | `skills/acc-find-resource-leaks/` | Detects unclosed connections, file handles |
| `acc-find-exception-issues` | `skills/acc-find-exception-issues/` | Detects swallowed exceptions, generic catches |
| `acc-find-type-issues` | `skills/acc-find-type-issues/` | Detects type coercion, mixed types, unsafe casts |
| `acc-find-sql-injection` | `skills/acc-find-sql-injection/` | Detects unescaped queries, SQL concatenation |
| `acc-find-infinite-loops` | `skills/acc-find-infinite-loops/` | Detects missing break conditions, infinite recursion |

### Security Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-check-input-validation` | `skills/acc-check-input-validation/` | Checks missing validation, weak regex |
| `acc-check-output-encoding` | `skills/acc-check-output-encoding/` | Checks XSS vectors, missing HTML encoding |
| `acc-check-authentication` | `skills/acc-check-authentication/` | Checks weak auth, insecure sessions |
| `acc-check-authorization` | `skills/acc-check-authorization/` | Checks missing access control, IDOR |
| `acc-check-sensitive-data` | `skills/acc-check-sensitive-data/` | Checks plaintext secrets, PII exposure |
| `acc-check-csrf-protection` | `skills/acc-check-csrf-protection/` | Checks missing CSRF tokens |
| `acc-check-crypto-usage` | `skills/acc-check-crypto-usage/` | Checks weak algorithms, hardcoded keys |
| `acc-check-dependency-vulnerabilities` | `skills/acc-check-dependency-vulnerabilities/` | Checks outdated packages, known CVEs |
| `acc-check-sql-injection` | `skills/acc-check-sql-injection/` | Checks parameterized queries, ORM misuse |

### Performance Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-detect-n-plus-one` | `skills/acc-detect-n-plus-one/` | Detects queries in loops, missing eager loading |
| `acc-check-query-efficiency` | `skills/acc-check-query-efficiency/` | Checks SELECT *, missing indexes |
| `acc-detect-memory-issues` | `skills/acc-detect-memory-issues/` | Checks large arrays, missing generators |
| `acc-check-caching-strategy` | `skills/acc-check-caching-strategy/` | Checks missing cache, invalidation issues |
| `acc-detect-unnecessary-loops` | `skills/acc-detect-unnecessary-loops/` | Checks nested loops, redundant iterations |
| `acc-check-lazy-loading` | `skills/acc-check-lazy-loading/` | Checks premature loading, missing pagination |
| `acc-check-batch-processing` | `skills/acc-check-batch-processing/` | Checks single-item vs bulk operations |

### Readability Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-check-naming` | `skills/acc-check-naming/` | Checks non-descriptive names, abbreviations |
| `acc-check-code-style` | `skills/acc-check-code-style/` | Checks PSR-12 compliance |
| `acc-check-method-length` | `skills/acc-check-method-length/` | Checks methods > 30 lines |
| `acc-check-class-length` | `skills/acc-check-class-length/` | Checks classes > 300 lines |
| `acc-check-nesting-depth` | `skills/acc-check-nesting-depth/` | Checks > 3 levels of nesting |
| `acc-check-comments` | `skills/acc-check-comments/` | Checks missing PHPDoc, outdated comments |
| `acc-check-magic-values` | `skills/acc-check-magic-values/` | Checks hardcoded values without constants |
| `acc-check-consistency` | `skills/acc-check-consistency/` | Checks inconsistent patterns, mixed styles |

### Testability Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-check-dependency-injection` | `skills/acc-check-dependency-injection/` | Checks constructor injection, missing interfaces |
| `acc-check-pure-functions` | `skills/acc-check-pure-functions/` | Checks side effects, external dependencies |
| `acc-check-side-effects` | `skills/acc-check-side-effects/` | Checks state mutation, global access |
| `acc-check-test-quality` | `skills/acc-check-test-quality/` | Checks test structure, assertions, isolation |

### Other Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-estimate-complexity` | `skills/acc-estimate-complexity/` | Analyzes O(n²) algorithms, exponential growth |
| `acc-suggest-simplification` | `skills/acc-suggest-simplification/` | Suggests extract method, introduce variable |
| `acc-suggest-testability-improvements` | `skills/acc-suggest-testability-improvements/` | Suggests DI refactoring, mock opportunities |

## Generator Skills

Code generators for DDD and architecture components (PHP 8.5).

### DDD Components

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-value-object` | `skills/acc-create-value-object/` | DDD Value Objects |
| `acc-create-entity` | `skills/acc-create-entity/` | DDD Entities |
| `acc-create-aggregate` | `skills/acc-create-aggregate/` | DDD Aggregates |
| `acc-create-domain-event` | `skills/acc-create-domain-event/` | Domain Events |
| `acc-create-repository` | `skills/acc-create-repository/` | Repository interfaces |
| `acc-create-domain-service` | `skills/acc-create-domain-service/` | DDD Domain Services |
| `acc-create-factory` | `skills/acc-create-factory/` | DDD Factories |
| `acc-create-specification` | `skills/acc-create-specification/` | DDD Specifications |
| `acc-create-dto` | `skills/acc-create-dto/` | DTOs for layer boundaries |
| `acc-create-anti-corruption-layer` | `skills/acc-create-anti-corruption-layer/` | Anti-Corruption Layer (ACL) |

### CQRS Components

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-command` | `skills/acc-create-command/` | CQRS Commands |
| `acc-create-query` | `skills/acc-create-query/` | CQRS Queries |
| `acc-create-use-case` | `skills/acc-create-use-case/` | Application Use Cases |
| `acc-create-read-model` | `skills/acc-create-read-model/` | CQRS Read Models/Projections |

### Stability Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-circuit-breaker` | `skills/acc-create-circuit-breaker/` | Circuit Breaker pattern |
| `acc-create-retry-pattern` | `skills/acc-create-retry-pattern/` | Retry with exponential backoff |
| `acc-create-rate-limiter` | `skills/acc-create-rate-limiter/` | Rate limiting (Token Bucket, Sliding Window) |
| `acc-create-bulkhead` | `skills/acc-create-bulkhead/` | Bulkhead isolation pattern |

### Integration Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-outbox-pattern` | `skills/acc-create-outbox-pattern/` | Transactional Outbox |
| `acc-create-saga-pattern` | `skills/acc-create-saga-pattern/` | Saga orchestration |

### Behavioral Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-strategy` | `skills/acc-create-strategy/` | Strategy pattern |
| `acc-create-state` | `skills/acc-create-state/` | State machine pattern |
| `acc-create-chain-of-responsibility` | `skills/acc-create-chain-of-responsibility/` | Handler chains |
| `acc-create-decorator` | `skills/acc-create-decorator/` | Decorator pattern |
| `acc-create-null-object` | `skills/acc-create-null-object/` | Null Object pattern |
| `acc-create-policy` | `skills/acc-create-policy/` | Policy pattern |

### Creational Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-builder` | `skills/acc-create-builder/` | Builder pattern |
| `acc-create-object-pool` | `skills/acc-create-object-pool/` | Object Pool pattern |
| `acc-create-di-container` | `skills/acc-create-di-container/` | DI Container configuration |
| `acc-create-mediator` | `skills/acc-create-mediator/` | Mediator pattern |

### Presentation Patterns (ADR)

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-action` | `skills/acc-create-action/` | ADR Action classes (HTTP handlers) |
| `acc-create-responder` | `skills/acc-create-responder/` | ADR Responder classes (response builders) |

### PSR Implementations

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-psr3-logger` | `skills/acc-create-psr3-logger/` | PSR-3 Logger Interface |
| `acc-create-psr6-cache` | `skills/acc-create-psr6-cache/` | PSR-6 Caching Interface |
| `acc-create-psr7-http-message` | `skills/acc-create-psr7-http-message/` | PSR-7 HTTP Messages |
| `acc-create-psr11-container` | `skills/acc-create-psr11-container/` | PSR-11 Container Interface |
| `acc-create-psr13-link` | `skills/acc-create-psr13-link/` | PSR-13 Hypermedia Links |
| `acc-create-psr14-event-dispatcher` | `skills/acc-create-psr14-event-dispatcher/` | PSR-14 Event Dispatcher |
| `acc-create-psr15-middleware` | `skills/acc-create-psr15-middleware/` | PSR-15 HTTP Middleware |
| `acc-create-psr16-simple-cache` | `skills/acc-create-psr16-simple-cache/` | PSR-16 Simple Cache |
| `acc-create-psr17-http-factory` | `skills/acc-create-psr17-http-factory/` | PSR-17 HTTP Factories |
| `acc-create-psr18-http-client` | `skills/acc-create-psr18-http-client/` | PSR-18 HTTP Client |
| `acc-create-psr20-clock` | `skills/acc-create-psr20-clock/` | PSR-20 Clock Interface |

### Testing

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-unit-test` | `skills/acc-create-unit-test/` | PHPUnit unit tests with AAA pattern |
| `acc-create-integration-test` | `skills/acc-create-integration-test/` | Integration tests with DB transactions |
| `acc-create-test-builder` | `skills/acc-create-test-builder/` | Test Data Builder / Object Mother patterns |
| `acc-create-mock-repository` | `skills/acc-create-mock-repository/` | InMemory repository implementations |
| `acc-create-test-double` | `skills/acc-create-test-double/` | Mocks, Stubs, Fakes, Spies |

### Documentation Templates

| Skill | Path | Description |
|-------|------|-------------|
| `acc-readme-template` | `skills/acc-readme-template/` | README.md generation |
| `acc-architecture-doc-template` | `skills/acc-architecture-doc-template/` | ARCHITECTURE.md generation |
| `acc-adr-template` | `skills/acc-adr-template/` | Architecture Decision Records |
| `acc-api-doc-template` | `skills/acc-api-doc-template/` | API documentation |
| `acc-getting-started-template` | `skills/acc-getting-started-template/` | Getting started guides |
| `acc-troubleshooting-template` | `skills/acc-troubleshooting-template/` | FAQ and troubleshooting |
| `acc-code-examples-template` | `skills/acc-code-examples-template/` | Code examples |
| `acc-mermaid-template` | `skills/acc-mermaid-template/` | Mermaid diagram templates |
| `acc-changelog-template` | `skills/acc-changelog-template/` | CHANGELOG format |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Component Flow →](component-flow.md) | [Quick Reference](quick-reference.md)
