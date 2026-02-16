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
| **Knowledge** | 42 | Provide expertise and best practices | `ddd-knowledge` |
| **Analyzer** | 99 | Detect violations and antipatterns | `analyze-solid-violations` |
| **Generator** | 104 | Generate PHP code with tests | `create-entity` |
| **Template** | 10 | Documentation and output templates | `readme-template` |
| **Other** | 4 | Estimation and suggestion utilities | `estimate-complexity` |

## How Skills Work

1. **Loading**: Skills are loaded by agents via `skills:` frontmatter
2. **Activation**: Triggered by keywords in user request or agent decision
3. **Execution**: Skill provides templates, rules, or generates code
4. **Output**: Generated code follows PHP 8.4, DDD, and PSR standards

---

## Knowledge Skills

Knowledge bases for architecture audits and best practices.

| Skill | Path | Description |
|-------|------|-------------|
| `claude-code-knowledge` | `skills/claude-code-knowledge/` | Claude Code formats, patterns, hooks (12 events), memory, plugins, permissions, settings |
| `ddd-knowledge` | `skills/ddd-knowledge/` | DDD patterns, antipatterns |
| `cqrs-knowledge` | `skills/cqrs-knowledge/` | CQRS command/query patterns |
| `clean-arch-knowledge` | `skills/clean-arch-knowledge/` | Clean Architecture patterns |
| `hexagonal-knowledge` | `skills/hexagonal-knowledge/` | Hexagonal/Ports & Adapters |
| `layer-arch-knowledge` | `skills/layer-arch-knowledge/` | Layered Architecture patterns |
| `event-sourcing-knowledge` | `skills/event-sourcing-knowledge/` | Event Sourcing patterns |
| `eda-knowledge` | `skills/eda-knowledge/` | Event-Driven Architecture |
| `outbox-pattern-knowledge` | `skills/outbox-pattern-knowledge/` | Transactional Outbox pattern |
| `saga-pattern-knowledge` | `skills/saga-pattern-knowledge/` | Saga/distributed transactions |
| `stability-patterns-knowledge` | `skills/stability-patterns-knowledge/` | Circuit Breaker, Retry, Rate Limiter, Bulkhead |
| `adr-knowledge` | `skills/adr-knowledge/` | Action-Domain-Responder pattern (MVC alternative) |
| `solid-knowledge` | `skills/solid-knowledge/` | SOLID principles (SRP, OCP, LSP, ISP, DIP) |
| `grasp-knowledge` | `skills/grasp-knowledge/` | GRASP patterns (9 responsibility assignment principles) |
| `psr-coding-style-knowledge` | `skills/psr-coding-style-knowledge/` | PSR-1/PSR-12 coding standards |
| `psr-autoloading-knowledge` | `skills/psr-autoloading-knowledge/` | PSR-4 autoloading standard |
| `psr-overview-knowledge` | `skills/psr-overview-knowledge/` | All PSR standards overview |
| `documentation-knowledge` | `skills/documentation-knowledge/` | Documentation types, audiences, best practices |
| `diagram-knowledge` | `skills/diagram-knowledge/` | Mermaid syntax, C4 model, diagram types |
| `documentation-qa-knowledge` | `skills/documentation-qa-knowledge/` | Quality checklists, audit criteria |
| `testing-knowledge` | `skills/testing-knowledge/` | Testing pyramid, AAA, naming, isolation, DDD testing |
| `ci-pipeline-knowledge` | `skills/ci-pipeline-knowledge/` | CI/CD platforms, stages, caching, parallelization |
| `ci-tools-knowledge` | `skills/ci-tools-knowledge/` | PHPStan levels, Psalm, CS-Fixer, DEPTRAC, Rector |
| `deployment-knowledge` | `skills/deployment-knowledge/` | Zero-downtime, blue-green, canary, rollback, feature flags |
| `task-progress-knowledge` | `skills/task-progress-knowledge/` | TaskCreate pattern for coordinator progress tracking |
| `docker-knowledge` | `skills/docker-knowledge/` | Docker patterns, PHP images, Compose, security |
| `docker-multistage-knowledge` | `skills/docker-multistage-knowledge/` | Multi-stage build patterns |
| `docker-base-images-knowledge` | `skills/docker-base-images-knowledge/` | Base image selection, Alpine vs Debian |
| `docker-php-extensions-knowledge` | `skills/docker-php-extensions-knowledge/` | PHP extension installation patterns |
| `docker-compose-knowledge` | `skills/docker-compose-knowledge/` | Compose configuration for PHP stacks |
| `docker-networking-knowledge` | `skills/docker-networking-knowledge/` | Network configuration, DNS, port mapping |
| `docker-security-knowledge` | `skills/docker-security-knowledge/` | Security hardening, scanning |
| `docker-buildkit-knowledge` | `skills/docker-buildkit-knowledge/` | BuildKit cache mounts, secrets |
| `docker-production-knowledge` | `skills/docker-production-knowledge/` | Health checks, graceful shutdown, logging |
| `docker-troubleshooting-knowledge` | `skills/docker-troubleshooting-knowledge/` | Error diagnosis, debugging commands |
| `docker-orchestration-knowledge` | `skills/docker-orchestration-knowledge/` | Swarm, Kubernetes, scaling |
| `docker-scanning-knowledge` | `skills/docker-scanning-knowledge/` | Vulnerability scanning, SBOM |
| `microservices-knowledge` | `skills/microservices-knowledge/` | Service decomposition, API gateway, service discovery, data management |
| `api-design-knowledge` | `skills/api-design-knowledge/` | REST constraints, Richardson Maturity, HTTP semantics, RFC 7807 |
| `message-queue-knowledge` | `skills/message-queue-knowledge/` | Broker comparison (RabbitMQ/Kafka/SQS), delivery guarantees, consumer groups |
| `caching-strategies-knowledge` | `skills/caching-strategies-knowledge/` | Cache-Aside, Read-Through, Write-Through, invalidation, Redis patterns |

## Analyzer Skills

### Architecture Analyzers

| Skill | Path | Description |
|-------|------|-------------|
| `analyze-solid-violations` | `skills/analyze-solid-violations/` | SOLID violations analyzer with reports |
| `analyze-test-coverage` | `skills/analyze-test-coverage/` | Detects untested classes, methods, branches |
| `detect-test-smells` | `skills/detect-test-smells/` | Detects 15 test antipatterns |
| `detect-code-smells` | `skills/detect-code-smells/` | Detects God Class, Feature Envy, Data Clumps, etc. |
| `check-bounded-contexts` | `skills/check-bounded-contexts/` | Analyzes DDD bounded context boundaries |
| `check-immutability` | `skills/check-immutability/` | Checks Value Objects, Events, DTOs immutability |
| `check-leaky-abstractions` | `skills/check-leaky-abstractions/` | Detects leaky abstractions, framework leakage |
| `check-encapsulation` | `skills/check-encapsulation/` | Detects public state, Tell Don't Ask violations |
| `analyze-coupling-cohesion` | `skills/analyze-coupling-cohesion/` | Coupling/cohesion metrics (Ca/Ce, LCOM) |
| `check-aggregate-consistency` | `skills/check-aggregate-consistency/` | Aggregate rules: single tx boundary, identity by root |
| `check-cqrs-alignment` | `skills/check-cqrs-alignment/` | CQRS/ES: commands no return, projections idempotent |
| `check-context-communication` | `skills/check-context-communication/` | Context Map: Shared Kernel, ACL, event vs direct calls |
| `check-doc-links` | `skills/check-doc-links/` | Broken relative links, missing anchor targets |
| `check-doc-examples` | `skills/check-doc-examples/` | Code examples match actual class/method names |
| `check-version-consistency` | `skills/check-version-consistency/` | Version sync: composer.json, README, CHANGELOG, docs |

### Bug Detection Skills

| Skill | Path | Description |
|-------|------|-------------|
| `find-logic-errors` | `skills/find-logic-errors/` | Detects incorrect conditions, wrong operators, missing cases |
| `find-null-pointer-issues` | `skills/find-null-pointer-issues/` | Detects null access, missing checks, nullable returns |
| `find-boundary-issues` | `skills/find-boundary-issues/` | Detects off-by-one, array bounds, empty collections |
| `find-race-conditions` | `skills/find-race-conditions/` | Detects shared mutable state, concurrent access |
| `find-resource-leaks` | `skills/find-resource-leaks/` | Detects unclosed connections, file handles |
| `find-exception-issues` | `skills/find-exception-issues/` | Detects swallowed exceptions, generic catches |
| `find-type-issues` | `skills/find-type-issues/` | Detects type coercion, mixed types, unsafe casts |
| `find-infinite-loops` | `skills/find-infinite-loops/` | Detects missing break conditions, infinite recursion |

### Bug Fix Skills

| Skill | Path | Description |
|-------|------|-------------|
| `bug-fix-knowledge` | `skills/bug-fix-knowledge/` | Bug categories, symptoms, fix patterns, minimal intervention |
| `bug-root-cause-finder` | `skills/bug-root-cause-finder/` | 5 Whys, fault tree, git bisect, stack trace parsing |
| `bug-impact-analyzer` | `skills/bug-impact-analyzer/` | Blast radius, callers/callees, API contract analysis |
| `generate-bug-fix` | `skills/generate-bug-fix/` | Fix templates for 9 bug categories |
| `bug-regression-preventer` | `skills/bug-regression-preventer/` | API compatibility, behavior preservation checklist |

### Security Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `check-input-validation` | `skills/check-input-validation/` | Checks missing validation, weak regex |
| `check-output-encoding` | `skills/check-output-encoding/` | Checks XSS vectors, missing HTML encoding |
| `check-authentication` | `skills/check-authentication/` | Checks weak auth, insecure sessions |
| `check-authorization` | `skills/check-authorization/` | Checks missing access control, IDOR |
| `check-sensitive-data` | `skills/check-sensitive-data/` | Checks plaintext secrets, PII exposure |
| `check-csrf-protection` | `skills/check-csrf-protection/` | Checks missing CSRF tokens |
| `check-crypto-usage` | `skills/check-crypto-usage/` | Checks weak algorithms, hardcoded keys |
| `check-dependency-vulnerabilities` | `skills/check-dependency-vulnerabilities/` | Checks outdated packages, known CVEs |
| `check-sql-injection` | `skills/check-sql-injection/` | Checks parameterized queries, ORM misuse |
| `check-ssrf` | `skills/check-ssrf/` | Checks SSRF, internal network access, cloud metadata |
| `check-command-injection` | `skills/check-command-injection/` | Checks shell_exec, exec, system with user input |
| `check-deserialization` | `skills/check-deserialization/` | Checks unserialize, allowed_classes, Phar attacks |
| `check-xxe` | `skills/check-xxe/` | Checks XML parsing, entity protection, XSLT attacks |
| `check-path-traversal` | `skills/check-path-traversal/` | Checks directory traversal, file inclusion, Zip slip |
| `check-insecure-design` | `skills/check-insecure-design/` | OWASP A04: missing rate limiting, account lockout, TOCTOU |
| `check-logging-failures` | `skills/check-logging-failures/` | OWASP A09: log injection, PII in logs, missing audit trail |
| `check-secure-headers` | `skills/check-secure-headers/` | CSP, X-Frame-Options, HSTS, Referrer-Policy |
| `check-cors-security` | `skills/check-cors-security/` | Wildcard origins, dynamic reflection, credentials misconfig |
| `check-mass-assignment` | `skills/check-mass-assignment/` | Request::all() to create, missing $fillable/$guarded |
| `check-type-juggling` | `skills/check-type-juggling/` | Loose == with user input, in_array without strict, hash bypass |

### Performance Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `detect-n-plus-one` | `skills/detect-n-plus-one/` | Detects queries in loops, missing eager loading |
| `check-query-efficiency` | `skills/check-query-efficiency/` | Checks SELECT *, missing indexes |
| `detect-memory-issues` | `skills/detect-memory-issues/` | Checks large arrays, missing generators |
| `check-caching-strategy` | `skills/check-caching-strategy/` | Checks missing cache, invalidation issues |
| `detect-unnecessary-loops` | `skills/detect-unnecessary-loops/` | Checks nested loops, redundant iterations |
| `check-lazy-loading` | `skills/check-lazy-loading/` | Checks premature loading, missing pagination |
| `check-batch-processing` | `skills/check-batch-processing/` | Checks single-item vs bulk operations |
| `check-connection-pool` | `skills/check-connection-pool/` | Checks connection leaks, pool exhaustion, timeouts |
| `check-serialization` | `skills/check-serialization/` | Checks JSON overhead, N+1 serialization, hydration |
| `check-index-usage` | `skills/check-index-usage/` | Missing DB indexes on WHERE/JOIN, composite index order |
| `check-async-patterns` | `skills/check-async-patterns/` | Sync ops that should be async: email, API calls in request |
| `check-file-io` | `skills/check-file-io/` | File I/O: streaming vs readAll, missing locks, temp cleanup |

### Readability Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `check-naming` | `skills/check-naming/` | Checks non-descriptive names, abbreviations |
| `check-code-style` | `skills/check-code-style/` | Checks PSR-12 compliance |
| `check-method-length` | `skills/check-method-length/` | Checks methods > 30 lines |
| `check-class-length` | `skills/check-class-length/` | Checks classes > 300 lines |
| `check-nesting-depth` | `skills/check-nesting-depth/` | Checks > 3 levels of nesting |
| `check-comments` | `skills/check-comments/` | Checks missing PHPDoc, outdated comments |
| `check-magic-values` | `skills/check-magic-values/` | Checks hardcoded values without constants |
| `check-consistency` | `skills/check-consistency/` | Checks inconsistent patterns, mixed styles |

### Testability Review Skills

| Skill | Path | Description |
|-------|------|-------------|
| `check-dependency-injection` | `skills/check-dependency-injection/` | Checks constructor injection, missing interfaces |
| `check-pure-functions` | `skills/check-pure-functions/` | Checks side effects, external dependencies |
| `check-side-effects` | `skills/check-side-effects/` | Checks state mutation, global access |
| `check-test-quality` | `skills/check-test-quality/` | Checks test structure, assertions, isolation |

### CI/CD Analyzer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `analyze-ci-config` | `skills/analyze-ci-config/` | Analyze existing CI configuration |
| `analyze-ci-logs` | `skills/analyze-ci-logs/` | Parse CI logs for failures |
| `detect-ci-antipatterns` | `skills/detect-ci-antipatterns/` | Detect CI antipatterns |

### Docker Analyzer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `analyze-docker-build-errors` | `skills/analyze-docker-build-errors/` | Build error diagnosis |
| `analyze-docker-runtime-errors` | `skills/analyze-docker-runtime-errors/` | Runtime error diagnosis |
| `analyze-docker-image-size` | `skills/analyze-docker-image-size/` | Image size analysis |
| `check-docker-security` | `skills/check-docker-security/` | Security checks |
| `check-docker-secrets` | `skills/check-docker-secrets/` | Secret detection |
| `check-docker-user-permissions` | `skills/check-docker-user-permissions/` | User/permission checks |
| `check-docker-compose-config` | `skills/check-docker-compose-config/` | Compose configuration checks |
| `check-docker-production-readiness` | `skills/check-docker-production-readiness/` | Production readiness checks |
| `detect-docker-antipatterns` | `skills/detect-docker-antipatterns/` | Dockerfile antipatterns |
| `check-docker-layer-efficiency` | `skills/check-docker-layer-efficiency/` | Layer caching analysis |
| `check-docker-php-config` | `skills/check-docker-php-config/` | PHP config in Docker |
| `check-docker-healthcheck` | `skills/check-docker-healthcheck/` | Health check verification |

### Code Explainer Skills

| Skill | Path | Description |
|-------|------|-------------|
| `scan-codebase-structure` | `skills/scan-codebase-structure/` | Scans directory tree, identifies layers, detects framework |
| `identify-entry-points` | `skills/identify-entry-points/` | Finds controllers, actions, CLI commands, event handlers |
| `detect-architecture-pattern` | `skills/detect-architecture-pattern/` | Detects MVC/DDD/Hexagonal/CQRS patterns with confidence scores |
| `resolve-entry-point` | `skills/resolve-entry-point/` | Resolves HTTP routes and console commands to handler files |
| `extract-business-rules` | `skills/extract-business-rules/` | Extracts validation, invariants, authorization, policies |
| `explain-business-process` | `skills/explain-business-process/` | Translates method chains into business process descriptions |
| `extract-domain-concepts` | `skills/extract-domain-concepts/` | Maps entities, VOs, aggregates, builds ubiquitous language |
| `extract-state-machine` | `skills/extract-state-machine/` | Detects states/transitions from enums, status fields |
| `trace-request-lifecycle` | `skills/trace-request-lifecycle/` | Traces Router → Middleware → Controller → UseCase → Response |
| `trace-data-transformation` | `skills/trace-data-transformation/` | Maps Request DTO → Command → Entity → Response DTO chain |
| `map-async-flows` | `skills/map-async-flows/` | Finds queue publishing, event dispatching, webhooks |

### Log Analysis Skills

| Skill | Path | Description |
|-------|------|-------------|
| `discover-project-logs` | `skills/discover-project-logs/` | Discovers log files across PHP frameworks, infrastructure, CI/CD |
| `analyze-php-logs` | `skills/analyze-php-logs/` | Parses PHP logs (PSR-3, Monolog, Laravel, Symfony, error_log, FPM slow log) |

### Other Skills

| Skill | Path | Description |
|-------|------|-------------|
| `estimate-complexity` | `skills/estimate-complexity/` | Analyzes O(n²) algorithms, exponential growth |
| `suggest-simplification` | `skills/suggest-simplification/` | Suggests extract method, introduce variable |
| `suggest-testability-improvements` | `skills/suggest-testability-improvements/` | Suggests DI refactoring, mock opportunities |
| `estimate-pipeline-time` | `skills/estimate-pipeline-time/` | Estimate and optimize CI pipeline time |

## Generator Skills

Code generators for DDD and architecture components (PHP 8.4).

### DDD Components

| Skill | Path | Description |
|-------|------|-------------|
| `create-value-object` | `skills/create-value-object/` | DDD Value Objects |
| `create-entity` | `skills/create-entity/` | DDD Entities |
| `create-aggregate` | `skills/create-aggregate/` | DDD Aggregates |
| `create-domain-event` | `skills/create-domain-event/` | Domain Events |
| `create-repository` | `skills/create-repository/` | Repository interfaces |
| `create-domain-service` | `skills/create-domain-service/` | DDD Domain Services |
| `create-factory` | `skills/create-factory/` | DDD Factories |
| `create-specification` | `skills/create-specification/` | DDD Specifications |
| `create-dto` | `skills/create-dto/` | DTOs for layer boundaries |
| `create-anti-corruption-layer` | `skills/create-anti-corruption-layer/` | Anti-Corruption Layer (ACL) |

### CQRS Components

| Skill | Path | Description |
|-------|------|-------------|
| `create-command` | `skills/create-command/` | CQRS Commands |
| `create-query` | `skills/create-query/` | CQRS Queries |
| `create-use-case` | `skills/create-use-case/` | Application Use Cases |
| `create-read-model` | `skills/create-read-model/` | CQRS Read Models/Projections |
| `create-event-store` | `skills/create-event-store/` | Event Store with optimistic locking |
| `create-snapshot` | `skills/create-snapshot/` | Aggregate snapshots for event sourcing |

### Stability Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `create-circuit-breaker` | `skills/create-circuit-breaker/` | Circuit Breaker pattern |
| `create-retry-pattern` | `skills/create-retry-pattern/` | Retry with exponential backoff |
| `create-rate-limiter` | `skills/create-rate-limiter/` | Rate limiting (Token Bucket, Sliding Window) |
| `create-bulkhead` | `skills/create-bulkhead/` | Bulkhead isolation pattern |
| `create-cache-aside` | `skills/create-cache-aside/` | Cache-Aside with stampede protection |
| `create-timeout` | `skills/create-timeout/` | Timeout pattern (signal/stream executors, middleware) |
| `check-timeout-strategy` | `skills/check-timeout-strategy/` | Timeout config: HTTP, DB, queue, cache, locks |
| `check-cascading-failures` | `skills/check-cascading-failures/` | Shared resources, unbounded queues, failure propagation |
| `check-fallback-strategy` | `skills/check-fallback-strategy/` | Graceful degradation, cache fallback, feature flags |

### Integration Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `create-outbox-pattern` | `skills/create-outbox-pattern/` | Transactional Outbox |
| `create-saga-pattern` | `skills/create-saga-pattern/` | Saga orchestration |
| `create-correlation-context` | `skills/create-correlation-context/` | Correlation ID propagation (middleware, log processor, message stamp) |
| `create-api-versioning` | `skills/create-api-versioning/` | API Versioning (URI/header/query strategies, deprecation) |
| `create-health-check` | `skills/create-health-check/` | Health Check endpoints (Database, Redis, RabbitMQ) |
| `create-unit-of-work` | `skills/create-unit-of-work/` | Unit of Work (aggregate tracking, transactional consistency) |
| `create-message-broker-adapter` | `skills/create-message-broker-adapter/` | Message Broker Adapter (RabbitMQ/Kafka/SQS) |
| `create-idempotent-consumer` | `skills/create-idempotent-consumer/` | Idempotent Consumer (message deduplication) |
| `create-dead-letter-queue` | `skills/create-dead-letter-queue/` | Dead Letter Queue (failed message capture and retry) |

### Behavioral Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `create-strategy` | `skills/create-strategy/` | Strategy pattern |
| `create-state` | `skills/create-state/` | State machine pattern |
| `create-chain-of-responsibility` | `skills/create-chain-of-responsibility/` | Handler chains |
| `create-decorator` | `skills/create-decorator/` | Decorator pattern |
| `create-null-object` | `skills/create-null-object/` | Null Object pattern |
| `create-policy` | `skills/create-policy/` | Policy pattern |
| `create-template-method` | `skills/create-template-method/` | Template Method pattern |
| `create-visitor` | `skills/create-visitor/` | Visitor pattern |
| `create-iterator` | `skills/create-iterator/` | Iterator pattern |
| `create-memento` | `skills/create-memento/` | Memento pattern |

### Structural Patterns (GoF)

| Skill | Path | Description |
|-------|------|-------------|
| `create-adapter` | `skills/create-adapter/` | Adapter pattern |
| `create-facade` | `skills/create-facade/` | Facade pattern |
| `create-proxy` | `skills/create-proxy/` | Proxy pattern |
| `create-composite` | `skills/create-composite/` | Composite pattern |
| `create-bridge` | `skills/create-bridge/` | Bridge pattern |
| `create-flyweight` | `skills/create-flyweight/` | Flyweight pattern |

### Creational Patterns

| Skill | Path | Description |
|-------|------|-------------|
| `create-builder` | `skills/create-builder/` | Builder pattern |
| `create-object-pool` | `skills/create-object-pool/` | Object Pool pattern |
| `create-di-container` | `skills/create-di-container/` | DI Container configuration |
| `create-mediator` | `skills/create-mediator/` | Mediator pattern |
| `create-prototype` | `skills/create-prototype/` | Prototype pattern (deep/shallow copy) |
| `check-singleton-antipattern` | `skills/check-singleton-antipattern/` | Singleton anti-pattern: global state, static instances |
| `check-abstract-factory` | `skills/check-abstract-factory/` | Abstract Factory: family consistency, product hierarchy |

### Presentation Patterns (ADR)

| Skill | Path | Description |
|-------|------|-------------|
| `create-action` | `skills/create-action/` | ADR Action classes (HTTP handlers) |
| `create-responder` | `skills/create-responder/` | ADR Responder classes (response builders) |

### PSR Implementations

| Skill | Path | Description |
|-------|------|-------------|
| `create-psr3-logger` | `skills/create-psr3-logger/` | PSR-3 Logger Interface |
| `create-psr6-cache` | `skills/create-psr6-cache/` | PSR-6 Caching Interface |
| `create-psr7-http-message` | `skills/create-psr7-http-message/` | PSR-7 HTTP Messages |
| `create-psr11-container` | `skills/create-psr11-container/` | PSR-11 Container Interface |
| `create-psr13-link` | `skills/create-psr13-link/` | PSR-13 Hypermedia Links |
| `create-psr14-event-dispatcher` | `skills/create-psr14-event-dispatcher/` | PSR-14 Event Dispatcher |
| `create-psr15-middleware` | `skills/create-psr15-middleware/` | PSR-15 HTTP Middleware |
| `create-psr16-simple-cache` | `skills/create-psr16-simple-cache/` | PSR-16 Simple Cache |
| `create-psr17-http-factory` | `skills/create-psr17-http-factory/` | PSR-17 HTTP Factories |
| `create-psr18-http-client` | `skills/create-psr18-http-client/` | PSR-18 HTTP Client |
| `create-psr20-clock` | `skills/create-psr20-clock/` | PSR-20 Clock Interface |

### Testing

| Skill | Path | Description |
|-------|------|-------------|
| `create-unit-test` | `skills/create-unit-test/` | PHPUnit unit tests with AAA pattern |
| `create-integration-test` | `skills/create-integration-test/` | Integration tests with DB transactions |
| `create-test-builder` | `skills/create-test-builder/` | Test Data Builder / Object Mother patterns |
| `create-mock-repository` | `skills/create-mock-repository/` | InMemory repository implementations |
| `create-test-double` | `skills/create-test-double/` | Mocks, Stubs, Fakes, Spies |

### CI/CD Config Generators

| Skill | Path | Description |
|-------|------|-------------|
| `create-github-actions` | `skills/create-github-actions/` | GitHub Actions workflow generation |
| `create-gitlab-ci` | `skills/create-gitlab-ci/` | GitLab CI configuration |
| `create-phpstan-config` | `skills/create-phpstan-config/` | PHPStan neon configuration |
| `create-psalm-config` | `skills/create-psalm-config/` | Psalm XML configuration |
| `create-deptrac-config` | `skills/create-deptrac-config/` | DEPTRAC YAML for DDD layers |
| `create-rector-config` | `skills/create-rector-config/` | Rector PHP configuration |
| `generate-ci-fix` | `skills/generate-ci-fix/` | CI configuration fix generation |

### Docker Skills

| Skill | Path | Description |
|-------|------|-------------|
| `create-dockerfile-ci` | `skills/create-dockerfile-ci/` | Multi-stage Dockerfiles for CI |
| `create-dockerfile-production` | `skills/create-dockerfile-production/` | Production Dockerfiles |
| `create-dockerfile-dev` | `skills/create-dockerfile-dev/` | Development Dockerfiles with Xdebug |
| `create-dockerignore` | `skills/create-dockerignore/` | .dockerignore generation |
| `create-docker-compose-dev` | `skills/create-docker-compose-dev/` | Development Compose stacks |
| `create-docker-compose-production` | `skills/create-docker-compose-production/` | Production Compose configs |
| `create-docker-php-config` | `skills/create-docker-php-config/` | php.ini, opcache, PHP-FPM configs |
| `create-docker-healthcheck` | `skills/create-docker-healthcheck/` | Health check scripts |
| `create-docker-entrypoint` | `skills/create-docker-entrypoint/` | Entrypoint scripts |
| `create-docker-nginx-config` | `skills/create-docker-nginx-config/` | Nginx reverse proxy configs |
| `create-docker-makefile` | `skills/create-docker-makefile/` | Docker Makefile commands |
| `create-docker-env-template` | `skills/create-docker-env-template/` | Environment templates |
| `create-docker-supervisor-config` | `skills/create-docker-supervisor-config/` | Supervisor configs |
| `optimize-docker-layers` | `skills/optimize-docker-layers/` | Docker layer caching optimization |
| `optimize-docker-build-time` | `skills/optimize-docker-build-time/` | Build time optimization |
| `optimize-docker-image-size` | `skills/optimize-docker-image-size/` | Image size reduction |
| `optimize-docker-php-fpm` | `skills/optimize-docker-php-fpm/` | PHP-FPM tuning |
| `optimize-docker-compose-resources` | `skills/optimize-docker-compose-resources/` | Resource allocation |
| `optimize-docker-opcache` | `skills/optimize-docker-opcache/` | OPcache configuration |
| `optimize-docker-startup` | `skills/optimize-docker-startup/` | Container startup optimization |

### Deployment Skills

| Skill | Path | Description |
|-------|------|-------------|
| `create-deploy-strategy` | `skills/create-deploy-strategy/` | Blue-green, canary, rolling configs |
| `create-feature-flags` | `skills/create-feature-flags/` | Feature flag PHP implementation |

### Documentation Templates

| Skill | Path | Description |
|-------|------|-------------|
| `readme-template` | `skills/readme-template/` | README.md generation |
| `architecture-doc-template` | `skills/architecture-doc-template/` | ARCHITECTURE.md generation |
| `adr-template` | `skills/adr-template/` | Architecture Decision Records |
| `api-doc-template` | `skills/api-doc-template/` | API documentation |
| `getting-started-template` | `skills/getting-started-template/` | Getting started guides |
| `troubleshooting-template` | `skills/troubleshooting-template/` | FAQ and troubleshooting |
| `code-examples-template` | `skills/code-examples-template/` | Code examples |
| `mermaid-template` | `skills/mermaid-template/` | Mermaid diagram templates |
| `changelog-template` | `skills/changelog-template/` | CHANGELOG format |
| `explain-output-template` | `skills/explain-output-template/` | Output templates for 5 explain modes |

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Component Flow →](component-flow.md) | [Quick Reference](quick-reference.md)
