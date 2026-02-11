# Skills

Knowledge bases and code generators. Skills provide domain expertise and code generation templates for agents.

## Table of Contents

- [Skill Types](#skill-types)
- [How Skills Work](#how-skills-work)
- [Knowledge Skills](#knowledge-skills)
- [Analyzer Skills](#analyzer-skills)
  - [Architecture Analyzers](#architecture-analyzers)
  - [Bug Detection Skills](#bug-detection-skills)
  - [Bug Fix Skills](#bug-fix-skills)
  - [Security Review Skills](#security-review-skills)
  - [Performance Review Skills](#performance-review-skills)
  - [Readability Review Skills](#readability-review-skills)
  - [Testability Review Skills](#testability-review-skills)
  - [CI/CD Analyzer Skills](#cicd-analyzer-skills)
  - [Docker Analyzer Skills](#docker-analyzer-skills)
  - [Code Explainer Skills](#code-explainer-skills)
  - [Log Analysis Skills](#log-analysis-skills)
- [Other Skills](#other-skills)
- [Generator Skills](#generator-skills)
  - [DDD Components](#ddd-components)
  - [CQRS Components](#cqrs-components)
  - [Stability Patterns](#stability-patterns)
  - [Integration Patterns](#integration-patterns)
  - [Behavioral Patterns](#behavioral-patterns)
  - [Structural Patterns (GoF)](#structural-patterns-gof)
  - [Creational Patterns](#creational-patterns)
  - [Presentation Patterns (ADR)](#presentation-patterns-adr)
  - [PSR Implementations](#psr-implementations)
  - [Testing](#testing)
  - [CI/CD Config Generators](#cicd-config-generators)
  - [Docker Skills](#docker-skills)
  - [Deployment Skills](#deployment-skills)
  - [Documentation Templates](#documentation-templates)

---

## Skill Types

| Type | Count | Purpose | Example |
|------|-------|---------|---------|
| **Knowledge** | 38 | Provide expertise and best practices | `acc-ddd-knowledge` |
| **Analyzer** | 99 | Detect violations and antipatterns | `acc-analyze-solid-violations` |
| **Generator** | 94 | Generate PHP code with tests | `acc-create-entity` |
| **Template** | 10 | Documentation and output templates | `acc-readme-template` |
| **Other** | 4 | Estimation and suggestion utilities | `acc-estimate-complexity` |

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
| `acc-claude-code-knowledge` | `skills/acc-claude-code-knowledge/` | Claude Code formats, patterns, hooks (12 events), memory, plugins, permissions, settings |
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
| `acc-ci-pipeline-knowledge` | `skills/acc-ci-pipeline-knowledge/` | CI/CD platforms, stages, caching, parallelization |
| `acc-ci-tools-knowledge` | `skills/acc-ci-tools-knowledge/` | PHPStan levels, Psalm, CS-Fixer, DEPTRAC, Rector |
| `acc-deployment-knowledge` | `skills/acc-deployment-knowledge/` | Zero-downtime, blue-green, canary, rollback, feature flags |
| `acc-task-progress-knowledge` | `skills/acc-task-progress-knowledge/` | TaskCreate pattern for coordinator progress tracking |
| `acc-docker-knowledge` | `skills/acc-docker-knowledge/` | Docker patterns, PHP images, Compose, security |
| `acc-docker-multistage-knowledge` | `skills/acc-docker-multistage-knowledge/` | Multi-stage build patterns |
| `acc-docker-base-images-knowledge` | `skills/acc-docker-base-images-knowledge/` | Base image selection, Alpine vs Debian |
| `acc-docker-php-extensions-knowledge` | `skills/acc-docker-php-extensions-knowledge/` | PHP extension installation patterns |
| `acc-docker-compose-knowledge` | `skills/acc-docker-compose-knowledge/` | Compose configuration for PHP stacks |
| `acc-docker-networking-knowledge` | `skills/acc-docker-networking-knowledge/` | Network configuration, DNS, port mapping |
| `acc-docker-security-knowledge` | `skills/acc-docker-security-knowledge/` | Security hardening, scanning |
| `acc-docker-buildkit-knowledge` | `skills/acc-docker-buildkit-knowledge/` | BuildKit cache mounts, secrets |
| `acc-docker-production-knowledge` | `skills/acc-docker-production-knowledge/` | Health checks, graceful shutdown, logging |
| `acc-docker-troubleshooting-knowledge` | `skills/acc-docker-troubleshooting-knowledge/` | Error diagnosis, debugging commands |
| `acc-docker-orchestration-knowledge` | `skills/acc-docker-orchestration-knowledge/` | Swarm, Kubernetes, scaling |
| `acc-docker-scanning-knowledge` | `skills/acc-docker-scanning-knowledge/` | Vulnerability scanning, SBOM |

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
| `acc-check-aggregate-consistency` | `skills/acc-check-aggregate-consistency/` | Aggregate rules: single tx boundary, identity by root |
| `acc-check-cqrs-alignment` | `skills/acc-check-cqrs-alignment/` | CQRS/ES: commands no return, projections idempotent |
| `acc-check-context-communication` | `skills/acc-check-context-communication/` | Context Map: Shared Kernel, ACL, event vs direct calls |
| `acc-check-doc-links` | `skills/acc-check-doc-links/` | Broken relative links, missing anchor targets |
| `acc-check-doc-examples` | `skills/acc-check-doc-examples/` | Code examples match actual class/method names |
| `acc-check-version-consistency` | `skills/acc-check-version-consistency/` | Version sync: composer.json, README, CHANGELOG, docs |

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
| `acc-find-infinite-loops` | `skills/acc-find-infinite-loops/` | Detects missing break conditions, infinite recursion |

### Bug Fix Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-bug-fix-knowledge` | `skills/acc-bug-fix-knowledge/` | Bug categories, symptoms, fix patterns, minimal intervention |
| `acc-bug-root-cause-finder` | `skills/acc-bug-root-cause-finder/` | 5 Whys, fault tree, git bisect, stack trace parsing |
| `acc-bug-impact-analyzer` | `skills/acc-bug-impact-analyzer/` | Blast radius, callers/callees, API contract analysis |
| `acc-generate-bug-fix` | `skills/acc-generate-bug-fix/` | Fix templates for 9 bug categories |
| `acc-bug-regression-preventer` | `skills/acc-bug-regression-preventer/` | API compatibility, behavior preservation checklist |

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
| `acc-check-ssrf` | `skills/acc-check-ssrf/` | Checks SSRF, internal network access, cloud metadata |
| `acc-check-command-injection` | `skills/acc-check-command-injection/` | Checks shell_exec, exec, system with user input |
| `acc-check-deserialization` | `skills/acc-check-deserialization/` | Checks unserialize, allowed_classes, Phar attacks |
| `acc-check-xxe` | `skills/acc-check-xxe/` | Checks XML parsing, entity protection, XSLT attacks |
| `acc-check-path-traversal` | `skills/acc-check-path-traversal/` | Checks directory traversal, file inclusion, Zip slip |
| `acc-check-insecure-design` | `skills/acc-check-insecure-design/` | OWASP A04: missing rate limiting, account lockout, TOCTOU |
| `acc-check-logging-failures` | `skills/acc-check-logging-failures/` | OWASP A09: log injection, PII in logs, missing audit trail |
| `acc-check-secure-headers` | `skills/acc-check-secure-headers/` | CSP, X-Frame-Options, HSTS, Referrer-Policy |
| `acc-check-cors-security` | `skills/acc-check-cors-security/` | Wildcard origins, dynamic reflection, credentials misconfig |
| `acc-check-mass-assignment` | `skills/acc-check-mass-assignment/` | Request::all() to create, missing $fillable/$guarded |
| `acc-check-type-juggling` | `skills/acc-check-type-juggling/` | Loose == with user input, in_array without strict, hash bypass |

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
| `acc-check-connection-pool` | `skills/acc-check-connection-pool/` | Checks connection leaks, pool exhaustion, timeouts |
| `acc-check-serialization` | `skills/acc-check-serialization/` | Checks JSON overhead, N+1 serialization, hydration |
| `acc-check-index-usage` | `skills/acc-check-index-usage/` | Missing DB indexes on WHERE/JOIN, composite index order |
| `acc-check-async-patterns` | `skills/acc-check-async-patterns/` | Sync ops that should be async: email, API calls in request |
| `acc-check-file-io` | `skills/acc-check-file-io/` | File I/O: streaming vs readAll, missing locks, temp cleanup |

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

### CI/CD Analyzer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-analyze-ci-config` | `skills/acc-analyze-ci-config/` | Analyze existing CI configuration |
| `acc-analyze-ci-logs` | `skills/acc-analyze-ci-logs/` | Parse CI logs for failures |
| `acc-detect-ci-antipatterns` | `skills/acc-detect-ci-antipatterns/` | Detect CI antipatterns |

### Docker Analyzer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-analyze-docker-build-errors` | `skills/acc-analyze-docker-build-errors/` | Build error diagnosis |
| `acc-analyze-docker-runtime-errors` | `skills/acc-analyze-docker-runtime-errors/` | Runtime error diagnosis |
| `acc-analyze-docker-image-size` | `skills/acc-analyze-docker-image-size/` | Image size analysis |
| `acc-check-docker-security` | `skills/acc-check-docker-security/` | Security checks |
| `acc-check-docker-secrets` | `skills/acc-check-docker-secrets/` | Secret detection |
| `acc-check-docker-user-permissions` | `skills/acc-check-docker-user-permissions/` | User/permission checks |
| `acc-check-docker-compose-config` | `skills/acc-check-docker-compose-config/` | Compose configuration checks |
| `acc-check-docker-production-readiness` | `skills/acc-check-docker-production-readiness/` | Production readiness checks |
| `acc-detect-docker-antipatterns` | `skills/acc-detect-docker-antipatterns/` | Dockerfile antipatterns |
| `acc-check-docker-layer-efficiency` | `skills/acc-check-docker-layer-efficiency/` | Layer caching analysis |
| `acc-check-docker-php-config` | `skills/acc-check-docker-php-config/` | PHP config in Docker |
| `acc-check-docker-healthcheck` | `skills/acc-check-docker-healthcheck/` | Health check verification |

### Code Explainer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-scan-codebase-structure` | `skills/acc-scan-codebase-structure/` | Scans directory tree, identifies layers, detects framework |
| `acc-identify-entry-points` | `skills/acc-identify-entry-points/` | Finds controllers, actions, CLI commands, event handlers |
| `acc-detect-architecture-pattern` | `skills/acc-detect-architecture-pattern/` | Detects MVC/DDD/Hexagonal/CQRS patterns with confidence scores |
| `acc-resolve-entry-point` | `skills/acc-resolve-entry-point/` | Resolves HTTP routes and console commands to handler files |
| `acc-extract-business-rules` | `skills/acc-extract-business-rules/` | Extracts validation, invariants, authorization, policies |
| `acc-explain-business-process` | `skills/acc-explain-business-process/` | Translates method chains into business process descriptions |
| `acc-extract-domain-concepts` | `skills/acc-extract-domain-concepts/` | Maps entities, VOs, aggregates, builds ubiquitous language |
| `acc-extract-state-machine` | `skills/acc-extract-state-machine/` | Detects states/transitions from enums, status fields |
| `acc-trace-request-lifecycle` | `skills/acc-trace-request-lifecycle/` | Traces Router → Middleware → Controller → UseCase → Response |
| `acc-trace-data-transformation` | `skills/acc-trace-data-transformation/` | Maps Request DTO → Command → Entity → Response DTO chain |
| `acc-map-async-flows` | `skills/acc-map-async-flows/` | Finds queue publishing, event dispatching, webhooks |

### Log Analysis Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-discover-project-logs` | `skills/acc-discover-project-logs/` | Discovers log files across PHP frameworks, infrastructure, CI/CD |
| `acc-analyze-php-logs` | `skills/acc-analyze-php-logs/` | Parses PHP logs (PSR-3, Monolog, Laravel, Symfony, error_log, FPM slow log) |

### Other Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-estimate-complexity` | `skills/acc-estimate-complexity/` | Analyzes O(n²) algorithms, exponential growth |
| `acc-suggest-simplification` | `skills/acc-suggest-simplification/` | Suggests extract method, introduce variable |
| `acc-suggest-testability-improvements` | `skills/acc-suggest-testability-improvements/` | Suggests DI refactoring, mock opportunities |
| `acc-estimate-pipeline-time` | `skills/acc-estimate-pipeline-time/` | Estimate and optimize CI pipeline time |

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
| `acc-check-timeout-strategy` | `skills/acc-check-timeout-strategy/` | Timeout config: HTTP, DB, queue, cache, locks |
| `acc-check-cascading-failures` | `skills/acc-check-cascading-failures/` | Shared resources, unbounded queues, failure propagation |
| `acc-check-fallback-strategy` | `skills/acc-check-fallback-strategy/` | Graceful degradation, cache fallback, feature flags |

### Integration Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-outbox-pattern` | `skills/acc-create-outbox-pattern/` | Transactional Outbox |
| `acc-create-saga-pattern` | `skills/acc-create-saga-pattern/` | Saga orchestration |
| `acc-create-correlation-context` | `skills/acc-create-correlation-context/` | Correlation ID propagation (middleware, log processor, message stamp) |

### Behavioral Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-strategy` | `skills/acc-create-strategy/` | Strategy pattern |
| `acc-create-state` | `skills/acc-create-state/` | State machine pattern |
| `acc-create-chain-of-responsibility` | `skills/acc-create-chain-of-responsibility/` | Handler chains |
| `acc-create-decorator` | `skills/acc-create-decorator/` | Decorator pattern |
| `acc-create-null-object` | `skills/acc-create-null-object/` | Null Object pattern |
| `acc-create-policy` | `skills/acc-create-policy/` | Policy pattern |
| `acc-create-template-method` | `skills/acc-create-template-method/` | Template Method pattern |
| `acc-create-visitor` | `skills/acc-create-visitor/` | Visitor pattern |
| `acc-create-iterator` | `skills/acc-create-iterator/` | Iterator pattern |
| `acc-create-memento` | `skills/acc-create-memento/` | Memento pattern |

### Structural Patterns (GoF)

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-adapter` | `skills/acc-create-adapter/` | Adapter pattern |
| `acc-create-facade` | `skills/acc-create-facade/` | Facade pattern |
| `acc-create-proxy` | `skills/acc-create-proxy/` | Proxy pattern |
| `acc-create-composite` | `skills/acc-create-composite/` | Composite pattern |
| `acc-create-bridge` | `skills/acc-create-bridge/` | Bridge pattern |
| `acc-create-flyweight` | `skills/acc-create-flyweight/` | Flyweight pattern |

### Creational Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-builder` | `skills/acc-create-builder/` | Builder pattern |
| `acc-create-object-pool` | `skills/acc-create-object-pool/` | Object Pool pattern |
| `acc-create-di-container` | `skills/acc-create-di-container/` | DI Container configuration |
| `acc-create-mediator` | `skills/acc-create-mediator/` | Mediator pattern |
| `acc-create-prototype` | `skills/acc-create-prototype/` | Prototype pattern (deep/shallow copy) |
| `acc-check-singleton-antipattern` | `skills/acc-check-singleton-antipattern/` | Singleton anti-pattern: global state, static instances |
| `acc-check-abstract-factory` | `skills/acc-check-abstract-factory/` | Abstract Factory: family consistency, product hierarchy |

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

### CI/CD Config Generators

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-github-actions` | `skills/acc-create-github-actions/` | GitHub Actions workflow generation |
| `acc-create-gitlab-ci` | `skills/acc-create-gitlab-ci/` | GitLab CI configuration |
| `acc-create-phpstan-config` | `skills/acc-create-phpstan-config/` | PHPStan neon configuration |
| `acc-create-psalm-config` | `skills/acc-create-psalm-config/` | Psalm XML configuration |
| `acc-create-deptrac-config` | `skills/acc-create-deptrac-config/` | DEPTRAC YAML for DDD layers |
| `acc-create-rector-config` | `skills/acc-create-rector-config/` | Rector PHP configuration |
| `acc-generate-ci-fix` | `skills/acc-generate-ci-fix/` | CI configuration fix generation |

### Docker Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-dockerfile-ci` | `skills/acc-create-dockerfile-ci/` | Multi-stage Dockerfiles for CI |
| `acc-create-dockerfile-production` | `skills/acc-create-dockerfile-production/` | Production Dockerfiles |
| `acc-create-dockerfile-dev` | `skills/acc-create-dockerfile-dev/` | Development Dockerfiles with Xdebug |
| `acc-create-dockerignore` | `skills/acc-create-dockerignore/` | .dockerignore generation |
| `acc-create-docker-compose-dev` | `skills/acc-create-docker-compose-dev/` | Development Compose stacks |
| `acc-create-docker-compose-production` | `skills/acc-create-docker-compose-production/` | Production Compose configs |
| `acc-create-docker-php-config` | `skills/acc-create-docker-php-config/` | php.ini, opcache, PHP-FPM configs |
| `acc-create-docker-healthcheck` | `skills/acc-create-docker-healthcheck/` | Health check scripts |
| `acc-create-docker-entrypoint` | `skills/acc-create-docker-entrypoint/` | Entrypoint scripts |
| `acc-create-docker-nginx-config` | `skills/acc-create-docker-nginx-config/` | Nginx reverse proxy configs |
| `acc-create-docker-makefile` | `skills/acc-create-docker-makefile/` | Docker Makefile commands |
| `acc-create-docker-env-template` | `skills/acc-create-docker-env-template/` | Environment templates |
| `acc-create-docker-supervisor-config` | `skills/acc-create-docker-supervisor-config/` | Supervisor configs |
| `acc-optimize-docker-layers` | `skills/acc-optimize-docker-layers/` | Docker layer caching optimization |
| `acc-optimize-docker-build-time` | `skills/acc-optimize-docker-build-time/` | Build time optimization |
| `acc-optimize-docker-image-size` | `skills/acc-optimize-docker-image-size/` | Image size reduction |
| `acc-optimize-docker-php-fpm` | `skills/acc-optimize-docker-php-fpm/` | PHP-FPM tuning |
| `acc-optimize-docker-compose-resources` | `skills/acc-optimize-docker-compose-resources/` | Resource allocation |
| `acc-optimize-docker-opcache` | `skills/acc-optimize-docker-opcache/` | OPcache configuration |
| `acc-optimize-docker-startup` | `skills/acc-optimize-docker-startup/` | Container startup optimization |

### Deployment Skills

| Skill | Path | Description |
|-------|------|-------------|
| `acc-create-deploy-strategy` | `skills/acc-create-deploy-strategy/` | Blue-green, canary, rolling configs |
| `acc-create-feature-flags` | `skills/acc-create-feature-flags/` | Feature flag PHP implementation |

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
| `acc-explain-output-template` | `skills/acc-explain-output-template/` | Output templates for 5 explain modes |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Component Flow →](component-flow.md) | [Quick Reference](quick-reference.md)
