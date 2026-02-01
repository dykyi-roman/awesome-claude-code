# Awesome Claude Code - DDD & Clean Architecture Generator for PHP

[![Latest Version on Packagist](https://img.shields.io/packagist/v/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![Total Downloads](https://img.shields.io/packagist/dt/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![PHP 8.5](https://img.shields.io/badge/PHP-8.5-blue?style=flat-square)](https://php.net)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Extension-purple?style=flat-square)](https://claude.ai/code)
[![DDD](https://img.shields.io/badge/DDD-Ready-green?style=flat-square)](https://en.wikipedia.org/wiki/Domain-driven_design)
[![CQRS](https://img.shields.io/badge/CQRS-Ready-orange?style=flat-square)](https://martinfowler.com/bliki/CQRS.html)
[![License](https://img.shields.io/packagist/l/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)

> **The most comprehensive Claude Code extension for PHP developers.**
> Auto-generate DDD components, audit architecture, and boost productivity with 39 skills and 7 agents.

## Features

- **39 Skills** — DDD, CQRS, Clean Architecture, Stability Patterns, Event Sourcing generators
- **Architecture Audit** — Automated compliance checking for 10+ patterns
- **Zero Config** — Auto-installs to `.claude/` directory via Composer
- **Tested Patterns** — Unit tests included for all generators
- **Knowledge Bases** — Deep expertise in DDD, CQRS, Hexagonal, EDA, Stability patterns

## Why Use This?

| Without | With Awesome Claude Code |
|---------|--------------------------|
| Manual boilerplate code | One command generates complete component |
| Architecture drift | Automated compliance audits |
| Inconsistent patterns | Standardized DDD/CQRS templates |
| Hours of setup | Instant productivity |
| Learning curve | Built-in knowledge bases |

## Quick Start

```bash
composer require dykyi-roman/awesome-claude-code
```

Then in Claude Code:

```
/acc-architecture-audit ./src
"Create Order aggregate with events"
"Generate Stripe payment ACL"
```

Components are **automatically copied** to your project's `.claude/` directory:
- `commands/` — slash commands
- `agents/` — subagents
- `skills/` — knowledge bases and generators

Existing files are not overwritten.

## Contents

- [Commands](#commands)
- [Agents](#agents)
- [Skills](#skills)
  - [Knowledge Skills](#knowledge-skills)
  - [Generator Skills](#generator-skills)
- [Documentation](#documentation)

## Commands

| Command | Description |
|---------|-------------|
| `/acc-claude-code` | Interactive wizard for creating commands, agents, skills, hooks |
| `/acc-claude-code-audit` | Audit `.claude/` folder structure and configuration quality |
| `/acc-commit` | Auto-generate commit message from diff and push to current branch |
| `/acc-architecture-audit` | Comprehensive multi-pattern architecture audit for PHP projects |
| `/acc-ddd-audit` | DDD compliance analysis for PHP projects |

## Agents

| Agent | Description |
|-------|-------------|
| `acc-claude-code-expert` | Expert in Claude Code architecture and extensions |
| `acc-architecture-auditor` | Multi-pattern architecture auditor (DDD, CQRS, Clean, Hexagonal, Layered, EDA, Stability) |
| `acc-architecture-generator` | Generates architecture components based on detected patterns |
| `acc-pattern-auditor` | Audits implementation patterns (Saga, Outbox, Stability, Behavioral) |
| `acc-pattern-generator` | Generates advanced pattern components |
| `acc-ddd-auditor` | Specialized DDD compliance auditor |
| `acc-ddd-generator` | Creates DDD and architecture components |

## Skills

### Knowledge Skills

Knowledge bases for architecture audits and best practices.

| Skill | Description |
|-------|-------------|
| `acc-claude-code-knowledge` | Knowledge base for Claude Code formats and patterns |
| `acc-ddd-knowledge` | DDD patterns, antipatterns, PHP guidelines |
| `acc-cqrs-knowledge` | CQRS patterns, command/query separation |
| `acc-clean-arch-knowledge` | Clean Architecture, dependency rules |
| `acc-hexagonal-knowledge` | Hexagonal Architecture, Ports & Adapters patterns |
| `acc-layer-arch-knowledge` | Layered Architecture, DTO patterns |
| `acc-event-sourcing-knowledge` | Event Sourcing, projections, snapshots |
| `acc-eda-knowledge` | Event-Driven Architecture, messaging, sagas |
| `acc-saga-pattern-knowledge` | Saga pattern, orchestration, compensation |
| `acc-outbox-pattern-knowledge` | Transactional Outbox, reliable messaging |
| `acc-stability-patterns-knowledge` | Circuit Breaker, Retry, Rate Limiter, Bulkhead |

### Generator Skills

Code generators for DDD and architecture components.

#### DDD Components

| Skill | Description |
|-------|-------------|
| `acc-create-value-object` | Generates DDD Value Objects with tests |
| `acc-create-entity` | Generates DDD Entities with tests |
| `acc-create-aggregate` | Generates DDD Aggregates with tests |
| `acc-create-domain-event` | Generates Domain Events with tests |
| `acc-create-domain-service` | Generates Domain Services with tests |
| `acc-create-repository` | Generates Repository interfaces and stubs |
| `acc-create-specification` | Generates Specification pattern with tests |
| `acc-create-factory` | Generates Factory pattern with tests |
| `acc-create-dto` | Generates DTOs with tests |
| `acc-create-anti-corruption-layer` | Generates ACL for external integrations |

#### CQRS Components

| Skill | Description |
|-------|-------------|
| `acc-create-command` | Generates CQRS Commands and Handlers |
| `acc-create-query` | Generates CQRS Queries and Handlers |
| `acc-create-use-case` | Generates Application Use Cases with tests |
| `acc-create-read-model` | Generates CQRS Read Models/Projections |

#### Stability Patterns

| Skill | Description |
|-------|-------------|
| `acc-create-circuit-breaker` | Generates Circuit Breaker with state management |
| `acc-create-retry-pattern` | Generates Retry with exponential backoff |
| `acc-create-rate-limiter` | Generates Rate Limiter (Token Bucket, Sliding Window) |
| `acc-create-bulkhead` | Generates Bulkhead isolation pattern |

#### Integration Patterns

| Skill | Description |
|-------|-------------|
| `acc-create-saga-pattern` | Generates Saga orchestration components |
| `acc-create-outbox-pattern` | Generates Transactional Outbox components |

#### Behavioral Patterns

| Skill | Description |
|-------|-------------|
| `acc-create-strategy` | Generates Strategy pattern with tests |
| `acc-create-state` | Generates State machine pattern with tests |
| `acc-create-chain-of-responsibility` | Generates Handler chains with tests |
| `acc-create-decorator` | Generates Decorator pattern with tests |
| `acc-create-null-object` | Generates Null Object pattern with tests |
| `acc-create-policy` | Generates Policy pattern with tests |

#### Creational Patterns

| Skill | Description |
|-------|-------------|
| `acc-create-builder` | Generates Builder pattern with tests |
| `acc-create-object-pool` | Generates Object Pool pattern with tests |

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

## Documentation

See [.claude/README.md](.claude/README.md) for detailed documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

The MIT License (MIT). Please see [License File](LICENSE) for more information.