# Awesome Claude Code

[![Latest Version on Packagist](https://img.shields.io/packagist/v/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![Total Downloads](https://img.shields.io/packagist/dt/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)
[![License](https://img.shields.io/packagist/l/dykyi-roman/awesome-claude-code.svg?style=flat-square)](https://packagist.org/packages/dykyi-roman/awesome-claude-code)

A collection of awesome Claude Code resources: commands, skills, agents, hooks, and more.

## Installation

Install via Composer:

```bash
composer require dykyi-roman/awesome-claude-code
```

Components are **automatically copied** to your project's `.claude/` directory:
- `commands/` — slash commands
- `agents/` — subagents
- `skills/` — skills

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
| `/acc-commit` | Auto-generate commit message from diff and push to current branch |
| `/acc-architecture-audit` | Comprehensive multi-pattern architecture audit for PHP projects |
| `/acc-ddd-audit` | DDD compliance analysis for PHP projects |

## Agents

| Agent | Description |
|-------|-------------|
| `acc-claude-code-expert` | Expert in Claude Code architecture and extensions |
| `acc-architecture-auditor` | Multi-pattern architecture auditor (DDD, CQRS, Clean, Hexagonal, Layered, EDA) |
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

### Generator Skills

Code generators for DDD and architecture components (PHP 8.4).

| Skill | Description |
|-------|-------------|
| `acc-create-value-object` | Generates DDD Value Objects with tests |
| `acc-create-entity` | Generates DDD Entities with tests |
| `acc-create-aggregate` | Generates DDD Aggregates with tests |
| `acc-create-domain-event` | Generates Domain Events with tests |
| `acc-create-repository` | Generates Repository interfaces and stubs |
| `acc-create-command` | Generates CQRS Commands and Handlers |
| `acc-create-query` | Generates CQRS Queries and Handlers |
| `acc-create-use-case` | Generates Application Use Cases with tests |

## Documentation

See [.claude/README.md](.claude/README.md) for detailed documentation.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

The MIT License (MIT). Please see [License File](LICENSE) for more information.
