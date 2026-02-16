# Component Flow

How commands, agents, and skills interact. This document shows the dependency graph and execution flow.

## Architecture Overview

```
User Input → Command → Agent(s) → Skills → Output
```

1. **User** invokes a slash command (e.g., `/acc:audit-architecture`)
2. **Command** loads primary agent and passes context
3. **Agent** loads skills and performs analysis/generation
4. **Agent** may delegate subtasks to other agents via Task tool
5. **Skills** provide domain knowledge or generate code
6. **Output** is returned to user (report, generated files, etc.)

---

## Dependency Graph

```
COMMANDS                    AGENTS                      SKILLS
────────                    ──────                      ──────
/acc:commit ────────────→ (direct Bash)

/acc:generate-claude-component ───────→ acc:claude-code-expert ───→ claude-code-knowledge

/acc:audit-claude-components → (direct analysis)

/acc:audit-ddd ─────────→ acc:ddd-auditor (8 skills) ──→ DDD, SOLID, GRASP knowledge + 3 analyzers
                                │
                                ├──→ (Task) acc:ddd-generator ──→ 11 create-* skills (domain + app)
                                └──→ (Task) acc:cqrs-generator ─→ 6 create-* skills (CQRS/ES)

/acc:audit-architecture ─→ acc:architecture-auditor (coordinator)
                                │
                                ├──→ (Task) acc:structural-auditor ──→ 12 skills
                                │           └── DDD, Clean, Hexagonal, Layered, SOLID, GRASP + 6 analyzers
                                │
                                ├──→ (Task) acc:behavioral-auditor ──→ 11 skills
                                │           └── Strategy, State, Chain, Decorator, Null Object, etc.
                                │
                                ├──→ (Task) acc:integration-auditor ─→ 12 skills
                                │           └── Outbox, Saga, ADR
                                │
                                ├──→ (Task) acc:ddd-generator
                                ├──→ (Task) acc:cqrs-generator
                                └──→ (Task) acc:pattern-generator (coordinator)
                                                  │
                                                  ├──→ (Task) acc:stability-generator ──→ 6 skills
                                                  ├──→ (Task) acc:behavioral-generator ─→ 10 skills
                                                  ├──→ (Task) acc:gof-structural-generator → 6 skills
                                                  ├──→ (Task) acc:creational-generator ─→ 3 skills
                                                  └──→ (Task) acc:integration-generator → 11 skills

/acc:audit-patterns ────→ acc:pattern-auditor (coordinator, 2 skills)
                                │
                                ├──→ (Task) acc:stability-auditor ───→ 9 skills
                                │           └── Circuit Breaker, Retry, Rate Limiter, Bulkhead,
                                │               Timeout, Cascading Failures, Fallback
                                │
                                ├──→ (Task) acc:behavioral-auditor ──→ 11 skills
                                │           └── Strategy, State, Chain, Decorator, Null Object,
                                │               Template Method, Visitor, Iterator, Memento
                                │
                                ├──→ (Task) acc:gof-structural-auditor → 6 skills
                                │           └── Adapter, Facade, Proxy, Composite, Bridge, Flyweight
                                │
                                ├──→ (Task) acc:creational-auditor ──→ 7 skills
                                │           └── Builder, Object Pool, Factory, Singleton (anti),
                                │               Abstract Factory, Prototype
                                │
                                └──→ (Task) acc:integration-auditor ─→ 12 skills
                                            └── Outbox, Saga, ADR

/acc:audit-psr ─────────→ acc:psr-auditor ─────────→ 3 PSR knowledge skills
                                │
                                └──→ (Skill) 11 PSR create-* skills

/acc:generate-documentation → acc:documentation-writer ─→ 8 template skills
                                │
                                └──→ (Task) acc:diagram-designer ─→ 2 diagram skills

/acc:audit-documentation → acc:documentation-auditor → 7 skills (3 knowledge + 3 analyzers + progress)

/acc:generate-test ────────→ acc:test-generator ────────→ testing-knowledge
                                                       5 test create-* skills

/acc:audit-test ────────→ acc:test-auditor ──────────→ testing-knowledge
                                │                      2 test analyze skills
                                └──→ (Task) acc:test-generator

/acc:bug-fix ──────────→ acc:bug-fix-coordinator
                                │
                                ├──→ (Task) acc:bug-hunter ─────────→ 11 skills (9 detection + 2 log analysis)
                                │           └── logic, null, boundary, race, resource, exception, type, sql, infinite
                                │           └── discover-project-logs, analyze-php-logs
                                │
                                ├──→ (Task) acc:bug-fixer ──────────→ 12 skills (5 fix + 6 quality + 1 log)
                                │           └── fix-knowledge, root-cause, impact, generate-fix, regression-preventer
                                │           └── code-smells, memory, solid, encapsulation, side-effects, immutability
                                │           └── analyze-php-logs
                                │
                                └──→ (Task) acc:test-generator ─────→ 6 test skills

/acc:ci-setup ────────→ acc:ci-coordinator (mode: SETUP)
/acc:ci-fix ──────────→       │
/acc:ci-optimize ─────→       │
/acc:audit-ci ────────→       │
                              │
                              ├── SETUP ────→ acc:pipeline-architect ──→ 3 knowledge skills
                              │                        │                   └── ci-pipeline, ci-tools, deployment
                              │                        └──→ (Task) acc:docker-agent ──→ 2 docker skills
                              │                        └──→ (Task) acc:static-analysis-agent ─→ 4 config skills
                              │                        └──→ (Task) acc:test-pipeline-agent ───→ testing skills
                              │
                              ├── FIX ─────→ acc:ci-debugger ──────────→ 4 skills
                              │                        │                   └── analyze-ci-logs, detect-ci-antipatterns,
                              │                        │                       analyze-ci-config, discover-project-logs
                              │                        └──→ (Task) acc:ci-fixer ──→ generate-ci-fix skill
                              │
                              ├── OPTIMIZE → acc:pipeline-optimizer ───→ 3 skills
                              │                                          └── detect-ci-antipatterns, estimate-pipeline-time, optimize-docker-layers
                              │
                              └── AUDIT ───→ acc:ci-security-agent ────→ deployment-knowledge
                                             acc:deployment-agent ──────→ 2 deploy skills
                                                                          └── deploy-strategy, feature-flags

/acc:audit-docker ─────→ acc:docker-coordinator (opus, 4 skills)
                                │
                                ├──→ (Task) acc:docker-architect-agent ──→ 5 skills
                                │           └── multi-stage builds, BuildKit, Dockerfile production/dev
                                │
                                ├──→ (Task) acc:docker-image-builder ───→ 5 skills
                                │           └── base images, PHP extensions, Dockerfile, dockerignore
                                │
                                ├──→ (Task) acc:docker-compose-agent ───→ 6 skills
                                │           └── Compose config, networking, dev/production, env template
                                │
                                ├──→ (Task) acc:docker-performance-agent → 6 skills
                                │           └── build time, image size, OPcache, PHP-FPM, startup
                                │
                                ├──→ (Task) acc:docker-security-agent ──→ 6 skills
                                │           └── secrets, permissions, scanning, antipatterns
                                │
                                └──→ (Task) acc:docker-production-agent → 6 skills
                                            └── health checks, entrypoint, nginx, supervisor

/acc:explain ──────────→ acc:explain-coordinator (opus, 2 skills)
                                │
                                ├──→ (Task) acc:codebase-navigator ────→ 3 skills
                                │           └── scan-codebase-structure, identify-entry-points, detect-architecture-pattern
                                │
                                ├──→ (Task) acc:business-logic-analyst → 4 skills
                                │           └── extract-business-rules, explain-business-process,
                                │               extract-domain-concepts, extract-state-machine
                                │
                                ├──→ (Task) acc:data-flow-analyst ─────→ 4 skills
                                │           └── trace-request-lifecycle, trace-data-transformation,
                                │               map-async-flows, discover-project-logs
                                │
                                ├──→ (Task) acc:structural-auditor [REUSED, deep/onboarding]
                                ├──→ (Task) acc:behavioral-auditor [REUSED, deep/onboarding]
                                ├──→ (Task) acc:diagram-designer [REUSED, deep/onboarding/business]
                                └──→ (Task) acc:documentation-writer [REUSED, deep/onboarding/business]

/acc:generate-docker ──→ acc:docker-coordinator (opus, 4 skills)
                                │
                                ├── dockerfile → acc:docker-architect-agent
                                ├── compose ──→ acc:docker-compose-agent
                                ├── nginx ───→ acc:docker-production-agent
                                ├── entrypoint → acc:docker-production-agent
                                ├── makefile ─→ acc:docker-production-agent
                                ├── env ─────→ acc:docker-compose-agent
                                ├── healthcheck → acc:docker-production-agent
                                └── full ────→ All Docker agents (parallel)
```

## Audit → Generate Workflow

```
User: /acc:audit-architecture ./src
       ↓
Command loads acc:architecture-auditor agent
       ↓
Auditor analyzes project using knowledge skills
       ↓
Auditor generates report with recommendations
       ↓
Auditor asks "Generate code?"
       ↓
If yes → Task tool invokes generator agent
       ↓
Generator selects appropriate create-* skill
       ↓
Skill generates PHP code with tests
```

## Generator Mapping

| Issue Type | Generator Agent | Skills Used |
|------------|-----------------|-------------|
| DDD building blocks | `ddd-generator` | 11 create-* skills |
| CQRS/ES components | `cqrs-generator` | 6 create-* skills |
| Stability patterns | `stability-generator` | 6 create-* skills |
| Behavioral patterns | `behavioral-generator` | 10 create-* skills |
| GoF Structural patterns | `gof-structural-generator` | 6 create-* skills |
| Creational patterns | `creational-generator` | 3 create-* skills |
| Integration patterns | `integration-generator` | 11 create-* skills |
| PSR implementations | `psr-generator` | 11 create-psr* skills |
| Architecture | `architecture-generator` | Coordinator (delegates) |
| Design patterns | `pattern-generator` | Coordinator (delegates to 5 generators) |
| Bug fixes | `bug-fixer` | 5 bug-* skills + 6 quality + 1 log |

## Generator Skills by Category

### DDD Building Blocks (11 skills)

- `create-value-object` — Value Objects
- `create-entity` — Entities
- `create-aggregate` — Aggregates
- `create-domain-event` — Domain Events
- `create-repository` — Repository interfaces
- `create-domain-service` — Domain Services
- `create-factory` — Factories
- `create-specification` — Specifications
- `create-use-case` — Application Use Cases
- `create-dto` — DTOs
- `create-anti-corruption-layer` — Anti-Corruption Layer

### CQRS/ES (6 skills)

- `create-command` — CQRS Commands
- `create-query` — CQRS Queries
- `create-use-case` — Application Use Cases
- `create-event-store` — Event Store
- `create-snapshot` — Snapshots
- `create-read-model` — Read Models/Projections

### Stability Patterns (6 skills)

- `create-circuit-breaker` — Circuit Breaker
- `create-retry-pattern` — Retry with backoff
- `create-rate-limiter` — Rate limiting
- `create-bulkhead` — Bulkhead isolation
- `create-cache-aside` — Cache-Aside pattern
- `create-timeout` — Timeout pattern

### Integration Patterns (9 skills)

- `create-outbox-pattern` — Transactional Outbox
- `create-saga-pattern` — Saga orchestration
- `create-correlation-context` — Correlation ID propagation
- `create-unit-of-work` — Unit of Work
- `create-message-broker-adapter` — Message Broker Adapter
- `create-idempotent-consumer` — Idempotent Consumer
- `create-dead-letter-queue` — Dead Letter Queue
- `create-api-versioning` — API Versioning
- `create-health-check` — Health Check

### Behavioral Patterns (10 skills)

- `create-strategy` — Strategy pattern
- `create-state` — State machine
- `create-chain-of-responsibility` — Handler chains
- `create-decorator` — Decorator pattern
- `create-null-object` — Null Object pattern
- `create-policy` — Policy pattern
- `create-template-method` — Template Method pattern
- `create-visitor` — Visitor pattern
- `create-iterator` — Iterator pattern
- `create-memento` — Memento pattern

### GoF Structural Patterns (6 skills)

- `create-adapter` — Adapter pattern
- `create-facade` — Facade pattern
- `create-proxy` — Proxy pattern
- `create-composite` — Composite pattern
- `create-bridge` — Bridge pattern
- `create-flyweight` — Flyweight pattern

### Creational Patterns (3 skills)

- `create-builder` — Builder pattern
- `create-object-pool` — Object Pool
- `create-factory` — Factory pattern

### Enterprise Patterns (2 skills)

- `create-read-model` — CQRS Read Models
- `create-policy` — Policy pattern

### PSR Implementations (11 skills)

- `create-psr3-logger` — PSR-3 Logger Interface
- `create-psr6-cache` — PSR-6 Caching Interface
- `create-psr7-http-message` — PSR-7 HTTP Message Interface
- `create-psr11-container` — PSR-11 Container Interface
- `create-psr13-link` — PSR-13 Hypermedia Links
- `create-psr14-event-dispatcher` — PSR-14 Event Dispatcher
- `create-psr15-middleware` — PSR-15 HTTP Handlers/Middleware
- `create-psr16-simple-cache` — PSR-16 Simple Cache
- `create-psr17-http-factory` — PSR-17 HTTP Factories
- `create-psr18-http-client` — PSR-18 HTTP Client
- `create-psr20-clock` — PSR-20 Clock Interface

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Quick Reference →](quick-reference.md)
