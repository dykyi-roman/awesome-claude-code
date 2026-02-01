# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0] - 2026-02-01

### Added

#### Commands
- `/acc-psr-audit` - PSR compliance audit (PSR-1/12 coding style, PSR-4 autoloading, PSR interfaces)

#### Agents
- `acc-psr-generator` - Generates PSR-compliant PHP components (11 skills)

#### Knowledge Skills
- `acc-solid-knowledge` - SOLID principles (SRP, OCP, LSP, ISP, DIP) with detection patterns and PHP examples
- `acc-grasp-knowledge` - 9 GRASP patterns (Information Expert, Creator, Controller, Low Coupling, High Cohesion, Polymorphism, Pure Fabrication, Indirection, Protected Variations)
- `acc-psr-coding-style-knowledge` - PSR-1/PSR-12 coding standards
- `acc-psr-autoloading-knowledge` - PSR-4 autoloading standard
- `acc-psr-overview-knowledge` - All PSR standards overview
- `acc-adr-knowledge` - Action-Domain-Responder pattern (web-specific MVC alternative)

#### Analyzer Skills
- `acc-analyze-solid-violations` - SOLID violations analyzer with severity levels and remediation recommendations

#### Generator Skills
- `acc-create-di-container` - DI Container configuration (modules, service providers, autowiring)
- `acc-create-mediator` - Mediator pattern for component coordination
- `acc-create-psr3-logger` - PSR-3 Logger Interface implementation
- `acc-create-psr6-cache` - PSR-6 Caching Interface implementation
- `acc-create-psr7-http-message` - PSR-7 HTTP Message Interface implementation
- `acc-create-psr11-container` - PSR-11 Container Interface implementation
- `acc-create-psr13-link` - PSR-13 Hypermedia Links implementation
- `acc-create-psr14-event-dispatcher` - PSR-14 Event Dispatcher implementation
- `acc-create-psr15-middleware` - PSR-15 HTTP Middleware implementation
- `acc-create-psr16-simple-cache` - PSR-16 Simple Cache implementation
- `acc-create-psr17-http-factory` - PSR-17 HTTP Factories implementation
- `acc-create-psr18-http-client` - PSR-18 HTTP Client implementation
- `acc-create-psr20-clock` - PSR-20 Clock Interface implementation
- `acc-create-action` - ADR Action classes for HTTP endpoints
- `acc-create-responder` - ADR Responder classes for HTTP response building

### Changed
- Updated `acc-architecture-auditor` to include SOLID, GRASP, and ADR knowledge skills
- Updated `acc-ddd-auditor` to include SOLID and GRASP knowledge skills
- Updated `acc-pattern-generator` to include DI Container, Mediator, Action, and Responder skills
- Updated `acc-pattern-auditor` to include SOLID/GRASP knowledge and analyzer skills

## [2.1.0] - 2026-01-31

### Added

#### Commands
- `/acc-claude-code-audit` - audit .claude folder structure and configuration quality

#### Agents
- `acc-architecture-generator` - meta-generator coordinating DDD and pattern generators
- `acc-pattern-auditor` - design and integration patterns auditor
- `acc-pattern-generator` - creates integration and design pattern components

#### Knowledge Skills
- `acc-outbox-pattern-knowledge` - Outbox pattern, polling publisher, reliable messaging
- `acc-saga-pattern-knowledge` - Saga orchestration, choreography, compensation
- `acc-stability-patterns-knowledge` - Circuit Breaker, Retry, Rate Limiter, Bulkhead

#### Generator Skills
- `acc-create-dto` - generates DTOs for layer boundaries and APIs
- `acc-create-specification` - generates DDD Specifications with composite pattern
- `acc-create-factory` - generates DDD Factories for complex object creation
- `acc-create-domain-service` - generates DDD Domain Services
- `acc-create-outbox-pattern` - generates Transactional Outbox components
- `acc-create-saga-pattern` - generates Saga orchestration components
- `acc-create-circuit-breaker` - generates Circuit Breaker pattern
- `acc-create-retry-pattern` - generates Retry pattern with backoff
- `acc-create-rate-limiter` - generates Rate Limiter pattern
- `acc-create-bulkhead` - generates Bulkhead pattern for isolation
- `acc-create-strategy` - generates Strategy pattern
- `acc-create-state` - generates State pattern
- `acc-create-decorator` - generates Decorator pattern
- `acc-create-chain-of-responsibility` - generates Chain of Responsibility pattern
- `acc-create-builder` - generates Builder pattern
- `acc-create-null-object` - generates Null Object pattern
- `acc-create-object-pool` - generates Object Pool pattern
- `acc-create-anti-corruption-layer` - generates ACL components
- `acc-create-read-model` - generates Read Model/Projection for CQRS
- `acc-create-policy` - generates Policy pattern

### Changed
- Refactored 22 skills to use `references/` folder structure (under 500 lines each)
- Skills now have `templates.md` and `examples.md` in references folder

## [2.0.0] - 2026-01-30

### Added

#### Commands
- `/acc-architecture-audit` - comprehensive multi-pattern architecture audit
- `/acc-ddd-audit` - DDD compliance analysis for PHP projects

#### Agents
- `acc-architecture-auditor` - multi-pattern architecture auditor (DDD, CQRS, Clean, Hexagonal, Layered, EDA, Event Sourcing)
- `acc-ddd-auditor` - specialized DDD compliance auditor
- `acc-ddd-generator` - creates DDD and architecture components

#### Knowledge Skills (for audits)
- `acc-ddd-knowledge` - DDD patterns, antipatterns, PHP guidelines
- `acc-cqrs-knowledge` - CQRS patterns, command/query separation
- `acc-clean-arch-knowledge` - Clean Architecture, dependency rules
- `acc-hexagonal-knowledge` - Hexagonal/Ports & Adapters patterns
- `acc-layer-arch-knowledge` - Layered Architecture, DTO patterns
- `acc-event-sourcing-knowledge` - Event Sourcing, projections, snapshots
- `acc-eda-knowledge` - Event-Driven Architecture, messaging, sagas

#### Generator Skills (for code generation)
- `acc-create-value-object` - generates DDD Value Objects with tests
- `acc-create-entity` - generates DDD Entities with tests
- `acc-create-aggregate` - generates DDD Aggregates with tests
- `acc-create-domain-event` - generates Domain Events with tests
- `acc-create-repository` - generates Repository interfaces and stubs
- `acc-create-command` - generates CQRS Commands and Handlers
- `acc-create-query` - generates CQRS Queries and Handlers
- `acc-create-use-case` - generates Application Use Cases

## [1.0.0] - 2026-01-29

### Added

- Initial release
- Composer plugin for auto-copying Claude Code components
- Command `/acc-claude-code` - interactive wizard for creating commands, agents, skills, hooks
- Command `/acc-commit` - auto-generate commit message and push
- Agent `acc-claude-code-expert` - expert in Claude Code architecture
- Skill `acc-claude-code-knowledge` - knowledge base for formats and patterns
- Comprehensive documentation in `.claude/README.md`

[Unreleased]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.2.0...HEAD
[2.2.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/dykyi-roman/awesome-claude-code/releases/tag/v1.0.0
