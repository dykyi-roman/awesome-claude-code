# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.0] - 2026-02-04

### Added

#### Commands
- `/acc-code-review` - Multi-level code review with git diff analysis, task matching, and verdicts

#### Agents (6 new agents)
- `acc-code-review-coordinator` - Code review coordinator orchestrating review levels (low/medium/high)
- `acc-bug-hunter` - Bug detection specialist (logic errors, null pointers, race conditions, resource leaks) — 9 skills
- `acc-security-reviewer` - Security review specialist (input validation, auth, CSRF, crypto) — 9 skills
- `acc-performance-reviewer` - Performance review specialist (N+1 queries, memory, caching) — 8 skills
- `acc-readability-reviewer` - Readability review specialist (naming, style, method/class length) — 9 skills
- `acc-testability-reviewer` - Testability review specialist (DI, pure functions, side effects) — 7 skills

#### Bug Detection Skills (9)
- `acc-find-logic-errors` - Detects incorrect conditions, wrong operators, missing cases
- `acc-find-null-pointer-issues` - Detects null access, missing checks, nullable returns
- `acc-find-boundary-issues` - Detects off-by-one, array bounds, empty collections
- `acc-find-race-conditions` - Detects shared mutable state, concurrent access without locks
- `acc-find-resource-leaks` - Detects unclosed connections, file handles, streams
- `acc-find-exception-issues` - Detects swallowed exceptions, generic catches, missing finally
- `acc-find-type-issues` - Detects type coercion, mixed types, unsafe casts
- `acc-find-sql-injection` - Detects unescaped queries, SQL concatenation
- `acc-find-infinite-loops` - Detects missing break conditions, infinite recursion

#### Security Review Skills (9)
- `acc-check-input-validation` - Checks missing validation, weak regex, type coercion
- `acc-check-output-encoding` - Checks XSS vectors, missing HTML encoding
- `acc-check-authentication` - Checks weak auth, insecure sessions, tokens
- `acc-check-authorization` - Checks missing access control, IDOR vulnerabilities
- `acc-check-sensitive-data` - Checks plaintext secrets, exposed credentials, PII logging
- `acc-check-csrf-protection` - Checks missing CSRF tokens, GET state changes
- `acc-check-crypto-usage` - Checks weak algorithms, hardcoded keys
- `acc-check-dependency-vulnerabilities` - Checks outdated packages, known CVEs
- `acc-check-sql-injection` - Checks parameterized queries, ORM misuse

#### Performance Review Skills (8)
- `acc-detect-n-plus-one` - Detects queries in loops, missing eager loading
- `acc-check-query-efficiency` - Checks SELECT *, missing indexes, full table scans
- `acc-detect-memory-issues` - Checks large arrays, missing generators
- `acc-check-caching-strategy` - Checks missing cache, invalidation issues
- `acc-detect-unnecessary-loops` - Checks nested loops, redundant iterations
- `acc-check-lazy-loading` - Checks premature loading, missing pagination
- `acc-check-batch-processing` - Checks single-item vs bulk operations
- `acc-estimate-complexity` - Analyzes O(n²) algorithms, exponential growth

#### Readability Review Skills (9)
- `acc-check-naming` - Checks non-descriptive names, abbreviations
- `acc-check-code-style` - Checks PSR-12 compliance
- `acc-check-method-length` - Checks methods > 30 lines
- `acc-check-class-length` - Checks classes > 300 lines
- `acc-check-nesting-depth` - Checks > 3 levels of nesting
- `acc-check-comments` - Checks missing PHPDoc, outdated comments
- `acc-check-magic-values` - Checks hardcoded values without constants
- `acc-check-consistency` - Checks inconsistent patterns, mixed styles
- `acc-suggest-simplification` - Suggests extract method, introduce variable

#### Testability Review Skills (5 new)
- `acc-check-dependency-injection` - Checks constructor injection, missing interfaces
- `acc-check-pure-functions` - Checks side effects, external dependencies
- `acc-check-side-effects` - Checks state mutation, global access
- `acc-check-test-quality` - Checks test structure, assertions, isolation
- `acc-suggest-testability-improvements` - Suggests DI refactoring, mock opportunities

### Changed
- Updated component counts: 11 commands, 29 agents, 127 skills

## [2.4.0] - 2026-02-03

### Added

#### Commands
- `/acc-write-test` - Generate tests for PHP file/folder (unit, integration, builders, mocks)
- `/acc-audit-test` - Audit test quality (coverage gaps, test smells, naming, isolation)
- `/acc-write-documentation` - Generate documentation for file/folder (README, architecture, diagrams)
- `/acc-audit-documentation` - Audit documentation quality (completeness, accuracy, clarity)

#### Agents (15 new agents)
- `acc-structural-auditor` - Structural architecture auditor (DDD, Clean, Hexagonal, Layered, SOLID, GRASP) — 12 skills (6 knowledge + 6 analyzer)
- `acc-behavioral-auditor` - Behavioral patterns auditor (CQRS, Event Sourcing, EDA, Strategy, State, etc.) — 12 skills
- `acc-integration-auditor` - Integration patterns auditor (Outbox, Saga, ADR) — 12 skills
- `acc-stability-auditor` - Stability patterns auditor (Circuit Breaker, Retry, Rate Limiter, Bulkhead) — 5 skills
- `acc-creational-auditor` - Creational patterns auditor (Builder, Object Pool, Factory) — 3 skills
- `acc-stability-generator` - Stability patterns generator — 5 skills
- `acc-behavioral-generator` - Behavioral patterns generator (Strategy, State, Chain, Decorator, Null Object) — 5 skills
- `acc-creational-generator` - Creational patterns generator — 3 skills
- `acc-integration-generator` - Integration patterns generator (Outbox, Saga, Action, Responder) — 7 skills
- `acc-test-auditor` - Test quality auditor (coverage analysis, smell detection, quality metrics)
- `acc-test-generator` - Test generator for DDD/CQRS projects (unit, integration, builders, mocks)
- `acc-documentation-writer` - Technical documentation writer (README, architecture, API docs, ADRs)
- `acc-documentation-auditor` - Documentation quality auditor
- `acc-diagram-designer` - Mermaid diagram designer (C4, sequence, class, ER diagrams)
- `acc-psr-auditor` - PSR compliance auditor for `/acc-audit-psr` command

#### Knowledge Skills
- `acc-testing-knowledge` - Testing pyramid, AAA pattern, naming conventions, isolation, DDD testing
- `acc-documentation-knowledge` - Documentation types, audiences, best practices, antipatterns
- `acc-diagram-knowledge` - Mermaid syntax, C4 model, diagram types, best practices
- `acc-documentation-qa-knowledge` - Quality checklists, audit criteria, scoring metrics

#### Analyzer Skills (8 new)
- `acc-analyze-test-coverage` - Detects untested classes, methods, branches, exception paths
- `acc-detect-test-smells` - Detects 15 test antipatterns (logic in test, mock overuse, etc.)
- `acc-detect-code-smells` - Detects God Class, Feature Envy, Data Clumps, Long Parameter List, Long Method, Primitive Obsession, Message Chains, Inappropriate Intimacy
- `acc-check-bounded-contexts` - Analyzes DDD bounded context boundaries, cross-context coupling, shared kernel violations, context mapping issues
- `acc-check-immutability` - Checks Value Objects, Events, DTOs for readonly properties, no setters, final classes, wither patterns
- `acc-check-leaky-abstractions` - Detects leaky abstractions, implementation details in interfaces, framework leakage into domain
- `acc-check-encapsulation` - Detects public mutable state, exposed internals, Tell Don't Ask violations, getter/setter abuse
- `acc-analyze-coupling-cohesion` - Analyzes coupling/cohesion metrics (Afferent/Efferent coupling Ca/Ce, LCOM, instability index)

#### Generator Skills
- `acc-create-unit-test` - PHPUnit unit tests with AAA pattern, proper naming, attributes
- `acc-create-integration-test` - Integration tests with database transactions, HTTP mocking
- `acc-create-test-builder` - Test Data Builder and Object Mother patterns
- `acc-create-mock-repository` - InMemory repository implementations for testing
- `acc-create-test-double` - Mocks, Stubs, Fakes, Spies with decision matrix

#### Template Skills
- `acc-readme-template` - README.md generation with badges, sections, examples
- `acc-architecture-doc-template` - ARCHITECTURE.md with layers, components, diagrams
- `acc-adr-template` - Architecture Decision Records (context, decision, consequences)
- `acc-api-doc-template` - API documentation (endpoints, params, responses)
- `acc-getting-started-template` - Quick start guides, tutorials
- `acc-troubleshooting-template` - FAQ and troubleshooting sections
- `acc-code-examples-template` - Code examples (minimal, complete, progressive)
- `acc-mermaid-template` - Mermaid diagram templates for all types
- `acc-changelog-template` - Keep a Changelog format

#### Hooks (10 ready-to-use)
- Auto-format PHP - runs `php-cs-fixer` on PHP files after editing
- Require strict_types - blocks PHP files without `declare(strict_types=1)`
- Protect vendor/ - prevents modification of vendor/ directory
- PHP Syntax Check - validates PHP syntax after editing
- Auto-run Tests - runs PHPUnit tests for modified class
- Final Domain Classes - warns if Domain class not final
- File Size Check - detects God Class antipattern (>300 lines)
- No Direct Commits - forbids commits to main/master branches
- Protect Migrations - prevents editing existing migrations
- Test Without Source - warns when changing only tests

#### MCP Documentation
- `docs/mcp.md` - Model Context Protocol servers guide
- Database MCP (PostgreSQL/MySQL) - query databases, validate Entity/table mapping
- Configuration examples for Docker environments

#### Configuration
- `settings.json` - Shared team-wide settings with hooks and permissions

#### Documentation
- `docs/hooks.md` - Full hooks documentation with installation guide
- `docs/mcp.md` - MCP servers documentation with DDD use cases

#### Features
- **Meta-instructions support** for all commands via `--` separator
  - Allows passing additional context to any command
  - Examples: `/acc-audit-ddd ./src -- focus on aggregate boundaries`
  - Supports language customization: `/acc-commit -- use Russian for commit message`

### Changed
- **Decomposed `acc-architecture-auditor`** from 42 skills to coordinator pattern (0 skills)
  - Now delegates to 3 specialized auditors via Task tool (parallel execution)
  - Cross-pattern conflict analysis between structural/behavioral/integration domains
- **Refactored `acc-pattern-auditor`** from 24 skills to coordinator pattern (2 knowledge skills)
  - Now delegates to 4 specialized auditors via Task tool
  - Prevents God-Agent antipattern (max 15 skills per agent rule)
- **Refactored `acc-pattern-generator`** from 23 skills to coordinator pattern (1 skill)
  - Now delegates to 4 specialized generators via Task tool
- **Reduced `acc-ddd-auditor`** from 16 to 3 skills (knowledge only)
  - Generation delegated to `acc-ddd-generator` via Task tool
- **Reduced `acc-structural-auditor`** from 16 to 6 knowledge skills, then extended to 12 skills (added 6 analyzer skills: solid-violations, code-smells, bounded-contexts, immutability, leaky-abstractions, encapsulation)
- **Extended `acc-behavioral-auditor`** to include GoF patterns (Strategy, State, Chain, Decorator, Null Object) and immutability checks — now 13 skills
- **Extended `acc-pattern-auditor`** from 2 to 3 skills (added coupling/cohesion analysis)
- **Extended `acc-ddd-auditor`** from 3 to 4 skills (added bounded context analysis)
- Renamed `/acc-claude-code` to `/acc-write-claude-component` for consistency
- Updated component counts: 10 commands, 23 agents, 87 skills

## Note: See [2.5.0] for Code Review system additions

## [2.3.0] - 2026-02-02

### Added

#### Commands
- `/acc-audit-psr` - PSR compliance audit (PSR-1/12 coding style, PSR-4 autoloading, PSR interfaces)

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

## [2.2.0] - 2026-01-31

### Added

#### Commands
- `/acc-audit-claude-code` - audit .claude folder structure and configuration quality

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

## [2.1.0] - 2026-01-30

### Added

#### Commands
- `/acc-audit-architecture` - comprehensive multi-pattern architecture audit
- `/acc-audit-ddd` - DDD compliance analysis for PHP projects

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

## [2.0.0] - 2026-01-29

### Added

- Composer plugin for auto-copying Claude Code components
- Command `/acc-write-claude-component` - interactive wizard for creating commands, agents, skills, hooks
- Command `/acc-commit` - auto-generate commit message and push
- Agent `acc-claude-code-expert` - expert in Claude Code architecture
- Skill `acc-claude-code-knowledge` - knowledge base for formats and patterns
- Comprehensive documentation in `.claude/README.md`

## [1.0.0] - 2026-01-28

### Added

- Initial release
- Project structure and Composer package setup

[Unreleased]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.5.0...HEAD
[2.5.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.4.0...v2.5.0
[2.4.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.3.0...v2.4.0
[2.3.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.2.0...v2.3.0
[2.2.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.1.0...v2.2.0
[2.1.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v2.0.0...v2.1.0
[2.0.0]: https://github.com/dykyi-roman/awesome-claude-code/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/dykyi-roman/awesome-claude-code/releases/tag/v1.0.0