# Awesome Claude Code - DDD & Clean Architecture Generator for PHP

[![Latest Version on Packagist](https://img.shields.io/packagist/v/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![Total Downloads](https://img.shields.io/packagist/dt/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![PHP 8.5](https://img.shields.io/badge/PHP-8.5-blue?style=flat-square)](https://php.net)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Extension-purple?style=flat-square)](https://claude.ai/code)
[![DDD](https://img.shields.io/badge/DDD-Ready-green?style=flat-square)](https://en.wikipedia.org/wiki/Domain-driven_design)
[![CQRS](https://img.shields.io/badge/CQRS-Ready-orange?style=flat-square)](https://martinfowler.com/bliki/CQRS.html)
[![License](https://img.shields.io/packagist/l/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![GitHub Stars](https://img.shields.io/github/stars/dykyi-roman/awesome-claude-code?style=flat-square)](https://github.com/dykyi-roman/awesome-claude-code)
[![Last Commit](https://img.shields.io/github/last-commit/dykyi-roman/awesome-claude-code?style=flat-square)](https://github.com/dykyi-roman/awesome-claude-code)

> **The most comprehensive Claude Code extension for PHP developers.**
> Auto-generate DDD components, audit architecture, generate documentation, and boost productivity with 73 skills and 12 agents.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Requirements](#requirements)
- [Quick Start](#quick-start)
- [Use Cases](#use-cases)
- [Overview](#overview)
- [Commands](#commands)
- [Agents](#agents)
- [Skills](#skills)
- [Component Flow](#component-flow)
- [Supported Patterns](#supported-patterns)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

## Features

- **73 Skills** — DDD, CQRS, Clean Architecture, Stability Patterns, PSR implementations, Documentation, SOLID/GRASP audits
- **Architecture Audit** — Automated compliance checking for 10+ patterns
- **Zero Config** — Auto-installs to `.claude/` directory via Composer
- **Tested Patterns** — Unit tests included for all generators
- **Knowledge Bases** — Deep expertise in DDD, CQRS, Hexagonal, EDA, Stability patterns

## Demo

### Architecture Audit

```bash
/acc-audit-architecture ./src
```

```
📊 Architecture Audit Report
├── Pattern: DDD + CQRS detected
├── Compliance: 87%
├── Issues: 3 warnings
│   ├── Domain layer has infrastructure dependency (UserRepository.php:45)
│   ├── Missing aggregate root for Order context
│   └── Query handler modifies state (GetUserHandler.php:23)
└── Recommendations: 5 suggestions
    ├── Extract OrderAggregate from Order entity
    ├── Move repository implementation to Infrastructure
    └── ... (3 more)
```

### Code Generation

```bash
/acc-claude-code
> What would you like to create? Entity
> Entity name? User
> Properties? id:UserId, email:Email, name:string
```

Generates:
- `src/Domain/User/User.php` — Entity with validation
- `src/Domain/User/UserRepositoryInterface.php` — Repository interface
- `tests/Unit/Domain/User/UserTest.php` — Unit tests

### PSR Compliance Check

```bash
/acc-audit-psr ./src
```

```
📋 PSR Compliance Report
├── PSR-1: ✅ Passed
├── PSR-4: ✅ Passed
├── PSR-12: ⚠️ 2 warnings
│   ├── Line too long (UserService.php:89)
│   └── Missing blank line after namespace
└── PSR Interfaces: 3 implementations detected
```

## Why Use This?

| Without | With Awesome Claude Code |
|---------|--------------------------|
| Manual boilerplate code | One command generates complete component |
| Architecture drift | Automated compliance audits |
| Inconsistent patterns | Standardized DDD/CQRS templates |
| Hours of setup | Instant productivity |
| Learning curve | Built-in knowledge bases |

## Requirements

- **PHP 8.5+** — for generated code (strict typing, readonly classes)
- **Composer 2.0+** — for package installation
- **Claude Code CLI** — [Installation guide](https://docs.anthropic.com/en/docs/claude-code)

## Quick Start

```bash
composer require dykyi-roman/awesome-claude-code
```

Then in Claude Code:

```
/acc-audit-architecture ./src
```

Components are **automatically copied** to your project's `.claude/` directory:
- `commands/` — slash commands
- `agents/` — subagents
- `skills/` — knowledge bases and generators

Existing files are not overwritten.

## Use Cases

| Scenario | Command | Result |
|----------|---------|--------|
| Audit existing architecture | `/acc-audit-architecture ./src` | Full compliance report with recommendations |
| Create DDD entity | `/acc-claude-code` → Entity | Entity + Repository interface + Unit tests |
| Generate Value Object | `/acc-claude-code` → Value Object | Immutable VO with validation + tests |
| Check PSR compliance | `/acc-audit-psr ./src` | Coding standards report (PSR-1, 4, 12) |
| Generate documentation | `/acc-write-documentation` | README + ARCHITECTURE.md + diagrams |
| Audit documentation quality | `/acc-audit-documentation ./docs` | Completeness and accuracy report |
| Create stability pattern | `/acc-claude-code` → Circuit Breaker | Pattern implementation + tests |
| DDD-specific audit | `/acc-audit-ddd ./src` | Domain model analysis + suggestions |

## Overview

| Component | Count | Description |
|-----------|-------|-------------|
| Commands | 8 | Slash commands for audits, generation, commits |
| Agents | 11 | Specialized subagents for complex tasks |
| Skills | 73 | Knowledge bases, code generators, templates |

## Documentation

- [Commands](docs/commands.md) — 8 slash commands
- [Agents](docs/agents.md) — 11 subagents
- [Skills](docs/skills.md) — 73 skills (knowledge + generators + templates)
- [Component Flow](docs/component-flow.md) — dependency graph and workflows
- [Quick Reference](docs/quick-reference.md) — paths, formats, best practices

## Commands

| Command                     | Description                                                       |
|-----------------------------|-------------------------------------------------------------------|
| `/acc-commit`               | Auto-generate commit message from diff and push to current branch |
| `/acc-claude-code`          | Interactive wizard for creating commands, agents, skills, hooks   |
| `/acc-audit-claude-code`    | Audit `.claude/` folder structure and configuration quality       |
| `/acc-audit-architecture`   | Comprehensive multi-pattern architecture audit for PHP projects   |
| `/acc-audit-ddd`            | DDD compliance analysis for PHP projects                          |
| `/acc-audit-psr`            | PSR compliance audit (coding style, autoloading, interfaces)      |
| `/acc-write-documentation`  | Generate README, architecture docs, Mermaid diagrams              |
| `/acc-audit-documentation`  | Audit documentation quality (completeness, accuracy, clarity)     |

## Agents

| Agent                        | Description                                                                               |
|------------------------------|-------------------------------------------------------------------------------------------|
| `acc-claude-code-expert`     | Expert in Claude Code architecture and extensions                                         |
| `acc-architecture-auditor`   | Multi-pattern architecture auditor (DDD, CQRS, Clean, Hexagonal, Layered, EDA, Stability) |
| `acc-architecture-generator` | Generates architecture components based on detected patterns                              |
| `acc-pattern-auditor`        | Audits implementation patterns (Saga, Outbox, Stability, Behavioral)                      |
| `acc-pattern-generator`      | Generates advanced pattern components                                                     |
| `acc-ddd-auditor`            | Specialized DDD compliance auditor                                                        |
| `acc-ddd-generator`          | Creates DDD and architecture components                                                   |
| `acc-psr-generator`          | Generates PSR-compliant PHP components                                                    |
| `acc-documentation-writer`   | Technical documentation writer (README, architecture, API docs)                           |
| `acc-documentation-auditor`  | Documentation quality auditor (completeness, accuracy, clarity)                           |
| `acc-diagram-designer`       | Diagram designer for Mermaid, C4 models, sequence diagrams                                |

## Skills

### Skills by Category

| Category | Count | Examples |
|----------|-------|----------|
| Knowledge | 20 | DDD, CQRS, Clean Architecture, SOLID, GRASP, PSR |
| Analyzer | 1 | SOLID violations analyzer |
| DDD Generators | 10 | Entity, ValueObject, Aggregate, Repository |
| CQRS Generators | 4 | Command, Query, UseCase, ReadModel |
| Stability Patterns | 4 | CircuitBreaker, Retry, RateLimiter, Bulkhead |
| Integration Patterns | 2 | Saga, Outbox |
| Behavioral Patterns | 6 | Strategy, State, Decorator, Chain, NullObject, Policy |
| Creational Patterns | 4 | Builder, ObjectPool, DIContainer, Mediator |
| ADR Patterns | 2 | Action, Responder |
| PSR Implementations | 11 | PSR-3, 6, 7, 11, 13, 14, 15, 16, 17, 18, 20 |
| Documentation Templates | 9 | README, Architecture, ADR, API, Mermaid |

### Knowledge Skills

| Skill                              | Description                                             |
|------------------------------------|---------------------------------------------------------|
| `acc-claude-code-knowledge`        | Knowledge base for Claude Code formats and patterns     |
| `acc-ddd-knowledge`                | DDD patterns, antipatterns, PHP guidelines              |
| `acc-cqrs-knowledge`               | CQRS patterns, command/query separation                 |
| `acc-clean-arch-knowledge`         | Clean Architecture, dependency rules                    |
| `acc-hexagonal-knowledge`          | Hexagonal Architecture, Ports & Adapters patterns       |
| `acc-layer-arch-knowledge`         | Layered Architecture, DTO patterns                      |
| `acc-event-sourcing-knowledge`     | Event Sourcing, projections, snapshots                  |
| `acc-eda-knowledge`                | Event-Driven Architecture, messaging, sagas             |
| `acc-saga-pattern-knowledge`       | Saga pattern, orchestration, compensation               |
| `acc-outbox-pattern-knowledge`     | Transactional Outbox, reliable messaging                |
| `acc-stability-patterns-knowledge` | Circuit Breaker, Retry, Rate Limiter, Bulkhead          |
| `acc-solid-knowledge`              | SOLID principles (SRP, OCP, LSP, ISP, DIP)              |
| `acc-grasp-knowledge`              | GRASP patterns (9 responsibility assignment principles) |
| `acc-adr-knowledge`                | Action-Domain-Responder pattern (MVC alternative)       |
| `acc-psr-coding-style-knowledge`   | PSR-1/PSR-12 coding standards                           |
| `acc-psr-autoloading-knowledge`    | PSR-4 autoloading standard                              |
| `acc-psr-overview-knowledge`       | All PSR standards overview                              |
| `acc-documentation-knowledge`      | Documentation types, audiences, best practices          |
| `acc-diagram-knowledge`            | Mermaid syntax, C4 model, diagram best practices        |
| `acc-documentation-qa-knowledge`   | Documentation quality checklists, audit criteria        |

### Generator Skills

#### DDD Components

| Skill                              | Description                                |
|------------------------------------|--------------------------------------------|
| `acc-create-value-object`          | Generates DDD Value Objects with tests     |
| `acc-create-entity`                | Generates DDD Entities with tests          |
| `acc-create-aggregate`             | Generates DDD Aggregates with tests        |
| `acc-create-domain-event`          | Generates Domain Events with tests         |
| `acc-create-domain-service`        | Generates Domain Services with tests       |
| `acc-create-repository`            | Generates Repository interfaces and stubs  |
| `acc-create-specification`         | Generates Specification pattern with tests |
| `acc-create-factory`               | Generates Factory pattern with tests       |
| `acc-create-dto`                   | Generates DTOs with tests                  |
| `acc-create-anti-corruption-layer` | Generates ACL for external integrations    |

#### CQRS Components

| Skill                   | Description                                |
|-------------------------|--------------------------------------------|
| `acc-create-command`    | Generates CQRS Commands and Handlers       |
| `acc-create-query`      | Generates CQRS Queries and Handlers        |
| `acc-create-use-case`   | Generates Application Use Cases with tests |
| `acc-create-read-model` | Generates CQRS Read Models/Projections     |

#### Stability Patterns

| Skill                        | Description                                           |
|------------------------------|-------------------------------------------------------|
| `acc-create-circuit-breaker` | Generates Circuit Breaker with state management       |
| `acc-create-retry-pattern`   | Generates Retry with exponential backoff              |
| `acc-create-rate-limiter`    | Generates Rate Limiter (Token Bucket, Sliding Window) |
| `acc-create-bulkhead`        | Generates Bulkhead isolation pattern                  |

#### Integration Patterns

| Skill                       | Description                               |
|-----------------------------|-------------------------------------------|
| `acc-create-saga-pattern`   | Generates Saga orchestration components   |
| `acc-create-outbox-pattern` | Generates Transactional Outbox components |

#### Behavioral Patterns

| Skill                                | Description                                |
|--------------------------------------|--------------------------------------------|
| `acc-create-strategy`                | Generates Strategy pattern with tests      |
| `acc-create-state`                   | Generates State machine pattern with tests |
| `acc-create-chain-of-responsibility` | Generates Handler chains with tests        |
| `acc-create-decorator`               | Generates Decorator pattern with tests     |
| `acc-create-null-object`             | Generates Null Object pattern with tests   |
| `acc-create-policy`                  | Generates Policy pattern with tests        |

#### Creational Patterns

| Skill                     | Description                              |
|---------------------------|------------------------------------------|
| `acc-create-builder`      | Generates Builder pattern with tests     |
| `acc-create-object-pool`  | Generates Object Pool pattern with tests |
| `acc-create-di-container` | Generates DI Container configuration     |
| `acc-create-mediator`     | Generates Mediator pattern with tests    |

#### Presentation Patterns (ADR)

| Skill                  | Description                                         |
|------------------------|-----------------------------------------------------|
| `acc-create-action`    | Generates ADR Action classes (HTTP handlers)        |
| `acc-create-responder` | Generates ADR Responder classes (response builders) |

#### PSR Implementations

| Skill                               | Description                          |
|-------------------------------------|--------------------------------------|
| `acc-create-psr3-logger`            | Generates PSR-3 Logger Interface     |
| `acc-create-psr6-cache`             | Generates PSR-6 Caching Interface    |
| `acc-create-psr7-http-message`      | Generates PSR-7 HTTP Messages        |
| `acc-create-psr11-container`        | Generates PSR-11 Container Interface |
| `acc-create-psr13-link`             | Generates PSR-13 Hypermedia Links    |
| `acc-create-psr14-event-dispatcher` | Generates PSR-14 Event Dispatcher    |
| `acc-create-psr15-middleware`       | Generates PSR-15 HTTP Middleware     |
| `acc-create-psr16-simple-cache`     | Generates PSR-16 Simple Cache        |
| `acc-create-psr17-http-factory`     | Generates PSR-17 HTTP Factories      |
| `acc-create-psr18-http-client`      | Generates PSR-18 HTTP Client         |
| `acc-create-psr20-clock`            | Generates PSR-20 Clock Interface     |

#### Documentation Templates

| Skill                           | Description                       |
|---------------------------------|-----------------------------------|
| `acc-readme-template`           | README.md generation templates    |
| `acc-architecture-doc-template` | ARCHITECTURE.md templates         |
| `acc-adr-template`              | Architecture Decision Records     |
| `acc-api-doc-template`          | API documentation templates       |
| `acc-getting-started-template`  | Getting started guide templates   |
| `acc-troubleshooting-template`  | Troubleshooting and FAQ templates |
| `acc-code-examples-template`    | Code examples templates           |
| `acc-mermaid-template`          | Mermaid diagram templates         |
| `acc-changelog-template`        | CHANGELOG.md templates            |

## Component Flow

```
COMMANDS                      AGENTS                      SKILLS
────────                      ──────                      ──────
/acc-commit ──────────────→ (direct Bash)

/acc-claude-code ─────────→ acc-claude-code-expert ───→ acc-claude-code-knowledge

/acc-audit-ddd ───────────→ acc-ddd-auditor ──────────→ acc-ddd-knowledge
                                  │
                                  └──→ (Task) acc-ddd-generator ──→ 13 create-* skills

/acc-audit-architecture ──→ acc-architecture-auditor ─→ 10 knowledge skills
                                  │
                                  ├──→ (Task) acc-ddd-generator ──→ 13 create-* skills
                                  └──→ (Task) acc-pattern-generator → 20 create-* skills

/acc-audit-psr ───────────→ acc-psr-auditor ──────────→ 3 PSR knowledge skills
                                  │
                                  └──→ (Skill) 11 PSR create-* skills

/acc-write-documentation ─→ acc-documentation-writer ─→ 8 template skills
                                  │
                                  └──→ (Task) acc-diagram-designer → 2 diagram skills

/acc-audit-documentation → acc-documentation-auditor → 3 QA knowledge skills
```

## Supported Patterns

This extension provides comprehensive support for modern software architecture patterns:

- **Domain-Driven Design (DDD)** — Aggregates, Entities, Value Objects, Domain Events, Repositories
- **CQRS** — Command/Query separation, Handlers, Buses
- **Clean Architecture** — Use Cases, Boundaries, Dependency Inversion
- **Hexagonal Architecture** — Ports & Adapters, Primary/Secondary adapters
- **Event Sourcing** — Event stores, Projections, Snapshots
- **Event-Driven Architecture** — Messaging, Pub/Sub, Event handlers
- **Saga Pattern** — Orchestration, Choreography, Compensation
- **Outbox Pattern** — Transactional messaging, Reliable delivery
- **Anti-Corruption Layer** — External system isolation, Translation
- **Stability Patterns** — Circuit Breaker, Retry, Rate Limiter, Bulkhead
- **Action-Domain-Responder** — Web-specific MVC alternative
- **PSR Standards** — PSR-3, 6, 7, 11, 13, 14, 15, 16, 17, 18, 20 implementations

## File Structure

```
.claude/
├── commands/           # 8 slash commands
├── agents/             # 11 subagents
└── skills/             # 73 skills

docs/                   # Detailed documentation
├── commands.md
├── agents.md
├── skills.md
├── component-flow.md
└── quick-reference.md
```

## FAQ

<details>
<summary><strong>How does auto-installation work?</strong></summary>

The Composer plugin subscribes to `POST_PACKAGE_INSTALL` and `POST_PACKAGE_UPDATE` events. When you run `composer require`, it automatically copies `.claude/` components (commands, agents, skills) to your project directory. Existing files are never overwritten to preserve your customizations.
</details>

<details>
<summary><strong>Can I customize generated code?</strong></summary>

Yes! Skills use templates stored in the `references/` folder within each skill directory. You can modify these templates to match your project's coding style, naming conventions, or add custom functionality.
</details>

<details>
<summary><strong>Which PHP versions are supported?</strong></summary>

Generated code targets PHP 8.5+ and uses modern features like readonly classes, constructor property promotion, and strict typing. The skills themselves work with Claude Code on any platform.
</details>

<details>
<summary><strong>How do I add my own commands/skills?</strong></summary>

Use the `/acc-claude-code` wizard to create new components interactively. It guides you through creating commands, agents, or skills with proper formatting and structure.
</details>

<details>
<summary><strong>What if I want to update to a newer version?</strong></summary>

Run `composer update dykyi-roman/awesome-claude-code`. New components are added, but existing files are not overwritten. To get updated versions of existing files, delete them first, then run the update.
</details>

<details>
<summary><strong>Can I use only specific skills?</strong></summary>

Yes. After installation, you can remove unwanted components from `.claude/` directory. Each component (command, agent, skill) works independently.
</details>

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

The MIT License (MIT). Please see [License File](LICENSE) for more information.
