# Component Flow

How commands, agents, and skills interact. This document shows the dependency graph and execution flow.

## Architecture Overview

```
User Input → Command → Agent(s) → Skills → Output
```

1. **User** invokes a slash command (e.g., `/acc-audit-architecture`)
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
/acc-commit ────────────→ (direct Bash)

/acc-generate-claude-component ───────→ acc-claude-code-expert ───→ acc-claude-code-knowledge

/acc-audit-claude-components → (direct analysis)

/acc-audit-ddd ─────────→ acc-ddd-auditor (8 skills) ──→ DDD, SOLID, GRASP knowledge + 3 analyzers
                                │
                                └──→ (Task) acc-ddd-generator ──→ 13 create-* skills

/acc-audit-architecture ─→ acc-architecture-auditor (coordinator)
                                │
                                ├──→ (Task) acc-structural-auditor ──→ 12 skills
                                │           └── DDD, Clean, Hexagonal, Layered, SOLID, GRASP + 6 analyzers
                                │
                                ├──→ (Task) acc-behavioral-auditor ──→ 11 skills
                                │           └── Strategy, State, Chain, Decorator, Null Object, etc.
                                │
                                ├──→ (Task) acc-integration-auditor ─→ 12 skills
                                │           └── Outbox, Saga, ADR
                                │
                                ├──→ (Task) acc-ddd-generator
                                └──→ (Task) acc-pattern-generator (coordinator)
                                                  │
                                                  ├──→ (Task) acc-stability-generator ──→ 5 skills
                                                  ├──→ (Task) acc-behavioral-generator ─→ 10 skills
                                                  ├──→ (Task) acc-gof-structural-generator → 6 skills
                                                  ├──→ (Task) acc-creational-generator ─→ 3 skills
                                                  └──→ (Task) acc-integration-generator → 8 skills

/acc-audit-patterns ────→ acc-pattern-auditor (coordinator, 2 skills)
                                │
                                ├──→ (Task) acc-stability-auditor ───→ 9 skills
                                │           └── Circuit Breaker, Retry, Rate Limiter, Bulkhead,
                                │               Timeout, Cascading Failures, Fallback
                                │
                                ├──→ (Task) acc-behavioral-auditor ──→ 11 skills
                                │           └── Strategy, State, Chain, Decorator, Null Object,
                                │               Template Method, Visitor, Iterator, Memento
                                │
                                ├──→ (Task) acc-gof-structural-auditor → 6 skills
                                │           └── Adapter, Facade, Proxy, Composite, Bridge, Flyweight
                                │
                                ├──→ (Task) acc-creational-auditor ──→ 7 skills
                                │           └── Builder, Object Pool, Factory, Singleton (anti),
                                │               Abstract Factory, Prototype
                                │
                                └──→ (Task) acc-integration-auditor ─→ 12 skills
                                            └── Outbox, Saga, ADR

/acc-audit-psr ─────────→ acc-psr-auditor ─────────→ 3 PSR knowledge skills
                                │
                                └──→ (Skill) 11 PSR create-* skills

/acc-generate-documentation → acc-documentation-writer ─→ 8 template skills
                                │
                                └──→ (Task) acc-diagram-designer ─→ 2 diagram skills

/acc-audit-documentation → acc-documentation-auditor → 7 skills (3 knowledge + 3 analyzers + progress)

/acc-generate-test ────────→ acc-test-generator ────────→ acc-testing-knowledge
                                                       5 test create-* skills

/acc-audit-test ────────→ acc-test-auditor ──────────→ acc-testing-knowledge
                                │                      2 test analyze skills
                                └──→ (Task) acc-test-generator

/acc-bug-fix ──────────→ acc-bug-fix-coordinator
                                │
                                ├──→ (Task) acc-bug-hunter ─────────→ 11 skills (9 detection + 2 log analysis)
                                │           └── logic, null, boundary, race, resource, exception, type, sql, infinite
                                │           └── discover-project-logs, analyze-php-logs
                                │
                                ├──→ (Task) acc-bug-fixer ──────────→ 12 skills (5 fix + 6 quality + 1 log)
                                │           └── fix-knowledge, root-cause, impact, generate-fix, regression-preventer
                                │           └── code-smells, memory, solid, encapsulation, side-effects, immutability
                                │           └── analyze-php-logs
                                │
                                └──→ (Task) acc-test-generator ─────→ 6 test skills

/acc-ci-setup ────────→ acc-ci-coordinator (mode: SETUP)
/acc-ci-fix ──────────→       │
/acc-ci-optimize ─────→       │
/acc-audit-ci ────────→       │
                              │
                              ├── SETUP ────→ acc-pipeline-architect ──→ 3 knowledge skills
                              │                        │                   └── ci-pipeline, ci-tools, deployment
                              │                        └──→ (Task) acc-docker-agent ──→ 2 docker skills
                              │                        └──→ (Task) acc-static-analysis-agent ─→ 4 config skills
                              │                        └──→ (Task) acc-test-pipeline-agent ───→ testing skills
                              │
                              ├── FIX ─────→ acc-ci-debugger ──────────→ 4 skills
                              │                        │                   └── analyze-ci-logs, detect-ci-antipatterns,
                              │                        │                       analyze-ci-config, discover-project-logs
                              │                        └──→ (Task) acc-ci-fixer ──→ generate-ci-fix skill
                              │
                              ├── OPTIMIZE → acc-pipeline-optimizer ───→ 3 skills
                              │                                          └── detect-ci-antipatterns, estimate-pipeline-time, optimize-docker-layers
                              │
                              └── AUDIT ───→ acc-ci-security-agent ────→ deployment-knowledge
                                             acc-deployment-agent ──────→ 2 deploy skills
                                                                          └── deploy-strategy, feature-flags

/acc-audit-docker ─────→ acc-docker-coordinator (opus, 4 skills)
                                │
                                ├──→ (Task) acc-docker-architect-agent ──→ 5 skills
                                │           └── multi-stage builds, BuildKit, Dockerfile production/dev
                                │
                                ├──→ (Task) acc-docker-image-builder ───→ 5 skills
                                │           └── base images, PHP extensions, Dockerfile, dockerignore
                                │
                                ├──→ (Task) acc-docker-compose-agent ───→ 6 skills
                                │           └── Compose config, networking, dev/production, env template
                                │
                                ├──→ (Task) acc-docker-performance-agent → 6 skills
                                │           └── build time, image size, OPcache, PHP-FPM, startup
                                │
                                ├──→ (Task) acc-docker-security-agent ──→ 6 skills
                                │           └── secrets, permissions, scanning, antipatterns
                                │
                                └──→ (Task) acc-docker-production-agent → 6 skills
                                            └── health checks, entrypoint, nginx, supervisor

/acc-explain ──────────→ acc-explain-coordinator (opus, 2 skills)
                                │
                                ├──→ (Task) acc-codebase-navigator ────→ 3 skills
                                │           └── scan-codebase-structure, identify-entry-points, detect-architecture-pattern
                                │
                                ├──→ (Task) acc-business-logic-analyst → 4 skills
                                │           └── extract-business-rules, explain-business-process,
                                │               extract-domain-concepts, extract-state-machine
                                │
                                ├──→ (Task) acc-data-flow-analyst ─────→ 4 skills
                                │           └── trace-request-lifecycle, trace-data-transformation,
                                │               map-async-flows, discover-project-logs
                                │
                                ├──→ (Task) acc-structural-auditor [REUSED, deep/onboarding]
                                ├──→ (Task) acc-behavioral-auditor [REUSED, deep/onboarding]
                                ├──→ (Task) acc-diagram-designer [REUSED, deep/onboarding/business]
                                └──→ (Task) acc-documentation-writer [REUSED, deep/onboarding/business]

/acc-generate-docker ──→ acc-docker-coordinator (opus, 4 skills)
                                │
                                ├── dockerfile → acc-docker-architect-agent
                                ├── compose ──→ acc-docker-compose-agent
                                ├── nginx ───→ acc-docker-production-agent
                                ├── entrypoint → acc-docker-production-agent
                                ├── makefile ─→ acc-docker-production-agent
                                ├── env ─────→ acc-docker-compose-agent
                                ├── healthcheck → acc-docker-production-agent
                                └── full ────→ All Docker agents (parallel)
```

## Audit → Generate Workflow

```
User: /acc-audit-architecture ./src
       ↓
Command loads acc-architecture-auditor agent
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
| DDD components | `acc-ddd-generator` | 13 acc-create-* skills |
| Stability patterns | `acc-stability-generator` | 5 acc-create-* skills |
| Behavioral patterns | `acc-behavioral-generator` | 10 acc-create-* skills |
| GoF Structural patterns | `acc-gof-structural-generator` | 6 acc-create-* skills |
| Creational patterns | `acc-creational-generator` | 3 acc-create-* skills |
| Integration patterns | `acc-integration-generator` | 8 acc-create-* skills |
| PSR implementations | `acc-psr-generator` | 11 acc-create-psr* skills |
| Architecture | `acc-architecture-generator` | Coordinator (delegates) |
| Design patterns | `acc-pattern-generator` | Coordinator (delegates to 5 generators) |
| Bug fixes | `acc-bug-fixer` | 5 acc-bug-* skills + 6 quality + 1 log |

## Generator Skills by Category

### DDD (13 skills)

- `acc-create-value-object` — Value Objects
- `acc-create-entity` — Entities
- `acc-create-aggregate` — Aggregates
- `acc-create-domain-event` — Domain Events
- `acc-create-repository` — Repository interfaces
- `acc-create-command` — CQRS Commands
- `acc-create-query` — CQRS Queries
- `acc-create-use-case` — Application Use Cases
- `acc-create-domain-service` — Domain Services
- `acc-create-factory` — Factories
- `acc-create-specification` — Specifications
- `acc-create-dto` — DTOs
- `acc-create-anti-corruption-layer` — Anti-Corruption Layer

### Stability Patterns (4 skills)

- `acc-create-circuit-breaker` — Circuit Breaker
- `acc-create-retry-pattern` — Retry with backoff
- `acc-create-rate-limiter` — Rate limiting
- `acc-create-bulkhead` — Bulkhead isolation

### Integration Patterns (3 skills)

- `acc-create-outbox-pattern` — Transactional Outbox
- `acc-create-saga-pattern` — Saga orchestration
- `acc-create-correlation-context` — Correlation ID propagation

### Behavioral Patterns (10 skills)

- `acc-create-strategy` — Strategy pattern
- `acc-create-state` — State machine
- `acc-create-chain-of-responsibility` — Handler chains
- `acc-create-decorator` — Decorator pattern
- `acc-create-null-object` — Null Object pattern
- `acc-create-policy` — Policy pattern
- `acc-create-template-method` — Template Method pattern
- `acc-create-visitor` — Visitor pattern
- `acc-create-iterator` — Iterator pattern
- `acc-create-memento` — Memento pattern

### GoF Structural Patterns (6 skills)

- `acc-create-adapter` — Adapter pattern
- `acc-create-facade` — Facade pattern
- `acc-create-proxy` — Proxy pattern
- `acc-create-composite` — Composite pattern
- `acc-create-bridge` — Bridge pattern
- `acc-create-flyweight` — Flyweight pattern

### Creational Patterns (2 skills)

- `acc-create-builder` — Builder pattern
- `acc-create-object-pool` — Object Pool

### Enterprise Patterns (2 skills)

- `acc-create-read-model` — CQRS Read Models
- `acc-create-policy` — Policy pattern

### PSR Implementations (11 skills)

- `acc-create-psr3-logger` — PSR-3 Logger Interface
- `acc-create-psr6-cache` — PSR-6 Caching Interface
- `acc-create-psr7-http-message` — PSR-7 HTTP Message Interface
- `acc-create-psr11-container` — PSR-11 Container Interface
- `acc-create-psr13-link` — PSR-13 Hypermedia Links
- `acc-create-psr14-event-dispatcher` — PSR-14 Event Dispatcher
- `acc-create-psr15-middleware` — PSR-15 HTTP Handlers/Middleware
- `acc-create-psr16-simple-cache` — PSR-16 Simple Cache
- `acc-create-psr17-http-factory` — PSR-17 HTTP Factories
- `acc-create-psr18-http-client` — PSR-18 HTTP Client
- `acc-create-psr20-clock` — PSR-20 Clock Interface

---

## Navigation

[← Back to README](../README.md) | [Commands](commands.md) | [Agents](agents.md) | [Skills](skills.md) | [Quick Reference →](quick-reference.md)
